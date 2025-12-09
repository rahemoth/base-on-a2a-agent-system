# Multi-Agent Collaboration Examples

This document provides practical examples of using the new multi-agent collaboration features.

## Example 1: Using LM Studio with Custom Agents

### Step 1: Start LM Studio
1. Download and install LM Studio from https://lmstudio.ai/
2. Load a model (e.g., Llama 2 7B, Mistral 7B)
3. Start the local server (usually on port 1234)

### Step 2: Create Agents with LM Studio

**Agent 1: Software Architect**
```json
{
  "name": "Software Architect",
  "description": "Expert in system design and architecture",
  "provider": "openai",
  "model": "llama-2-7b-chat",
  "openai_base_url": "http://localhost:1234",
  "system_prompt": "You are an experienced software architect specializing in scalable systems. Focus on architectural patterns, design principles, and best practices.",
  "temperature": 0.7
}
```

**Agent 2: Backend Developer**
```json
{
  "name": "Backend Developer",
  "description": "Expert in backend development and APIs",
  "provider": "openai",
  "model": "llama-2-7b-chat",
  "openai_base_url": "http://localhost:1234",
  "system_prompt": "You are a skilled backend developer with expertise in API design, databases, and server-side logic. Focus on implementation details and code structure.",
  "temperature": 0.7
}
```

**Agent 3: Frontend Developer**
```json
{
  "name": "Frontend Developer",
  "description": "Expert in UI/UX and frontend technologies",
  "provider": "openai",
  "model": "llama-2-7b-chat",
  "openai_base_url": "http://localhost:1234",
  "system_prompt": "You are a creative frontend developer specializing in modern UI frameworks and user experience. Focus on interface design and client-side implementation.",
  "temperature": 0.8
}
```

**Note**: Base URLs should NOT include `/v1` suffix - the OpenAI SDK adds it automatically.
```

### Step 3: Start Collaboration

Use the UI:
1. Click "Collaborate" button in the dashboard
2. Select all three agents
3. Enter task: "Design and plan a real-time chat application with user presence, message history, and file sharing"
4. Select "Software Architect" as coordinator
5. Set max rounds to 5
6. Click "Start Collaboration"

Or use the API:
```bash
curl -X POST http://localhost:8000/api/agents/collaborate \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["agent-id-1", "agent-id-2", "agent-id-3"],
    "task": "Design and plan a real-time chat application with user presence, message history, and file sharing",
    "coordinator_agent": "agent-id-1",
    "max_rounds": 5
  }'
```

## Example 2: Mixing Cloud and Local Models

You can create a team where some agents use cloud models and others use local models:

**Agent 1: Research Agent (Google Gemini)**
```json
{
  "name": "Research Agent",
  "provider": "google",
  "model": "gemini-2.0-flash-exp",
  "system_prompt": "You are a research specialist. Analyze requirements and gather information."
}
```

**Agent 2: Code Generator (LM Studio)**
```json
{
  "name": "Code Generator",
  "provider": "openai",
  "model": "codellama-7b",
  "openai_base_url": "http://localhost:1234",
  "system_prompt": "You are a code generation specialist. Write clean, efficient code."
}
```

**Agent 3: Code Reviewer (OpenAI GPT-4)**
```json
{
  "name": "Code Reviewer",
  "provider": "openai",
  "model": "gpt-4",
  "system_prompt": "You are a code review expert. Find issues and suggest improvements."
}
```

This hybrid approach allows you to:
- Use powerful cloud models for complex reasoning (Gemini, GPT-4)
- Use local models for privacy-sensitive tasks
- Optimize costs by using local models where appropriate

## Example 3: Domain-Specific Collaboration

**Marketing Campaign Planning**

Agents:
1. **Market Analyst** - Analyzes market trends and competitor strategies
2. **Content Strategist** - Plans content calendar and messaging
3. **Social Media Manager** - Optimizes for different platforms
4. **Performance Analyst** - Tracks KPIs and suggests improvements

Task: "Plan a product launch campaign for a new AI-powered productivity tool"

## Example 4: Using Different Local LLM Servers

You can use different local servers for different agents:

**Agent with LocalAI:**
```json
{
  "name": "LocalAI Agent",
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "openai_base_url": "http://localhost:8080/v1"
}
```

**Agent with Ollama:**
```json
{
  "name": "Ollama Agent",
  "provider": "openai",
  "model": "llama2",
  "openai_base_url": "http://localhost:11434/v1"
}
```

**Agent with Text Generation WebUI:**
```json
{
  "name": "WebUI Agent",
  "provider": "openai",
  "model": "custom-model",
  "openai_base_url": "http://localhost:5000/v1"
}
```

## Tips for Effective Multi-Agent Collaboration

1. **Define Clear Roles**: Give each agent a specific role and expertise area in their system prompt
2. **Choose the Right Coordinator**: Select an agent with broad knowledge to coordinate the discussion
3. **Adjust Max Rounds**: Start with 3-5 rounds, increase if needed for complex tasks
4. **Mix Model Types**: Combine different models for diverse perspectives
5. **Review Results**: The conversation history shows how agents collaborated - use it to improve prompts
6. **Temperature Settings**: 
   - Use lower temperature (0.3-0.5) for analytical agents
   - Use higher temperature (0.7-0.9) for creative agents

## Troubleshooting

### LM Studio Connection Issues
- Ensure LM Studio server is running (check the "Server" tab)
- Verify the port number (default is 1234)
- Test with: `curl http://localhost:1234/v1/models`
- Check firewall settings

### Model Not Responding
- Verify the model is loaded in your local server
- Check the model name matches what your server expects
- Review server logs for errors

### Collaboration Not Starting
- Ensure you have at least 2 agents selected
- Check that all agents are properly configured
- Verify API keys are set for cloud providers
- Review browser console for JavaScript errors

## Advanced: A2A Protocol Compliance

This system implements Google's A2A (Agent-to-Agent) protocol, which means:
- Agents communicate using standardized message formats
- Context is preserved across collaboration rounds
- Metadata tracks agent contributions
- Compatible with other A2A-compliant systems

For more details, see: https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
