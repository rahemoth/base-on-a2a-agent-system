"""
Database manager for persistent storage
"""
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from backend.models.database import Base, Agent, Conversation

logger = logging.getLogger(__name__)

# Database URL - using SQLite for simplicity
DATABASE_URL = "sqlite+aiosqlite:///./data/agents.db"


class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
        
    async def initialize(self):
        """Initialize database connection and create tables"""
        import os
        os.makedirs("data", exist_ok=True)
        
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
    
    async def save_agent(self, agent_id: str, config: dict, status: str = "idle") -> bool:
        """Save or update agent to database"""
        try:
            async with self.async_session() as session:
                # Check if agent exists
                result = await session.get(Agent, agent_id)
                
                if result:
                    # Update existing agent
                    result.config = config
                    result.name = config.get("name", "Unnamed Agent")
                    result.description = config.get("description", "")
                    result.status = status
                    result.updated_at = datetime.utcnow()
                else:
                    # Create new agent
                    agent = Agent(
                        id=agent_id,
                        name=config.get("name", "Unnamed Agent"),
                        description=config.get("description", ""),
                        config=config,
                        status=status,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(agent)
                
                await session.commit()
                logger.info(f"Agent {agent_id} saved to database")
                return True
        except Exception as e:
            logger.error(f"Error saving agent to database: {e}")
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent from database"""
        try:
            async with self.async_session() as session:
                result = await session.get(Agent, agent_id)
                if result:
                    return {
                        "id": result.id,
                        "name": result.name,
                        "description": result.description,
                        "config": result.config,
                        "status": result.status,
                        "created_at": result.created_at.isoformat() if result.created_at else None,
                        "updated_at": result.updated_at.isoformat() if result.updated_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting agent from database: {e}")
            return None
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents from database"""
        try:
            async with self.async_session() as session:
                from sqlalchemy import select
                result = await session.execute(select(Agent))
                agents = result.scalars().all()
                
                return [
                    {
                        "id": agent.id,
                        "name": agent.name,
                        "description": agent.description,
                        "config": agent.config,
                        "status": agent.status,
                        "created_at": agent.created_at.isoformat() if agent.created_at else None,
                        "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
                    }
                    for agent in agents
                ]
        except Exception as e:
            logger.error(f"Error listing agents from database: {e}")
            return []
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete agent from database"""
        try:
            async with self.async_session() as session:
                result = await session.get(Agent, agent_id)
                if result:
                    await session.delete(result)
                    await session.commit()
                    logger.info(f"Agent {agent_id} deleted from database")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting agent from database: {e}")
            return False
    
    async def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Update agent status in database"""
        try:
            async with self.async_session() as session:
                result = await session.get(Agent, agent_id)
                if result:
                    result.status = status
                    result.updated_at = datetime.utcnow()
                    await session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            return False
    
    async def save_conversation(self, agent_id: str, messages: List[Dict[str, Any]]) -> bool:
        """Save conversation to database"""
        try:
            async with self.async_session() as session:
                conversation = Conversation(
                    id=f"{agent_id}_{datetime.utcnow().timestamp()}",
                    agent_id=agent_id,
                    messages=messages,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(conversation)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False
    
    async def get_conversations(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversations for an agent"""
        try:
            async with self.async_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(Conversation)
                    .where(Conversation.agent_id == agent_id)
                    .order_by(Conversation.created_at.desc())
                    .limit(limit)
                )
                conversations = result.scalars().all()
                
                return [
                    {
                        "id": conv.id,
                        "agent_id": conv.agent_id,
                        "messages": conv.messages,
                        "created_at": conv.created_at.isoformat() if conv.created_at else None,
                        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
                    }
                    for conv in conversations
                ]
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []


# Global database manager instance
db_manager = DatabaseManager()