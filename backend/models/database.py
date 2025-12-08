"""
Database models for the A2A Agent System
"""
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Agent(Base):
    """Agent database model"""
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, default="")
    config = Column(JSON, nullable=False)
    status = Column(String, default="idle")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Conversation(Base):
    """Conversation history database model"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, index=True, nullable=False)
    messages = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
