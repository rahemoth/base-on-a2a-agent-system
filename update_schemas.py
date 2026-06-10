with open('backend/models/schemas.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_agent_config = '''class AgentConfig(BaseModel):
    """Agent configuration model"""
    name: str = Field(..., description="Agent name")
    description: str = Field("", description="Agent description")
    provider: ModelProvider = Field(ModelProvider.GOOGLE, description="Model provider")
    model: str = Field("gemini-2.0-flash-exp", description="Model to use")
    system_prompt: Optional[str] = Field(None, description="System prompt for the agent")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    google_api_key: Optional[str] = Field(None, description="Google API key for this agent (overrides global setting)")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key for this agent (overrides global setting)")
    openai_base_url: Optional[str] = Field(None, description="Custom OpenAI-compatible API base URL (e.g., http://localhost:1234/v1 for LMStudio)")
    api_base_url: Optional[str] = Field(None, description="API base URL for local/custom providers")
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list, description="MCP servers configuration")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")'''

new_agent_config = '''class CompressionConfig(BaseModel):
    """Configuration for context compression using small models"""
    enabled: bool = Field(False, description="Enable context compression")
    provider: str = Field("openai", description="Compression model provider")
    model: str = Field("gpt-4o-mini", description="Model to use for compression")
    api_key: Optional[str] = Field(None, description="API key for compression model (overrides global setting)")
    base_url: Optional[str] = Field(None, description="Base URL for compression API")
    max_tokens: int = Field(500, description="Maximum tokens for compression output")
    temperature: float = Field(0.3, description="Temperature for compression")
    target_ratio: float = Field(0.3, description="Target compression ratio")


class AgentConfig(BaseModel):
    """Agent configuration model"""
    name: str = Field(..., description="Agent name")
    description: str = Field("", description="Agent description")
    provider: ModelProvider = Field(ModelProvider.GOOGLE, description="Model provider")
    model: str = Field("gemini-2.0-flash-exp", description="Model to use")
    system_prompt: Optional[str] = Field(None, description="System prompt for the agent")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    google_api_key: Optional[str] = Field(None, description="Google API key for this agent (overrides global setting)")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key for this agent (overrides global setting)")
    openai_base_url: Optional[str] = Field(None, description="Custom OpenAI-compatible API base URL (e.g., http://localhost:1234/v1 for LMStudio)")
    api_base_url: Optional[str] = Field(None, description="API base URL for local/custom providers")
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list, description="MCP servers configuration")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # RAG and Memory Configuration
    rag_enabled: bool = Field(False, description="Enable RAG memory system")
    compression: CompressionConfig = Field(default_factory=CompressionConfig, description="Context compression configuration")'''

content = content.replace(old_agent_config, new_agent_config)

with open('backend/models/schemas.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Agent config schema updated with compression settings!")