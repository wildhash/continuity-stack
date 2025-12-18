"""
EchoForge API - Team Memory & Decision Layer
FastAPI backend integrating Continuity Core, MemMachine, and Neo4j
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
import os
import logging

from continuity_core import ContinuityCore, TaskStatus
from memmachine import MemMachine
from neo4j_client import Neo4jClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
continuity_core = ContinuityCore()
memmachine = MemMachine(storage_path=os.getenv("MEMMACHINE_PATH", "./memmachine_data"))

# Neo4j connection (will be initialized in lifespan)
neo4j_client: Optional[Neo4jClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    global neo4j_client
    
    # Startup
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "continuity123")
    
    try:
        neo4j_client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_password)
        logger.info("Connected to Neo4j database")
        
        # Initialize seed data
        await initialize_seed_data()
        
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        logger.warning("Running without Neo4j support")
    
    yield
    
    # Shutdown
    if neo4j_client:
        neo4j_client.close()
        logger.info("Closed Neo4j connection")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="EchoForge API",
    description="Team Memory & Decision Layer for Continuity Stack",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================

class TaskRequest(BaseModel):
    type: str
    data: Dict[str, Any] = {}
    should_fail_first: bool = True


class TaskResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    timestamp: str
    agent_version: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MemoryRequest(BaseModel):
    content: str
    category: str = "general"
    description: Optional[str] = None


class DecisionRequest(BaseModel):
    title: str
    description: str
    made_by: str
    context: Dict[str, Any] = {}


class IdentityRequest(BaseModel):
    id: str
    name: str
    role: str
    metadata: Dict[str, Any] = {}


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}


# ==================== Health & Info Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "EchoForge API",
        "version": "1.0.0",
        "description": "Team Memory & Decision Layer for Continuity Stack",
        "status": "operational",
        "components": {
            "continuity_core": "active",
            "memmachine": "active",
            "neo4j": "active" if neo4j_client else "unavailable"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "neo4j_connected": neo4j_client is not None
    }


# ==================== Agent & Task Endpoints ====================

@app.post("/api/tasks/execute", response_model=TaskResponse)
async def execute_task(task: TaskRequest):
    """Execute a task through the Continuity Core"""
    try:
        result = await continuity_core.execute_task(task.dict())
        
        # Store task result in memory
        memmachine.store_memory({
            "category": "task_execution",
            "content": f"Task {result['task_id']}: {result['status']}",
            "description": f"Executed {task.type} task",
            "task_result": result
        })
        
        # Store in Neo4j if failed (for reflection tracking)
        if neo4j_client and result["status"] == TaskStatus.FAILED.value:
            decision_id = f"decision_{result['task_id']}"
            neo4j_client.create_decision(
                decision_id=decision_id,
                title=f"Task Failure: {task.type}",
                description=result.get("error", "Unknown error"),
                made_by="agent_system",
                status="failed",
                context={"task_id": result["task_id"], "task_type": task.type}
            )
        
        return TaskResponse(**result)
        
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/status")
async def get_agent_status():
    """Get current agent status and capabilities"""
    capabilities = continuity_core.get_current_capabilities()
    lessons = continuity_core.get_learned_lessons()
    
    status = {
        "version": continuity_core.current_version,
        "capabilities": capabilities,
        "learned_lessons": lessons,
        "total_tasks": len(continuity_core.task_history),
        "total_reflections": len(continuity_core.reflections)
    }
    
    # Update agent state in MemMachine
    memmachine.update_agent_state(status)
    
    return status


@app.get("/api/agent/history")
async def get_agent_history():
    """Get agent task history"""
    return {
        "tasks": continuity_core.get_task_history(),
        "reflections": continuity_core.get_reflections()
    }


@app.get("/api/agent/reflections")
async def get_reflections():
    """Get all agent reflections"""
    return {
        "reflections": continuity_core.get_reflections()
    }


# ==================== Memory Endpoints ====================

@app.post("/api/memory/store")
async def store_memory(memory: MemoryRequest):
    """Store a memory in MemMachine"""
    try:
        memory_id = memmachine.store_memory(memory.dict())
        return {
            "memory_id": memory_id,
            "status": "stored",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/list")
async def list_memories(limit: int = 50, category: Optional[str] = None):
    """List memories with optional filtering"""
    memories = memmachine.get_memories(limit=limit, category=category)
    return {"memories": memories, "count": len(memories)}


@app.get("/api/memory/search")
async def search_memories(query: str):
    """Search memories by text query"""
    results = memmachine.search_memories(query)
    return {"results": results, "count": len(results)}


# ==================== Decision Endpoints ====================

@app.post("/api/decisions/create")
async def create_decision(decision: DecisionRequest):
    """Create a decision record in Neo4j"""
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        # Ensure identity exists
        identity = neo4j_client.get_identity(decision.made_by)
        if not identity:
            neo4j_client.create_identity(
                identity_id=decision.made_by,
                name=decision.made_by,
                role="user"
            )
        
        decision_id = f"decision_{datetime.utcnow().timestamp()}"
        result = neo4j_client.create_decision(
            decision_id=decision_id,
            title=decision.title,
            description=decision.description,
            made_by=decision.made_by,
            context=decision.context
        )
        
        # Also store in MemMachine
        memmachine.store_decision({
            "decision_id": decision_id,
            "title": decision.title,
            "description": decision.description,
            "made_by": decision.made_by,
            "status": "pending"
        })
        
        return {"decision_id": decision_id, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decisions/list")
async def list_decisions(identity_id: Optional[str] = None, status_filter: Optional[str] = None):
    """List decisions from Neo4j"""
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        decisions = neo4j_client.list_decisions(identity_id=identity_id, status=status_filter)
        return {"decisions": decisions, "count": len(decisions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/decisions/{decision_id}/status")
async def update_decision_status(decision_id: str, status: str, outcome: Optional[str] = None):
    """Update decision status"""
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        result = neo4j_client.update_decision_status(decision_id, status, outcome)
        return {"decision_id": decision_id, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Identity Endpoints ====================

@app.post("/api/identities/create")
async def create_identity(identity: IdentityRequest):
    """Create an identity in Neo4j"""
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        result = neo4j_client.create_identity(
            identity_id=identity.id,
            name=identity.name,
            role=identity.role,
            metadata=identity.metadata
        )
        return {"identity_id": identity.id, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/identities/list")
async def list_identities():
    """List all identities"""
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        identities = neo4j_client.list_identities()
        return {"identities": identities, "count": len(identities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/identities/{identity_id}/influence")
async def get_identity_influence(identity_id: str):
    """Get identity influence analysis"""
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        influence = neo4j_client.get_identity_influence(identity_id)
        return influence
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Graph Analysis Endpoints ====================

@app.get("/api/graph/version-evolution")
async def get_version_evolution():
    """Get agent version evolution chain"""
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        evolution = neo4j_client.get_version_evolution()
        return {"evolution": evolution}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/decision-impact/{decision_id}")
async def get_decision_impact(decision_id: str):
    """Get decision impact analysis"""
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        impact = neo4j_client.get_decision_impact_analysis(decision_id)
        return impact
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Chat Interface Endpoints ====================

@app.post("/api/chat/send")
async def send_chat_message(chat: ChatRequest):
    """Send a chat message and get agent response"""
    user_message = chat.message.lower()
    
    # Simple chat logic based on keywords
    if "execute" in user_message or "run task" in user_message:
        # Extract task type from message
        task_type = "validation_task" if "validation" in user_message else "generic_task"
        
        task = TaskRequest(type=task_type, data={"message": chat.message})
        result = await execute_task(task)
        
        if result.status == "failed":
            response = f"Task failed: {result.error}. I will reflect on this and learn."
        else:
            response = f"Task completed successfully! {result.output.get('message', '')}"
    
    elif "status" in user_message or "capabilities" in user_message:
        status = await get_agent_status()
        response = f"I'm version {status['version']} with {len(status['capabilities'])} capabilities. I've learned {len(status['learned_lessons'])} lessons so far."
    
    elif "lessons" in user_message or "learned" in user_message:
        lessons = continuity_core.get_learned_lessons()
        if lessons:
            response = f"I've learned {len(lessons)} lessons:\n" + "\n".join(f"- {l}" for l in lessons)
        else:
            response = "I haven't learned any lessons yet."
    
    elif "history" in user_message:
        history = await get_agent_history()
        response = f"I've executed {len(history['tasks'])} tasks and made {len(history['reflections'])} reflections."
    
    else:
        response = "I'm an evolving AI agent. Ask me to execute tasks, check my status, or review what I've learned!"
    
    # Store chat interaction in memory
    memmachine.store_memory({
        "category": "chat",
        "content": f"User: {chat.message}\nAgent: {response}",
        "description": "Chat interaction"
    })
    
    return {
        "response": response,
        "timestamp": datetime.utcnow().isoformat(),
        "agent_version": continuity_core.current_version
    }


# ==================== Demo Scenario Endpoint ====================

@app.post("/api/demo/run-scenario")
async def run_demo_scenario():
    """Run the complete demo scenario: fail -> reflect -> learn -> succeed"""
    scenario_log = []
    
    try:
        # Step 1: Execute task that will fail
        scenario_log.append("Step 1: Attempting validation_task (will fail)")
        task1 = TaskRequest(type="validation_task", data={"input": "test"}, should_fail_first=True)
        result1 = await execute_task(task1)
        scenario_log.append(f"Result: {result1.status} - {result1.error}")
        
        # Step 2: Check reflections
        scenario_log.append("\nStep 2: Checking reflections")
        reflections = continuity_core.get_reflections()
        if reflections:
            latest_reflection = reflections[-1]
            scenario_log.append(f"Learned: {latest_reflection.get('lesson_learned')}")
            scenario_log.append(f"Strategy: {latest_reflection.get('improvement_strategy')}")
        
        # Step 3: Check updated capabilities
        scenario_log.append("\nStep 3: Updated capabilities")
        capabilities = continuity_core.get_current_capabilities()
        scenario_log.append(f"Capabilities: {', '.join(capabilities)}")
        
        # Step 4: Store lesson in Neo4j
        if neo4j_client and reflections:
            scenario_log.append("\nStep 4: Storing lesson in graph database")
            neo4j_client.create_agent_version(
                version=continuity_core.current_version,
                capabilities=capabilities
            )
            neo4j_client.add_learned_lesson(
                version=continuity_core.current_version,
                lesson=latest_reflection.get('lesson_learned', '')
            )
            scenario_log.append("Lesson stored in Neo4j graph")
        
        # Step 5: Execute same task again (should succeed)
        scenario_log.append("\nStep 5: Retrying validation_task (should succeed)")
        task2 = TaskRequest(type="validation_task", data={"input": "test"}, should_fail_first=False)
        result2 = await execute_task(task2)
        scenario_log.append(f"Result: {result2.status}")
        if result2.output:
            scenario_log.append(f"Output: {result2.output.get('message')}")
        
        return {
            "success": True,
            "scenario_log": scenario_log,
            "final_status": {
                "version": continuity_core.current_version,
                "capabilities": capabilities,
                "lessons_learned": continuity_core.get_learned_lessons()
            }
        }
        
    except Exception as e:
        scenario_log.append(f"\nError: {str(e)}")
        return {
            "success": False,
            "scenario_log": scenario_log,
            "error": str(e)
        }


# ==================== Seed Data Initialization ====================

async def initialize_seed_data():
    """Initialize seed data in Neo4j"""
    if not neo4j_client:
        return
    
    try:
        # Check if data already exists
        identities = neo4j_client.list_identities()
        if identities:
            logger.info("Seed data already exists, skipping initialization")
            return
        
        # Create initial identity
        neo4j_client.create_identity(
            identity_id="agent_system",
            name="Continuity Agent System",
            role="system",
            metadata={"type": "autonomous_agent"}
        )
        
        # Create initial agent version
        neo4j_client.create_agent_version(
            version="1.0.0",
            capabilities=["basic_task_execution", "error_logging"]
        )
        
        logger.info("Seed data initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing seed data: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
