"""
Application configuration settings.
Uses pydantic-settings for environment variable management.
"""

import os
from typing import List, Optional, Dict, Any, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "Presentation Generator API"
    app_version: str = "1.0.0"
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=False)
    
    # API Configuration
    api_prefix: str = "/api/v1"
    websocket_path: str = "/ws"
    cors_origins: Union[str, List[str]] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "https://www.deckster.xyz",
            "https://deckster.xyz"
        ],
        env="CORS_ORIGINS"
    )
    cors_allow_vercel_previews: bool = Field(default=True)
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Authentication
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiry_hours: int = Field(default=24, env="JWT_EXPIRY_HOURS")
    
    # Database
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_anon_key: str = Field(..., env="SUPABASE_ANON_KEY")
    supabase_service_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_KEY")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # AI Services
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    cohere_api_key: Optional[str] = Field(default=None, env="COHERE_API_KEY")
    replicate_api_token: Optional[str] = Field(default=None, env="REPLICATE_API_TOKEN")
    
    # MCP Servers
    brave_api_key: Optional[str] = Field(default=None, env="BRAVE_API_KEY")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    logfire_token: Optional[str] = Field(default=None, env="LOGFIRE_TOKEN")
    logfire_project: str = Field(default="presentation-generator", env="LOGFIRE_PROJECT")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=10, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    
    # File Upload
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    allowed_file_extensions: Union[str, List[str]] = Field(
        default=[".pdf", ".pptx", ".docx", ".xlsx", ".png", ".jpg", ".jpeg"],
        env="ALLOWED_FILE_EXTENSIONS"
    )
    
    # Session Management
    session_ttl_seconds: int = Field(default=3600, env="SESSION_TTL_SECONDS")
    session_cleanup_interval: int = Field(default=300, env="SESSION_CLEANUP_INTERVAL")
    
    # Agent Configuration
    agent_timeout_seconds: int = Field(default=30, env="AGENT_TIMEOUT_SECONDS")
    agent_max_retries: int = Field(default=3, env="AGENT_MAX_RETRIES")
    
    # Model Configuration
    primary_llm_model: str = Field(default="openai:gpt-4", env="PRIMARY_LLM_MODEL")
    fallback_llm_models: Union[str, List[str]] = Field(
        default=["openai:gpt-3.5-turbo", "anthropic:claude-3-sonnet"],
        env="FALLBACK_LLM_MODELS"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        env="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=1536, env="EMBEDDING_DIMENSION")
    
    # Presentation Defaults
    default_slide_count: int = Field(default=10, env="DEFAULT_SLIDE_COUNT")
    max_slide_count: int = Field(default=50, env="MAX_SLIDE_COUNT")
    default_presentation_theme: str = Field(default="professional", env="DEFAULT_PRESENTATION_THEME")
    
    # Performance
    cache_ttl_seconds: int = Field(default=300, env="CACHE_TTL_SECONDS")
    max_concurrent_agents: int = Field(default=5, env="MAX_CONCURRENT_AGENTS")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("app_env")
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "staging", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v
    
    @field_validator("cors_origins", mode="before")
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            if not v:
                return [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "https://www.deckster.xyz",
                    "https://deckster.xyz"
                ]
            # Try JSON first for backward compatibility
            if v.startswith('['):
                try:
                    import json
                    return json.loads(v)
                except:
                    pass
            # Parse comma-separated and clean up any semicolons Railway might add
            origins = []
            for origin in v.split(","):
                # Remove semicolons and whitespace
                cleaned = origin.strip().rstrip(';')
                if cleaned:
                    origins.append(cleaned)
            return origins if origins else [
                "http://localhost:3000",
                "http://localhost:5173",
                "https://www.deckster.xyz",
                "https://deckster.xyz"
            ]
        return v
    
    
    @field_validator("allowed_file_extensions", mode="before")
    def parse_file_extensions(cls, v):
        """Parse file extensions from string or list."""
        if isinstance(v, str):
            if not v:
                return [".pdf", ".pptx", ".docx", ".xlsx", ".png", ".jpg", ".jpeg"]
            if v.startswith('['):
                try:
                    import json
                    return json.loads(v)
                except:
                    return [".pdf", ".pptx", ".docx", ".xlsx", ".png", ".jpg", ".jpeg"]
            return [ext.strip() for ext in v.split(",") if ext.strip()]
        return v
    
    @field_validator("fallback_llm_models", mode="before")
    def parse_fallback_models(cls, v):
        """Parse fallback models from string or list."""
        if isinstance(v, str):
            if not v:
                return ["openai:gpt-3.5-turbo", "anthropic:claude-3-sonnet"]
            if v.startswith('['):
                try:
                    import json
                    return json.loads(v)
                except:
                    pass
            return [model.strip() for model in v.split(",") if model.strip()]
        return v
    
    @field_validator("cors_origins", "allowed_file_extensions", "fallback_llm_models", mode="after")
    def ensure_list_fields(cls, v):
        """Ensure these fields are always lists after processing."""
        if isinstance(v, str):
            # This should not happen if before validators work correctly
            return [v]
        return v if isinstance(v, list) else []
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.app_env == "development"
    
    @property
    def database_url(self) -> str:
        """Get database URL for direct connections."""
        # Extract from Supabase URL
        # Format: https://[project-ref].supabase.co
        # DB URL: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
        # This would need the actual database password, not included in basic setup
        return self.supabase_url
    
    @property
    def redis_dsn(self) -> str:
        """Get Redis DSN with password."""
        if self.redis_password:
            # Parse URL and insert password
            parts = self.redis_url.split("://")
            return f"{parts[0]}://:{self.redis_password}@{parts[1]}"
        return self.redis_url
    
    def get_llm_config(self, model_key: str) -> Dict[str, Any]:
        """Get configuration for a specific LLM model."""
        provider, model = model_key.split(":", 1)
        
        config = {
            "model": model,
            "provider": provider
        }
        
        if provider == "openai":
            config["api_key"] = self.openai_api_key
        elif provider == "anthropic":
            config["api_key"] = self.anthropic_api_key
        elif provider == "cohere":
            config["api_key"] = self.cohere_api_key
        
        return config
    
    def validate_required_services(self):
        """Validate that required services are configured."""
        errors = []
        
        # Check database
        if not self.supabase_url or not self.supabase_anon_key:
            errors.append("Supabase configuration missing")
        
        # Check at least one LLM service
        if not any([self.openai_api_key, self.anthropic_api_key, self.cohere_api_key]):
            errors.append("No LLM service API key configured")
        
        # Check JWT secret
        if not self.jwt_secret_key or self.jwt_secret_key == "your-secret-key-here":
            errors.append("JWT secret key not properly configured")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    



# Create singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings instance."""
    global _settings
    
    if _settings is None:
        _settings = Settings()
        
        # Validate in non-test environments
        if os.getenv("TESTING") != "true":
            _settings.validate_required_services()
    
    return _settings


# Convenience exports
settings = get_settings()


# Export
__all__ = ['Settings', 'get_settings', 'settings']