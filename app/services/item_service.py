from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate


class ItemService:
    """
    Service Layer: Handles all business and storage operations.
    Standard pattern for separating business logic from HTTP routing.
    """

    def __init__(self):
        # In-memory storage dictionary: {id: ItemResponse}
        self._items: Dict[int, ItemResponse] = {}
        self._next_id: int = 1
        self._seed_sample_data()

    def _seed_sample_data(self):
        """Pre-populate a couple of items for easy initial testing."""
        sample_items = [
            ItemCreate(
                title="Python for Data Science",
                description="Comprehensive NumPy and Pandas handbook",
                price=29.99,
                is_available=True,
            ),
            ItemCreate(
                title="Deep Learning with PyTorch",
                description="Neural network architectures and model training",
                price=45.50,
                is_available=True,
            ),
        ]
        for item in sample_items:
            self.create(item)

    def get_all(self, skip: int = 0, limit: int = 10, search: Optional[str] = None) -> List[ItemResponse]:
        """READ (List): Returns paginated items with optional keyword search."""
        items = list(self._items.values())
        if search:
            search_lower = search.lower()
            items = [
                item for item in items
                if search_lower in item.title.lower() or (item.description and search_lower in item.description.lower())
            ]
        return items[skip : skip + limit]

    def get_by_id(self, item_id: int) -> Optional[ItemResponse]:
        """READ (Single): Returns a single item by primary key."""
        return self._items.get(item_id)

    def create(self, item_in: ItemCreate) -> ItemResponse:
        """CREATE: Inserts a new item and auto-assigns an ID and timestamps."""
        now = datetime.now(timezone.utc)
        item = ItemResponse(
            id=self._next_id,
            title=item_in.title,
            description=item_in.description,
            price=item_in.price,
            is_available=item_in.is_available,
            created_at=now,
            updated_at=now,
        )
        self._items[self._next_id] = item
        self._next_id += 1
        return item

    def update(self, item_id: int, item_in: ItemUpdate) -> Optional[ItemResponse]:
        """UPDATE: Modifies fields that are provided in the payload."""
        existing_item = self.get_by_id(item_id)
        if not existing_item:
            return None

        # Exclude unset fields so only passed fields are modified
        update_data = item_in.model_dump(exclude_unset=True)
        updated_dict = existing_item.model_dump()
        updated_dict.update(update_data)
        updated_dict["updated_at"] = datetime.now(timezone.utc)

        updated_item = ItemResponse(**updated_dict)
        self._items[item_id] = updated_item
        return updated_item

    def delete(self, item_id: int) -> bool:
        """DELETE: Removes an item by ID. Returns True if deleted, False if not found."""
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False


# Singleton service instance to share state across HTTP requests
item_service = ItemService()


def get_item_service() -> ItemService:
    """Dependency injection provider function."""
    return item_service
