"""Gateway configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Rate limiting (requests per window)
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    # Cache
    cache_ttl_seconds: int = 300
    
    # Backend upstream (default target for reverse proxy)
    upstream_url: str = "http://httpbin.org"
    
    # API key validation (comma-separated keys for dev; use DB in production)
    api_keys: str = ""
    
    # Logging
    log_requests: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
