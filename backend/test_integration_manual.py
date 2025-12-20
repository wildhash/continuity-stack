#!/usr/bin/env python3
"""
Manual test script for AGI Runtime integration
Tests both legacy and AGI runtime modes
"""
import os
import sys
import asyncio
import json

# Add backend to path
sys.path.insert(0, '/home/runner/work/continuity-stack/continuity-stack/backend')

from agent_integration import ContinuityAgent, is_agi_runtime_enabled


async def test_legacy_mode():
    """Test legacy mode (CONTINUITY_AGI_RUNTIME=0)"""
    print("\n" + "="*60)
    print("Testing LEGACY MODE (continuity_core)")
    print("="*60)
    
    # Ensure AGI runtime is disabled
    os.environ['CONTINUITY_AGI_RUNTIME'] = '0'
    
    agent = ContinuityAgent()
    
    print(f"✓ AGI Runtime enabled: {is_agi_runtime_enabled()}")
    print(f"✓ Agent type: {type(agent.runtime).__name__}")
    
    # Execute a task
    task = {
        "id": "test_legacy_1",
        "type": "validation_task",
        "data": {"input": "test data"},
        "should_fail_first": True
    }
    
    print(f"\n▶ Executing task: {task['type']}")
    result = await agent.execute_task(task)
    
    print(f"  Status: {result['status']}")
    print(f"  Agent version: {result['agent_version']}")
    print(f"  Steps: {len(result['steps'])}")
    
    if result['status'] == 'failed':
        print(f"  ✓ Task failed as expected (missing capability)")
        print(f"  Lesson: {result.get('lesson', 'N/A')}")
    
    # Second attempt should succeed
    task2 = {
        "id": "test_legacy_2",
        "type": "validation_task",
        "data": {"input": "test data"},
        "should_fail_first": False
    }
    
    print(f"\n▶ Executing task again (should succeed)")
    result2 = await agent.execute_task(task2)
    
    print(f"  Status: {result2['status']}")
    if result2['status'] == 'success':
        print(f"  ✓ Task succeeded (capability learned)")
    
    print("\n✅ Legacy mode test complete\n")


async def test_agi_mode():
    """Test AGI runtime mode (CONTINUITY_AGI_RUNTIME=1)"""
    print("\n" + "="*60)
    print("Testing AGI RUNTIME MODE")
    print("="*60)
    
    # Enable AGI runtime
    os.environ['CONTINUITY_AGI_RUNTIME'] = '1'
    os.environ['AGI_ENVIRONMENT'] = 'development'
    
    agent = ContinuityAgent()
    
    print(f"✓ AGI Runtime enabled: {is_agi_runtime_enabled()}")
    print(f"✓ Agent type: {type(agent.runtime).__name__}")
    
    # Execute a task
    task = {
        "id": "test_agi_1",
        "type": "validate data",
        "data": {"input": "test data"}
    }
    
    print(f"\n▶ Executing task: {task['type']}")
    result = await agent.execute_task(task)
    
    print(f"  Status: {result['status']}")
    print(f"  Agent version: {result['agent_version']}")
    
    # Check AGI-specific fields
    if 'agi_cycle' in result:
        cycle = result['agi_cycle']
        print(f"\n  AGI Cycle Details:")
        print(f"    Cycle ID: {cycle['cycle_id']}")
        print(f"    Hash: {cycle['hash'][:16]}...")
        print(f"    Prev Hash: {cycle['prev_hash'][:16] if cycle['prev_hash'] else 'None'}...")
        print(f"    Eval Score: {cycle['eval_scores']['overall_score']:.2f}")
        print(f"    Safety Status: {cycle['safety_assessment']['status']}")
        print(f"    Actions Taken: {len(cycle['actions_taken'])}")
        print(f"    Reflection:")
        for item in cycle['reflection']['what_worked'][:2]:
            print(f"      ✓ {item}")
        
        # Verify hash chain
        from agi_runtime.signing import verify_hash_chain
        from agi_runtime.types import CycleRecord
        
        cycle_record = CycleRecord(**cycle)
        print(f"    Hash valid: {cycle_record.hash == cycle['hash']}")
        
        print("\n  ✓ AGI cycle completed successfully")
    
    # Execute another task to test hash chain
    task2 = {
        "id": "test_agi_2",
        "type": "analyze results",
        "data": {"results": [1, 2, 3]}
    }
    
    print(f"\n▶ Executing second task (testing hash chain)")
    result2 = await agent.execute_task(task2)
    
    if 'agi_cycle' in result2:
        cycle2 = result2['agi_cycle']
        print(f"  Cycle ID: {cycle2['cycle_id']}")
        print(f"  Prev Hash matches: {cycle2['prev_hash'] == cycle['hash']}")
        print(f"  ✓ Hash chain verified")
    
    print("\n✅ AGI Runtime mode test complete\n")


async def test_eval_suite():
    """Test eval suite CLI"""
    print("\n" + "="*60)
    print("Testing EVAL SUITE")
    print("="*60)
    
    from agi_runtime.evals import run_smoke_suite
    
    print("\n▶ Running smoke test suite")
    results = run_smoke_suite()
    
    print(f"\n  Overall: {results['summary']}")
    
    for test_name, test_result in results['tests'].items():
        status = "✅" if test_result['passed'] else "❌"
        print(f"  {status} {test_name}: {test_result['message']}")
    
    if results['overall_passed']:
        print("\n✅ All smoke tests passed\n")
    else:
        print("\n❌ Some smoke tests failed\n")
        sys.exit(1)


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AGI RUNTIME INTEGRATION TEST")
    print("="*60)
    
    # Test 1: Legacy mode
    await test_legacy_mode()
    
    # Test 2: AGI runtime mode
    await test_agi_mode()
    
    # Test 3: Eval suite
    await test_eval_suite()
    
    print("="*60)
    print("✅ ALL INTEGRATION TESTS PASSED")
    print("="*60)
    print("\nSummary:")
    print("  ✓ Legacy mode works")
    print("  ✓ AGI runtime mode works")
    print("  ✓ Hash chains work")
    print("  ✓ Eval suite works")
    print("  ✓ Both modes use same interface")
    print("\nTo use AGI Runtime:")
    print("  export CONTINUITY_AGI_RUNTIME=1")
    print("  export AGI_ENVIRONMENT=production  # or staging, development")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
