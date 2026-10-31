from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.item_service import ItemService, get_item_service

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. CREATE (POST /items)
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new item",
    description="Add a new item to the inventory. Returns the newly created item with its ID.",
)
def create_item(
    item_in: ItemCreate,
    service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    return service.create(item_in)


# ---------------------------------------------------------------------------
# 2. READ ALL (GET /items) with Pagination & Search
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=List[ItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List all items",
    description="Retrieve a paginated list of items with optional search filtering.",
)
def list_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max number of items to return"),
    search: Optional[str] = Query(None, description="Search term for title or description"),
    service: ItemService = Depends(get_item_service),
) -> List[ItemResponse]:
    return service.get_all(skip=skip, limit=limit, search=search)


# ---------------------------------------------------------------------------
# 3. READ ONE (GET /items/{item_id})
# ---------------------------------------------------------------------------
@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get item by ID",
    description="Retrieve details for a specific item using its primary key.",
)
def get_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    item = service.get_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )
    return item


# ---------------------------------------------------------------------------
# 4. UPDATE (PUT /items/{item_id})
# ---------------------------------------------------------------------------
@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing item",
    description="Update an item's fields by ID. Only provided fields will be modified.",
)
def update_item(
    item_id: int,
    item_in: ItemUpdate,
    service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    updated = service.update(item_id, item_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )
    return updated


# ---------------------------------------------------------------------------
# 5. DELETE (DELETE /items/{item_id})
# ---------------------------------------------------------------------------
@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an item",
    description="Remove an item from the inventory. Returns empty response on success.",
)
def delete_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
):
    deleted = service.delete(item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )
    return None
