# FastAPI & PostgreSQL (Neon) CRUD Masterclass API

A production-grade Python REST API demonstrating enterprise-standard folder structure, SQLAlchemy ORM integration, Pydantic v2 schemas, and a complete CRUD workflow connected to **Neon Serverless PostgreSQL**.

---

## 🏗️ Industry-Standard Architecture

```text
.
├── .env                       # Environment variables (Neon Database URL, debug flags)
├── .env.example               # Template for environment configuration
├── requirements.txt           # Project dependencies (FastAPI, SQLAlchemy, psycopg2, Pydantic)
├── tests/
│   └── test_api.py            # Comprehensive Pytest test suite for all CRUD operations
└── app/
    ├── __init__.py
    ├── main.py                # FastAPI app initialization, lifespan, CORS, and health checks
    ├── config.py              # Pydantic BaseSettings & Database URI configuration
    ├── db/
    │   ├── __init__.py        # Exports Base, engine, SessionLocal, get_db
    │   ├── base.py            # SQLAlchemy 2.0 DeclarativeBase
    │   └── session.py         # Engine connection pool and get_db request dependency
    ├── models/
    │   ├── __init__.py        # Model registry
    │   └── item.py            # SQLAlchemy Item table model (PostgreSQL schema)
    ├── schemas/
    │   ├── __init__.py        # Schema exports
    │   └── item.py            # Pydantic request/response schemas (Base, Create, Update, Response)
    ├── crud/
    │   ├── __init__.py        # CRUD class exports
    │   └── crud_item.py       # Encapsulated SQLAlchemy database query operations
    └── api/
        ├── __init__.py
        ├── router.py          # Centralized API v1 router
        └── v1/
            ├── __init__.py
            └── endpoints.py   # REST API route handlers (POST, GET, PUT, PATCH, DELETE)
```

---

## 🔌 Database Connection (Neon PostgreSQL)

The database connection is configured in [`.env`](file:///.env) using your Neon connection URL:
```env
DATABASE_URL="postgresql://neondb_owner:npg_KlWx35zAZwBq@ep-misty-band-b6fdcpb1-pooler.c-2.sa-east-1.aws.neon.tech/Python%20Fast%20api?sslmode=require&channel_binding=require"
```

* Tables are automatically created upon application startup using SQLAlchemy's `Base.metadata.create_all()`.
* An automatic connection health-check endpoint (`GET /health`) actively pings the Neon PostgreSQL database.

---

## 🚀 Getting Started

### 1. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at: `http://127.0.0.1:8000`

### 4. Interactive Swagger Documentation
Open your browser and navigate to:
* **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔄 The Full CRUD Workflow

| Operation | HTTP Method | Endpoint | Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Create** | `POST` | `/api/v1/items/` | `201 Created` | Insert a new item into PostgreSQL |
| **Read (List)** | `GET` | `/api/v1/items/` | `200 OK` | Fetch paginated records with search & filters |
| **Read (Single)**| `GET` | `/api/v1/items/{id}` | `200 OK` | Fetch single record by primary key ID |
| **Update** | `PUT` | `/api/v1/items/{id}` | `200 OK` | Full / partial update of existing item |
| **Patch** | `PATCH` | `/api/v1/items/{id}` | `200 OK` | Selective field update (RFC 5789 PATCH) |
| **Delete** | `DELETE` | `/api/v1/items/{id}` | `204 No Content` | Permanently remove record by ID |
| **Health** | `GET` | `/health` | `200 OK` | Check API and live PostgreSQL connection |

---

## 🧪 Testing with cURL

### 1. Create a New Item (POST)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "PostgreSQL & FastAPI Masterclass",
    "description": "Production database CRUD guide with SQLAlchemy 2.0",
    "price": 39.99,
    "is_available": true
  }'
```

### 2. List Items with Search & Pagination (GET)
```bash
curl "http://127.0.0.1:8000/api/v1/items/?skip=0&limit=10&search=PostgreSQL&sort_by=price&sort_order=asc"
```

### 3. Read Single Item by ID (GET)
```bash
curl "http://127.0.0.1:8000/api/v1/items/1"
```

### 4. Update an Item (PUT or PATCH)
```bash
curl -X PATCH "http://127.0.0.1:8000/api/v1/items/1" \
  -H "Content-Type: application/json" \
  -d '{"price": 49.99, "is_available": false}'
```

### 5. Delete an Item (DELETE)
```bash
curl -X DELETE "http://127.0.0.1:8000/api/v1/items/1"
```

---

## ⚡ Running Automated Tests

Run the full Pytest suite against the live Neon database:
```bash
pytest -v
```