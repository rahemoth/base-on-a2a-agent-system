"""
Consistency Maintenance System
Implements incremental consistency updates for memory operations
"""
from typing import List, Dict, Any, Optional, Tuple, Literal
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import numpy as np


@dataclass
class MemoryOperation:
    """Represents a memory consistency operation"""
    operation_type: Literal["ADD", "UPDATE", "DELETE", "NOOP"]
    memory_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1
    source_confidence: float = 1.0
    
    def __hash__(self):
        return hash((self.operation_type, self.memory_id, self.version))


@dataclass
class MemoryFact:
    """Represents a fact stored in memory"""
    fact_id: str
    content: str
    embedding: np.ndarray
    entities: List[str]
    timestamp: str
    version: int = 1
    source_confidence: float = 1.0
    access_count: int = 0
    last_accessed: Optional[str] = None
    
    def __post_init__(self):
        self.embedding = np.array(self.embedding, dtype=np.float32)
        
    def __hash__(self):
        return hash((self.fact_id, self.version))


class VectorClock:
    """
    Vector clock for tracking causality in distributed updates
    
    Structure:
    - Maps replica IDs to logical timestamps
    - Ensures causal consistency across operations
    """
    
    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self.clock: Dict[str, int] = {replica_id: 0}
        
    def increment(self):
        """Increment clock for this replica"""
        self.clock[self.replica_id] += 1
        
    def update(self, other_clock: 'VectorClock'):
        """Merge with another clock (max per replica)"""
        for replica_id, timestamp in other_clock.clock.items():
            if replica_id in self.clock:
                self.clock[replica_id] = max(self.clock[replica_id], timestamp)
            else:
                self.clock[replica_id] = timestamp
                
    def is_before(self, other_clock: 'VectorClock') -> Optional[bool]:
        """
        Check if this clock is before other clock

        Returns:
            - True if this < other
            - False if this > other
            - None if concurrent
        """
        all_le = True
        any_lt = False

        # Compare across the union of replicas in both clocks. Only iterating
        # self.clock misses replicas that exist solely in other_clock, which
        # would leave them treated as 0 on both sides and skew the result.
        all_replicas = set(self.clock) | set(other_clock.clock)
        for replica_id in all_replicas:
            timestamp = self.clock.get(replica_id, 0)
            other_timestamp = other_clock.clock.get(replica_id, 0)

            if timestamp > other_timestamp:
                all_le = False

            if timestamp < other_timestamp:
                any_lt = True

        if all_le and any_lt:
            return True
        elif not all_le and any_lt:
            return False
        else:
            return None
            
    def copy(self) -> 'VectorClock':
        """Create a copy of this clock"""
        new_clock = VectorClock(self.replica_id)
        new_clock.clock = self.clock.copy()
        return new_clock


class SemanticRelationClassifier:
    """
    Classifies semantic relationships between memories
    
    Determines whether a new memory should:
    - ADD: Create a new fact
    - UPDATE: Modify an existing fact
    - DELETE: Remove an existing fact
    - NOOP: Ignore (duplicate or irrelevant)
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        
    def _calculate_cosine_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray
    ) -> float:
        """Calculate cosine similarity"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
        
    def _detect_contradiction(
        self,
        existing_fact: MemoryFact,
        new_content: str
    ) -> bool:
        """
        Detect if new content contradicts existing fact
        
        Simplified heuristic - in production use NLI models
        """
        # Look for negation patterns
        contradiction_patterns = [
            "not", "never", "no longer", "didn't", "doesn't",
            "contrary", "however", "but", "actually", "in fact"
        ]
        
        new_lower = new_content.lower()
        
        for pattern in contradiction_patterns:
            if pattern in new_lower:
                # Check if entities match
                for entity in existing_fact.entities:
                    if entity.lower() in new_lower:
                        return True
                        
        return False
        
    def classify_relation(
        self,
        existing_fact: MemoryFact,
        new_content: str,
        new_embedding: np.ndarray
    ) -> Literal["ADD", "UPDATE", "DELETE", "NOOP"]:
        """
        Classify the relationship between existing and new memory
        
        Returns:
            Operation type to perform
        """
        # Calculate similarity
        similarity = self._calculate_cosine_similarity(
            existing_fact.embedding,
            new_embedding
        )
        
        # High similarity - check for update or delete
        if similarity >= self.similarity_threshold:
            # Check for contradiction
            if self._detect_contradiction(existing_fact, new_content):
                return "DELETE"
            else:
                return "UPDATE"
                
        # Moderate similarity - could be related but distinct
        elif similarity >= 0.6:
            # Check if it's just a rephrase
            existing_lower = existing_fact.content.lower()
            new_lower = new_content.lower()
            
            # Simple overlap check
            words_existing = set(existing_lower.split())
            words_new = set(new_lower.split())
            
            overlap = words_existing & words_new
            overlap_ratio = len(overlap) / max(len(words_existing), len(words_new), 1)
            
            if overlap_ratio > 0.5:
                return "UPDATE"
            else:
                return "ADD"
                
        # Low similarity - distinct fact
        else:
            return "ADD"
            
    def find_most_similar_fact(
        self,
        facts: List[MemoryFact],
        new_embedding: np.ndarray
    ) -> Optional[Tuple[int, float]]:
        """
        Find the most similar fact to a new memory
        
        Returns:
            Tuple of (index, similarity) or None
        """
        if not facts:
            return None
            
        best_index = 0
        best_similarity = self._calculate_cosine_similarity(
            facts[0].embedding,
            new_embedding
        )
        
        for i in range(1, len(facts)):
            similarity = self._calculate_cosine_similarity(
                facts[i].embedding,
                new_embedding
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_index = i
                
        return (best_index, best_similarity)


class ConsistencyManager:
    """
    Manages consistency of memory operations
    
    Features:
    - Semantic classification of memory relations
    - Incremental updates with vector clocks
    - Fact merging with conflict resolution
    - Version tracking and access statistics
    """
    
    def __init__(
        self,
        replica_id: str = "default",
        similarity_threshold: float = 0.85
    ):
        self.replica_id = replica_id
        self.vector_clock = VectorClock(replica_id)
        self.classifier = SemanticRelationClassifier(similarity_threshold)
        
        self.facts: Dict[str, MemoryFact] = {}
        self.operation_log: List[MemoryOperation] = []
        
    def add_memory(
        self,
        fact_id: str,
        content: str,
        embedding: np.ndarray,
        entities: List[str],
        source_confidence: float = 1.0
    ) -> MemoryOperation:
        """
        Add a new memory or update existing
        
        Returns:
            The operation performed
        """
        self.vector_clock.increment()
        
        # Check for similar existing facts
        similar_fact_idx, similarity = self._find_similar_fact(embedding)
        
        if similar_fact_idx is not None:
            similar_fact = list(self.facts.values())[similar_fact_idx]
            
            # Classify relation
            operation_type = self.classifier.classify_relation(
                similar_fact,
                content,
                embedding
            )
            
            if operation_type == "UPDATE":
                return self._update_fact(
                    similar_fact.fact_id,
                    content,
                    embedding,
                    entities,
                    source_confidence
                )
            elif operation_type == "DELETE":
                return self._delete_fact(similar_fact.fact_id)
            elif operation_type == "NOOP":
                return MemoryOperation(
                    operation_type="NOOP",
                    memory_id=fact_id,
                    content=content
                )
        
        # Add new fact
        return self._add_new_fact(
            fact_id,
            content,
            embedding,
            entities,
            source_confidence
        )
        
    def _find_similar_fact(
        self,
        embedding: np.ndarray
    ) -> Tuple[Optional[int], float]:
        """Find most similar fact"""
        if not self.facts:
            return None, 0.0
            
        facts_list = list(self.facts.values())
        result = self.classifier.find_most_similar_fact(facts_list, embedding)
        
        if result:
            return result
        else:
            return None, 0.0
            
    def _add_new_fact(
        self,
        fact_id: str,
        content: str,
        embedding: np.ndarray,
        entities: List[str],
        source_confidence: float
    ) -> MemoryOperation:
        """Add a completely new fact"""
        fact = MemoryFact(
            fact_id=fact_id,
            content=content,
            embedding=embedding,
            entities=entities,
            timestamp=datetime.now().isoformat(),
            source_confidence=source_confidence
        )
        
        self.facts[fact_id] = fact
        
        operation = MemoryOperation(
            operation_type="ADD",
            memory_id=fact_id,
            content=content,
            source_confidence=source_confidence,
            timestamp=fact.timestamp,
            version=1
        )
        
        self.operation_log.append(operation)
        return operation
        
    def _update_fact(
        self,
        fact_id: str,
        content: str,
        embedding: np.ndarray,
        entities: List[str],
        source_confidence: float
    ) -> MemoryOperation:
        """Update an existing fact with merging"""
        existing_fact = self.facts.get(fact_id)
        
        if not existing_fact:
            return self._add_new_fact(
                fact_id,
                content,
                embedding,
                entities,
                source_confidence
            )
        
        # Merge facts - preserve earliest timestamp and highest confidence
        merged_content = self._merge_facts(existing_fact, content)
        merged_confidence = max(existing_fact.source_confidence, source_confidence)
        
        # Update version
        new_version = existing_fact.version + 1
        
        # Create updated fact
        updated_fact = MemoryFact(
            fact_id=fact_id,
            content=merged_content,
            embedding=embedding,
            entities=list(set(existing_fact.entities + entities)),
            timestamp=existing_fact.timestamp,  # Preserve earliest timestamp
            version=new_version,
            source_confidence=merged_confidence,
            access_count=existing_fact.access_count,
            last_accessed=existing_fact.last_accessed
        )
        
        self.facts[fact_id] = updated_fact
        
        operation = MemoryOperation(
            operation_type="UPDATE",
            memory_id=fact_id,
            content=merged_content,
            source_confidence=merged_confidence,
            timestamp=updated_fact.timestamp,
            version=new_version
        )
        
        self.operation_log.append(operation)
        return operation
        
    def _merge_facts(self, existing_fact: MemoryFact, new_content: str) -> str:
        """
        Merge two facts intelligently
        
        Strategy:
        - Preserve complementary information
        - Use structured merging (not simple concatenation)
        - Maintain coherence
        """
        # Simplified merging - combine complementary parts
        existing_sentences = existing_fact.content.split('.')
        new_sentences = new_content.split('.')
        
        # Remove duplicates
        existing_set = set(s.strip().lower() for s in existing_sentences if s.strip())
        new_set = set(s.strip().lower() for s in new_sentences if s.strip())
        
        # Keep unique sentences
        merged_sentences = list(existing_set | new_set)
        
        return '. '.join(merged_sentences) + '.'
        
    def _delete_fact(self, fact_id: str) -> MemoryOperation:
        """Delete a fact"""
        if fact_id in self.facts:
            del self.facts[fact_id]
            
        operation = MemoryOperation(
            operation_type="DELETE",
            memory_id=fact_id,
            content="",
            version=0
        )
        
        self.operation_log.append(operation)
        return operation
        
    def get_fact(self, fact_id: str) -> Optional[MemoryFact]:
        """Get a fact by ID and update access stats"""
        fact = self.facts.get(fact_id)
        
        if fact:
            fact.access_count += 1
            fact.last_accessed = datetime.now().isoformat()
            
        return fact
        
    def get_all_facts(self) -> List[MemoryFact]:
        """Get all facts"""
        return list(self.facts.values())
        
    def get_operation_log(self, limit: int = 100) -> List[MemoryOperation]:
        """Get recent operations"""
        return self.operation_log[-limit:]
        
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "num_facts": len(self.facts),
            "num_operations": len(self.operation_log),
            "vector_clock": self.vector_clock.clock,
            "avg_confidence": sum(
                f.source_confidence for f in self.facts.values()
            ) / max(len(self.facts), 1),
            "avg_access_count": sum(
                f.access_count for f in self.facts.values()
            ) / max(len(self.facts), 1)
        }
