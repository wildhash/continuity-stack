"""
Tests for Continuity Core
"""
import pytest
from continuity_core import ContinuityCore, TaskStatus, Reflection, AgentVersion


@pytest.mark.asyncio
async def test_task_execution_failure():
    """Test task execution that fails"""
    core = ContinuityCore()
    
    task = {
        "id": "test_task_1",
        "type": "validation_task",
        "data": {"input": "test"},
        "should_fail_first": True
    }
    
    result = await core.execute_task(task)
    
    assert result["status"] == TaskStatus.FAILED.value
    assert result["error"] is not None
    assert len(core.reflections) == 1


@pytest.mark.asyncio
async def test_task_execution_success():
    """Test task execution that succeeds"""
    core = ContinuityCore()
    
    # Add capability first
    core.agent_version.add_capability("handle_validation_task")
    
    task = {
        "id": "test_task_2",
        "type": "validation_task",
        "data": {"input": "test"},
        "should_fail_first": False
    }
    
    result = await core.execute_task(task)
    
    assert result["status"] == TaskStatus.SUCCESS.value
    assert result["output"] is not None


@pytest.mark.asyncio
async def test_reflection_on_failure():
    """Test reflection generates lessons"""
    core = ContinuityCore()
    
    task = {
        "id": "test_task_3",
        "type": "new_task",
        "data": {},
        "should_fail_first": True
    }
    
    result = await core.execute_task(task)
    
    lessons = core.get_learned_lessons()
    assert len(lessons) > 0
    
    capabilities = core.get_current_capabilities()
    assert "handle_new_task" in capabilities


@pytest.mark.asyncio
async def test_learning_loop():
    """Test complete learning loop: fail -> reflect -> learn -> succeed"""
    core = ContinuityCore()
    
    # First attempt - should fail
    task1 = {
        "id": "test_loop_1",
        "type": "learning_task",
        "data": {},
        "should_fail_first": True
    }
    
    result1 = await core.execute_task(task1)
    assert result1["status"] == TaskStatus.FAILED.value
    
    # Check learning happened
    assert len(core.get_learned_lessons()) > 0
    assert "handle_learning_task" in core.get_current_capabilities()
    
    # Second attempt - should succeed
    task2 = {
        "id": "test_loop_2",
        "type": "learning_task",
        "data": {},
        "should_fail_first": False
    }
    
    result2 = await core.execute_task(task2)
    assert result2["status"] == TaskStatus.SUCCESS.value


def test_agent_version():
    """Test agent version management"""
    version = AgentVersion("1.0.0", ["capability1", "capability2"])
    
    version.add_capability("capability3")
    assert "capability3" in version.capabilities
    
    version.add_lesson("Test lesson")
    assert "Test lesson" in version.learned_lessons


def test_reflection():
    """Test reflection analysis"""
    reflection = Reflection("task_1", TaskStatus.FAILED, "Validation error occurred")
    
    context = {"error_type": "ValidationError"}
    lesson = reflection.analyze_failure(context)
    
    assert reflection.lesson_learned is not None
    assert reflection.improvement_strategy is not None
