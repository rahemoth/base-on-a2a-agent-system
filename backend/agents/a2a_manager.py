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
        logger.debug(f"Sending message to agent {agent_id}")
        
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
        
        logger.debug(f"Received response from agent {agent_id}")
        
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
            "content": f"Starting collaboration on task: {task}",
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
        
        # Initial message to coordinator
        current_message = f"Task: {task}\n\nYou are coordinating a collaboration with {len(agent_ids) - 1} other agents. Please provide your initial thoughts and approach."
        
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
                
                logger.debug(f"Processing agent {agent_name} ({idx + 1}/{len(agent_ids)})")
                
                # Customize message for each agent
                if idx == 0 and round_num == 0:
                    message_to_send = current_message
                else:
                    # Build context from previous responses (last 3 for context)
                    relevant_messages = [
                        f"{msg['metadata'].get('agent_name', 'Unknown')}: {msg['content']}"
                        for msg in collaboration_history
                        if msg['role'] == 'agent' and msg.get('metadata', {}).get('agent_id') != agent_id
                    ]
                    previous_responses = "\n\n".join(relevant_messages[-3:])
                    
                    if previous_responses:
                        message_to_send = f"Round {round_num + 1}/{max_rounds}\n\nPrevious contributions:\n{previous_responses}\n\nBased on the discussion so far, what is your contribution to the task?"
                    else:
                        message_to_send = f"Round {round_num + 1}/{max_rounds}\n\nTask: {task}\n\nPlease provide your thoughts and contribution."
                
                # Send message to agent and wait for completion
                try:
                    logger.debug(f"Sending message to agent {agent_name}")
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
                    
                    logger.debug(f"Agent {agent_name} completed task in round {round_num + 1}")
                    
                except Exception as e:
                    logger.error(f"Error getting response from agent {agent_name}: {str(e)}", exc_info=True)
                    collaboration_history.append({
                        "role": "agent",
                        "content": f"[{agent_name}]: Error - {str(e)}",
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
