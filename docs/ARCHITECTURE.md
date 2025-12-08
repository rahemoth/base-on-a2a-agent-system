# Architecture Overview

This document provides a detailed overview of the A2A Multi-Agent System architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                     │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐ │
│  │Dashboard │  │Agent Card│  │Config Modal│  │Chat Modal  │ │
│  └─────┬────┘  └────┬─────┘  └─────┬─────┘  └─────┬──────┘ │
│        │            │               │               │         │
│        └────────────┴───────────────┴───────────────┘         │
│                          │                                    │
│                    API Service                                │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTP/REST
┌──────────────────────────┼───────────────────────────────────┐
│                    Backend (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    API Layer                             │ │
│  │  ┌──────────────┐         ┌─────────────┐              │ │
│  │  │ Agent Routes │         │ MCP Routes  │              │ │
│  │  └──────┬───────┘         └──────┬──────┘              │ │
│  └─────────┼────────────────────────┼────────────────────┘ │
│            │                        │                        │
│  ┌─────────▼────────────────────────▼────────────────────┐ │
│  │              Agent Manager                             │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │              A2A Agent                           │ │ │
│  │  │  ┌─────────────┐  ┌─────────────┐              │ │ │
│  │  │  │Configuration│  │Conversation │              │ │ │
│  │  │  └─────────────┘  └─────────────┘              │ │ │
│  │  └──────────┬──────────────────┬──────────────────┘ │ │
│  └─────────────┼──────────────────┼────────────────────┘ │
│                │                  │                        │
│  ┌─────────────▼──────────┐  ┌───▼───────────────────┐   │
│  │    Google GenAI         │  │   MCP Manager         │   │
│  │    (A2A Protocol)       │  │                        │   │
│  └─────────────────────────┘  └───┬───────────────────┘   │
└───────────────────────────────────┼───────────────────────┘
                                    │
                    ┌───────────────┼──────────────┐
                    │               │              │
              ┌─────▼─────┐  ┌─────▼─────┐  ┌────▼──────┐
              │MCP Server │  │MCP Server │  │MCP Server │
              │(Filesystem)  │(GitHub)   │  │(Search)   │
              └───────────┘  └───────────┘  └───────────┘
```

## Component Details

### Frontend Layer

#### 1. Dashboard (`frontend/src/pages/Dashboard.jsx`)
- Main application view
- Lists all agents
- Manages agent lifecycle (create, update, delete)
- Coordinates interactions with modals

#### 2. Agent Card (`frontend/src/components/AgentCard.jsx`)
- Displays agent information
- Shows agent status (idle, busy, error, offline)
- Provides quick actions (chat, configure, delete)

#### 3. Configuration Modal (`frontend/src/components/AgentConfigModal.jsx`)
- Agent creation and editing interface
- Basic configuration (name, model, prompts)
- MCP server management
- Form validation

#### 4. Chat Modal (`frontend/src/components/ChatModal.jsx`)
- Real-time chat interface
- Message history display
- Streaming response support
- Context management

#### 5. API Service (`frontend/src/services/api.js`)
- Centralized API client
- Handles HTTP requests to backend
- Error handling and response parsing

### Backend Layer

#### 1. FastAPI Application (`backend/main.py`)
- Main application entry point
- CORS configuration
- Route registration
- Lifespan management (startup/shutdown)

#### 2. API Routes

**Agent Routes** (`backend/api/agents.py`)
- `POST /api/agents/` - Create agent
- `GET /api/agents/` - List agents
- `GET /api/agents/{id}` - Get agent details
- `PUT /api/agents/{id}` - Update agent
- `DELETE /api/agents/{id}` - Delete agent
- `POST /api/agents/message` - Send message to agent
- `POST /api/agents/collaborate` - Multi-agent collaboration

**MCP Routes** (`backend/api/mcp.py`)
- `GET /api/mcp/agents/{id}/tools` - List available tools
- `GET /api/mcp/agents/{id}/resources` - List available resources
- `POST /api/mcp/agents/{id}/tools/{server}/{tool}` - Call tool

#### 3. Agent Manager (`backend/agents/manager.py`)
- Manages all agent instances
- Agent lifecycle management
- Message routing
- Collaboration coordination

#### 4. A2A Agent (`backend/agents/a2a_agent.py`)
- Core agent implementation
- Google GenAI integration
- A2A protocol implementation
- Message processing
- Tool execution via MCP
- Conversation history management

#### 5. MCP Integration (`backend/mcp/client.py`)
- MCP client implementation
- Server connection management
- Tool discovery and execution
- Resource access
- Multi-server support

#### 6. Data Models (`backend/models/`)
- Pydantic schemas for validation
- Database models (SQLAlchemy)
- Type definitions

### External Integrations

#### 1. Google GenAI (A2A Protocol)
- Primary LLM provider
- Supports Gemini models
- Function calling capabilities
- Streaming responses
- Context management

#### 2. MCP Servers
- Filesystem server - File operations
- GitHub server - Repository interactions
- Database servers - SQL queries
- Search servers - Web search
- Custom servers - Extensible

## Data Flow

### Agent Creation Flow

```
User → Dashboard → AgentConfigModal
  ↓
  Fill form with config
  ↓
  Submit → API Service
  ↓
  POST /api/agents/
  ↓
  Agent Manager → Create A2AAgent
  ↓
  Initialize with Google GenAI
  ↓
  Connect MCP Servers (if configured)
  ↓
  Return AgentResponse
  ↓
  Update Dashboard
```

### Chat Flow

```
User → ChatModal → Type message
  ↓
  Submit → API Service
  ↓
  POST /api/agents/message
  ↓
  Agent Manager → Get agent
  ↓
  A2AAgent.send_message()
  ↓
  Build context from history
  ↓
  Get available MCP tools
  ↓
  Generate content via Google GenAI
  ↓
  [If function call] → Execute via MCP
  ↓
  [Send result back] → Generate final response
  ↓
  Return response
  ↓
  Display in ChatModal
```

### MCP Tool Execution Flow

```
Agent receives message requiring tool
  ↓
  A2AAgent.get_tools() → MCP Manager
  ↓
  List tools from all connected servers
  ↓
  Convert to GenAI tool format
  ↓
  GenAI generates function call
  ↓
  A2AAgent._execute_tool()
  ↓
  Parse server and tool name
  ↓
  MCP Client → Call tool on server
  ↓
  Return tool result
  ↓
  Send result back to GenAI
  ↓
  Generate natural language response
```

## Key Design Decisions

### 1. Separation of Concerns
- Frontend: Pure presentation and user interaction
- Backend: Business logic and AI orchestration
- MCP: External tool and resource integration

### 2. Async/Await Pattern
- All agent operations are asynchronous
- Non-blocking I/O for better performance
- Supports streaming responses

### 3. MCP as Plugin System
- Agents can dynamically add capabilities
- Clean separation from core logic
- Easy to add new tools without code changes

### 4. Stateless API
- Each request is independent
- Agent state managed in memory (can be persisted)
- Scales horizontally

### 5. Type Safety
- Pydantic for runtime validation
- Clear contracts between components
- Better developer experience

## Security Considerations

### 1. API Keys
- Stored in environment variables
- Never exposed to frontend
- Required for backend operations

### 2. Input Validation
- Pydantic models validate all inputs
- Prevents injection attacks
- Type checking at runtime

### 3. CORS
- Configurable allowed origins
- Prevents unauthorized access
- Production-ready settings

### 4. MCP Security
- Sandboxed tool execution
- Limited filesystem access
- Environment variable isolation

## Scalability

### Current Architecture
- Single process, in-memory state
- Suitable for development and small deployments
- Quick startup and simple operations

### Scaling Options

**Horizontal Scaling:**
- Add database for persistent state
- Use Redis for agent session management
- Load balancer for multiple backend instances

**Vertical Scaling:**
- Increase resources for more concurrent agents
- Better hardware for faster responses

**Distributed Architecture:**
- Message queue (RabbitMQ/Redis) for agent communication
- Separate MCP server instances
- Distributed tracing for monitoring

## Future Enhancements

1. **Persistent Storage**
   - PostgreSQL for agent configurations
   - Conversation history persistence
   - User management

2. **Advanced Collaboration**
   - Dynamic task decomposition
   - Hierarchical agent structures
   - Voting and consensus mechanisms

3. **Monitoring**
   - Usage analytics
   - Performance metrics
   - Error tracking

4. **Enhanced MCP**
   - MCP server marketplace
   - Hot-reload for MCP servers
   - Server health monitoring

5. **Multi-Model Support**
   - Anthropic Claude integration
   - OpenAI models
   - Local models (Ollama)

## Performance Considerations

- **Caching**: Tool definitions and resources
- **Connection Pooling**: MCP server connections
- **Lazy Loading**: Frontend components
- **Streaming**: Large responses
- **Rate Limiting**: API protection
