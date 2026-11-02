from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify health endpoint pings PostgreSQL and returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "connected"
    assert data["database"]["engine"] == "PostgreSQL (Neon)"


def test_root_redirect():
    """Verify root URL redirects to interactive Swagger /docs."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_crud_full_lifecycle():
    """
    Test complete CRUD lifecycle:
    1. CREATE -> POST /api/v1/items/
    2. READ ONE -> GET /api/v1/items/{id}
    3. READ LIST with pagination -> GET /api/v1/items/
    4. UPDATE (PUT) -> PUT /api/v1/items/{id}
    5. PARTIAL UPDATE (PATCH) -> PATCH /api/v1/items/{id}
    6. DELETE -> DELETE /api/v1/items/{id}
    7. VERIFY GONE -> GET /api/v1/items/{id} returns 404
    """
    # 1. CREATE
    payload = {
        "title": "CRUD Workflow Masterclass",
        "description": "Step by step guide to mastering FastAPI and PostgreSQL CRUD.",
        "price": 29.99,
        "is_available": True,
    }
    create_res = client.post("/api/v1/items/", json=payload)
    assert create_res.status_code == 201
    created_item = create_res.json()
    item_id = created_item["id"]
    assert created_item["title"] == payload["title"]
    assert created_item["description"] == payload["description"]
    assert created_item["price"] == payload["price"]
    assert created_item["is_available"] is True
    assert "created_at" in created_item
    assert "updated_at" in created_item

    # 2. READ ONE
    get_res = client.get(f"/api/v1/items/{item_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == item_id

    # 3. READ LIST with filtering & pagination
    list_res = client.get(f"/api/v1/items/?skip=0&limit=10&search=Masterclass")
    assert list_res.status_code == 200
    items = list_res.json()
    assert isinstance(items, list)
    assert any(i["id"] == item_id for i in items)

    # 4. UPDATE (PUT)
    put_payload = {
        "title": "CRUD Workflow Masterclass (Updated)",
        "price": 34.99,
    }
    put_res = client.put(f"/api/v1/items/{item_id}", json=put_payload)
    assert put_res.status_code == 200
    updated_data = put_res.json()
    assert updated_data["title"] == "CRUD Workflow Masterclass (Updated)"
    assert updated_data["price"] == 34.99
    # Description should remain unchanged because exclude_unset preserves existing fields
    assert updated_data["description"] == payload["description"]

    # 5. PARTIAL UPDATE (PATCH)
    patch_payload = {
        "is_available": False,
    }
    patch_res = client.patch(f"/api/v1/items/{item_id}", json=patch_payload)
    assert patch_res.status_code == 200
    assert patch_res.json()["is_available"] is False

    # 6. DELETE
    del_res = client.delete(f"/api/v1/items/{item_id}")
    assert del_res.status_code == 204

    # 7. VERIFY GONE (404)
    verify_res = client.get(f"/api/v1/items/{item_id}")
    assert verify_res.status_code == 404
    assert verify_res.json()["detail"] == f"Item with ID {item_id} not found"


def test_get_item_not_found():
    """Verify 404 is returned when querying non-existent item."""
    response = client.get("/api/v1/items/99999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_item_not_found():
    """Verify 404 is returned when attempting to delete non-existent item."""
    response = client.delete("/api/v1/items/99999999")
    assert response.status_code == 404
