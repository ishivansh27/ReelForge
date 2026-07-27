"""
App-wide settings, loaded from environment variables (via .env file).

Non-technical note: this is the single place that reads your `.env` file.
Every other file in the app should import `settings` from here instead of
reading environment variables directly.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://reelapp:reelapp_local_password@localhost:5432/reelapp"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET_KEY: str = "changeme_generate_a_real_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = ""
    # Override to point at a local/mock S3-compatible endpoint (testing,
    # or a non-AWS provider). Leave blank to use real AWS.
    S3_ENDPOINT_URL: str = ""

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # OCR (text overlay detection)
    # Leave blank to rely on PATH (works out of the box on Linux prod
    # once tesseract-ocr is apt-installed). On Windows, a fresh winget
    # install often isn't on PATH for already-open shells, so fall back
    # to its default install location if present.
    TESSERACT_CMD: str = ""

    # Rendering (FFmpeg)
    # Leave blank to rely on PATH (works out of the box on Linux prod
    # once ffmpeg is apt-installed). On Windows, a fresh winget install
    # updates PATH at the OS level, but any process whose parent was
    # already running before the install (this whole harness included)
    # keeps the PATH it started with -- so fall back to the known
    # winget install location if present.
    FFMPEG_CMD: str = ""
    FFPROBE_CMD: str = ""
    # Bold font for gap-fill text clips (Day 16). Leave blank to try a
    # few common bold system fonts (Windows and Linux paths both
    # checked, since this app runs on both across dev/prod).
    FONT_PATH: str = ""

    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
