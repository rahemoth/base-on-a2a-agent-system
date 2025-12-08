# A2A Multi-Agent Collaboration System

A sophisticated multi-agent collaboration system built on Google's A2A (Agent-to-Agent) protocol with Model Context Protocol (MCP) support and a beautiful, modern web interface.

## Features

🤖 **Multi-Agent System**
- Create and manage multiple AI agents
- Based on Google's A2A protocol
- Support for various AI models:
  - **Google Gemini**: 2.0 Flash, 1.5 Pro, 1.5 Flash
  - **OpenAI GPT**: GPT-4, GPT-4 Turbo, GPT-4o, GPT-3.5 Turbo
- Customizable agent configurations

🔧 **MCP Integration**
- Full Model Context Protocol support
- Connect agents to MCP servers
- Access tools and resources from MCP servers
- Seamless tool execution

💬 **Agent Communication**
- Real-time chat with individual agents
- Multi-agent collaboration on tasks
- Conversation history tracking
- Streaming responses

🎨 **Beautiful UI**
- Modern, responsive design
- Dark theme optimized for extended use
- Intuitive agent management
- Real-time status updates

## Architecture

### Backend (Python/FastAPI)
- **FastAPI**: High-performance async API server
- **Google GenAI**: A2A protocol implementation
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
   - **Provider**: Choose between Google (Gemini) or OpenAI (GPT)
   - **Model**: Choose a model from the selected provider
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

### Agent Collaboration

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
HOST=0.0.0.0
PORT=8000
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./agents.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

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

- **Backend**: Python, FastAPI, Google GenAI SDK, OpenAI SDK, MCP, SQLAlchemy
- **Frontend**: React, Vite, Axios, Lucide Icons
- **AI**: Google Gemini models, OpenAI GPT models, A2A protocol
- **Protocol**: Model Context Protocol (MCP)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.

## Acknowledgments

- Google's A2A (Agent-to-Agent) protocol
- Model Context Protocol (MCP) community
- FastAPI framework
- React and Vite teams