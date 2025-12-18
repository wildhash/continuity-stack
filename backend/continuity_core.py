"""
Continuity Core - Self-reflecting agent loop
Implements the core logic for agent learning and evolution
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    SUCCESS = "success"


class Reflection:
    """Represents a reflection on a task execution"""
    
    def __init__(self, task_id: str, status: TaskStatus, error: Optional[str] = None):
        self.task_id = task_id
        self.status = status
        self.error = error
        self.timestamp = datetime.utcnow()
        self.lesson_learned: Optional[str] = None
        self.improvement_strategy: Optional[str] = None
    
    def analyze_failure(self, context: Dict[str, Any]) -> str:
        """Analyze failure and generate lesson"""
        if self.status != TaskStatus.FAILED:
            return "No failure to analyze"
        
        # Simple reflection logic
        error_type = context.get("error_type", "unknown")
        
        if "validation" in str(self.error).lower():
            self.lesson_learned = "Input validation is required before processing"
            self.improvement_strategy = "Add input validation checks at the beginning of task execution"
        elif "connection" in str(self.error).lower():
            self.lesson_learned = "Connection errors require retry logic"
            self.improvement_strategy = "Implement exponential backoff retry mechanism"
        elif "timeout" in str(self.error).lower():
            self.lesson_learned = "Timeout indicates need for async processing"
            self.improvement_strategy = "Break down task into smaller chunks or increase timeout"
        else:
            self.lesson_learned = f"Generic failure: {self.error}"
            self.improvement_strategy = "Implement better error handling and logging"
        
        return self.lesson_learned
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "lesson_learned": self.lesson_learned,
            "improvement_strategy": self.improvement_strategy
        }


class AgentVersion:
    """Represents a version of the agent with learned capabilities"""
    
    def __init__(self, version: str, capabilities: List[str]):
        self.version = version
        self.capabilities = capabilities
        self.created_at = datetime.utcnow()
        self.learned_lessons: List[str] = []
    
    def add_capability(self, capability: str):
        """Add a new capability based on learning"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
    
    def add_lesson(self, lesson: str):
        """Store a learned lesson"""
        if lesson not in self.learned_lessons:
            self.learned_lessons.append(lesson)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "capabilities": self.capabilities,
            "created_at": self.created_at.isoformat(),
            "learned_lessons": self.learned_lessons
        }


class ContinuityCore:
    """
    Core self-reflecting agent system
    Implements the fail -> reflect -> learn -> improve cycle
    """
    
    def __init__(self):
        self.current_version = "1.0.0"
        self.agent_version = AgentVersion(
            self.current_version,
            ["basic_task_execution", "error_logging"]
        )
        self.task_history: List[Dict[str, Any]] = []
        self.reflections: List[Reflection] = []
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task and track the result
        Simulates task execution with potential for failure
        """
        task_id = task.get("id", f"task_{len(self.task_history)}")
        task_type = task.get("type", "generic")
        task_data = task.get("data", {})
        
        # Check if we've learned how to handle this type of task
        required_capability = f"handle_{task_type}"
        has_capability = required_capability in self.agent_version.capabilities
        
        # Simulate task execution
        result = {
            "task_id": task_id,
            "task_type": task_type,
            "timestamp": datetime.utcnow().isoformat(),
            "status": TaskStatus.IN_PROGRESS.value,
            "agent_version": self.current_version
        }
        
        try:
            # First attempt without capability fails
            if not has_capability and task.get("should_fail_first", True):
                raise ValueError(f"Missing capability: {required_capability}")
            
            # Successful execution
            result["status"] = TaskStatus.SUCCESS.value
            result["output"] = {
                "message": f"Successfully executed {task_type} task",
                "data": task_data,
                "capabilities_used": [required_capability] if has_capability else []
            }
            
        except Exception as e:
            # Task failed
            result["status"] = TaskStatus.FAILED.value
            result["error"] = str(e)
            result["output"] = None
            
            # Trigger reflection
            await self.reflect_on_failure(task_id, str(e), task)
        
        self.task_history.append(result)
        return result
    
    async def reflect_on_failure(self, task_id: str, error: str, task: Dict[str, Any]) -> Reflection:
        """
        Reflect on a failed task and generate lessons
        """
        reflection = Reflection(task_id, TaskStatus.FAILED, error)
        
        # Analyze the failure
        context = {
            "error_type": type(error).__name__,
            "task_type": task.get("type", "generic"),
            "task_data": task.get("data", {})
        }
        
        lesson = reflection.analyze_failure(context)
        
        # Store the reflection
        self.reflections.append(reflection)
        
        # Update agent with learned lesson
        self.agent_version.add_lesson(lesson)
        
        # Add capability based on lesson
        if reflection.improvement_strategy:
            task_type = task.get("type", "generic")
            new_capability = f"handle_{task_type}"
            self.agent_version.add_capability(new_capability)
        
        return reflection
    
    def get_learned_lessons(self) -> List[str]:
        """Get all lessons learned by the agent"""
        return self.agent_version.learned_lessons
    
    def get_current_capabilities(self) -> List[str]:
        """Get current agent capabilities"""
        return self.agent_version.capabilities
    
    def get_task_history(self) -> List[Dict[str, Any]]:
        """Get full task execution history"""
        return self.task_history
    
    def get_reflections(self) -> List[Dict[str, Any]]:
        """Get all reflections"""
        return [r.to_dict() for r in self.reflections]
    
    def upgrade_version(self, new_version: str):
        """Upgrade agent to a new version"""
        old_version = self.agent_version
        self.current_version = new_version
        self.agent_version = AgentVersion(
            new_version,
            old_version.capabilities.copy()
        )
        self.agent_version.learned_lessons = old_version.learned_lessons.copy()
