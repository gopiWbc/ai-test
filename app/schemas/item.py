from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# 1. Base Schema: Shared properties across request and response
class ItemBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=100, example="Machine Learning Textbook")
    description: Optional[str] = Field(None, max_length=500, example="A complete guide to Deep Learning and Transformers")
    price: float = Field(..., gt=0, example=49.99, description="Price must be greater than zero")
    is_available: bool = Field(default=True, example=True)


# 2. Create Schema: Attributes required when creating a new resource (POST)
class ItemCreate(ItemBase):
    pass


# 3. Update Schema: Attributes that can be modified (PUT / PATCH)
class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    is_available: Optional[bool] = None


# 4. Response Schema: What the client receives back from the API
class ItemResponse(ItemBase):
    id: int = Field(..., example=1)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
