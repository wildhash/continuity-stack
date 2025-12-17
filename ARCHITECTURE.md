# Architecture Documentation

## System Overview

Continuity Stack is a three-layer self-evolving agent system that demonstrates machine learning through reflection and knowledge graph integration.

## Layer Architecture

### Layer 1: Lifeline UI (Presentation Layer)

**Technology**: Next.js 14, React, TypeScript, Tailwind CSS

**Components**:
- `ChatInterface.tsx` - Real-time chat with the agent
- `ProfileTimeline.tsx` - Visual timeline of agent activities
- `DemoScenario.tsx` - Automated demo runner

**Responsibilities**:
- User interaction and experience
- Real-time updates and polling
- Visual representation of agent state
- Demo orchestration

**API Communication**: 
- REST API calls to EchoForge via Axios
- Polling for status updates (5-second intervals)
- Error handling and connection status monitoring

### Layer 2: EchoForge API (Business Logic Layer)

**Technology**: FastAPI, Python 3.11, Pydantic

**Core Modules**:

1. **main.py** - FastAPI application
   - REST API endpoints
   - Request/response handling
   - CORS middleware
   - Startup/shutdown events

2. **Integration Points**:
   - Continuity Core (agent logic)
   - MemMachine (persistent memory)
   - Neo4j Client (graph database)

**API Endpoints Categories**:
- Agent & Tasks (`/api/tasks/*`, `/api/agent/*`)
- Memory Management (`/api/memory/*`)
- Decision Tracking (`/api/decisions/*`)
- Identity Management (`/api/identities/*`)
- Graph Analysis (`/api/graph/*`)
- Chat Interface (`/api/chat/*`)
- Demo Scenarios (`/api/demo/*`)

**Responsibilities**:
- Request validation (Pydantic models)
- Business logic orchestration
- Data persistence coordination
- Error handling and logging
- State management

### Layer 3: Continuity Core (Agent Intelligence Layer)

**Technology**: Pure Python, async/await

**Core Components**:

1. **continuity_core.py** - Self-reflecting agent
   - Task execution
   - Failure detection
   - Reflection analysis
   - Learning mechanism
   - Capability management
   - Version tracking

2. **Key Classes**:
   - `ContinuityCore` - Main agent system
   - `Reflection` - Failure analysis
   - `AgentVersion` - Version and capabilities
   - `TaskStatus` - Execution states

**Learning Loop**:
```
Execute Task → Detect Failure → Reflect → Learn Lesson → 
Update Capabilities → Store Knowledge → Retry → Success
```

**Reflection Logic**:
- Error pattern matching
- Lesson generation
- Improvement strategy creation
- Capability acquisition

## Data Storage Systems

### MemMachine (File-Based Persistent Memory)

**Location**: `./memmachine_data/`

**Storage Files**:
- `memories.json` - General memories
- `decisions.json` - Decision records
- `agent_state.json` - Agent state history

**Features**:
- JSON-based storage
- Category filtering
- Text search
- Temporal ordering
- State snapshots

**Use Cases**:
- Quick memory retrieval
- Simple text search
- State history tracking
- Backup and replay

### Neo4j Graph Database

**Technology**: Neo4j 5.13

**Graph Schema**:

```
(Identity)-[:MADE]->(Decision)
(Decision)<-[:FROM_DECISION]-(Lesson)
(Lesson)<-[:LEARNED]-(AgentVersion)
(AgentVersion)-[:EVOLVED_TO]->(AgentVersion)
```

**Node Types**:

1. **Identity**
   - Properties: id, name, role, created_at, metadata
   - Represents: System users and agents

2. **Decision**
   - Properties: id, title, description, status, created_at, context
   - Represents: Decisions made in the system

3. **AgentVersion**
   - Properties: version, capabilities, created_at
   - Represents: Different states of agent evolution

4. **Lesson**
   - Properties: content, learned_at
   - Represents: Learned knowledge

**Relationships**:
- `MADE` - Identity → Decision
- `FROM_DECISION` - Lesson → Decision
- `LEARNED` - AgentVersion → Lesson
- `EVOLVED_TO` - AgentVersion → AgentVersion

**Use Cases**:
- Complex relationship queries
- Impact analysis
- Evolution tracking
- Influence mapping

## Data Flow

### Task Execution Flow

```
User Request (UI)
    ↓
POST /api/tasks/execute (EchoForge)
    ↓
ContinuityCore.execute_task()
    ↓
[Has Capability?]
    ├─ Yes → Execute Successfully
    │           ↓
    │       Store in MemMachine
    │           ↓
    │       Return Success
    │
    └─ No → Fail with Error
                ↓
            Trigger Reflection
                ↓
            Analyze Failure
                ↓
            Generate Lesson
                ↓
            Update Capabilities
                ↓
            Store in MemMachine
                ↓
            Store in Neo4j
                ↓
            Return Failure with Lesson
```

### Demo Scenario Flow

```
1. POST /api/demo/run-scenario
2. Execute validation_task (will fail)
3. Reflect on failure
4. Learn lesson: "Input validation required"
5. Gain capability: handle_validation_task
6. Store lesson in Neo4j graph
7. Retry validation_task (will succeed)
8. Return complete scenario log
```

## Communication Patterns

### Frontend ↔ Backend

**Protocol**: HTTP REST
**Format**: JSON
**Error Handling**: Try-catch with user feedback
**Updates**: Polling (5s interval for timeline)

### Backend ↔ Continuity Core

**Type**: Direct Python function calls
**Pattern**: Async/await
**State**: In-memory with persistence hooks

### Backend ↔ MemMachine

**Type**: File I/O
**Pattern**: Synchronous read/write
**Format**: JSON files
**Locking**: Not implemented (single instance assumed)

### Backend ↔ Neo4j

**Protocol**: Bolt protocol (port 7687)
**Driver**: Official Neo4j Python driver
**Pattern**: Session-based transactions
**Connection**: Connection pooling (driver managed)

## Scalability Considerations

### Current Architecture (Demo Scale)

- Single instance of each component
- File-based memory (MemMachine)
- Direct database connections
- No authentication/authorization
- Polling for updates

### Production Considerations

**For Production Scale**:

1. **API Layer**:
   - Add authentication (JWT tokens)
   - Rate limiting
   - Request caching
   - Load balancing

2. **Data Storage**:
   - Redis for caching
   - PostgreSQL for structured data
   - S3 for MemMachine data
   - Neo4j clustering

3. **Real-time Updates**:
   - WebSocket connections
   - Server-sent events
   - Message queue (RabbitMQ/Kafka)

4. **Monitoring**:
   - Prometheus metrics
   - Grafana dashboards
   - Error tracking (Sentry)
   - Logging (ELK stack)

## Security Architecture

### Current (Demo) Security

- No authentication
- No authorization
- Local network only
- Docker network isolation
- Default credentials

### Production Security Recommendations

1. **Authentication**:
   - OAuth 2.0 / OpenID Connect
   - JWT tokens
   - API keys for service-to-service

2. **Authorization**:
   - Role-based access control (RBAC)
   - Identity-based permissions
   - Graph-level security in Neo4j

3. **Data Security**:
   - Encryption at rest
   - TLS/SSL for all connections
   - Secrets management (Vault)
   - Regular backups

4. **Network Security**:
   - Private networks
   - Firewall rules
   - DDoS protection
   - API gateway

## Extension Points

### Adding New Capabilities

1. Update `ContinuityCore` reflection logic
2. Add capability detection patterns
3. Extend Neo4j schema if needed
4. Add UI components for visualization

### Adding New Data Sources

1. Create new client module
2. Add to EchoForge initialization
3. Create API endpoints
4. Update UI to display data

### Custom Reflection Strategies

1. Extend `Reflection.analyze_failure()`
2. Add pattern matching logic
3. Define new lesson types
4. Update graph schema

## Testing Strategy

### Unit Tests

- Backend: pytest
- Core logic: Async test cases
- MemMachine: File I/O mocking

### Integration Tests

- API endpoints: FastAPI TestClient
- Database: Neo4j test database
- End-to-end scenarios

### Manual Testing

- UI interactions
- Demo scenario
- Graph visualization
- Error conditions

## Deployment Architecture

### Docker Compose (Current)

```
services:
  - neo4j (database)
  - backend (FastAPI)
  - frontend (Next.js)

volumes:
  - neo4j_data
  - memmachine_data

networks:
  - default (bridge)
```

### Kubernetes (Future)

- Deployment manifests
- Service definitions
- Persistent volumes
- Ingress controller
- Horizontal pod autoscaling

## Performance Characteristics

### Expected Response Times (Local)

- Chat message: < 200ms
- Task execution: < 100ms
- Graph query: < 50ms
- MemMachine read: < 10ms
- Demo scenario: ~2-3 seconds

### Bottlenecks

1. **Neo4j queries** - Complex graph traversals
2. **File I/O** - MemMachine JSON parsing
3. **Frontend polling** - Network overhead
4. **No caching** - Repeated queries

### Optimization Opportunities

1. Add Redis caching
2. Implement query result caching
3. Use WebSockets for real-time updates
4. Batch Neo4j operations
5. Add database indexes
