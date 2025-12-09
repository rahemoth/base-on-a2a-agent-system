# Migration to Official A2A SDK

## Overview

This document describes the migration from a custom A2A protocol implementation to using the official A2A Python SDK (`a2a-sdk`).

## What Changed

### Before (Custom Implementation)
- Custom A2A protocol implementation built on top of Google GenAI
- Direct integration with LLM providers without A2A abstraction
- No standardized agent cards or protocol compliance

### After (Official SDK)
- Official `a2a-sdk` v0.3.20+ from https://github.com/a2aproject/a2a-python
- Full A2A protocol v0.3.0 compliance
- Standardized agent cards, JSON-RPC endpoints, and task management
- Better interoperability with other A2A systems

## New Architecture

### Key Components

1. **LLMAgentExecutor** (`backend/agents/a2a_executor.py`)
   - Implements the `AgentExecutor` interface from A2A SDK
   - Integrates LLM providers (Google GenAI, OpenAI)
   - Handles message processing and response generation
   - Supports MCP tool integration

2. **A2AAgentManager** (`backend/agents/a2a_manager.py`)
   - Manages agent lifecycle using A2A SDK components
   - Creates and configures `DefaultRequestHandler` instances
   - Manages task stores and queue managers
   - Generates A2A-compliant agent cards

3. **A2A Protocol Endpoints** (`backend/api/agents_a2a.py`)
   - Standard A2A endpoints:
     - `GET /{agent_id}/.well-known/agent-card.json` - Agent discovery
     - `POST /{agent_id}/a2a` - JSON-RPC protocol endpoint
     - `GET /{agent_id}/tasks/{task_id}` - Task information
   - Legacy endpoints for backward compatibility

## A2A Protocol Endpoints

### Agent Card Discovery
```
GET /api/agents/{agent_id}/.well-known/agent-card.json
```
Returns the agent's capability card in A2A format.

### JSON-RPC Protocol
```
POST /api/agents/{agent_id}/a2a
```
Handles A2A protocol methods:
- `sendMessage` - Send a message to the agent
- `getTask` - Get task information
- `cancelTask` - Cancel a running task

### Task Management
```
GET /api/agents/{agent_id}/tasks/{task_id}
```
Retrieve information about a specific task.

## Benefits

1. **Standards Compliance**: Full adherence to A2A protocol specification
2. **Interoperability**: Can communicate with any A2A-compliant system
3. **Official Support**: Updates and improvements from the A2A project
4. **Better Structure**: Clean separation of concerns using SDK abstractions
5. **Community**: Access to examples, tools, and community resources

## Backward Compatibility

All existing API endpoints remain functional:
- `POST /api/agents/` - Create agent
- `GET /api/agents/` - List agents
- `GET /api/agents/{id}` - Get agent
- `PUT /api/agents/{id}` - Update agent
- `DELETE /api/agents/{id}` - Delete agent
- `POST /api/agents/message` - Send message (legacy)

The frontend continues to work without any changes.

## Testing with A2A Inspector

You can validate your agents using the official A2A inspector:
```bash
git clone https://github.com/a2aproject/a2a-inspector
cd a2a-inspector
# Follow setup instructions
```

Point the inspector to your agent's card URL:
```
http://localhost:8000/api/agents/{agent_id}/.well-known/agent-card.json
```

## Dependencies

New dependency added:
```
a2a-sdk[http-server]>=0.3.20
```

This includes:
- Core A2A SDK
- FastAPI integration
- All protocol types and utilities

## Security Improvements

1. HTTPS protocol for production deployments
2. Sanitized error messages to prevent information leakage
3. Proper error logging for debugging
4. CodeQL security scan passed with 0 vulnerabilities

## Future Enhancements

With the official SDK, we can now easily add:
- Streaming responses
- Push notifications
- Advanced task management
- Multi-turn conversations with context
- Integration with other A2A agents and services

## References

- **A2A Protocol**: https://a2a-protocol.org/
- **A2A Python SDK**: https://github.com/a2aproject/a2a-python
- **A2A Samples**: https://github.com/a2aproject/a2a-samples
- **PyPI Package**: https://pypi.org/project/a2a-sdk/
