# AGI Runtime Documentation

## Overview

The **AGI Runtime** is a structured, persistent, and measurable agent execution system that implements a complete observe → model → plan → act → verify → reflect → store → evolve cycle.

It extends Continuity's existing agent capabilities with:

- **Structured Cycles**: Every execution is a complete, auditable cycle with defined phases
- **Hash Chaining**: Tamper-evident append-only log with SHA-256 hash chains
- **Safety Gates**: Tool allowlisting, injection detection, and tripwires
- **Evaluation Harness**: Automated scoring and quality metrics
- **Three-Tier Memory**: Episodic, semantic, and procedural memory systems
- **World Model**: Lightweight belief state tracking
- **Deterministic Fallback**: Fully functional without API keys

## Architecture

### The AGI Cycle

Each cycle executes these phases in order:

```
1. OBSERVE    → Gather context, retrieve memories, summarize world state
2. MODEL      → Update world model with new observations
3. PLAN       → Generate plan steps (LLM or deterministic)
4. SAFETY     → Evaluate plan against safety gates
5. ACT        → Execute approved actions
6. VERIFY     → Score cycle quality with eval harness
7. REFLECT    → Analyze what worked/failed, generate lessons
8. STORE      → Write memories (episodic, semantic, procedural)
9. EVOLVE     → Increment agent version if improved
```

### Cycle Record Schema

Each cycle produces a `CycleRecord` containing:

```python
{
  "cycle_id": "cycle_abc123",
  "timestamp_start": "2024-01-01T00:00:00Z",
  "timestamp_end": "2024-01-01T00:00:05Z",
  "agent_version": "1.0.0",
  
  # Goals and context
  "goal_stack": ["Complete task X"],
  "observation": {...},
  
  # World model
  "world_state_before": {...},
  "world_state_after": {...},
  
  # Planning and execution
  "plan": [{tool, args, expected_outcome, rationale}, ...],
  "actions_taken": [{tool, args, output, hash, status}, ...],
  "tool_outputs": {tool: {content, hash}, ...},
  
  # Safety
  "safety_assessment": {
    "status": "allowed|blocked|sandboxed",
    "allowed_tools": [...],
    "blocked_tools": [...],
    "reasons": [...],
    "risk_flags": [...]
  },
  
  # Evaluation
  "eval_scores": {
    "reasoning_score": 0.8,
    "planning_score": 0.7,
    "tool_use_score": 0.9,
    "safety_score": 1.0,
    "overall_score": 0.85
  },
  
  # Reflection
  "reflection": {
    "what_worked": [...],
    "what_failed": [...],
    "next_steps": [...],
    "lessons_learned": [...]
  },
  
  # Memory and artifacts
  "memory_writes": [{memory_type, memory_id, content}, ...],
  "artifacts": ["/path/to/artifact", ...],
  
  # Confidence and uncertainties
  "confidence": 0.8,
  "uncertainties": [...],
  
  # Hash chain
  "prev_hash": "abc123..." or null,
  "hash": "def456..."
}
```

## Storage

### Cycle Logs

Cycles are stored in append-only JSONL format:

```
runs/agi_runtime/YYYY-MM-DD/cycles.jsonl
```

Each line is a complete cycle record.

### Artifacts

Large outputs and generated files are stored separately:

```
runs/agi_runtime/YYYY-MM-DD/artifacts/<cycle_id>/
```

Only hashes and truncated summaries are stored in the cycle record.

## Memory System

### Three Tiers

1. **Episodic Memory**
   - Cycle record references
   - Event sequences
   - Stored: Full cycle context

2. **Semantic Memory**
   - Distilled facts
   - Learned constraints
   - Stable knowledge
   - Stored: Lessons, rules, insights

3. **Procedural Memory**
   - Verified skills/procedures
   - Preconditions + steps
   - Validation notes
   - Stored: Executable playbooks

### Retrieval

```python
# Deterministic keyword + recency scoring (default)
memories = await memory.retrieve_relevant(goal, world_summary, k=8)

# By type
episodic = await memory.retrieve_by_type("episodic", limit=10)
semantic = await memory.retrieve_by_type("semantic", limit=10)
procedural = await memory.retrieve_by_type("procedural", limit=10)

# Specialized queries
successes = await memory.get_recent_successes(limit=5)
constraints = await memory.get_learned_constraints()
skills = await memory.get_available_skills()
```

## Safety System

### Tool Categories

- **SAFE_TOOLS**: Always allowed (read_file, validate_json, etc.)
- **RISKY_TOOLS**: Allowed in dev/staging (write_file, network_request, etc.)
- **BLOCKED_TOOLS**: Never allowed (execute_arbitrary_code, access_secrets, etc.)

### Safety Gates

```python
gate = SafetyGate(environment="production")  # or "staging", "development"

assessment = gate.assess_plan(plan, confidence=0.8)

if assessment.status == "allowed":
    # Execute plan
elif assessment.status == "sandboxed":
    # Requires sandbox rehearsal
elif assessment.status == "blocked":
    # Log violation, don't execute
```

### Tripwires

Automatically detect and block:
- XSS and injection patterns
- Secret-like strings (api_key, password, etc.)
- Unknown tools (not in allowlist)
- Risky tools with low confidence

## Evaluation Harness

### Smoke Suite

Run basic validation tests:

```bash
python -m agi_runtime.evals --suite smoke
```

Tests:
- `reasoning_smoke`: Reflection structure validation
- `planning_smoke`: Constraint-aware planning
- `tool_use_smoke`: Tool execution structure
- `safety_smoke`: Injection blocking

### Cycle Scoring

Each cycle receives scores (0.0 to 1.0):

- **reasoning_score**: Quality of reflection
- **planning_score**: Plan structure and constraint adherence
- **tool_use_score**: Action execution success rate
- **safety_score**: Safety compliance
- **overall_score**: Weighted average

## World Model

Lightweight JSON-first belief state:

```python
WorldModel {
  entities: [{id, type, attributes}, ...]
  relations: [{from, to, type, metadata}, ...]
  constraints: [{type, description, enforced}, ...]
  hypotheses: [{claim, confidence, evidence}, ...]
  timeline: [{timestamp, event, refs}, ...]
}
```

Updated after each cycle based on:
- New observations
- Tool execution results
- Reflection lessons

## Usage

### Enable AGI Runtime

Set environment variable:

```bash
export CONTINUITY_AGI_RUNTIME=1
```

### Run a Cycle

```python
from agi_runtime import AGIRuntime

runtime = AGIRuntime(
    llm_client=None,  # Optional, uses deterministic fallback
    memmachine_client=memmachine,
    neo4j_client=neo4j,
    environment="production"
)

cycle = await runtime.run_cycle(
    goal="validate user input",
    input_data={"user": "data"}
)

print(f"Cycle: {cycle.cycle_id}")
print(f"Score: {cycle.eval_scores.overall_score}")
print(f"Hash: {cycle.hash}")
```

### Verify Hash Chain

```python
from agi_runtime import verify_hash_chain

cycles = persistence.read_cycles(date="2024-01-01")
is_valid = verify_hash_chain(cycles)
print(f"Chain valid: {is_valid}")
```

### Access Cycle Data

```python
# Read recent cycles
cycles = persistence.read_cycles(limit=10)

for cycle in cycles:
    print(f"{cycle.cycle_id}: {cycle.goal_stack[0]}")
    print(f"  Score: {cycle.eval_scores.overall_score}")
    print(f"  Lessons: {cycle.reflection.lessons_learned}")
```

## Deterministic Mode

AGI Runtime works without API keys using rule-based fallbacks:

- **Planner**: Pattern-matching on goal keywords
- **Reflection**: Error pattern analysis
- **Tool Execution**: Simulated outputs
- **Memory Retrieval**: Keyword + recency scoring

Set up:
```bash
unset OPENAI_API_KEY
export CONTINUITY_AGI_RUNTIME=1
```

The system will use deterministic implementations for all LLM-dependent functions.

## Adding a Tool

1. **Define Tool Function**
   ```python
   def my_new_tool(args):
       return {"result": "success"}
   ```

2. **Add to Tool Registry**
   ```python
   # In safety.py
   SAFE_TOOLS.add("my_new_tool")  # or RISKY_TOOLS
   ```

3. **Add Execution Logic**
   ```python
   # In runtime.py _execute_tool_deterministic
   elif tool == "my_new_tool":
       return my_new_tool(args)
   ```

4. **Test Safety**
   ```python
   gate = SafetyGate()
   plan = [PlanStep(tool="my_new_tool", args={}, expected_outcome="")]
   assert gate.assess_plan(plan).status == "allowed"
   ```

## Adding an Eval

Create a new eval function:

```python
# In evals.py

def my_custom_eval() -> Dict[str, Any]:
    """Eval: Description of what this tests"""
    # Run test
    passed = True  # Your test logic
    
    return {
        "passed": passed,
        "name": "my_custom_eval",
        "message": "Test passed" if passed else "Test failed"
    }

# Add to suite
def run_extended_suite():
    results = {
        **run_smoke_suite()["tests"],
        "my_custom_eval": my_custom_eval()
    }
    # ... compute overall
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONTINUITY_AGI_RUNTIME` | `0` | Enable AGI runtime (`1` = on) |
| `AGI_ENVIRONMENT` | `production` | Safety level: `production`, `staging`, `development` |
| `OPENAI_API_KEY` | - | Optional: LLM for planning/reflection |
| `LOCAL_FAKE_MEMORY` | `0` | Use local MemMachine (`1` = local) |

## Integration with Existing Continuity

The AGI Runtime integrates seamlessly:

```python
from agent_integration import ContinuityAgent

# Auto-switches based on CONTINUITY_AGI_RUNTIME
agent = ContinuityAgent(llm_client, memmachine_client, neo4j_client)

# Same API works for both modes
result = await agent.execute_task(task)
```

**Legacy mode** (default): Uses `continuity_core.py`  
**AGI mode** (flag=1): Uses `agi_runtime/runtime.py`

Both return compatible response formats.

## Hash Chain Integrity

Cycles are chained via SHA-256 hashes:

```
Cycle 1: hash = SHA256(cycle_1_data + prev_hash=null)
Cycle 2: hash = SHA256(cycle_2_data + prev_hash=cycle_1_hash)
Cycle 3: hash = SHA256(cycle_3_data + prev_hash=cycle_2_hash)
...
```

Any tampering breaks the chain. Use `verify_hash_chain()` to detect.

## Best Practices

1. **Start in Development Environment**
   ```bash
   export AGI_ENVIRONMENT=development
   ```
   Allows risky tools for testing.

2. **Review Cycle Logs Regularly**
   Check `runs/agi_runtime/` for anomalies.

3. **Monitor Eval Scores**
   Low scores indicate quality issues.

4. **Use Semantic Memory for Constraints**
   Store important rules as semantic memories.

5. **Verify Hash Chains Periodically**
   Ensures audit log integrity.

6. **Keep Artifacts Small**
   Large outputs increase storage; use truncation.

## Troubleshooting

### Cycles Not Persisting

Check write permissions:
```bash
ls -la runs/agi_runtime/
```

### Low Eval Scores

Review reflection:
```python
print(cycle.reflection.what_failed)
print(cycle.reflection.lessons_learned)
```

### Safety Gate Blocking Valid Tools

Adjust environment or add to allowlist:
```python
# In safety.py
SAFE_TOOLS.add("your_tool")
```

### Hash Chain Verification Fails

Check for file corruption or manual edits:
```bash
cat runs/agi_runtime/YYYY-MM-DD/cycles.jsonl | jq .hash
```

## Advanced: Multi-Cycle Execution

For running multiple cycles in sequence:

```python
goals = ["goal_1", "goal_2", "goal_3"]

for goal in goals:
    cycle = await runtime.run_cycle(goal, {})
    
    if cycle.eval_scores.overall_score < 0.5:
        print(f"Low score on {goal}, stopping")
        break
    
    print(f"Completed {goal} with score {cycle.eval_scores.overall_score}")
```

## Future Extensions

Potential enhancements (not yet implemented):

- **Multi-cycle orchestrator**: Goal decomposition
- **Skill compiler**: Procedural memory → executable
- **Constraint solver**: Advanced planning
- **World model inference**: Richer belief updates
- **Tool capability descriptors**: Auto-allowlisting
- **Regression dashboard**: Visual analytics

## See Also

- [README.md](../README.md) - Main project documentation
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [backend/agi_runtime/](../backend/agi_runtime/) - Source code
