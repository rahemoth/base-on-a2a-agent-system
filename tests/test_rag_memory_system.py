"""
Comprehensive test suite for RAG memory system
Tests all core algorithms and components
"""
import pytest
import numpy as np
from datetime import datetime, timedelta

# Import all modules
from backend.agents.rag_vector_index import HNSWIndex, VectorNode
from backend.agents.rag_dialogue_compression import (
    HierarchicalDialogueCompressor,
    DialogueChunk,
    LSHApproximator
)
from backend.agents.rag_hybrid_retrieval import HybridRetrievalSystem, Document
from backend.agents.rag_memory_graph import (
    MemoryGraph,
    BeamSearchPathFinder,
    MemoryGraphQueryEngine,
    Entity,
    Relation
)
from backend.agents.rag_consistency_manager import (
    ConsistencyManager,
    MemoryFact,
    SemanticRelationClassifier,
    VectorClock
)
from backend.agents.rag_performance_optimizer import (
    LRUCache,
    ProductQuantizer,
    MemoryPool,
    QueryOptimizer,
    PerformanceMonitor
)


class TestHNSWIndex:
    """Tests for HNSW vector index"""
    
    @pytest.fixture
    def index(self):
        """Create HNSW index"""
        return HNSWIndex(dimension=128, M=16, ef_construction=100, ef_search=64)
        
    @pytest.fixture
    def vectors(self):
        """Generate test vectors"""
        np.random.seed(42)
        return np.random.randn(100, 128).astype(np.float32)
        
    def test_add_vector(self, index, vectors):
        """Test adding vectors"""
        index.add_vector("vec_0", vectors[0])
        stats = index.get_stats()
        
        assert stats["node_count"] == 1
        assert stats["entry_point"] == "vec_0"
        
    def test_add_multiple_vectors(self, index, vectors):
        """Test adding multiple vectors"""
        for i in range(50):
            index.add_vector(f"vec_{i}", vectors[i])
            
        stats = index.get_stats()
        assert stats["node_count"] == 50
        
    def test_search_single_vector(self, index, vectors):
        """Test searching for single vector"""
        # Add vectors
        for i in range(10):
            index.add_vector(f"vec_{i}", vectors[i])
            
        # Search
        results = index.search(vectors[0], k=5)
        
        assert len(results) > 0
        assert results[0]["node_id"] == "vec_0"
        assert results[0]["distance"] < 0.1  # Should be very close
        
    def test_search_with_filters(self, index, vectors):
        """Test searching with metadata filters"""
        # Add vectors with metadata
        for i in range(10):
            metadata = {"category": "A" if i < 5 else "B"}
            index.add_vector(f"vec_{i}", vectors[i], metadata)
            
        # Search with filter
        results = index.search(vectors[0], k=10, filters={"category": "A"})
        
        # All results should have category A
        for result in results:
            assert result["metadata"]["category"] == "A"
            
    def test_delete_vector(self, index, vectors):
        """Test deleting a vector"""
        index.add_vector("vec_0", vectors[0])
        index.add_vector("vec_1", vectors[1])
        
        stats_before = index.get_stats()
        assert stats_before["node_count"] == 2
        
        index.delete_vector("vec_0")
        
        stats_after = index.get_stats()
        assert stats_after["node_count"] == 1
        assert stats_after["entry_point"] == "vec_1"
        
    def test_search_performance(self, index, vectors):
        """Test search performance with large dataset"""
        # Add many vectors
        for i in range(1000):
            index.add_vector(f"vec_{i}", vectors[i % 100])
            
        # Measure search time
        import time
        start = time.time()
        
        for i in range(100):
            results = index.search(vectors[i], k=10)
            assert len(results) > 0
            
        duration = time.time() - start
        
        # Should be fast (< 1 second for 100 searches)
        assert duration < 1.0


class TestDialogueCompression:
    """Tests for dialogue compression"""
    
    @pytest.fixture
    def dialogue(self):
        """Create test dialogue"""
        dialogue = []
        for i in range(20):
            dialogue.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"This is message {i} with some content",
                "timestamp": (datetime.now() + timedelta(minutes=i)).isoformat()
            })
        return dialogue
        
    @pytest.fixture
    def embeddings(self):
        """Generate test embeddings"""
        np.random.seed(42)
        return np.random.randn(20, 768).astype(np.float32)
        
    def test_create_chunks(self, dialogue):
        """Test chunk creation"""
        compressor = HierarchicalDialogueCompressor(chunk_size=5)
        chunks = compressor._create_chunks_from_dialogue(dialogue)
        
        assert len(chunks) == 4  # 20 / 5
        assert chunks[0].start_turn == 0
        assert chunks[0].end_turn == 5
        
    def test_compress_dialogue(self, dialogue, embeddings):
        """Test full compression pipeline"""
        compressor = HierarchicalDialogueCompressor(
            chunk_size=5,
            compression_target=0.5
        )
        
        chunks = compressor.compress_dialogue(dialogue, embeddings)
        
        # Should have fewer chunks than original
        assert len(chunks) < len(dialogue)
        
        # Check compression stats
        stats = compressor.get_compression_stats()
        assert stats["compression_ratio"] > 1.0
        assert stats["original_turns"] == 20
        
    def test_lsh_approximation(self):
        """Test LSH approximation"""
        lsh = LSHApproximator(dimension=128, num_tables=10, hash_size=8)
        
        # Add vectors
        np.random.seed(42)
        for i in range(100):
            vec = np.random.randn(128).astype(np.float32)
            lsh.add_vector(f"vec_{i}", vec)
            
        # Query
        query = np.random.randn(128).astype(np.float32)
        candidates = lsh.query_candidates(query)
        
        # Should return some candidates
        assert len(candidates) > 0
        
    def test_merge_chunks(self, dialogue):
        """Test chunk merging"""
        compressor = HierarchicalDialogueCompressor()
        
        # Create two chunks
        chunk1 = DialogueChunk(
            chunk_id="chunk_0",
            start_turn=0,
            end_turn=5,
            turns=dialogue[0:5],
            summary="Summary 1",
            embedding=np.random.randn(768).astype(np.float32),
            information_density=0.5
        )
        
        chunk2 = DialogueChunk(
            chunk_id="chunk_1",
            start_turn=5,
            end_turn=10,
            turns=dialogue[5:10],
            summary="Summary 2",
            embedding=np.random.randn(768).astype(np.float32),
            information_density=0.6
        )
        
        # Merge
        merged = compressor._merge_chunks(chunk1, chunk2)
        
        assert merged.start_turn == 0
        assert merged.end_turn == 10
        assert len(merged.turns) == 10
        assert merged.information_density == 0.55  # Average


class TestHybridRetrieval:
    """Tests for hybrid retrieval system"""
    
    @pytest.fixture
    def retrieval_system(self):
        """Create retrieval system"""
        return HybridRetrievalSystem(dimension=128)
        
    @pytest.fixture
    def documents(self):
        """Generate test documents"""
        np.random.seed(42)
        docs = []
        for i in range(100):
            docs.append({
                "doc_id": f"doc_{i}",
                "content": f"Document content {i}",
                "embedding": np.random.randn(128).astype(np.float32),
                "entities": [f"entity_{i%10}"],
                "timestamp": (datetime.now() + timedelta(hours=i)).isoformat()
            })
        return docs
        
    def test_add_document(self, retrieval_system, documents):
        """Test adding documents"""
        doc = documents[0]
        retrieval_system.add_document(
            doc_id=doc["doc_id"],
            content=doc["content"],
            embedding=doc["embedding"],
            entities=doc["entities"],
            timestamp=doc["timestamp"]
        )
        
        stats = retrieval_system.get_stats()
        assert stats["num_documents"] == 1
        
    def test_search_vectors(self, retrieval_system, documents):
        """Test vector search"""
        # Add documents
        for doc in documents[:20]:
            retrieval_system.add_document(**doc)
            
        # Search
        query = documents[0]["embedding"]
        results = retrieval_system.search(query, k=5)
        
        assert len(results) > 0
        assert results[0]["doc_id"] == "doc_0"
        
    def test_search_with_entity_filter(self, retrieval_system, documents):
        """Test search with entity filter"""
        # Add documents
        for doc in documents[:20]:
            retrieval_system.add_document(**doc)
            
        # Search with entity filter
        query = documents[0]["embedding"]
        results = retrieval_system.search(query, k=10, entities=["entity_0"])
        
        # All results should have entity_0
        doc_ids_with_entity_0 = [d["doc_id"] for d in documents[:20] if "entity_0" in d["entities"]]
        result_ids = [r["doc_id"] for r in results]
        
        assert all(rid in doc_ids_with_entity_0 for rid in result_ids)
        
    def test_search_with_time_filter(self, retrieval_system, documents):
        """Test search with time range filter"""
        # Add documents
        for doc in documents[:20]:
            retrieval_system.add_document(**doc)
            
        # Search with time filter
        start_time = documents[5]["timestamp"]
        end_time = documents[10]["timestamp"]
        
        query = documents[0]["embedding"]
        results = retrieval_system.search(
            query,
            k=20,
            start_time=start_time,
            end_time=end_time
        )
        
        # Results should be within time range
        for result in results:
            assert start_time <= result["timestamp"] <= end_time
            
    def test_brute_force_vs_hnsw(self, retrieval_system, documents):
        """Test that HNSW gives similar results to brute force for small sets"""
        # Add documents
        for doc in documents[:50]:
            retrieval_system.add_document(**doc)
            
        query = documents[0]["embedding"]
        
        # Force brute force by setting threshold high
        retrieval_system.candidate_threshold = 1000
        results_bf = retrieval_system.search(query, k=10)
        
        # Use HNSW
        retrieval_system.candidate_threshold = 10
        results_hnsw = retrieval_system.search(query, k=10)
        
        # Should find similar top result
        assert results_bf[0]["doc_id"] == results_hnsw[0]["doc_id"]


class TestMemoryGraph:
    """Tests for memory graph"""
    
    @pytest.fixture
    def graph(self):
        """Create memory graph"""
        return MemoryGraph()
        
    @pytest.fixture
    def entities(self):
        """Generate test entities"""
        np.random.seed(42)
        entities = []
        entity_types = ["person", "location", "event", "concept"]
        
        for i in range(10):
            entities.append({
                "entity_id": f"entity_{i}",
                "name": f"Entity {i}",
                "entity_type": entity_types[i % len(entity_types)],
                "embedding": np.random.randn(128).astype(np.float32),
                "properties": {"index": i}
            })
        return entities
        
    def test_add_entity(self, graph, entities):
        """Test adding entities"""
        entity = entities[0]
        graph.add_entity(**entity)
        
        stats = graph.get_stats()
        assert stats["num_entities"] == 1
        
    def test_add_relation(self, graph, entities):
        """Test adding relations"""
        # Add entities
        for entity in entities:
            graph.add_entity(**entity)
            
        # Add relation
        graph.add_relation(
            relation_id="rel_0",
            source_id="entity_0",
            target_id="entity_1",
            relation_type="knows"
        )
        
        stats = graph.get_stats()
        assert stats["num_relations"] == 1
        
        # Check neighbors
        neighbors = graph.get_neighbors("entity_0")
        assert len(neighbors) == 1
        assert neighbors[0]["entity_id"] == "entity_1"
        
    def test_beam_search_path_finding(self, graph, entities):
        """Test beam search path finding"""
        # Add entities
        for entity in entities:
            graph.add_entity(**entity)
            
        # Create a path: entity_0 -> entity_1 -> entity_2 -> entity_3
        graph.add_relation("rel_0", "entity_0", "entity_1", "knows")
        graph.add_relation("rel_1", "entity_1", "entity_2", "works_with")
        graph.add_relation("rel_2", "entity_2", "entity_3", "located_in")
        
        # Find paths
        finder = BeamSearchPathFinder(beam_width=3, max_hops=4)
        paths = finder.find_paths(graph, "entity_0", entities[0]["embedding"])
        
        # Should find at least one path
        assert len(paths) > 0
        
        # Check that the path reaches entity_3
        best_path = paths[0]
        assert "entity_3" in best_path.nodes
        
    def test_entity_deletion(self, graph, entities):
        """Test deleting entities"""
        # Add entities and relation
        for entity in entities:
            graph.add_entity(**entity)
            
        graph.add_relation("rel_0", "entity_0", "entity_1", "knows")
        
        # Delete entity
        graph.delete_entity("entity_0")
        
        stats = graph.get_stats()
        assert stats["num_entities"] == 9
        assert stats["num_relations"] == 0  # Relation should be deleted too


class TestConsistencyManager:
    """Tests for consistency management"""
    
    @pytest.fixture
    def manager(self):
        """Create consistency manager"""
        return ConsistencyManager(replica_id="test_replica")
        
    @pytest.fixture
    def facts(self):
        """Generate test facts"""
        np.random.seed(42)
        facts = []
        for i in range(10):
            facts.append({
                "fact_id": f"fact_{i}",
                "content": f"This is fact {i}",
                "embedding": np.random.randn(128).astype(np.float32),
                "entities": [f"entity_{i}"],
                "source_confidence": 0.9
            })
        return facts
        
    def test_add_memory(self, manager, facts):
        """Test adding memory"""
        fact = facts[0]
        operation = manager.add_memory(**fact)
        
        assert operation.operation_type == "ADD"
        assert len(manager.facts) == 1
        
    def test_update_memory(self, manager, facts):
        """Test updating memory"""
        # Add initial memory
        manager.add_memory(**facts[0])
        
        # Add similar memory (should trigger update)
        similar_fact = facts[0].copy()
        similar_fact["fact_id"] = "fact_0_updated"
        similar_fact["content"] = "This is fact 0 with more details"
        
        operation = manager.add_memory(**similar_fact)
        
        # Should be an update
        assert operation.operation_type == "UPDATE"
        
    def test_vector_clock(self):
        """Test vector clock operations"""
        clock1 = VectorClock("replica_1")
        clock2 = VectorClock("replica_2")
        
        # Increment clock1
        clock1.increment()
        assert clock1.clock["replica_1"] == 1
        
        # Merge clocks
        clock2.update(clock1)
        assert clock2.clock["replica_1"] == 1
        
        # Check ordering
        clock2.increment()
        order = clock1.is_before(clock2)
        assert order == True
        
    def test_memory_fact_versioning(self, manager, facts):
        """Test fact versioning"""
        manager.add_memory(**facts[0])
        
        # Update fact
        similar_fact = facts[0].copy()
        similar_fact["content"] = "Updated content"
        manager.add_memory(**similar_fact)
        
        # Check version
        fact = manager.get_fact("fact_0")
        assert fact.version == 2
        
    def test_access_tracking(self, manager, facts):
        """Test access tracking"""
        manager.add_memory(**facts[0])
        
        # Access fact
        manager.get_fact("fact_0")
        manager.get_fact("fact_0")
        
        # Check access count
        fact = manager.get_fact("fact_0")
        assert fact.access_count == 3


class TestPerformanceOptimizer:
    """Tests for performance optimization"""
    
    def test_lru_cache(self):
        """Test LRU cache"""
        cache = LRUCache(capacity=5)
        
        # Add entries
        for i in range(10):
            cache.put(f"key_{i}", f"value_{i}")
            
        # Should only have 5 entries
        assert len(cache.cache) == 5
        
        # Oldest entries should be evicted
        assert cache.get("key_0") is None
        assert cache.get("key_5") is not None
        
        # Test cache hit
        value = cache.get("key_5")
        assert value == "value_5"
        
        # Check stats
        stats = cache.get_stats()
        assert stats["hit_count"] > 0
        
    def test_product_quantizer(self):
        """Test product quantization"""
        np.random.seed(42)
        
        # Generate training data
        vectors = np.random.randn(1000, 128).astype(np.float32)
        
        # Train quantizer
        quantizer = ProductQuantizer(dimension=128, n_subspaces=8, n_centroids=16)
        quantizer.train(vectors, n_iter=5)
        
        assert quantizer.is_trained
        
        # Encode vectors
        codes = quantizer.encode(vectors[:10])
        assert codes.shape == (10, 8)
        
        # Decode vectors
        decoded = quantizer.decode(codes)
        assert decoded.shape == (10, 128)
        
        # Check compression ratio
        ratio = quantizer.get_compression_ratio()
        assert ratio == 4.0  # 32-bit to 8-bit
        
    def test_memory_pool(self):
        """Test memory pool"""
        pool = MemoryPool(dimension=128, pool_size=10)
        
        # Get buffers
        vec_buffer = pool.get_vector_buffer()
        dist_buffer = pool.get_distance_buffer(10)
        
        assert vec_buffer.shape == (128,)
        assert dist_buffer.shape == (10,)
        
        # Return buffers
        pool.return_vector_buffer(vec_buffer)
        pool.return_distance_buffer(dist_buffer)
        
        # Check stats
        stats = pool.get_stats()
        assert stats["available_vectors"] == 1
        
    def test_query_optimizer(self):
        """Test query optimizer"""
        optimizer = QueryOptimizer(cache_capacity=10)
        
        # Define test query function
        def test_query_func(x):
            return x * 2
            
        # Execute query
        result = optimizer.optimize_query(
            "test_query",
            test_query_func,
            5
        )
        
        assert result == 10
        
        # Second call should hit cache
        result2 = optimizer.optimize_query(
            "test_query",
            test_query_func,
            5
        )
        
        assert result2 == 10
        
        # Check cache stats
        cache_stats = optimizer.cache.get_stats()
        assert cache_stats["hit_count"] == 1
        
    def test_performance_monitor(self):
        """Test performance monitor"""
        monitor = PerformanceMonitor()
        
        # Simulate operations
        monitor.start_timer("search")
        # Simulate work
        import time
        time.sleep(0.001)
        monitor.end_timer("search")
        
        monitor.start_timer("search")
        time.sleep(0.002)
        monitor.end_timer("search")
        
        # Get metrics
        metrics = monitor.get_metrics("search")
        
        assert "search" in metrics
        assert metrics["search"]["count"] == 2
        assert metrics["search"]["mean"] > 0


class TestIntegration:
    """Integration tests for complete system"""
    
    def test_end_to_end_retrieval(self):
        """Test complete retrieval pipeline"""
        # Create components
        retrieval_system = HybridRetrievalSystem(dimension=128)
        manager = ConsistencyManager()
        optimizer = QueryOptimizer()
        
        # Add documents
        np.random.seed(42)
        for i in range(100):
            doc = {
                "doc_id": f"doc_{i}",
                "content": f"Document {i}",
                "embedding": np.random.randn(128).astype(np.float32),
                "entities": [f"entity_{i%10}"],
                "timestamp": datetime.now().isoformat()
            }
            retrieval_system.add_document(**doc)
            
            # Add to consistency manager
            manager.add_memory(
                fact_id=f"fact_{i}",
                content=doc["content"],
                embedding=doc["embedding"],
                entities=doc["entities"]
            )
            
        # Perform optimized search
        query = np.random.randn(128).astype(np.float32)
        
        results = optimizer.optimize_query(
            query_hash="test_search",
            query_func=retrieval_system.search,
            query_embedding=query,
            k=10
        )
        
        assert len(results) > 0
        
        # Second search should hit cache
        results2 = optimizer.optimize_query(
            query_hash="test_search",
            query_func=retrieval_system.search,
            query_embedding=query,
            k=10
        )
        
        assert results == results2
        
    def test_multi_hop_reasoning(self):
        """Test multi-hop reasoning with memory graph"""
        # Create graph
        graph = MemoryGraph()
        query_engine = MemoryGraphQueryEngine(graph)
        
        # Add entities
        np.random.seed(42)
        entities_data = []
        for i in range(10):
            entities_data.append({
                "entity_id": f"entity_{i}",
                "name": f"Entity {i}",
                "entity_type": "person",
                "embedding": np.random.randn(128).astype(np.float32)
            })
            
        for entity in entities_data:
            graph.add_entity(**entity)
            
        # Create path: entity_0 -> entity_1 -> entity_2 -> entity_3
        graph.add_relation("rel_0", "entity_0", "entity_1", "knows")
        graph.add_relation("rel_1", "entity_1", "entity_2", "works_with")
        graph.add_relation("rel_2", "entity_2", "entity_3", "located_in")
        
        # Query paths
        query_embedding = entities_data[0]["embedding"]
        paths = query_engine.query_path("entity_0", query_embedding)
        
        assert len(paths) > 0
        assert "entity_3" in paths[0].nodes
        
    def test_dialogue_compression_with_retrieval(self):
        """Test dialogue compression combined with retrieval"""
        # Create dialogue
        dialogue = []
        np.random.seed(42)
        for i in range(30):
            dialogue.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i} with various content",
                "timestamp": datetime.now().isoformat()
            })
            
        # Compress dialogue
        compressor = HierarchicalDialogueCompressor(
            chunk_size=5,
            compression_target=0.4
        )
        
        embeddings = np.random.randn(30, 768).astype(np.float32)
        chunks = compressor.compress_dialogue(dialogue, embeddings)
        
        # Create retrieval system with compressed chunks
        retrieval_system = HybridRetrievalSystem(dimension=768)
        
        for chunk in chunks:
            retrieval_system.add_document(
                doc_id=chunk.chunk_id,
                content=chunk.summary,
                embedding=chunk.embedding,
                entities=chunk.entities,
                timestamp=chunk.timestamp
            )
            
        # Search
        query = embeddings[0]
        results = retrieval_system.search(query, k=3)
        
        assert len(results) > 0
        
        # Check compression ratio
        stats = compressor.get_compression_stats()
        assert stats["compression_ratio"] > 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])