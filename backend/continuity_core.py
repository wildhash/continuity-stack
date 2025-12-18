"""
Continuity Core - Self-reflecting agent loop
Implements the core logic for agent learning and evolution
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


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
    
    def __init__(self, llm_client=None, memmachine_client=None, neo4j_client=None):
        self.current_version = "1.0.0"
        self.agent_version = AgentVersion(
            self.current_version,
            ["basic_task_execution", "error_logging"]
        )
        self.task_history: List[Dict[str, Any]] = []
        self.reflections: List[Reflection] = []
        self.llm_client = llm_client
        self.memmachine_client = memmachine_client
        self.neo4j_client = neo4j_client
        self.run_counter = 0
    
    def _increment_version(self):
        """Increment agent version when new capabilities are learned"""
        version_parts = self.current_version.split(".")
        version_parts[2] = str(int(version_parts[2]) + 1)
        new_version = ".".join(version_parts)
        
        logger.info(f"Upgrading agent from {self.current_version} to {new_version}")
        
        # Create new agent version in graph
        if self.neo4j_client:
            try:
                self.neo4j_client.create_agent_version(
                    version=new_version,
                    capabilities=self.agent_version.capabilities,
                    parent_version=self.current_version
                )
            except Exception as e:
                logger.error(f"Failed to create agent version in graph: {e}")
        
        self.upgrade_version(new_version)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task and track the result
        Simulates task execution with potential for failure
        """
        self.run_counter += 1
        task_id = task.get("id", f"task_{self.run_counter}_{int(datetime.utcnow().timestamp())}")
        run_id = f"run_{self.run_counter}_{int(datetime.utcnow().timestamp())}"
        task_type = task.get("type", "generic")
        task_data = task.get("data", {})
        
        # Check if we've learned how to handle this type of task
        required_capability = f"handle_{task_type}"
        has_capability = required_capability in self.agent_version.capabilities
        
        # Check for recalled lessons and memories
        recalled_info = await self._recall_relevant_knowledge(task_type)
        
        # Simulate task execution
        result = {
            "task_id": task_id,
            "run_id": run_id,
            "task_type": task_type,
            "timestamp": datetime.utcnow().isoformat(),
            "status": TaskStatus.IN_PROGRESS.value,
            "agent_version": self.current_version,
            "steps": [],
            "recalled_knowledge": recalled_info,
            "graph_summary": None
        }
        
        # Log the run start in Neo4j
        if self.neo4j_client:
            try:
                self.neo4j_client.create_run(
                    run_id=run_id,
                    task_type=task_type,
                    agent_version=self.current_version,
                    success=False,
                    context={"task_id": task_id}
                )
            except Exception as e:
                logger.error(f"Failed to create run in graph: {e}")
        
        try:
            # Add step: Check capability
            result["steps"].append({
                "step": "check_capability",
                "capability_required": required_capability,
                "has_capability": has_capability,
                "current_capabilities": self.agent_version.capabilities.copy()
            })
            
            # First attempt without capability fails
            if not has_capability and task.get("should_fail_first", True):
                result["steps"].append({
                    "step": "capability_check_failed",
                    "message": f"Missing capability: {required_capability}"
                })
                raise ValueError(f"Missing capability: {required_capability}")
            
            # Check for recalled knowledge
            if recalled_info["has_relevant_knowledge"]:
                result["steps"].append({
                    "step": "recall_knowledge",
                    "message": f"Recalled {len(recalled_info['lessons'])} relevant lessons and {len(recalled_info['memories'])} memories",
                    "lessons": recalled_info["lessons"],
                    "memories_summary": f"Found {len(recalled_info['memories'])} related memories"
                })
            
            # Successful execution with LLM or deterministic
            if self.llm_client:
                task_response = await self.llm_client.generate_task_response(
                    task_type, task_data, self.agent_version.capabilities
                )
            else:
                task_response = self._generate_deterministic_response(task_type, task_data)
            
            result["steps"].append({
                "step": "execute_task",
                "message": task_response.get("message", "Task executed successfully"),
                "capability_used": required_capability
            })
            
            result["status"] = TaskStatus.SUCCESS.value
            result["output"] = {
                "message": task_response.get("message", f"Successfully executed {task_type} task"),
                "details": task_response.get("details", task_data),
                "capabilities_used": [required_capability] if has_capability else []
            }
            
            # Add explicit citations (always present, even if empty)
            result["output"]["memory_citations"] = recalled_info.get("memories", [])
            result["output"]["graph_citations"] = recalled_info.get("lessons", [])
            result["output"]["citation_summary"] = {
                "has_citations": recalled_info["has_relevant_knowledge"],
                "memory_count": len(recalled_info.get("memories", [])),
                "lesson_count": len(recalled_info.get("lessons", []))
            }
            
            # Update run status in Neo4j
            if self.neo4j_client:
                try:
                    self.neo4j_client.create_run(
                        run_id=run_id,
                        task_type=task_type,
                        agent_version=self.current_version,
                        success=True,
                        context={"task_id": task_id, "output": result["output"]}
                    )
                except Exception as e:
                    logger.error(f"Failed to update run in graph: {e}")
            
        except Exception as e:
            # Task failed
            result["status"] = TaskStatus.FAILED.value
            result["error"] = str(e)
            result["output"] = None
            result["steps"].append({
                "step": "task_failed",
                "error": str(e)
            })
            
            # Trigger reflection
            reflection_data = await self.reflect_on_failure(task_id, run_id, str(e), task)
            result["reflection"] = reflection_data
            result["lesson"] = reflection_data.get("lesson_learned")
            result["steps"].append({
                "step": "reflection_completed",
                "lesson": reflection_data.get("lesson_learned"),
                "new_capability": reflection_data.get("capability_needed")
            })
        
        # Add graph summary
        if self.neo4j_client:
            try:
                result["graph_summary"] = {
                    "run_id": run_id,
                    "agent_version": self.current_version,
                    "capabilities_count": len(self.agent_version.capabilities),
                    "lessons_count": len(self.agent_version.learned_lessons)
                }
            except Exception as e:
                logger.error(f"Failed to get graph summary: {e}")
        
        self.task_history.append(result)
        return result
    
    async def _recall_relevant_knowledge(self, task_type: str) -> Dict[str, Any]:
        """Recall relevant lessons and memories for this task"""
        recalled = {
            "has_relevant_knowledge": False,
            "lessons": [],
            "memories": [],
            "graph_insights": {}
        }
        
        # Query Neo4j for relevant lessons
        if self.neo4j_client:
            try:
                lessons = self.neo4j_client.get_lessons_for_task_type(task_type)
                if lessons:
                    recalled["lessons"] = [
                        {"content": l.get("content", ""), "id": l.get("id", "")}
                        for l in lessons[:3]  # Top 3 most recent
                    ]
                    recalled["has_relevant_knowledge"] = True
            except Exception as e:
                logger.error(f"Failed to recall lessons from graph: {e}")
        
        # Query MemMachine for relevant memories
        if self.memmachine_client:
            try:
                memories = await self.memmachine_client.search_memory(task_type, limit=3)
                if memories:
                    recalled["memories"] = [
                        {"content": m.get("content", ""), "id": m.get("id", "")}
                        for m in memories
                    ]
                    recalled["has_relevant_knowledge"] = True
            except Exception as e:
                logger.error(f"Failed to search memories: {e}")
        
        return recalled
    
    def _generate_deterministic_response(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a deterministic response for demo purposes"""
        if "validation" in task_type:
            return {
                "message": "Successfully validated input data against schema. All required fields present and type-correct.",
                "details": {
                    "validated": True,
                    "schema_check": "passed",
                    "required_fields": "verified",
                    "input_data": data
                }
            }
        
        return {
            "message": f"Successfully executed {task_type} task",
            "details": data
        }
    
    async def reflect_on_failure(self, task_id: str, run_id: str, error: str, task: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # Use LLM for reflection if available
        if self.llm_client:
            try:
                reflection_data = await self.llm_client.generate_reflection(
                    task.get("type", "generic"), error, context
                )
                reflection.lesson_learned = reflection_data.get("lesson_learned")
                reflection.improvement_strategy = reflection_data.get("improvement_strategy")
                capability_needed = reflection_data.get("capability_needed", f"handle_{task.get('type', 'generic')}")
            except Exception as e:
                logger.error(f"LLM reflection failed: {e}, using deterministic")
                lesson = reflection.analyze_failure(context)
                capability_needed = f"handle_{task.get('type', 'generic')}"
        else:
            lesson = reflection.analyze_failure(context)
            capability_needed = f"handle_{task.get('type', 'generic')}"
        
        # Store the reflection
        self.reflections.append(reflection)
        
        # Update agent with learned lesson
        self.agent_version.add_lesson(reflection.lesson_learned)
        
        # Add capability based on lesson
        if reflection.improvement_strategy:
            self.agent_version.add_capability(capability_needed)
        
        # Track if any storage succeeded (for version increment)
        storage_succeeded = False
        
        # Store in MemMachine
        if self.memmachine_client:
            try:
                await self.memmachine_client.write_memory(
                    content=f"Lesson: {reflection.lesson_learned}",
                    metadata={
                        "category": "lesson",
                        "task_type": task.get("type"),
                        "task_id": task_id,
                        "run_id": run_id,
                        "capability_gained": capability_needed
                    }
                )
                storage_succeeded = True
                logger.info(f"Stored lesson in MemMachine for {capability_needed}")
            except Exception as e:
                logger.error(f"Failed to store lesson in MemMachine: {e}")
        
        # Store in Neo4j graph
        if self.neo4j_client:
            try:
                # Create outcome node
                decision_id = f"decision_{run_id}"
                outcome_id = self.neo4j_client.log_outcome(
                    decision_id=decision_id,
                    success=False,
                    details=error
                )
                
                # Create lesson from outcome
                lesson_id = self.neo4j_client.create_lesson_from_outcome(
                    outcome_id=outcome_id,
                    title=f"Lesson from {task.get('type')} failure",
                    content=reflection.lesson_learned,
                    confidence=1.0
                )
                
                # Link lesson to capability
                self.neo4j_client.lesson_updates_capability(lesson_id, capability_needed)
                
                # Agent gains capability
                self.neo4j_client.agent_gains_capability(self.current_version, capability_needed)
                
                # Add learned lesson to agent version
                self.neo4j_client.add_learned_lesson(
                    version=self.current_version,
                    lesson=reflection.lesson_learned
                )
                storage_succeeded = True
                logger.info(f"Stored lesson in Neo4j graph for {capability_needed}")
            except Exception as e:
                logger.error(f"Failed to store lesson in graph: {e}")
        
        # Increment version only if at least one storage succeeded
        if storage_succeeded:
            self._increment_version()
        else:
            logger.warning(f"Skipping version increment - no storage succeeded for capability {capability_needed}")
        
        return {
            "lesson_learned": reflection.lesson_learned,
            "improvement_strategy": reflection.improvement_strategy,
            "capability_needed": capability_needed,
            "agent_version": self.current_version
        }
    
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
