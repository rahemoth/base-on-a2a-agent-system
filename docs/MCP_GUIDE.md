# MCP Integration Guide

This guide explains how to integrate Model Context Protocol (MCP) servers with your A2A agents.

## What is MCP?

The Model Context Protocol (MCP) is an open protocol that enables AI applications to securely connect to external data sources and tools. MCP servers provide:

- **Tools**: Functions that agents can call
- **Resources**: Data sources agents can access
- **Prompts**: Pre-defined prompt templates

## Setting Up MCP Servers

### 1. Available MCP Servers

Here are some popular MCP servers you can use:

#### Filesystem Server
Access local files and directories.

```json
{
  "name": "filesystem",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"],
  "env": {}
}
```

#### GitHub Server
Interact with GitHub repositories.

```json
{
  "name": "github",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token"
  }
}
```

#### PostgreSQL Server
Query PostgreSQL databases.

```json
{
  "name": "postgres",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/db"],
  "env": {}
}
```

#### SQLite Server
Access SQLite databases.

```json
{
  "name": "sqlite",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sqlite", "/path/to/database.db"],
  "env": {}
}
```

#### Brave Search Server
Web search capabilities.

```json
{
  "name": "brave_search",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-brave-search"],
  "env": {
    "BRAVE_API_KEY": "your_brave_api_key"
  }
}
```

#### Puppeteer Server
Web scraping and browser automation.

```json
{
  "name": "puppeteer",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
  "env": {}
}
```

### 2. Custom MCP Servers

You can also create custom MCP servers. Here's a Python example:

```python
from mcp.server import Server
from mcp.types import Tool

app = Server("my-custom-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="my_tool",
            description="Does something useful",
            inputSchema={
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "my_tool":
        return {"result": f"Processed: {arguments['param']}"}
```

Run it:
```bash
python my_server.py
```

Then configure it in your agent:
```json
{
  "name": "custom",
  "command": "python",
  "args": ["my_server.py"],
  "env": {}
}
```

## Using MCP in Agents

### Step 1: Create Agent with MCP

When creating an agent, add MCP server configurations:

```javascript
const agentConfig = {
  name: "Research Agent",
  description: "Agent with web search capabilities",
  model: "gemini-2.0-flash-exp",
  system_prompt: "You are a research assistant with web search capabilities.",
  temperature: 0.7,
  mcp_servers: [
    {
      name: "brave_search",
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
      env: {
        BRAVE_API_KEY: "your_api_key"
      }
    }
  ]
};
```

### Step 2: Agent Automatically Uses Tools

When you chat with the agent, it will automatically detect when to use MCP tools based on the conversation context.

Example:
```
User: "Search for recent developments in quantum computing"
Agent: [Uses brave_search tool automatically]
       "Based on recent searches, here are the key developments..."
```

### Step 3: View Available Tools

Check what tools are available for an agent:

```bash
curl http://localhost:8000/api/mcp/agents/{agent_id}/tools
```

Response:
```json
{
  "tools": {
    "brave_search": [
      {
        "name": "brave_web_search",
        "description": "Search the web using Brave Search",
        "input_schema": {...}
      }
    ]
  }
}
```

### Step 4: Manually Call Tools (Optional)

You can also manually call MCP tools:

```bash
curl -X POST http://localhost:8000/api/mcp/agents/{agent_id}/tools/brave_search/brave_web_search \
  -H "Content-Type: application/json" \
  -d '{"query": "quantum computing 2024"}'
```

## Best Practices

### 1. Security

- Never commit API keys to version control
- Use environment variables for sensitive data
- Restrict filesystem access to necessary directories only
- Use read-only database connections when possible

### 2. Performance

- Limit the number of MCP servers per agent (3-5 recommended)
- Use caching when possible
- Monitor tool call frequency
- Set timeouts for long-running operations

### 3. Error Handling

- MCP servers may fail - agents will continue without them
- Check MCP server logs for connection issues
- Test MCP servers independently before adding to agents

### 4. Tool Selection

- Choose tools relevant to the agent's purpose
- Don't overwhelm agents with too many tools
- Document what each tool does for users

## Troubleshooting

### MCP Server Not Connecting

1. Check that the command is installed:
   ```bash
   npx -y @modelcontextprotocol/server-filesystem --help
   ```

2. Verify environment variables are set correctly

3. Check server logs in the backend console

### Tools Not Being Used

1. Make system prompt clear about tool usage
2. Ask questions that clearly need tool usage
3. Check tool availability via the API

### Performance Issues

1. Reduce number of MCP servers
2. Use lighter-weight tools when possible
3. Implement caching for frequently accessed data

## Advanced Usage

### Multi-Server Setup

Agents can use multiple MCP servers simultaneously:

```json
{
  "mcp_servers": [
    {
      "name": "github",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "token"}
    },
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
      "env": {}
    }
  ]
}
```

The agent can now use both GitHub API and filesystem operations!

### Resource Access

Some MCP servers provide resources (not just tools):

```bash
curl http://localhost:8000/api/mcp/agents/{agent_id}/resources
```

Resources can include:
- Files and documents
- Database schemas
- API documentation
- Configuration data

## More Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [MCP Server Registry](https://github.com/modelcontextprotocol/servers)
- [Creating Custom Servers](https://modelcontextprotocol.io/docs/building-servers)
