"""
AGI Runtime Type Definitions
Schemas for CycleRecord, WorldModel, and related structures
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ToolStatus(str, Enum):
    """Status of tool execution"""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    SANDBOXED = "sandboxed"


class PlanStep(BaseModel):
    """Single step in a plan"""
    tool: str
    args: Dict[str, Any]
    expected_outcome: str
    rationale: Optional[str] = None


class ActionResult(BaseModel):
    """Result of executing an action"""
    tool: str
    args: Dict[str, Any]
    output: Any
    output_hash: str
    status: str
    timestamp: str
    execution_time_ms: float


class SafetyAssessment(BaseModel):
    """Safety evaluation of a plan or action"""
    status: ToolStatus
    allowed_tools: List[str]
    blocked_tools: List[str]
    reasons: List[str]
    risk_flags: List[str]
    sandbox_required: bool = False


class EvalScores(BaseModel):
    """Evaluation scores for a cycle"""
    reasoning_score: float = Field(ge=0.0, le=1.0)
    planning_score: float = Field(ge=0.0, le=1.0)
    tool_use_score: float = Field(ge=0.0, le=1.0)
    safety_score: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)
    details: Dict[str, Any] = Field(default_factory=dict)


class MemoryWrite(BaseModel):
    """Record of a memory write operation"""
    memory_type: str  # episodic, semantic, procedural
    memory_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorldEntity(BaseModel):
    """Entity in the world model"""
    id: str
    type: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class WorldRelation(BaseModel):
    """Relation between entities"""
    from_id: str
    to_id: str
    type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorldHypothesis(BaseModel):
    """Hypothesis in the world model"""
    claim: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: List[str] = Field(default_factory=list)


class WorldConstraint(BaseModel):
    """Constraint in the world model"""
    type: str  # safety, task, environment
    description: str
    enforced: bool = True


class WorldEvent(BaseModel):
    """Event in the timeline"""
    timestamp: str
    event: str
    refs: List[str] = Field(default_factory=list)


class WorldModel(BaseModel):
    """Lightweight world model structure"""
    entities: List[WorldEntity] = Field(default_factory=list)
    relations: List[WorldRelation] = Field(default_factory=list)
    constraints: List[WorldConstraint] = Field(default_factory=list)
    hypotheses: List[WorldHypothesis] = Field(default_factory=list)
    timeline: List[WorldEvent] = Field(default_factory=list)


class Reflection(BaseModel):
    """Reflection on cycle execution"""
    what_worked: List[str] = Field(default_factory=list)
    what_failed: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)


class CycleRecord(BaseModel):
    """
    Complete record of a single AGI cycle
    This is the canonical structure that gets hashed and stored
    """
    # Identity
    cycle_id: str
    timestamp_start: str
    timestamp_end: str
    agent_version: str
    
    # Goals and context
    goal_stack: List[str] = Field(default_factory=list)
    
    # Observation phase
    observation: Dict[str, Any] = Field(default_factory=dict)
    
    # World model
    world_state_before: WorldModel
    world_state_after: WorldModel
    
    # Planning phase
    plan: List[PlanStep] = Field(default_factory=list)
    
    # Action phase
    actions_taken: List[ActionResult] = Field(default_factory=list)
    tool_outputs: Dict[str, Any] = Field(default_factory=dict)  # Truncated + hashes
    
    # Safety phase
    safety_assessment: SafetyAssessment
    
    # Evaluation phase
    eval_scores: EvalScores
    
    # Reflection phase
    reflection: Reflection
    
    # Memory phase
    memory_writes: List[MemoryWrite] = Field(default_factory=list)
    
    # Artifacts
    artifacts: List[str] = Field(default_factory=list)  # Paths to generated files
    
    # Confidence and uncertainties
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    uncertainties: List[str] = Field(default_factory=list)
    
    # Hash chain
    prev_hash: Optional[str] = None
    hash: str = ""
    
    class Config:
        json_schema_extra = {
            "example": {
                "cycle_id": "cycle_001",
                "timestamp_start": "2024-01-01T00:00:00Z",
                "timestamp_end": "2024-01-01T00:00:05Z",
                "agent_version": "1.0.0",
                "goal_stack": ["Complete task X"],
                "observation": {"input": "test"},
                "world_state_before": {},
                "world_state_after": {},
                "plan": [],
                "actions_taken": [],
                "tool_outputs": {},
                "safety_assessment": {"status": "allowed", "allowed_tools": [], "blocked_tools": [], "reasons": [], "risk_flags": []},
                "eval_scores": {"reasoning_score": 0.8, "planning_score": 0.7, "tool_use_score": 0.9, "safety_score": 1.0, "overall_score": 0.85},
                "reflection": {"what_worked": [], "what_failed": [], "next_steps": [], "lessons_learned": []},
                "memory_writes": [],
                "artifacts": [],
                "confidence": 0.8,
                "uncertainties": [],
                "prev_hash": None,
                "hash": "abc123..."
            }
        }
