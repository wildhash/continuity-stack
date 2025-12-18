"""
Integration tests for the complete Continuity Stack workflow
Tests the fail -> reflect -> learn -> succeed cycle
"""
import pytest
import asyncio
from continuity_core import ContinuityCore, TaskStatus
from llm_client import LLMClient
from memmachine_client import MemMachineClient


@pytest.mark.asyncio
async def test_learning_cycle():
    """Test the complete learning cycle: fail -> reflect -> learn -> succeed"""
    # Initialize components
    llm = LLMClient()
    mm = MemMachineClient()
    core = ContinuityCore(llm_client=llm, memmachine_client=mm, neo4j_client=None)
    
    initial_version = core.current_version
    initial_capabilities = len(core.get_current_capabilities())
    
    # First run: should fail
    result1 = await core.execute_task({
        "type": "validation_task",
        "data": {"test": "data"},
        "should_fail_first": True
    })
    
    # Verify failure
    assert result1["status"] == TaskStatus.FAILED.value
    assert "Missing capability" in result1["error"]
    assert "lesson" in result1
    assert result1["lesson"] is not None
    
    # Verify learning occurred
    new_capabilities = core.get_current_capabilities()
    assert len(new_capabilities) > initial_capabilities
    assert "handle_validation_task" in new_capabilities
    
    # Verify version increment
    assert core.current_version != initial_version
    
    # Verify reflection was stored
    reflections = core.get_reflections()
    assert len(reflections) > 0
    last_reflection = reflections[-1]
    assert "lesson_learned" in last_reflection
    
    # Second run: should succeed
    result2 = await core.execute_task({
        "type": "validation_task",
        "data": {"test": "data"},
        "should_fail_first": False
    })
    
    # Verify success
    assert result2["status"] == TaskStatus.SUCCESS.value
    assert result2["output"] is not None
    
    # Cleanup
    await mm.close()


@pytest.mark.asyncio
async def test_memory_citation():
    """Test that agent cites recalled knowledge on second run"""
    llm = LLMClient()
    mm = MemMachineClient()
    core = ContinuityCore(llm_client=llm, memmachine_client=mm, neo4j_client=None)
    
    # First run to create knowledge
    await core.execute_task({
        "type": "test_task",
        "data": {},
        "should_fail_first": True
    })
    
    # Second run should cite knowledge
    result = await core.execute_task({
        "type": "test_task",
        "data": {},
        "should_fail_first": False
    })
    
    # Verify the result contains citation information
    assert "steps" in result
    assert len(result["steps"]) > 0
    
    # Check if capability was used
    capability_check_step = next((s for s in result["steps"] if s["step"] == "check_capability"), None)
    assert capability_check_step is not None
    assert capability_check_step["has_capability"] == True
    
    await mm.close()


@pytest.mark.asyncio
async def test_version_incrementing():
    """Test that agent version increments after learning"""
    llm = LLMClient()
    mm = MemMachineClient()
    core = ContinuityCore(llm_client=llm, memmachine_client=mm, neo4j_client=None)
    
    initial_version = core.current_version
    
    # Trigger learning by failing a task
    await core.execute_task({
        "type": "unique_task_type",
        "data": {},
        "should_fail_first": True
    })
    
    # Verify version incremented
    assert core.current_version != initial_version
    
    # Version should follow semantic versioning
    initial_parts = initial_version.split(".")
    new_parts = core.current_version.split(".")
    
    # Patch version should have incremented
    assert int(new_parts[2]) == int(initial_parts[2]) + 1
    
    await mm.close()


@pytest.mark.asyncio
async def test_deterministic_reflection():
    """Test deterministic reflection without LLM"""
    llm = LLMClient()  # Will use deterministic mode if no API key
    mm = MemMachineClient()
    core = ContinuityCore(llm_client=llm, memmachine_client=mm, neo4j_client=None)
    
    # Run a validation task to trigger specific reflection
    result = await core.execute_task({
        "type": "validation_task",
        "data": {},
        "should_fail_first": True
    })
    
    # Verify deterministic lesson
    assert "lesson" in result
    assert "validation" in result["lesson"].lower() or "schema" in result["lesson"].lower()
    
    # Verify improvement strategy exists
    assert "reflection" in result
    assert "improvement_strategy" in result["reflection"]
    
    await mm.close()


@pytest.mark.asyncio
async def test_citation_format():
    """Test that citations are always present in consistent format"""
    llm = LLMClient()
    mm = MemMachineClient()
    core = ContinuityCore(llm_client=llm, memmachine_client=mm, neo4j_client=None)
    
    # First run to create knowledge
    await core.execute_task({
        "type": "citation_test_task",
        "data": {},
        "should_fail_first": True
    })
    
    # Second run should have citations
    result = await core.execute_task({
        "type": "citation_test_task",
        "data": {},
        "should_fail_first": False
    })
    
    # Verify output structure
    assert "output" in result
    assert result["output"] is not None
    
    # Verify explicit citation fields are always present
    assert "memory_citations" in result["output"]
    assert "graph_citations" in result["output"]
    assert "citation_summary" in result["output"]
    
    # Verify citation_summary structure
    citation_summary = result["output"]["citation_summary"]
    assert "has_citations" in citation_summary
    assert "memory_count" in citation_summary
    assert "lesson_count" in citation_summary
    
    # Verify counts are numeric
    assert isinstance(citation_summary["memory_count"], int)
    assert isinstance(citation_summary["lesson_count"], int)
    
    await mm.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
