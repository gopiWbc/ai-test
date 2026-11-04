from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 1. Document Ingestion Schemas
# ---------------------------------------------------------------------------
class DocumentCreate(BaseModel):
    """Payload for uploading and indexing a document into the RAG knowledge base."""
    title: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Name or title of the document",
        examples=["Neon PostgreSQL High Availability Architecture"],
    )
    content: str = Field(
        ...,
        min_length=10,
        description="Full text content of the document to be chunked and embedded",
        examples=["Neon is a serverless open-source alternative to AWS Aurora Postgres..."],
    )
    source: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Source identifier (e.g., file name, URL, department)",
        examples=["docs/architecture.pdf"],
    )
    chunk_size: int = Field(
        default=600,
        ge=100,
        le=2000,
        description="Target character length for each semantic chunk",
    )
    chunk_overlap: int = Field(
        default=100,
        ge=0,
        le=500,
        description="Sliding window overlap between consecutive chunks to maintain context continuity",
    )


class DocumentResponse(BaseModel):
    """Response returned after a document has been successfully chunked and embedded."""
    id: Union[int, str]
    title: str
    source: Optional[str]
    total_chunks: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 2. Retrieval & Query Schemas
# ---------------------------------------------------------------------------
class RAGQueryRequest(BaseModel):
    """User prompt and configuration parameters for RAG execution."""
    query: str = Field(
        ...,
        min_length=3,
        description="The question or prompt to answer using the knowledge base",
        examples=["How does Neon handle database branching and autoscaling?"],
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Number of most relevant text chunks to retrieve and feed into the LLM",
    )
    enable_hybrid: bool = Field(
        default=True,
        description="Whether to use Hybrid Search (Dense Vector + Keyword BM25) for retrieval",
    )
    document_ids: Optional[List[Union[int, str]]] = Field(
        default=None,
        description="Optional filter: restrict search to specific document IDs",
    )


class CitationChunk(BaseModel):
    """Source reference chunk proving where the LLM got its information."""
    chunk_id: Union[int, str]
    document_id: Union[int, str]
    document_title: str
    content: str
    similarity_score: float = Field(
        ...,
        description="Relevance score (higher is more relevant, range 0.0 to 1.0)",
    )


class RAGQueryResponse(BaseModel):
    """Final grounded synthesis from the LLM with verifiable source citations."""
    query: str
    answer: str
    citations: List[CitationChunk]
    model_used: str
    chunks_evaluated: int

