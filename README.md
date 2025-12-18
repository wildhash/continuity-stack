# Continuity Stack

A 3-layer memory-powered agent system demonstrating self-reflection and learning capabilities.

**Lifeline UI** (Next.js) → **EchoForge API** (FastAPI) → **Continuity Core** (Self-evolving agent)

Built with **MemMachine** (persistent memory) + **Neo4j** (knowledge graph) for Identity, Decisions, and Agent Version tracking.

## 🎯 Demo Highlights

This full-stack demo showcases:

1. **Agent fails** on a task it hasn't encountered before
2. **Agent reflects** on the failure and analyzes what went wrong
3. **Agent stores lesson** in both MemMachine and Neo4j graph
4. **Agent updates** its capabilities and knowledge graph
5. **Agent succeeds** when retrying the same task

## 🏗️ Architecture

### Three-Layer System

```
┌─────────────────────────────────────────┐
│         Lifeline UI (Next.js)           │
│  - Chat Interface                       │
│  - Profile Timeline                     │
│  - Demo Scenario Runner                 │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│       EchoForge API (FastAPI)           │
│  - Team Memory Layer                    │
│  - Decision Tracking                    │
│  - Agent State Management               │
└────┬──────────────────────┬─────────────┘
     │                      │
     ▼                      ▼
┌──────────────┐   ┌─────────────────────┐
│  MemMachine  │   │   Continuity Core   │
│  (Persistent │   │  (Self-reflecting   │
│   Memory)    │   │    Agent Loop)      │
└──────────────┘   └──────────┬──────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │   Neo4j Knowledge    │
                   │       Graph          │
                   │  - Identities        │
                   │  - Decisions         │
                   │  - Agent Versions    │
                   │  - Learned Lessons   │
                   └──────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/wildhash/continuity-stack.git
   cd continuity-stack
   ```

2. **Start the entire stack with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

   This will start:
   - Neo4j database (ports 7474, 7687)
   - FastAPI backend (port 8000)
   - Next.js frontend (port 3000)

3. **Access the interfaces:**
   - **Lifeline UI**: http://localhost:3000
   - **EchoForge API Docs**: http://localhost:8000/docs
   - **Neo4j Browser**: http://localhost:7474 (username: `neo4j`, password: `continuity123`)

### Alternative: Local Development

#### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt

# Start Neo4j first (or use docker-compose up neo4j)
# Then run the backend
uvicorn main:app --reload --port 8000
```

#### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

## 📖 Usage Guide

### Running the Demo Scenario

1. Open Lifeline UI at http://localhost:3000
2. Navigate to the **"Demo Scenario"** tab
3. Click **"Run Demo Scenario"**
4. Watch the execution log showing:
   - Initial task failure
   - Reflection and lesson learning
   - Capability acquisition
   - Graph database update
   - Successful retry

### Using the Chat Interface

Try these commands in the chat:

- `"Execute a validation task"` - Run a task that demonstrates learning
- `"Show me your status"` - View agent capabilities and stats
- `"What have you learned?"` - See all learned lessons
- `"Show me your history"` - View task execution history

### Viewing the Profile Timeline

The **Profile & Timeline** tab shows:
- Current agent version and statistics
- Chronological timeline of all events
- Tasks executed (success/failure)
- Reflections and learned lessons
- Acquired capabilities

## 🔌 API Endpoints

### Agent & Tasks

- `POST /api/tasks/execute` - Execute a task through the agent
- `GET /api/agent/status` - Get current agent status and capabilities
- `GET /api/agent/history` - Get task execution history
- `GET /api/agent/reflections` - Get all reflections

### Memory (MemMachine)

- `POST /api/memory/store` - Store a memory
- `GET /api/memory/list` - List memories with filtering
- `GET /api/memory/search` - Search memories by text

### Decisions (Neo4j)

- `POST /api/decisions/create` - Create a decision record
- `GET /api/decisions/list` - List decisions
- `PUT /api/decisions/{id}/status` - Update decision status

### Graph Analysis

- `GET /api/graph/version-evolution` - Get agent evolution chain
- `GET /api/graph/decision-impact/{id}` - Analyze decision impact

### Demo

- `POST /api/demo/run-scenario` - Run the complete demo scenario

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest test_continuity_core.py -v
pytest test_memmachine.py -v
```

### Running All Tests

```bash
cd backend
pytest -v
```

## 🗄️ Data Storage

### MemMachine

File-based persistent storage in `./memmachine_data/`:
- `memories.json` - All stored memories
- `decisions.json` - Decision records
- `agent_state.json` - Agent state history

### Neo4j Graph Database

Graph data stored in `./neo4j_data/` with:

**Node Types:**
- `Identity` - System identities (users, agents)
- `Decision` - Decisions made in the system
- `AgentVersion` - Different versions of the agent
- `Lesson` - Learned lessons

**Relationship Types:**
- `MADE` - Identity made a Decision
- `LEARNED` - AgentVersion learned a Lesson
- `FROM_DECISION` - Lesson came from a Decision
- `EVOLVED_TO` - AgentVersion evolved to another version

## 📊 Key Cypher Queries

### View All Agent Versions and Evolution

```cypher
MATCH (a:AgentVersion)
OPTIONAL MATCH (a)-[:EVOLVED_TO]->(next:AgentVersion)
RETURN a, next
ORDER BY a.created_at
```

### See Lessons Learned

```cypher
MATCH (a:AgentVersion)-[:LEARNED]->(l:Lesson)
RETURN a.version as version, collect(l.content) as lessons
```

### Decision Impact Analysis

```cypher
MATCH (d:Decision)<-[:FROM_DECISION]-(l:Lesson)<-[:LEARNED]-(a:AgentVersion)
RETURN d.title as decision, 
       collect(DISTINCT a.version) as affected_versions,
       collect(l.content) as lessons
```

### Identity Influence

```cypher
MATCH (i:Identity)-[:MADE]->(d:Decision)
OPTIONAL MATCH (d)<-[:FROM_DECISION]-(l:Lesson)
RETURN i.name as identity,
       count(DISTINCT d) as decisions,
       count(DISTINCT l) as lessons_generated
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Neo4j** - Graph database for knowledge representation
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS
- **Axios** - HTTP client

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Neo4j 5.13** - Graph database

## 🔧 Configuration

### Environment Variables

Backend (set in `docker-compose.yml` or `.env`):
```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=continuity123
MEMMACHINE_PATH=./memmachine_data
```

Frontend:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🐛 Troubleshooting

### Neo4j Connection Issues

If you see "Neo4j not available" errors:

1. Check Neo4j is running: `docker-compose ps`
2. Wait for Neo4j to fully start (can take 30-60 seconds)
3. Verify connection at http://localhost:7474

### Backend Not Starting

```bash
# Check logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Frontend Build Issues

```bash
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

## 📝 Seed Data

The system initializes with:
- Default `agent_system` identity
- Initial agent version `1.0.0` with basic capabilities
- Empty knowledge graph ready for learning

## 🎓 Learning Flow Example

```
1. User: "Execute a validation task"
   └─> Agent attempts task without validation capability
       └─> FAILS with "Missing capability: handle_validation_task"

2. Agent reflects on failure
   └─> Analyzes error: validation required
       └─> Learns: "Input validation is required before processing"
           └─> Gains capability: handle_validation_task

3. Agent stores in graph
   └─> Creates Lesson node
       └─> Links to AgentVersion
           └─> Records in MemMachine

4. User: "Execute a validation task" (retry)
   └─> Agent has capability
       └─> SUCCESS ✓
```

## 🤝 Contributing

This is a demonstration project showing self-evolving agent architecture. Feel free to:
- Extend the learning capabilities
- Add more sophisticated reflection logic
- Implement additional graph queries
- Enhance the UI with more visualizations

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built to demonstrate:
- Self-reflecting AI agents
- Knowledge graph reasoning
- Persistent memory systems
- Full-stack AI application architecture
