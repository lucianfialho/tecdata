"""
Configuration settings for Termômetro de Tecnologia project.
Uses Pydantic for validation and type safety.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    host: str = Field(default="localhost", env="POSTGRES_HOST")
    port: int = Field(default=5432, env="POSTGRES_PORT")
    database: str = Field(default="tecdata", env="POSTGRES_DB")
    username: str = Field(default="tecdata_user", env="POSTGRES_USER")
    password: str = Field(default="tecdata_pass", env="POSTGRES_PASSWORD")
    url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    class Config:
        extra = "ignore"
    
    @validator("url", always=True)
    def build_database_url(cls, v, values):
        """Build database URL if not provided."""
        if v:
            return v
        return (
            f"postgresql://{values['username']}:{values['password']}"
            f"@{values['host']}:{values['port']}/{values['database']}"
        )


class APISettings(BaseSettings):
    """API configuration settings."""
    
    tecmundo_base_url: str = Field(
        default="https://www.tecmundo.com.br",
        env="TECMUNDO_API_BASE_URL"
    )
    tecmundo_endpoint: str = Field(
        default="/api/posts?endpoint=home-author",
        env="TECMUNDO_API_ENDPOINT"
    )
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT_SECONDS")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    backoff_factor: float = Field(default=2.0, env="BACKOFF_FACTOR")
    
    class Config:
        extra = "ignore"
    
    @property
    def tecmundo_full_url(self) -> str:
        """Get complete Tecmundo API URL."""
        return f"{self.tecmundo_base_url}{self.tecmundo_endpoint}"


class CollectionSettings(BaseSettings):
    """Data collection configuration settings."""
    
    interval_hours: int = Field(default=6, env="COLLECTION_INTERVAL_HOURS")
    requests_per_minute: int = Field(default=10, env="REQUESTS_PER_MINUTE")
    min_request_interval: int = Field(default=6, env="MIN_REQUEST_INTERVAL_SECONDS")
    
    class Config:
        extra = "ignore"
    
    @validator("interval_hours")
    def validate_interval(cls, v):
        """Validate collection interval."""
        if v < 1 or v > 24:
            raise ValueError("Collection interval must be between 1 and 24 hours")
        return v


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", env="LOG_LEVEL")
    file_path: str = Field(default="./logs/tecdata.log", env="LOG_FILE_PATH")
    rotation: str = Field(default="1 day", env="LOG_ROTATION")
    retention: str = Field(default="30 days", env="LOG_RETENTION")
    
    class Config:
        extra = "ignore"
    
    @validator("level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class AppSettings(BaseSettings):
    """Main application settings."""
    
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    collection: CollectionSettings = CollectionSettings()
    logging: LoggingSettings = LoggingSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from env
        
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()


# Global settings instance
settings = AppSettings()