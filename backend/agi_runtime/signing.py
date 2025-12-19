"""
Signing and Hash Chain Module
Implements canonical JSON serialization and SHA-256 hash chaining
"""
import json
import hashlib
import logging
from typing import Any, Dict, List
from .types import CycleRecord

logger = logging.getLogger(__name__)


def canonical_json(data: Any) -> str:
    """
    Generate canonical JSON representation
    Ensures consistent ordering for stable hashing
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=True
    )


def compute_hash(data: Any) -> str:
    """
    Compute SHA-256 hash of data
    Uses canonical JSON serialization
    """
    canonical = canonical_json(data)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def compute_cycle_hash(cycle: CycleRecord, prev_hash: str = None) -> str:
    """
    Compute hash of a cycle record
    Excludes the hash field itself to avoid circular dependency
    Includes prev_hash for chain integrity
    """
    # Convert to dict and remove hash field
    cycle_dict = cycle.model_dump()
    cycle_dict.pop('hash', None)
    
    # Set prev_hash
    cycle_dict['prev_hash'] = prev_hash
    
    # Compute hash
    return compute_hash(cycle_dict)


def verify_hash_chain(cycles: List[CycleRecord]) -> bool:
    """
    Verify integrity of a hash chain
    Returns True if all hashes are valid
    """
    if not cycles:
        return True
    
    prev_hash = None
    for cycle in cycles:
        # Compute expected hash
        expected_hash = compute_cycle_hash(cycle, prev_hash)
        
        # Verify
        if cycle.hash != expected_hash:
            return False
        
        # Update prev_hash for next iteration
        prev_hash = cycle.hash
    
    return True


def truncate_with_hash(content: str, max_length: int = 1000) -> Dict[str, str]:
    """
    Truncate content and include hash of full content
    Useful for storing large tool outputs
    """
    content_hash = compute_hash(content)
    
    if len(content) <= max_length:
        return {
            "content": content,
            "truncated": False,
            "hash": content_hash,
            "full_length": len(content)
        }
    
    return {
        "content": content[:max_length] + "...[truncated]",
        "truncated": True,
        "hash": content_hash,
        "full_length": len(content)
    }
