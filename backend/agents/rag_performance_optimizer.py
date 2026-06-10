"""
Performance Optimization Module
Implements caching, quantization, and parallelization for memory operations
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import heapq
import math


@dataclass
class CacheEntry:
    """Represents an entry in the cache"""
    key: str
    value: Any
    embedding: np.ndarray
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    last_accessed: Optional[str] = None
    size_bytes: int = 0
    
    def __post_init__(self):
        self.embedding = np.array(self.embedding, dtype=np.float32)


class LRUCache:
    """
    LRU (Least Recently Used) cache for high-frequency queries
    
    Features:
    - O(1) lookup and insertion
    - Automatic eviction of least recently used items
    - Size-based eviction with LRU tiebreaker
    
    Parameters:
        - capacity: Maximum number of entries
        - max_memory_bytes: Maximum memory usage in bytes
    """
    
    def __init__(self, capacity: int = 1000, max_memory_bytes: int = 100 * 1024 * 1024):
        self.capacity = capacity
        self.max_memory_bytes = max_memory_bytes
        
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_memory_bytes = 0
        self.hit_count = 0
        self.miss_count = 0
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            # Update access stats and move to end
            entry = self.cache[key]
            entry.access_count += 1
            entry.last_accessed = datetime.now().isoformat()
            
            self.cache.move_to_end(key)
            self.hit_count += 1
            
            return entry.value
        else:
            self.miss_count += 1
            return None
            
    def put(
        self,
        key: str,
        value: Any,
        embedding: Optional[np.ndarray] = None,
        size_bytes: int = 0
    ):
        """Put value into cache"""
        # If key exists, update
        if key in self.cache:
            entry = self.cache[key]
            entry.value = value
            entry.access_count += 1
            entry.last_accessed = datetime.now().isoformat()
            
            if embedding is not None:
                entry.embedding = np.array(embedding, dtype=np.float32)
                
            self.cache.move_to_end(key)
            return
            
        # Create new entry
        entry = CacheEntry(
            key=key,
            value=value,
            embedding=embedding or np.zeros(0),
            size_bytes=size_bytes
        )
        
        # Check memory constraint
        self.current_memory_bytes += size_bytes
        
        # Evict if necessary
        while (len(self.cache) >= self.capacity or 
               self.current_memory_bytes > self.max_memory_bytes):
            self._evict_one()
            
        self.cache[key] = entry
        
    def _evict_one(self):
        """Evict least recently used entry"""
        if not self.cache:
            return
            
        key, entry = self.cache.popitem(last=False)
        self.current_memory_bytes -= entry.size_bytes
        
    def invalidate(self, key: str):
        """Invalidate a cache entry"""
        if key in self.cache:
            entry = self.cache[key]
            self.current_memory_bytes -= entry.size_bytes
            del self.cache[key]
            
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.current_memory_bytes = 0
        self.hit_count = 0
        self.miss_count = 0
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "num_entries": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "memory_usage_bytes": self.current_memory_bytes,
            "memory_usage_mb": self.current_memory_bytes / (1024 * 1024)
        }


class ProductQuantizer:
    """
    Product Quantization for memory-efficient vector storage
    
    Algorithm:
    1. Split vector into D subspaces (typically D=8)
    2. Train K centroids for each subspace (typically K=256, 8-bit)
    3. Encode each subvector as nearest centroid index
    4. Store 8-bit codes instead of original vectors
    
    Compression: 32-bit float -> 8-bit code per subspace
    Memory reduction: 4x
    Search: Use asymmetric distance computation (ADC)
    
    Parameters:
        - dimension: Original vector dimension
        - n_subspaces: Number of subspaces (D)
        - n_centroids: Number of centroids per subspace (K)
    """
    
    def __init__(
        self,
        dimension: int,
        n_subspaces: int = 8,
        n_centroids: int = 256
    ):
        if dimension % n_subspaces != 0:
            raise ValueError(f"Dimension {dimension} must be divisible by n_subspaces {n_subspaces}")
            
        self.dimension = dimension
        self.n_subspaces = n_subspaces
        self.n_centroids = n_centroids
        self.subspace_dim = dimension // n_subspaces
        
        # Centroids for each subspace
        self.centroids = np.zeros((n_subspaces, n_centroids, self.subspace_dim), dtype=np.float32)
        
        # Is trained?
        self.is_trained = False
        
    def train(self, vectors: np.ndarray, n_iter: int = 25):
        """
        Train quantizer on vectors
        
        Args:
            vectors: Training data (N x dimension)
            n_iter: Number of k-means iterations
        """
        n_samples = vectors.shape[0]
        
        # Split vectors into subspaces
        subspaces = []
        for i in range(self.n_subspaces):
            start = i * self.subspace_dim
            end = (i + 1) * self.subspace_dim
            subspace_vectors = vectors[:, start:end]
            subspaces.append(subspace_vectors)
            
        # Train centroids for each subspace using k-means
        for i in range(self.n_subspaces):
            subspace_vectors = subspaces[i]
            
            # Initialize centroids randomly
            indices = np.random.choice(n_samples, self.n_centroids, replace=False)
            centroids = subspace_vectors[indices].copy()
            
            # K-means iterations
            for _ in range(n_iter):
                # Assign to nearest centroid
                distances = self._compute_distances(subspace_vectors, centroids)
                assignments = np.argmin(distances, axis=1)
                
                # Update centroids
                for k in range(self.n_centroids):
                    mask = assignments == k
                    if np.sum(mask) > 0:
                        centroids[k] = np.mean(subspace_vectors[mask], axis=0)
                        
            self.centroids[i] = centroids
            
        self.is_trained = True
        
    def _compute_distances(
        self,
        vectors: np.ndarray,
        centroids: np.ndarray
    ) -> np.ndarray:
        """Compute distances between vectors and centroids"""
        n_samples = vectors.shape[0]
        n_centroids = centroids.shape[0]
        
        distances = np.zeros((n_samples, n_centroids), dtype=np.float32)
        
        for k in range(n_centroids):
            diff = vectors - centroids[k]
            distances[:, k] = np.sum(diff ** 2, axis=1)
            
        return distances
        
    def encode(self, vectors: np.ndarray) -> np.ndarray:
        """
        Encode vectors to quantized codes
        
        Returns:
            Codes (N x n_subspaces) where each value is a centroid index [0, K-1]
        """
        if not self.is_trained:
            raise RuntimeError("Quantizer must be trained before encoding")
            
        n_samples = vectors.shape[0]
        codes = np.zeros((n_samples, self.n_subspaces), dtype=np.uint8)
        
        # Encode each subspace
        for i in range(self.n_subspaces):
            start = i * self.subspace_dim
            end = (i + 1) * self.subspace_dim
            subspace_vectors = vectors[:, start:end]
            
            # Find nearest centroid
            distances = self._compute_distances(subspace_vectors, self.centroids[i])
            codes[:, i] = np.argmin(distances, axis=1)
            
        return codes
        
    def decode(self, codes: np.ndarray) -> np.ndarray:
        """
        Decode quantized codes back to vectors
        
        Returns:
            Reconstructed vectors (N x dimension)
        """
        if not self.is_trained:
            raise RuntimeError("Quantizer must be trained before decoding")
            
        n_samples = codes.shape[0]
        vectors = np.zeros((n_samples, self.dimension), dtype=np.float32)
        
        # Decode each subspace
        for i in range(self.n_subspaces):
            start = i * self.subspace_dim
            end = (i + 1) * self.subspace_dim
            
            # Look up centroid for each code
            centroid_indices = codes[:, i]
            subspace_vectors = self.centroids[i][centroid_indices]
            
            vectors[:, start:end] = subspace_vectors
            
        return vectors
        
    def compute_distance(
        self,
        query_vector: np.ndarray,
        codes: np.ndarray
    ) -> np.ndarray:
        """
        Compute distances between query and quantized vectors using ADC
        
        Asymmetric Distance Computation:
        - Don't decode quantized vectors (which would be lossy)
        - Pre-compute query-to-centroid distances
        - Sum nearest centroid distances
        
        Returns:
            Distances (N,)
        """
        if not self.is_trained:
            raise RuntimeError("Quantizer must be trained before computing distances")
            
        n_samples = codes.shape[0]
        distances = np.zeros(n_samples, dtype=np.float32)
        
        # Compute distances for each subspace
        for i in range(self.n_subspaces):
            start = i * self.subspace_dim
            end = (i + 1) * self.subspace_dim
            
            query_subvector = query_vector[start:end]
            
            # Compute query-to-centroid distances
            diff = self.centroids[i] - query_subvector
            centroid_distances = np.sum(diff ** 2, axis=1)  # (n_centroids,)
            
            # Add appropriate distance for each code
            distances += centroid_distances[codes[:, i]]
            
        return distances
        
    def get_compression_ratio(self) -> float:
        """Calculate compression ratio"""
        original_size = self.dimension * 4  # 32-bit floats
        compressed_size = self.n_subspaces * 1  # 8-bit codes
        return original_size / compressed_size


class MemoryPool:
    """
    Pre-allocated memory pool for vector operations
    
    Reduces memory allocation overhead during queries
    """
    
    def __init__(self, dimension: int, pool_size: int = 1000):
        self.dimension = dimension
        self.pool_size = pool_size
        
        # Pre-allocate matrices
        self.vector_pool: List[np.ndarray] = []
        self.distance_pool: List[np.ndarray] = []
        
        for _ in range(pool_size):
            self.vector_pool.append(np.zeros(dimension, dtype=np.float32))
            self.distance_pool.append(np.zeros(pool_size, dtype=np.float32))
            
    def get_vector_buffer(self) -> np.ndarray:
        """Get a vector buffer from pool"""
        if self.vector_pool:
            return self.vector_pool.pop()
        else:
            return np.zeros(self.dimension, dtype=np.float32)
            
    def return_vector_buffer(self, buffer: np.ndarray):
        """Return a vector buffer to pool"""
        if len(self.vector_pool) < self.pool_size:
            self.vector_pool.append(buffer)
            
    def get_distance_buffer(self, size: int) -> np.ndarray:
        """Get a distance buffer from pool"""
        if self.distance_pool:
            buffer = self.distance_pool.pop()
            if len(buffer) >= size:
                return buffer[:size]
                
        return np.zeros(size, dtype=np.float32)
        
    def return_distance_buffer(self, buffer: np.ndarray):
        """Return a distance buffer to pool"""
        if len(self.distance_pool) < self.pool_size:
            self.distance_pool.append(buffer)
            
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        return {
            "dimension": self.dimension,
            "pool_size": self.pool_size,
            "available_vectors": len(self.vector_pool),
            "available_distances": len(self.distance_pool)
        }


class QueryOptimizer:
    """
    Optimizes query execution based on patterns
    
    Features:
        - Cache high-frequency queries
        - Pre-warm cache based on usage patterns
        - Parallel query execution
    """
    
    def __init__(
        self,
        cache_capacity: int = 1000,
        max_memory_bytes: int = 100 * 1024 * 1024
    ):
        self.cache = LRUCache(cache_capacity, max_memory_bytes)
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        
    def optimize_query(
        self,
        query_hash: str,
        query_func,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute query with optimization
        
        Returns:
            Query result
        """
        # Check cache
        cached_result = self.cache.get(query_hash)
        if cached_result is not None:
            return cached_result
            
        # Execute query
        result = query_func(*args, **kwargs)
        
        # Update stats
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                "count": 0,
                "total_time": 0.0,
                "last_executed": None
            }
            
        self.query_stats[query_hash]["count"] += 1
        self.query_stats[query_hash]["last_executed"] = datetime.now().isoformat()
        
        # Cache result
        self.cache.put(query_hash, result)
        
        return result
        
    def predict_next_queries(self) -> List[str]:
        """
        Predict likely next queries based on patterns
        
        Returns:
            List of query hashes to pre-warm
        """
        # Simple frequency-based prediction
        sorted_queries = sorted(
            self.query_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        # Return top 10 most frequent queries
        return [q[0] for q in sorted_queries[:10]]
        
    def pre_warm_cache(self, query_func, query_hashes: List[str]):
        """Pre-warm cache for predicted queries"""
        for query_hash in query_hashes:
            if self.cache.get(query_hash) is None:
                # Generate key/args for this query hash
                # In production, store query parameters with hash
                pass
                
    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        return {
            "cache_stats": self.cache.get_stats(),
            "num_unique_queries": len(self.query_stats),
            "top_queries": sorted(
                self.query_stats.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:5]
        }


class PerformanceMonitor:
    """
    Monitors and reports performance metrics
    """
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.start_times: Dict[str, float] = {}
        
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = datetime.now().timestamp()
        
    def end_timer(self, operation: str):
        """End timing an operation and record metric"""
        if operation not in self.start_times:
            return
            
        start_time = self.start_times[operation]
        end_time = datetime.now().timestamp()
        duration = (end_time - start_time) * 1000  # Convert to ms
        
        if operation not in self.metrics:
            self.metrics[operation] = []
            
        self.metrics[operation].append(duration)
        del self.start_times[operation]
        
    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """
        Get performance metrics
        
        Returns:
            Dictionary with mean, p50, p95, p99 for each operation
        """
        if operation:
            ops_to_check = [operation]
        else:
            ops_to_check = self.metrics.keys()
            
        results = {}
        
        for op in ops_to_check:
            if op not in self.metrics or not self.metrics[op]:
                continue
                
            durations = self.metrics[op]
            durations.sort()
            
            n = len(durations)
            results[op] = {
                "mean": sum(durations) / n,
                "p50": durations[int(n * 0.5)],
                "p95": durations[int(n * 0.95)],
                "p99": durations[int(n * 0.99)],
                "min": durations[0],
                "max": durations[-1],
                "count": n
            }
            
        return results