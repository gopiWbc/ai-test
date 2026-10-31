from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from app.api.router import api_router
from app.config import settings

TEMPLATES_DIR = Path(__file__).parent / "templates"
TRIAGE_UI_PATH = TEMPLATES_DIR / "triage_ui.html"
IMAGE_UI_PATH = TEMPLATES_DIR / "image_ui.html"

tags_metadata = [
    {
        "name": "AI Support Triage (Ollama)",
        "description": "Real-time Customer Support & Ticket Triage powered by Ollama on local network (192.168.1.16).",
    },
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
    description="""
### 🎯 AI Support Triage, Image Studio & Python REST API
Powered by local **Ollama** running on your local network (`192.168.1.16`).

* **Support Triage UI**: [/chat-ui](/chat-ui) or [/triage-ui](/triage-ui)
* **AI Image Studio UI**: [/image-ui](/image-ui)
* **Swagger API Docs**: [/docs](/docs)
    """,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
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


# Route 1: Dedicated Support Triage UI
@app.get("/chat-ui", response_class=HTMLResponse, include_in_schema=False)
@app.get("/triage-ui", response_class=HTMLResponse, include_in_schema=False)
def serve_triage_ui():
    """Serve the dedicated AI Customer Support Triage Dashboard UI."""
    if TRIAGE_UI_PATH.exists():
        return TRIAGE_UI_PATH.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Triage UI template not found</h1>", status_code=404)


# Route 2: Dedicated AI Image Prompt Enhancer Studio UI
@app.get("/image-ui", response_class=HTMLResponse, include_in_schema=False)
@app.get("/prompt-studio", response_class=HTMLResponse, include_in_schema=False)
def serve_image_ui():
    """Serve the dedicated AI Image Generation Studio UI."""
    if IMAGE_UI_PATH.exists():
        return IMAGE_UI_PATH.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Image UI template not found</h1>", status_code=404)


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root directly to the support triage UI."""
    return RedirectResponse(url="/chat-ui")


@app.get("/health", tags=["Health"], summary="API Health Check")
def health_check():
    """Returns runtime health status and metadata."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "ollama_host": settings.OLLAMA_BASE_URL,
        "triage_ui": "/chat-ui",
        "image_ui": "/image-ui",
        "swagger_docs": "/docs",
        "redoc_docs": "/redoc",
    }
