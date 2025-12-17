"""
MemMachine - Persistent Memory System
Simple file-based persistent memory for agent state and history
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class MemMachine:
    """
    Persistent memory system for agent state
    Stores memories, decisions, and agent state to disk
    """
    
    def __init__(self, storage_path: str = "./memmachine_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Memory categories
        self.memories_file = self.storage_path / "memories.json"
        self.decisions_file = self.storage_path / "decisions.json"
        self.agent_state_file = self.storage_path / "agent_state.json"
        
        # Initialize storage files
        self._init_storage()
    
    def _init_storage(self):
        """Initialize storage files if they don't exist"""
        for file in [self.memories_file, self.decisions_file, self.agent_state_file]:
            if not file.exists():
                self._write_json(file, [])
    
    def _read_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read JSON data from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _write_json(self, file_path: Path, data: List[Dict[str, Any]]):
        """Write JSON data to file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def store_memory(self, memory: Dict[str, Any]) -> str:
        """Store a memory with timestamp"""
        memories = self._read_json(self.memories_file)
        
        memory_entry = {
            "id": f"mem_{len(memories)}",
            "timestamp": datetime.utcnow().isoformat(),
            **memory
        }
        
        memories.append(memory_entry)
        self._write_json(self.memories_file, memories)
        
        return memory_entry["id"]
    
    def get_memories(self, limit: Optional[int] = None, 
                     category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve memories with optional filtering"""
        memories = self._read_json(self.memories_file)
        
        if category:
            memories = [m for m in memories if m.get("category") == category]
        
        # Sort by timestamp (newest first)
        memories = sorted(memories, key=lambda x: x.get("timestamp", ""), reverse=True)
        
        if limit:
            memories = memories[:limit]
        
        return memories
    
    def store_decision(self, decision: Dict[str, Any]) -> str:
        """Store a decision record"""
        decisions = self._read_json(self.decisions_file)
        
        decision_entry = {
            "id": f"decision_{len(decisions)}",
            "timestamp": datetime.utcnow().isoformat(),
            **decision
        }
        
        decisions.append(decision_entry)
        self._write_json(self.decisions_file, decisions)
        
        return decision_entry["id"]
    
    def get_decisions(self, limit: Optional[int] = None,
                      status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve decision records"""
        decisions = self._read_json(self.decisions_file)
        
        if status:
            decisions = [d for d in decisions if d.get("status") == status]
        
        # Sort by timestamp (newest first)
        decisions = sorted(decisions, key=lambda x: x.get("timestamp", ""), reverse=True)
        
        if limit:
            decisions = decisions[:limit]
        
        return decisions
    
    def update_agent_state(self, state: Dict[str, Any]):
        """Update the current agent state"""
        current_state = self._read_json(self.agent_state_file)
        
        state_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            **state
        }
        
        current_state.append(state_entry)
        self._write_json(self.agent_state_file, current_state)
    
    def get_agent_state(self) -> Optional[Dict[str, Any]]:
        """Get the most recent agent state"""
        states = self._read_json(self.agent_state_file)
        return states[-1] if states else None
    
    def get_agent_state_history(self) -> List[Dict[str, Any]]:
        """Get full agent state history"""
        return self._read_json(self.agent_state_file)
    
    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Simple text search in memories"""
        memories = self._read_json(self.memories_file)
        query_lower = query.lower()
        
        results = []
        for memory in memories:
            # Search in content and description
            content = str(memory.get("content", "")).lower()
            description = str(memory.get("description", "")).lower()
            
            if query_lower in content or query_lower in description:
                results.append(memory)
        
        return results
    
    def clear_all(self):
        """Clear all stored data (for testing)"""
        self._write_json(self.memories_file, [])
        self._write_json(self.decisions_file, [])
        self._write_json(self.agent_state_file, [])
