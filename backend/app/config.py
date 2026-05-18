from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "QAgent — AI SDLC Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "dev_secret_key_replace_in_production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://qagent:qagent_secret@localhost:5432/qagent"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI Models
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    AI_MODEL: str = "claude-sonnet-4-6"
    AI_MODEL_FAST: str = "claude-haiku-4-5-20251001"
    AI_TEMPERATURE: float = 0.1
    AI_MAX_TOKENS: int = 8192

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Playwright
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_SLOW_MO: int = 0
    PLAYWRIGHT_TIMEOUT: int = 30000
    SCREENSHOT_ON_FAILURE: bool = True
    VIDEO_ON_FAILURE: bool = True


settings = Settings()
