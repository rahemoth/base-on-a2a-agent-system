"""
RAG Memory System Integration
Integrates all RAG memory components into a cohesive system
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from .rag_vector_index import HNSWIndex, VectorNode
from .rag_dialogue_compression import HierarchicalDialogueCompressor, DialogueChunk
from .rag_hybrid_retrieval import HybridRetrievalSystem, Document
from .rag_memory_graph import MemoryGraph, MemoryGraphQueryEngine, Entity, Relation
from .rag_consistency_manager import ConsistencyManager, MemoryFact
from .rag_performance_optimizer import LRUCache, ProductQuantizer, QueryOptimizer, PerformanceMonitor


class RAGMemorySystem:
    """
    Complete RAG memory system integrating all components
    
    Architecture:
    1. Hot Memory: Recent dialogue chunks (Dialogue Compressor)
    2. Warm Memory: Vector-indexed summaries (Hybrid Retrieval)
    3. Cold Memory: Entity relationships (Memory Graph)
    4. Consistency: Unified fact management (Consistency Manager)
    5. Optimization: Caching and quantization (Performance Optimizer)
    
    Flow:
    - Input dialogue -> Compress -> Index -> Store
    - Query -> Optimize -> Retrieve -> Re-rank -> Return
    """
    
    def __init__(
        self,
        embedding_dimension: int = 768,
        compression_target: float = 0.3,
        cache_capacity: int = 1000,
        enable_quantization: bool = True
    ):
        self.embedding_dimension = embedding_dimension
        
        # Core components
        self.compressor = HierarchicalDialogueCompressor(
            chunk_size=5,
            compression_target=compression_target
        )
        
        self.retrieval_system = HybridRetrievalSystem(
            dimension=embedding_dimension
        )
        
        self.memory_graph = MemoryGraph()
        self.graph_query_engine = MemoryGraphQueryEngine(self.memory_graph)
        
        self.consistency_manager = ConsistencyManager()
        
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
            
    def add_dialogue(
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
        
        # Step 2: Add chunks to retrieval system
        for chunk in chunks:
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
                    "information_density": chunk.information_density
                }
            )
            
        # Step 3: Extract entities and add to graph
        for chunk in chunks:
            for entity_name in chunk.entities:
                entity_id = f"entity_{entity_name}"
                
                if entity_id not in self.memory_graph.entities:
                    # Create new entity
                    entity_embedding = chunk.embedding
                    
                    self.memory_graph.add_entity(
                        entity_id=entity_id,
                        name=entity_name,
                        entity_type="concept",
                        embedding=entity_embedding,
                        properties={"mentions": 1}
                    )
                else:
                    # Update existing entity
                    entity = self.memory_graph.entities[entity_id]
                    entity.properties["mentions"] = entity.properties.get("mentions", 0) + 1
                    
        # Step 4: Add to consistency manager
        for chunk in chunks:
            self.consistency_manager.add_memory(
                fact_id=chunk.chunk_id,
                content=chunk.summary,
                embedding=chunk.embedding,
                entities=chunk.entities,
                source_confidence=chunk.information_density
            )
            
        self.monitor.end_timer("add_dialogue")
        
        return {
            "status": "success",
            "num_chunks": len(chunks),
            "compression_stats": self.compressor.get_compression_stats(),
            "graph_stats": self.graph_query_engine.get_stats(),
            "consistency_stats": self.consistency_manager.get_stats()
        }
        
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
                "cache_hit": self.optimizer.cache.get(query_hash) is not None,
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
        # Simple hash based on embedding and filters
        import hashlib
        
        hash_input = str(query_embedding[:10].tobytes())
        if entities:
            hash_input += ",".join(sorted(entities))
        if start_time:
            hash_input += start_time
        if end_time:
            hash_input += end_time
            
        return hashlib.md5(hash_input.encode()).hexdigest()
        
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


from datetime import timedelta