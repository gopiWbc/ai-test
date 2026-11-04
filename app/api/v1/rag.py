"""
RAG API Endpoints (Powered by ChromaDB Vector Store).

Presentation / Transport Layer:
- Document Management (Ingestion, Listing, Deletion)
- Grounded RAG Query with Citations (Standard HTTP JSON)
- Real-Time Streaming RAG with Server-Sent Events (SSE)
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.schemas.rag import (
    DocumentCreate,
    DocumentResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.services.rag_service import rag_service

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. DOCUMENT INGESTION & MANAGEMENT
# ---------------------------------------------------------------------------
@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Document into ChromaDB",
    description="Chunks raw document text, calculates 1536-dimensional embeddings, and stores them persistently in ChromaDB with HNSW indexing.",
)
def ingest_document(
    doc_in: DocumentCreate,
) -> DocumentResponse:
    return rag_service.ingest_document(doc_in=doc_in)


@router.get(
    "/documents",
    response_model=List[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="List Ingested Documents in ChromaDB",
    description="Retrieves a list of all documents indexed in the ChromaDB knowledge base.",
)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> List[DocumentResponse]:
    all_docs = rag_service.list_documents()
    return all_docs[skip : skip + limit]


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document & Chunks from ChromaDB",
    description="Permanently deletes a document and all associated embedding chunks from ChromaDB.",
)
def delete_document(
    document_id: str,
):
    rag_service.delete_document(doc_id=document_id)
    return None


# ---------------------------------------------------------------------------
# 2. RAG QUERY EXECUTION (NON-STREAMING)
# ---------------------------------------------------------------------------
@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask Question with RAG via ChromaDB (Non-Streaming)",
    description="Retrieves relevant chunks using ChromaDB HNSW cosine similarity, reranks via RRF, prompts OpenRouter LLM, and returns the grounded answer with verifiable citations.",
)
def query_rag(
    query_in: RAGQueryRequest,
) -> RAGQueryResponse:
    return rag_service.answer_query(query_in=query_in)


# ---------------------------------------------------------------------------
# 3. RAG STREAMING QUERY (SERVER-SENT EVENTS)
# ---------------------------------------------------------------------------
@router.post(
    "/query/stream",
    summary="Ask Question with RAG via ChromaDB (Real-Time Token Streaming)",
    description="Streams LLM tokens in real-time as Server-Sent Events (SSE). Sends citation metadata first, followed by live generated tokens.",
)
def stream_query_rag(
    query_in: RAGQueryRequest,
):
    event_generator = rag_service.stream_answer_query(query_in=query_in)
    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
