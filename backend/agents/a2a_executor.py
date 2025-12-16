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
from backend.utils.a2a_utils import extract_text_from_parts
from backend.agents.memory import AgentMemory
from backend.agents.cognitive import CognitiveProcessor
from backend.agents.tools import EnhancedToolManager

# Configure logger
logger = logging.getLogger(__name__)

# Constants for content truncation
CONTENT_SUMMARY_LENGTH = 200  # For summarizing content in memory
CONTENT_RESULT_LENGTH = 500   # For storing task results

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
        
        # Initialize memory and cognitive systems
        self.memory = AgentMemory(agent_id=agent_id)
        self.cognitive = CognitiveProcessor(agent_id=agent_id, agent_name=config.name)
        
        # Initialize enhanced tool manager (will be fully initialized in initialize_mcp)
        self.tool_manager = None
        
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

            elif self.config.openai_base_url:
                # Backward compatibility
                base_url = self.config.openai_base_url

            elif self.config.provider == ModelProvider.OPENAI:
                # Use official OpenAI API (no custom base URL)
                base_url = None

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
        """Initialize MCP servers and memory system"""
        # Initialize memory database
        await self.memory.initialize()
        
        # Initialize MCP servers if configured
        if self.config.mcp_servers:
            self.mcp_client = await mcp_manager.create_client(self.agent_id)
            for mcp_config in self.config.mcp_servers:
                await self.mcp_client.connect_server(
                    name=mcp_config.name,
                    command=mcp_config.command,
                    args=mcp_config.args,
                    env=mcp_config.env
                )
        
        # Initialize enhanced tool manager with MCP client
        self.tool_manager = EnhancedToolManager(
            agent_id=self.agent_id,
            mcp_client=self.mcp_client
        )
        
        # Discover available tools
        await self.tool_manager.discover_tools()
        
        logger.info(f"Agent {self.agent_id}: Initialized with {len(self.tool_manager.tools)} tools")
    
    async def execute(self, request_context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute agent logic for an incoming request with enhanced cognitive processing.
        This is the main entry point called by the A2A framework.
        """

        task_id = None
        
        try:
            # Get the incoming message
            message = request_context.message
            task_id = message.task_id or f"task_{self.agent_id}_{uuid.uuid4()}"
            
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
            
            # Save to short-term memory
            self.memory.add_to_short_term({
                "role": "user",
                "content": text_content,
                "task_id": task_id
            })
            
            # Save task to history
            await self.memory.save_task(
                task_id=task_id,
                task_description=text_content,
                status="started"
            )
            
            # Get available tools for perception using enhanced tool manager
            available_tools = []
            if self.tool_manager:
                try:
                    all_tools = await self.tool_manager.discover_tools()
                    available_tools = [tool.name for tool in all_tools]
                except Exception as e:
                    logger.warning(f"Agent {self.agent_id}: Error discovering tools: {e}")
            
            # Get conversation context from task
            context_messages = []
            if hasattr(request_context, 'task') and request_context.task:
                for msg in request_context.task.messages:
                    msg_text = self._extract_text_from_message(msg)
                    if msg_text:
                        context_messages.append({
                            "role": "user" if msg.role == types.Role.user else "assistant",
                            "content": msg_text
                        })
            
            # 1. ENVIRONMENTAL PERCEPTION
            perception = self.cognitive.perceive_environment(
                message=text_content,
                context=context_messages,
                available_tools=available_tools,
                collaboration_context=None  # Can be enhanced with collaboration info
            )
            
            # Update environment context in memory
            self.memory.update_environment_context({
                "last_message": text_content,
                "context_size": len(context_messages),
                "available_tools": available_tools,
                "timestamp": datetime.now().isoformat()
            })
            
            # 2. REASONING
            reasoning = self.cognitive.reason(
                perception=perception,
                task_goal=text_content,
                constraints=[]
            )
            
            # 3. DECISION MAKING
            decision = self.cognitive.decide(
                reasoning=reasoning,
                perception=perception
            )
            
            # 4. EXECUTION PLANNING
            execution_plan = self.cognitive.plan_execution(
                decision=decision,
                task_description=text_content
            )
            
            # Update working memory with plan
            self.memory.update_working_memory("current_plan", execution_plan)
            self.memory.update_working_memory("decision", decision)
            
            # Generate response using LLM with enhanced context
            logger.info(f"Agent {self.agent_id}: Generating response using {self.config.provider.value} with model {self.config.model}")
            
            # Add cognitive context to the generation
            cognitive_context = self._build_cognitive_context(perception, reasoning, decision)
            
            if self.config.provider == ModelProvider.GOOGLE:
                response_text = await self._generate_google(text_content, request_context, cognitive_context)
            elif self.config.provider in [ModelProvider.OPENAI, ModelProvider.LMSTUDIO, 
                                          ModelProvider.LOCALAI, ModelProvider.OLLAMA, 
                                          ModelProvider.TEXTGEN_WEBUI, ModelProvider.CUSTOM]:
                response_text = await self._generate_openai(text_content, request_context, cognitive_context)
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
            
            
            # 5. FEEDBACK PROCESSING
            feedback = self.cognitive.process_feedback(
                result=response_text,
                expected_outcome=None,
                success=True
            )
            
            # Store response in memory
            self.memory.add_to_short_term({
                "role": "assistant",
                "content": response_text,
                "task_id": task_id
            })
            
            # Save important information to long-term memory
            await self.memory.add_to_long_term(
                memory_type="conversation",
                content=f"Q: {text_content[:CONTENT_SUMMARY_LENGTH]}... A: {response_text[:CONTENT_SUMMARY_LENGTH]}...",
                metadata={
                    "task_id": task_id,
                    "decision_type": decision["decision_type"],
                    "complexity": perception["complexity"]
                },
                importance=0.7 if perception["complexity"] == "high" else 0.5
            )
            
            # Update task status
            await self.memory.update_task(
                task_id=task_id,
                status="completed",
                result=response_text[:CONTENT_RESULT_LENGTH]  # Store first 500 chars
            )
            
            # Update execution plan status
            self.cognitive.update_plan_status(
                step_number=len(execution_plan["steps"]),
                status="completed",
                result="Response generated successfully"
            )
            
            # Create and publish response message
            response_message = self._create_message(
                response_text,
                context_id=message.context_id,
                task_id=message.task_id
            )
            
            await event_queue.enqueue_event(response_message)
            
        except Exception as e:
            # Handle errors with feedback
            logger.error(f"Agent {self.agent_id}: Error processing message: {str(e)}", exc_info=True)
            
            # Process failure feedback
            self.cognitive.process_feedback(
                result=str(e),
                expected_outcome="Successful response generation",
                success=False
            )
            
            # Update task status if we have a task_id
            if task_id:
                await self.memory.update_task(
                    task_id=task_id,
                    status="failed",
                    result=f"Error: {str(e)}"
                )
            
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
        
        Uses centralized utility function to ensure consistent behavior
        across the application when extracting text from A2A messages.
        """
        return extract_text_from_parts(message.parts)
    
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
    
    def _build_cognitive_context(
        self,
        perception: Dict[str, Any],
        reasoning: Dict[str, Any],
        decision: Dict[str, Any]
    ) -> str:
        """Build cognitive context to enhance LLM generation"""
        context_parts = []
        
        # Add perception insights
        context_parts.append(f"[Internal Analysis]")
        context_parts.append(f"Task Complexity: {perception.get('complexity', 'unknown')}")
        context_parts.append(f"Intent: {perception.get('intent', 'unknown')}")
        
        # Add reasoning conclusion
        if reasoning.get('conclusion'):
            context_parts.append(f"Approach: {reasoning['conclusion']}")
        
        # Add decision rationale
        if decision.get('rationale'):
            context_parts.append(f"Strategy: {decision['rationale']}")
        
        # Add memory context
        memory_context = self.memory.get_context_for_llm(max_messages=5)
        if memory_context:
            context_parts.append(f"\n{memory_context}")
        
        return "\n".join(context_parts)
    
    def _build_tools_description(self) -> str:
        """Build a description of available MCP tools for the system prompt
        
        This ensures the LLM knows what tools are available and how to use them.
        """
        if not self.tool_manager or not self.tool_manager.tools:
            return ""
        
        tools_info = []
        tools_info.append("\n[Available MCP Tools]")
        tools_info.append("You have access to the following tools through MCP (Model Context Protocol):")
        
        # Group tools by server/category, excluding built-in tools
        tools_by_category = {}
        for tool_name, tool in self.tool_manager.tools.items():
            # Skip built-in tools - only show MCP tools
            if tool.is_builtin:
                continue
            category = tool.category
            if category not in tools_by_category:
                tools_by_category[category] = []
            tools_by_category[category].append(tool)
        
        # If no MCP tools available, return empty
        if not tools_by_category:
            return ""
        
        for category, tools in tools_by_category.items():
            tools_info.append(f"\n### {category} tools:")
            for tool in tools:
                desc = tool.description or "No description"
                tools_info.append(f"  - {tool.name}: {desc}")
        
        tools_info.append("\nWhen the user asks for something that requires these tools, describe what you would do with them.")
        tools_info.append("Note: Tool execution is handled automatically by the system when appropriate.")
        
        return "\n".join(tools_info)
    
    async def _generate_google(self, text: str, request_context: RequestContext, cognitive_context: Optional[str] = None) -> str:
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
        
        # Add current message with cognitive context
        message_text = text
        if cognitive_context:
            message_text = f"{cognitive_context}\n\nUser Message: {text}"
        
        contents.append(genai.types.Content(
            role="user",
            parts=[genai.types.Part(text=message_text)]
        ))
        
        # Configure generation
        config = {
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens:
            config["max_output_tokens"] = self.config.max_tokens
        
        # Enhance system prompt with cognitive capabilities and MCP tools if configured
        system_instruction = self.config.system_prompt or f"You are {self.config.name}."
        
        # Add available MCP tools information to system instruction
        tools_description = self._build_tools_description()
        if tools_description:
            system_instruction += tools_description
        
        if cognitive_context:
            system_instruction += "\n\nUse the internal analysis provided to enhance your response quality."
        
        if system_instruction:
            config["system_instruction"] = system_instruction
        
        # Generate response
        response = await self.google_client.aio.models.generate_content(
            model=self.config.model,
            contents=contents,
            config=config
        )
        
        return response.text
    
    async def _generate_openai(self, text: str, request_context: RequestContext, cognitive_context: Optional[str] = None) -> str:
        """Generate response using OpenAI"""
        if not self.openai_client:
            logger.error(f"Agent {self.agent_id}: OpenAI client not initialized")
            raise RuntimeError("OpenAI client not initialized")
        
        # Build messages array
        messages = []
        
        # Add enhanced system prompt if configured
        system_prompt = self.config.system_prompt or f"You are {self.config.name}, an AI assistant."
        
        # Add available MCP tools information to system prompt
        tools_description = self._build_tools_description()
        if tools_description:
            system_prompt += tools_description
        
        if cognitive_context:
            system_prompt += "\n\nUse the internal analysis provided to enhance your response quality and reasoning."
        
        messages.append({
            "role": "system",
            "content": system_prompt
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
        
        # Add current message with cognitive context
        message_content = text
        if cognitive_context:
            message_content = f"{cognitive_context}\n\nUser Message: {text}"
        
        messages.append({
            "role": "user",
            "content": message_content
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

            return result
        except Exception as e:
            logger.error(f"Agent {self.agent_id}: Failed to generate response: {str(e)}", exc_info=True)
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.mcp_client:
            await mcp_manager.remove_client(self.agent_id)
        
        # Clear in-memory data (database persists)
        self.memory.clear_short_term_memory()
        self.memory.clear_working_memory()
