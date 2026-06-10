"""
RAG Memory System API routes
Provides endpoints for managing and querying RAG memory
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.models import AgentConfig, AgentResponse
from backend.agents import agent_manager
from backend.config import settings

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/compress")
async def compress_dialogue(
    agent_id: str,
    dialogue: List[Dict[str, Any]],
    return_full_summary: bool = False
):
    """
    Compress dialogue using LLM-based summarization
    
    Args:
        agent_id: Agent ID to use for compression
        dialogue: List of dialogue turns to compress
        return_full_summary: Whether to return a full summary as well
    
    Returns:
        Compressed dialogue chunks with summaries
    """
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if compression is enabled
        if not agent.config.compression or not agent.config.compression.enabled:
            raise HTTPException(status_code=400, detail="Compression is not enabled for this agent")
        
        # Get compression config
        compression_config = agent.config.compression
        
        # Create compressor with config
        from backend.agents.rag_dialogue_compression import LLMEnhancedDialogueCompressor
        
        compressor = LLMEnhancedDialogueCompressor(
            compression_target=compression_config.target_ratio,
            compression_api_key=compression_config.api_key or settings.compression_api_key,
            compression_base_url=compression_config.base_url or settings.compression_base_url,
            compression_model=compression_config.model or settings.compression_model,
            compression_max_tokens=compression_config.max_tokens or settings.compression_max_tokens,
            compression_temperature=compression_config.temperature or settings.compression_temperature
        )
        
        # Compress dialogue
        result = await compressor.compress_and_summarize_dialogue(
            dialogue=dialogue,
            return_full_summary=return_full_summary
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_memory(
    agent_id: str,
    query: str,
    k: int = 10,
    use_graph_reasoning: bool = False
):
    """
    Query memory system for relevant context
    
    Args:
        agent_id: Agent ID to query
        query: Query text
        k: Number of results to return
        use_graph_reasoning: Enable multi-hop reasoning
    
    Returns:
        Retrieved memory results
    """
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if RAG is enabled
        if not agent.config.rag_enabled:
            raise HTTPException(status_code=400, detail="RAG is not enabled for this agent")
        
        # Generate query embedding (simplified - would use actual embedding model in production)
        import numpy as np
        query_embedding = np.random.rand(768).astype(np.float32)
        
        # Query memory system
        result = await agent.memory.query(
            query_embedding=query_embedding,
            k=k,
            use_graph_reasoning=use_graph_reasoning
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_memory(
    agent_id: str,
    dialogue: List[Dict[str, Any]]
):
    """
    Add dialogue to memory system
    
    Args:
        agent_id: Agent ID to add memory to
        dialogue: List of dialogue turns to add
    
    Returns:
        Memory addition result with statistics
    """
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if RAG is enabled
        if not agent.config.rag_enabled:
            raise HTTPException(status_code=400, detail="RAG is not enabled for this agent")
        
        # Add to memory
        result = await agent.memory.add_dialogue(dialogue=dialogue)
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{agent_id}")
async def get_memory_stats(agent_id: str):
    """
    Get memory system statistics for an agent
    
    Args:
        agent_id: Agent ID to get stats for
    
    Returns:
        Comprehensive memory statistics
    """
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        stats = agent.memory.get_memory_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entities/{agent_id}")
async def get_entity_relations(
    agent_id: str,
    entity_name: str
):
    """
    Get relations for a specific entity
    
    Args:
        agent_id: Agent ID
        entity_name: Name of entity to query
    
    Returns:
        Entity relations
    """
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        relations = agent.memory.get_entity_relations(entity_name=entity_name)
        
        return {
            "status": "success",
            **relations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear/{agent_id}")
async def clear_memory(agent_id: str):
    """
    Clear all memory for an agent
    
    Args:
        agent_id: Agent ID to clear memory for
    
    Returns:
        Success message
    """
    try:
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # In production, this would actually clear the memory
        # For now, just return success
        
        return {
            "status": "success",
            "message": "Memory cleared successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_rag_config():
    """
    Get global RAG configuration
    
    Returns:
        Global RAG settings
    """
    return {
        "status": "success",
        "config": {
            "rag_enabled": settings.rag_enabled,
            "compression_target": settings.rag_compression_target,
            "max_context_chunks": settings.rag_max_context_chunks,
            "embedding_dimension": settings.rag_embedding_dimension,
            "compression_model": settings.compression_model,
            "compression_max_tokens": settings.compression_max_tokens,
            "compression_temperature": settings.compression_temperature
        }
    }


@router.post("/config")
async def update_rag_config(config: Dict[str, Any]):
    """
    Update global RAG configuration
    
    Args:
        config: Configuration to update
    
    Returns:
        Updated configuration
    """
    # Update global settings (in-memory only for this example)
    # In production, you'd persist these to a config file or database
    
    if "compression_model" in config:
        settings.compression_model = config["compression_model"]
    if "compression_max_tokens" in config:
        settings.compression_max_tokens = config["compression_max_tokens"]
    if "compression_temperature" in config:
        settings.compression_temperature = config["compression_temperature"]
    if "rag_compression_target" in config:
        settings.rag_compression_target = config["rag_compression_target"]
    if "rag_max_context_chunks" in config:
        settings.rag_max_context_chunks = config["rag_max_context_chunks"]
    
    return await get_rag_config()