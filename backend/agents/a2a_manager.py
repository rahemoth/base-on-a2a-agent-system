"""
A2A-compliant Agent Manager using the official a2a-sdk
"""
import uuid
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone

from a2a import types
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import RequestContext
from a2a.server.events import InMemoryQueueManager

from backend.agents.a2a_executor import LLMAgentExecutor
from backend.models import AgentConfig, AgentStatus, AgentResponse
from backend.config import settings
from backend.utils.a2a_utils import extract_text_from_parts

# Initialize logger at module level
logger = logging.getLogger(__name__)


class A2AAgentManager:
    """Manager for A2A-compliant agents"""
    
    def __init__(self):
        self.agents: Dict[str, LLMAgentExecutor] = {}
        self.agent_cards: Dict[str, types.AgentCard] = {}
        self.request_handlers: Dict[str, DefaultRequestHandler] = {}
        self.task_stores: Dict[str, InMemoryTaskStore] = {}
        self.agent_metadata: Dict[str, Dict] = {}
    
    def _create_agent_card(self, agent_id: str, config: AgentConfig) -> types.AgentCard:
        """Create an A2A agent card for the agent"""
        # Determine base URL for the agent
        protocol = "https" if settings.host != "localhost" and settings.host != "127.0.0.1" else "http"
        base_url = f"{protocol}://{settings.host}:{settings.port}"
        
        # Create agent card
        return types.AgentCard(
            name=config.name,
            description=config.description or f"AI Agent powered by {config.provider.value}",
            protocol_version="0.3.0",
            version="1.0.0",
            url=f"{base_url}/api/agents/{agent_id}",
            skills=[
                types.AgentSkill(
                    id="chat",
                    name="Chat",
                    description="Have a conversation with the agent",
                    tags=["chat", "conversation"]
                )
            ],
            capabilities=types.AgentCapabilities(
                push_notifications=False,
                streaming=False,  # Can be enabled later
            ),
            default_input_modes=["text"],
            default_output_modes=["text"],
        )
    
    async def create_agent(self, config: AgentConfig) -> AgentResponse:
        """Create a new A2A-compliant agent"""
        agent_id = str(uuid.uuid4())
        
        # Create agent executor
        # Per-agent API keys take priority over global settings
        executor = LLMAgentExecutor(
            agent_id=agent_id,
            config=config,
            google_api_key=config.google_api_key or settings.google_api_key,
            openai_api_key=config.openai_api_key or settings.openai_api_key,
            openai_base_url=settings.openai_base_url,
        )
        
        # Initialize MCP if configured
        await executor.initialize_mcp()
        
        # Create agent card
        agent_card = self._create_agent_card(agent_id, config)
        
        # Create task store and queue manager
        task_store = InMemoryTaskStore()
        queue_manager = InMemoryQueueManager()
        
        # Create request handler with proper parameters
        request_handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=task_store,
            queue_manager=queue_manager,
        )
        
        # Store everything
        self.agents[agent_id] = executor
        self.agent_cards[agent_id] = agent_card
        self.request_handlers[agent_id] = request_handler
        self.task_stores[agent_id] = task_store
        self.agent_metadata[agent_id] = {
            "config": config,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        
        return AgentResponse(
            id=agent_id,
            config=config,
            status=AgentStatus.IDLE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    async def get_agent(self, agent_id: str) -> Optional[LLMAgentExecutor]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    def get_agent_card(self, agent_id: str) -> Optional[types.AgentCard]:
        """Get an agent's A2A card"""
        return self.agent_cards.get(agent_id)
    
    def get_request_handler(self, agent_id: str) -> Optional[DefaultRequestHandler]:
        """Get an agent's request handler"""
        return self.request_handlers.get(agent_id)
    
    async def list_agents(self) -> List[AgentResponse]:
        """List all agents"""
        responses = []
        for agent_id, metadata in self.agent_metadata.items():
            responses.append(AgentResponse(
                id=agent_id,
                config=metadata["config"],
                status=AgentStatus.IDLE,
                created_at=metadata["created_at"],
                updated_at=metadata["updated_at"]
            ))
        return responses
    
    async def update_agent(self, agent_id: str, config: AgentConfig) -> Optional[AgentResponse]:
        """Update an agent's configuration"""
        if agent_id not in self.agents:
            return None
        
        # For now, we'll need to recreate the agent with new config
        # In a production system, you might want to handle this more gracefully
        await self.delete_agent(agent_id)
        
        # Create new agent with same ID
        # Per-agent API keys take priority over global settings
        executor = LLMAgentExecutor(
            agent_id=agent_id,
            config=config,
            google_api_key=config.google_api_key or settings.google_api_key,
            openai_api_key=config.openai_api_key or settings.openai_api_key,
            openai_base_url=settings.openai_base_url,
        )
        
        await executor.initialize_mcp()
        
        agent_card = self._create_agent_card(agent_id, config)
        task_store = InMemoryTaskStore()
        queue_manager = InMemoryQueueManager()
        request_handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=task_store,
            queue_manager=queue_manager,
        )
        
        self.agents[agent_id] = executor
        self.agent_cards[agent_id] = agent_card
        self.request_handlers[agent_id] = request_handler
        self.task_stores[agent_id] = task_store
        self.agent_metadata[agent_id] = {
            "config": config,
            "created_at": self.agent_metadata.get(agent_id, {}).get("created_at", datetime.now(timezone.utc)),
            "updated_at": datetime.now(timezone.utc),
        }
        
        return AgentResponse(
            id=agent_id,
            config=config,
            status=AgentStatus.IDLE,
            created_at=self.agent_metadata[agent_id]["created_at"],
            updated_at=datetime.now(timezone.utc)
        )
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        if agent_id not in self.agents:
            return False
        
        # Cleanup agent resources
        await self.agents[agent_id].cleanup()
        
        # Remove from storage
        del self.agents[agent_id]
        del self.agent_cards[agent_id]
        del self.request_handlers[agent_id]
        del self.task_stores[agent_id]
        del self.agent_metadata[agent_id]
        
        return True
    
    async def send_message(
        self,
        agent_id: str,
        message_text: str,
        context_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> types.Message:
        """Send a message to an agent and get response"""
        handler = self.request_handlers.get(agent_id)
        if not handler:
            logger.error(f"Agent {agent_id} not found")
            raise ValueError(f"Agent {agent_id} not found")
        
        # Create message
        message = types.Message(
            kind="message",
            message_id=str(uuid.uuid4()),
            role=types.Role.user,
            parts=[types.TextPart(kind="text", text=message_text)],
            context_id=context_id,
            task_id=task_id,
        )
        
        # Send message through handler
        params = types.MessageSendParams(message=message)
        
        # Call the handler's on_message_send method directly
        response = await handler.on_message_send(params)
        return response
    
    async def collaborate_agents(
        self,
        agent_ids: List[str],
        task: str,
        coordinator_id: Optional[str] = None,
        max_rounds: int = 5
    ) -> List[Dict]:
        """
        Facilitate collaboration between agents using A2A protocol with proper task completion tracking
        
        Args:
            agent_ids: List of agent IDs to collaborate. Must contain at least one agent.
            task: The task description for agents to collaborate on.
            coordinator_id: Optional ID of the agent to coordinate. If not specified, 
                          the first agent in agent_ids will be used as coordinator.
            max_rounds: Maximum number of collaboration rounds. Default is 5.
        
        Returns:
            List[Dict]: Collaboration history with the following structure for each entry:
                - role: "system" or "agent"
                - content: The message content
                - metadata: Dict containing agent_id, agent_name, and optionally "error": True
                - timestamp: ISO format timestamp string
        
        Raises:
            ValueError: If no agents are specified or if any agent ID is not found.
        """
        if not agent_ids:
            raise ValueError("No agents specified for collaboration")
        
        # Validate all agents exist
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
        
        # Use first agent as coordinator if not specified
        if coordinator_id:
            if coordinator_id not in self.agents:
                raise ValueError(f"Coordinator agent {coordinator_id} not found")
        else:
            coordinator_id = agent_ids[0]
        
        collaboration_history = []
        
        # Track task completion for each agent
        agent_task_status = {agent_id: {"completed": False, "result": None} for agent_id in agent_ids}
        
        # Initialize collaboration task
        collaboration_history.append({
            "role": "system",
            "content": f"开始协作任务: {task}",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Update environment context for all agents with collaboration info
        collaboration_context = {
            "in_collaboration": True,
            "total_agents": len(agent_ids),
            "agent_ids": agent_ids,
            "coordinator_id": coordinator_id,
            "task": task
        }
        
        for agent_id in agent_ids:
            executor = self.agents.get(agent_id)
            if executor:
                executor.memory.update_environment_context(collaboration_context)
        
        # Track coordinator's task assignments
        coordinator_assignments = {}
        
        # Collaboration rounds
        for round_num in range(max_rounds):
            logger.info(f"Collaboration round {round_num + 1}/{max_rounds}")
            
            # Round completion tracking
            round_start_time = datetime.now(timezone.utc)
            
            # Get responses from all agents in this round
            for idx, agent_id in enumerate(agent_ids):
                agent_metadata = self.agent_metadata.get(agent_id)
                if agent_metadata and "config" in agent_metadata:
                    agent_name = agent_metadata["config"].name
                else:
                    agent_name = agent_id
                
                
                is_coordinator = (agent_id == coordinator_id)
                
                # Customize message based on role (coordinator vs worker)
                if is_coordinator:
                    # Message for coordinator
                    if round_num == 0:
                        # Initial coordinator prompt - include other agents' capabilities
                        other_agents = [aid for aid in agent_ids if aid != coordinator_id]
                        agent_info_list = []
                        for aid in other_agents:
                            meta = self.agent_metadata.get(aid)
                            if meta and "config" in meta:
                                config = meta["config"]
                                agent_desc = f"- {config.name}"
                                if config.description:
                                    agent_desc += f": {config.description}"
                                if config.system_prompt:
                                    agent_desc += f"\n  系统提示: {config.system_prompt}"
                                agent_info_list.append(agent_desc)
                            else:
                                agent_info_list.append(f"- {aid}")
                        
                        agents_info = "\n".join(agent_info_list)
                        first_agent_name = agent_info_list[0].split(':')[0].strip('- ') if agent_info_list else "Agent"
                        
                        message_to_send = f"""任务: {task}

你是协调员智能体，与 {len(agent_ids) - 1} 个其他智能体协作。

可用智能体及其能力:
{agents_info}

重要约束:
- 总共有 {max_rounds} 轮完成此任务
- 当前是第 1/{max_rounds} 轮
- 任务必须在第 {max_rounds} 轮结束前完成
- 你需要为每个智能体分配具体的子任务

你作为协调员的职责:
1. 将主任务分解为更小的子任务
2. 根据每个智能体的能力和系统提示，为其分配合适的子任务
3. 明确指定谁做什么（例如："{first_agent_name} 应该..."）
4. 协调工作并确保在 {max_rounds} 轮内完成

请提供:
- 你的工作分配计划
- 每个智能体的具体分配

你的协调响应:"""
                    else:
                        # Subsequent coordinator prompts
                        worker_results = [
                            msg for msg in collaboration_history
                            if msg['role'] == 'agent' 
                            and msg.get('metadata', {}).get('round') == round_num
                            and msg.get('metadata', {}).get('agent_id') != coordinator_id
                        ]
                        
                        results_summary = "\n\n".join([
                            f"{msg['metadata'].get('agent_name', 'Unknown')}: {msg['content']}"
                            for msg in worker_results
                        ])
                        
                        message_to_send = f"""第 {round_num + 1}/{max_rounds} 轮 - 注意：任务必须在第 {max_rounds} 轮前完成

工作智能体已完成第 {round_num} 轮的分配任务:
{results_summary if results_summary else "暂无工作者响应"}

剩余轮次: {max_rounds - round_num}

作为协调员，请:
1. 审查已完成的工作
2. 如需要，为智能体分配下一步任务，或
3. 如任务完成，整合最终结果

你的协调响应:"""
                else:
                    # Message for worker agents
                    # Find the latest coordinator message that might contain their assignment
                    coordinator_messages = [
                        msg for msg in collaboration_history
                        if msg['role'] == 'agent'
                        and msg.get('metadata', {}).get('agent_id') == coordinator_id
                    ]
                    
                    if coordinator_messages:
                        latest_coordination = coordinator_messages[-1]['content']
                        message_to_send = f"""第 {round_num + 1}/{max_rounds} 轮 - 任务截止：第 {max_rounds} 轮

协调员指示:
{latest_coordination}

根据上述协调员的分配，完成你的具体子任务。
只专注于分配给你的工作。

你的工作成果:"""
                    else:
                        # Fallback if no coordinator message yet
                        message_to_send = f"""第 {round_num + 1}/{max_rounds} 轮 - 任务截止：第 {max_rounds} 轮

主任务: {task}

等待协调员分配并完成你被分配的子任务。

你的工作成果:"""
                
                # Send message to agent and wait for completion
                try:
                    response = await self.send_message(agent_id, message_to_send)
                    
                    # Extract text from response using centralized utility
                    text_response = extract_text_from_parts(response.parts)
                    
                    # Mark task as completed for this round
                    agent_task_status[agent_id]["completed"] = True
                    agent_task_status[agent_id]["result"] = text_response
                    
                    collaboration_history.append({
                        "role": "agent",
                        "content": f"[{agent_name}]: {text_response}",
                        "metadata": {
                            "agent_id": agent_id,
                            "agent_name": agent_name,
                            "round": round_num + 1,
                            "completed": True
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                except Exception as e:
                    logger.error(f"从智能体 {agent_name} 获取响应时出错: {str(e)}", exc_info=True)
                    collaboration_history.append({
                        "role": "agent",
                        "content": f"[{agent_name}]: 错误 - {str(e)}",
                        "metadata": {
                            "agent_id": agent_id,
                            "agent_name": agent_name,
                            "round": round_num + 1,
                            "error": True,
                            "completed": False
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    agent_task_status[agent_id]["completed"] = False
            
            # Check if all agents completed their tasks in this round
            all_completed = all(status["completed"] for status in agent_task_status.values())
            
            round_duration = (datetime.now(timezone.utc) - round_start_time).total_seconds()
            
            collaboration_history.append({
                "role": "system",
                "content": f"Round {round_num + 1} completed in {round_duration:.2f}s. All agents responded: {all_completed}",
                "metadata": {
                    "round": round_num + 1,
                    "duration": round_duration,
                    "all_completed": all_completed,
                    "agent_status": agent_task_status.copy()
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            logger.info(f"Round {round_num + 1} completed: all_agents_responded={all_completed}, duration={round_duration:.2f}s")
            
            # Reset completion status for next round
            for agent_id in agent_ids:
                agent_task_status[agent_id]["completed"] = False
        
        # Clear collaboration context from agents
        for agent_id in agent_ids:
            executor = self.agents.get(agent_id)
            if executor:
                executor.memory.update_environment_context({"in_collaboration": False})
        
        # Add final summary
        collaboration_history.append({
            "role": "system",
            "content": f"Collaboration completed after {max_rounds} rounds",
            "metadata": {"total_rounds": max_rounds},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return collaboration_history
    
    async def collaborate_agents_stream(
        self,
        agent_ids: List[str],
        task: str,
        coordinator_id: Optional[str] = None,
        max_rounds: int = 5
    ):
        """
        Stream collaboration messages in real-time using async generator
        
        Yields messages as they are generated during collaboration
        """
        if not agent_ids:
            raise ValueError("No agents specified for collaboration")
        
        # Validate all agents exist
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
        
        # Use first agent as coordinator if not specified
        if coordinator_id:
            if coordinator_id not in self.agents:
                raise ValueError(f"Coordinator agent {coordinator_id} not found")
        else:
            coordinator_id = agent_ids[0]
        
        # Track task completion for each agent
        agent_task_status = {agent_id: {"completed": False, "result": None} for agent_id in agent_ids}
        
        # Initialize collaboration task
        init_msg = {
            "role": "system",
            "content": f"开始协作任务: {task}",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        yield init_msg
        
        # Update environment context for all agents with collaboration info
        collaboration_context = {
            "in_collaboration": True,
            "total_agents": len(agent_ids),
            "agent_ids": agent_ids,
            "coordinator_id": coordinator_id,
            "task": task
        }
        
        for agent_id in agent_ids:
            executor = self.agents.get(agent_id)
            if executor:
                executor.memory.update_environment_context(collaboration_context)
        
        # Track messages for streaming mode
        stream_history = []
        
        # Collaboration rounds
        for round_num in range(max_rounds):
            logger.info(f"Collaboration round {round_num + 1}/{max_rounds}")
            
            # Round completion tracking
            round_start_time = datetime.now(timezone.utc)
            
            # Get responses from all agents in this round
            for idx, agent_id in enumerate(agent_ids):
                agent_metadata = self.agent_metadata.get(agent_id)
                if agent_metadata and "config" in agent_metadata:
                    agent_name = agent_metadata["config"].name
                else:
                    agent_name = agent_id
                
                
                is_coordinator = (agent_id == coordinator_id)
                
                # Customize message based on role (coordinator vs worker)
                if is_coordinator:
                    # Message for coordinator
                    if round_num == 0:
                        # Initial coordinator prompt - include other agents' capabilities
                        other_agents = [aid for aid in agent_ids if aid != coordinator_id]
                        agent_info_list = []
                        for aid in other_agents:
                            meta = self.agent_metadata.get(aid)
                            if meta and "config" in meta:
                                config = meta["config"]
                                agent_desc = f"- {config.name}"
                                if config.description:
                                    agent_desc += f": {config.description}"
                                if config.system_prompt:
                                    agent_desc += f"\n  系统提示: {config.system_prompt}"
                                agent_info_list.append(agent_desc)
                            else:
                                agent_info_list.append(f"- {aid}")
                        
                        agents_info = "\n".join(agent_info_list)
                        first_agent_name = agent_info_list[0].split(':')[0].strip('- ') if agent_info_list else "Agent"
                        
                        message_to_send = f"""任务: {task}

你是协调员智能体，与 {len(agent_ids) - 1} 个其他智能体协作。

可用智能体及其能力:
{agents_info}

重要约束:
- 总共有 {max_rounds} 轮完成此任务
- 当前是第 1/{max_rounds} 轮
- 任务必须在第 {max_rounds} 轮结束前完成
- 你需要为每个智能体分配具体的子任务

你作为协调员的职责:
1. 将主任务分解为更小的子任务
2. 根据每个智能体的能力和系统提示，为其分配合适的子任务
3. 明确指定谁做什么（例如："{first_agent_name} 应该..."）
4. 协调工作并确保在 {max_rounds} 轮内完成

请提供:
- 你的工作分配计划
- 每个智能体的具体分配

你的协调响应:"""
                    else:
                        # Subsequent coordinator prompts
                        worker_results = [
                            msg for msg in stream_history
                            if msg['role'] == 'agent' 
                            and msg.get('metadata', {}).get('round') == round_num
                            and msg.get('metadata', {}).get('agent_id') != coordinator_id
                        ]
                        
                        results_summary = "\n\n".join([
                            f"{msg['metadata'].get('agent_name', 'Unknown')}: {msg['content']}"
                            for msg in worker_results
                        ])
                        
                        message_to_send = f"""第 {round_num + 1}/{max_rounds} 轮 - 注意：任务必须在第 {max_rounds} 轮前完成

工作智能体已完成第 {round_num} 轮的分配任务:
{results_summary if results_summary else "暂无工作者响应"}

剩余轮次: {max_rounds - round_num}

作为协调员，请:
1. 审查已完成的工作
2. 如需要，为智能体分配下一步任务，或
3. 如任务完成，整合最终结果

你的协调响应:"""
                else:
                    # Message for worker agents
                    # Find the latest coordinator message
                    coordinator_messages = [
                        msg for msg in stream_history
                        if msg['role'] == 'agent'
                        and msg.get('metadata', {}).get('agent_id') == coordinator_id
                    ]
                    
                    if coordinator_messages:
                        latest_coordination = coordinator_messages[-1]['content']
                        message_to_send = f"""第 {round_num + 1}/{max_rounds} 轮 - 任务截止：第 {max_rounds} 轮

协调员指示:
{latest_coordination}

根据上述协调员的分配，完成你的具体子任务。
只专注于分配给你的工作。

你的工作成果:"""
                    else:
                        # Fallback if no coordinator message yet
                        message_to_send = f"""第 {round_num + 1}/{max_rounds} 轮 - 任务截止：第 {max_rounds} 轮

主任务: {task}

等待协调员分配并完成你被分配的子任务。

你的工作成果:"""
                
                # Send message to agent and wait for completion
                try:
                    response = await self.send_message(agent_id, message_to_send)
                    
                    # Extract text from response using centralized utility
                    text_response = extract_text_from_parts(response.parts)
                    
                    # Mark task as completed for this round
                    agent_task_status[agent_id]["completed"] = True
                    agent_task_status[agent_id]["result"] = text_response
                    
                    agent_msg = {
                        "role": "agent",
                        "content": f"[{agent_name}]: {text_response}",
                        "metadata": {
                            "agent_id": agent_id,
                            "agent_name": agent_name,
                            "round": round_num + 1,
                            "completed": True
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    stream_history.append(agent_msg)
                    yield agent_msg
                except Exception as e:
                    logger.error(f"从智能体 {agent_name} 获取响应时出错: {str(e)}", exc_info=True)
                    error_msg = {
                        "role": "agent",
                        "content": f"[{agent_name}]: 错误 - {str(e)}",
                        "metadata": {
                            "agent_id": agent_id,
                            "agent_name": agent_name,
                            "round": round_num + 1,
                            "error": True,
                            "completed": False
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    stream_history.append(error_msg)
                    yield error_msg
                    agent_task_status[agent_id]["completed"] = False
            
            # Check if all agents completed their tasks in this round
            all_completed = all(status["completed"] for status in agent_task_status.values())
            
            round_duration = (datetime.now(timezone.utc) - round_start_time).total_seconds()
            
            round_msg = {
                "role": "system",
                "content": f"Round {round_num + 1} completed in {round_duration:.2f}s. All agents responded: {all_completed}",
                "metadata": {
                    "round": round_num + 1,
                    "duration": round_duration,
                    "all_completed": all_completed,
                    "agent_status": agent_task_status.copy()
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            yield round_msg
            
            logger.info(f"Round {round_num + 1} completed: all_agents_responded={all_completed}, duration={round_duration:.2f}s")
            
            # Reset completion status for next round
            for agent_id in agent_ids:
                agent_task_status[agent_id]["completed"] = False
        
        # Clear collaboration context from agents
        for agent_id in agent_ids:
            executor = self.agents.get(agent_id)
            if executor:
                executor.memory.update_environment_context({"in_collaboration": False})
        
        # Add final summary
        final_msg = {
            "role": "system",
            "content": f"Collaboration completed after {max_rounds} rounds",
            "metadata": {"total_rounds": max_rounds},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        yield final_msg
    
    async def cleanup_all(self):
        """Cleanup all agents"""
        for agent in self.agents.values():
            await agent.cleanup()
        self.agents.clear()
        self.agent_cards.clear()
        self.request_handlers.clear()
        self.task_stores.clear()
        self.agent_metadata.clear()


# Global A2A agent manager instance
a2a_agent_manager = A2AAgentManager()
