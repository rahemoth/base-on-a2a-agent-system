"""
Configuration module for the A2A Agent System
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    google_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    kimi_api_key: Optional[str] = None
    mimo_api_key: Optional[str] = None
    minimax_api_key: Optional[str] = None
    zhipu_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    
    # Compression Model Configuration (for RAG context compression)
    compression_api_key: Optional[str] = None
    compression_base_url: Optional[str] = None
    compression_model: str = "glm-4.5-air"
    compression_max_tokens: int = 500
    compression_temperature: float = 0.3
    
    # API Base URLs
    openai_base_url: Optional[str] = None  # e.g., http://localhost:1234/v1 for LM Studio
    kimi_base_url: Optional[str] = None
    mimo_base_url: Optional[str] = None
    minimax_base_url: Optional[str] = None
    zhipu_base_url: Optional[str] = None
    qwen_base_url: Optional[str] = None
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./agents.db"
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # RAG Configuration
    rag_enabled: bool = True
    rag_compression_target: float = 0.3
    rag_max_context_chunks: int = 10
    rag_embedding_dimension: int = 768

    # ChromaDB vector store (persistent vector index for RAG)
    chroma_persist_dir: str = "./data/chroma"

    # LLM-based entity/relation extraction for the RAG memory graph.
    # The LLM client is the agent's own (per-provider), so no separate
    # api_key/base_url here — only model + sampling defaults.
    entity_extraction_enabled: bool = False
    entity_extraction_model: str = "gpt-4o-mini"
    entity_extraction_max_tokens: int = 800
    entity_extraction_temperature: float = 0.2

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
