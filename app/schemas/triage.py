from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TicketRequest(BaseModel):
    customer_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the customer who submitted the ticket",
        examples=["Sarah Connor"],
    )
    subject: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Subject line of the customer inquiry",
        examples=["Package delayed for 2 weeks & no response!"],
    )
    message: str = Field(
        ...,
        min_length=5,
        max_length=3000,
        description="Full customer message content",
        examples=[
            "Hi, I placed order #9482 over two weeks ago. The tracking hasn't updated in 9 days. "
            "Nobody is answering my emails! I need this for my son's birthday this Saturday. "
            "Please expedite or refund me immediately!"
        ],
    )
    model: Optional[str] = Field(
        default=None,
        description="Ollama model to use (leave empty for default)",
        examples=["llama3.2"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_name": "Sarah Connor",
                "subject": "Package delayed for 2 weeks & no response!",
                "message": (
                    "Hi, I placed order #9482 over two weeks ago. The tracking hasn't updated in 9 days. "
                    "Nobody is answering my emails! I need this for my son's birthday this Saturday. "
                    "Please expedite or refund me immediately!"
                ),
                "model": "llama3.2",
            }
        }
    )


class TicketTriageResponse(BaseModel):
    sentiment: str = Field(..., description="Customer sentiment: Positive, Neutral, Frustrated, or Angry")
    urgency: str = Field(..., description="Priority tier: LOW, MEDIUM, HIGH, or CRITICAL")
    category: str = Field(..., description="Classification category: Shipping, Billing, Technical, or General")
    summary: str = Field(..., description="A 1-sentence summary of the core issue")
    suggested_reply: str = Field(..., description="An empathetic, professional draft reply to send back")
    model_used: str = Field(..., description="The Ollama model that performed the triage")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")


class PromptEnhanceRequest(BaseModel):
    raw_prompt: str = Field(
        ...,
        min_length=2,
        max_length=1500,
        description="Raw idea or concept to enhance (e.g. 'deadpool and spider man standing together')",
        examples=["deadpool and spider man standing together"],
    )
    style: Optional[str] = Field(
        default="Cinematic Photorealistic",
        description="Target aesthetic (e.g. Cinematic Photorealistic, Cyberpunk, 3D Pixar, Anime, Studio Photography)",
        examples=["Cinematic Photorealistic"],
    )
    target_engine: Optional[str] = Field(
        default="Midjourney & Stable Diffusion",
        description="Target image generator to format prompt for",
        examples=["Midjourney & Stable Diffusion"],
    )
    model: Optional[str] = Field(
        default=None,
        description="Ollama model used as prompt director",
        examples=["qwen3-coder:30b"],
    )


class PromptEnhanceResponse(BaseModel):
    original_prompt: str = Field(..., description="The user's initial input concept")
    enhanced_positive_prompt: str = Field(..., description="Rich, vivid, production-grade prompt ready to paste")
    negative_prompt: str = Field(..., description="Negative prompt keywords to filter out artifacts")
    suggested_aspect_ratio: str = Field(..., description="Optimal aspect ratio, e.g. 16:9, 1:1, or 9:16")
    lighting_and_atmosphere: str = Field(..., description="Lighting, mood, and color palette breakdown")
    camera_and_composition: str = Field(..., description="Camera angle, lens, and focal framing")
    style_tags: List[str] = Field(default_factory=list, description="Keywords and tags")
    model_used: str = Field(..., description="The Ollama model that generated the prompt package")
    processing_time_seconds: float = Field(..., description="Total processing time in seconds")
