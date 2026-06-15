"""
Embedding Service
Reusable embedding generation for AgentMemory and RAG subsystem
"""
import logging
import numpy as np
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Generate embeddings for text using local fallback or external API.
    Supports configurable vector dimension to align with RAG subsystem.
    """

    def __init__(
        self,
        dimension: int = 768,
        use_api: bool = False,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None
    ):
        self.dimension = dimension
        self.use_api = use_api
        self.api_key = api_key
        self.api_base_url = api_base_url

    async def generate(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        if self.use_api and self.api_key:
            return await self._generate_api(text)
        return self._generate_local(text)

    async def generate_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts"""
        if self.use_api and self.api_key:
            return await self._generate_api_batch(texts)
        return [self._generate_local(t) for t in texts]

    def _generate_local(self, text: str) -> np.ndarray:
        """
        Generate local embedding using character frequencies and hash features.
        Same algorithm as the original EmbeddingGenerator but parameterized by dimension.
        """
        vector = np.zeros(self.dimension, dtype=np.float32)

        # Character frequency features
        for i, char in enumerate(text[:self.dimension]):
            vector[i % self.dimension] += ord(char) / 1000.0

        # Hash-based features from words
        for word in text.split():
            hash_val = hash(word) % self.dimension
            vector[hash_val] += 1.0

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    async def _generate_api(self, text: str) -> np.ndarray:
        """Generate embedding using OpenAI-compatible API"""
        try:
            from openai import AsyncOpenAI

            client_kwargs = {"api_key": self.api_key}
            if self.api_base_url:
                client_kwargs["base_url"] = self.api_base_url

            client = AsyncOpenAI(**client_kwargs)

            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                dimensions=self.dimension
            )

            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"API embedding failed, falling back to local: {e}")
            return self._generate_local(text)

    async def _generate_api_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a batch using OpenAI-compatible API"""
        try:
            from openai import AsyncOpenAI

            client_kwargs = {"api_key": self.api_key}
            if self.api_base_url:
                client_kwargs["base_url"] = self.api_base_url

            client = AsyncOpenAI(**client_kwargs)

            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
                dimensions=self.dimension
            )

            return [
                np.array(item.embedding, dtype=np.float32)
                for item in response.data
            ]
        except Exception as e:
            logger.error(f"API batch embedding failed, falling back to local: {e}")
            return [self._generate_local(t) for t in texts]
