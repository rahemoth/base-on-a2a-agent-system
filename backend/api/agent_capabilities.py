"""
FastAPI routes for agent memory and tools management
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Optional, List

from backend.agents.a2a_manager import a2a_agent_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agent-capabilities"])


# ============================================================================
# Memory API Endpoints
# ============================================================================

@router.get("/{agent_id}/memory/short-term")
async def get_short_term_memory(agent_id: str, limit: Optional[int] = None):
    """Get agent's short-term memory"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        memory = agent.memory.get_short_term_memory(limit=limit)
        return {"agent_id": agent_id, "memory": memory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/memory/long-term")
async def get_long_term_memory(
    agent_id: str,
    memory_type: Optional[str] = None,
    limit: int = 10,
    min_importance: float = 0.0
):
    """Search agent's long-term memory"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        memories = await agent.memory.search_long_term_memory(
            memory_type=memory_type,
            limit=limit,
            min_importance=min_importance
        )
        return {
            "agent_id": agent_id,
            "memories": memories,
            "count": len(memories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/memory/tasks")
async def get_task_history(
    agent_id: str,
    limit: int = 10,
    status: Optional[str] = None
):
    """Get agent's task history"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        tasks = await agent.memory.get_task_history(limit=limit, status=status)
        return {
            "agent_id": agent_id,
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/memory/environment")
async def get_environment_context(agent_id: str):
    """Get agent's current environment context"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        context = agent.memory.get_environment_context()
        return {"agent_id": agent_id, "context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}/memory/short-term")
async def clear_short_term_memory(agent_id: str):
    """Clear agent's short-term memory"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        agent.memory.clear_short_term_memory()
        return {"message": "Short-term memory cleared", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Cognitive State API Endpoints
# ============================================================================

@router.get("/{agent_id}/cognitive/state")
async def get_cognitive_state(agent_id: str):
    """Get agent's current cognitive state"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        state = agent.cognitive.get_cognitive_state()
        return {"agent_id": agent_id, "cognitive_state": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/cognitive/reasoning-chain")
async def get_reasoning_chain(agent_id: str, limit: int = 5):
    """Get agent's recent reasoning chain"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        chain = agent.cognitive.reasoning_chain[-limit:]
        return {
            "agent_id": agent_id,
            "reasoning_chain": chain,
            "count": len(chain)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/cognitive/current-plan")
async def get_current_plan(agent_id: str):
    """Get agent's current execution plan"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        plan = agent.cognitive.current_plan
        return {"agent_id": agent_id, "current_plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/cognitive/feedback-history")
async def get_feedback_history(agent_id: str, limit: int = 10):
    """Get agent's feedback history"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        feedback = agent.cognitive.feedback_history[-limit:]
        return {
            "agent_id": agent_id,
            "feedback_history": feedback,
            "count": len(feedback)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Tools API Endpoints
# ============================================================================

@router.get("/{agent_id}/tools")
async def list_agent_tools(
    agent_id: str,
    query: Optional[str] = None,
    category: Optional[str] = None
):
    """List all tools available to the agent"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if not agent.tool_manager:
        raise HTTPException(status_code=400, detail="Tool manager not initialized for this agent")
    
    try:
        tools = agent.tool_manager.search_tools(query=query, category=category)
        return {
            "agent_id": agent_id,
            "tools": [tool.to_dict() for tool in tools],
            "count": len(tools)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/tools/categories")
async def get_tool_categories(agent_id: str):
    """Get all tool categories available to the agent"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if not agent.tool_manager:
        raise HTTPException(status_code=400, detail="Tool manager not initialized for this agent")
    
    try:
        categories = agent.tool_manager.get_tool_categories()
        return {
            "agent_id": agent_id,
            "categories": categories,
            "count": len(categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/tools/statistics")
async def get_tool_statistics(agent_id: str, tool_name: Optional[str] = None):
    """Get tool execution statistics"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if not agent.tool_manager:
        raise HTTPException(status_code=400, detail="Tool manager not initialized for this agent")
    
    try:
        stats = agent.tool_manager.tracker.get_tool_statistics(tool_name=tool_name)
        return {
            "agent_id": agent_id,
            "tool_name": tool_name,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/tools/execution-history")
async def get_tool_execution_history(
    agent_id: str,
    tool_name: Optional[str] = None,
    limit: int = 10
):
    """Get tool execution history"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if not agent.tool_manager:
        raise HTTPException(status_code=400, detail="Tool manager not initialized for this agent")
    
    try:
        history = agent.tool_manager.tracker.get_execution_history(
            tool_name=tool_name,
            limit=limit
        )
        return {
            "agent_id": agent_id,
            "tool_name": tool_name,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/tools/report")
async def get_tool_execution_report(agent_id: str):
    """Get comprehensive tool execution report"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if not agent.tool_manager:
        raise HTTPException(status_code=400, detail="Tool manager not initialized for this agent")
    
    try:
        report = agent.tool_manager.get_execution_report()
        return {"agent_id": agent_id, "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
