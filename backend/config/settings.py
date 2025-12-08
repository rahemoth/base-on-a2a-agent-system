"""
Configuration module for the A2A Agent System
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    google_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./agents.db"
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
