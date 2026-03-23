"""
EgoZone Configuration Management
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application Configuration"""

    # Application base configuration
    app_name: str = "EgoZone"
    debug: bool = False  # Should be False in production
    secret_key: str = "change-me-in-production"

    # Gemini / Vertex AI configuration
    gemini_api_key: Optional[str] = None  # Not required when using service account
    gemini_model: str = "gemini-3-flash-preview"
    gcp_project: str  # GCP Project ID - must be set from environment variable
    gcp_location: str = (
        "us-central1"  # Vertex AI region (supports latest Gemini 3.0 Pro model)
    )

    # Database
    database_url: str = "sqlite:///./egozone.db"

    # Redis (optional)
    redis_url: Optional[str] = None

    # Telegram (optional)
    telegram_bot_token: Optional[str] = None

    # Google Cloud (Voice service, optional)
    google_cloud_project: Optional[str] = None

    # Admin password (for accessing interview, knowledge base, settings features) - must be set from environment variable
    admin_password: str  # Must be obtained from environment variable, no default value

    # Public access password (for accessing chat features, to prevent malicious attacks) - must be set from environment variable
    access_password: str  # Must be obtained from environment variable, no default value

    # Google Cloud Storage (persistent storage)
    gcs_bucket: Optional[str] = "egozone-data"
    use_gcs: bool = True  # Set to True in production

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get configuration singleton"""
    return Settings()
