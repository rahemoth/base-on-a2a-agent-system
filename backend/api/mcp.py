"""
FastAPI routes for MCP management
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from backend.mcp import mcp_manager

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


@router.get("/agents/{agent_id}/status")
async def get_agent_mcp_status(agent_id: str):
    """Get MCP server connection status for an agent
    
    Returns diagnostic information about MCP server connections,
    including which servers are connected and available tools.
    """
    try:
        client = await mcp_manager.get_client(agent_id)
        if not client:
            return {
                "status": "no_client",
                "message": "No MCP client found for this agent. The agent may not have any MCP servers configured, or the agent hasn't been initialized yet.",
                "connected_servers": [],
                "tools_available": 0
            }
        
        # Get list of connected servers
        connected_servers = list(client.sessions.keys())
        
        # Try to list tools to verify connections are working
        total_tools = 0
        server_status = []
        
        for server_name in connected_servers:
            try:
                server_tools = await client.list_tools(server_name)
                tools_list = server_tools.get(server_name, [])
                tool_count = len(tools_list)
                total_tools += tool_count
                server_status.append({
                    "name": server_name,
                    "status": "connected",
                    "tools_count": tool_count
                })
            except Exception:
                server_status.append({
                    "name": server_name,
                    "status": "error",
                    "error": "Failed to list tools from server"
                })
        
        return {
            "status": "ok" if connected_servers else "no_servers",
            "message": f"Agent has {len(connected_servers)} MCP server(s) connected with {total_tools} tool(s) available." if connected_servers else "No MCP servers connected.",
            "connected_servers": server_status,
            "tools_available": total_tools
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
