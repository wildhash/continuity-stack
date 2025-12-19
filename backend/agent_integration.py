"""
AGI Runtime Integration Layer
Feature-flagged integration between existing continuity_core and new AGI runtime
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def is_agi_runtime_enabled() -> bool:
    """Check if AGI runtime is enabled via feature flag"""
    return os.getenv("CONTINUITY_AGI_RUNTIME", "0") == "1"


class ContinuityAgent:
    """
    Unified agent interface that switches between:
    - Legacy continuity_core (default)
    - New AGI runtime (when CONTINUITY_AGI_RUNTIME=1)
    """
    
    def __init__(self, llm_client=None, memmachine_client=None, neo4j_client=None):
        self.llm_client = llm_client
        self.memmachine_client = memmachine_client
        self.neo4j_client = neo4j_client
        
        self.use_agi_runtime = is_agi_runtime_enabled()
        
        if self.use_agi_runtime:
            logger.info("✓ AGI Runtime mode enabled")
            from .agi_runtime import AGIRuntime
            self.runtime = AGIRuntime(
                llm_client=llm_client,
                memmachine_client=memmachine_client,
                neo4j_client=neo4j_client,
                environment=os.getenv("AGI_ENVIRONMENT", "production")
            )
        else:
            logger.info("✓ Legacy continuity_core mode (default)")
            from .continuity_core import ContinuityCore
            self.runtime = ContinuityCore(
                llm_client=llm_client,
                memmachine_client=memmachine_client,
                neo4j_client=neo4j_client
            )
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task using either legacy or AGI runtime
        Returns unified response format
        """
        if self.use_agi_runtime:
            return await self._execute_task_agi(task)
        else:
            return await self._execute_task_legacy(task)
    
    async def _execute_task_agi(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using AGI runtime"""
        goal = task.get("type", "generic_task")
        input_data = task.get("data", {})
        
        # Run AGI cycle
        cycle = await self.runtime.run_cycle(goal, input_data)
        
        # Convert to legacy format for backwards compatibility
        status = "success" if cycle.eval_scores.overall_score >= 0.5 else "failed"
        
        result = {
            "task_id": task.get("id", cycle.cycle_id),
            "run_id": cycle.cycle_id,
            "task_type": goal,
            "timestamp": cycle.timestamp_start,
            "status": status,
            "agent_version": cycle.agent_version,
            "steps": [
                {"step": "agi_cycle_completed", "cycle_id": cycle.cycle_id}
            ],
            "output": {
                "message": f"AGI cycle completed with score {cycle.eval_scores.overall_score:.2f}",
                "details": {
                    "cycle_id": cycle.cycle_id,
                    "eval_scores": cycle.eval_scores.model_dump(),
                    "actions_taken": len(cycle.actions_taken),
                    "safety_status": cycle.safety_assessment.status.value,
                    "reflection": cycle.reflection.model_dump()
                },
                "memory_citations": [],
                "graph_citations": [],
                "citation_summary": {
                    "has_citations": len(cycle.memory_writes) > 0,
                    "memory_count": len(cycle.memory_writes),
                    "lesson_count": len(cycle.reflection.lessons_learned)
                }
            },
            "agi_cycle": cycle.model_dump(),  # Full cycle data
            "graph_summary": {
                "cycle_id": cycle.cycle_id,
                "agent_version": cycle.agent_version,
                "eval_score": cycle.eval_scores.overall_score,
                "hash": cycle.hash,
                "prev_hash": cycle.prev_hash
            }
        }
        
        return result
    
    async def _execute_task_legacy(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using legacy continuity_core"""
        return await self.runtime.execute_task(task)
    
    def get_current_capabilities(self):
        """Get current agent capabilities"""
        if self.use_agi_runtime:
            # AGI runtime tracks capabilities differently
            return ["agi_runtime_enabled"]
        else:
            return self.runtime.get_current_capabilities()
    
    def get_task_history(self):
        """Get task execution history"""
        if self.use_agi_runtime:
            # Return recent cycles
            try:
                cycles = self.runtime.persistence.read_cycles(limit=10)
                return [
                    {
                        "cycle_id": c.cycle_id,
                        "timestamp": c.timestamp_start,
                        "goal": c.goal_stack[0] if c.goal_stack else "unknown",
                        "score": c.eval_scores.overall_score
                    }
                    for c in cycles
                ]
            except Exception as e:
                logger.error(f"Failed to get cycle history: {e}")
                return []
        else:
            return self.runtime.get_task_history()
    
    def get_reflections(self):
        """Get reflections"""
        if self.use_agi_runtime:
            # Return recent cycle reflections
            try:
                cycles = self.runtime.persistence.read_cycles(limit=10)
                return [
                    {
                        "cycle_id": c.cycle_id,
                        "timestamp": c.timestamp_start,
                        "reflection": c.reflection.model_dump()
                    }
                    for c in cycles
                ]
            except Exception as e:
                logger.error(f"Failed to get reflections: {e}")
                return []
        else:
            return self.runtime.get_reflections()
