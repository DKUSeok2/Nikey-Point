"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://nikepoint:dev_password@localhost:5432/nikepoint"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    STORAGE_PATH: str = "./storage/videos"
    STORAGE_TYPE: str = "local"  # "local" or "s3" (future)
    MAX_VIDEO_SIZE_MB: int = 100
    ALLOWED_VIDEO_EXTENSIONS: list[str] = [".mp4", ".mov", ".avi"]
    
    # MediaPipe
    MEDIAPIPE_MODEL_COMPLEXITY: int = 2  # 0, 1, or 2
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE: float = 0.5
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE: float = 0.5
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Security (for future JWT implementation)
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]  # In production, specify exact origins
    
    # OpenAI
    OPENAI_API_KEY: str | None = None  # Optional for LLM feedback
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
