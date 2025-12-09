# A2A Multi-Agent Collaboration System

A sophisticated multi-agent collaboration system built with the **official A2A Python SDK** ([a2a-sdk](https://github.com/a2aproject/a2a-python)), implementing Google's Agent2Agent (A2A) protocol with Model Context Protocol (MCP) support and a beautiful, modern web interface.

## Features

🤖 **Multi-Agent System**
- Create and manage multiple AI agents
- **Built with official A2A SDK (a2a-sdk v0.3.20+)**
- Full A2A protocol compliance
- Support for various AI providers:
  - **Google Gemini**: 2.0 Flash, 1.5 Pro, 1.5 Flash (requires API key)
  - **OpenAI GPT**: GPT-4, GPT-4 Turbo, GPT-4o, GPT-3.5 Turbo (requires API key)
  - **Local LLMs** (no API key required):
    - **LM Studio**: Easy-to-use local LLM server
    - **LocalAI**: Self-hosted OpenAI-compatible API
    - **Ollama**: Local LLM runner with simple setup
    - **Text Generation WebUI**: Feature-rich web interface for local models
    - **Custom**: Any OpenAI-compatible API endpoint
- Customizable agent configurations
- **Separate provider options for local models** - no need for API keys when using local LLMs
- **Per-agent API key configuration** - different API keys for each cloud provider agent
- **Per-agent API endpoint configuration** for flexible LLM server setups

🤝 **Multi-Agent Collaboration (NEW!)**
- **Interactive collaboration UI** for coordinating multiple agents
- Select agents and define collaborative tasks through intuitive interface
- Real-time visualization of agent discussions and contributions
- Round-based collaboration with configurable iterations
- Coordinator agent selection for managing collaboration flow
- Complete conversation history with timestamps and metadata
- Inspired by CrewAI's multi-agent patterns and A2A protocol standards

🔧 **MCP Integration**
- Full Model Context Protocol support
- Connect agents to MCP servers
- Access tools and resources from MCP servers
- Seamless tool execution

💬 **Agent Communication**
- Real-time chat with individual agents
- A2A protocol-compliant messaging
- Conversation history tracking
- Support for streaming responses

🎨 **Beautiful UI**
- Modern, responsive design
- Dark theme optimized for extended use
- Intuitive agent management
- Real-time status updates
- **LM Studio URL configuration** with presets for popular local LLM servers

## Architecture

### Backend (Python/FastAPI)
- **A2A SDK**: Official Python SDK for Agent2Agent protocol
- **FastAPI**: High-performance async API server
- **Google GenAI**: LLM provider for Gemini models
- **OpenAI**: LLM provider for GPT models
- **MCP Client**: Model Context Protocol integration
- **Pydantic**: Data validation and settings management

### Frontend (React/Vite)
- **React 18**: Modern UI library
- **Vite**: Fast build tool and dev server
- **Lucide Icons**: Beautiful icon set
- **Axios**: HTTP client for API communication

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google API Key (for Gemini models) and/or OpenAI API Key (for GPT models)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd base-on-a2a-agent-system
```

2. **Set up the backend**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY and/or OPENAI_API_KEY
```

3. **Set up the frontend**
```bash
cd frontend
npm install
```

### Running the Application

1. **Start the backend server**
```bash
# From the root directory
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start the frontend dev server**
```bash
# From the frontend directory
cd frontend
npm run dev
```

3. **Access the application**
Open your browser and navigate to: `http://localhost:5173`

The backend API documentation is available at: `http://localhost:8000/docs`

## Usage

### Creating an Agent

1. Click the "Create Agent" button in the dashboard
2. Fill in the agent configuration:
   - **Name**: Give your agent a descriptive name
   - **Description**: Describe the agent's purpose
   - **Provider**: Choose from available providers:
     - **Google (Gemini)**: Google's Gemini models (requires Google API key)
     - **OpenAI (GPT)**: OpenAI's GPT models (requires OpenAI API key)
     - **LM Studio**: Local LM Studio server (no API key required)
     - **LocalAI**: Local LocalAI server (no API key required)
     - **Ollama**: Local Ollama server (no API key required)
     - **Text Generation WebUI**: Text Generation WebUI server (no API key required)
     - **Custom (OpenAI-compatible)**: Any custom OpenAI-compatible API (no API key required)
   - **Model**: Choose or enter a model name
     - For Google and OpenAI: Select from predefined models
     - For local providers: Enter your model name (e.g., llama2, mistral)
   - **API Key** (Optional): Configure per-agent API key
     - **Google API Key**: For Google (Gemini) provider only
     - **OpenAI API Key**: For OpenAI (GPT) provider only
     - Local providers don't require API keys
     - Leave empty to use global API key from `.env` file
     - Per-agent key overrides global setting
   - **API Base URL**: Configure API endpoint for local/custom providers
     - Automatically set to default for each provider
     - Can be customized as needed
   - **System Prompt**: Define the agent's behavior and personality
   - **Temperature**: Control randomness (0.0 - 2.0)
   - **Max Tokens**: Set output length limit (optional)

3. **Add MCP Servers** (optional):
   - Server Name: Identifier for the MCP server
   - Command: Executable command (e.g., `npx`, `python`)
   - Args: Additional command arguments

4. Click "Create Agent"

### Chatting with an Agent

1. Click the chat icon on an agent card
2. Type your message in the input field
3. Press Enter or click the send button
4. The agent will respond using the A2A protocol

### Multi-Agent Collaboration (NEW!)

Leverage the power of multiple agents working together on complex tasks:

**Using the UI:**
1. Create at least 2 agents with different capabilities or perspectives
2. Click the "Collaborate" button in the dashboard header
3. Select the agents you want to collaborate
4. Enter a task description (be specific about what you want to accomplish)
5. Optionally select a coordinator agent (or let the system auto-select)
6. Set the maximum number of collaboration rounds
7. Click "Start Collaboration"
8. Watch the agents work together, each contributing their expertise
9. Review the complete conversation history with all agent contributions

**Using the API:**

Use the API endpoint `/api/agents/collaborate` to start multi-agent collaboration:

```bash
curl -X POST http://localhost:8000/api/agents/collaborate \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["agent-id-1", "agent-id-2"],
    "task": "Design a web application architecture",
    "max_rounds": 5
  }'
```

**Collaboration Features:**
- **A2A Protocol Compliant**: Follows Google's Agent-to-Agent protocol standards
- **Flexible Coordination**: Choose a coordinator agent or auto-select
- **Round-based**: Control how many iterations agents collaborate
- **Full History**: View complete conversation with metadata and timestamps
- **Real-time Updates**: See agents working together in real-time

## API Documentation

### Agent Endpoints

- `POST /api/agents/` - Create a new agent
- `GET /api/agents/` - List all agents
- `GET /api/agents/{agent_id}` - Get agent details
- `PUT /api/agents/{agent_id}` - Update agent configuration
- `DELETE /api/agents/{agent_id}` - Delete an agent
- `POST /api/agents/message` - Send message to an agent
- `POST /api/agents/collaborate` - Start agent collaboration

### MCP Endpoints

- `GET /api/mcp/agents/{agent_id}/tools` - Get available tools
- `GET /api/mcp/agents/{agent_id}/resources` - Get available resources
- `POST /api/mcp/agents/{agent_id}/tools/{server_name}/{tool_name}` - Call a tool

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Required (at least one)
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI Configuration (Optional)
# Use this to connect to OpenAI-compatible APIs like LM Studio, LocalAI, etc.
# If not set, uses official OpenAI API endpoint
OPENAI_BASE_URL=http://localhost:1234/v1

HOST=0.0.0.0
PORT=8000
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./agents.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Using Local LLM Providers (LM Studio, LocalAI, Ollama, etc.)

The system now has dedicated provider options for local LLM servers, making it easier to use them without API keys:

#### Simple Method: Direct Provider Selection (Recommended)

1. **Start your local LLM server** (e.g., LM Studio, LocalAI, Ollama)
2. **Create or edit an agent** in the dashboard
3. **Select the appropriate provider**:
   - **LM Studio**: Default URL `http://localhost:1234/v1`
   - **LocalAI**: Default URL `http://localhost:8080/v1`
   - **Ollama**: Default URL `http://localhost:11434/v1`
   - **Text Generation WebUI**: Default URL `http://localhost:5000/v1`
   - **Custom (OpenAI-compatible)**: Enter your custom URL
4. **Enter your model name** (e.g., `llama2`, `mistral`, `codellama`)
5. **No API key required** - local providers work without authentication by default

This method is simpler and doesn't require you to configure API keys for local models.

#### Alternative Method: Using OpenAI Provider with Custom URL

You can still use the OpenAI provider with a custom base URL if needed:

1. **Start your local LLM server**
2. **Create an agent** and select "OpenAI (GPT)" as the provider
3. **Configure a dummy API key** (can be any string, e.g., "local")
4. **Set a custom base URL** in your `.env` file or per-agent configuration
5. **Enter your model name**

**Note**: The direct provider selection method (first method) is recommended as it's more intuitive and doesn't require configuring API keys.

**Supported OpenAI-Compatible Platforms:**
- LM Studio
- LocalAI
- Ollama (with OpenAI compatibility layer)
- Text Generation WebUI (with OpenAI extension)
- vLLM
- Any other service implementing OpenAI's API format

### Agent Configuration Schema

```json
{
  "name": "string",
  "description": "string",
  "provider": "google",
  "model": "gemini-2.0-flash-exp",
  "system_prompt": "string",
  "temperature": 0.7,
  "max_tokens": null,
  "openai_base_url": "http://localhost:1234/v1",
  "mcp_servers": [
    {
      "name": "string",
      "command": "string",
      "args": [],
      "env": {}
    }
  ],
  "capabilities": [],
  "metadata": {}
}
```

## MCP Integration

The system supports full MCP (Model Context Protocol) integration. You can connect agents to MCP servers to provide them with tools and resources.

### Example MCP Server Configuration

```json
{
  "name": "filesystem",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"],
  "env": {}
}
```

### Available MCP Servers

- **filesystem**: File system operations
- **github**: GitHub API integration
- **postgres**: PostgreSQL database access
- **sqlite**: SQLite database access
- **brave-search**: Web search capabilities
- And many more from the MCP ecosystem

## Development

### Project Structure

```
base-on-a2a-agent-system/
├── backend/
│   ├── agents/          # Agent implementation
│   ├── api/             # FastAPI routes
│   ├── config/          # Configuration
│   ├── mcp/             # MCP integration
│   ├── models/          # Data models
│   └── main.py          # Application entry point
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API services
│   │   └── styles/      # CSS styles
│   └── package.json
├── requirements.txt
└── README.md
```

### Building for Production

**Backend:**
```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run build
```

The built frontend will be in `frontend/dist` and can be served by the backend automatically.

## Technologies Used

- **Backend**: Python, FastAPI, **A2A SDK (official)**, Google GenAI SDK, OpenAI SDK, MCP, SQLAlchemy
- **Frontend**: React, Vite, Axios, Lucide Icons
- **AI**: Google Gemini models, OpenAI GPT models
- **Protocols**: Agent2Agent (A2A) Protocol, Model Context Protocol (MCP)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.

## Acknowledgments

- [A2A Project](https://a2a-protocol.org/) - Official Agent2Agent Protocol
- [A2A Python SDK](https://github.com/a2aproject/a2a-python) - Official Python SDK
- Model Context Protocol (MCP) community
- FastAPI framework
- React and Vite teams