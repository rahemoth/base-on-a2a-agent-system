"""
FastAPI routes for agent management
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import json

from backend.models import (
    AgentCreate,
    AgentResponse,
    AgentMessage,
    AgentCollaboration,
    AgentUpdate,
)
from backend.agents import agent_manager

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/", response_model=AgentResponse)
async def create_agent(agent_create: AgentCreate):
    """Create a new agent"""
    try:
        agent = await agent_manager.create_agent(agent_create.config)
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[AgentResponse])
async def list_agents():
    """List all agents"""
    try:
        agents = await agent_manager.list_agents()
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent by ID"""
    agent = await agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    from datetime import datetime
    return AgentResponse(
        id=agent_id,
        config=agent.config,
        status=agent.status,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent_update: AgentUpdate):
    """Update agent configuration"""
    if not agent_update.config:
        raise HTTPException(status_code=400, detail="Config is required for update")
    
    agent = await agent_manager.update_agent(agent_id, agent_update.config)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    success = await agent_manager.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"message": "Agent deleted successfully"}


@router.post("/message")
async def send_message(agent_message: AgentMessage):
    """Send a message to an agent"""
    try:
        if agent_message.stream:
            async def generate():
                async for chunk in await agent_manager.send_message_to_agent(
                    agent_message.agent_id,
                    agent_message.message,
                    agent_message.context,
                    stream=True
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            response = await agent_manager.send_message_to_agent(
                agent_message.agent_id,
                agent_message.message,
                agent_message.context,
                stream=False
            )
            return {"response": response}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collaborate")
async def collaborate(collaboration: AgentCollaboration):
    """Start a collaboration between multiple agents"""
    try:
        result = await agent_manager.collaborate_agents(
            agent_ids=collaboration.agents,
            task=collaboration.task,
            coordinator_id=collaboration.coordinator_agent,
            max_rounds=collaboration.max_rounds
        )
        
        return {
            "collaboration_history": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "metadata": msg.metadata,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in result
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
