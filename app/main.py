from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api.router import api_router
from app.config import settings

tags_metadata = [
    {
        "name": "Items",
        "description": "Standard CRUD operations for catalog item management.",
    },
    {
        "name": "Health",
        "description": "System health and status monitoring endpoints.",
    },
]

# Initialize FastAPI with full Swagger (OpenAPI) configuration
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="### 🚀 Standard Python REST API & CRUD Operations",
    openapi_tags=tags_metadata,
    docs_url="/docs",          # Swagger UI endpoint
    redoc_url="/redoc",        # ReDoc alternative documentation
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 2,
        "docExpansion": "list",
        "filter": True,
        "tryItOutEnabled": True,
        "syntaxHighlight.theme": "monokai",
    },
)

# CORS middleware for allowing web frontend clients (e.g. React, Next.js, Vue)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount central API router under /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root directly to the interactive Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"], summary="API Health Check")
def health_check():
    """Returns runtime health status and metadata."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "swagger_docs": "/docs",
        "redoc_docs": "/redoc",
    }
