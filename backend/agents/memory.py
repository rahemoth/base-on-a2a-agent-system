"""
Agent Memory System with RAG (Retrieval-Augmented Generation)
Delegates vector indexing and semantic search to the unified RAG subsystem.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from collections import deque
from pathlib import Path
import aiosqlite

from .embedding_service import EmbeddingService
from .rag_memory_system import RAGMemorySystem

logger = logging.getLogger(__name__)


class AgentMemory:
    """
    Memory system backed by the unified RAG subsystem.

    Features:
    - Short-term memory: Recent conversation (deque)
    - Working memory: Current task context (dict)
    - Long-term memory: Persistent SQLite + RAG retrieval (HNSW + inverted index + time index)
    - Semantic search: Delegated to HybridRetrievalSystem
    - RAG proxy methods: For /api/rag/ endpoint compatibility
    """

    def __init__(
        self,
        agent_id: str,
        short_term_capacity: int = 20,
        db_path: str = "./data/agent_memory.db",
        embedding_api_key: str = None,
        embedding_api_base_url: str = None,
        embedding_dimension: int = 768
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

        # Embedding service (shared by memory and RAG subsystem)
        self.embedding_service = EmbeddingService(
            dimension=embedding_dimension,
            use_api=bool(embedding_api_key),
            api_key=embedding_api_key,
            api_base_url=embedding_api_base_url
        )

        # Unified RAG subsystem
        self.rag_system = RAGMemorySystem(
            embedding_dimension=embedding_dimension
        )

        # Cache for embeddings (avoid recomputation)
        self._embedding_cache: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize the memory database and load records into RAG subsystem"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

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

        # Load existing memories into RAG subsystem
        await self._load_memories_to_index()

        rag_stats = self.rag_system.retrieval_system.get_stats()
        logger.info(
            f"Memory initialized for agent {self.agent_id}, "
            f"RAG indexed {rag_stats.get('num_documents', 0)} documents"
        )

    async def _load_memories_to_index(self):
        """Load existing memories from database into RAG subsystem"""
        try:
            memories = await self.search_long_term_memory(limit=1000)

            for mem in memories:
                content = mem.get("content", "")
                if content:
                    embedding = await self.embedding_service.generate(content)
                    doc_id = f"mem_{mem['id']}"
                    self.rag_system.retrieval_system.add_document(
                        doc_id=doc_id,
                        content=content,
                        embedding=embedding,
                        metadata={
                            "id": mem['id'],
                            "memory_type": mem.get("memory_type", ""),
                            "importance": mem.get("importance", 0.5)
                        },
                        timestamp=mem.get("timestamp", "")
                    )

            logger.info(f"Loaded {len(memories)} memories into RAG subsystem")
        except Exception as e:
            logger.error(f"Failed to load memories to RAG subsystem: {e}")

    def add_to_short_term(self, memory_item: Dict[str, Any]):
        """Add an item to short-term memory (conversation context)"""
        if "timestamp" not in memory_item:
            memory_item["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.short_term_memory.append(memory_item)

    def get_short_term_memory(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent short-term memory items"""
        if limit is None:
            return list(self.short_term_memory)
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
        Add an item to long-term memory with RAG indexing.
        Persists to SQLite and indexes in RAG subsystem (HNSW + inverted + time).
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

        # Generate embedding and add to RAG subsystem
        try:
            embedding = await self.embedding_service.generate(content)
            doc_id = f"mem_{memory_id}"
            self.rag_system.retrieval_system.add_document(
                doc_id=doc_id,
                content=content,
                embedding=embedding,
                metadata={
                    "id": memory_id,
                    "memory_type": memory_type,
                    "importance": importance
                },
                timestamp=timestamp
            )
            logger.debug(f"Added memory {memory_id} to RAG subsystem")
        except Exception as e:
            logger.error(f"Failed to add to RAG subsystem: {e}")

        return memory_id

    async def search_long_term_memory(
        self,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search long-term memory by type/importance (SQL-based)"""
        query = """
            SELECT id, memory_type, content, metadata, importance, timestamp, accessed_count
            FROM long_term_memory
            WHERE agent_id = ? AND importance >= ?
        """
        params: list = [self.agent_id, min_importance]

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

                if memories:
                    memory_ids = [m["id"] for m in memories]
                    placeholders = ",".join("?" * len(memory_ids))
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
        Semantic search using RAG subsystem (HNSW + hybrid retrieval).
        """
        query_embedding = await self.embedding_service.generate(query)

        # Delegate to RAG subsystem
        vector_results = self.rag_system.retrieval_system.search(
            query_embedding=query_embedding,
            k=top_k * 2
        )

        # Filter and map results to the expected format
        results = []
        for result in vector_results:
            score = result.get("score", 0.0)
            if score < min_similarity:
                continue

            meta = result.get("metadata", {})

            if memory_type and meta.get("memory_type") != memory_type:
                continue

            results.append({
                "id": meta.get("id"),
                "content": result.get("content", ""),
                "memory_type": meta.get("memory_type", ""),
                "importance": meta.get("importance", 0.5),
                "similarity": score,
                "timestamp": result.get("timestamp", "")
            })

            if len(results) >= top_k:
                break

        return results

    async def update_long_term(
        self,
        memory_id: int,
        content: str,
        importance: float
    ):
        """Update existing memory in database and re-index in RAG subsystem"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE long_term_memory
                SET content = ?, importance = ?, accessed_count = accessed_count + 1
                WHERE id = ?
            """, (content, importance, memory_id))
            await db.commit()

        # Re-generate embedding and update in RAG subsystem
        try:
            embedding = await self.embedding_service.generate(content)
            doc_id = f"mem_{memory_id}"
            # Remove old entry and re-add
            self.rag_system.retrieval_system.delete_document(doc_id)
            self.rag_system.retrieval_system.add_document(
                doc_id=doc_id,
                content=content,
                embedding=embedding,
                metadata={"id": memory_id, "importance": importance}
            )
        except Exception as e:
            logger.error(f"Failed to update RAG index: {e}")

    async def search_by_keywords(
        self,
        keywords: List[str],
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories by keywords (SQL-based, for backward compatibility)"""
        query = """
            SELECT id, memory_type, content, metadata, importance, timestamp, accessed_count
            FROM long_term_memory
            WHERE agent_id = ?
        """
        params: list = [self.agent_id]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

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
        """Update working memory (current task context)"""
        self.working_memory[key] = value

    def get_working_memory(self, key: str) -> Optional[Any]:
        """Get a value from working memory"""
        return self.working_memory.get(key)

    def clear_working_memory(self):
        """Clear working memory"""
        self.working_memory.clear()

    def update_environment_context(self, context: Dict[str, Any]):
        """Update environmental context"""
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
        """Save a task to task history"""
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
        """Update a task in task history"""
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
        """Get task history"""
        query = "SELECT * FROM task_history WHERE agent_id = ?"
        params: list = [self.agent_id]

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
        """Get formatted context for LLM prompting"""
        context_parts = []

        if self.environment_context:
            context_parts.append("Environment Context:")
            for key, value in self.environment_context.items():
                context_parts.append(f"  {key}: {value}")

        if self.working_memory:
            context_parts.append("\nCurrent Task Context:")
            for key, value in self.working_memory.items():
                context_parts.append(f"  {key}: {value}")

        recent_messages = self.get_short_term_memory(limit=max_messages)
        if recent_messages:
            context_parts.append("\nRecent Conversation:")
            for msg in recent_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_parts.append(f"  {role}: {content[:200]}")

        return "\n".join(context_parts) if context_parts else ""

    # ── RAG proxy methods (for /api/rag/ endpoint compatibility) ──

    @staticmethod
    def _sanitize_for_json(obj):
        """Recursively convert numpy types to native Python types for JSON serialization"""
        import numpy as np
        if isinstance(obj, dict):
            return {k: AgentMemory._sanitize_for_json(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [AgentMemory._sanitize_for_json(v) for v in obj]
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    def get_memory_stats(self) -> Dict[str, Any]:
        """Delegate to RAG subsystem for comprehensive memory stats"""
        return self._sanitize_for_json(self.rag_system.get_memory_stats())

    def get_entity_relations(self, entity_name: str) -> Dict[str, Any]:
        """Delegate to RAG subsystem for entity relations"""
        return self._sanitize_for_json(self.rag_system.get_entity_relations(entity_name))

    async def add_dialogue(
        self,
        dialogue: List[Dict[str, Any]],
        embeddings=None
    ) -> Dict[str, Any]:
        """
        Add dialogue to RAG subsystem.
        Generates embeddings if not provided.
        """
        if embeddings is None:
            embeddings = []
            for turn in dialogue:
                content = turn.get("content", "")
                emb = await self.embedding_service.generate(content)
                embeddings.append(emb)

        return self.rag_system.add_dialogue(dialogue, embeddings)

    async def query(
        self,
        query_embedding=None,
        query: str = None,
        k: int = 10,
        use_graph_reasoning: bool = False,
        entities=None,
        start_time=None,
        end_time=None,
        beam_width: int = 5
    ) -> Dict[str, Any]:
        """
        Query the RAG subsystem.
        If query text is provided, generates embedding automatically.
        """
        if query_embedding is None and query:
            query_embedding = await self.embedding_service.generate(query)

        if query_embedding is None:
            return {"status": "error", "results": [], "num_results": 0}

        result = self.rag_system.query(
            query_embedding=query_embedding,
            k=k,
            use_graph_reasoning=use_graph_reasoning,
            entities=entities,
            start_time=start_time,
            end_time=end_time,
            beam_width=beam_width
        )

        # Convert numpy types to native Python types for JSON serialization
        return self._sanitize_for_json(result)
