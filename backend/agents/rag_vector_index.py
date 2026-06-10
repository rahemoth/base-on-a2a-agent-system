"""
Vector Index Module
Implements HNSW (Hierarchical Navigable Small World) vector indexing for efficient similarity search
"""
import math
import heapq
import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np


@dataclass
class VectorNode:
    """Represents a node in the HNSW graph"""
    id: str
    vector: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        self.vector = np.array(self.vector, dtype=np.float32)
        

@dataclass
class Neighbor:
    """Represents a connection to another node"""
    node: VectorNode
    distance: float


class HNSWLayer:
    """Single layer in the HNSW hierarchy"""
    
    def __init__(self, layer_level: int, max_connections: int = 32):
        self.layer_level = layer_level
        self.max_connections = max_connections
        self.graph: Dict[str, List[str]] = {}
        self.nodes: Dict[str, VectorNode] = {}
        
    def add_node(self, node: VectorNode, neighbors: List[str]):
        """Add a node to this layer with its connections"""
        self.nodes[node.id] = node
        self.graph[node.id] = neighbors[:self.max_connections]
        
    def get_node(self, node_id: str) -> Optional[VectorNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
        
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get neighbor IDs for a node"""
        return self.graph.get(node_id, [])
        
    def get_closest_nodes(
        self,
        query_vector: np.ndarray,
        entry_point: str,
        ef: int = 128
    ) -> List[Tuple[str, float]]:
        """
        Search for closest nodes using greedy traversal
        
        Args:
            query_vector: Query vector
            entry_point: Starting node ID
            ef: Number of candidates to maintain
            
        Returns:
            List of (node_id, distance) tuples sorted by distance
        """
        if entry_point not in self.nodes:
            return []
            
        visited = set()
        candidates = []
        result_set = []
        
        entry_node = self.nodes[entry_point]
        entry_dist = np.linalg.norm(query_vector - entry_node.vector)
        
        heapq.heappush(candidates, (entry_dist, entry_point))
        heapq.heappush(result_set, (-entry_dist, entry_point))
        visited.add(entry_point)
        
        while candidates:
            current_dist, current_id = heapq.heappop(candidates)
            
            if len(result_set) >= ef and current_dist > -result_set[0][0]:
                break
                
            for neighbor_id in self.graph.get(current_id, []):
                if neighbor_id in visited:
                    continue
                    
                visited.add(neighbor_id)
                
                neighbor_node = self.nodes.get(neighbor_id)
                if neighbor_node is None:
                    continue
                    
                neighbor_dist = np.linalg.norm(query_vector - neighbor_node.vector)
                
                if len(result_set) < ef or neighbor_dist < -result_set[0][0]:
                    heapq.heappush(candidates, (neighbor_dist, neighbor_id))
                    heapq.heappush(result_set, (-neighbor_dist, neighbor_id))
                    
                    if len(result_set) > ef:
                        heapq.heappop(result_set)
                        
        return [(node_id, -dist) for dist, node_id in sorted(result_set, key=lambda x: x[0])]


class HNSWIndex:
    """
    Hierarchical Navigable Small World (HNSW) index for efficient vector similarity search
    
    Core algorithm:
    - Multi-layer graph structure (O(log N) layers)
    - Each layer is a sparse graph with degree M
    - Insert: Greedy search + local connection optimization
    - Search: O(log N) average complexity
    
    Parameters:
        - M: Maximum number of connections per node (default: 32)
        - ef_construction: Size of candidate list during construction (default: 200)
        - ef_search: Size of candidate list during search (default: 128)
        - ml: Max layer level multiplier (default: 1/ln(M))
    """
    
    def __init__(
        self,
        dimension: int,
        M: int = 32,
        ef_construction: int = 200,
        ef_search: int = 128
    ):
        self.dimension = dimension
        self.M = M
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        
        self.ml = 1.0 / math.log(M)
        
        self.layers: List[HNSWLayer] = []
        self.entry_point: Optional[str] = None
        self.max_level = 0
        
        self.node_count = 0
        
    def _get_random_level(self) -> int:
        """Generate random layer level using geometric distribution"""
        level = int(-math.log(random.random()) * self.ml)
        return level
        
    def _select_neighbors_heuristic(
        self,
        candidates: List[Tuple[str, float]],
        M: int
    ) -> List[str]:
        """
        Select best neighbors using heuristic selection
        
        Args:
            candidates: List of (node_id, distance) tuples
            M: Maximum number of neighbors
            
        Returns:
            List of selected node IDs
        """
        if not candidates:
            return []
            
        candidates = sorted(candidates, key=lambda x: x[1])
        selected = []
        discarded = []
        
        for node_id, dist in candidates[:M]:
            selected.append((node_id, dist))
            
        for node_id, dist in candidates[M:]:
            discarded.append((node_id, dist))
            
        # Check if any discarded node is closer to selected nodes
        final_neighbors = []
        for node_id, dist in selected:
            is_closest = True
            for other_id, other_dist in discarded:
                if other_dist < dist * 1.2:  # 20% tolerance
                    is_closest = False
                    break
            if is_closest:
                final_neighbors.append(node_id)
                
        return final_neighbors
        
    def add_vector(
        self,
        node_id: str,
        vector: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a vector to the index
        
        Args:
            node_id: Unique identifier for the vector
            vector: The vector to index
            metadata: Optional metadata associated with the vector
        """
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(vector)}")
            
        node = VectorNode(
            id=node_id,
            vector=vector,
            metadata=metadata or {}
        )
        
        level = self._get_random_level()
        
        # Ensure layers exist up to target level
        while len(self.layers) <= level:
            new_layer = HNSWLayer(len(self.layers), self.M)
            self.layers.append(new_layer)
            
        # Set entry point if first node
        if self.entry_point is None:
            self.entry_point = node_id
            
        # Add node to layers from top down
        for current_level in range(min(level, self.max_level), -1, -1):
            layer = self.layers[current_level]
            
            # Find closest nodes
            if current_level == self.max_level:
                candidates = layer.get_closest_nodes(
                    node.vector,
                    self.entry_point,
                    self.ef_construction
                )
            else:
                # Use entry point from upper layer
                upper_entry = self.entry_point
                candidates = layer.get_closest_nodes(
                    node.vector,
                    upper_entry,
                    self.ef_construction
                )
                
            # Select neighbors
            neighbors = self._select_neighbors_heuristic(candidates, self.M)
            
            # Add node to layer
            layer.add_node(node, neighbors)
            
            # Update entry point
            if current_level > self.max_level:
                self.entry_point = node_id
                self.max_level = current_level
                
        self.node_count += 1
        
    def search(
        self,
        query_vector: np.ndarray,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for k nearest neighbors
        
        Args:
            query_vector: Query vector
            k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of results with node_id, distance, and metadata
        """
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query dimension mismatch: expected {self.dimension}, got {len(query_vector)}")
            
        if self.entry_point is None:
            return []
            
        # Start from top layer
        closest_nodes = None
        current_point = self.entry_point
        
        for level in range(self.max_level, 0, -1):
            layer = self.layers[level]
            candidates = layer.get_closest_nodes(query_vector, current_point, 1)
            
            if candidates:
                current_point = candidates[0][0]
                
        # Final search on level 0
        if len(self.layers) > 0:
            layer_0 = self.layers[0]
            closest_nodes = layer_0.get_closest_nodes(
                query_vector,
                current_point,
                self.ef_search
            )
            
        # Apply filters and return top k
        results = []
        for node_id, distance in closest_nodes:
            if filters:
                node = self.layers[0].get_node(node_id)
                if node:
                    match = True
                    for key, value in filters.items():
                        if node.metadata.get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                        
            results.append({
                "node_id": node_id,
                "distance": distance,
                "metadata": self.layers[0].get_node(node_id).metadata if self.layers else {}
            })
            
            if len(results) >= k:
                break
                
        return results
        
    def delete_vector(self, node_id: str):
        """
        Remove a vector from the index
        
        Args:
            node_id: ID of the node to remove
        """
        for layer in self.layers:
            if node_id in layer.nodes:
                # Remove node
                del layer.nodes[node_id]
                
                # Remove from neighbors' adjacency lists
                if node_id in layer.graph:
                    for neighbor_id in layer.graph[node_id]:
                        if neighbor_id in layer.graph:
                            layer.graph[neighbor_id] = [
                                nid for nid in layer.graph[neighbor_id] 
                                if nid != node_id
                            ]
                    del layer.graph[node_id]
                    
        if self.entry_point == node_id:
            # Find new entry point
            for layer in reversed(self.layers):
                if layer.nodes:
                    self.entry_point = next(iter(layer.nodes.keys()))
                    break
            else:
                self.entry_point = None
                
        self.node_count = max(0, self.node_count - 1)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            "node_count": self.node_count,
            "max_level": self.max_level,
            "num_layers": len(self.layers),
            "entry_point": self.entry_point,
            "dimension": self.dimension,
            "M": self.M,
            "ef_construction": self.ef_construction,
            "ef_search": self.ef_search
        }