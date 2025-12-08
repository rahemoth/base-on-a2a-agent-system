"""
MCP (Model Context Protocol) integration for A2A Agent System
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack


class MCPClient:
    """MCP Client for connecting to MCP servers"""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        
    async def connect_server(self, name: str, command: str, args: List[str] = None, env: Dict[str, str] = None):
        """Connect to an MCP server"""
        try:
            if args is None:
                args = []
            if env is None:
                env = {}
                
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env
            )
            
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport
            
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )
            
            await session.initialize()
            self.sessions[name] = session
            
            return True
        except Exception as e:
            print(f"Error connecting to MCP server {name}: {e}")
            return False
    
    async def disconnect_server(self, name: str):
        """Disconnect from an MCP server"""
        if name in self.sessions:
            del self.sessions[name]
    
    async def list_tools(self, server_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List available tools from MCP servers"""
        tools = {}
        
        servers = [server_name] if server_name else self.sessions.keys()
        
        for name in servers:
            if name in self.sessions:
                try:
                    result = await self.sessions[name].list_tools()
                    tools[name] = [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema
                        }
                        for tool in result.tools
                    ]
                except Exception as e:
                    print(f"Error listing tools from {name}: {e}")
                    tools[name] = []
        
        return tools
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on an MCP server"""
        if server_name not in self.sessions:
            raise ValueError(f"Server {server_name} not connected")
        
        try:
            result = await self.sessions[server_name].call_tool(tool_name, arguments)
            return result
        except Exception as e:
            print(f"Error calling tool {tool_name} on {server_name}: {e}")
            raise
    
    async def list_resources(self, server_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List available resources from MCP servers"""
        resources = {}
        
        servers = [server_name] if server_name else self.sessions.keys()
        
        for name in servers:
            if name in self.sessions:
                try:
                    result = await self.sessions[name].list_resources()
                    resources[name] = [
                        {
                            "uri": resource.uri,
                            "name": resource.name,
                            "description": resource.description,
                            "mimeType": resource.mimeType
                        }
                        for resource in result.resources
                    ]
                except Exception as e:
                    print(f"Error listing resources from {name}: {e}")
                    resources[name] = []
        
        return resources
    
    async def read_resource(self, server_name: str, uri: str) -> Any:
        """Read a resource from an MCP server"""
        if server_name not in self.sessions:
            raise ValueError(f"Server {server_name} not connected")
        
        try:
            result = await self.sessions[server_name].read_resource(uri)
            return result
        except Exception as e:
            print(f"Error reading resource {uri} from {server_name}: {e}")
            raise
    
    async def close_all(self):
        """Close all MCP connections"""
        await self.exit_stack.aclose()
        self.sessions.clear()


class MCPManager:
    """Manager for MCP clients per agent"""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
    
    async def create_client(self, agent_id: str) -> MCPClient:
        """Create a new MCP client for an agent"""
        if agent_id not in self.clients:
            self.clients[agent_id] = MCPClient()
        return self.clients[agent_id]
    
    async def get_client(self, agent_id: str) -> Optional[MCPClient]:
        """Get MCP client for an agent"""
        return self.clients.get(agent_id)
    
    async def remove_client(self, agent_id: str):
        """Remove MCP client for an agent"""
        if agent_id in self.clients:
            await self.clients[agent_id].close_all()
            del self.clients[agent_id]
    
    async def close_all(self):
        """Close all MCP clients"""
        for client in self.clients.values():
            await client.close_all()
        self.clients.clear()


# Global MCP manager instance
mcp_manager = MCPManager()
