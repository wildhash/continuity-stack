"""
AGI Runtime Module
Main cycle orchestrator implementing:
observe → model → plan → act → verify → reflect → store → evolve
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from .types import (
    CycleRecord, PlanStep, ActionResult, Reflection,
    EvalScores, MemoryWrite, WorldModel, ToolStatus
)
from .world_model import (
    create_empty_world_model, update_world_model,
    summarize_world_model, get_relevant_constraints
)
from .memory import ThreeTierMemory
from .safety import SafetyGate
from .evals import EvalHarness
from .persistence import CyclePersistence
from .signing import compute_cycle_hash, truncate_with_hash

logger = logging.getLogger(__name__)


class AGIRuntime:
    """
    Main AGI Runtime orchestrator
    Implements structured, measurable, auditable agent loop
    """
    
    def __init__(
        self,
        llm_client=None,
        memmachine_client=None,
        neo4j_client=None,
        environment: str = "production"
    ):
        """
        Args:
            llm_client: LLM client (optional, uses deterministic fallback)
            memmachine_client: MemMachine client for persistence
            neo4j_client: Neo4j client for graph operations
            environment: "production", "staging", or "development"
        """
        self.llm_client = llm_client
        self.memmachine_client = memmachine_client
        self.neo4j_client = neo4j_client
        self.environment = environment
        
        # Initialize components
        self.memory = ThreeTierMemory(memmachine_client)
        self.safety_gate = SafetyGate(environment)
        self.eval_harness = EvalHarness()
        self.persistence = CyclePersistence()
        
        # Runtime state
        self.agent_version = "1.0.0"
        self.world_model = create_empty_world_model()
        
        logger.info(f"AGI Runtime initialized (env: {environment}, agent: {self.agent_version})")
    
    async def run_cycle(self, goal: str, input_data: Dict[str, Any] = None) -> CycleRecord:
        """
        Execute one complete AGI cycle
        Returns: CycleRecord with full audit trail
        """
        cycle_id = f"cycle_{uuid.uuid4().hex[:8]}"
        timestamp_start = datetime.now().isoformat()
        
        logger.info(f"Starting cycle {cycle_id} with goal: {goal}")
        
        # Get previous hash for chain
        prev_cycle = self.persistence.get_latest_cycle()
        prev_hash = prev_cycle.hash if prev_cycle else None
        
        try:
            # Phase 1: OBSERVE
            observation = await self.observe(goal, input_data or {})
            
            # Phase 2: MODEL (update world state)
            world_state_before = self.world_model
            world_summary = summarize_world_model(world_state_before)
            
            # Phase 3: PLAN
            plan = await self.plan(goal, observation, world_summary)
            
            # Phase 4: SAFETY CHECK
            safety_assessment = self.safety_gate.assess_plan(plan, confidence=0.8)
            
            # Phase 5: ACT (if safe)
            actions_taken = []
            tool_outputs = {}
            
            if safety_assessment.status == ToolStatus.ALLOWED:
                actions_taken, tool_outputs = await self.act(plan)
            elif safety_assessment.status == ToolStatus.SANDBOXED:
                logger.warning(f"Plan requires sandbox rehearsal: {safety_assessment.reasons}")
                # Could implement sandbox here
            else:
                logger.warning(f"Plan blocked by safety gate: {safety_assessment.reasons}")
            
            # Phase 6: VERIFY (evaluate)
            # Create preliminary cycle for evaluation
            preliminary_reflection = Reflection(
                what_worked=["Cycle completed"] if actions_taken else [],
                what_failed=["No actions taken"] if not actions_taken else [],
                next_steps=[],
                lessons_learned=[]
            )
            
            preliminary_cycle = CycleRecord(
                cycle_id=cycle_id,
                timestamp_start=timestamp_start,
                timestamp_end=datetime.now().isoformat(),
                agent_version=self.agent_version,
                goal_stack=[goal],
                observation=observation,
                world_state_before=world_state_before,
                world_state_after=self.world_model,  # Will update later
                plan=plan,
                actions_taken=actions_taken,
                tool_outputs=tool_outputs,
                safety_assessment=safety_assessment,
                eval_scores=EvalScores(
                    reasoning_score=0.5,
                    planning_score=0.5,
                    tool_use_score=0.5,
                    safety_score=0.5,
                    overall_score=0.5
                ),
                reflection=preliminary_reflection,
                memory_writes=[],
                artifacts=[],
                prev_hash=prev_hash,
                hash=""
            )
            
            eval_scores = self.eval_harness.evaluate_cycle(preliminary_cycle)
            
            # Phase 7: REFLECT
            reflection = await self.reflect(
                goal, observation, plan, actions_taken,
                tool_outputs, safety_assessment, eval_scores
            )
            
            # Phase 8: UPDATE WORLD MODEL
            world_state_after = update_world_model(
                world_state_before,
                observation,
                [{"tool": a.tool, "status": a.status, "output": a.output} for a in actions_taken],
                reflection.model_dump()
            )
            self.world_model = world_state_after
            
            # Phase 9: STORE (memory writes)
            memory_writes = await self.store_memories(
                cycle_id, goal, reflection, eval_scores
            )
            
            # Phase 10: Create final cycle record
            timestamp_end = datetime.now().isoformat()
            
            cycle = CycleRecord(
                cycle_id=cycle_id,
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
                agent_version=self.agent_version,
                goal_stack=[goal],
                observation=observation,
                world_state_before=world_state_before,
                world_state_after=world_state_after,
                plan=plan,
                actions_taken=actions_taken,
                tool_outputs=tool_outputs,
                safety_assessment=safety_assessment,
                eval_scores=eval_scores,
                reflection=reflection,
                memory_writes=memory_writes,
                artifacts=[],
                confidence=eval_scores.overall_score,
                uncertainties=self._identify_uncertainties(plan, actions_taken),
                prev_hash=prev_hash,
                hash=""  # Will be computed next
            )
            
            # Compute hash
            cycle.hash = compute_cycle_hash(cycle, prev_hash)
            
            # Persist cycle
            self.persistence.append_cycle(cycle)
            logger.info(f"Cycle {cycle_id} completed (score: {eval_scores.overall_score:.2f})")
            
            # Phase 11: EVOLVE (check if version should increment)
            await self.evolve(eval_scores)
            
            return cycle
        
        except Exception as e:
            logger.error(f"Cycle {cycle_id} failed: {e}", exc_info=True)
            
            # Create failure cycle record
            failure_cycle = self._create_failure_cycle(
                cycle_id, timestamp_start, goal, str(e), prev_hash
            )
            self.persistence.append_cycle(failure_cycle)
            
            return failure_cycle
    
    async def observe(self, goal: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Observation phase: gather context
        """
        # Retrieve relevant memories
        world_summary = summarize_world_model(self.world_model)
        relevant_memories = await self.memory.retrieve_relevant(goal, world_summary, k=8)
        
        observation = {
            "goal": goal,
            "input_data": input_data,
            "timestamp": datetime.now().isoformat(),
            "agent_version": self.agent_version,
            "relevant_memories": [m.to_dict() for m in relevant_memories],
            "world_summary": world_summary,
            "environment": self.environment
        }
        
        return observation
    
    async def plan(
        self,
        goal: str,
        observation: Dict[str, Any],
        world_summary: str
    ) -> List[PlanStep]:
        """
        Planning phase: create plan
        Uses LLM if available, otherwise deterministic planner
        """
        # Get relevant constraints
        constraints = get_relevant_constraints(self.world_model, goal)
        
        if self.llm_client:
            # LLM-based planning (not implemented in this version)
            return await self._plan_deterministic(goal, observation, constraints)
        else:
            return await self._plan_deterministic(goal, observation, constraints)
    
    async def _plan_deterministic(
        self,
        goal: str,
        observation: Dict[str, Any],
        constraints: List
    ) -> List[PlanStep]:
        """Deterministic planner based on goal patterns"""
        plan = []
        
        # Simple rule-based planning
        if "validat" in goal.lower():
            plan.append(PlanStep(
                tool="validate_json",
                args={"data": observation.get("input_data", {})},
                expected_outcome="Data passes validation",
                rationale="Validation required before processing"
            ))
        
        if "analyz" in goal.lower() or "process" in goal.lower():
            plan.append(PlanStep(
                tool="analyze_data",
                args={"data": observation.get("input_data", {})},
                expected_outcome="Data analyzed successfully",
                rationale="Analyze input to extract insights"
            ))
        
        # Default: read and process
        if not plan:
            plan.append(PlanStep(
                tool="read_file",
                args={"path": "/default"},
                expected_outcome="File read successfully",
                rationale="Default action for goal"
            ))
        
        return plan
    
    async def act(self, plan: List[PlanStep]) -> Tuple[List[ActionResult], Dict[str, Any]]:
        """
        Action phase: execute approved plan steps
        Returns (actions_taken, tool_outputs)
        """
        actions_taken = []
        tool_outputs = {}
        
        for step in plan:
            start_time = datetime.now()
            
            # Simulate tool execution (deterministic for now)
            output = self._execute_tool_deterministic(step.tool, step.args)
            
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Truncate output and hash it
            truncated = truncate_with_hash(str(output), max_length=500)
            
            action = ActionResult(
                tool=step.tool,
                args=step.args,
                output=truncated["content"],
                output_hash=truncated["hash"],
                status="success",
                timestamp=start_time.isoformat(),
                execution_time_ms=execution_time_ms
            )
            
            actions_taken.append(action)
            tool_outputs[step.tool] = truncated
        
        return actions_taken, tool_outputs
    
    def _execute_tool_deterministic(self, tool: str, args: Dict[str, Any]) -> Any:
        """Execute tool with deterministic behavior"""
        if tool == "validate_json":
            return {"valid": True, "message": "Validation passed"}
        elif tool == "analyze_data":
            return {"analyzed": True, "insights": ["Data is well-formed"]}
        elif tool == "read_file":
            return {"content": "File contents here", "size": 1024}
        else:
            return {"executed": True, "tool": tool, "args": args}
    
    async def reflect(
        self,
        goal: str,
        observation: Dict[str, Any],
        plan: List[PlanStep],
        actions_taken: List[ActionResult],
        tool_outputs: Dict[str, Any],
        safety_assessment,
        eval_scores: EvalScores
    ) -> Reflection:
        """
        Reflection phase: analyze what happened
        """
        what_worked = []
        what_failed = []
        next_steps = []
        lessons_learned = []
        
        # Analyze actions
        if actions_taken:
            successful = [a for a in actions_taken if a.status == "success"]
            what_worked.append(f"{len(successful)}/{len(actions_taken)} actions completed successfully")
        else:
            what_failed.append("No actions were executed")
        
        # Analyze safety
        if safety_assessment.status == ToolStatus.BLOCKED:
            what_failed.append(f"Safety gate blocked plan: {safety_assessment.reasons}")
            lessons_learned.append("Need to improve plan safety")
        elif safety_assessment.status == ToolStatus.ALLOWED:
            what_worked.append("Plan passed safety checks")
        
        # Analyze eval scores
        if eval_scores.overall_score >= 0.7:
            what_worked.append(f"High quality cycle (score: {eval_scores.overall_score:.2f})")
        else:
            what_failed.append(f"Low quality cycle (score: {eval_scores.overall_score:.2f})")
            lessons_learned.append("Need to improve cycle quality")
        
        # Determine next steps
        if what_failed:
            next_steps.append("Review and address failures")
        next_steps.append("Continue with next goal")
        
        return Reflection(
            what_worked=what_worked,
            what_failed=what_failed,
            next_steps=next_steps,
            lessons_learned=lessons_learned
        )
    
    async def store_memories(
        self,
        cycle_id: str,
        goal: str,
        reflection: Reflection,
        eval_scores: EvalScores
    ) -> List[MemoryWrite]:
        """
        Memory storage phase
        """
        memory_writes = []
        
        # Store lessons as semantic memories
        for lesson in reflection.lessons_learned:
            try:
                memory_id = await self.memory.store_semantic(
                    fact=lesson,
                    category="lesson",
                    confidence=eval_scores.overall_score
                )
                memory_writes.append(MemoryWrite(
                    memory_type="semantic",
                    memory_id=memory_id,
                    content=lesson,
                    metadata={"cycle_id": cycle_id}
                ))
            except Exception as e:
                logger.error(f"Failed to store semantic memory: {e}")
        
        return memory_writes
    
    async def evolve(self, eval_scores: EvalScores):
        """
        Evolution phase: increment version if improved
        """
        # Simple evolution: increment patch version if overall score > 0.8
        if eval_scores.overall_score > 0.8:
            version_parts = self.agent_version.split(".")
            patch = int(version_parts[2]) + 1
            new_version = f"{version_parts[0]}.{version_parts[1]}.{patch}"
            
            logger.info(f"Agent evolved: {self.agent_version} → {new_version}")
            self.agent_version = new_version
    
    def _identify_uncertainties(
        self,
        plan: List[PlanStep],
        actions_taken: List[ActionResult]
    ) -> List[str]:
        """Identify uncertainties in the cycle"""
        uncertainties = []
        
        if len(actions_taken) < len(plan):
            uncertainties.append(f"Only {len(actions_taken)}/{len(plan)} planned actions executed")
        
        return uncertainties
    
    def _create_failure_cycle(
        self,
        cycle_id: str,
        timestamp_start: str,
        goal: str,
        error: str,
        prev_hash: Optional[str]
    ) -> CycleRecord:
        """Create a cycle record for a failed cycle"""
        from .types import SafetyAssessment, ToolStatus
        
        timestamp_end = datetime.now().isoformat()
        
        cycle = CycleRecord(
            cycle_id=cycle_id,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            agent_version=self.agent_version,
            goal_stack=[goal],
            observation={"error": error},
            world_state_before=self.world_model,
            world_state_after=self.world_model,
            plan=[],
            actions_taken=[],
            tool_outputs={},
            safety_assessment=SafetyAssessment(
                status=ToolStatus.BLOCKED,
                allowed_tools=[],
                blocked_tools=[],
                reasons=[f"Cycle failed: {error}"],
                risk_flags=["cycle_failure"]
            ),
            eval_scores=EvalScores(
                reasoning_score=0.0,
                planning_score=0.0,
                tool_use_score=0.0,
                safety_score=0.0,
                overall_score=0.0
            ),
            reflection=Reflection(
                what_worked=[],
                what_failed=[error],
                next_steps=["Debug and retry"],
                lessons_learned=["Cycle execution failed"]
            ),
            memory_writes=[],
            artifacts=[],
            prev_hash=prev_hash,
            hash=""
        )
        
        cycle.hash = compute_cycle_hash(cycle, prev_hash)
        return cycle
