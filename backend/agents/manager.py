"""
Agent Manager for handling agent lifecycle and operations
"""
import uuid
from typing import Dict, Optional, List
from datetime import datetime

from backend.agents.a2a_agent import A2AAgent
from backend.models import AgentConfig, AgentStatus, AgentResponse
from backend.config import settings


class AgentManager:
    """Manager for all agents in the system"""
    
    def __init__(self):
        self.agents: Dict[str, A2AAgent] = {}
    
    async def create_agent(self, config: AgentConfig) -> AgentResponse:
        """Create a new agent"""
        agent_id = str(uuid.uuid4())
        agent = A2AAgent(agent_id, config)
        
        # Initialize agent with appropriate API key(s)
        google_api_key = settings.google_api_key
        openai_api_key = settings.openai_api_key
        
        await agent.initialize(google_api_key=google_api_key, openai_api_key=openai_api_key)
        self.agents[agent_id] = agent
        
        return AgentResponse(
            id=agent_id,
            config=config,
            status=agent.status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def get_agent(self, agent_id: str) -> Optional[A2AAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    async def list_agents(self) -> List[AgentResponse]:
        """List all agents"""
        return [
            AgentResponse(
                id=agent_id,
                config=agent.config,
                status=agent.status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for agent_id, agent in self.agents.items()
        ]
    
    async def update_agent(self, agent_id: str, config: AgentConfig) -> Optional[AgentResponse]:
        """Update an agent's configuration"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        # Update configuration
        agent.config = config
        
        # Reinitialize with both API keys
        google_api_key = settings.google_api_key
        openai_api_key = settings.openai_api_key
        await agent.initialize(google_api_key=google_api_key, openai_api_key=openai_api_key)
        
        return AgentResponse(
            id=agent_id,
            config=config,
            status=agent.status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        await agent.cleanup()
        del self.agents[agent_id]
        return True
    
    async def send_message_to_agent(
        self,
        agent_id: str,
        message: str,
        context: Optional[List] = None,
        stream: bool = False
    ):
        """Send a message to an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        return await agent.send_message(message, context, stream)
    
    async def collaborate_agents(
        self,
        agent_ids: List[str],
        task: str,
        coordinator_id: Optional[str] = None,
        max_rounds: int = 5
    ):
        """Facilitate collaboration between agents"""
        if not agent_ids:
            raise ValueError("No agents specified for collaboration")
        
        # Get all agents
        agents = []
        for agent_id in agent_ids:
            agent = self.agents.get(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            agents.append(agent)
        
        # Use first agent as coordinator if not specified
        if coordinator_id:
            coordinator = self.agents.get(coordinator_id)
            if not coordinator:
                raise ValueError(f"Coordinator agent {coordinator_id} not found")
        else:
            coordinator = agents[0]
            agents = agents[1:]
        
        # Start collaboration
        return await coordinator.collaborate(agents, task, max_rounds)
    
    async def cleanup_all(self):
        """Cleanup all agents"""
        for agent in self.agents.values():
            await agent.cleanup()
        self.agents.clear()


# Global agent manager instance
agent_manager = AgentManager()
