from fastapi import APIRouter
from app.api.v1.endpoints import router as items_router

api_router = APIRouter()

# Register resource routes with prefix and OpenAPI tag
api_router.include_router(items_router, prefix="/items", tags=["Items"])
