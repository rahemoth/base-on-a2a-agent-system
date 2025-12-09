"""
A2A Agent Executor implementation using the official a2a-sdk
"""
import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from a2a import types
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import parts as parts_utils
from google import genai
from openai import AsyncOpenAI

from backend.models import AgentConfig, ModelProvider
from backend.mcp import mcp_manager

# Configure logger
logger = logging.getLogger(__name__)


class LLMAgentExecutor(AgentExecutor):
    """
    Agent executor that integrates LLMs (Google GenAI, OpenAI) with A2A protocol.
    Supports MCP tool integration.
    """
    
    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        google_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openai_base_url: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self.config = config
        self.google_api_key = google_api_key
        self.openai_api_key = openai_api_key
        self.openai_base_url = openai_base_url
        
        # Initialize LLM clients
        self.google_client = None
        self.openai_client = None
        self.mcp_client = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients based on configuration"""
        logger.info(f"Agent {self.agent_id}: Initializing clients for provider: {self.config.provider.value}")
        
        if self.config.provider == ModelProvider.GOOGLE:
            if self.google_api_key:
                self.google_client = genai.Client(api_key=self.google_api_key)
                logger.info(f"Agent {self.agent_id}: Google client initialized")
            else:
                logger.warning(f"Agent {self.agent_id}: Google API key not provided")
        elif self.config.provider in [ModelProvider.OPENAI, ModelProvider.LMSTUDIO, 
                                      ModelProvider.LOCALAI, ModelProvider.OLLAMA, 
                                      ModelProvider.TEXTGEN_WEBUI, ModelProvider.CUSTOM]:
            # For OpenAI and all local/custom providers using OpenAI-compatible API
            api_key = self.openai_api_key or "local-llm-key-not-required"
            
            # Determine base URL based on provider
            if self.config.api_base_url:
                base_url = self.config.api_base_url
                logger.debug(f"Agent {self.agent_id}: Using api_base_url from config: {base_url}")
            elif self.config.openai_base_url:
                # Backward compatibility
                base_url = self.config.openai_base_url
                logger.debug(f"Agent {self.agent_id}: Using openai_base_url from config: {base_url}")
            elif self.config.provider == ModelProvider.OPENAI:
                # Use official OpenAI API (no custom base URL)
                base_url = None
                logger.debug(f"Agent {self.agent_id}: Using official OpenAI API")
            else:
                # Default URLs for each local provider
                default_urls = {
                    ModelProvider.LMSTUDIO: "http://localhost:1234/v1",
                    ModelProvider.LOCALAI: "http://localhost:8080/v1",
                    ModelProvider.OLLAMA: "http://localhost:11434/v1",
                    ModelProvider.TEXTGEN_WEBUI: "http://localhost:5000/v1",
                    ModelProvider.CUSTOM: None
                }
                base_url = default_urls.get(self.config.provider)
                logger.debug(f"Agent {self.agent_id}: Using default URL for {self.config.provider.value}: {base_url}")
            
            if base_url:
                self.openai_client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                logger.info(f"Agent {self.agent_id}: OpenAI client initialized with base_url: {base_url}")
            else:
                self.openai_client = AsyncOpenAI(api_key=api_key)
                logger.info(f"Agent {self.agent_id}: OpenAI client initialized with default endpoint")
        else:
            logger.error(f"Agent {self.agent_id}: Unsupported provider: {self.config.provider}")
    
    async def initialize_mcp(self):
        """Initialize MCP servers if configured"""
        if self.config.mcp_servers:
            self.mcp_client = await mcp_manager.create_client(self.agent_id)
            for mcp_config in self.config.mcp_servers:
                await self.mcp_client.connect_server(
                    name=mcp_config.name,
                    command=mcp_config.command,
                    args=mcp_config.args,
                    env=mcp_config.env
                )
    
    async def execute(self, request_context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute agent logic for an incoming request.
        This is the main entry point called by the A2A framework.
        """
        logger.debug(f"Agent {self.agent_id}: Processing message")
        try:
            # Get the incoming message
            message = request_context.message
            
            # Extract text content from message parts
            text_content = self._extract_text_from_message(message)
            
            if not text_content:
                # No text content, send error
                logger.warning(f"Agent {self.agent_id}: No text content found in message")
                error_message = self._create_message(
                    "No text content found in the message.",
                    context_id=message.context_id,
                    task_id=message.task_id
                )
                await event_queue.enqueue_event(error_message)
                return
            
            # Generate response using LLM
            logger.info(f"Agent {self.agent_id}: Generating response using {self.config.provider.value} with model {self.config.model}")
            if self.config.provider == ModelProvider.GOOGLE:
                response_text = await self._generate_google(text_content, request_context)
            elif self.config.provider in [ModelProvider.OPENAI, ModelProvider.LMSTUDIO, 
                                          ModelProvider.LOCALAI, ModelProvider.OLLAMA, 
                                          ModelProvider.TEXTGEN_WEBUI, ModelProvider.CUSTOM]:
                response_text = await self._generate_openai(text_content, request_context)
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
            
            logger.debug(f"Agent {self.agent_id}: Generated response ({len(response_text)} chars)")
            
            # Create and publish response message
            response_message = self._create_message(
                response_text,
                context_id=message.context_id,
                task_id=message.task_id
            )
            
            await event_queue.enqueue_event(response_message)
            
        except Exception as e:
            # Handle errors
            logger.error(f"Agent {self.agent_id}: Error processing message: {str(e)}", exc_info=True)
            error_message = self._create_message(
                f"Error processing message: {str(e)}",
                context_id=request_context.message.context_id,
                task_id=request_context.message.task_id
            )
            await event_queue.enqueue_event(error_message)
    
    async def cancel(self, task_id: str, reason: Optional[str] = None) -> None:
        """Cancel a running task (required by AgentExecutor interface)"""
        # For simple synchronous agents, there's nothing to cancel
        pass
    
    def _extract_text_from_message(self, message: types.Message) -> str:
        """Extract text content from message parts
        
        The A2A SDK uses Pydantic RootModel for discriminated unions, where Part
        is a wrapper around TextPart | FilePart | DataPart. We access part.root
        to get the actual typed part before checking instance type.
        """
        text_parts = []
        
        for part in message.parts:
            # In A2A SDK, Part is a RootModel wrapper around the actual part type
            # We need to access part.root to get the actual TextPart/FilePart/DataPart
            actual_part = part.root if hasattr(part, 'root') else part
            
            # Only extract from TextPart - other part types (FilePart, DataPart) don't have text
            if isinstance(actual_part, types.TextPart):
                text_parts.append(actual_part.text)
        
        return " ".join(text_parts)
    
    def _create_message(
        self,
        text: str,
        context_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> types.Message:
        """Create an A2A message with text content"""
        return types.Message(
            kind="message",
            message_id=str(uuid.uuid4()),
            role=types.Role.agent,
            parts=[types.TextPart(kind="text", text=text)],
            context_id=context_id,
            task_id=task_id
        )
    
    async def _generate_google(self, text: str, request_context: RequestContext) -> str:
        """Generate response using Google GenAI"""
        if not self.google_client:
            raise RuntimeError("Google client not initialized")
        
        # Build conversation history from context
        contents = []
        
        # Add context messages if available
        if hasattr(request_context, 'task') and request_context.task:
            # Get messages from task history
            for msg in request_context.task.messages:
                role = "user" if msg.role == types.Role.user else "model"
                msg_text = self._extract_text_from_message(msg)
                if msg_text:
                    contents.append(genai.types.Content(
                        role=role,
                        parts=[genai.types.Part(text=msg_text)]
                    ))
        
        # Add current message
        contents.append(genai.types.Content(
            role="user",
            parts=[genai.types.Part(text=text)]
        ))
        
        # Configure generation
        config = {
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens:
            config["max_output_tokens"] = self.config.max_tokens
        if self.config.system_prompt:
            config["system_instruction"] = self.config.system_prompt
        
        # Generate response
        response = await self.google_client.aio.models.generate_content(
            model=self.config.model,
            contents=contents,
            config=config
        )
        
        return response.text
    
    async def _generate_openai(self, text: str, request_context: RequestContext) -> str:
        """Generate response using OpenAI"""
        if not self.openai_client:
            logger.error(f"Agent {self.agent_id}: OpenAI client not initialized")
            raise RuntimeError("OpenAI client not initialized")
        
        # Build messages array
        messages = []
        
        # Add system prompt if configured
        if self.config.system_prompt:
            messages.append({
                "role": "system",
                "content": self.config.system_prompt
            })
        
        # Add context messages if available
        if hasattr(request_context, 'task') and request_context.task:
            for msg in request_context.task.messages:
                role = "user" if msg.role == types.Role.user else "assistant"
                msg_text = self._extract_text_from_message(msg)
                if msg_text:
                    messages.append({
                        "role": role,
                        "content": msg_text
                    })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": text
        })
        
        # Configure generation
        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens:
            kwargs["max_tokens"] = self.config.max_tokens
        
        # Generate response
        try:
            logger.debug(f"Agent {self.agent_id}: Calling {self.config.provider.value} API (model: {self.config.model})")
            response = await self.openai_client.chat.completions.create(**kwargs)
            
            if not response.choices:
                error_msg = "No response choices returned from API"
                logger.error(f"Agent {self.agent_id}: {error_msg}")
                raise RuntimeError(error_msg)
            
            if not response.choices[0].message.content:
                error_msg = "Empty content in response"
                logger.error(f"Agent {self.agent_id}: {error_msg}")
                raise RuntimeError(error_msg)
            
            result = response.choices[0].message.content
            logger.debug(f"Agent {self.agent_id}: Received response from API")
            return result
        except Exception as e:
            logger.error(f"Agent {self.agent_id}: Failed to generate response: {str(e)}", exc_info=True)
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.mcp_client:
            await mcp_manager.remove_client(self.agent_id)
