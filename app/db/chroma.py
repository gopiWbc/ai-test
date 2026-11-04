"""
ChromaDB Vector Store Client & Repository.

Provides persistent, embedded vector storage with native HNSW indexing.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


class ChromaVectorStore:
    def __init__(self):
        # Ensure persistence directory exists
        persist_dir = Path(settings.CHROMA_PERSIST_DIRECTORY)
        persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedded persistent Chroma client
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Create or retrieve the collection with Cosine similarity distance metric
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # Uses HNSW with Cosine distance
        )

    def add_document_chunks(
        self,
        doc_id: str,
        title: str,
        chunks: List[str],
        embeddings: List[List[float]],
        source: Optional[str] = None,
    ) -> int:
        """
        Stores chunks and their 1536-dim embeddings into ChromaDB with metadata.
        """
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "title": title,
                "source": source or "unknown",
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        return len(chunks)

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB for the closest vector chunks using Cosine Distance.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        output: List[Dict[str, Any]] = []
        if not results["ids"] or not results["ids"][0]:
            return output

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for chunk_id, doc_text, meta, dist in zip(ids, documents, metadatas, distances):
            # ChromaDB cosine distance: 0.0 (identical) to 2.0 (opposite).
            # Convert distance to similarity score between 0.0 and 1.0
            similarity = max(0.0, 1.0 - (dist / 2.0))
            output.append({
                "chunk_id": chunk_id,
                "doc_id": meta.get("doc_id", "unknown"),
                "doc_title": meta.get("title", "Untitled"),
                "source": meta.get("source"),
                "chunk_index": meta.get("chunk_index", 0),
                "content": doc_text,
                "distance": dist,
                "similarity_score": round(similarity, 4),
            })

        return output

    def delete_document(self, doc_id: str) -> None:
        """Removes all chunks associated with a specific document ID."""
        self.collection.delete(where={"doc_id": doc_id})

    def list_documents(self) -> List[Dict[str, Any]]:
        """Scans metadata to return unique indexed documents and their chunk counts."""
        data = self.collection.get(include=["metadatas"])
        if not data or not data["metadatas"]:
            return []

        doc_summary: Dict[str, Dict[str, Any]] = {}
        for meta in data["metadatas"]:
            doc_id = meta.get("doc_id")
            if not doc_id:
                continue
            if doc_id not in doc_summary:
                doc_summary[doc_id] = {
                    "doc_id": doc_id,
                    "title": meta.get("title", "Untitled"),
                    "source": meta.get("source"),
                    "total_chunks": 0,
                }
            doc_summary[doc_id]["total_chunks"] += 1

        return list(doc_summary.values())


chroma_store = ChromaVectorStore()

