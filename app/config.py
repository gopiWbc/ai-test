from urllib.parse import unquote
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI PostgreSQL CRUD API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # PostgreSQL Connection String (e.g. Neon Serverless Postgres)
    DATABASE_URL: str = "postgresql://neondb_owner:npg_KlWx35zAZwBq@ep-misty-band-b6fdcpb1-pooler.c-2.sa-east-1.aws.neon.tech/Python%20Fast%20api?sslmode=require&channel_binding=require"

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Ensure database URL is decoded (handling %20 space in DB name)
        and compatible with SQLAlchemy.
        """
        url = unquote(self.DATABASE_URL)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
