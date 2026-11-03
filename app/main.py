from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.config import settings
from app.db.base import Base
from app.db.session import engine, get_db
import app.models  # Ensures all models are registered on Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Event Handler:
    - Runs on startup: Creates database tables in PostgreSQL if they don't exist.
    - Runs on shutdown: Closes and disposes engine connection pool.
    """
    # 1. Startup: Create tables in Neon PostgreSQL
    Base.metadata.create_all(bind=engine)

    yield

    # 2. Shutdown: Dispose engine connection pool
    engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 2,
        "docExpansion": "list",
        "filter": True,
        "tryItOutEnabled": True,
        "syntaxHighlight.theme": "monokai",
    },
)

# CORS middleware for allowing frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the centralized API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root():
    """Redirect root path directly to interactive Swagger API documentation."""
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    tags=["Health"],
    summary="Service & Database Health Check",
    status_code=status.HTTP_200_OK,
)
def health_check(db: Session = Depends(get_db)):
    """
    Pings the Neon PostgreSQL database with `SELECT 1` and returns system health status.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unreachable: {str(exc)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": {
            "status": db_status,
            "engine": "PostgreSQL (Neon)",
        },
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }
