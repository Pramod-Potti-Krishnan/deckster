"""
Settings configuration for Deckster.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # App settings
    APP_ENV: str = Field("development", env="APP_ENV")
    DEBUG: bool = Field(True, env="DEBUG")
    LOG_LEVEL: str = Field("DEBUG", env="LOG_LEVEL")
    
    # API settings
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="PORT")
    
    # Supabase settings
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(..., env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = Field(None, env="SUPABASE_SERVICE_KEY")
    
    # AI services
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    
    # Logging
    LOGFIRE_TOKEN: Optional[str] = Field(None, env="LOGFIRE_TOKEN")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# For backward compatibility with existing code
settings = get_settings()