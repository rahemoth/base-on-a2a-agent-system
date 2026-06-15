"""
Pydantic models for the A2A Agent System
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class ModelProvider(str, Enum):
    """Model provider enumeration"""
    DEEPSEEK = "deepseek"
    KIMI = "kimi"
    MIMO = "mimo"
    MINIMAX = "minimax"
    GLM = "glm"
    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"
    QWEN = "qwen"
    CUSTOM = "custom"


class MCPServerConfig(BaseModel):
    """MCP Server configuration"""
    name: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}


class CompressionConfig(BaseModel):
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
    provider: ModelProvider = Field(ModelProvider.DEEPSEEK, description="Model provider")
    model: str = Field("deepseek-v4-pro", description="Model to use")
    system_prompt: Optional[str] = Field(None, description="System prompt for the agent")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    google_api_key: Optional[str] = Field(None, description="Google API key for this agent (overrides global setting)")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key for this agent (overrides global setting)")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key for this agent (overrides global setting)")
    kimi_api_key: Optional[str] = Field(None, description="Kimi API key for this agent (overrides global setting)")
    mimo_api_key: Optional[str] = Field(None, description="MiMo API key for this agent (overrides global setting)")
    minimax_api_key: Optional[str] = Field(None, description="MiniMax API key for this agent (overrides global setting)")
    zhipu_api_key: Optional[str] = Field(None, description="Zhipu API key for this agent (overrides global setting)")
    qwen_api_key: Optional[str] = Field(None, description="Qwen API key for this agent (overrides global setting)")
    openai_base_url: Optional[str] = Field(None, description="Custom OpenAI-compatible API base URL (e.g., http://localhost:1234/v1 for LMStudio)")
    api_base_url: Optional[str] = Field(None, description="API base URL for local/custom providers")
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list, description="MCP servers configuration")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # RAG and Memory Configuration
    rag_enabled: bool = Field(False, description="Enable RAG memory system")
    compression: CompressionConfig = Field(default_factory=CompressionConfig, description="Context compression configuration")

    # Skill Configuration
    skills: List[str] = Field(default_factory=list, description="List of active skill IDs")


class AgentCreate(BaseModel):
    """Model for creating an agent"""
    config: AgentConfig


class AgentResponse(BaseModel):
    """Agent response model"""
    id: str
    config: AgentConfig
    status: AgentStatus
    created_at: datetime
    updated_at: datetime


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class Message(BaseModel):
    """Message model for agent communication"""
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentMessage(BaseModel):
    """Message to send to an agent"""
    agent_id: str
    message: str
    context: Optional[List[Message]] = None
    stream: bool = False


class AgentCollaboration(BaseModel):
    """Model for multi-agent collaboration"""
    agents: List[str] = Field(..., description="List of agent IDs to collaborate")
    task: str = Field(..., description="Task description")
    coordinator_agent: Optional[str] = Field(None, description="Coordinator agent ID")
    max_rounds: int = Field(5, description="Maximum collaboration rounds")


class AgentUpdate(BaseModel):
    """Model for updating agent configuration"""
    config: Optional[AgentConfig] = None
    status: Optional[AgentStatus] = None
