"""
Tests for AGI Runtime
"""
import pytest
import os
import json
from datetime import datetime
from pathlib import Path

from agi_runtime.types import (
    CycleRecord, PlanStep, ActionResult, Reflection,
    EvalScores, SafetyAssessment, ToolStatus, WorldModel
)
from agi_runtime.signing import (
    canonical_json, compute_hash, compute_cycle_hash,
    verify_hash_chain, truncate_with_hash
)
from agi_runtime.safety import SafetyGate, SAFE_TOOLS, BLOCKED_TOOLS
from agi_runtime.persistence import CyclePersistence
from agi_runtime.evals import run_smoke_suite
from agi_runtime.world_model import (
    create_empty_world_model, update_world_model, summarize_world_model
)
from agi_runtime.runtime import AGIRuntime


class TestSigning:
    """Test canonical JSON and hash chain"""
    
    def test_canonical_json_stable(self):
        """Test that canonical JSON is stable for same input"""
        data = {"b": 2, "a": 1, "c": [3, 2, 1]}
        
        json1 = canonical_json(data)
        json2 = canonical_json(data)
        
        assert json1 == json2
        assert json1 == '{"a":1,"b":2,"c":[3,2,1]}'
    
    def test_compute_hash_stable(self):
        """Test that hash is stable for same input"""
        data = {"test": "data", "number": 42}
        
        hash1 = compute_hash(data)
        hash2 = compute_hash(data)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex is 64 chars
    
    def test_compute_hash_different(self):
        """Test that different data produces different hash"""
        data1 = {"test": "data1"}
        data2 = {"test": "data2"}
        
        hash1 = compute_hash(data1)
        hash2 = compute_hash(data2)
        
        assert hash1 != hash2
    
    def test_cycle_hash_chain(self):
        """Test cycle hash includes prev_hash"""
        cycle1 = CycleRecord(
            cycle_id="cycle1",
            timestamp_start="2024-01-01T00:00:00Z",
            timestamp_end="2024-01-01T00:00:05Z",
            agent_version="1.0.0",
            goal_stack=["test"],
            observation={},
            world_state_before=WorldModel(),
            world_state_after=WorldModel(),
            plan=[],
            actions_taken=[],
            tool_outputs={},
            safety_assessment=SafetyAssessment(
                status=ToolStatus.ALLOWED,
                allowed_tools=[],
                blocked_tools=[],
                reasons=[],
                risk_flags=[]
            ),
            eval_scores=EvalScores(
                reasoning_score=0.5,
                planning_score=0.5,
                tool_use_score=0.5,
                safety_score=1.0,
                overall_score=0.6
            ),
            reflection=Reflection(),
            prev_hash=None,
            hash=""
        )
        
        hash1 = compute_cycle_hash(cycle1, None)
        cycle1.hash = hash1
        
        # Second cycle references first
        cycle2 = CycleRecord(
            cycle_id="cycle2",
            timestamp_start="2024-01-01T00:00:10Z",
            timestamp_end="2024-01-01T00:00:15Z",
            agent_version="1.0.0",
            goal_stack=["test2"],
            observation={},
            world_state_before=WorldModel(),
            world_state_after=WorldModel(),
            plan=[],
            actions_taken=[],
            tool_outputs={},
            safety_assessment=SafetyAssessment(
                status=ToolStatus.ALLOWED,
                allowed_tools=[],
                blocked_tools=[],
                reasons=[],
                risk_flags=[]
            ),
            eval_scores=EvalScores(
                reasoning_score=0.5,
                planning_score=0.5,
                tool_use_score=0.5,
                safety_score=1.0,
                overall_score=0.6
            ),
            reflection=Reflection(),
            prev_hash=hash1,
            hash=""
        )
        
        hash2 = compute_cycle_hash(cycle2, hash1)
        cycle2.hash = hash2
        
        # Hashes should be different
        assert hash1 != hash2
        
        # Verify chain
        assert verify_hash_chain([cycle1, cycle2])
    
    def test_verify_hash_chain_detects_tampering(self):
        """Test that hash chain verification detects tampering"""
        cycle1 = CycleRecord(
            cycle_id="cycle1",
            timestamp_start="2024-01-01T00:00:00Z",
            timestamp_end="2024-01-01T00:00:05Z",
            agent_version="1.0.0",
            goal_stack=["test"],
            observation={},
            world_state_before=WorldModel(),
            world_state_after=WorldModel(),
            plan=[],
            actions_taken=[],
            tool_outputs={},
            safety_assessment=SafetyAssessment(
                status=ToolStatus.ALLOWED,
                allowed_tools=[],
                blocked_tools=[],
                reasons=[],
                risk_flags=[]
            ),
            eval_scores=EvalScores(
                reasoning_score=0.5,
                planning_score=0.5,
                tool_use_score=0.5,
                safety_score=1.0,
                overall_score=0.6
            ),
            reflection=Reflection(),
            prev_hash=None,
            hash=""
        )
        
        cycle1.hash = compute_cycle_hash(cycle1, None)
        
        # Tamper with cycle
        original_goal = cycle1.goal_stack[0]
        cycle1.goal_stack = ["tampered"]
        
        # Verification should fail
        assert not verify_hash_chain([cycle1])
        
        # Restore
        cycle1.goal_stack = [original_goal]
        assert verify_hash_chain([cycle1])
    
    def test_truncate_with_hash(self):
        """Test content truncation with hash"""
        short_content = "short"
        result = truncate_with_hash(short_content, max_length=100)
        
        assert result["content"] == short_content
        assert not result["truncated"]
        assert result["hash"]
        assert result["full_length"] == 5
        
        long_content = "x" * 2000
        result = truncate_with_hash(long_content, max_length=100)
        
        assert len(result["content"]) < len(long_content)
        assert result["truncated"]
        assert result["hash"]
        assert result["full_length"] == 2000


class TestSafety:
    """Test safety gates and tripwires"""
    
    def test_safety_gate_blocks_injection(self):
        """Test that safety gate blocks injection attempts"""
        gate = SafetyGate(environment="production")
        
        malicious_plan = [
            PlanStep(
                tool="execute_command",
                args={"command": "<script>alert('xss')</script>"},
                expected_outcome="Run script"
            )
        ]
        
        assessment = gate.assess_plan(malicious_plan, confidence=0.8)
        
        assert assessment.status == ToolStatus.BLOCKED
        assert len(assessment.blocked_tools) > 0
        assert "injection" in str(assessment.reasons).lower() or "execute_command" in str(assessment.blocked_tools)
    
    def test_safety_gate_allows_safe_tools(self):
        """Test that safety gate allows safe tools"""
        gate = SafetyGate(environment="production")
        
        safe_plan = [
            PlanStep(
                tool="read_file",
                args={"path": "/test.txt"},
                expected_outcome="Read file"
            )
        ]
        
        assessment = gate.assess_plan(safe_plan, confidence=0.8)
        
        assert assessment.status == ToolStatus.ALLOWED
        assert len(assessment.blocked_tools) == 0
    
    def test_safety_gate_blocks_unknown_tools(self):
        """Test that safety gate blocks unknown tools"""
        gate = SafetyGate(environment="production")
        
        unknown_plan = [
            PlanStep(
                tool="unknown_dangerous_tool",
                args={},
                expected_outcome="Unknown"
            )
        ]
        
        assessment = gate.assess_plan(unknown_plan, confidence=0.8)
        
        assert assessment.status == ToolStatus.BLOCKED
        assert "unknown_dangerous_tool" in assessment.blocked_tools
    
    def test_safety_gate_requires_sandbox_for_risky_tools_low_confidence(self):
        """Test that risky tools with low confidence require sandbox"""
        gate = SafetyGate(environment="development")  # Allows risky tools
        
        risky_plan = [
            PlanStep(
                tool="write_file",
                args={"path": "/test.txt", "content": "data"},
                expected_outcome="Write file"
            )
        ]
        
        # Low confidence
        assessment = gate.assess_plan(risky_plan, confidence=0.5)
        
        assert assessment.sandbox_required
        assert assessment.status == ToolStatus.SANDBOXED


class TestPersistence:
    """Test cycle persistence"""
    
    @pytest.fixture
    def temp_persistence(self, tmp_path):
        """Create a temporary persistence instance"""
        return CyclePersistence(base_path=str(tmp_path / "test_runs"))
    
    def test_append_and_read_cycle(self, temp_persistence):
        """Test appending and reading cycles"""
        cycle = CycleRecord(
            cycle_id="test_cycle",
            timestamp_start=datetime.now().isoformat(),
            timestamp_end=datetime.now().isoformat(),
            agent_version="1.0.0",
            goal_stack=["test goal"],
            observation={"test": "data"},
            world_state_before=WorldModel(),
            world_state_after=WorldModel(),
            plan=[],
            actions_taken=[],
            tool_outputs={},
            safety_assessment=SafetyAssessment(
                status=ToolStatus.ALLOWED,
                allowed_tools=[],
                blocked_tools=[],
                reasons=[],
                risk_flags=[]
            ),
            eval_scores=EvalScores(
                reasoning_score=0.5,
                planning_score=0.5,
                tool_use_score=0.5,
                safety_score=1.0,
                overall_score=0.6
            ),
            reflection=Reflection(
                what_worked=["Test worked"],
                what_failed=[],
                next_steps=[],
                lessons_learned=["Test lesson"]
            ),
            prev_hash=None,
            hash="test_hash"
        )
        
        # Append
        path = temp_persistence.append_cycle(cycle)
        assert os.path.exists(path)
        
        # Read
        cycles = temp_persistence.read_cycles()
        assert len(cycles) == 1
        assert cycles[0].cycle_id == "test_cycle"
        assert cycles[0].goal_stack == ["test goal"]
    
    def test_get_latest_cycle(self, temp_persistence):
        """Test getting the latest cycle"""
        # No cycles yet
        assert temp_persistence.get_latest_cycle() is None
        
        # Add a cycle
        cycle = CycleRecord(
            cycle_id="latest",
            timestamp_start=datetime.now().isoformat(),
            timestamp_end=datetime.now().isoformat(),
            agent_version="1.0.0",
            goal_stack=[],
            observation={},
            world_state_before=WorldModel(),
            world_state_after=WorldModel(),
            plan=[],
            actions_taken=[],
            tool_outputs={},
            safety_assessment=SafetyAssessment(
                status=ToolStatus.ALLOWED,
                allowed_tools=[],
                blocked_tools=[],
                reasons=[],
                risk_flags=[]
            ),
            eval_scores=EvalScores(
                reasoning_score=0.5,
                planning_score=0.5,
                tool_use_score=0.5,
                safety_score=1.0,
                overall_score=0.6
            ),
            reflection=Reflection(),
            prev_hash=None,
            hash="hash"
        )
        
        temp_persistence.append_cycle(cycle)
        
        latest = temp_persistence.get_latest_cycle()
        assert latest is not None
        assert latest.cycle_id == "latest"


class TestEvals:
    """Test evaluation harness"""
    
    def test_smoke_suite_runs(self):
        """Test that smoke suite runs successfully"""
        results = run_smoke_suite()
        
        assert "overall_passed" in results
        assert "tests" in results
        assert "summary" in results
        
        # All smoke tests should pass
        assert results["overall_passed"]
        assert results["tests"]["reasoning_smoke"]["passed"]
        assert results["tests"]["planning_smoke"]["passed"]
        assert results["tests"]["tool_use_smoke"]["passed"]
        assert results["tests"]["safety_smoke"]["passed"]


class TestWorldModel:
    """Test world model"""
    
    def test_create_empty_world_model(self):
        """Test creating empty world model"""
        model = create_empty_world_model()
        
        assert len(model.entities) == 0
        assert len(model.relations) == 0
        assert len(model.constraints) == 0
        assert len(model.hypotheses) == 0
        assert len(model.timeline) == 0
    
    def test_update_world_model(self):
        """Test updating world model"""
        model = create_empty_world_model()
        
        observation = {"task_type": "validation_task"}
        tool_results = [{"tool": "validate", "status": "success", "output": "OK"}]
        reflection = {"lessons_learned": ["Validation is important"]}
        
        updated = update_world_model(model, observation, tool_results, reflection)
        
        # Should have added entities, constraints, hypotheses
        assert len(updated.entities) > 0 or len(updated.constraints) > 0 or len(updated.hypotheses) > 0
        assert len(updated.timeline) > 0  # At least the update event
    
    def test_summarize_world_model(self):
        """Test world model summarization"""
        model = create_empty_world_model()
        summary = summarize_world_model(model)
        
        assert "empty" in summary.lower()
        
        # Add some data
        observation = {"task_type": "test"}
        tool_results = []
        reflection = {}
        
        updated = update_world_model(model, observation, tool_results, reflection)
        summary = summarize_world_model(updated)
        
        assert len(summary) > 0


@pytest.mark.asyncio
class TestAGIRuntime:
    """Test AGI Runtime integration"""
    
    async def test_run_cycle_deterministic(self):
        """Test running one AGI cycle in deterministic mode"""
        runtime = AGIRuntime(
            llm_client=None,  # Deterministic mode
            memmachine_client=None,
            neo4j_client=None,
            environment="development"
        )
        
        # Run a cycle
        cycle = await runtime.run_cycle(
            goal="validate data",
            input_data={"test": "data"}
        )
        
        # Verify cycle record
        assert cycle.cycle_id is not None
        assert cycle.agent_version == "1.0.0"
        assert len(cycle.goal_stack) == 1
        assert cycle.goal_stack[0] == "validate data"
        
        # Verify hash chain
        assert cycle.hash != ""
        assert len(cycle.hash) == 64  # SHA-256
        
        # Verify observation
        assert "goal" in cycle.observation
        
        # Verify plan
        assert len(cycle.plan) > 0
        
        # Verify safety
        assert cycle.safety_assessment is not None
        
        # Verify eval scores
        assert 0.0 <= cycle.eval_scores.overall_score <= 1.0
        
        # Verify reflection
        assert cycle.reflection is not None
    
    async def test_hash_chain_across_cycles(self, tmp_path):
        """Test that hash chain works across multiple cycles"""
        runtime = AGIRuntime(environment="development")
        runtime.persistence = CyclePersistence(base_path=str(tmp_path / "test_chain"))
        
        # Run first cycle
        cycle1 = await runtime.run_cycle("goal1", {})
        assert cycle1.prev_hash is None
        assert cycle1.hash != ""
        
        # Run second cycle
        cycle2 = await runtime.run_cycle("goal2", {})
        assert cycle2.prev_hash == cycle1.hash
        assert cycle2.hash != ""
        assert cycle2.hash != cycle1.hash
        
        # Verify chain
        assert verify_hash_chain([cycle1, cycle2])
    
    async def test_cycle_persisted_to_jsonl(self, tmp_path):
        """Test that cycles are persisted to JSONL"""
        runtime = AGIRuntime(environment="development")
        runtime.persistence = CyclePersistence(base_path=str(tmp_path / "test_agi_runs"))
        
        cycle = await runtime.run_cycle("test goal", {})
        
        # Check that JSONL file exists
        cycles = runtime.persistence.read_cycles()
        assert len(cycles) >= 1
        assert any(c.cycle_id == cycle.cycle_id for c in cycles)
