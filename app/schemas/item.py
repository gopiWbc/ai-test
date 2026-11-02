from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 1. Base Schema: Shared properties across request and response
# ---------------------------------------------------------------------------
class ItemBase(BaseModel):
    title: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="The name or title of the item",
        examples=["PostgreSQL High Performance Guide"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Detailed description of the item",
        examples=["Master query optimization, indexing, and connection pooling."],
    )
    price: float = Field(
        ...,
        gt=0,
        description="Price in USD (must be greater than 0)",
        examples=[49.99],
    )
    is_available: bool = Field(
        default=True,
        description="Availability status in the store/catalog",
        examples=[True],
    )


# ---------------------------------------------------------------------------
# 2. Create Schema: Attributes required when creating a new resource (POST)
# ---------------------------------------------------------------------------
class ItemCreate(ItemBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "FastAPI & SQLAlchemy Complete Guide",
                "description": "Production-ready backend API development with PostgreSQL.",
                "price": 39.99,
                "is_available": True,
            }
        }
    )


# ---------------------------------------------------------------------------
# 3. Update Schema: Attributes that can be modified (PUT / PATCH)
# ---------------------------------------------------------------------------
class ItemUpdate(BaseModel):
    title: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        examples=["Advanced FastAPI & Neon Cloud Postgres"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        examples=["Updated edition covering connection pooling, async, and indexes."],
    )
    price: Optional[float] = Field(
        default=None,
        gt=0,
        examples=[44.99],
    )
    is_available: Optional[bool] = Field(
        default=None,
        examples=[True],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "price": 44.99,
                "is_available": True,
            }
        }
    )


# ---------------------------------------------------------------------------
# 4. Response Schema: What the client receives back from the API
# ---------------------------------------------------------------------------
class ItemResponse(ItemBase):
    id: int = Field(..., description="Unique auto-incremented primary key", examples=[1])
    created_at: datetime = Field(..., description="Timestamp when record was created in database (UTC)")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated (UTC)")

    model_config = ConfigDict(from_attributes=True)
