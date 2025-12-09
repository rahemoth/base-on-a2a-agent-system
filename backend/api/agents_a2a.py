"""
FastAPI routes for A2A-compliant agent management and A2A protocol endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional
import json

from a2a import types
from backend.models import (
    AgentCreate,
    AgentResponse,
    AgentMessage,
    AgentUpdate,
    AgentCollaboration,
)
from backend.agents.a2a_manager import a2a_agent_manager

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ============================================================================
# Legacy API Endpoints (for backward compatibility with existing frontend)
# ============================================================================

@router.post("/", response_model=AgentResponse)
async def create_agent(agent_create: AgentCreate):
    """Create a new agent"""
    try:
        agent = await a2a_agent_manager.create_agent(agent_create.config)
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[AgentResponse])
async def list_agents():
    """List all agents"""
    try:
        agents = await a2a_agent_manager.list_agents()
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent by ID"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get metadata
    metadata = a2a_agent_manager.agent_metadata.get(agent_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Agent metadata not found")
    
    from backend.models import AgentStatus
    return AgentResponse(
        id=agent_id,
        config=metadata["config"],
        status=AgentStatus.IDLE,
        created_at=metadata["created_at"],
        updated_at=metadata["updated_at"]
    )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent_update: AgentUpdate):
    """Update agent configuration"""
    if not agent_update.config:
        raise HTTPException(status_code=400, detail="Config is required for update")
    
    agent = await a2a_agent_manager.update_agent(agent_id, agent_update.config)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    success = await a2a_agent_manager.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"message": "Agent deleted successfully"}


@router.post("/message")
async def send_message(agent_message: AgentMessage):
    """Send a message to an agent (legacy endpoint)"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.debug(f"Received message for agent {agent_message.agent_id}")
    
    try:
        # Use A2A manager to send message
        response = await a2a_agent_manager.send_message(
            agent_message.agent_id,
            agent_message.message,
        )
        
        # Extract text from response
        # Note: response.parts contains Part objects which are RootModel wrappers
        # We need to access part.root to get the actual TextPart/FilePart/DataPart
        text_response = ""
        for part in response.parts:
            actual_part = part.root if hasattr(part, 'root') else part
            if isinstance(actual_part, types.TextPart):
                text_response += actual_part.text
        
        logger.debug(f"Returning response to client")
        
        return {"response": text_response}
    except ValueError as e:
        logger.error(f"Agent not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collaborate")
async def collaborate(collaboration: AgentCollaboration):
    """Start a collaboration between multiple agents"""
    try:
        result = await a2a_agent_manager.collaborate_agents(
            agent_ids=collaboration.agents,
            task=collaboration.task,
            coordinator_id=collaboration.coordinator_agent,
            max_rounds=collaboration.max_rounds
        )
        
        return {
            "collaboration_history": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# A2A Protocol Endpoints
# ============================================================================

@router.get("/{agent_id}/.well-known/agent-card.json")
async def get_agent_card(agent_id: str):
    """Get the agent's A2A card (A2A protocol endpoint)"""
    agent_card = a2a_agent_manager.get_agent_card(agent_id)
    if not agent_card:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent_card.model_dump(exclude_none=True)


@router.post("/{agent_id}/a2a")
async def a2a_jsonrpc_endpoint(agent_id: str, request: Request):
    """
    A2A JSON-RPC endpoint for agent communication
    This endpoint follows the A2A protocol specification
    """
    handler = a2a_agent_manager.get_request_handler(agent_id)
    if not handler:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        # Get raw JSON body
        body = await request.json()
        
        # Parse as JSON-RPC request
        method = body.get("method")
        
        if method == "sendMessage":
            # Parse as SendMessageRequest
            req = types.SendMessageRequest(**body)
            response = await handler.send_message(req)
            return response.model_dump(exclude_none=True)
        
        elif method == "getTask":
            # Parse as GetTaskRequest
            req = types.GetTaskRequest(**body)
            response = await handler.get_task(req)
            return response.model_dump(exclude_none=True)
        
        elif method == "cancelTask":
            # Parse as CancelTaskRequest
            req = types.CancelTaskRequest(**body)
            response = await handler.cancel_task(req)
            return response.model_dump(exclude_none=True)
        
        else:
            # Unknown method
            error_response = types.JSONRPCErrorResponse(
                jsonrpc="2.0",
                id=body.get("id"),
                error=types.MethodNotFoundError(
                    message=f"Method '{method}' not found"
                )
            )
            return error_response.model_dump(exclude_none=True)
    
    except Exception as e:
        # Log the full error internally
        import logging
        logging.error(f"Error handling A2A request for agent {agent_id}: {str(e)}", exc_info=True)
        
        # Return generic JSON-RPC error to client
        error_response = types.JSONRPCErrorResponse(
            jsonrpc="2.0",
            id=body.get("id") if body else None,
            error=types.InternalError(
                message="An internal error occurred while processing the request"
            )
        )
        return error_response.model_dump(exclude_none=True)


@router.get("/{agent_id}/tasks/{task_id}")
async def get_task(agent_id: str, task_id: str):
    """Get task information (A2A protocol endpoint)"""
    task_store = a2a_agent_manager.task_stores.get(agent_id)
    if not task_store:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    task = await task_store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.model_dump(exclude_none=True)
