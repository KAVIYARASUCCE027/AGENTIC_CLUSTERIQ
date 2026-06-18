"""
Application Settings Module.

Loads and validates environment variables using Pydantic Settings.
Provides a singleton settings instance for the entire application.
"""

import logging
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Resolve the .env file path relative to the project root
_ENV_FILE_PATH: Path = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.

    Attributes:
        GOOGLE_API_KEY: Google API key for Gemini model access.
        MODEL_NAME: The Gemini model identifier to use.
        HOST: The host address for the FastAPI server.
        PORT: The port number for the FastAPI server.
    """

    GOOGLE_API_KEY: str = ""
    MODEL_NAME: str = "gemini-2.5-flash"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- Phase 3: Spring Boot Integration ---
    SPRING_BOOT_BASE_URL: str = "http://localhost:8080"
    REQUEST_TIMEOUT: int = 10          # seconds
    CACHE_TTL: int = 60                # seconds
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0           # base delay in seconds

    # --- Phase 4: Database Integration ---
    MONGODB_URI: str = "mongodb+srv://user:pass@cluster.mongodb.net/"
    DATABASE_NAME: str = "agentic_k8s"

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE_PATH),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached singleton instance of the application settings.

    Uses lru_cache to ensure settings are loaded and validated only once.

    Returns:
        Settings: The validated application settings.
    """
    settings = Settings()
    logger.info("Application settings loaded successfully.")
    logger.info("Model configured: %s", settings.MODEL_NAME)
    logger.info("Server will bind to %s:%d", settings.HOST, settings.PORT)

    if not settings.GOOGLE_API_KEY:
        logger.warning(
            "GOOGLE_API_KEY is not set. Gemini API calls will fail. "
            "Please set it in the .env file."
        )

    return settings
