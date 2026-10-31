from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas.triage import (
    PromptEnhanceRequest,
    PromptEnhanceResponse,
    TicketRequest,
    TicketTriageResponse,
)
from app.services.ollama_service import OllamaService, get_ollama_service

router = APIRouter()


@router.get(
    "/models",
    summary="List installed Ollama models",
    description="Connects to the Ollama server on your network (192.168.1.16) and lists all installed models.",
)
def list_models(
    service: OllamaService = Depends(get_ollama_service),
) -> Dict[str, Any]:
    try:
        models = service.get_available_models()
        return {
            "ollama_host": service.base_url,
            "default_model": service.default_model,
            "available_models": models,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.post(
    "/analyze",
    response_model=TicketTriageResponse,
    status_code=status.HTTP_200_OK,
    summary="Triage Support Ticket (Structured AI Output)",
    description=(
        "Analyzes a customer inquiry using System Prompt + User Prompt. "
        "Classifies sentiment, urgency, category, and generates an empathetic resolution draft."
    ),
)
def analyze_ticket(
    payload: TicketRequest,
    service: OllamaService = Depends(get_ollama_service),
) -> TicketTriageResponse:
    try:
        return service.triage_ticket(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.post(
    "/stream-reply",
    summary="Live Streaming Support Reply",
    description="Streams an AI-generated customer response live token-by-token.",
)
def stream_reply(
    payload: TicketRequest,
    service: OllamaService = Depends(get_ollama_service),
):
    try:
        return StreamingResponse(
            service.stream_ticket_reply(payload),
            media_type="text/plain",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.post(
    "/enhance-prompt",
    response_model=PromptEnhanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Enhance Image Prompt with Selected Ollama Model",
    description=(
        "Transforms a rough idea into an expert Midjourney/Flux/SD prompt package, "
        "including negative prompts, lighting, composition, and optimal aspect ratio."
    ),
)
def enhance_prompt(
    payload: PromptEnhanceRequest,
    service: OllamaService = Depends(get_ollama_service),
) -> PromptEnhanceResponse:
    try:
        return service.enhance_image_prompt(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
