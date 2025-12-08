"""
FastAPI routes for MCP management
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.mcp import mcp_manager

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


@router.get("/agents/{agent_id}/tools")
async def get_agent_tools(agent_id: str):
    """Get available MCP tools for an agent"""
    try:
        client = await mcp_manager.get_client(agent_id)
        if not client:
            raise HTTPException(status_code=404, detail="Agent MCP client not found")
        
        tools = await client.list_tools()
        return {"tools": tools}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/resources")
async def get_agent_resources(agent_id: str):
    """Get available MCP resources for an agent"""
    try:
        client = await mcp_manager.get_client(agent_id)
        if not client:
            raise HTTPException(status_code=404, detail="Agent MCP client not found")
        
        resources = await client.list_resources()
        return {"resources": resources}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/tools/{server_name}/{tool_name}")
async def call_tool(agent_id: str, server_name: str, tool_name: str, arguments: Dict[str, Any]):
    """Call a tool on an MCP server"""
    try:
        client = await mcp_manager.get_client(agent_id)
        if not client:
            raise HTTPException(status_code=404, detail="Agent MCP client not found")
        
        result = await client.call_tool(server_name, tool_name, arguments)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
