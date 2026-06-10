with open('backend/config/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_settings = '''class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    google_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # OpenAI Configuration (supports OpenAI-compatible APIs like LM Studio)
    openai_base_url: Optional[str] = None  # e.g., http://localhost:1234/v1 for LM Studio
    
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
        case_sensitive = False'''

new_settings = '''class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    google_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Compression Model Configuration (for RAG context compression)
    compression_api_key: Optional[str] = None
    compression_base_url: Optional[str] = None
    compression_model: str = "gpt-4o-mini"
    compression_max_tokens: int = 500
    compression_temperature: float = 0.3
    
    # OpenAI Configuration (supports OpenAI-compatible APIs like LM Studio)
    openai_base_url: Optional[str] = None  # e.g., http://localhost:1234/v1 for LM Studio
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False'''

content = content.replace(old_settings, new_settings)

with open('backend/config/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Settings updated with compression model configuration!")