"""
RAG Orchestration & Domain Service.

Coordinates:
1. Ingestion: Document chunking, batch vector embedding, and persistence in PostgreSQL pgvector.
2. Retrieval: Hybrid Search combining Dense Cosine Similarity with Keyword BM25 using Reciprocal Rank Fusion.
3. Generation: Grounded prompt synthesis with strict anti-hallucination guardrails and source citations.
4. Streaming: Real-time token streaming via Server-Sent Events (SSE).
"""
import json
from typing import Generator, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.document import Document, DocumentChunk
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
    def ingest_document(self, db: Session, doc_in: DocumentCreate) -> DocumentResponse:
        """
        Ingests a document into the knowledge base:
        1. Creates parent Document entity.
        2. Chunks raw text using recursive separator splitting with overlap.
        3. Generates 1536-dimensional embeddings for each chunk via OpenRouter.
        4. Saves chunks into PostgreSQL with pgvector cosine indexes.
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

        # Step 2: Create Parent Document in DB
        doc = Document(
            title=doc_in.title.strip(),
            source=doc_in.source.strip() if doc_in.source else None,
            total_chunks=len(text_chunks),
        )
        db.add(doc)
        db.flush()  # Flush to generate doc.id for foreign keys

        # Step 3: Generate Vector Embeddings in batches
        BATCH_SIZE = 16
        all_embeddings: List[List[float]] = []
        for i in range(0, len(text_chunks), BATCH_SIZE):
            batch = text_chunks[i : i + BATCH_SIZE]
            batch_vectors = openrouter_client.generate_embeddings(batch)
            all_embeddings.extend(batch_vectors)

        # Step 4: Persist DocumentChunk entities with vector embeddings
        for idx, (chunk_text, vector) in enumerate(zip(text_chunks, all_embeddings)):
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_text,
                token_count=len(chunk_text.split()),
                embedding=vector,
            )
            db.add(chunk)

        db.commit()
        db.refresh(doc)
        return DocumentResponse.model_validate(doc)

    # -----------------------------------------------------------------------
    # 2. HYBRID RETRIEVAL & FUSION
    # -----------------------------------------------------------------------
    def retrieve_relevant_chunks(
        self,
        db: Session,
        query: str,
        top_k: int = 4,
        enable_hybrid: bool = True,
        document_ids: Optional[List[int]] = None,
    ) -> List[CitationChunk]:
        """
        Executes hybrid retrieval:
        1. Dense Retrieval: Computes query vector and runs pgvector cosine distance query.
        2. Sparse Retrieval: Performs full-text / keyword matching across chunks.
        3. Fuses both ranked lists using Reciprocal Rank Fusion (RRF).
        """
        # Step 1: Generate dense vector for the user query
        query_vector = openrouter_client.generate_single_embedding(query)

        # Step 2: Dense pgvector search (Cosine Distance: 0 = identical, 2 = opposite)
        # In pgvector: cosine_distance = 1 - cosine_similarity
        distance_col = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
        dense_query = (
            db.query(DocumentChunk, distance_col)
            .join(Document, Document.id == DocumentChunk.document_id)
            .options(joinedload(DocumentChunk.document))
        )
        if document_ids:
            dense_query = dense_query.filter(DocumentChunk.document_id.in_(document_ids))

        # Retrieve top candidates for re-ranking
        dense_results = dense_query.order_by(distance_col.asc()).limit(top_k * 3).all()
        dense_chunks = [chunk for chunk, _ in dense_results]

        # Step 3: Sparse / Keyword search (if hybrid enabled)
        sparse_chunks: List[DocumentChunk] = []
        if enable_hybrid:
            keywords = [w.strip() for w in query.split() if len(w.strip()) > 3]
            if keywords:
                keyword_filters = [DocumentChunk.content.ilike(f"%{kw}%") for kw in keywords[:5]]
                sparse_query = (
                    db.query(DocumentChunk)
                    .join(Document, Document.id == DocumentChunk.document_id)
                    .options(joinedload(DocumentChunk.document))
                    .filter(or_(*keyword_filters))
                )
                if document_ids:
                    sparse_query = sparse_query.filter(DocumentChunk.document_id.in_(document_ids))
                sparse_chunks = sparse_query.limit(top_k * 3).all()

        # Step 4: Merge results via Reciprocal Rank Fusion (RRF)
        if enable_hybrid and sparse_chunks:
            fused_results = reciprocal_rank_fusion(
                ranked_lists=[dense_chunks, sparse_chunks],
                k=60,
                id_getter=lambda c: c.id,
            )
            selected_items = fused_results[:top_k]
        else:
            # Fall back to dense vector distance rankings
            selected_items = [(chunk, 1.0 / (1.0 + dist)) for chunk, dist in dense_results[:top_k]]

        # Step 5: Format structured citation references
        citations: List[CitationChunk] = []
        for chunk, score in selected_items:
            doc_title = chunk.document.title if chunk.document else "Unknown Document"
            citations.append(
                CitationChunk(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=doc_title,
                    content=chunk.content,
                    similarity_score=round(score, 4),
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

    def answer_query(self, db: Session, query_in: RAGQueryRequest) -> RAGQueryResponse:
        """
        Standard Non-Streaming RAG response generation.
        """
        citations = self.retrieve_relevant_chunks(
            db=db,
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
        self, db: Session, query_in: RAGQueryRequest
    ) -> Generator[str, None, None]:
        """
        Streams RAG tokens in real-time as Server-Sent Events (SSE).
        Emits:
        1. 'citations' metadata event with retrieved chunk references.
        2. 'token' events containing LLM output chunks.
        3. '[DONE]' event on completion.
        """
        citations = self.retrieve_relevant_chunks(
            db=db,
            query=query_in.query,
            top_k=query_in.top_k,
            enable_hybrid=query_in.enable_hybrid,
            document_ids=query_in.document_ids,
        )

        # 1. Emit retrieved citations first so the client UI can render sources immediately
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


rag_service = RAGService()

