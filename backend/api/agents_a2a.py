"""
FastAPI routes for A2A-compliant agent management and A2A protocol endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional, AsyncGenerator
import json
import asyncio

from a2a import types
from backend.models import (
    AgentCreate,
    AgentResponse,
    AgentMessage,
    AgentUpdate,
    AgentCollaboration,
)
from backend.agents.a2a_manager import a2a_agent_manager
from backend.utils.a2a_utils import extract_text_from_parts

# Initialize logger at module level
logger = logging.getLogger(__name__)

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
    logger.debug(f"Received message for agent {agent_message.agent_id}")
    
    try:
        # Use A2A manager to send message
        response = await a2a_agent_manager.send_message(
            agent_message.agent_id,
            agent_message.message,
        )
        
        # Extract text from response using centralized utility
        text_response = extract_text_from_parts(response.parts)
        
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


@router.post("/collaborate/stream")
async def collaborate_stream(collaboration: AgentCollaboration):
    """Start a collaboration with real-time Server-Sent Events streaming"""
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate Server-Sent Events for collaboration updates"""
        try:
            # Create an asyncio queue for messages
            message_queue = asyncio.Queue()
            
            # Start collaboration in background task
            async def run_collaboration():
                try:
                    async for message in a2a_agent_manager.collaborate_agents_stream(
                        agent_ids=collaboration.agents,
                        task=collaboration.task,
                        coordinator_id=collaboration.coordinator_agent,
                        max_rounds=collaboration.max_rounds
                    ):
                        await message_queue.put(message)
                except Exception as e:
                    logger.error(f"Error in collaboration stream: {str(e)}", exc_info=True)
                    await message_queue.put({"error": str(e)})
                finally:
                    await message_queue.put(None)  # Signal completion
            
            # Start collaboration task
            task = asyncio.create_task(run_collaboration())
            
            # Stream messages as they arrive
            while True:
                message = await message_queue.get()
                
                if message is None:
                    # Collaboration completed
                    yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                    break
                
                if "error" in message:
                    yield f"data: {json.dumps({'type': 'error', 'message': message['error']})}\n\n"
                    break
                
                # Send message as SSE
                yield f"data: {json.dumps({'type': 'message', 'data': message})}\n\n"
            
            # Wait for task to complete
            await task
            
        except Exception as e:
            logger.error(f"Error in event generator: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


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
