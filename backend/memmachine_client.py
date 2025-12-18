"""
MemMachine Client - Integration with MemMachine API or local fallback
Supports both external MemMachine service and local file-based storage
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)


class MemMachineClient:
    """
    MemMachine client with support for external API or local fallback
    """
    
    def __init__(self):
        self.api_key = os.getenv("MEMMACHINE_API_KEY")
        self.base_url = os.getenv("MEMMACHINE_BASE_URL", "https://api.memmachine.ai")
        self.namespace = os.getenv("MEMMACHINE_NAMESPACE", "continuity-stack-demo")
        self.use_local = os.getenv("LOCAL_FAKE_MEMORY", "0") == "1" or not self.api_key
        
        if self.use_local:
            logger.info("Using local file-based memory storage")
            self.storage_path = Path(os.getenv("MEMMACHINE_PATH", "./memmachine_data"))
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self.memories_file = self.storage_path / "memories.json"
            self._init_local_storage()
        else:
            logger.info(f"Using MemMachine API at {self.base_url}")
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0
            )
    
    def _init_local_storage(self):
        """Initialize local storage files"""
        if not self.memories_file.exists():
            self._write_local_json(self.memories_file, [])
    
    def _read_local_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read JSON from local file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _write_local_json(self, file_path: Path, data: List[Dict[str, Any]]):
        """Write JSON to local file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def write_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Write a memory to MemMachine or local storage
        Returns: memory_id
        """
        if self.use_local:
            return self._write_memory_local(content, metadata)
        else:
            return await self._write_memory_api(content, metadata)
    
    def _write_memory_local(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Write memory to local storage"""
        memories = self._read_local_json(self.memories_file)
        
        memory_id = f"mem_{len(memories)}_{int(datetime.utcnow().timestamp())}"
        memory = {
            "id": memory_id,
            "namespace": self.namespace,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        memories.append(memory)
        self._write_local_json(self.memories_file, memories)
        
        logger.info(f"Wrote memory {memory_id} to local storage")
        return memory_id
    
    async def _write_memory_api(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Write memory to MemMachine API"""
        try:
            response = await self.client.post(
                "/api/v1/memories",
                json={
                    "namespace": self.namespace,
                    "content": content,
                    "metadata": metadata or {}
                }
            )
            response.raise_for_status()
            data = response.json()
            memory_id = data.get("id", f"mem_{int(datetime.utcnow().timestamp())}")
            logger.info(f"Wrote memory {memory_id} to MemMachine API")
            return memory_id
        except Exception as e:
            logger.error(f"Failed to write to MemMachine API: {e}, falling back to local")
            return self._write_memory_local(content, metadata)
    
    async def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories by query
        Returns: list of matching memories
        """
        if self.use_local:
            return self._search_memory_local(query, limit)
        else:
            return await self._search_memory_api(query, limit)
    
    def _search_memory_local(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories in local storage"""
        memories = self._read_local_json(self.memories_file)
        query_lower = query.lower()
        
        results = []
        for memory in memories:
            content = str(memory.get("content", "")).lower()
            metadata_str = str(memory.get("metadata", {})).lower()
            
            if query_lower in content or query_lower in metadata_str:
                results.append(memory)
        
        # Sort by timestamp (newest first) and limit
        results = sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:limit]
    
    async def _search_memory_api(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories via MemMachine API"""
        try:
            response = await self.client.post(
                "/api/v1/memories/search",
                json={
                    "namespace": self.namespace,
                    "query": query,
                    "limit": limit
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Failed to search MemMachine API: {e}, falling back to local")
            return self._search_memory_local(query, limit)
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored memories
        Returns: {total_memories, namespaces, recent_count}
        """
        if self.use_local:
            return self._get_memory_stats_local()
        else:
            return await self._get_memory_stats_api()
    
    def _get_memory_stats_local(self) -> Dict[str, Any]:
        """Get stats from local storage"""
        memories = self._read_local_json(self.memories_file)
        
        # Count by category from metadata
        categories = {}
        for memory in memories:
            category = memory.get("metadata", {}).get("category", "general")
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_memories": len(memories),
            "namespace": self.namespace,
            "categories": categories,
            "recent_count": len([m for m in memories if m.get("timestamp", "") > "2024-01-01"]),
            "storage_mode": "local"
        }
    
    async def _get_memory_stats_api(self) -> Dict[str, Any]:
        """Get stats from MemMachine API"""
        try:
            response = await self.client.get(
                f"/api/v1/memories/stats",
                params={"namespace": self.namespace}
            )
            response.raise_for_status()
            data = response.json()
            data["storage_mode"] = "api"
            return data
        except Exception as e:
            logger.error(f"Failed to get stats from MemMachine API: {e}, falling back to local")
            return self._get_memory_stats_local()
    
    async def close(self):
        """Close the client connection"""
        if not self.use_local:
            await self.client.aclose()
