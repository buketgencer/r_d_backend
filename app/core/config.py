# .env -> Settings sınıfı
# .env değerlerini Settings sınıfına aktarıp dependency injection sağlar

from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings  # ← yeni import


class Settings(BaseSettings):
    workspace_root: str = "workspace"
    embed_model: str
    topk: int = 10
    outer_api_url: Optional[str] = None
    outer_api_token: Optional[str] = None
    openai_api_key: str
    model_config = {"env_file": ".env", "case_sensitive": False}  # Pydantic-v2 eşdeğeri


@lru_cache
def get_settings() -> Settings:
    return Settings()
