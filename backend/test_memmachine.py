"""
Tests for MemMachine
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from memmachine import MemMachine


@pytest.fixture
def temp_storage():
    """Create temporary storage directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_store_memory(temp_storage):
    """Test storing a memory"""
    mm = MemMachine(storage_path=temp_storage)
    
    memory_id = mm.store_memory({
        "content": "Test memory",
        "category": "test",
        "description": "A test memory"
    })
    
    assert memory_id.startswith("mem_")
    
    memories = mm.get_memories()
    assert len(memories) == 1
    assert memories[0]["content"] == "Test memory"


def test_get_memories_with_filter(temp_storage):
    """Test retrieving memories with category filter"""
    mm = MemMachine(storage_path=temp_storage)
    
    mm.store_memory({"content": "Memory 1", "category": "cat1"})
    mm.store_memory({"content": "Memory 2", "category": "cat2"})
    mm.store_memory({"content": "Memory 3", "category": "cat1"})
    
    cat1_memories = mm.get_memories(category="cat1")
    assert len(cat1_memories) == 2


def test_store_decision(temp_storage):
    """Test storing a decision"""
    mm = MemMachine(storage_path=temp_storage)
    
    decision_id = mm.store_decision({
        "title": "Test Decision",
        "description": "A test decision",
        "status": "pending"
    })
    
    assert decision_id.startswith("decision_")
    
    decisions = mm.get_decisions()
    assert len(decisions) == 1


def test_agent_state(temp_storage):
    """Test agent state management"""
    mm = MemMachine(storage_path=temp_storage)
    
    mm.update_agent_state({
        "version": "1.0.0",
        "capabilities": ["cap1", "cap2"]
    })
    
    state = mm.get_agent_state()
    assert state["version"] == "1.0.0"
    assert len(state["capabilities"]) == 2


def test_search_memories(temp_storage):
    """Test memory search"""
    mm = MemMachine(storage_path=temp_storage)
    
    mm.store_memory({"content": "Python programming", "category": "tech"})
    mm.store_memory({"content": "JavaScript coding", "category": "tech"})
    mm.store_memory({"content": "Cooking recipes", "category": "food"})
    
    results = mm.search_memories("programming")
    assert len(results) == 1
    assert "Python" in results[0]["content"]
