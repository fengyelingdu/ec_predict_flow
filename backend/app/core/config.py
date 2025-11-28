from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "EC Predict Flow"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    ANTHROPIC_API_KEY: Optional[str] = None
    BINANCE_PROXY: Optional[str] = None

    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    RAW_DATA_DIR: str = os.path.join(BASE_DIR, "data", "raw")
    PROCESSED_DATA_DIR: str = os.path.join(BASE_DIR, "data", "processed")
    MODELS_DIR: str = os.path.join(BASE_DIR, "data", "models")
    PLOTS_DIR: str = os.path.join(BASE_DIR, "data", "plots")
  

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

os.makedirs(settings.RAW_DATA_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)
os.makedirs(settings.PLOTS_DIR, exist_ok=True)
