from fastapi import APIRouter
from app.api.v1.endpoints import router as items_router
from app.api.v1.triage import router as triage_router

api_router = APIRouter()

# Register resource routes with prefix and OpenAPI tag
api_router.include_router(items_router, prefix="/items", tags=["Items"])
api_router.include_router(triage_router, prefix="/triage", tags=["AI Support Triage (Ollama)"])
