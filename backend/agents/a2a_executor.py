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

from google import genai
from openai import AsyncOpenAI

from backend.models import AgentConfig, ModelProvider
from backend.mcp import mcp_manager
from backend.utils.a2a_utils import extract_text_from_parts
from backend.agents.memory import AgentMemory
from backend.agents.cognitive import CognitiveProcessor
from backend.agents.tools import EnhancedToolManager
from backend.config import settings

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
        anthropic_api_key: Optional[str] = None,
        kimi_api_key: Optional[str] = None,
        mimo_api_key: Optional[str] = None,
        minimax_api_key: Optional[str] = None,
        zhipu_api_key: Optional[str] = None,
        qwen_api_key: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        kimi_base_url: Optional[str] = None,
        mimo_base_url: Optional[str] = None,
        minimax_base_url: Optional[str] = None,
        zhipu_base_url: Optional[str] = None,
        qwen_base_url: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self.config = config
        
        # API Keys
        self.google_api_key = google_api_key
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.kimi_api_key = kimi_api_key
        self.mimo_api_key = mimo_api_key
        self.minimax_api_key = minimax_api_key
        self.zhipu_api_key = zhipu_api_key
        self.qwen_api_key = qwen_api_key
        
        # Base URLs
        self.openai_base_url = openai_base_url
        self.kimi_base_url = kimi_base_url
        self.mimo_base_url = mimo_base_url
        self.minimax_base_url = minimax_base_url
        self.zhipu_base_url = zhipu_base_url
        self.qwen_base_url = qwen_base_url
        
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
        
        if self.config.provider == ModelProvider.GEMINI:
            api_key = self.config.google_api_key or self.google_api_key
            if api_key:
                self.google_client = genai.Client(api_key=api_key)
                logger.info(f"Agent {self.agent_id}: Google client initialized")
            else:
                logger.warning(f"Agent {self.agent_id}: Google API key not provided")
        
        elif self.config.provider == ModelProvider.GPT:
            api_key = self.config.openai_api_key or self.openai_api_key
            base_url = self.config.api_base_url or self.openai_base_url or "https://api.openai.com/v1"
            
            if api_key:
                self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                logger.info(f"Agent {self.agent_id}: GPT client initialized with base_url: {base_url}")
            else:
                logger.warning(f"Agent {self.agent_id}: OpenAI API key not provided")
        
        elif self.config.provider == ModelProvider.CLAUDE:
            api_key = self.config.anthropic_api_key or self.anthropic_api_key
            if api_key:
                self.openai_client = AsyncOpenAI(api_key=api_key, base_url="https://api.anthropic.com/v1")
                logger.info(f"Agent {self.agent_id}: Claude client initialized")
            else:
                logger.warning(f"Agent {self.agent_id}: Anthropic API key not provided")
        
        elif self.config.provider == ModelProvider.DEEPSEEK:
            api_key = self.config.openai_api_key or self.openai_api_key
            base_url = self.config.api_base_url or self.openai_base_url or "https://api.deepseek.com/v1"
            
            if api_key:
                self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                logger.info(f"Agent {self.agent_id}: DeepSeek client initialized with base_url: {base_url}")
            else:
                logger.warning(f"Agent {self.agent_id}: DeepSeek API key not provided")
        
        elif self.config.provider == ModelProvider.KIMI:
            api_key = self.config.kimi_api_key or self.kimi_api_key
            base_url = self.config.api_base_url or self.kimi_base_url or "https://api.moonshot.cn/v1"
            
            if api_key:
                self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                logger.info(f"Agent {self.agent_id}: Kimi client initialized with base_url: {base_url}")
            else:
                logger.warning(f"Agent {self.agent_id}: Kimi API key not provided")
        
        elif self.config.provider == ModelProvider.MIMO:
            api_key = self.config.mimo_api_key or self.mimo_api_key
            base_url = self.config.api_base_url or self.mimo_base_url or "https://api.xiaomimimo.com/v1"
            
            if api_key:
                self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                logger.info(f"Agent {self.agent_id}: MiMo client initialized with base_url: {base_url}")
            else:
                logger.warning(f"Agent {self.agent_id}: MiMo API key not provided")
        
        elif self.config.provider == ModelProvider.MINIMAX:
            api_key = self.config.minimax_api_key or self.minimax_api_key
            base_url = self.config.api_base_url or self.minimax_base_url or "https://api.minimax.chat/v1/text/chatcompletion"
            
            if api_key:
                self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                logger.info(f"Agent {self.agent_id}: MiniMax client initialized with base_url: {base_url}")
            else:
                logger.warning(f"Agent {self.agent_id}: MiniMax API key not provided")
        
        elif self.config.provider == ModelProvider.GLM:
            api_key = self.config.zhipu_api_key or self.zhipu_api_key
            base_url = self.config.api_base_url or self.zhipu_base_url or "https://open.bigmodel.cn/api/paas/v4"
            
            if api_key:
                self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                logger.info(f"Agent {self.agent_id}: GLM client initialized with base_url: {base_url}")
            else:
                logger.warning(f"Agent {self.agent_id}: Zhipu API key not provided")
        
        elif self.config.provider == ModelProvider.QWEN:
            api_key = self.config.qwen_api_key or self.qwen_api_key
            base_url = self.config.api_base_url or self.qwen_base_url or "https://dashscope.aliyuncs.com/api/text-generation/v1"
            
            if api_key:
                self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                logger.info(f"Agent {self.agent_id}: Qwen client initialized with base_url: {base_url}")
            else:
                logger.warning(f"Agent {self.agent_id}: Qwen API key not provided")
        
        elif self.config.provider == ModelProvider.CUSTOM:
            # Custom/OpenAI-compatible API (supports LM Studio, Ollama, LocalAI, etc.)
            api_key = self.config.openai_api_key or self.openai_api_key or "local-llm-key-not-required"
            
            if self.config.api_base_url:
                base_url = self.config.api_base_url
            elif self.config.openai_base_url:
                base_url = self.config.openai_base_url
            else:
                logger.error(f"Agent {self.agent_id}: Base URL required for custom provider")
                return
            
            self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            logger.info(f"Agent {self.agent_id}: Custom client initialized with base_url: {base_url}")
        
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
                            "role": "user" if msg.role == types.Role.ROLE_USER else "assistant",
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
            
            # PRE-STORE role assignments to long-term memory BEFORE generating response
            # This ensures role settings are immediately available for RAG retrieval
            detected_role = self._detect_role_assignment(text_content)
            if detected_role:
                # Check if user is REMOVING a role (e.g., "你不是猫娘了")
                role_removal_patterns = ["不是", "不再是", "别当", "别做", "停止"]
                is_role_removal = any(pattern in text_content for pattern in role_removal_patterns)
                
                if is_role_removal:
                    # Store role removal with highest importance
                    await self.memory.add_to_long_term(
                        memory_type="role",
                        content=f"用户撤销AI角色: {detected_role}。现在AI是普通助手。",
                        metadata={"role": "assistant", "source": "user_removal", "removed_role": detected_role},
                        importance=1.0
                    )
                    print(f"\n[ROLE REMOVED] User removed role: {detected_role}")
                else:
                    # Store new role assignment
                    await self.memory.add_to_long_term(
                        memory_type="role",
                        content=f"用户设定AI角色为: {detected_role}",
                        metadata={"role": detected_role, "source": "user_assignment"},
                        importance=1.0
                    )
                    print(f"\n[ROLE STORED] Detected role assignment: {detected_role}")
            
            # Generate response using LLM with enhanced context
            logger.info(f"Agent {self.agent_id}: Generating response using {self.config.provider.value} with model {self.config.model}")
            
            # Add cognitive context to the generation (with RAG retrieval)
            cognitive_context = await self._build_cognitive_context_with_rag(perception, reasoning, decision, text_content)
            
            # Check if API key is configured
            # Get API key based on provider
            if self.config.provider == ModelProvider.GEMINI:
                api_key = self.config.google_api_key or self.google_api_key or settings.google_api_key
            elif self.config.provider == ModelProvider.GPT:
                api_key = self.config.openai_api_key or self.openai_api_key or settings.openai_api_key
            elif self.config.provider == ModelProvider.CLAUDE:
                api_key = self.config.anthropic_api_key or self.anthropic_api_key
            elif self.config.provider == ModelProvider.DEEPSEEK:
                api_key = self.config.openai_api_key or self.openai_api_key or settings.openai_api_key
            elif self.config.provider == ModelProvider.KIMI:
                api_key = self.config.kimi_api_key or self.kimi_api_key
            elif self.config.provider == ModelProvider.MIMO:
                api_key = self.config.mimo_api_key or self.mimo_api_key
            elif self.config.provider == ModelProvider.MINIMAX:
                api_key = self.config.minimax_api_key or self.minimax_api_key
            elif self.config.provider == ModelProvider.GLM:
                api_key = self.config.zhipu_api_key or self.zhipu_api_key
            elif self.config.provider == ModelProvider.QWEN:
                api_key = self.config.qwen_api_key or self.qwen_api_key
            else:
                api_key = None
            
            if not api_key:
                # No API key configured, return mock response
                logger.warning(f"Agent {self.agent_id}: No API key configured, returning mock response")
                response_text = f"[Mock Response] I have processed your request: '{text_content}'. This is a simulated response since no LLM API key has been configured."
            elif self.config.provider == ModelProvider.GEMINI:
                response_text = await self._generate_google(text_content, request_context, cognitive_context)
            elif self.config.provider in [ModelProvider.GPT, ModelProvider.CLAUDE,
                                          ModelProvider.DEEPSEEK, ModelProvider.KIMI,
                                          ModelProvider.MIMO, ModelProvider.MINIMAX,
                                          ModelProvider.GLM, ModelProvider.QWEN,
                                          ModelProvider.CUSTOM]:
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
            
            # RAG Memory Compression - Log compressed memory output
            short_term = self.memory.get_short_term_memory()
            if short_term:
                print("\n" + "="*60)
                print(f"[MEMORY] Agent: {self.agent_id[:8]}...")
                print("="*60)
                
                # Display short-term memory (hot memory)
                print("\n[HOT MEMORY]")
                for i, mem in enumerate(short_term[-3:]):  # Show last 3
                    role = mem.get('role', 'unknown')
                    content = mem.get('content', '')[:50]
                    print(f"  {role}: {content}...")
                
                # Display compression stats
                print(f"\n[STATS] {len(short_term)} turns | {sum(len(m.get('content', '')) for m in short_term)} chars")
                
                print("="*60 + "\n")
            
            # Save important information to long-term memory with REAL compression
            importance = 0.7 if perception["complexity"] == "high" else 0.5
            
            # Extract key information from dialogue
            compressed_memory = self._extract_key_information(text_content, response_text)
            
            # Check for similar memories and merge if found
            merged = await self._merge_or_add_memory(
                content=compressed_memory,
                memory_type="conversation",
                importance=importance,
                metadata={
                    "task_id": task_id,
                    "decision_type": decision["decision_type"],
                    "complexity": perception["complexity"],
                    "intent": perception["intent"],
                    "entities": self._extract_entities(text_content + " " + response_text)
                }
            )
            
            # Log long-term memory storage with compression details
            print(f"\n[MEMORY STORAGE]")
            print("-"*40)
            print(f"  Type: conversation")
            print(f"  Importance: {importance}")
            print(f"  Original: {len(text_content) + len(response_text)} chars")
            print(f"  Compressed: {len(compressed_memory)} chars")
            print(f"  Ratio: {(len(text_content) + len(response_text)) / max(len(compressed_memory), 1):.1f}x")
            print(f"  Content: {compressed_memory[:100]}...")
            if merged:
                print(f"  Action: MERGED with existing memory")
            else:
                print(f"  Action: ADDED new memory")
            print("")
            
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
            message_id=str(uuid.uuid4()),
            role=types.Role.ROLE_AGENT,
            parts=[types.Part(text=text)],
            context_id=context_id,
            task_id=task_id
        )
    
    def _build_cognitive_context(
        self,
        perception: Dict[str, Any],
        reasoning: Dict[str, Any],
        decision: Dict[str, Any],
        query_text: Optional[str] = None
    ) -> str:
        """Build cognitive context to enhance LLM generation with RAG retrieval"""
        context_parts = []
        
        # RAG Retrieval - Search long-term memory for relevant information
        if query_text:
            # Search for relevant memories based on keywords
            search_keywords = query_text.lower().split()
            
            print("\n🔍 RAG RETRIEVAL:")
            print("-"*40)
            print(f"  Query: {query_text}")
            print(f"  Search keywords: {search_keywords}")
        
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
        
        # Add short-term memory context
        memory_context = self.memory.get_context_for_llm(max_messages=5)
        if memory_context:
            context_parts.append(f"\n{memory_context}")
        
        # Add long-term memory retrieval results (RAG)
        # This will be populated asynchronously
        context_parts.append("\n[RAG Memory Retrieval]")
        context_parts.append("Searching relevant memories...")
        
        return "\n".join(context_parts)
    
    async def _build_cognitive_context_with_rag(
        self,
        perception: Dict[str, Any],
        reasoning: Dict[str, Any],
        decision: Dict[str, Any],
        query_text: str
    ) -> str:
        """Build cognitive context with RAG retrieval from long-term memory"""
        context_parts = []
        
        # RAG Retrieval - Semantic search
        print("\n[RAG SEMANTIC SEARCH]")
        print("-"*40)
        print(f"  Query: {query_text}")
        
        # Semantic search using vector similarity
        semantic_results = await self.memory.semantic_search(
            query=query_text,
            top_k=5,
            min_similarity=0.2
        )
        
        print(f"  Found {len(semantic_results)} semantic matches")
        
        # Also search for role memories (always include)
        role_memories = await self.memory.search_long_term_memory(
            memory_type="role",
            limit=3,
            min_importance=0.0
        )
        
        # Combine results (role memories + semantic matches)
        scored_memories = []
        
        # Add role memories with high priority
        for mem in role_memories:
            scored_memories.append({
                "content": mem.get("content", ""),
                "memory_type": "role",
                "importance": mem.get("importance", 1.0),
                "similarity": 1.0,  # Role memories always relevant
                "source": "role"
            })
        
        # Add semantic matches
        for result in semantic_results:
            # Skip if already in role memories
            if any(r.get("content") == result.get("content") for r in scored_memories):
                continue
                
            scored_memories.append({
                "content": result.get("content", ""),
                "memory_type": result.get("memory_type", ""),
                "importance": result.get("importance", 0.5),
                "similarity": result.get("similarity", 0),
                "source": "semantic"
            })
        
        # Sort by similarity * importance
        scored_memories.sort(
            key=lambda x: x.get("similarity", 0) * x.get("importance", 0.5),
            reverse=True
        )
        
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
        
        # Add short-term memory context
        memory_context = self.memory.get_context_for_llm(max_messages=5)
        if memory_context:
            context_parts.append(f"\n{memory_context}")
        
        # Add RAG retrieved memories
        if scored_memories:
            context_parts.append("\n[RAG Retrieved Memories]")
            context_parts.append("Use these memories to maintain consistency:")
            
            for i, mem in enumerate(scored_memories[:5]):  # Top 5
                content = mem.get("content", "")
                similarity = mem.get("similarity", 0)
                mem_type = mem.get("memory_type", "unknown")
                source = mem.get("source", "unknown")
                
                print(f"  [{i+1}] Type: {mem_type} | Similarity: {similarity:.2f} | Source: {source}")
                print(f"      {content[:60]}...")
                
                context_parts.append(f"\nMemory {i+1} ({mem_type}, similarity: {similarity:.2f}):")
                context_parts.append(f"  {content}")
            
            print("-"*40)
        else:
            context_parts.append("\n[RAG Retrieved Memories]")
            context_parts.append("No relevant memories found yet.")
            print("  No relevant memories found")
            print("-"*40)
        
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
                role = "user" if msg.role == types.Role.ROLE_USER else "model"
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
        """Generate response using OpenAI with RAG memory integration"""
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
        
        # Add RAG memory context to system prompt
        if cognitive_context:
            system_prompt += f"""

[IMPORTANT: RAG Memory Context]
The following information has been retrieved from your memory system. Use this to maintain consistency and remember important details about the user and your previous interactions:

{cognitive_context}

Based on these memories, you should:
1. Remember your previous role/persona if the user asks about it
2. Maintain consistency with previous responses
3. Reference past interactions when relevant
4. Acknowledge when the user asks you to recall something"""
        
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add context messages if available
        if hasattr(request_context, 'task') and request_context.task:
            for msg in request_context.task.messages:
                role = "user" if msg.role == types.Role.ROLE_USER else "assistant"
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
    
    async def _merge_or_add_memory(
        self,
        content: str,
        memory_type: str,
        importance: float,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Check for similar memories and merge if found
        
        Returns:
            True if merged with existing memory, False if added new
        """
        # Search for existing memories of same type
        existing_memories = await self.memory.search_long_term_memory(
            memory_type=memory_type,
            limit=50,
            min_importance=0.0
        )
        
        # Extract intent and key info from new content
        new_intent = self._extract_intent_from_memory(content)
        new_keywords = self._extract_keywords_from_memory(content)
        
        # Check for similar memories
        for mem in existing_memories:
            existing_content = mem.get("content", "")
            existing_intent = self._extract_intent_from_memory(existing_content)
            existing_keywords = self._extract_keywords_from_memory(existing_content)
            
            # Calculate similarity score
            similarity = self._calculate_memory_similarity(
                new_intent, new_keywords,
                existing_intent, existing_keywords
            )
            
            # If highly similar, merge
            if similarity >= 0.7:
                merged_content = self._merge_memory_content(existing_content, content)
                
                # Update existing memory with merged content
                await self._update_memory(
                    memory_id=mem["id"],
                    content=merged_content,
                    importance=max(importance, mem.get("importance", 0))
                )
                
                print(f"  [MERGED] Similarity: {similarity:.2f}")
                print(f"    Old: {existing_content[:50]}...")
                print(f"    New: {content[:50]}...")
                print(f"    Merged: {merged_content[:50]}...")
                return True
        
        # No similar memory found, add new
        await self.memory.add_to_long_term(
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            importance=importance
        )
        return False
    
    def _extract_intent_from_memory(self, content: str) -> str:
        """Extract intent from memory content"""
        # Look for intent pattern
        if "意图:" in content:
            start = content.find("意图:") + 3
            end = content.find("|", start)
            if end == -1:
                end = min(start + 10, len(content))
            return content[start:end].strip()
        if "角色:" in content:
            start = content.find("角色:") + 3
            end = content.find("|", start)
            if end == -1:
                end = min(start + 10, len(content))
            return content[start:end].strip()
        if "身份:" in content:
            start = content.find("身份:") + 3
            end = content.find("|", start)
            if end == -1:
                end = min(start + 10, len(content))
            return content[start:end].strip()
        return ""
    
    def _extract_keywords_from_memory(self, content: str) -> set:
        """Extract keywords from memory content"""
        import re
        # Extract Chinese words
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}', content)
        # Filter stop words
        stop_words = {'用户', '意图', '角色', '身份', 'AI', '对话', '请求', '类型', '关键', '实体'}
        return {w for w in words if w not in stop_words and len(w) >= 2}
    
    def _calculate_memory_similarity(
        self,
        new_intent: str, new_keywords: set,
        existing_intent: str, existing_keywords: set
    ) -> float:
        """Calculate similarity between two memories"""
        score = 0.0
        
        # Intent match (high weight)
        if new_intent and existing_intent:
            if new_intent == existing_intent:
                score += 0.5
            elif new_intent in existing_intent or existing_intent in new_intent:
                score += 0.3
        
        # Keyword overlap
        if new_keywords and existing_keywords:
            overlap = len(new_keywords & existing_keywords)
            total = max(len(new_keywords | existing_keywords), 1)
            score += 0.5 * (overlap / total)
        
        return min(score, 1.0)
    
    def _merge_memory_content(self, existing: str, new: str) -> str:
        """Merge two memory contents"""
        # Parse existing content
        existing_parts = existing.split(" | ")
        new_parts = new.split(" | ")
        
        # Merge parts
        merged = {}
        for part in existing_parts:
            if ":" in part:
                key, value = part.split(":", 1)
                merged[key.strip()] = value.strip()
        
        for part in new_parts:
            if ":" in part:
                key, value = part.split(":", 1)
                # Update with new value (newer takes precedence)
                merged[key.strip()] = value.strip()
        
        # Rebuild content
        return " | ".join([f"{k}:{v}" for k, v in merged.items()])
    
    async def _update_memory(self, memory_id: int, content: str, importance: float):
        """Update existing memory in database and re-index in RAG subsystem"""
        await self.memory.update_long_term(memory_id, content, importance)
    
    def _detect_role_assignment(self, message: str) -> Optional[str]:
        """Detect if user is assigning or removing a role to the AI"""
        role_patterns = {
            "猫娘": "猫娘", "喵": "猫娘",
            "助手": "助手", "assistant": "助手",
            "老师": "老师", "teacher": "老师",
            "专家": "专家", "expert": "专家",
            "朋友": "朋友", "friend": "朋友",
            "秘书": "秘书", "保姆": "保姆",
            "黑客": "黑客", "程序员": "程序员",
            "诗人": "诗人", "作家": "作家",
            "医生": "医生", "律师": "律师"
        }
        
        # Check for role assignment patterns
        assignment_patterns = ["你是", "你是", "当", "扮演", "作为", "变成", "成为"]
        
        for keyword, role in role_patterns.items():
            if keyword in message:
                # Check if it's a role assignment pattern
                for pattern in assignment_patterns:
                    if pattern in message:
                        return role
        
        # Check for role removal patterns
        removal_patterns = ["不是", "不再是", "别当", "别做", "停止"]
        for pattern in removal_patterns:
            if pattern in message:
                # Find which role is being removed
                for keyword, role in role_patterns.items():
                    if keyword in message:
                        return role
        
        return None
    
    def _extract_key_information(self, user_message: str, assistant_response: str) -> str:
        """
        Extract key information from dialogue using rule-based compression
        
        Returns a compressed summary with:
        - User intent/request
        - Key entities mentioned
        - Assistant's role/persona if defined
        - AI response key points
        """
        compressed_parts = []
        
        # 1. Extract user intent
        user_lower = user_message.lower()
        
        # Detect role assignment
        role_keywords = {
            "猫娘": "猫娘", "cat": "猫娘", "喵": "猫娘",
            "助手": "助手", "assistant": "助手",
            "老师": "老师", "teacher": "老师",
            "专家": "专家", "expert": "专家",
            "朋友": "朋友", "friend": "朋友"
        }
        
        detected_role = None
        for keyword, role in role_keywords.items():
            if keyword in user_message:
                detected_role = role
                break
        
        if detected_role:
            compressed_parts.append(f"角色:{detected_role}")
        
        # 2. Detect user request type
        request_types = {
            "写": "创作", "创作": "创作", "小说": "创作",
            "故事": "创作", "诗": "创作",
            "翻译": "翻译", "解释": "解释",
            "什么是": "查询", "你是谁": "身份",
            "回忆": "记忆", "记住": "记忆", "生日": "个人信息",
            "名字": "个人信息", "年龄": "个人信息", "喜欢": "偏好"
        }
        
        detected_request = None
        for keyword, req_type in request_types.items():
            if keyword in user_message:
                detected_request = req_type
                break
        
        if detected_request:
            compressed_parts.append(f"意图:{detected_request}")
        
        # 3. Extract persona from assistant response (shorter)
        persona_indicators = ["我是", "我叫", "名字"]
        for indicator in persona_indicators:
            if indicator in assistant_response:
                idx = assistant_response.find(indicator)
                # Get just the persona name, up to 30 chars
                persona_text = assistant_response[idx:idx+30].split("，")[0].split("。")[0].split("\n")[0]
                compressed_parts.append(f"身份:{persona_text}")
                break
        
        # 4. Extract AI response key points
        ai_key_points = self._extract_ai_key_points(assistant_response)
        if ai_key_points:
            compressed_parts.append(f"AI:{ai_key_points}")
        
        # 5. Build compressed memory
        if compressed_parts:
            compressed_memory = " | ".join(compressed_parts)
            # Add short user message
            compressed_memory += f" | 用户:{user_message[:30]}"
        else:
            # Fallback
            compressed_memory = f"对话 | 用户:{user_message[:20]} | AI:{assistant_response[:30]}"
        
        return compressed_memory
    
    def _extract_ai_key_points(self, response: str) -> str:
        """Extract key points from AI response"""
        # Remove common prefixes/suffixes
        response = response.strip()
        
        # Skip if too short
        if len(response) < 10:
            return response[:30]
        
        # Extract first meaningful sentence
        sentences = response.replace("！", "。").replace("？", "。").replace("...", "。").split("。")
        first_sentence = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= 5:
                first_sentence = sentence
                break
        
        if not first_sentence:
            first_sentence = response[:40]
        
        # Limit length
        if len(first_sentence) > 40:
            first_sentence = first_sentence[:40] + "..."
        
        # Remove emojis and special chars for cleaner output
        import re
        first_sentence = re.sub(r'[^\w\s，。、：！？]', '', first_sentence)
        
        return first_sentence
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities from text - meaningful words only"""
        import re
        
        entities = []
        
        # Extract Chinese words (2-4 chars)
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        
        # Common stop words
        stop_words = {
            '一个', '这个', '那个', '什么', '怎么', '可以', '就是', '不是', '没有',
            '因为', '所以', '但是', '然后', '如果', '虽然', '只是', '而且', '或者',
            '已经', '需要', '应该', '可能', '知道', '觉得', '认为', '希望', '喜欢',
            '今天', '明天', '昨天', '现在', '这里', '那里', '这些', '那些', '一些',
            '你好', '谢谢', '请', '帮', '想', '要', '会', '能', '在', '有', '是',
            '的', '了', '吗', '呢', '吧', '啊', '哦', '嗯', '呀', '啦', '喵',
            '主人', '一篇', '五百', '小说', '写一', '百字', '用户', '助手'
        }
        
        for word in chinese_words:
            if word not in stop_words and len(word) >= 2:
                entities.append(word)
        
        # Deduplicate and limit to 5
        unique_entities = list(dict.fromkeys(entities))[:5]
        
        return unique_entities
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.mcp_client:
            await mcp_manager.remove_client(self.agent_id)
        
        # Clear in-memory data (database persists)
        self.memory.clear_short_term_memory()
        self.memory.clear_working_memory()
