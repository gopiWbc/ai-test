from fastapi import APIRouter
from app.api.v1.endpoints import router as items_router
from app.api.v1.rag import router as rag_router

api_router = APIRouter()

# Mount items CRUD router
api_router.include_router(items_router, prefix="/items", tags=["Items (CRUD)"])

# Mount RAG & Vector Knowledge Base router
api_router.include_router(rag_router, prefix="/rag", tags=["RAG (Vector Knowledge Base)"])
