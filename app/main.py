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
    - Runs on startup: Creates database tables in PostgreSQL if they don't exist
      and seeds initial data if table is empty.
    - Runs on shutdown: Closes and disposes engine connection pool.
    """
    # 1. Startup: Create tables in Neon PostgreSQL
    Base.metadata.create_all(bind=engine)

    # 2. Seed initial sample data if the table is currently empty
    with Session(engine) as db:
        from app.models.item import Item
        count = db.query(Item).count()
        if count == 0:
            sample_items = [
                Item(
                    title="Python Web Development with FastAPI",
                    description="Comprehensive guide covering modern REST APIs, Pydantic, and dependency injection.",
                    price=34.99,
                    is_available=True,
                ),
                Item(
                    title="Mastering PostgreSQL Architecture",
                    description="Deep dive into indexing, connection pooling, transactions, and query plans.",
                    price=49.99,
                    is_available=True,
                ),
                Item(
                    title="Cloud-Native Backend Systems",
                    description="Architecting scalable microservices on AWS and serverless Neon databases.",
                    price=59.00,
                    is_available=False,
                ),
            ]
            db.add_all(sample_items)
            db.commit()

    yield

    # 3. Shutdown: Dispose engine connection pool
    engine.dispose()


tags_metadata = [
    {
        "name": "Items (CRUD)",
        "description": "Full Create, Read, Update, and Delete operations backed by PostgreSQL.",
    },
    {
        "name": "Health",
        "description": "Service and PostgreSQL database connectivity health checks.",
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
### 🚀 Production-Grade FastAPI & PostgreSQL CRUD API
Connected to **Neon Serverless PostgreSQL**.

#### 📚 Features:
* **Create (POST /api/v1/items/)**: Add new records with Pydantic validation.
* **Read List (GET /api/v1/items/)**: Paginated listings with search, price filters, and sorting.
* **Read One (GET /api/v1/items/{id})**: Fetch a single item by primary key.
* **Update (PUT & PATCH /api/v1/items/{id})**: Full or partial record updates with auto-timestamping.
* **Delete (DELETE /api/v1/items/{id})**: Delete records with standard 204 response.
* **Health Check (GET /health)**: Live database ping to confirm PostgreSQL connectivity.

👉 Explore and test the API interactively using the Swagger documentation below.
    """,
    openapi_tags=tags_metadata,
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
