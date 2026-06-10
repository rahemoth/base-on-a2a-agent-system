"""
Memory Graph Database
Implements a knowledge graph for multi-hop reasoning and entity relationships
"""
import heapq
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np


@dataclass
class Entity:
    """Represents an entity (person, place, event, concept)"""
    entity_id: str
    name: str
    entity_type: str  # person, location, event, concept, etc.
    embedding: np.ndarray
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1
    
    def __post_init__(self):
        self.embedding = np.array(self.embedding, dtype=np.float32)


@dataclass
class Relation:
    """Represents a relation between entities"""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: str  # works_with, located_in, part_of, etc.
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1


@dataclass
class Path:
    """Represents a path through the knowledge graph"""
    nodes: List[str]
    edges: List[str]
    total_weight: float
    semantic_score: float


class MemoryGraph:
    """
    Knowledge graph for storing entity relationships
    
    Structure:
    - Nodes: Entities with embeddings and properties
    - Edges: Relations with weights and metadata
    
    Operations:
    - Add/Update/Delete entities
    - Add/Update/Delete relations
    - Path finding for multi-hop reasoning
    """
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        
        # Adjacency lists
        self.outgoing: Dict[str, List[Tuple[str, str]]] = {}  # source -> (target, relation_id)
        self.incoming: Dict[str, List[Tuple[str, str]]] = {}  # target -> (source, relation_id)
        
    def add_entity(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
        embedding: np.ndarray,
        properties: Optional[Dict[str, Any]] = None
    ):
        """Add an entity to the graph"""
        entity = Entity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            embedding=embedding,
            properties=properties or {}
        )
        
        self.entities[entity_id] = entity
        
        # Initialize adjacency lists
        if entity_id not in self.outgoing:
            self.outgoing[entity_id] = []
        if entity_id not in self.incoming:
            self.incoming[entity_id] = []
            
    def update_entity(
        self,
        entity_id: str,
        properties: Optional[Dict[str, Any]] = None,
        embedding: Optional[np.ndarray] = None
    ):
        """Update an entity"""
        if entity_id not in self.entities:
            return
            
        entity = self.entities[entity_id]
        
        if properties:
            entity.properties.update(properties)
            
        if embedding is not None:
            entity.embedding = np.array(embedding, dtype=np.float32)
            
        entity.version += 1
        
    def delete_entity(self, entity_id: str):
        """Delete an entity and all its relations"""
        if entity_id not in self.entities:
            return
            
        # Delete all relations involving this entity
        relation_ids = []
        
        # Outgoing relations
        for target_id, relation_id in self.outgoing.get(entity_id, []):
            relation_ids.append(relation_id)
            
        # Incoming relations
        for source_id, relation_id in self.incoming.get(entity_id, []):
            relation_ids.append(relation_id)
            
        for relation_id in relation_ids:
            self.delete_relation(relation_id)
            
        # Remove adjacency lists
        self.outgoing.pop(entity_id, None)
        self.incoming.pop(entity_id, None)
        
        # Remove entity
        del self.entities[entity_id]
        
    def add_relation(
        self,
        relation_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a relation between entities"""
        # Validate entities exist
        if source_id not in self.entities or target_id not in self.entities:
            raise ValueError("Source or target entity does not exist")
            
        relation = Relation(
            relation_id=relation_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            metadata=metadata or {}
        )
        
        self.relations[relation_id] = relation
        
        # Update adjacency lists
        self.outgoing[source_id].append((target_id, relation_id))
        self.incoming[target_id].append((source_id, relation_id))
        
    def update_relation(
        self,
        relation_id: str,
        weight: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update a relation"""
        if relation_id not in self.relations:
            return
            
        relation = self.relations[relation_id]
        
        if weight is not None:
            relation.weight = weight
            
        if metadata:
            relation.metadata.update(metadata)
            
        relation.version += 1
        
    def delete_relation(self, relation_id: str):
        """Delete a relation"""
        if relation_id not in self.relations:
            return
            
        relation = self.relations[relation_id]
        
        # Remove from adjacency lists
        source_id = relation.source_id
        target_id = relation.target_id
        
        self.outgoing[source_id] = [
            (tid, rid) for tid, rid in self.outgoing[source_id]
            if rid != relation_id
        ]
        
        self.incoming[target_id] = [
            (sid, rid) for sid, rid in self.incoming[target_id]
            if rid != relation_id
        ]
        
        # Remove relation
        del self.relations[relation_id]
        
    def get_neighbors(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all neighbors of an entity"""
        neighbors = []
        
        for target_id, relation_id in self.outgoing.get(entity_id, []):
            relation = self.relations.get(relation_id)
            entity = self.entities.get(target_id)
            
            if relation and entity:
                neighbors.append({
                    "entity_id": target_id,
                    "entity_name": entity.name,
                    "entity_type": entity.entity_type,
                    "relation_id": relation_id,
                    "relation_type": relation.relation_type,
                    "weight": relation.weight
                })
                
        return neighbors
        
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID"""
        return self.entities.get(entity_id)
        
    def get_relation(self, relation_id: str) -> Optional[Relation]:
        """Get a relation by ID"""
        return self.relations.get(relation_id)


class BeamSearchPathFinder:
    """
    Beam search for multi-hop reasoning paths
    
    Algorithm:
    - Maintain top-b paths at each expansion step
    - Heuristic combines semantic alignment and time correlation
    - Time complexity: O(b^k * (|E|/|V|))
    
    Parameters:
        - beam_width: Number of paths to keep at each step (b)
        - max_hops: Maximum number of hops (k)
        - semantic_weight: Weight for semantic similarity in heuristic
    """
    
    def __init__(
        self,
        beam_width: int = 5,
        max_hops: int = 4,
        semantic_weight: float = 0.7
    ):
        self.beam_width = beam_width
        self.max_hops = max_hops
        self.semantic_weight = semantic_weight
        
    def _calculate_heuristic(
        self,
        query_embedding: np.ndarray,
        current_entity: Entity,
        path_weight: float,
        total_hops: int
    ) -> float:
        """
        Calculate heuristic score for path expansion
        
        Combines:
        - Semantic alignment (dot product of embeddings)
        - Time correlation (timestamp decay)
        - Path weight accumulation
        - Hop penalty (prefer shorter paths)
        """
        # Semantic alignment
        semantic_score = np.dot(query_embedding, current_entity.embedding)
        
        # Normalize to [0, 1]
        semantic_score = (semantic_score + 1) / 2
        
        # Time correlation (simplified - use creation time)
        now = datetime.now()
        created_at = datetime.fromisoformat(current_entity.created_at)
        hours_ago = (now - created_at).total_seconds() / 3600
        time_score = math.exp(-hours_ago / 168)  # Decay over 1 week
        
        # Combined heuristic
        heuristic = (
            self.semantic_weight * semantic_score +
            (1 - self.semantic_weight) * time_score
        )
        
        # Accumulate path weight
        total_score = path_weight * heuristic
        
        # Hop penalty
        hop_penalty = math.exp(-0.1 * total_hops)
        total_score *= hop_penalty
        
        return total_score
        
    def find_paths(
        self,
        graph: MemoryGraph,
        start_entity_id: str,
        query_embedding: np.ndarray
    ) -> List[Path]:
        """
        Find top paths using beam search
        
        Args:
            graph: The knowledge graph
            start_entity_id: Starting entity ID
            query_embedding: Query embedding for heuristic
            
        Returns:
            List of best paths found
        """
        if start_entity_id not in graph.entities:
            return []
            
        # Initialize beam with starting path
        initial_path = Path(
            nodes=[start_entity_id],
            edges=[],
            total_weight=1.0,
            semantic_score=np.dot(
                query_embedding,
                graph.entities[start_entity_id].embedding
            )
        )
        
        beam = [initial_path]
        visited_paths = set()
        
        for hop in range(self.max_hops):
            new_beam = []
            
            for path in beam:
                current_entity_id = path.nodes[-1]
                
                # Get neighbors
                neighbors = graph.outgoing.get(current_entity_id, [])
                
                for target_id, relation_id in neighbors:
                    # Skip if already in path
                    if target_id in path.nodes:
                        continue
                        
                    target_entity = graph.entities.get(target_id)
                    if not target_entity:
                        continue
                        
                    relation = graph.relations.get(relation_id)
                    if not relation:
                        continue
                        
                    # Calculate heuristic
                    heuristic_score = self._calculate_heuristic(
                        query_embedding,
                        target_entity,
                        path.total_weight * relation.weight,
                        hop + 1
                    )
                    
                    # Create new path
                    new_path = Path(
                        nodes=path.nodes + [target_id],
                        edges=path.edges + [relation_id],
                        total_weight=path.total_weight * relation.weight,
                        semantic_score=heuristic_score
                    )
                    
                    # Skip if we've seen this path
                    path_signature = tuple(new_path.nodes)
                    if path_signature in visited_paths:
                        continue
                    visited_paths.add(path_signature)
                    
                    new_beam.append(new_path)
                    
            # Keep top-b paths
            beam = heapq.nlargest(
                self.beam_width,
                new_beam,
                key=lambda p: p.semantic_score
            )
            
        return beam
        
    def explain_path(
        self,
        graph: MemoryGraph,
        path: Path
    ) -> str:
        """Generate human-readable explanation of a path"""
        explanation_parts = []
        
        for i, entity_id in enumerate(path.nodes):
            entity = graph.entities.get(entity_id)
            if not entity:
                continue
                
            explanation_parts.append(f"Entity: {entity.name} ({entity.entity_type})")
            
            if i < len(path.edges):
                relation = graph.relations.get(path.edges[i])
                if relation:
                    explanation_parts.append(f"  -> {relation.relation_type} (weight: {relation.weight:.2f})")
                    
        return "\n".join(explanation_parts)


class MemoryGraphQueryEngine:
    """
    Query engine for the memory graph
    
    Combines:
    - Entity search (by name, type, embedding)
    - Path finding (multi-hop reasoning)
    - Relation traversal
    """
    
    def __init__(self, graph: MemoryGraph):
        self.graph = graph
        self.path_finder = BeamSearchPathFinder()
        
    def query_entity_by_name(self, name: str) -> List[Entity]:
        """Query entities by name (fuzzy match)"""
        results = []
        
        for entity in self.graph.entities.values():
            if name.lower() in entity.name.lower():
                results.append(entity)
                
        return results
        
    def query_entity_by_type(self, entity_type: str) -> List[Entity]:
        """Query entities by type"""
        return [
            entity for entity in self.graph.entities.values()
            if entity.entity_type == entity_type
        ]
        
    def query_entity_by_embedding(
        self,
        query_embedding: np.ndarray,
        k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Query entities by embedding similarity
        
        Returns:
            List of (entity_id, similarity_score) tuples
        """
        results = []
        
        for entity_id, entity in self.graph.entities.items():
            similarity = np.dot(query_embedding, entity.embedding)
            # Normalize to [0, 1]
            similarity = (similarity + 1) / 2
            results.append((entity_id, similarity))
            
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:k]
        
    def query_path(
        self,
        start_entity_id: str,
        query_embedding: np.ndarray,
        beam_width: Optional[int] = None
    ) -> List[Path]:
        """
        Query for reasoning paths
        
        Args:
            start_entity_id: Starting entity
            query_embedding: Query embedding
            beam_width: Override default beam width
            
        Returns:
            List of best paths
        """
        if beam_width:
            self.path_finder.beam_width = beam_width
            
        return self.path_finder.find_paths(self.graph, start_entity_id, query_embedding)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            "num_entities": len(self.graph.entities),
            "num_relations": len(self.graph.relations),
            "avg_degree": sum(
                len(neighbors) for neighbors in self.graph.outgoing.values()
            ) / max(len(self.graph.entities), 1)
        }


import math