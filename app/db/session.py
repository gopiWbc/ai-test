from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# Create engine with pre-ping to handle serverless idle connection drops gracefully
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

# Session factory for synchronous database transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional SQLAlchemy session per request.
    Closes the session automatically when the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
