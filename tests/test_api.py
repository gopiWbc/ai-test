from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify health endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_item():
    """Test CREATE (POST /api/v1/items/)."""
    payload = {
        "title": "Machine Learning Fundamentals",
        "description": "Intro to regression and classification",
        "price": 39.99,
        "is_available": True,
    }
    response = client.post("/api/v1/items/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["price"] == payload["price"]
    assert "id" in data
    assert "created_at" in data


def test_list_items():
    """Test READ ALL (GET /api/v1/items/)."""
    response = client.get("/api/v1/items/?skip=0&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_item_by_id():
    """Test READ ONE (GET /api/v1/items/{id})."""
    response = client.get("/api/v1/items/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1


def test_get_item_not_found():
    """Test 404 behavior for non-existent item."""
    response = client.get("/api/v1/items/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item with ID 999999 not found"


def test_update_item():
    """Test UPDATE (PUT /api/v1/items/{id})."""
    update_payload = {
        "price": 19.99,
        "is_available": False,
    }
    response = client.put("/api/v1/items/1", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 19.99
    assert data["is_available"] is False


def test_delete_item():
    """Test DELETE (DELETE /api/v1/items/{id})."""
    # Create item to delete
    create_res = client.post("/api/v1/items/", json={
        "title": "Item To Delete",
        "price": 9.99,
        "is_available": True,
    })
    item_id = create_res.json()["id"]

    # Delete it
    del_res = client.delete(f"/api/v1/items/{item_id}")
    assert del_res.status_code == 204

    # Verify it is gone
    get_res = client.get(f"/api/v1/items/{item_id}")
    assert get_res.status_code == 404
