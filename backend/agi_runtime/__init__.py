"""
AGI Runtime Module
Structured, persistent, measurable agent loop with safety gates and eval harness
"""
from .types import (
    CycleRecord, PlanStep, ActionResult, Reflection,
    EvalScores, MemoryWrite, WorldModel, SafetyAssessment,
    ToolStatus, WorldEntity, WorldRelation, WorldConstraint,
    WorldHypothesis, WorldEvent
)
from .runtime import AGIRuntime
from .memory import ThreeTierMemory, MemoryItem
from .safety import SafetyGate
from .evals import EvalHarness, run_eval_suite, run_smoke_suite
from .persistence import CyclePersistence
from .signing import compute_hash, compute_cycle_hash, verify_hash_chain
from .world_model import (
    create_empty_world_model, update_world_model,
    summarize_world_model, get_relevant_constraints
)

__all__ = [
    # Main runtime
    "AGIRuntime",
    
    # Types
    "CycleRecord",
    "PlanStep",
    "ActionResult",
    "Reflection",
    "EvalScores",
    "MemoryWrite",
    "WorldModel",
    "SafetyAssessment",
    "ToolStatus",
    "WorldEntity",
    "WorldRelation",
    "WorldConstraint",
    "WorldHypothesis",
    "WorldEvent",
    
    # Components
    "ThreeTierMemory",
    "MemoryItem",
    "SafetyGate",
    "EvalHarness",
    "CyclePersistence",
    
    # Utilities
    "compute_hash",
    "compute_cycle_hash",
    "verify_hash_chain",
    "create_empty_world_model",
    "update_world_model",
    "summarize_world_model",
    "get_relevant_constraints",
    "run_eval_suite",
    "run_smoke_suite",
]

__version__ = "0.1.0"
