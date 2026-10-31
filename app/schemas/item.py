from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# 1. Base Schema: Shared properties across request and response
class ItemBase(BaseModel):
    title: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="The name or title of the item",
        examples=["Machine Learning with PyTorch"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional detailed description",
        examples=["Comprehensive hands-on guide to deep neural networks."],
    )
    price: float = Field(
        ...,
        gt=0,
        description="Item price in USD (must be positive)",
        examples=[49.99],
    )
    is_available: bool = Field(
        default=True,
        description="Availability status in catalog",
        examples=[True],
    )


# 2. Create Schema: Attributes required when creating a new resource (POST)
class ItemCreate(ItemBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Natural Language Processing with Transformers",
                "description": "Building and fine-tuning BERT, GPT, and modern LLMs.",
                "price": 54.99,
                "is_available": True,
            }
        }
    )


# 3. Update Schema: Attributes that can be modified (PUT / PATCH)
class ItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=100, examples=["Updated AI Handbook"])
    description: Optional[str] = Field(default=None, max_length=500, examples=["Updated edition with LangChain and RAG."])
    price: Optional[float] = Field(default=None, gt=0, examples=[39.99])
    is_available: Optional[bool] = Field(default=None, examples=[False])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "price": 39.99,
                "is_available": False,
            }
        }
    )


# 4. Response Schema: What the client receives back from the API
class ItemResponse(ItemBase):
    id: int = Field(..., description="Unique auto-incremented identifier", examples=[1])
    created_at: datetime = Field(..., description="Timestamp when item was first created (UTC)")
    updated_at: datetime = Field(..., description="Timestamp of most recent update (UTC)")

    model_config = ConfigDict(from_attributes=True)
