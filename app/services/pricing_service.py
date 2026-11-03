"""
Pricing & Checkout Service.

Layer Role:
- Encapsulates business logic, domain rules, and workflow orchestration.
- Coordinates between DB (via CRUD) and utility helper functions.
- Protects the API layer from being bloated with business rules.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud.crud_item import crud_item
from app.schemas.pricing import PriceBreakdownResponse, QuoteRequest
from app.utils.pricing import (
    compute_discount_amount,
    compute_sales_tax,
    round_to_two_decimals,
)

# Business constants / domain rules
PROMO_DISCOUNTS = {
    "SAVE10": 10.0,
    "SAVE20": 20.0,
    "VIP50": 50.0,
}
SALES_TAX_PERCENTAGE = 8.5  # Standard 8.5% sales tax
BULK_THRESHOLD = 5
BULK_BONUS_DISCOUNT = 5.0  # Extra 5% discount for bulk orders (>= 5 units)


class PricingService:
    def calculate_item_quote(
        self,
        db: Session,
        item_id: int,
        quote_in: QuoteRequest,
    ) -> PriceBreakdownResponse:
        """
        Business Logic Workflow:
        1. Query entity from database.
        2. Validate business rules (availability, promo code validity).
        3. Determine combined discount percentage (promo + bulk tier).
        4. Delegate math calculations to pure helper functions.
        5. Return the finalized price breakdown DTO.
        """
        # Step 1: Entity lookup via CRUD layer
        item = crud_item.get(db=db, id=item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_id} not found",
            )

        # Step 2: Domain validation - Item must be available
        if not item.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item '{item.title}' is currently unavailable for order calculation.",
            )

        # Step 3: Domain validation - Promo code evaluation
        discount_percentage = 0.0
        if quote_in.promo_code:
            code = quote_in.promo_code.strip().upper()
            if code not in PROMO_DISCOUNTS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid promo code '{quote_in.promo_code}'. Valid codes: {list(PROMO_DISCOUNTS.keys())}",
                )
            discount_percentage += PROMO_DISCOUNTS[code]

        # Step 4: Business Rule - Bulk order bonus discount
        if quote_in.quantity >= BULK_THRESHOLD:
            discount_percentage += BULK_BONUS_DISCOUNT

        # Cap max discount at 70% to preserve business margin
        discount_percentage = min(discount_percentage, 70.0)

        # Step 5: Execute financial calculations using pure helper functions
        gross_subtotal = round_to_two_decimals(item.price * quote_in.quantity)
        discount_amount = compute_discount_amount(gross_subtotal, discount_percentage)
        net_taxable_amount = round_to_two_decimals(gross_subtotal - discount_amount)
        tax_amount = compute_sales_tax(net_taxable_amount, SALES_TAX_PERCENTAGE)
        final_total = round_to_two_decimals(net_taxable_amount + tax_amount)

        # Step 6: Assemble and return structured response
        return PriceBreakdownResponse(
            item_id=item.id,
            title=item.title,
            unit_price=item.price,
            quantity=quote_in.quantity,
            gross_subtotal=gross_subtotal,
            discount_percentage=discount_percentage,
            discount_amount=discount_amount,
            net_taxable_amount=net_taxable_amount,
            tax_rate_percentage=SALES_TAX_PERCENTAGE,
            tax_amount=tax_amount,
            final_total=final_total,
        )


pricing_service = PricingService()

