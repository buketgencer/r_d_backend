# .env -> Settings sınıfı
#.env değerlerini Settings sınıfına aktarıp dependency injection sağlar

from functools import lru_cache
from pydantic_settings import BaseSettings     # ← yeni import

class Settings(BaseSettings):
    workspace_root: str = "workspace"
    embed_model: str
    topk: int = 10
    outer_api_url: str
    outer_api_token: str

    model_config = {               # Pydantic-v2 eşdeğeri
        "env_file": ".env",
        "case_sensitive": False
    }

@lru_cache
def get_settings() -> Settings:
    return Settings()

