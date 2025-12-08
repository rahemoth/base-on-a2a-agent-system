# Quick Start Guide

This guide will help you get the A2A Multi-Agent System up and running in minutes.

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Google API Key (get one from [Google AI Studio](https://aistudio.google.com/app/apikey))

## Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd base-on-a2a-agent-system
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your_actual_api_key_here
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

## Running the Application

### Option 1: Run Both Servers (Recommended for Development)

**Terminal 1 - Backend:**
```bash
python run_backend.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

### Option 2: Production Build

```bash
# Build frontend
cd frontend
npm run build
cd ..

# Run backend (serves frontend automatically)
python run_backend.py
```

Then open http://localhost:8000 in your browser.

## First Steps

### 1. Create Your First Agent

1. Click "Create Agent" button
2. Fill in the basic information:
   - **Name**: e.g., "My Assistant"
   - **Description**: e.g., "A helpful AI assistant"
   - **Model**: Select "Gemini 2.0 Flash" (default)
   - **System Prompt**: e.g., "You are a helpful AI assistant"
   - **Temperature**: 0.7 (default is fine)

3. Click "Create Agent"

### 2. Chat with Your Agent

1. Click the chat icon on your agent card
2. Type a message and press Enter
3. Get AI-powered responses!

### 3. Add MCP Servers (Optional)

To give your agent additional capabilities:

1. Click "Configure" on an agent
2. Scroll to "MCP Servers" section
3. Add a server:
   - **Name**: e.g., "filesystem"
   - **Command**: e.g., "npx"
   - **Args**: Add args like "-y @modelcontextprotocol/server-filesystem /path/to/dir"
4. Click "Add Server"
5. Click "Update Agent"

## Example Configurations

### General Assistant
```
Name: General Assistant
Model: Gemini 2.0 Flash
Temperature: 0.7
System Prompt: You are a helpful, knowledgeable AI assistant.
```

### Code Helper
```
Name: Code Helper
Model: Gemini 1.5 Pro
Temperature: 0.3
System Prompt: You are an expert software engineer. Help with code writing and debugging.
```

### Creative Writer
```
Name: Creative Writer
Model: Gemini 2.0 Flash
Temperature: 1.0
System Prompt: You are a creative writer. Help craft compelling stories and content.
```

## API Usage

The system also provides a REST API:

```bash
# List all agents
curl http://localhost:8000/api/agents/

# Create an agent
curl -X POST http://localhost:8000/api/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "name": "API Agent",
      "description": "Created via API",
      "model": "gemini-2.0-flash-exp",
      "temperature": 0.7
    }
  }'

# Send a message
curl -X POST http://localhost:8000/api/agents/message \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-id-here",
    "message": "Hello, how are you?",
    "stream": false
  }'
```

## Troubleshooting

### Backend won't start
- Check that Python 3.10+ is installed: `python --version`
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check that your Google API key is set in `.env`

### Frontend won't start
- Check that Node.js 18+ is installed: `node --version`
- Verify dependencies installed: `cd frontend && npm install`
- Try clearing cache: `rm -rf frontend/node_modules && cd frontend && npm install`

### Agent returns errors
- Verify your Google API key is valid
- Check backend logs for error messages
- Ensure you have internet connectivity

### MCP servers not working
- Verify the command is available (e.g., `npx --version`)
- Check that environment variables are set correctly
- Look at backend console for MCP connection errors

## Next Steps

- Read the [full README](../README.md) for detailed information
- Check [Agent Examples](AGENT_EXAMPLES.md) for more configurations
- Review [MCP Integration Guide](MCP_GUIDE.md) for advanced MCP usage
- Explore the API at http://localhost:8000/docs

## Getting Help

If you encounter issues:
1. Check the logs in the terminal
2. Review the documentation
3. Open an issue on GitHub

Happy agent building! 🤖✨
