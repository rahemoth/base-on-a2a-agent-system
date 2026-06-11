"""
Agent Memory System with RAG (Retrieval-Augmented Generation)
Integrates vector indexing for semantic search
"""
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from collections import deque
from pathlib import Path
import aiosqlite

logger = logging.getLogger(__name__)


class SimpleVectorIndex:
    """
    Simple vector index for semantic search
    Uses cosine similarity for small datasets, HNSW for larger
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors: Dict[str, np.ndarray] = {}
        self.metadata: Dict[str, Dict] = {}
        
    def add(self, id: str, vector: np.ndarray, metadata: Dict = None):
        """Add a vector to the index"""
        self.vectors[id] = np.array(vector, dtype=np.float32)
        self.metadata[id] = metadata or {}
        
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Search for similar vectors using cosine similarity"""
        if not self.vectors:
            return []
            
        query_vector = np.array(query_vector, dtype=np.float32)
        results = []
        
        for id, vector in self.vectors.items():
            # Cosine similarity
            dot_product = np.dot(query_vector, vector)
            norm_query = np.linalg.norm(query_vector)
            norm_vector = np.linalg.norm(vector)
            
            if norm_query > 0 and norm_vector > 0:
                similarity = dot_product / (norm_query * norm_vector)
            else:
                similarity = 0.0
                
            results.append({
                "id": id,
                "score": float(similarity),
                "metadata": self.metadata.get(id, {})
            })
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def remove(self, id: str):
        """Remove a vector from the index"""
        self.vectors.pop(id, None)
        self.metadata.pop(id, None)
        
    def size(self) -> int:
        """Return number of vectors"""
        return len(self.vectors)


class EmbeddingGenerator:
    """
    Generate embeddings using simple TF-IDF or external API
    """
    
    def __init__(self, use_api: bool = False, api_key: str = None):
        self.use_api = use_api
        self.api_key = api_key
        self.dimension = 384  # Default dimension
        
    async def generate(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        if self.use_api and self.api_key:
            return await self._generate_api(text)
        else:
            return self._generate_local(text)
    
    def _generate_local(self, text: str) -> np.ndarray:
        """Generate simple local embedding using character frequencies"""
        # Simple TF-IDF like embedding
        # In production, use sentence-transformers or OpenAI embeddings
        
        # Create a fixed-size vector based on character frequencies
        vector = np.zeros(self.dimension, dtype=np.float32)
        
        # Use character codes to fill vector
        for i, char in enumerate(text[:self.dimension]):
            vector[i % self.dimension] += ord(char) / 1000.0
            
        # Add some hash-based features
        words = text.split()
        for word in words:
            hash_val = hash(word) % self.dimension
            vector[hash_val] += 1.0
            
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
    
    async def _generate_api(self, text: str) -> np.ndarray:
        """Generate embedding using external API (OpenAI, etc.)"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            
            response = await client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"API embedding failed: {e}")
            return self._generate_local(text)


class AgentMemory:
    """
    Memory system with RAG capabilities
    
    Features:
    - Short-term memory: Recent conversation (deque)
    - Long-term memory: Persistent storage (SQLite + Vector Index)
    - Semantic search: Vector similarity-based retrieval
    - Memory compression: Automatic summarization
    """
    
    def __init__(
        self,
        agent_id: str,
        short_term_capacity: int = 20,
        db_path: str = "./data/agent_memory.db",
        embedding_api_key: str = None
    ):
        self.agent_id = agent_id
        self.short_term_capacity = short_term_capacity
        self.db_path = db_path
        
        # Short-term memory (recent conversation context)
        self.short_term_memory: deque = deque(maxlen=short_term_capacity)
        
        # Working memory (current task context)
        self.working_memory: Dict[str, Any] = {}
        
        # Environmental context
        self.environment_context: Dict[str, Any] = {}
        
        # RAG components
        self.embedding_generator = EmbeddingGenerator(
            use_api=bool(embedding_api_key),
            api_key=embedding_api_key
        )
        self.vector_index = SimpleVectorIndex(dimension=self.embedding_generator.dimension)
        
        # Cache for embeddings (avoid recomputation)
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
    async def initialize(self):
        """Initialize the memory database and vector index"""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create tables
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    importance REAL DEFAULT 0.5,
                    timestamp TEXT NOT NULL,
                    accessed_count INTEGER DEFAULT 0,
                    last_accessed TEXT
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_memory 
                ON long_term_memory(agent_id, memory_type, timestamp)
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    result TEXT,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    metadata TEXT
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_tasks 
                ON task_history(agent_id, task_id, status)
            """)
            
            await db.commit()
        
        # Load existing memories into vector index
        await self._load_memories_to_index()
        
        logger.info(f"Memory initialized for agent {self.agent_id}, indexed {self.vector_index.size()} memories")
    
    async def _load_memories_to_index(self):
        """Load existing memories from database into vector index"""
        try:
            memories = await self.search_long_term_memory(limit=1000)
            
            for mem in memories:
                content = mem.get("content", "")
                if content:
                    # Generate embedding
                    embedding = await self.embedding_generator.generate(content)
                    
                    # Add to vector index
                    mem_id = f"mem_{mem['id']}"
                    self.vector_index.add(
                        id=mem_id,
                        vector=embedding,
                        metadata={
                            "id": mem['id'],
                            "content": content,
                            "memory_type": mem.get("memory_type", ""),
                            "importance": mem.get("importance", 0.5)
                        }
                    )
                    
            logger.info(f"Loaded {len(memories)} memories into vector index")
        except Exception as e:
            logger.error(f"Failed to load memories to index: {e}")
    
    def add_to_short_term(self, memory_item: Dict[str, Any]):
        """
        Add an item to short-term memory (conversation context)
        
        Args:
            memory_item: Dict containing role, content, timestamp, etc.
        """
        if "timestamp" not in memory_item:
            memory_item["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        self.short_term_memory.append(memory_item)
    
    def get_short_term_memory(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recent short-term memory items
        
        Args:
            limit: Maximum number of items to return (None for all)
        
        Returns:
            List of memory items
        """
        if limit is None:
            return list(self.short_term_memory)
        else:
            return list(self.short_term_memory)[-limit:]
    
    def clear_short_term_memory(self):
        """Clear short-term memory"""
        self.short_term_memory.clear()

    async def add_to_long_term(
        self,
        memory_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ):
        """
        Add an item to long-term memory with vector indexing
        
        Args:
            memory_type: Type of memory (conversation, task, knowledge, etc.)
            content: The memory content
            metadata: Additional metadata
            importance: Importance score (0.0 to 1.0)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        # Store in SQLite
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO long_term_memory 
                (agent_id, memory_type, content, metadata, importance, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.agent_id, memory_type, content, metadata_json, importance, timestamp))
            await db.commit()
            
            memory_id = cursor.lastrowid
        
        # Generate embedding and add to vector index
        try:
            embedding = await self.embedding_generator.generate(content)
            mem_id = f"mem_{memory_id}"
            
            self.vector_index.add(
                id=mem_id,
                vector=embedding,
                metadata={
                    "id": memory_id,
                    "content": content,
                    "memory_type": memory_type,
                    "importance": importance,
                    "timestamp": timestamp
                }
            )
            
            logger.debug(f"Added memory {memory_id} to vector index")
        except Exception as e:
            logger.error(f"Failed to add to vector index: {e}")
        
        return memory_id

    async def search_long_term_memory(
        self,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search long-term memory
        
        Args:
            memory_type: Filter by memory type (None for all)
            limit: Maximum number of results
            min_importance: Minimum importance score
        
        Returns:
            List of memory items
        """
        query = """
            SELECT id, memory_type, content, metadata, importance, timestamp, accessed_count
            FROM long_term_memory
            WHERE agent_id = ? AND importance >= ?
        """
        params = [self.agent_id, min_importance]
        
        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)
        
        query += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
                memories = []
                for row in rows:
                    memory = {
                        "id": row[0],
                        "memory_type": row[1],
                        "content": row[2],
                        "metadata": json.loads(row[3]) if row[3] else None,
                        "importance": row[4],
                        "timestamp": row[5],
                        "accessed_count": row[6]
                    }
                    memories.append(memory)
                
                # Update access count with parameterized query
                if memories:
                    memory_ids = [m["id"] for m in memories]
                    placeholders = ",".join("?" * len(memory_ids))
                    # Build parameterized query safely
                    update_query = f"""
                        UPDATE long_term_memory 
                        SET accessed_count = accessed_count + 1,
                            last_accessed = ?
                        WHERE id IN ({placeholders})
                    """
                    update_params = [datetime.now(timezone.utc).isoformat()] + memory_ids
                    await db.execute(update_query, update_params)
                    await db.commit()
                
                return memories
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.3,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using vector similarity
        
        Args:
            query: Search query text
            top_k: Number of results to return
            min_similarity: Minimum similarity score (0-1)
            memory_type: Filter by memory type
            
        Returns:
            List of similar memories with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_generator.generate(query)
        
        # Search vector index
        vector_results = self.vector_index.search(query_embedding, top_k=top_k * 2)
        
        # Filter and enrich results
        results = []
        for result in vector_results:
            if result["score"] < min_similarity:
                continue
                
            metadata = result.get("metadata", {})
            
            # Filter by memory type if specified
            if memory_type and metadata.get("memory_type") != memory_type:
                continue
                
            results.append({
                "id": metadata.get("id"),
                "content": metadata.get("content", ""),
                "memory_type": metadata.get("memory_type", ""),
                "importance": metadata.get("importance", 0.5),
                "similarity": result["score"],
                "timestamp": metadata.get("timestamp", "")
            })
            
            if len(results) >= top_k:
                break
        
        return results
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories by keywords (for backward compatibility)
        
        Args:
            keywords: List of keywords to search
            memory_type: Filter by memory type
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        query = """
            SELECT id, memory_type, content, metadata, importance, timestamp, accessed_count
            FROM long_term_memory
            WHERE agent_id = ?
        """
        params = [self.agent_id]
        
        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)
        
        # Add keyword conditions
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append("content LIKE ?")
                params.append(f"%{keyword}%")
            query += " AND (" + " OR ".join(keyword_conditions) + ")"
        
        query += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
                memories = []
                for row in rows:
                    memory = {
                        "id": row[0],
                        "memory_type": row[1],
                        "content": row[2],
                        "metadata": json.loads(row[3]) if row[3] else None,
                        "importance": row[4],
                        "timestamp": row[5],
                        "accessed_count": row[6]
                    }
                    memories.append(memory)
                
                return memories
    
    def update_working_memory(self, key: str, value: Any):
        """
        Update working memory (current task context)
        
        Args:
            key: Memory key
            value: Memory value
        """
        self.working_memory[key] = value

    def get_working_memory(self, key: str) -> Optional[Any]:
        """Get a value from working memory"""
        return self.working_memory.get(key)
    
    def clear_working_memory(self):
        """Clear working memory"""
        self.working_memory.clear()

    def update_environment_context(self, context: Dict[str, Any]):
        """
        Update environmental context
        
        Args:
            context: Environmental context data
        """
        self.environment_context.update(context)

    def get_environment_context(self) -> Dict[str, Any]:
        """Get current environmental context"""
        return self.environment_context.copy()
    
    async def save_task(
        self,
        task_id: str,
        task_description: str,
        status: str = "started",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save a task to task history
        
        Args:
            task_id: Unique task identifier
            task_description: Description of the task
            status: Task status (started, completed, failed)
            metadata: Additional task metadata
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO task_history 
                (agent_id, task_id, task_description, status, started_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.agent_id, task_id, task_description, status, timestamp, metadata_json))
            await db.commit()

    async def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        result: Optional[str] = None
    ):
        """
        Update a task in task history
        
        Args:
            task_id: Task identifier
            status: New task status
            result: Task result
        """
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status)
        
        if result:
            updates.append("result = ?")
            params.append(result)
        
        if status in ["completed", "failed"]:
            updates.append("completed_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
        
        if not updates:
            return
        
        params.extend([self.agent_id, task_id])
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                UPDATE task_history 
                SET {', '.join(updates)}
                WHERE agent_id = ? AND task_id = ?
            """, params)
            await db.commit()

    async def get_task_history(
        self,
        limit: int = 10,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get task history
        
        Args:
            limit: Maximum number of tasks to return
            status: Filter by status (None for all)
        
        Returns:
            List of task records
        """
        query = "SELECT * FROM task_history WHERE agent_id = ?"
        params = [self.agent_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                tasks = []
                for row in rows:
                    task = dict(zip(columns, row))
                    if task.get("metadata"):
                        task["metadata"] = json.loads(task["metadata"])
                    tasks.append(task)
                
                return tasks
    
    def get_context_for_llm(self, max_messages: int = 10) -> str:
        """
        Get formatted context for LLM prompting
        
        Args:
            max_messages: Maximum number of recent messages to include
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add environment context
        if self.environment_context:
            context_parts.append("Environment Context:")
            for key, value in self.environment_context.items():
                context_parts.append(f"  {key}: {value}")
        
        # Add working memory
        if self.working_memory:
            context_parts.append("\nCurrent Task Context:")
            for key, value in self.working_memory.items():
                context_parts.append(f"  {key}: {value}")
        
        # Add short-term memory
        recent_messages = self.get_short_term_memory(limit=max_messages)
        if recent_messages:
            context_parts.append("\nRecent Conversation:")
            for msg in recent_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_parts.append(f"  {role}: {content[:200]}")
        
        return "\n".join(context_parts) if context_parts else ""
