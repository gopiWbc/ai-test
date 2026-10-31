from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Customer Support & Ticket Triage API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Ollama Local Network Settings
    OLLAMA_BASE_URL: str = "http://192.168.1.16:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
