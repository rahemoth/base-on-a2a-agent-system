"""
Dialogue Compression Module
Implements hierarchical clustering-based dialogue summarization and compression
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class DialogueChunk:
    """Represents a chunk of dialogue with its summary and metadata"""
    chunk_id: str
    start_turn: int
    end_turn: int
    turns: List[Dict[str, Any]]
    summary: str
    embedding: np.ndarray
    information_density: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.embedding = np.array(self.embedding, dtype=np.float32)


@dataclass
class DialogueTurn:
    """Represents a single turn in dialogue"""
    turn_id: int
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "turn_id": self.turn_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }


class LSHApproximator:
    """
    Locality Sensitive Hashing for approximate similarity search
    
    Reduces O(N²) pairwise similarity computation to O(N) for candidate selection
    """
    
    def __init__(self, dimension: int, num_tables: int = 10, hash_size: int = 8):
        self.dimension = dimension
        self.num_tables = num_tables
        self.hash_size = hash_size
        
        # Random hyperplanes for hashing
        self.hyperplanes = [
            np.random.randn(dimension, hash_size)
            for _ in range(num_tables)
        ]
        
        self.tables: List[Dict[str, List[str]]] = [
            {} for _ in range(num_tables)
        ]
        
    def _hash_vector(self, vector: np.ndarray, table_idx: int) -> str:
        """Hash a vector to a bucket key"""
        projections = np.dot(vector, self.hyperplanes[table_idx])
        hash_key = ''.join(['1' if x > 0 else '0' for x in projections])
        return hash_key
        
    def add_vector(self, vector_id: str, vector: np.ndarray):
        """Add a vector to all hash tables"""
        for table_idx in range(self.num_tables):
            hash_key = self._hash_vector(vector, table_idx)
            
            if hash_key not in self.tables[table_idx]:
                self.tables[table_idx][hash_key] = []
                
            self.tables[table_idx][hash_key].append(vector_id)
            
    def query_candidates(self, vector: np.ndarray, num_candidates: int = 50) -> List[str]:
        """Query for candidate vectors"""
        candidates = set()
        
        for table_idx in range(self.num_tables):
            hash_key = self._hash_vector(vector, table_idx)
            
            if hash_key in self.tables[table_idx]:
                candidates.update(self.tables[table_idx][hash_key])
                
                if len(candidates) >= num_candidates * 2:
                    break
                    
        return list(candidates)[:num_candidates]
        
    def clear(self):
        """Clear all hash tables"""
        self.tables = [{} for _ in range(self.num_tables)]


class HierarchicalDialogueCompressor:
    """
    Hierarchical dialogue compression using clustering-based merging
    
    Algorithm:
    1. Split dialogue into chunks
    2. Compute embeddings for each chunk
    3. Use LSH to find similar chunks efficiently
    4. Merge chunks based on similarity and importance scores
    5. Generate summaries for merged chunks
    
    Time Complexity: O(N log N) for insertion + incremental merging
    Space Complexity: O(N)
    """
    
    def __init__(
        self,
        chunk_size: int = 5,
        min_similarity: float = 0.7,
        max_chunk_size: int = 20,
        compression_target: float = 0.3  # Target compression ratio
    ):
        self.chunk_size = chunk_size
        self.min_similarity = min_similarity
        self.max_chunk_size = max_chunk_size
        self.compression_target = compression_target
        
        self.chunks: List[DialogueChunk] = []
        self.lsh: Optional[LSHApproximator] = None
        
    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
        
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text (simplified)"""
        # In production, use NER models like spaCy
        entities = []
        
        # Simple heuristic: capitalized words
        words = text.split()
        for word in words:
            if word and word[0].isupper() and len(word) > 2:
                entities.append(word)
                
        return list(set(entities))
        
    def _calculate_information_density(self, turns: List[Dict[str, Any]]) -> float:
        """
        Calculate information density score
        
        Factors:
        - Entity density
        - User feedback weight
        - Time decay (more recent = higher)
        - Content length variance
        """
        if not turns:
            return 0.0
            
        total_entities = 0
        total_length = 0
        
        for turn in turns:
            content = turn.get("content", "")
            total_length += len(content)
            entities = self._extract_entities(content)
            total_entities += len(entities)
            
        # Entity density
        entity_density = total_entities / max(total_length, 1) * 100
        
        # User feedback (weight user questions higher)
        user_weight = sum(1 for t in turns if t.get("role") == "user") / len(turns)
        
        # Time decay (recent turns get higher weight)
        time_weights = []
        now = datetime.now()
        for turn in turns:
            timestamp = datetime.fromisoformat(turn.get("timestamp", now.isoformat()))
            hours_ago = (now - timestamp).total_seconds() / 3600
            time_weight = math.exp(-hours_ago / 24)  # Decay over 24 hours
            time_weights.append(time_weight)
            
        avg_time_weight = sum(time_weights) / len(time_weights) if time_weights else 0
        
        # Combined score
        density = 0.4 * entity_density + 0.3 * user_weight + 0.3 * avg_time_weight
        
        return min(max(density, 0.0), 1.0)
        
    def _create_chunks_from_dialogue(
        self,
        dialogue: List[Dict[str, Any]]
    ) -> List[DialogueChunk]:
        """Split dialogue into chunks"""
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(dialogue), self.chunk_size):
            chunk_turns = dialogue[i:i + self.chunk_size]
            
            chunk = DialogueChunk(
                chunk_id=f"chunk_{chunk_id}",
                start_turn=i,
                end_turn=min(i + self.chunk_size, len(dialogue)),
                turns=chunk_turns,
                summary="",  # Will be generated later
                embedding=np.zeros(768),  # Will be computed later
                information_density=self._calculate_information_density(chunk_turns),
                entities=[],
                metadata={"turn_count": len(chunk_turns)}
            )
            
            chunks.append(chunk)
            chunk_id += 1
            
        return chunks
        
    def _merge_chunks(
        self,
        chunk1: DialogueChunk,
        chunk2: DialogueChunk
    ) -> DialogueChunk:
        """Merge two chunks into one"""
        merged_turns = chunk1.turns + chunk2.turns
        
        # Weighted average of embeddings
        weight1 = len(chunk1.turns)
        weight2 = len(chunk2.turns)
        merged_embedding = (
            weight1 * chunk1.embedding + weight2 * chunk2.embedding
        ) / (weight1 + weight2)
        
        merged_density = (
            weight1 * chunk1.information_density + 
            weight2 * chunk2.information_density
        ) / (weight1 + weight2)
        
        merged_entities = list(set(chunk1.entities + chunk2.entities))
        
        merged_chunk = DialogueChunk(
            chunk_id=f"merged_{chunk1.chunk_id}_{chunk2.chunk_id}",
            start_turn=min(chunk1.start_turn, chunk2.start_turn),
            end_turn=max(chunk1.end_turn, chunk2.end_turn),
            turns=merged_turns,
            summary="",  # Will be regenerated
            embedding=merged_embedding,
            information_density=merged_density,
            entities=merged_entities,
            metadata={"merged_from": [chunk1.chunk_id, chunk2.chunk_id]}
        )
        
        return merged_chunk
        
    def _find_best_merge_pair(self) -> Optional[Tuple[int, int]]:
        """Find the best pair of chunks to merge"""
        if len(self.chunks) < 2:
            return None
            
        best_pair = None
        best_score = -1.0
        
        # Use LSH for candidate selection if available
        candidates = []
        
        if self.lsh:
            for i, chunk in enumerate(self.chunks):
                similar_chunk_ids = self.lsh.query_candidates(chunk.embedding, 10)
                similar_indices = [
                    j for j, c in enumerate(self.chunks) 
                    if c.chunk_id in similar_chunk_ids
                ]
                candidates.extend(similar_indices)
        else:
            candidates = range(len(self.chunks))
            
        # Evaluate candidate pairs
        for i in candidates:
            for j in range(i + 1, len(self.chunks)):
                if i == j:
                    continue
                    
                chunk1 = self.chunks[i]
                chunk2 = self.chunks[j]
                
                # Check size constraint
                if len(chunk1.turns) + len(chunk2.turns) > self.max_chunk_size:
                    continue
                    
                # Calculate similarity
                similarity = self._calculate_cosine_similarity(
                    chunk1.embedding,
                    chunk2.embedding
                )
                
                if similarity < self.min_similarity:
                    continue
                    
                # Calculate merge score (similarity * importance)
                importance = (chunk1.information_density + chunk2.information_density) / 2
                merge_score = similarity * importance
                
                if merge_score > best_score:
                    best_score = merge_score
                    best_pair = (i, j)
                    
        return best_pair
        
    def _merge_until_target(self):
        """Merge chunks until compression target is reached"""
        initial_turn_count = sum(len(c.turns) for c in self.chunks)
        target_turn_count = initial_turn_count * self.compression_target
        
        while len(self.chunks) > 1:
            current_turn_count = sum(len(c.turns) for c in self.chunks)
            
            if current_turn_count <= target_turn_count:
                break
                
            merge_pair = self._find_best_merge_pair()
            
            if not merge_pair:
                break
                
            i, j = merge_pair
            
            # Merge chunks
            merged = self._merge_chunks(self.chunks[i], self.chunks[j])
            
            # Remove old chunks and add merged
            # Remove higher index first to avoid index shift
            for idx in sorted([i, j], reverse=True):
                self.chunks.pop(idx)
                
            self.chunks.append(merged)
            
    def compress_dialogue(
        self,
        dialogue: List[Dict[str, Any]],
        embeddings: Optional[List[np.ndarray]] = None
    ) -> List[DialogueChunk]:
        """
        Compress dialogue into summarized chunks
        
        Args:
            dialogue: List of dialogue turns
            embeddings: Pre-computed embeddings (optional)
            
        Returns:
            List of compressed chunks
        """
        if not dialogue:
            return []
            
        # Create chunks
        self.chunks = self._create_chunks_from_dialogue(dialogue)
        
        # Initialize embeddings if not provided
        if embeddings:
            for i, chunk in enumerate(self.chunks):
                if i < len(embeddings):
                    chunk.embedding = embeddings[i]
        else:
            # Initialize LSH with dimension
            if self.chunks and len(self.chunks[0].embedding) > 0:
                dimension = len(self.chunks[0].embedding)
                self.lsh = LSHApproximator(dimension)
                
                # Add all chunks to LSH
                for chunk in self.chunks:
                    self.lsh.add_vector(chunk.chunk_id, chunk.embedding)
                    
        # Extract entities
        for chunk in self.chunks:
            text = " ".join([t.get("content", "") for t in chunk.turns])
            chunk.entities = self._extract_entities(text)
            
        # Merge chunks
        self._merge_until_target()
        
        return self.chunks
        
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        if not self.chunks:
            return {
                "original_turns": 0,
                "compressed_turns": 0,
                "compression_ratio": 0.0,
                "num_chunks": 0
            }
            
        original_turns = sum(c.end_turn - c.start_turn for c in self.chunks)
        compressed_turns = len(self.chunks)
        compression_ratio = original_turns / max(compressed_turns, 1)
        
        return {
            "original_turns": original_turns,
            "compressed_turns": compressed_turns,
            "compression_ratio": compression_ratio,
            "num_chunks": len(self.chunks),
            "avg_chunk_size": sum(len(c.turns) for c in self.chunks) / len(self.chunks),
            "avg_information_density": sum(c.information_density for c in self.chunks) / len(self.chunks)
        }


import math