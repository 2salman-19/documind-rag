"""
Centralized configuration loader for DocuMind RAG.

WHY: Single source of truth prevents scattered env var access across modules.
Makes testing easier (mock Settings instead of patching os.environ) and 
supports secret rotation without code changes. Uses Pydantic BaseSettings 
for automatic type validation and .env file loading.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    
    # Supabase Configuration (UPPERCASE to match .env)
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    
    # LLM Inference Configuration  
    GROQ_API_KEY: str
    
    # Environment & Debug
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True  # Now matches perfectly


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance.
    
    WHY: @lru_cache ensures Settings are parsed only once at startup.
    Prevents repeated .env file reads and provides singleton-like behavior
    without global state. Safe for async contexts as parsing is synchronous.
    """
    return Settings()