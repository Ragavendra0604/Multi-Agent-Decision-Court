"""
Multi-Agent Decision Court Configuration
Implements Module 27 (LLM Provider Abstraction Config) & Module 38 (Security & App Settings).
"""

from typing import Literal, Optional
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Multi-Agent Decision Court"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # LLM Settings (Module 27)
    LLM_PROVIDER: Literal["mock", "openrouter", "huggingface", "openai", "custom", "groq"] = "groq"
    LLM_MODEL: str = Field(
        default="openai/gpt-oss-120b",
        validation_alias=AliasChoices("LLM_MODEL", "OPENROUTER_MODEL", "GROQ_MODEL")
    )
    FALLBACK_LLM_MODEL: str = "openai/gpt-oss-20b"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "recursive/flint-v1.0:free"
    HUGGINGFACE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    ENABLE_CASCADE: bool = True
    
    # Execution & Cost Settings (Module 46 & 47)
    MAX_DEBATE_ROUNDS: int = 3
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_MAX_RETRIES: int = 3
    TEMPERATURE: float = 0.2
    
    # Database & Storage Settings (Module 39)
    DATABASE_URL: str = "sqlite+aiosqlite:///./court.db"
    STORAGE_DIR: str = "./storage"
    
    # Security (Module 38)
    SECRET_KEY: str = "madc-dev-secret-key-change-in-production-32bytes"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
