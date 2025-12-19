"""
Memory Module
Three-tier memory system: episodic, semantic, procedural
Builds on top of MemMachine
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .types import CycleRecord, MemoryWrite

logger = logging.getLogger(__name__)


class MemoryItem:
    """Generic memory item"""
    def __init__(self, memory_id: str, content: str, memory_type: str, metadata: Dict[str, Any]):
        self.memory_id = memory_id
        self.content = content
        self.memory_type = memory_type
        self.metadata = metadata
        self.timestamp = metadata.get("timestamp", datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class ThreeTierMemory:
    """
    Three-tier memory system:
    1. Episodic - Event sequences and cycle records
    2. Semantic - Distilled facts and learned constraints
    3. Procedural - Verified procedures and skills
    """
    
    def __init__(self, memmachine_client=None):
        """
        Args:
            memmachine_client: MemMachine client instance (from existing system)
        """
        self.memmachine_client = memmachine_client
    
    async def store_episodic(self, cycle_record: CycleRecord) -> str:
        """
        Store episodic memory - a cycle record reference
        Returns memory_id
        """
        if not self.memmachine_client:
            logger.warning("No MemMachine client available for episodic storage")
            return f"episodic_{cycle_record.cycle_id}"
        
        content = f"Cycle {cycle_record.cycle_id}: {cycle_record.goal_stack}"
        metadata = {
            "memory_type": "episodic",
            "cycle_id": cycle_record.cycle_id,
            "timestamp": cycle_record.timestamp_start,
            "agent_version": cycle_record.agent_version,
            "goal_stack": cycle_record.goal_stack,
            "success": len(cycle_record.reflection.what_failed) == 0,
            "eval_score": cycle_record.eval_scores.overall_score
        }
        
        memory_id = await self.memmachine_client.write_memory(content, metadata)
        logger.info(f"Stored episodic memory {memory_id} for cycle {cycle_record.cycle_id}")
        return memory_id
    
    async def store_semantic(self, fact: str, category: str = "general", confidence: float = 0.8) -> str:
        """
        Store semantic memory - distilled fact or learned constraint
        Returns memory_id
        """
        if not self.memmachine_client:
            logger.warning("No MemMachine client available for semantic storage")
            return f"semantic_{int(datetime.now().timestamp())}"
        
        metadata = {
            "memory_type": "semantic",
            "category": category,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        memory_id = await self.memmachine_client.write_memory(fact, metadata)
        logger.info(f"Stored semantic memory {memory_id}: {fact[:50]}...")
        return memory_id
    
    async def store_procedural(
        self,
        skill_name: str,
        procedure: Dict[str, Any],
        preconditions: List[str] = None,
        validation_notes: str = None
    ) -> str:
        """
        Store procedural memory - verified skill/procedure
        Returns memory_id
        """
        if not self.memmachine_client:
            logger.warning("No MemMachine client available for procedural storage")
            return f"procedural_{skill_name}"
        
        content = f"Skill: {skill_name}"
        metadata = {
            "memory_type": "procedural",
            "skill_name": skill_name,
            "procedure": procedure,
            "preconditions": preconditions or [],
            "validation_notes": validation_notes or "",
            "verified": True,
            "timestamp": datetime.now().isoformat()
        }
        
        memory_id = await self.memmachine_client.write_memory(content, metadata)
        logger.info(f"Stored procedural memory {memory_id}: {skill_name}")
        return memory_id
    
    async def retrieve_relevant(
        self,
        goal: str,
        world_summary: str,
        k: int = 8
    ) -> List[MemoryItem]:
        """
        Retrieve relevant memories for a goal and world state
        Returns up to k most relevant memories
        """
        if not self.memmachine_client:
            logger.warning("No MemMachine client available for retrieval")
            return []
        
        # Combine goal and world summary for search
        query = f"{goal} {world_summary}"
        
        try:
            # Search memories
            results = await self.memmachine_client.search_memory(query, limit=k)
            
            # Convert to MemoryItem objects
            memory_items = []
            for result in results:
                memory_items.append(MemoryItem(
                    memory_id=result.get("id", "unknown"),
                    content=result.get("content", ""),
                    memory_type=result.get("metadata", {}).get("memory_type", "unknown"),
                    metadata=result.get("metadata", {})
                ))
            
            # Sort by relevance (using timestamp as proxy for now)
            memory_items.sort(key=lambda x: x.timestamp, reverse=True)
            
            logger.info(f"Retrieved {len(memory_items)} relevant memories")
            return memory_items
        
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    async def retrieve_by_type(
        self,
        memory_type: str,
        limit: int = 10
    ) -> List[MemoryItem]:
        """
        Retrieve memories by type
        """
        if not self.memmachine_client:
            return []
        
        try:
            # Search by memory type
            results = await self.memmachine_client.search_memory(memory_type, limit=limit * 2)
            
            # Filter by type
            filtered = [
                MemoryItem(
                    memory_id=r.get("id", "unknown"),
                    content=r.get("content", ""),
                    memory_type=r.get("metadata", {}).get("memory_type", "unknown"),
                    metadata=r.get("metadata", {})
                )
                for r in results
                if r.get("metadata", {}).get("memory_type") == memory_type
            ]
            
            return filtered[:limit]
        
        except Exception as e:
            logger.error(f"Failed to retrieve memories by type: {e}")
            return []
    
    async def get_recent_successes(self, limit: int = 5) -> List[MemoryItem]:
        """Get recent successful cycle records"""
        episodic = await self.retrieve_by_type("episodic", limit=limit * 2)
        
        # Filter for successes
        successes = [m for m in episodic if m.metadata.get("success", False)]
        return successes[:limit]
    
    async def get_learned_constraints(self) -> List[MemoryItem]:
        """Get all learned constraints (semantic memories)"""
        semantic = await self.retrieve_by_type("semantic", limit=50)
        
        # Filter for constraints
        constraints = [m for m in semantic if m.metadata.get("category") == "constraint"]
        return constraints
    
    async def get_available_skills(self) -> List[MemoryItem]:
        """Get all available procedural skills"""
        procedural = await self.retrieve_by_type("procedural", limit=100)
        
        # Filter for verified skills
        skills = [m for m in procedural if m.metadata.get("verified", False)]
        return skills


def deterministic_retrieval(goal: str, memories: List[MemoryItem], k: int = 8) -> List[MemoryItem]:
    """
    Deterministic memory retrieval using keyword matching and recency
    Fallback when embeddings are not available
    """
    scored_memories = []
    
    goal_keywords = set(goal.lower().split())
    
    for memory in memories:
        score = 0.0
        
        # Keyword matching
        content_lower = memory.content.lower()
        matching_keywords = sum(1 for kw in goal_keywords if kw in content_lower)
        score += matching_keywords * 0.5
        
        # Recency bonus
        try:
            from datetime import timezone
            timestamp = datetime.fromisoformat(memory.timestamp.replace('Z', '+00:00'))
            age_days = (datetime.now(timezone.utc) - timestamp).days
            recency_score = max(0, 1.0 - (age_days / 30))  # Decay over 30 days
            score += recency_score * 0.3
        except Exception:
            pass
        
        # Memory type weighting
        if memory.memory_type == "procedural":
            score += 0.2  # Prefer skills
        elif memory.memory_type == "semantic":
            score += 0.1  # Then facts
        
        scored_memories.append((score, memory))
    
    # Sort by score and return top k
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored_memories[:k]]
