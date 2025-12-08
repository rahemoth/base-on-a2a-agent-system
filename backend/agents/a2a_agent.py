"""
A2A Agent implementation using Google's Agent-to-Agent protocol
"""
import asyncio
import json
import uuid
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime
from google import genai
from google.genai.types import Content, Part, Tool, FunctionDeclaration
from openai import AsyncOpenAI

from backend.models import AgentConfig, AgentStatus, Message, MessageRole, ModelProvider
from backend.mcp import mcp_manager


# Role mapping for OpenAI API
ROLE_MAPPING = {
    MessageRole.USER: "user",
    MessageRole.AGENT: "assistant",
    MessageRole.SYSTEM: "system"
}


class A2AAgent:
    """Agent implementation using A2A protocol"""
    
    def __init__(self, agent_id: str, config: AgentConfig):
        self.id = agent_id
        self.config = config
        self.status = AgentStatus.IDLE
        self.client = None
        self.openai_client = None
        self.conversation_history: List[Message] = []
        self.mcp_client = None
        
    async def initialize(self, google_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        """Initialize the agent with appropriate client based on provider"""
        try:
            if self.config.provider == ModelProvider.GOOGLE:
                if not google_api_key:
                    raise ValueError("Google API key not configured")
                self.client = genai.Client(api_key=google_api_key)
            elif self.config.provider == ModelProvider.OPENAI:
                if not openai_api_key:
                    raise ValueError("OpenAI API key not configured")
                self.openai_client = AsyncOpenAI(api_key=openai_api_key)
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
            
            # Initialize MCP servers if configured
            if self.config.mcp_servers:
                self.mcp_client = await mcp_manager.create_client(self.id)
                for mcp_config in self.config.mcp_servers:
                    await self.mcp_client.connect_server(
                        name=mcp_config.name,
                        command=mcp_config.command,
                        args=mcp_config.args,
                        env=mcp_config.env
                    )
            
            self.status = AgentStatus.IDLE
            return True
        except Exception as e:
            self.status = AgentStatus.ERROR
            print(f"Error initializing agent {self.id}: {e}")
            return False
    
    async def get_tools(self) -> List[Tool]:
        """Get available tools from MCP servers (Google format)"""
        tools = []
        
        if self.mcp_client:
            try:
                mcp_tools = await self.mcp_client.list_tools()
                
                for server_name, server_tools in mcp_tools.items():
                    for tool in server_tools:
                        # Convert MCP tool to GenAI tool format
                        function_declaration = FunctionDeclaration(
                            name=f"{server_name}_{tool['name']}",
                            description=tool.get('description', ''),
                            parameters=tool.get('input_schema', {})
                        )
                        tools.append(Tool(function_declarations=[function_declaration]))
            except Exception as e:
                print(f"Error getting tools for agent {self.id}: {e}")
        
        return tools
    
    async def _get_tools_openai(self) -> List[Dict[str, Any]]:
        """Get available tools from MCP servers (OpenAI format)"""
        tools = []
        
        if self.mcp_client:
            try:
                mcp_tools = await self.mcp_client.list_tools()
                
                for server_name, server_tools in mcp_tools.items():
                    for tool in server_tools:
                        # Convert MCP tool to OpenAI tool format
                        tools.append({
                            "type": "function",
                            "function": {
                                "name": f"{server_name}_{tool['name']}",
                                "description": tool.get('description', ''),
                                "parameters": tool.get('input_schema', {})
                            }
                        })
            except Exception as e:
                print(f"Error getting tools for agent {self.id}: {e}")
        
        return tools
    
    async def send_message(
        self,
        message: str,
        context: Optional[List[Message]] = None,
        stream: bool = False
    ):
        """Send a message to the agent"""
        if not self.client and not self.openai_client:
            raise RuntimeError("Agent not initialized")
        
        self.status = AgentStatus.BUSY
        
        try:
            if self.config.provider == ModelProvider.GOOGLE:
                return await self._send_message_google(message, context, stream)
            elif self.config.provider == ModelProvider.OPENAI:
                return await self._send_message_openai(message, context, stream)
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
                
        finally:
            self.status = AgentStatus.IDLE
    
    async def _send_message_google(
        self,
        message: str,
        context: Optional[List[Message]] = None,
        stream: bool = False
    ):
        """Send a message using Google GenAI"""
        # Build conversation history
        contents = []
        
        # Add context if provided
        if context:
            for msg in context:
                contents.append(Content(
                    role=msg.role.value,
                    parts=[Part(text=msg.content)]
                ))
        
        # Add current message
        contents.append(Content(
            role="user",
            parts=[Part(text=message)]
        ))
        
        # Get available tools
        tools = await self.get_tools()
        
        # Configure generation
        config = {
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens:
            config["max_output_tokens"] = self.config.max_tokens
        if self.config.system_prompt:
            config["system_instruction"] = self.config.system_prompt
        
        # Generate response
        if stream:
            async def stream_response():
                response = await self.client.aio.models.generate_content_stream(
                    model=self.config.model,
                    contents=contents,
                    config=config,
                    tools=tools if tools else None
                )
                
                async for chunk in response:
                    if chunk.text:
                        yield chunk.text
            
            return stream_response()
        else:
            response = await self.client.aio.models.generate_content(
                model=self.config.model,
                contents=contents,
                config=config,
                tools=tools if tools else None
            )
            
            # Handle tool calls if present
            if response.candidates[0].content.parts[0].function_call:
                tool_call = response.candidates[0].content.parts[0].function_call
                tool_result = await self._execute_tool(tool_call)
                
                # Send tool result back to model
                contents.append(response.candidates[0].content)
                contents.append(Content(
                    role="user",
                    parts=[Part(function_response=tool_result)]
                ))
                
                response = await self.client.aio.models.generate_content(
                    model=self.config.model,
                    contents=contents,
                    config=config,
                    tools=tools if tools else None
                )
            
            result = response.text
            
            # Store in conversation history
            self.conversation_history.append(Message(
                role=MessageRole.USER,
                content=message,
                timestamp=datetime.utcnow()
            ))
            self.conversation_history.append(Message(
                role=MessageRole.AGENT,
                content=result,
                timestamp=datetime.utcnow()
            ))
            
            return result
    
    async def _send_message_openai(
        self,
        message: str,
        context: Optional[List[Message]] = None,
        stream: bool = False
    ):
        """Send a message using OpenAI"""
        # Build messages array
        messages = []
        
        # Add system prompt if configured
        if self.config.system_prompt:
            messages.append({
                "role": "system",
                "content": self.config.system_prompt
            })
        
        # Add context if provided
        if context:
            for msg in context:
                role = ROLE_MAPPING.get(msg.role, msg.role.value)
                messages.append({
                    "role": role,
                    "content": msg.content
                })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Get available tools (OpenAI format)
        tools = await self._get_tools_openai()
        
        # Configure generation
        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens:
            kwargs["max_tokens"] = self.config.max_tokens
        if tools:
            kwargs["tools"] = tools
        
        # Generate response
        if stream:
            async def stream_response():
                response = await self.openai_client.chat.completions.create(
                    **kwargs,
                    stream=True
                )
                
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            return stream_response()
        else:
            response = await self.openai_client.chat.completions.create(**kwargs)
            
            # Handle tool calls if present
            message_obj = response.choices[0].message
            if message_obj.tool_calls:
                # Execute tools and get responses
                tool_messages = []
                for tool_call in message_obj.tool_calls:
                    tool_result = await self._execute_tool_openai(tool_call)
                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(tool_result)
                    })
                
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": message_obj.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message_obj.tool_calls
                    ]
                })
                
                # Add tool results
                messages.extend(tool_messages)
                
                # Get final response (reuse config from kwargs)
                final_kwargs = {
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": self.config.temperature,
                }
                if self.config.max_tokens:
                    final_kwargs["max_tokens"] = self.config.max_tokens
                
                response = await self.openai_client.chat.completions.create(**final_kwargs)
            
            result = response.choices[0].message.content
            
            # Store in conversation history
            self.conversation_history.append(Message(
                role=MessageRole.USER,
                content=message,
                timestamp=datetime.utcnow()
            ))
            self.conversation_history.append(Message(
                role=MessageRole.AGENT,
                content=result,
                timestamp=datetime.utcnow()
            ))
            
            return result
    
    async def _execute_tool(self, tool_call: Any) -> Dict[str, Any]:
        """Execute a tool call via MCP (Google format)"""
        try:
            # Parse server name and tool name
            full_name = tool_call.name
            server_name, tool_name = full_name.split('_', 1)
            
            # Execute tool
            result = await self.mcp_client.call_tool(
                server_name=server_name,
                tool_name=tool_name,
                arguments=tool_call.args
            )
            
            return {
                "name": full_name,
                "response": result
            }
        except Exception as e:
            return {
                "name": tool_call.name,
                "response": {"error": str(e)}
            }
    
    async def _execute_tool_openai(self, tool_call: Any) -> Dict[str, Any]:
        """Execute a tool call via MCP (OpenAI format)"""
        try:
            # Parse server name and tool name
            full_name = tool_call.function.name
            parts = full_name.split('_', 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid tool name format: {full_name}. Expected 'server_toolname'")
            server_name, tool_name = parts
            
            # Parse arguments
            arguments = json.loads(tool_call.function.arguments)
            
            # Execute tool
            result = await self.mcp_client.call_tool(
                server_name=server_name,
                tool_name=tool_name,
                arguments=arguments
            )
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def collaborate(
        self,
        other_agents: List['A2AAgent'],
        task: str,
        max_rounds: int = 5
    ) -> List[Message]:
        """Collaborate with other agents on a task"""
        collaboration_history = []
        
        # Initialize task
        current_message = f"Task: {task}\n\nYou are collaborating with {len(other_agents)} other agents. Please provide your initial thoughts and approach."
        
        collaboration_history.append(Message(
            role=MessageRole.SYSTEM,
            content=f"Starting collaboration on task: {task}",
            timestamp=datetime.utcnow()
        ))
        
        # Collaboration rounds
        for round_num in range(max_rounds):
            # This agent's turn
            response = await self.send_message(current_message, context=collaboration_history)
            collaboration_history.append(Message(
                role=MessageRole.AGENT,
                content=f"[{self.config.name}]: {response}",
                metadata={"agent_id": self.id, "agent_name": self.config.name},
                timestamp=datetime.utcnow()
            ))
            
            # Other agents' turns
            for agent in other_agents:
                context_message = f"Previous responses:\n{response}\n\nBased on the discussion so far, what is your contribution?"
                agent_response = await agent.send_message(context_message, context=collaboration_history)
                collaboration_history.append(Message(
                    role=MessageRole.AGENT,
                    content=f"[{agent.config.name}]: {agent_response}",
                    metadata={"agent_id": agent.id, "agent_name": agent.config.name},
                    timestamp=datetime.utcnow()
                ))
            
            # Check if task is complete (simplified check)
            if round_num == max_rounds - 1:
                break
            
            current_message = "Based on all previous contributions, please provide your next thoughts or indicate if the task is complete."
        
        return collaboration_history
    
    async def cleanup(self):
        """Cleanup agent resources"""
        if self.mcp_client:
            await mcp_manager.remove_client(self.id)
        self.status = AgentStatus.OFFLINE
