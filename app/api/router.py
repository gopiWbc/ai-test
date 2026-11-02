from fastapi import APIRouter
from app.api.v1.endpoints import router as items_router

api_router = APIRouter()

# Mount items CRUD router
api_router.include_router(items_router, prefix="/items", tags=["Items (CRUD)"])
