# AI Learning - Standard FastAPI CRUD Project

A production-ready reference Python REST API demonstrating standard enterprise architecture, clean code practices, and full CRUD operations.

---

## Architecture Overview

```text
app/
├── main.py              # Entry point: FastAPI app, middleware, routers
├── config.py            # Environment configuration with pydantic-settings
├── api/
│   ├── router.py        # Central API router consolidating all endpoints
│   └── v1/
│       └── endpoints.py # REST endpoints (HTTP POST, GET, PUT, DELETE)
├── schemas/
│   └── item.py          # Data validation & serialization models (Pydantic)
└── services/
    └── item_service.py  # Business logic & repository layer
tests/
└── test_api.py          # Automated Pytest suite
```

---

## Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Development Server
```bash
uvicorn app.main:app --reload
```

The server will start at: `http://127.0.0.1:8000`

### 3. Interactive Documentation (Swagger UI)
Open your browser and visit:
- **Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Standard CRUD API Endpoints

| Operation | Method | Endpoint | HTTP Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Create** | `POST` | `/api/v1/items/` | `201 Created` | Add a new item |
| **Read All** | `GET` | `/api/v1/items/` | `200 OK` | Paginated list with search |
| **Read One** | `GET` | `/api/v1/items/{id}` | `200 OK` | Fetch item by ID |
| **Update** | `PUT` | `/api/v1/items/{id}` | `200 OK` | Partial/full update by ID |
| **Delete** | `DELETE` | `/api/v1/items/{id}` | `204 No Content` | Remove item by ID |

---

## Testing with cURL

### 1. Create an Item
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/items/" \
  -H "Content-Type: application/json" \
  -d '{"title": "Natural Language Processing", "description": "Transformers and Attention mechanisms", "price": 49.99, "is_available": true}'
```

### 2. List Items
```bash
curl "http://127.0.0.1:8000/api/v1/items/?skip=0&limit=5"
```

### 3. Get Single Item
```bash
curl "http://127.0.0.1:8000/api/v1/items/1"
```

### 4. Update an Item
```bash
curl -X PUT "http://127.0.0.1:8000/api/v1/items/1" \
  -H "Content-Type: application/json" \
  -d '{"price": 19.99, "is_available": false}'
```

### 5. Delete an Item
```bash
curl -X DELETE "http://127.0.0.1:8000/api/v1/items/1"
```

---

## Running Automated Tests
```bash
pytest
```
