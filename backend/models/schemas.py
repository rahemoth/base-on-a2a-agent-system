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
    GOOGLE = "google"
    OPENAI = "openai"
    LMSTUDIO = "lmstudio"
    LOCALAI = "localai"
    OLLAMA = "ollama"
    TEXTGEN_WEBUI = "textgen-webui"
    CUSTOM = "custom"


class MCPServerConfig(BaseModel):
    """MCP Server configuration"""
    name: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}


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
