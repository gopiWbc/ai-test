from typing import List, Optional
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class CRUDItem:
    """
    CRUD Layer: Encapsulates all SQLAlchemy queries and persistence operations for the Item entity.
    Keeps API route handlers clean and decouples database queries from HTTP logic.
    """

    def get(self, db: Session, id: int) -> Optional[Item]:
        """
        READ (Single): Fetch one item by its primary key ID.
        Equivalent to: SELECT * FROM items WHERE id = :id;
        """
        stmt = select(Item).where(Item.id == id)
        return db.scalar(stmt)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        is_available: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> List[Item]:
        """
        READ (List): Fetch a paginated and filtered list of items.
        Supports search across title and description, availability filter, price range, and ordering.
        """
        stmt = select(Item)

        # Keyword search filter (case-insensitive ILIKE)
        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Item.title.ilike(search_pattern),
                    Item.description.ilike(search_pattern),
                )
            )

        # Availability filter
        if is_available is not None:
            stmt = stmt.where(Item.is_available == is_available)

        # Price range filter
        if min_price is not None:
            stmt = stmt.where(Item.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Item.price <= max_price)

        # Sorting
        sort_column = getattr(Item, sort_by, Item.id)
        if sort_order.lower() == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Pagination: OFFSET and LIMIT
        stmt = stmt.offset(skip).limit(limit)

        return list(db.scalars(stmt).all())

    def create(self, db: Session, *, obj_in: ItemCreate) -> Item:
        """
        CREATE: Inserts a new record into the items table and commits the transaction.
        Equivalent to: INSERT INTO items (...) VALUES (...);
        """
        db_obj = Item(
            title=obj_in.title,
            description=obj_in.description,
            price=obj_in.price,
            is_available=obj_in.is_available,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Item,
        obj_in: ItemUpdate,
    ) -> Item:
        """
        UPDATE: Updates existing item with provided fields and commits the transaction.
        Only fields explicitly provided in the request payload are modified (partial update / PATCH semantics).
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[Item]:
        """
        DELETE: Removes a record from the database by primary key.
        Equivalent to: DELETE FROM items WHERE id = :id;
        """
        obj = self.get(db, id=id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


crud_item = CRUDItem()
