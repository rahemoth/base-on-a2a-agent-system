"""
Utility functions for working with A2A SDK types
"""
from typing import List
from a2a import types
import logging

logger = logging.getLogger(__name__)


def extract_text_from_parts(parts: List[types.Part]) -> str:
    """
    Extract text content from A2A message parts.
    
    Args:
        parts: List of Part objects from an A2A message
        
    Returns:
        Concatenated text content from all Part objects with text
    """
    text_parts = []
    
    for part in parts:
        if hasattr(part, 'text') and part.text:
            text_parts.append(part.text)
    
    return " ".join(text_parts)