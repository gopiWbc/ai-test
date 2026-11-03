from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud.crud_item import crud_item
from app.db.session import get_db
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.schemas.pricing import PriceBreakdownResponse, QuoteRequest
from app.services.pricing_service import pricing_service

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. CREATE (POST /api/v1/items/)
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new item",
    description="Inserts a new item into the PostgreSQL database. Returns the newly created record with its assigned ID and timestamp.",
)
def create_item(
    item_in: ItemCreate,
    db: Session = Depends(get_db),
) -> ItemResponse:
    """
    CRUD - Create:
    - Validates request payload against Pydantic schema
    - Persists record into Neon PostgreSQL using SQLAlchemy Session
    - Commits and returns the created entity
    """
    return crud_item.create(db=db, obj_in=item_in)


# ---------------------------------------------------------------------------
# 2. READ ALL (GET /api/v1/items/) with Filtering, Pagination & Sorting
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=List[ItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List items with filter, pagination & sorting",
    description="Query items from PostgreSQL with optional search keyword, availability filter, price range, sorting, and pagination.",
)
def list_items(
    skip: int = Query(0, ge=0, description="Offset: Number of records to skip for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Limit: Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Case-insensitive search in title or description"),
    is_available: Optional[bool] = Query(None, description="Filter by availability status (true/false)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    sort_by: str = Query("id", pattern="^(id|title|price|created_at)$", description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort direction ('asc' or 'desc')"),
    db: Session = Depends(get_db),
) -> List[ItemResponse]:
    """
    CRUD - Read (List):
    - Executes SELECT query with dynamic WHERE, ORDER BY, and LIMIT/OFFSET clauses
    """
    return crud_item.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        is_available=is_available,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
    )


# ---------------------------------------------------------------------------
# 3. READ ONE (GET /api/v1/items/{item_id})
# ---------------------------------------------------------------------------
@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get item by ID",
    description="Retrieve a single item from PostgreSQL using its unique primary key ID.",
)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> ItemResponse:
    """
    CRUD - Read (Single):
    - Queries item by primary key
    - Returns 404 NOT FOUND if record does not exist
    """
    item = crud_item.get(db=db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )
    return item


# ---------------------------------------------------------------------------
# 4. UPDATE (PUT /api/v1/items/{item_id}) - Full / Standard Update
# ---------------------------------------------------------------------------
@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing item",
    description="Update an item in PostgreSQL. Only provided fields are updated, preserving unmodified values.",
)
def update_item(
    item_id: int,
    item_in: ItemUpdate,
    db: Session = Depends(get_db),
) -> ItemResponse:
    """
    CRUD - Update:
    - Finds existing database record
    - Updates fields and auto-refreshes updated_at timestamp
    """
    item = crud_item.get(db=db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )
    return crud_item.update(db=db, db_obj=item, obj_in=item_in)


# ---------------------------------------------------------------------------
# 5. PARTIAL UPDATE (PATCH /api/v1/items/{item_id})
# ---------------------------------------------------------------------------
@router.patch(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update an existing item",
    description="Modify specific fields of an existing item without affecting other fields.",
)
def patch_item(
    item_id: int,
    item_in: ItemUpdate,
    db: Session = Depends(get_db),
) -> ItemResponse:
    """
    CRUD - Partial Update:
    - Supports HTTP PATCH standard for selective field modification
    """
    item = crud_item.get(db=db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )
    return crud_item.update(db=db, db_obj=item, obj_in=item_in)


# ---------------------------------------------------------------------------
# 6. DELETE (DELETE /api/v1/items/{item_id})
# ---------------------------------------------------------------------------
@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an item",
    description="Permanently remove an item from PostgreSQL. Returns 204 No Content on success.",
)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """
    CRUD - Delete:
    - Removes record from PostgreSQL
    - Returns 404 NOT FOUND if item was already deleted or doesn't exist
    """
    item = crud_item.remove(db=db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )
    return None


# ---------------------------------------------------------------------------
# 7. BUSINESS LOGIC (POST /api/v1/items/{item_id}/quote)
# ---------------------------------------------------------------------------
@router.post(
    "/{item_id}/quote",
    response_model=PriceBreakdownResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate order quote & discount (Business Logic)",
    description="Calculates gross total, applies promotional & bulk discounts, computes sales tax, and returns a detailed price breakdown.",
)
def calculate_item_quote(
    item_id: int,
    quote_in: QuoteRequest,
    db: Session = Depends(get_db),
) -> PriceBreakdownResponse:
    """
    Business Logic Endpoint:
    - Presentation layer: receives HTTP request, parses JSON via Pydantic.
    - Delegates domain rules & calculations to PricingService.
    """
    return pricing_service.calculate_item_quote(
        db=db,
        item_id=item_id,
        quote_in=quote_in,
    )

