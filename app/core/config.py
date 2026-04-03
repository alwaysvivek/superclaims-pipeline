from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    MAX_CONCURRENCY: int = 5
    MODEL_NAME: str = "llama-3.3-70b-versatile"

    class Config:
        env_file = ".env"

settings = Settings()
