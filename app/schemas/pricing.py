from typing import Optional
from pydantic import BaseModel, Field


class QuoteRequest(BaseModel):
    """Input payload for price calculation business logic."""
    quantity: int = Field(default=1, ge=1, le=100, description="Number of units to purchase")
    promo_code: Optional[str] = Field(default=None, description="Optional promotional discount code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "quantity": 3,
                "promo_code": "SAVE10",
            }
        }
    }


class PriceBreakdownResponse(BaseModel):
    """Response payload returning detailed financial breakdown."""
    item_id: int
    title: str
    unit_price: float
    quantity: int
    gross_subtotal: float
    discount_percentage: float
    discount_amount: float
    net_taxable_amount: float
    tax_rate_percentage: float
    tax_amount: float
    final_total: float

