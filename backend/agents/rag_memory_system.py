"""
RAG Memory System Integration
Integrates all RAG memory components into a cohesive system
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging
import numpy as np

from .rag_vector_index import HNSWIndex, VectorNode
from .rag_dialogue_compression import HierarchicalDialogueCompressor, DialogueChunk
from .rag_hybrid_retrieval import HybridRetrievalSystem, Document, _sanitize_collection_name
from .rag_memory_graph import MemoryGraph, MemoryGraphQueryEngine, Entity, Relation
from .rag_consistency_manager import ConsistencyManager, MemoryFact
from .rag_performance_optimizer import LRUCache, ProductQuantizer, QueryOptimizer, PerformanceMonitor
from .rag_entity_extraction import LLMEntityRelationExtractor

logger = logging.getLogger(__name__)


class RAGMemorySystem:
    """
    Complete RAG memory system integrating all components

    Architecture:
    1. Hot Memory: Recent dialogue chunks (Dialogue Compressor)
    2. Warm Memory: Vector-indexed summaries (Hybrid Retrieval, ChromaDB-backed)
    3. Cold Memory: Entity relationships (Memory Graph, rebuilt from ChromaDB metadata)
    4. Consistency: Unified fact management (Consistency Manager)
    5. Optimization: Caching and quantization (Performance Optimizer)

    Flow:
    - Input dialogue -> Compress -> Index -> Store ( + LLM entity/relation extraction)
    - Query -> Optimize -> Retrieve -> Re-rank -> Return
    """

    def __init__(
        self,
        embedding_dimension: int = 768,
        compression_target: float = 0.3,
        cache_capacity: int = 1000,
        enable_quantization: bool = True,
        agent_id: Optional[str] = None,
        chroma_persist_dir: Optional[str] = None,
        entity_extraction_enabled: bool = False,
        entity_extraction_model: str = "gpt-4o-mini",
        entity_extraction_max_tokens: int = 800,
        entity_extraction_temperature: float = 0.2,
    ):
        self.embedding_dimension = embedding_dimension
        self.agent_id = agent_id

        # Core components
        self.compressor = HierarchicalDialogueCompressor(
            chunk_size=5,
            compression_target=compression_target
        )

        collection_name = (
            _sanitize_collection_name(agent_id) if agent_id and chroma_persist_dir else None
        )
        self.retrieval_system = HybridRetrievalSystem(
            dimension=embedding_dimension,
            chroma_persist_dir=chroma_persist_dir,
            collection_name=collection_name,
        )

        self.memory_graph = MemoryGraph()
        self.graph_query_engine = MemoryGraphQueryEngine(self.memory_graph)

        # Rebuild entity graph from persisted ChromaDB metadata (if using chroma)
        if self.retrieval_system.get_backend_type() == "chroma":
            self._load_graph_from_chroma()

        self.consistency_manager = ConsistencyManager()

        # LLM entity/relation extraction (client injected later via set_llm_client)
        self.entity_extraction_enabled = entity_extraction_enabled
        self.entity_extractor = LLMEntityRelationExtractor(
            client=None,
            model=entity_extraction_model,
            max_tokens=entity_extraction_max_tokens,
            temperature=entity_extraction_temperature,
        )

        # Optimization
        self.optimizer = QueryOptimizer(
            cache_capacity=cache_capacity,
            max_memory_bytes=100 * 1024 * 1024  # 100MB
        )

        self.monitor = PerformanceMonitor()

        self.quantizer = None
        if enable_quantization:
            self.quantizer = ProductQuantizer(
                dimension=embedding_dimension,
                n_subspaces=8,
                n_centroids=256
            )

    def set_llm_client(self, client: Any) -> None:
        """Inject an AsyncOpenAI-compatible client for entity/relation extraction."""
        self.entity_extractor.set_client(client)
        if client is not None and self.entity_extraction_enabled:
            logger.info(f"RAG system for agent {self.agent_id}: LLM extraction enabled")

    def _load_graph_from_chroma(self) -> None:
        """Rebuild MemoryGraph entities + relations from persisted ChromaDB metadata."""
        if self.retrieval_system.get_backend_type() != "chroma":
            return
        for item in self.retrieval_system.vector_index.get_all():
            meta = item.get("metadata", {})
            # Need an embedding for graph entities; reuse the doc embedding if present
            emb = item.get("embedding")
            if emb is None:
                emb = np.zeros(self.embedding_dimension, dtype=np.float32)
            for name in meta.get("entities", []) or []:
                if isinstance(name, str) and name:
                    eid = f"entity_{name}"
                    if eid not in self.memory_graph.entities:
                        self.memory_graph.add_entity(
                            entity_id=eid, name=name, entity_type="concept",
                            embedding=emb, properties={"mentions": 1},
                        )
            for rel in meta.get("relations", []) or []:
                if not isinstance(rel, dict):
                    continue
                src, pred, tgt = rel.get("subject"), rel.get("predicate"), rel.get("object")
                if not (src and pred and tgt):
                    continue
                src_id, tgt_id = f"entity_{src}", f"entity_{tgt}"
                for name, eid in ((src, src_id), (tgt, tgt_id)):
                    if eid not in self.memory_graph.entities:
                        self.memory_graph.add_entity(
                            entity_id=eid, name=name, entity_type="concept",
                            embedding=emb, properties={"mentions": 1},
                        )
                relation_id = f"rel_{item['id']}_{src_id}_{tgt_id}_{pred}"
                if relation_id in self.memory_graph.relations:
                    continue
                try:
                    self.memory_graph.add_relation(
                        relation_id=relation_id, source_id=src_id, target_id=tgt_id,
                        relation_type=pred, weight=float(meta.get("information_density", 0.5)),
                    )
                except ValueError:
                    continue
        logger.info(
            f"RAG system for agent {self.agent_id}: rebuilt graph from ChromaDB "
            f"({len(self.memory_graph.entities)} entities, {len(self.memory_graph.relations)} relations)"
        )
            
    async def add_dialogue(
        self,
        dialogue: List[Dict[str, Any]],
        embeddings: Optional[List[np.ndarray]] = None
    ) -> Dict[str, Any]:
        """
        Add dialogue to memory system

        Args:
            dialogue: List of dialogue turns
            embeddings: Pre-computed embeddings (optional)

        Returns:
            Operation result with statistics
        """
        self.monitor.start_timer("add_dialogue")

        # Step 1: Compress dialogue
        chunks = self.compressor.compress_dialogue(dialogue, embeddings)

        # Step 2: Extract entities/relations (LLM if enabled + client available,
        # else empty → co-occurrence fallback). Done before add_document so the
        # relations can be persisted into the ChromaDB metadata in one write.
        for chunk in chunks:
            chunk_text = " ".join([t.get("content", "") for t in chunk.turns])
            extracted = await self._extract_entities_and_relations(chunk_text)

            if extracted["entities"]:
                chunk.entities = [e["name"] for e in extracted["entities"]]
                entity_types = {e["name"]: e["type"] for e in extracted["entities"]}
            else:
                entity_types = {}

            # Add entities to graph
            for entity_name in chunk.entities:
                entity_id = f"entity_{entity_name}"
                if entity_id not in self.memory_graph.entities:
                    self.memory_graph.add_entity(
                        entity_id=entity_id,
                        name=entity_name,
                        entity_type=entity_types.get(entity_name, "concept"),
                        embedding=chunk.embedding,
                        properties={"mentions": 1}
                    )
                else:
                    entity = self.memory_graph.entities[entity_id]
                    entity.properties["mentions"] = entity.properties.get("mentions", 0) + 1

            # Build relations: LLM semantic triples if available, else co-occurrence
            relations_for_meta = []
            if extracted["relations"]:
                for rel in extracted["relations"]:
                    src_name, pred, tgt_name = rel["subject"], rel["predicate"], rel["object"]
                    src_id = f"entity_{src_name}"
                    tgt_id = f"entity_{tgt_name}"
                    for name, eid in ((src_name, src_id), (tgt_name, tgt_id)):
                        if eid not in self.memory_graph.entities:
                            self.memory_graph.add_entity(
                                entity_id=eid, name=name,
                                entity_type=entity_types.get(name, "concept"),
                                embedding=chunk.embedding,
                                properties={"mentions": 1},
                            )
                    relation_id = f"rel_{chunk.chunk_id}_{src_id}_{tgt_id}_{pred}"
                    if relation_id in self.memory_graph.relations:
                        continue
                    try:
                        self.memory_graph.add_relation(
                            relation_id=relation_id,
                            source_id=src_id,
                            target_id=tgt_id,
                            relation_type=pred,
                            weight=chunk.information_density,
                        )
                        relations_for_meta.append(rel)
                    except ValueError:
                        continue
            else:
                # Co-occurrence fallback when LLM extraction is unavailable/empty
                chunk_entity_ids = [f"entity_{name}" for name in chunk.entities]
                for i in range(len(chunk_entity_ids)):
                    for j in range(i + 1, len(chunk_entity_ids)):
                        src, tgt = chunk_entity_ids[i], chunk_entity_ids[j]
                        if src == tgt:
                            continue
                        relation_id = f"rel_{chunk.chunk_id}_{src}_{tgt}"
                        if relation_id in self.memory_graph.relations:
                            continue
                        try:
                            self.memory_graph.add_relation(
                                relation_id=relation_id,
                                source_id=src,
                                target_id=tgt,
                                relation_type="co_occurs",
                                weight=chunk.information_density,
                            )
                            relations_for_meta.append({
                                "subject": chunk.entities[i],
                                "predicate": "co_occurs",
                                "object": chunk.entities[j],
                            })
                        except ValueError:
                            continue

            # Step 3: Add chunk to retrieval system with entities + relations in
            # metadata, so the MemoryGraph can be rebuilt from ChromaDB on restart.
            self.retrieval_system.add_document(
                doc_id=chunk.chunk_id,
                content=chunk.summary,
                embedding=chunk.embedding,
                entities=chunk.entities,
                timestamp=chunk.timestamp,
                metadata={
                    "chunk_id": chunk.chunk_id,
                    "turns": chunk.start_turn,
                    "turn_count": len(chunk.turns),
                    "information_density": chunk.information_density,
                    "relations": relations_for_meta,
                }
            )

        # Step 4: Add to consistency manager
        for chunk in chunks:
            self.consistency_manager.add_memory(
                fact_id=chunk.chunk_id,
                content=chunk.summary,
                embedding=chunk.embedding,
                entities=chunk.entities,
                source_confidence=chunk.information_density
            )

        # New data invalidates any cached query results — otherwise repeat
        # queries would keep returning the pre-add result set.
        self.optimizer.cache.clear()

        self.monitor.end_timer("add_dialogue")

        return {
            "status": "success",
            "num_chunks": len(chunks),
            "compression_stats": self.compressor.get_compression_stats(),
            "graph_stats": self.graph_query_engine.get_stats(),
            "consistency_stats": self.consistency_manager.get_stats()
        }

    async def _extract_entities_and_relations(self, text: str) -> Dict[str, Any]:
        """Run LLM extraction if enabled and a client is available, else return empty."""
        if self.entity_extraction_enabled and self.entity_extractor.available:
            return await self.entity_extractor.extract(text)
        return {"entities": [], "relations": []}
        
    def query(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        entities: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        use_graph_reasoning: bool = False,
        beam_width: int = 5
    ) -> Dict[str, Any]:
        """
        Query the memory system
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            entities: Filter by entities
            start_time: Start of time range
            end_time: End of time range
            use_graph_reasoning: Enable multi-hop reasoning
            beam_width: Beam width for graph search
            
        Returns:
            Query results with metadata
        """
        self.monitor.start_timer("query")
        
        # Generate query hash for caching
        query_hash = self._generate_query_hash(
            query_embedding, entities, start_time, end_time
        )

        # Check cache hit BEFORE optimize_query, which itself puts the result
        # back into the cache — checking afterwards would always report True.
        cache_hit = self.optimizer.cache.get(query_hash) is not None

        # Define query function
        def _execute_query():
            results = self.retrieval_system.search(
                query_embedding=query_embedding,
                k=k,
                entities=entities,
                start_time=start_time,
                end_time=end_time,
                use_reranking=True
            )

            # Add graph reasoning if enabled
            if use_graph_reasoning and entities:
                graph_results = self._perform_graph_reasoning(
                    query_embedding,
                    entities[0],  # Use first entity as start
                    beam_width
                )
                results.extend(graph_results)

            return results

        # Execute with optimization
        results = self.optimizer.optimize_query(
            query_hash=query_hash,
            query_func=_execute_query
        )

        self.monitor.end_timer("query")

        return {
            "status": "success",
            "results": results[:k],
            "num_results": len(results),
            "query_stats": {
                "cache_hit": cache_hit,
                "entities_filter": entities,
                "time_filter": (start_time, end_time)
            }
        }
        
    def _perform_graph_reasoning(
        self,
        query_embedding: np.ndarray,
        start_entity: str,
        beam_width: int
    ) -> List[Dict[str, Any]]:
        """Perform multi-hop reasoning on knowledge graph"""
        entity_id = f"entity_{start_entity}"
        
        if entity_id not in self.memory_graph.entities:
            return []
            
        paths = self.graph_query_engine.query_path(
            start_entity_id=entity_id,
            query_embedding=query_embedding,
            beam_width=beam_width
        )
        
        # Convert paths to result format
        results = []
        for path in paths[:3]:  # Top 3 paths
            path_explanation = self.graph_query_engine.path_finder.explain_path(
                self.memory_graph,
                path
            )
            
            results.append({
                "doc_id": f"path_{path.nodes[-1]}",
                "score": path.semantic_score,
                "content": path_explanation,
                "metadata": {
                    "type": "graph_reasoning",
                    "path_length": len(path.nodes),
                    "path_nodes": path.nodes
                },
                "timestamp": datetime.now().isoformat()
            })
            
        return results
        
    def train_quantizer(self, vectors: np.ndarray, n_iter: int = 25):
        """Train product quantizer on vectors"""
        if self.quantizer:
            self.monitor.start_timer("train_quantizer")
            self.quantizer.train(vectors, n_iter)
            self.monitor.end_timer("train_quantizer")
            
    def get_entity_relations(self, entity_name: str) -> Dict[str, Any]:
        """Get relations for an entity"""
        entity_id = f"entity_{entity_name}"
        
        neighbors = self.memory_graph.get_neighbors(entity_id)
        
        return {
            "entity_name": entity_name,
            "num_relations": len(neighbors),
            "relations": neighbors
        }
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        return {
            "compression": self.compressor.get_compression_stats(),
            "retrieval": self.retrieval_system.get_stats(),
            "graph": self.graph_query_engine.get_stats(),
            "consistency": self.consistency_manager.get_stats(),
            "optimization": {
                "cache": self.optimizer.cache.get_stats(),
                "optimizer": self.optimizer.get_stats()
            },
            "performance": self.monitor.get_metrics()
        }
        
    def _generate_query_hash(
        self,
        query_embedding: np.ndarray,
        entities: Optional[List[str]],
        start_time: Optional[str],
        end_time: Optional[str]
    ) -> str:
        """Generate hash for query caching"""
        import hashlib

        # Hash the full embedding, not just the first 10 dimensions — two
        # different queries whose embeddings happen to share a prefix would
        # otherwise collide and return each other's cached results.
        hash_input = query_embedding.tobytes()
        if entities:
            hash_input += b"," + ",".join(sorted(entities)).encode()
        if start_time:
            hash_input += start_time.encode()
        if end_time:
            hash_input += end_time.encode()

        return hashlib.md5(hash_input).hexdigest()
        
    def warm_cache(self, num_queries: int = 10):
        """Pre-warm cache with predicted queries"""
        predicted_queries = self.optimizer.predict_next_queries()
        
        if not predicted_queries:
            return
            
        # In production, execute actual queries here
        print(f"Pre-warming cache with {len(predicted_queries)} queries")
        
    def cleanup_old_memories(self, days_old: int = 30):
        """Clean up memories older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days_old)
        
        # This would require implementing a cleanup method
        # in the retrieval system and other components
        pass
        
    def export_state(self) -> Dict[str, Any]:
        """Export system state for backup"""
        return {
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_memory_stats(),
            "config": {
                "embedding_dimension": self.embedding_dimension,
                "compression_target": self.compressor.compression_target,
                "cache_capacity": self.optimizer.cache.capacity
            }
        }
