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
    
    The A2A SDK uses Pydantic RootModel for discriminated unions, where Part
    is a wrapper around TextPart | FilePart | DataPart. We access part.root
    to get the actual typed part before checking instance type.
    
    Args:
        parts: List of Part objects from an A2A message
        
    Returns:
        Concatenated text content from all TextPart objects
    """
    text_parts = []
    
    for part in parts:
        # In A2A SDK, Part is a RootModel wrapper around the actual part type
        # We need to access part.root to get the actual TextPart/FilePart/DataPart
        if hasattr(part, 'root'):
            actual_part = part.root
        else:
            # Fallback for cases where part is already unwrapped
            # This shouldn't normally happen but provides compatibility
            actual_part = part
            logger.debug(f"Unexpected: Part without 'root' attribute (type: {type(part).__name__}, hasattr text: {hasattr(part, 'text')})")
        
        # Only extract from TextPart - other part types (FilePart, DataPart) don't have text
        if isinstance(actual_part, types.TextPart):
            text_parts.append(actual_part.text)
    
    return " ".join(text_parts)
