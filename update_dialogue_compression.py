with open('backend/agents/rag_dialogue_compression.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 在文件开头添加OpenAI导入
old_imports = '''"""
Dialogue Compression Module
Implements hierarchical clustering-based dialogue summarization and compression
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json'''

new_imports = '''"""
Dialogue Compression Module
Implements hierarchical clustering-based dialogue summarization and compression
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from openai import AsyncOpenAI'''

content = content.replace(old_imports, new_imports)

# 在文件末尾添加新的带LLM摘要功能的压缩器类
additional_code = '''


class LLMEnhancedDialogueCompressor(HierarchicalDialogueCompressor):
    """
    Enhanced dialogue compressor that uses small LLMs for summarization
    
    This compressor:
    1. Uses hierarchical clustering to identify similar dialogue chunks
    2. Calls a small/fast LLM (like gpt-4o-mini) to generate summaries
    3. Maintains context coherence across chunks
    """
    
    def __init__(
        self,
        chunk_size: int = 5,
        min_similarity: float = 0.7,
        max_chunk_size: int = 20,
        compression_target: float = 0.3,
        compression_api_key: Optional[str] = None,
        compression_base_url: Optional[str] = None,
        compression_model: str = "gpt-4o-mini",
        compression_max_tokens: int = 500,
        compression_temperature: float = 0.3
    ):
        super().__init__(
            chunk_size=chunk_size,
            min_similarity=min_similarity,
            max_chunk_size=max_chunk_size,
            compression_target=compression_target
        )
        
        # LLM configuration
        self.compression_api_key = compression_api_key
        self.compression_base_url = compression_base_url
        self.compression_model = compression_model
        self.compression_max_tokens = compression_max_tokens
        self.compression_temperature = compression_temperature
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=compression_api_key,
            base_url=compression_base_url if compression_base_url else None
        )
        
    async def _generate_chunk_summary(self, chunk: DialogueChunk) -> str:
        """
        Generate a summary for a dialogue chunk using an LLM
        
        Args:
            chunk: Dialogue chunk to summarize
            
        Returns:
            Generated summary string
        """
        if not chunk.turns:
            return ""
            
        # Format dialogue for summarization
        dialogue_text = "\n".join([
            f"{turn.get('role', '')}: {turn.get('content', '')}"
            for turn in chunk.turns
        ])
        
        # Build prompt
        prompt = f"""
        Please summarize the following dialogue concisely:
        
        Dialogue:
        {dialogue_text}
        
        Summary requirements:
        - Keep key information and decisions
        - Maintain entity references
        - Use bullet points if helpful
        - Maximum {self.compression_max_tokens} tokens
        
        Summary:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.compression_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes dialogues."},
                    {"role": "user", "content": prompt.strip()}
                ],
                max_tokens=self.compression_max_tokens,
                temperature=self.compression_temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback: simple concatenation of key points
            logger.error(f"Error generating summary: {e}")
            return self._simple_summary(chunk)
    
    def _simple_summary(self, chunk: DialogueChunk) -> str:
        """
        Simple fallback summary when LLM is unavailable
        
        Args:
            chunk: Dialogue chunk to summarize
            
        Returns:
            Simple summary string
        """
        if not chunk.turns:
            return ""
            
        # Get first and last user messages
        user_messages = [t for t in chunk.turns if t.get("role") == "user"]
        assistant_messages = [t for t in chunk.turns if t.get("role") == "assistant"]
        
        summary_parts = []
        
        if user_messages:
            first_user = user_messages[0].get("content", "")[:100]
            summary_parts.append(f"User asked: {first_user}")
            
        if assistant_messages:
            last_assistant = assistant_messages[-1].get("content", "")[:150]
            summary_parts.append(f"Assistant responded: {last_assistant}")
            
        return " | ".join(summary_parts)
    
    async def compress_dialogue_with_summaries(
        self,
        dialogue: List[Dict[str, Any]],
        embeddings: Optional[List[np.ndarray]] = None
    ) -> List[DialogueChunk]:
        """
        Compress dialogue and generate summaries using LLM
        
        Args:
            dialogue: List of dialogue turns
            embeddings: Pre-computed embeddings (optional)
            
        Returns:
            List of compressed chunks with summaries
        """
        # First, do the clustering
        chunks = self.compress_dialogue(dialogue, embeddings)
        
        # Then, generate summaries for each chunk
        for chunk in chunks:
            chunk.summary = await self._generate_chunk_summary(chunk)
            
        return chunks
    
    async def compress_and_summarize_dialogue(
        self,
        dialogue: List[Dict[str, Any]],
        embeddings: Optional[List[np.ndarray]] = None,
        return_full_summary: bool = False
    ) -> Dict[str, Any]:
        """
        Full compression workflow with options for different output formats
        
        Args:
            dialogue: List of dialogue turns
            embeddings: Pre-computed embeddings (optional)
            return_full_summary: Whether to return a single full summary
            
        Returns:
            Compression result with chunks and optional full summary
        """
        chunks = await self.compress_dialogue_with_summaries(dialogue, embeddings)
        
        result = {
            "chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "summary": chunk.summary,
                    "turns": chunk.turns,
                    "information_density": chunk.information_density,
                    "entities": chunk.entities
                }
                for chunk in chunks
            ],
            "compression_stats": self.get_compression_stats()
        }
        
        # Optionally generate a single full summary
        if return_full_summary and chunks:
            full_summary = await self._generate_full_summary(chunks)
            result["full_summary"] = full_summary
            
        return result
    
    async def _generate_full_summary(self, chunks: List[DialogueChunk]) -> str:
        """
        Generate a comprehensive summary from all chunks
        
        Args:
            chunks: List of dialogue chunks
            
        Returns:
            Full summary string
        """
        chunk_summaries = "\n".join([
            f"Chunk {i+1}: {chunk.summary}"
            for i, chunk in enumerate(chunks)
        ])
        
        prompt = f"""
        Please create a comprehensive summary of the entire dialogue from the following chunk summaries:
        
        Chunk Summaries:
        {chunk_summaries}
        
        Create a coherent, well-structured summary that:
        1. Captures the main topics discussed
        2. Highlights key decisions and action items
        3. Maintains the flow of the conversation
        4. Is concise but comprehensive
        
        Full Summary:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.compression_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates comprehensive summaries."},
                    {"role": "user", "content": prompt.strip()}
                ],
                max_tokens=self.compression_max_tokens * 2,
                temperature=self.compression_temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating full summary: {e}")
            return chunk_summaries


# Add logger import
import logging
logger = logging.getLogger(__name__)
'''

# 添加额外代码到文件末尾
content += additional_code

with open('backend/agents/rag_dialogue_compression.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Dialogue compression module updated with LLM summarization!")