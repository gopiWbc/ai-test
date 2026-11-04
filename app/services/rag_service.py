"""
RAG Orchestration & Domain Service using ChromaDB.

Coordinates:
1. Ingestion: Document chunking, batch vector embedding, and persistence in ChromaDB.
2. Retrieval: Hybrid Search combining ChromaDB Dense Cosine HNSW Similarity with Keyword Matching via Reciprocal Rank Fusion.
3. Generation: Grounded prompt synthesis with strict anti-hallucination guardrails and source citations.
4. Streaming: Real-time token streaming via Server-Sent Events (SSE).
"""
from datetime import datetime
import json
from typing import Generator, List, Optional, Union
import uuid
from fastapi import HTTPException, status

from app.config import settings
from app.db.chroma import chroma_store
from app.schemas.rag import (
    CitationChunk,
    DocumentCreate,
    DocumentResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.utils.openrouter_client import openrouter_client
from app.utils.reranker import reciprocal_rank_fusion
from app.utils.text_chunker import recursive_chunk_text


class RAGService:
    # -----------------------------------------------------------------------
    # 1. DOCUMENT INGESTION
    # -----------------------------------------------------------------------
    def ingest_document(self, doc_in: DocumentCreate) -> DocumentResponse:
        """
        Ingests a document into ChromaDB:
        1. Chunks raw text using recursive separator splitting with overlap.
        2. Generates 1536-dimensional embeddings for each chunk via OpenRouter.
        3. Persists chunks and embeddings into ChromaDB collection.
        """
        # Step 1: Chunk text
        text_chunks = recursive_chunk_text(
            text=doc_in.content,
            chunk_size=doc_in.chunk_size,
            chunk_overlap=doc_in.chunk_overlap,
        )

        if not text_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document content produced 0 valid chunks after processing.",
            )

        doc_id = str(uuid.uuid4())[:8]

        # Step 2: Generate Vector Embeddings in batches
        BATCH_SIZE = 16
        all_embeddings: List[List[float]] = []
        for i in range(0, len(text_chunks), BATCH_SIZE):
            batch = text_chunks[i : i + BATCH_SIZE]
            batch_vectors = openrouter_client.generate_embeddings(batch)
            all_embeddings.extend(batch_vectors)

        # Step 3: Persist into ChromaDB
        chroma_store.add_document_chunks(
            doc_id=doc_id,
            title=doc_in.title.strip(),
            chunks=text_chunks,
            embeddings=all_embeddings,
            source=doc_in.source.strip() if doc_in.source else None,
        )

        return DocumentResponse(
            id=doc_id,
            title=doc_in.title.strip(),
            source=doc_in.source.strip() if doc_in.source else None,
            total_chunks=len(text_chunks),
            created_at=datetime.utcnow(),
        )

    # -----------------------------------------------------------------------
    # 2. HYBRID RETRIEVAL & FUSION
    # -----------------------------------------------------------------------
    def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = 4,
        enable_hybrid: bool = True,
        document_ids: Optional[List[Union[int, str]]] = None,
    ) -> List[CitationChunk]:
        """
        Executes retrieval using ChromaDB:
        1. Dense Retrieval: Computes query vector and runs ChromaDB HNSW cosine query.
        2. Sparse/Keyword Re-ranking: Re-ranks candidates matching keyword frequencies.
        3. Returns formatted source citation chunks.
        """
        # Step 1: Generate dense vector for user query
        query_vector = openrouter_client.generate_single_embedding(query)

        # Step 2: Metadata filter (optional document scoping)
        where_filter = None
        if document_ids:
            str_ids = [str(d) for d in document_ids]
            if len(str_ids) == 1:
                where_filter = {"doc_id": str_ids[0]}
            else:
                where_filter = {"doc_id": {"$in": str_ids}}

        # Step 3: Query ChromaDB for top candidates
        candidate_k = top_k * 3 if enable_hybrid else top_k
        dense_results = chroma_store.query(
            query_embedding=query_vector,
            top_k=candidate_k,
            where_filter=where_filter,
        )

        if not dense_results:
            return []

        # Step 4: Hybrid Re-ranking (if enabled)
        if enable_hybrid:
            keywords = [w.strip().lower() for w in query.split() if len(w.strip()) > 3]
            if keywords:
                # Rank candidates by keyword hits
                sparse_ranked = sorted(
                    dense_results,
                    key=lambda r: sum(1 for kw in keywords if kw in r["content"].lower()),
                    reverse=True,
                )
                fused = reciprocal_rank_fusion(
                    ranked_lists=[dense_results, sparse_ranked],
                    k=60,
                    id_getter=lambda x: x["chunk_id"],
                )
                selected_items = [item for item, _ in fused[:top_k]]
            else:
                selected_items = dense_results[:top_k]
        else:
            selected_items = dense_results[:top_k]

        # Step 5: Format structured citation references
        citations: List[CitationChunk] = []
        for item in selected_items:
            citations.append(
                CitationChunk(
                    chunk_id=item["chunk_id"],
                    document_id=item["doc_id"],
                    document_title=item["doc_title"],
                    content=item["content"],
                    similarity_score=item["similarity_score"],
                )
            )

        return citations

    # -----------------------------------------------------------------------
    # 3. PROMPT COMPOSITION & GROUNDED GENERATION
    # -----------------------------------------------------------------------
    def _build_rag_messages(self, query: str, citations: List[CitationChunk]) -> List[dict]:
        """
        Builds the prompt with strict grounding constraints to eliminate hallucinations.
        """
        context_blocks = []
        for i, c in enumerate(citations, 1):
            context_blocks.append(
                f"[Source #{i} | Doc ID {c.document_id}: '{c.document_title}' | Chunk {c.chunk_id}]\n{c.content}"
            )
        formatted_context = "\n\n---\n\n".join(context_blocks)

        system_prompt = (
            "You are a production-grade enterprise factual AI assistant.\n"
            "Your task is to answer the user's question accurately using ONLY the information provided in the CONTEXT blocks below.\n\n"
            "STRICT RULES:\n"
            "1. Answer strictly based on the context. Do not extrapolate, assume, or use prior outside knowledge.\n"
            "2. If the answer cannot be found in the context, explicitly say: 'Based on the provided documents, I do not have enough information to answer this question.'\n"
            "3. Cite your sources inline using [Source #X] whenever stating facts.\n"
            "4. Keep the explanation concise, professional, and directly to the point."
        )

        user_content = f"CONTEXT:\n{formatted_context}\n\nQUESTION: {query}"

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    def answer_query(self, query_in: RAGQueryRequest) -> RAGQueryResponse:
        """
        Standard Non-Streaming RAG response generation.
        """
        citations = self.retrieve_relevant_chunks(
            query=query_in.query,
            top_k=query_in.top_k,
            enable_hybrid=query_in.enable_hybrid,
            document_ids=query_in.document_ids,
        )

        if not citations:
            return RAGQueryResponse(
                query=query_in.query,
                answer="No relevant documents found in the database matching your query. Please upload reference documents first.",
                citations=[],
                model_used=settings.OPENROUTER_CHAT_MODEL,
                chunks_evaluated=0,
            )

        messages = self._build_rag_messages(query=query_in.query, citations=citations)
        llm_answer = openrouter_client.generate_chat_completion(messages=messages)

        return RAGQueryResponse(
            query=query_in.query,
            answer=llm_answer,
            citations=citations,
            model_used=settings.OPENROUTER_CHAT_MODEL,
            chunks_evaluated=len(citations),
        )

    # -----------------------------------------------------------------------
    # 4. STREAMING GENERATION (SERVER-SENT EVENTS)
    # -----------------------------------------------------------------------
    def stream_answer_query(
        self, query_in: RAGQueryRequest
    ) -> Generator[str, None, None]:
        """
        Streams RAG tokens in real-time as Server-Sent Events (SSE).
        """
        citations = self.retrieve_relevant_chunks(
            query=query_in.query,
            top_k=query_in.top_k,
            enable_hybrid=query_in.enable_hybrid,
            document_ids=query_in.document_ids,
        )

        # 1. Emit retrieved citations first
        citations_data = [c.model_dump() for c in citations]
        yield f"data: {json.dumps({'event': 'citations', 'data': citations_data})}\n\n"

        if not citations:
            no_docs_msg = "No relevant documents found in the database. Please upload knowledge documents first."
            yield f"data: {json.dumps({'token': no_docs_msg})}\n\n"
            yield "data: [DONE]\n\n"
            return

        # 2. Build prompt and stream tokens from OpenRouter LLM
        messages = self._build_rag_messages(query=query_in.query, citations=citations)
        for sse_event in openrouter_client.stream_chat_completion(messages=messages):
            yield sse_event

    # -----------------------------------------------------------------------
    # 5. DOCUMENT MANAGEMENT
    # -----------------------------------------------------------------------
    def list_documents(self) -> List[DocumentResponse]:
        docs = chroma_store.list_documents()
        return [
            DocumentResponse(
                id=d["doc_id"],
                title=d["title"],
                source=d.get("source"),
                total_chunks=d["total_chunks"],
            )
            for d in docs
        ]

    def delete_document(self, doc_id: str) -> None:
        chroma_store.delete_document(doc_id)


rag_service = RAGService()
