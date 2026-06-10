"""
Hybrid Retrieval System
Combines HNSW vector search with inverted index for efficient retrieval
"""
import bisect
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np


@dataclass
class Document:
    """Represents a document with metadata and embedding"""
    doc_id: str
    content: str
    embedding: np.ndarray
    entities: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.embedding = np.array(self.embedding, dtype=np.float32)


@dataclass
class TimeIndexNode:
    """Node in B+ tree for time indexing"""
    timestamp: str
    doc_ids: List[str] = field(default_factory=list)
    left: Optional['TimeIndexNode'] = None
    right: Optional['TimeIndexNode'] = None


class TimeBPlusTree:
    """
    B+ tree for efficient time range queries
    
    Operations:
    - Insert: O(log N)
    - Range query: O(log N + K) where K is result count
    """
    
    def __init__(self, order: int = 4):
        self.order = order
        self.root: Optional[TimeIndexNode] = None
        
    def _compare_time(self, time1: str, time2: str) -> int:
        """Compare two timestamp strings"""
        dt1 = datetime.fromisoformat(time1)
        dt2 = datetime.fromisoformat(time2)
        
        if dt1 < dt2:
            return -1
        elif dt1 > dt2:
            return 1
        else:
            return 0
            
    def insert(self, doc_id: str, timestamp: str):
        """Insert a document ID into the tree"""
        if not self.root:
            self.root = TimeIndexNode(timestamp=timestamp, doc_ids=[doc_id])
            return
            
        node = self.root
        parent = None
        
        # Find insertion point
        while node:
            cmp = self._compare_time(timestamp, node.timestamp)
            
            if cmp == 0:
                node.doc_ids.append(doc_id)
                return
            elif cmp < 0:
                if not node.left:
                    node.left = TimeIndexNode(timestamp=timestamp, doc_ids=[doc_id])
                    return
                node = node.left
            else:
                if not node.right:
                    node.right = TimeIndexNode(timestamp=timestamp, doc_ids=[doc_id])
                    return
                node = node.right
                    
    def query_range(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Set[str]:
        """
        Query documents within time range
        
        Args:
            start_time: Start of range (inclusive)
            end_time: End of range (inclusive)
            
        Returns:
            Set of document IDs
        """
        if not self.root:
            return set()
            
        results = set()
        self._query_range_recursive(self.root, start_time, end_time, results)
        return results
        
    def _query_range_recursive(
        self,
        node: Optional[TimeIndexNode],
        start_time: Optional[str],
        end_time: Optional[str],
        results: Set[str]
    ):
        """Recursively query range"""
        if not node:
            return
            
        # Check if node is in range
        in_range = True
        
        if start_time and self._compare_time(node.timestamp, start_time) < 0:
            in_range = False
            
        if end_time and self._compare_time(node.timestamp, end_time) > 0:
            in_range = False
            
        if in_range:
            results.update(node.doc_ids)
            
        # Continue searching both subtrees
        self._query_range_recursive(node.left, start_time, end_time, results)
        self._query_range_recursive(node.right, start_time, end_time, results)


class InvertedIndex:
    """
    Inverted index for efficient metadata-based retrieval
    
    Structure:
    - entity -> [doc_ids]
    - keyword -> [doc_ids]
    """
    
    def __init__(self):
        self.entity_index: Dict[str, Set[str]] = {}
        self.keyword_index: Dict[str, Set[str]] = {}
        
    def add_document(self, doc: Document):
        """Add a document to the index"""
        # Index entities
        for entity in doc.entities:
            if entity not in self.entity_index:
                self.entity_index[entity] = set()
            self.entity_index[entity].add(doc.doc_id)
            
        # Index keywords (simple tokenization)
        keywords = self._extract_keywords(doc.content)
        for keyword in keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = set()
            self.keyword_index[keyword].add(doc.doc_id)
            
    def query_entities(self, entities: List[str]) -> Set[str]:
        """Query by entities (intersection)"""
        if not entities:
            return set()
            
        results = self.entity_index.get(entities[0], set()).copy()
        
        for entity in entities[1:]:
            results &= self.entity_index.get(entity, set())
            
        return results
        
    def query_keywords(self, keywords: List[str]) -> Set[str]:
        """Query by keywords (intersection)"""
        if not keywords:
            return set()
            
        results = self.keyword_index.get(keywords[0], set()).copy()
        
        for keyword in keywords[1:]:
            results &= self.keyword_index.get(keyword, set())
            
        return results
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple tokenization and filtering
        words = text.lower().split()
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                     'to', 'of', 'and', 'in', 'that', 'for', 'it', 'with', 'as'}
        
        keywords = []
        for word in words:
            # Remove punctuation
            word = ''.join(c for c in word if c.isalnum())
            
            if len(word) > 2 and word not in stopwords:
                keywords.append(word)
                
        return keywords


class HybridRetrievalSystem:
    """
    Hybrid retrieval system combining vector search and metadata filtering
    
    Pipeline:
    Stage 1: Metadata pre-filtering (entities + time range) - O(|entities| * log N)
    Stage 2: Vector search on candidates - HNSW or brute force
    Stage 3: Re-ranking with cross-encoder (optional)
    
    Parameters:
        - vector_index: HNSW vector index
        - candidate_threshold: Use brute force if candidates < threshold
    """
    
    def __init__(
        self,
        dimension: int,
        candidate_threshold: int = 3000
    ):
        from .rag_vector_index import HNSWIndex
        
        self.vector_index = HNSWIndex(dimension=dimension)
        self.inverted_index = InvertedIndex()
        self.time_index = TimeBPlusTree()
        
        self.documents: Dict[str, Document] = {}
        self.candidate_threshold = candidate_threshold
        
    def add_document(
        self,
        doc_id: str,
        content: str,
        embedding: np.ndarray,
        entities: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a document to the retrieval system
        
        Args:
            doc_id: Unique document identifier
            content: Document content
            embedding: Document embedding vector
            entities: List of entities mentioned
            timestamp: Document timestamp
            metadata: Additional metadata
        """
        doc = Document(
            doc_id=doc_id,
            content=content,
            embedding=embedding,
            entities=entities or [],
            timestamp=timestamp or datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        # Add to all indexes
        self.documents[doc_id] = doc
        self.vector_index.add_vector(doc_id, embedding, metadata)
        self.inverted_index.add_document(doc)
        self.time_index.insert(doc_id, doc.timestamp)
        
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        entities: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        use_reranking: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector similarity and metadata filtering
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            entities: Filter by entities
            start_time: Start of time range
            end_time: End of time range
            keywords: Filter by keywords
            use_reranking: Whether to use cross-encoder reranking
            
        Returns:
            List of search results with scores
        """
        # Stage 1: Metadata pre-filtering
        candidates = self._get_candidates(entities, start_time, end_time, keywords)
        
        if not candidates:
            return []
            
        # Stage 2: Vector search on candidates
        if len(candidates) < self.candidate_threshold:
            # Brute force on small candidate set
            results = self._brute_force_search(
                query_embedding, 
                candidates, 
                k
            )
        else:
            # HNSW search with candidate filter
            results = self._hnsw_search(
                query_embedding,
                candidates,
                k * 3  # Get more candidates for reranking
            )
            
        # Stage 3: Re-ranking (optional)
        if use_reranking:
            results = self._rerank_results(query_embedding, results, k)
            
        return results[:k]
        
    def _get_candidates(
        self,
        entities: Optional[List[str]],
        start_time: Optional[str],
        end_time: Optional[str],
        keywords: Optional[List[str]]
    ) -> Set[str]:
        """Get candidate documents from metadata filters"""
        candidates = set(self.documents.keys())
        
        # Filter by entities
        if entities:
            entity_candidates = self.inverted_index.query_entities(entities)
            candidates &= entity_candidates
            
        # Filter by keywords
        if keywords:
            keyword_candidates = self.inverted_index.query_keywords(keywords)
            candidates &= keyword_candidates
            
        # Filter by time range
        if start_time or end_time:
            time_candidates = self.time_index.query_range(start_time, end_time)
            candidates &= time_candidates
            
        return candidates
        
    def _brute_force_search(
        self,
        query_embedding: np.ndarray,
        candidates: Set[str],
        k: int
    ) -> List[Dict[str, Any]]:
        """Brute force search on candidate set"""
        results = []
        
        for doc_id in candidates:
            doc = self.documents.get(doc_id)
            if not doc:
                continue
                
            # Calculate cosine similarity
            similarity = self._calculate_cosine_similarity(
                query_embedding,
                doc.embedding
            )
            
            results.append({
                "doc_id": doc_id,
                "score": similarity,
                "content": doc.content,
                "metadata": doc.metadata,
                "timestamp": doc.timestamp
            })
            
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:k]
        
    def _hnsw_search(
        self,
        query_embedding: np.ndarray,
        candidates: Set[str],
        k: int
    ) -> List[Dict[str, Any]]:
        """HNSW search with candidate filtering"""
        # Perform HNSW search
        vector_results = self.vector_index.search(
            query_embedding,
            k=k * 10  # Get more to filter
        )
        
        # Filter by candidates
        candidate_set = candidates
        filtered_results = [
            r for r in vector_results 
            if r["node_id"] in candidate_set
        ]
        
        # Convert to standard format
        results = []
        for r in filtered_results:
            doc_id = r["node_id"]
            doc = self.documents.get(doc_id)
            if doc:
                results.append({
                    "doc_id": doc_id,
                    "score": 1.0 - r["distance"],  # Convert distance to similarity
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "timestamp": doc.timestamp
                })
                
        return results[:k]
        
    def _rerank_results(
        self,
        query_embedding: np.ndarray,
        results: List[Dict[str, Any]],
        k: int
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results using cross-encoder style scoring
        
        In production, use actual cross-encoder model
        Here we use a heuristic combination of vector similarity
        and recency
        """
        now = datetime.now()
        
        for result in results:
            # Base score from vector similarity
            base_score = result["score"]
            
            # Time decay (more recent = higher score)
            timestamp = datetime.fromisoformat(result["timestamp"])
            hours_ago = (now - timestamp).total_seconds() / 3600
            time_decay = math.exp(-hours_ago / 168)  # Decay over 1 week
            
            # Combine scores
            result["reranked_score"] = 0.7 * base_score + 0.3 * time_decay
            
        # Sort by reranked score
        results.sort(key=lambda x: x["reranked_score"], reverse=True)
        
        return results[:k]
        
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
        
    def delete_document(self, doc_id: str):
        """Delete a document from all indexes"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self.vector_index.delete_vector(doc_id)
            
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "num_documents": len(self.documents),
            "vector_index_stats": self.vector_index.get_stats(),
            "candidate_threshold": self.candidate_threshold
        }


import math