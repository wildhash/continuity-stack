"""
Neo4j Graph Database Integration
Manages Identity, Decisions, and AgentVersions in the knowledge graph
"""
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j database client for Continuity Stack"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._init_constraints()
    
    def close(self):
        """Close the database connection"""
        self.driver.close()
    
    def _init_constraints(self):
        """Initialize database constraints and indexes"""
        with self.driver.session() as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT identity_id IF NOT EXISTS FOR (i:Identity) REQUIRE i.id IS UNIQUE",
                "CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT agent_version_id IF NOT EXISTS FOR (a:AgentVersion) REQUIRE a.version IS UNIQUE",
                "CREATE CONSTRAINT run_id IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE",
                "CREATE CONSTRAINT lesson_id IF NOT EXISTS FOR (l:Lesson) REQUIRE l.id IS UNIQUE",
                "CREATE CONSTRAINT capability_id IF NOT EXISTS FOR (c:Capability) REQUIRE c.id IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint already exists or error: {e}")
    
    # ==================== Identity Management ====================
    
    def create_identity(self, identity_id: str, name: str, role: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create an identity node"""
        query = """
        CREATE (i:Identity {
            id: $id,
            name: $name,
            role: $role,
            created_at: datetime(),
            metadata: $metadata
        })
        RETURN i
        """
        
        with self.driver.session() as session:
            result = session.run(query, 
                id=identity_id,
                name=name,
                role=role,
                metadata=metadata or {}
            )
            record = result.single()
            return dict(record["i"]) if record else {}
    
    def get_identity(self, identity_id: str) -> Optional[Dict[str, Any]]:
        """Get an identity by ID"""
        query = "MATCH (i:Identity {id: $id}) RETURN i"
        
        with self.driver.session() as session:
            result = session.run(query, id=identity_id)
            record = result.single()
            return dict(record["i"]) if record else None
    
    def list_identities(self) -> List[Dict[str, Any]]:
        """List all identities"""
        query = "MATCH (i:Identity) RETURN i ORDER BY i.created_at DESC"
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record["i"]) for record in result]
    
    # ==================== Decision Management ====================
    
    def create_decision(self, decision_id: str, title: str, description: str,
                       made_by: str, status: str = "pending",
                       context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a decision node and link to identity"""
        query = """
        MATCH (i:Identity {id: $made_by})
        CREATE (d:Decision {
            id: $id,
            title: $title,
            description: $description,
            status: $status,
            created_at: datetime(),
            context: $context
        })
        CREATE (i)-[:MADE]->(d)
        RETURN d
        """
        
        with self.driver.session() as session:
            result = session.run(query,
                id=decision_id,
                title=title,
                description=description,
                made_by=made_by,
                status=status,
                context=context or {}
            )
            record = result.single()
            return dict(record["d"]) if record else {}
    
    def update_decision_status(self, decision_id: str, status: str, 
                              outcome: Optional[str] = None) -> Dict[str, Any]:
        """Update decision status and outcome"""
        query = """
        MATCH (d:Decision {id: $id})
        SET d.status = $status,
            d.updated_at = datetime()
        """
        
        if outcome:
            query += ", d.outcome = $outcome"
        
        query += " RETURN d"
        
        with self.driver.session() as session:
            result = session.run(query, id=decision_id, status=status, outcome=outcome)
            record = result.single()
            return dict(record["d"]) if record else {}
    
    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get a decision by ID"""
        query = "MATCH (d:Decision {id: $id}) RETURN d"
        
        with self.driver.session() as session:
            result = session.run(query, id=decision_id)
            record = result.single()
            return dict(record["d"]) if record else None
    
    def list_decisions(self, identity_id: Optional[str] = None, 
                      status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List decisions with optional filters"""
        if identity_id:
            query = """
            MATCH (i:Identity {id: $identity_id})-[:MADE]->(d:Decision)
            """
        else:
            query = "MATCH (d:Decision)"
        
        if status:
            query += " WHERE d.status = $status"
        
        query += " RETURN d ORDER BY d.created_at DESC"
        
        with self.driver.session() as session:
            params = {}
            if identity_id:
                params["identity_id"] = identity_id
            if status:
                params["status"] = status
            
            result = session.run(query, **params)
            return [dict(record["d"]) for record in result]
    
    # ==================== Agent Version Management ====================
    
    def create_agent_version(self, version: str, capabilities: List[str],
                           parent_version: Optional[str] = None) -> Dict[str, Any]:
        """Create an agent version node"""
        query = """
        CREATE (a:AgentVersion {
            version: $version,
            capabilities: $capabilities,
            created_at: datetime()
        })
        """
        
        if parent_version:
            query += """
            WITH a
            MATCH (parent:AgentVersion {version: $parent_version})
            CREATE (parent)-[:EVOLVED_TO]->(a)
            """
        
        query += " RETURN a"
        
        with self.driver.session() as session:
            result = session.run(query,
                version=version,
                capabilities=capabilities,
                parent_version=parent_version
            )
            record = result.single()
            return dict(record["a"]) if record else {}
    
    def add_learned_lesson(self, version: str, lesson: str, 
                          from_decision: Optional[str] = None):
        """Add a learned lesson to an agent version"""
        query = """
        MATCH (a:AgentVersion {version: $version})
        CREATE (l:Lesson {
            content: $lesson,
            learned_at: datetime()
        })
        CREATE (a)-[:LEARNED]->(l)
        """
        
        if from_decision:
            query += """
            WITH l
            MATCH (d:Decision {id: $decision_id})
            CREATE (l)-[:FROM_DECISION]->(d)
            """
        
        with self.driver.session() as session:
            session.run(query,
                version=version,
                lesson=lesson,
                decision_id=from_decision
            )
    
    def get_agent_version(self, version: str) -> Optional[Dict[str, Any]]:
        """Get agent version with learned lessons"""
        query = """
        MATCH (a:AgentVersion {version: $version})
        OPTIONAL MATCH (a)-[:LEARNED]->(l:Lesson)
        RETURN a, collect(l.content) as lessons
        """
        
        with self.driver.session() as session:
            result = session.run(query, version=version)
            record = result.single()
            if record:
                agent_data = dict(record["a"])
                agent_data["lessons"] = record["lessons"]
                return agent_data
            return None
    
    def get_version_evolution(self) -> List[Dict[str, Any]]:
        """Get the evolution chain of agent versions"""
        query = """
        MATCH path = (start:AgentVersion)
        WHERE NOT (start)<-[:EVOLVED_TO]-()
        MATCH (start)-[:EVOLVED_TO*0..]->(version:AgentVersion)
        RETURN version
        ORDER BY version.created_at ASC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record["version"]) for record in result]
    
    # ==================== Graph Analysis Queries ====================
    
    def get_decision_impact_analysis(self, decision_id: str) -> Dict[str, Any]:
        """Analyze the impact of a decision on agent evolution"""
        query = """
        MATCH (d:Decision {id: $decision_id})
        OPTIONAL MATCH (d)<-[:FROM_DECISION]-(l:Lesson)<-[:LEARNED]-(a:AgentVersion)
        RETURN d, collect(DISTINCT a.version) as affected_versions, 
               collect(DISTINCT l.content) as lessons_learned
        """
        
        with self.driver.session() as session:
            result = session.run(query, decision_id=decision_id)
            record = result.single()
            if record:
                return {
                    "decision": dict(record["d"]),
                    "affected_versions": record["affected_versions"],
                    "lessons_learned": record["lessons_learned"]
                }
            return {}
    
    def get_identity_influence(self, identity_id: str) -> Dict[str, Any]:
        """Get the influence of an identity on the system"""
        query = """
        MATCH (i:Identity {id: $identity_id})-[:MADE]->(d:Decision)
        OPTIONAL MATCH (d)<-[:FROM_DECISION]-(l:Lesson)
        RETURN i, count(DISTINCT d) as decisions_made,
               count(DISTINCT l) as lessons_generated,
               collect(DISTINCT d.status) as decision_statuses
        """
        
        with self.driver.session() as session:
            result = session.run(query, identity_id=identity_id)
            record = result.single()
            if record:
                return {
                    "identity": dict(record["i"]),
                    "decisions_made": record["decisions_made"],
                    "lessons_generated": record["lessons_generated"],
                    "decision_statuses": record["decision_statuses"]
                }
            return {}
    
    # ==================== Run Management ====================
    
    def create_run(self, run_id: str, task_type: str, agent_version: str,
                   started_at: Optional[str] = None, success: bool = False,
                   context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a Run node and link to AgentVersion"""
        query = """
        MATCH (a:AgentVersion {version: $agent_version})
        CREATE (r:Run {
            id: $run_id,
            task_type: $task_type,
            started_at: $started_at,
            success: $success,
            context: $context
        })
        CREATE (a)-[:RAN]->(r)
        RETURN r
        """
        
        with self.driver.session() as session:
            result = session.run(query,
                run_id=run_id,
                task_type=task_type,
                agent_version=agent_version,
                started_at=started_at or datetime.utcnow().isoformat(),
                success=success,
                context=context or {}
            )
            record = result.single()
            return dict(record["r"]) if record else {}
    
    def log_decision_in_run(self, run_id: str, prompt: str, choice: str, rationale: str) -> str:
        """Log a decision made during a run"""
        decision_id = f"decision_{run_id}_{int(datetime.utcnow().timestamp())}"
        
        query = """
        MATCH (r:Run {id: $run_id})
        CREATE (d:Decision {
            id: $decision_id,
            prompt: $prompt,
            choice: $choice,
            rationale: $rationale,
            timestamp: $timestamp
        })
        CREATE (r)-[:MADE_DECISION]->(d)
        RETURN d
        """
        
        with self.driver.session() as session:
            result = session.run(query,
                run_id=run_id,
                decision_id=decision_id,
                prompt=prompt,
                choice=choice,
                rationale=rationale,
                timestamp=datetime.utcnow().isoformat()
            )
            record = result.single()
            return decision_id if record else ""
    
    def log_outcome(self, decision_id: str, success: bool, details: str) -> str:
        """Log the outcome of a decision"""
        outcome_id = f"outcome_{decision_id}"
        
        query = """
        MATCH (d:Decision {id: $decision_id})
        CREATE (o:Outcome {
            id: $outcome_id,
            success: $success,
            details: $details,
            timestamp: $timestamp
        })
        CREATE (d)-[:LED_TO]->(o)
        RETURN o
        """
        
        with self.driver.session() as session:
            result = session.run(query,
                decision_id=decision_id,
                outcome_id=outcome_id,
                success=success,
                details=details,
                timestamp=datetime.utcnow().isoformat()
            )
            record = result.single()
            return outcome_id if record else ""
    
    def create_lesson_from_outcome(self, outcome_id: str, title: str, content: str, confidence: float = 1.0) -> str:
        """Create a Lesson from an Outcome"""
        lesson_id = f"lesson_{int(datetime.utcnow().timestamp())}"
        
        query = """
        MATCH (o:Outcome {id: $outcome_id})
        CREATE (l:Lesson {
            id: $lesson_id,
            title: $title,
            content: $content,
            confidence: $confidence,
            created_at: $timestamp
        })
        CREATE (o)-[:PRODUCED]->(l)
        RETURN l
        """
        
        with self.driver.session() as session:
            result = session.run(query,
                outcome_id=outcome_id,
                lesson_id=lesson_id,
                title=title,
                content=content,
                confidence=confidence,
                timestamp=datetime.utcnow().isoformat()
            )
            record = result.single()
            return lesson_id if record else ""
    
    def add_capability(self, capability_name: str, description: str = "") -> str:
        """Create or get a Capability node"""
        capability_id = f"cap_{capability_name}"
        
        query = """
        MERGE (c:Capability {id: $capability_id})
        ON CREATE SET c.name = $name, c.description = $description, c.created_at = $timestamp
        RETURN c
        """
        
        with self.driver.session() as session:
            result = session.run(query,
                capability_id=capability_id,
                name=capability_name,
                description=description,
                timestamp=datetime.utcnow().isoformat()
            )
            record = result.single()
            return capability_id if record else ""
    
    def agent_gains_capability(self, agent_version: str, capability_name: str):
        """Link an agent version to a capability it gained"""
        capability_id = f"cap_{capability_name}"
        
        query = """
        MATCH (a:AgentVersion {version: $agent_version})
        MERGE (c:Capability {id: $capability_id})
        ON CREATE SET c.name = $capability_name, c.created_at = $timestamp
        MERGE (a)-[:GAINED]->(c)
        """
        
        with self.driver.session() as session:
            session.run(query,
                agent_version=agent_version,
                capability_id=capability_id,
                capability_name=capability_name,
                timestamp=datetime.utcnow().isoformat()
            )
    
    def lesson_updates_capability(self, lesson_id: str, capability_name: str):
        """Link a lesson to the capability it updates"""
        capability_id = f"cap_{capability_name}"
        
        query = """
        MATCH (l:Lesson {id: $lesson_id})
        MERGE (c:Capability {id: $capability_id})
        ON CREATE SET c.name = $capability_name, c.created_at = $timestamp
        MERGE (l)-[:UPDATES]->(c)
        """
        
        with self.driver.session() as session:
            session.run(query,
                lesson_id=lesson_id,
                capability_id=capability_id,
                capability_name=capability_name,
                timestamp=datetime.utcnow().isoformat()
            )
    
    # ==================== Query Methods ====================
    
    def get_recent_lessons(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent lessons learned"""
        query = """
        MATCH (l:Lesson)
        RETURN l
        ORDER BY l.created_at DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record["l"]) for record in result]
    
    def get_lessons_for_task_type(self, task_type: str) -> List[Dict[str, Any]]:
        """Get lessons relevant to a specific task type"""
        query = """
        MATCH (r:Run {task_type: $task_type})<-[:RAN]-(a:AgentVersion)-[:LEARNED]->(l:Lesson)
        RETURN DISTINCT l
        ORDER BY l.created_at DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query, task_type=task_type)
            return [dict(record["l"]) for record in result]
    
    def get_recurring_failure_modes(self) -> List[Dict[str, Any]]:
        """Get recurring failure patterns"""
        query = """
        MATCH (r:Run {success: false})
        WITH r.task_type AS task_type, COUNT(r) AS failure_count
        WHERE failure_count > 1
        RETURN task_type, failure_count
        ORDER BY failure_count DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def get_timeline_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get timeline of all events for UI display"""
        query = """
        MATCH (a:AgentVersion)
        OPTIONAL MATCH (a)-[:RAN]->(r:Run)
        OPTIONAL MATCH (a)-[:LEARNED]->(l:Lesson)
        OPTIONAL MATCH (a)-[:GAINED]->(c:Capability)
        WITH a, r, l, c
        UNWIND [
            {type: 'version', timestamp: a.created_at, data: a},
            {type: 'run', timestamp: r.started_at, data: r},
            {type: 'lesson', timestamp: l.created_at, data: l},
            {type: 'capability', timestamp: c.created_at, data: c}
        ] AS event
        WHERE event.data IS NOT NULL
        RETURN event
        ORDER BY event.timestamp DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record["event"]) for record in result]
    
    def get_graph_insights(self) -> Dict[str, Any]:
        """Get comprehensive graph insights for UI"""
        insights = {
            "top_lessons": self.get_recent_lessons(5),
            "recurring_failures": self.get_recurring_failure_modes(),
            "total_runs": 0,
            "success_rate": 0.0,
            "capabilities_gained": []
        }
        
        # Get run statistics
        with self.driver.session() as session:
            # Total runs and success rate
            result = session.run("""
                MATCH (r:Run)
                RETURN COUNT(r) AS total, SUM(CASE WHEN r.success THEN 1 ELSE 0 END) AS successful
            """)
            record = result.single()
            if record:
                total = record["total"] or 0
                successful = record["successful"] or 0
                insights["total_runs"] = total
                insights["success_rate"] = (successful / total * 100) if total > 0 else 0.0
            
            # Capabilities gained
            result = session.run("""
                MATCH (c:Capability)
                RETURN c.name AS name, c.description AS description
                ORDER BY c.created_at DESC
                LIMIT 10
            """)
            insights["capabilities_gained"] = [dict(record) for record in result]
        
        return insights
