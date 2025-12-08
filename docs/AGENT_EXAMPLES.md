# Example Agent Configurations

This directory contains example agent configurations for various use cases.

## General Purpose Assistant

```json
{
  "name": "General Assistant",
  "description": "A helpful AI assistant for general tasks",
  "model": "gemini-2.0-flash-exp",
  "system_prompt": "You are a helpful, knowledgeable AI assistant. Provide clear, accurate, and concise responses to user queries.",
  "temperature": 0.7,
  "max_tokens": null,
  "mcp_servers": [],
  "capabilities": ["general_knowledge", "task_assistance"],
  "metadata": {}
}
```

## Code Assistant

```json
{
  "name": "Code Assistant",
  "description": "AI agent specialized in software development",
  "model": "gemini-1.5-pro",
  "system_prompt": "You are an expert software engineer. Help users with code writing, debugging, and architecture design. Provide well-documented, efficient, and best-practice code.",
  "temperature": 0.3,
  "max_tokens": null,
  "mcp_servers": [
    {
      "name": "github",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    }
  ],
  "capabilities": ["code_generation", "debugging", "code_review"],
  "metadata": {
    "specialization": "full-stack"
  }
}
```

## Research Assistant

```json
{
  "name": "Research Assistant",
  "description": "AI agent for research and information gathering",
  "model": "gemini-1.5-pro",
  "system_prompt": "You are a research assistant. Help users find, analyze, and synthesize information. Provide well-researched, factual responses with sources when possible.",
  "temperature": 0.5,
  "max_tokens": null,
  "mcp_servers": [
    {
      "name": "brave_search",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your_api_key_here"
      }
    }
  ],
  "capabilities": ["web_search", "information_synthesis", "fact_checking"],
  "metadata": {
    "focus_areas": ["technology", "science"]
  }
}
```

## Data Analyst

```json
{
  "name": "Data Analyst",
  "description": "AI agent for data analysis and insights",
  "model": "gemini-1.5-pro",
  "system_prompt": "You are a data analyst. Help users understand data, create analyses, and generate insights. Explain statistical concepts clearly.",
  "temperature": 0.4,
  "max_tokens": null,
  "mcp_servers": [
    {
      "name": "sqlite",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "/path/to/database.db"],
      "env": {}
    }
  ],
  "capabilities": ["data_analysis", "statistics", "visualization"],
  "metadata": {
    "tools": ["sql", "statistics"]
  }
}
```

## Creative Writer

```json
{
  "name": "Creative Writer",
  "description": "AI agent for creative writing and storytelling",
  "model": "gemini-2.0-flash-exp",
  "system_prompt": "You are a creative writer. Help users craft compelling stories, poems, and creative content. Be imaginative and engaging while maintaining coherence.",
  "temperature": 1.0,
  "max_tokens": null,
  "mcp_servers": [],
  "capabilities": ["creative_writing", "storytelling", "brainstorming"],
  "metadata": {
    "styles": ["fiction", "poetry", "scripts"]
  }
}
```

## Customer Support Agent

```json
{
  "name": "Support Agent",
  "description": "AI agent for customer support",
  "model": "gemini-2.0-flash-exp",
  "system_prompt": "You are a friendly customer support agent. Help users with their questions and issues professionally and empathetically. Always be patient and clear.",
  "temperature": 0.6,
  "max_tokens": null,
  "mcp_servers": [],
  "capabilities": ["customer_service", "troubleshooting", "product_knowledge"],
  "metadata": {
    "tone": "friendly_professional"
  }
}
```

## Usage

To use these configurations:

1. Copy the JSON configuration you want to use
2. In the web interface, click "Create Agent"
3. Manually fill in the form fields with the values from the JSON
4. Or use the API directly:

```bash
curl -X POST http://localhost:8000/api/agents/ \
  -H "Content-Type: application/json" \
  -d @agent-config.json
```

## Notes

- Replace placeholder values like API keys and tokens with your actual credentials
- Adjust `temperature` based on your needs (lower = more focused, higher = more creative)
- Add or remove MCP servers based on your requirements
- Customize `system_prompt` to match your specific use case
