"""
Persistence Module
Handles append-only JSONL cycle logging and artifact storage
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from .types import CycleRecord


class CyclePersistence:
    """
    Manages persistent storage of cycle records
    Uses append-only JSONL format with daily rotation
    """
    
    def __init__(self, base_path: str = "./runs/agi_runtime"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_daily_path(self, timestamp: str = None) -> Path:
        """Get the directory path for a given timestamp (defaults to today)"""
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.now()
        
        date_str = dt.strftime("%Y-%m-%d")
        daily_path = self.base_path / date_str
        daily_path.mkdir(parents=True, exist_ok=True)
        return daily_path
    
    def _get_cycles_file(self, timestamp: str = None) -> Path:
        """Get the path to the cycles.jsonl file"""
        daily_path = self._get_daily_path(timestamp)
        return daily_path / "cycles.jsonl"
    
    def _get_artifacts_dir(self, cycle_id: str, timestamp: str = None) -> Path:
        """Get the artifacts directory for a cycle"""
        daily_path = self._get_daily_path(timestamp)
        artifacts_dir = daily_path / "artifacts" / cycle_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        return artifacts_dir
    
    def append_cycle(self, cycle: CycleRecord) -> str:
        """
        Append a cycle record to the JSONL log
        Returns the file path where it was written
        """
        cycles_file = self._get_cycles_file(cycle.timestamp_start)
        
        # Convert to JSON line
        cycle_json = cycle.model_dump_json()
        
        # Append to file
        with open(cycles_file, 'a') as f:
            f.write(cycle_json + '\n')
        
        return str(cycles_file)
    
    def read_cycles(self, date: str = None, limit: Optional[int] = None) -> List[CycleRecord]:
        """
        Read cycle records from JSONL log
        Args:
            date: Date string in YYYY-MM-DD format (defaults to today)
            limit: Maximum number of cycles to return (newest first)
        """
        if date:
            cycles_file = self.base_path / date / "cycles.jsonl"
        else:
            cycles_file = self._get_cycles_file()
        
        if not cycles_file.exists():
            return []
        
        cycles = []
        with open(cycles_file, 'r') as f:
            for line in f:
                if line.strip():
                    cycle_data = json.loads(line)
                    cycles.append(CycleRecord(**cycle_data))
        
        # Return newest first
        cycles.reverse()
        
        if limit:
            cycles = cycles[:limit]
        
        return cycles
    
    def get_latest_cycle(self) -> Optional[CycleRecord]:
        """Get the most recent cycle record"""
        # Check today and yesterday
        for days_back in range(2):
            dt = datetime.now()
            if days_back > 0:
                from datetime import timedelta
                dt = dt - timedelta(days=days_back)
            
            date_str = dt.strftime("%Y-%m-%d")
            cycles = self.read_cycles(date=date_str, limit=1)
            if cycles:
                return cycles[0]
        
        return None
    
    def save_artifact(self, cycle_id: str, artifact_name: str, content: bytes, timestamp: str = None) -> str:
        """
        Save an artifact (file) associated with a cycle
        Returns the full path to the saved artifact
        """
        artifacts_dir = self._get_artifacts_dir(cycle_id, timestamp)
        artifact_path = artifacts_dir / artifact_name
        
        with open(artifact_path, 'wb') as f:
            f.write(content)
        
        return str(artifact_path)
    
    def read_artifact(self, cycle_id: str, artifact_name: str, timestamp: str = None) -> Optional[bytes]:
        """Read an artifact associated with a cycle"""
        artifacts_dir = self._get_artifacts_dir(cycle_id, timestamp)
        artifact_path = artifacts_dir / artifact_name
        
        if not artifact_path.exists():
            return None
        
        with open(artifact_path, 'rb') as f:
            return f.read()
    
    def list_artifacts(self, cycle_id: str, timestamp: str = None) -> List[str]:
        """List all artifacts for a cycle"""
        artifacts_dir = self._get_artifacts_dir(cycle_id, timestamp)
        
        if not artifacts_dir.exists():
            return []
        
        return [f.name for f in artifacts_dir.iterdir() if f.is_file()]
    
    def get_all_dates(self) -> List[str]:
        """Get all dates with cycle records"""
        dates = []
        for path in self.base_path.iterdir():
            if path.is_dir() and len(path.name) == 10:  # YYYY-MM-DD format
                dates.append(path.name)
        return sorted(dates, reverse=True)
