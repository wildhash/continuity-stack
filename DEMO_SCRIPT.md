# Continuity Stack Demo Script

**Duration:** 2-4 minutes  
**Demo Type:** Interactive / Automated  
**Objective:** Showcase self-reflecting AI agent that learns from failures

---

## Pre-Demo Setup

1. **Ensure services are running:**
   ```bash
   docker compose up -d
   # OR
   ./start.sh
   ```

2. **Verify services:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Neo4j Browser: http://localhost:7474

---

## Demo Flow (2-4 Minutes)

### Opening (30 seconds)

**Say:**
> "I'm going to show you a self-evolving AI agent that learns from its mistakes. This isn't just error logging—it's a complete fail→reflect→learn→succeed cycle powered by a knowledge graph."

**Show:** Navigate to http://localhost:3000

---

### Part 1: The Failure (45 seconds)

**Do:** Click on the "Demo Scenario" tab

**Say:**
> "Watch what happens when we ask the agent to validate a data schema—something it's never done before."

**Do:** Click "Run Demo Scenario" button

**Point out on screen:**
- ❌ First execution fails
- "Missing capability: handle_validation_task"

**Say:**
> "The agent doesn't just crash—it reflects on why it failed."

---

### Part 2: The Reflection & Learning (60 seconds)

**Point out the reflection section showing:**
- **Lesson Learned:** "Input validation against schemas is required before processing data"
- **Strategy:** "Implement schema validation checks at the beginning of task execution"
- **Capability Gained:** `handle_validation_task`
- **Agent Version:** Upgraded from 1.0.0 → 1.0.1

**Say:**
> "The agent just:
> 1. Analyzed its failure
> 2. Extracted a reusable lesson
> 3. Gained a new capability
> 4. Incremented its version number
> 5. Stored everything in both MemMachine memory AND a Neo4j knowledge graph"

---

### Part 3: The Success (45 seconds)

**Point out second execution:**
- ✅ Task succeeds
- Shows "Using capability: handle_validation_task"
- Cites recalled knowledge: "Lesson L-123 from memory..."

**Say:**
> "Same task, second try—now it succeeds. And notice: it explicitly cites the lesson it learned. This isn't magic—it's measurable, auditable learning."

---

### Part 4: The Knowledge Graph (60 seconds)

**Do:** Click "Profile & Timeline" tab

**Show:**
- Agent version evolution (1.0.0 → 1.0.1)
- Timeline of events (tasks, reflections, lessons)
- Capabilities gained over time

**Do:** Open http://localhost:7474 in another tab

**Run this Cypher query:**
```cypher
MATCH (a:AgentVersion)-[:LEARNED]->(l:Lesson)
RETURN a.version, collect(l.content) as lessons
```

**Say:**
> "Every decision, outcome, and lesson is stored as a graph. You can query:
> - Which lessons came from which failures?
> - What capabilities did each agent version have?
> - Patterns of recurring failures
> 
> This makes the agent's learning process fully transparent and analyzable."

---

### Closing (30 seconds)

**Do:** Go to http://localhost:8000/docs

**Say:**
> "Everything is accessible via clean REST APIs. You can:
> - `/api/tasks/execute` - Run any task
> - `/api/graph/insights` - Get learning analytics
> - `/api/memory/search` - Query the agent's memory
> - `/api/agent/status` - See current capabilities
> 
> This is a production-ready pattern for building AI agents that actually evolve, not just hallucinate."

---

## Key Talking Points

✅ **Self-Reflection:** Agent analyzes its own failures  
✅ **Persistent Memory:** MemMachine stores lessons across restarts  
✅ **Knowledge Graph:** Neo4j tracks cause-effect relationships  
✅ **Versioning:** Each learning event increments agent version  
✅ **Transparency:** Every decision is auditable and queryable  
✅ **Repeatability:** Run the demo multiple times, same results  

---

## Backup: If Something Fails

### If docker isn't running:
```bash
./start.sh
# Wait 30 seconds for Neo4j to initialize
```

### If you need to reset the demo:
```bash
docker compose down -v
docker compose up -d
# OR
rm -rf memmachine_data neo4j_data
./start.sh
```

### If Neo4j isn't available:
- Demo still works! It falls back to local file storage
- MemMachine and reflection still function
- Just won't have graph visualization

---

## Advanced Demo (If You Have Extra Time)

### Chat Interface Demo

**Do:** Go to "Chat" tab

**Try these commands:**
1. "Execute a validation task"
2. "Show me your status"
3. "What have you learned?"

**Show:** Agent responds contextually based on its learned knowledge

### API Direct Testing

**Do:** Open http://localhost:8000/docs

**Execute:**
1. `POST /api/tasks/execute` with:
   ```json
   {
     "type": "validation_task",
     "data": {"input": "test"},
     "should_fail_first": false
   }
   ```

2. `GET /api/agent/reflections` - See all lessons

3. `GET /api/graph/insights` - Analytics on learning

---

## Questions to Anticipate

**Q: Is it using GPT-4 for reflection?**  
A: It can, but the demo runs in deterministic mode by default. Pattern-based reflection works for predictable scenarios. Add `OPENAI_API_KEY` for LLM-powered reflection.

**Q: How is this different from RAG?**  
A: RAG retrieves context. This agent modifies its own capabilities and version. It's more like CI/CD for agent evolution.

**Q: Can it learn wrong things?**  
A: Yes! That's why every lesson has a confidence score and is stored with full context. You can query and audit the graph to find bad lessons.

**Q: Does it work at scale?**  
A: This is a demo. For production: add Redis caching, PostgreSQL for structured data, WebSockets for real-time, and auth. Architecture is designed to scale.

---

## Post-Demo: Share the Code

**GitHub:** https://github.com/wildhash/continuity-stack

**Key Files to Highlight:**
- `backend/continuity_core.py` - The reflection loop
- `backend/llm_client.py` - LLM abstraction
- `backend/neo4j_client.py` - Graph operations
- `backend/memmachine_client.py` - Memory integration

**License:** MIT - use it, fork it, build on it!
