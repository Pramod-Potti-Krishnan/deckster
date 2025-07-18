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
    SUPABASE_URL: Optional[str] = Field(None, env="SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = Field(None, env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = Field(None, env="SUPABASE_SERVICE_KEY")
    
    # AI services
    GOOGLE_API_KEY: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Logging
    LOGFIRE_TOKEN: Optional[str] = Field(None, env="LOGFIRE_TOKEN")
    
    # Streamlined WebSocket Protocol
    USE_STREAMLINED_PROTOCOL: bool = Field(
        default=True,
        description="Enable streamlined WebSocket message protocol"
    )
    
    STREAMLINED_PROTOCOL_PERCENTAGE: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Percentage of sessions to use streamlined protocol (0-100)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env
    
    @property
    def has_ai_key(self) -> bool:
        """Check if at least one AI API key is configured."""
        return bool(self.GOOGLE_API_KEY or self.OPENAI_API_KEY or self.ANTHROPIC_API_KEY)
    
    def validate_settings(self) -> None:
        """Validate that essential settings are configured."""
        if not self.has_ai_key:
            raise ValueError(
                "At least one AI API key must be configured. "
                "Set GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in your .env file."
            )


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# For backward compatibility with existing code
settings = get_settings()