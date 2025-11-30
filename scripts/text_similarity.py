#!/usr/bin/env python3
"""Text similarity calculations using SequenceMatcher and keyword overlap."""

import re
from difflib import SequenceMatcher


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity (0.0-1.0) using sequence matching + keyword overlap."""
    if not text1 or not text2:
        return 0.0
    
    # Normalize for comparison
    text1_norm = re.sub(r'[^a-zA-Z0-9\s]', ' ', text1.lower()).strip()
    text2_norm = re.sub(r'[^a-zA-Z0-9\s]', ' ', text2.lower()).strip()
    
    text1_norm = re.sub(r'\s+', ' ', text1_norm)
    text2_norm = re.sub(r'\s+', ' ', text2_norm)
    
    similarity = SequenceMatcher(None, text1_norm, text2_norm).ratio()
    
    # Add keyword matching
    words1 = set(text1_norm.split())
    words2 = set(text2_norm.split())
    
    if words1 and words2:
        keyword_similarity = len(words1.intersection(words2)) / len(words1.union(words2))
        # Weighted combination: 70% sequence, 30% keywords
        return (similarity * 0.7) + (keyword_similarity * 0.3)
    
    return similarity
