"""
RAG API Endpoints.

Presentation / Transport Layer:
- Document Management (Ingestion, Listing, Deletion)
- Grounded RAG Query with Citations (Standard HTTP JSON)
- Real-Time Streaming RAG with Server-Sent Events (SSE)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
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
    summary="Ingest Document into Vector Database",
    description="Chunks raw document text, calculates 1536-dimensional embeddings, and stores them in Neon PostgreSQL with pgvector HNSW indexing.",
)
def ingest_document(
    doc_in: DocumentCreate,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    return rag_service.ingest_document(db=db, doc_in=doc_in)


@router.get(
    "/documents",
    response_model=List[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="List Ingested Documents",
    description="Retrieves a list of all documents indexed in the knowledge base.",
)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[DocumentResponse]:
    docs = db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document & Vector Chunks",
    description="Permanently deletes a document and all associated embedding chunks from PostgreSQL.",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found",
        )
    db.delete(doc)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# 2. RAG QUERY EXECUTION (NON-STREAMING)
# ---------------------------------------------------------------------------
@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask Question with RAG (Non-Streaming)",
    description="Retrieves relevant chunks using Hybrid Search (pgvector + BM25), reranks via RRF, prompts OpenRouter LLM, and returns the grounded answer with verifiable citations.",
)
def query_rag(
    query_in: RAGQueryRequest,
    db: Session = Depends(get_db),
) -> RAGQueryResponse:
    return rag_service.answer_query(db=db, query_in=query_in)


# ---------------------------------------------------------------------------
# 3. RAG STREAMING QUERY (SERVER-SENT EVENTS)
# ---------------------------------------------------------------------------
@router.post(
    "/query/stream",
    summary="Ask Question with RAG (Real-Time Token Streaming)",
    description="Streams LLM tokens in real-time as Server-Sent Events (SSE). Sends citation metadata first, followed by live generated tokens.",
)
def stream_query_rag(
    query_in: RAGQueryRequest,
    db: Session = Depends(get_db),
):
    event_generator = rag_service.stream_answer_query(db=db, query_in=query_in)
    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

