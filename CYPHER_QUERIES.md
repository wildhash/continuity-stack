# Cypher Query Reference

This document contains useful Cypher queries for exploring and analyzing the Continuity Stack knowledge graph.

## Basic Queries

### View All Nodes

```cypher
MATCH (n)
RETURN n
LIMIT 100
```

### Count Nodes by Type

```cypher
MATCH (n)
RETURN labels(n) as type, count(n) as count
```

## Identity Queries

### List All Identities

```cypher
MATCH (i:Identity)
RETURN i.id, i.name, i.role, i.created_at
ORDER BY i.created_at DESC
```

### Get Identity with Their Decisions

```cypher
MATCH (i:Identity)-[:MADE]->(d:Decision)
RETURN i.name as identity, 
       collect({
         id: d.id, 
         title: d.title, 
         status: d.status
       }) as decisions
```

### Identity Influence Analysis

```cypher
MATCH (i:Identity)-[:MADE]->(d:Decision)
OPTIONAL MATCH (d)<-[:FROM_DECISION]-(l:Lesson)
RETURN i.name as identity,
       i.role as role,
       count(DISTINCT d) as total_decisions,
       count(DISTINCT l) as lessons_generated,
       collect(DISTINCT d.status) as decision_statuses
ORDER BY total_decisions DESC
```

## Decision Queries

### All Decisions

```cypher
MATCH (d:Decision)
RETURN d.id, d.title, d.description, d.status, d.created_at
ORDER BY d.created_at DESC
```

### Decisions by Status

```cypher
MATCH (d:Decision {status: 'failed'})
RETURN d
ORDER BY d.created_at DESC
```

### Decision with Related Lessons

```cypher
MATCH (d:Decision)
OPTIONAL MATCH (d)<-[:FROM_DECISION]-(l:Lesson)
RETURN d.title as decision,
       d.status as status,
       collect(l.content) as lessons
```

### Decision Impact Analysis

```cypher
MATCH (d:Decision {id: $decision_id})
OPTIONAL MATCH (d)<-[:FROM_DECISION]-(l:Lesson)<-[:LEARNED]-(a:AgentVersion)
RETURN d.title as decision,
       d.description as description,
       collect(DISTINCT a.version) as affected_versions,
       collect(DISTINCT l.content) as lessons_learned
```

## Agent Version Queries

### All Agent Versions

```cypher
MATCH (a:AgentVersion)
RETURN a.version, a.capabilities, a.created_at
ORDER BY a.created_at ASC
```

### Agent Evolution Chain

```cypher
MATCH path = (start:AgentVersion)-[:EVOLVED_TO*]->(end:AgentVersion)
WHERE NOT (start)<-[:EVOLVED_TO]-()
RETURN path
```

### Latest Agent Version with Lessons

```cypher
MATCH (a:AgentVersion)
WHERE NOT (a)-[:EVOLVED_TO]->()
OPTIONAL MATCH (a)-[:LEARNED]->(l:Lesson)
RETURN a.version as version,
       a.capabilities as capabilities,
       collect(l.content) as lessons
```

### Agent Capabilities Over Time

```cypher
MATCH (a:AgentVersion)
RETURN a.version as version,
       a.created_at as created_at,
       size(a.capabilities) as capability_count,
       a.capabilities as capabilities
ORDER BY a.created_at ASC
```

## Lesson Queries

### All Learned Lessons

```cypher
MATCH (a:AgentVersion)-[:LEARNED]->(l:Lesson)
RETURN a.version as agent_version,
       l.content as lesson,
       l.learned_at as learned_at
ORDER BY l.learned_at DESC
```

### Lessons from Specific Decision

```cypher
MATCH (d:Decision {id: $decision_id})<-[:FROM_DECISION]-(l:Lesson)
RETURN l.content as lesson, l.learned_at as when_learned
```

### Most Impactful Lessons

Lessons that affected the most agent versions:

```cypher
MATCH (l:Lesson)<-[:LEARNED]-(a:AgentVersion)
RETURN l.content as lesson,
       count(DISTINCT a) as versions_affected,
       collect(a.version) as versions
ORDER BY versions_affected DESC
```

## Relationship Queries

### All Relationships in the Graph

```cypher
MATCH (n)-[r]->(m)
RETURN type(r) as relationship_type, 
       count(r) as count
```

### Full Decision Flow

```cypher
MATCH (i:Identity)-[:MADE]->(d:Decision)<-[:FROM_DECISION]-(l:Lesson)<-[:LEARNED]-(a:AgentVersion)
RETURN i.name as who_decided,
       d.title as decision,
       l.content as lesson,
       a.version as agent_version
ORDER BY d.created_at DESC
```

## Analysis Queries

### Learning Velocity

How many lessons per agent version:

```cypher
MATCH (a:AgentVersion)-[:LEARNED]->(l:Lesson)
RETURN a.version as version,
       count(l) as lessons_learned,
       a.created_at as version_created
ORDER BY a.created_at ASC
```

### Success Rate Analysis

```cypher
MATCH (d:Decision)
RETURN d.status as status,
       count(d) as count,
       round(100.0 * count(d) / (SELECT count(*) FROM Decision)) as percentage
```

### Agent Growth Visualization

```cypher
MATCH (a:AgentVersion)
OPTIONAL MATCH (a)-[:LEARNED]->(l:Lesson)
RETURN a.version as version,
       a.created_at as created,
       size(a.capabilities) as capabilities,
       count(l) as lessons
ORDER BY a.created_at ASC
```

## Maintenance Queries

### Delete All Data (Use with Caution!)

```cypher
MATCH (n)
DETACH DELETE n
```

### Delete Specific Node Types

```cypher
MATCH (l:Lesson)
DETACH DELETE l
```

### Reset to Initial State

```cypher
// Remove all data
MATCH (n) DETACH DELETE n

// Recreate system identity
CREATE (i:Identity {
  id: 'agent_system',
  name: 'Continuity Agent System',
  role: 'system',
  created_at: datetime(),
  metadata: {type: 'autonomous_agent'}
})

// Create initial agent version
CREATE (a:AgentVersion {
  version: '1.0.0',
  capabilities: ['basic_task_execution', 'error_logging'],
  created_at: datetime()
})
```

## Advanced Pattern Queries

### Find Circular Learning Patterns

```cypher
MATCH path = (d1:Decision)-[:FROM_DECISION]->()-[:LEARNED]->()
             -[:EVOLVED_TO*]->()-[:LEARNED]->()-[:FROM_DECISION]->(d2:Decision)
WHERE d1.title = d2.title
RETURN path
```

### Orphaned Nodes

Find nodes without relationships:

```cypher
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n) as type, count(n) as count
```

### Most Connected Nodes

```cypher
MATCH (n)
WITH n, size((n)--()) as connections
ORDER BY connections DESC
LIMIT 10
RETURN labels(n) as type, 
       n.id as id, 
       connections
```

## Parameter Examples

When using parameters in queries (recommended for security):

```cypher
// In Neo4j Browser or Python driver
:param decision_id => 'decision_123'
:param identity_id => 'agent_system'
:param version => '1.0.0'
```

Then use them in queries with `$parameter_name`.

## Query Tips

1. **Always use LIMIT** when exploring large datasets
2. **Use parameters** ($param) instead of string concatenation
3. **Create indexes** on frequently queried properties
4. **Use EXPLAIN** to analyze query performance
5. **Profile slow queries** with PROFILE keyword

## Creating Indexes

```cypher
CREATE INDEX identity_id IF NOT EXISTS FOR (i:Identity) ON (i.id)
CREATE INDEX decision_id IF NOT EXISTS FOR (d:Decision) ON (d.id)
CREATE INDEX agent_version IF NOT EXISTS FOR (a:AgentVersion) ON (a.version)
```

## Useful Aggregations

### Summary Statistics

```cypher
MATCH (i:Identity)
WITH count(i) as identities
MATCH (d:Decision)
WITH identities, count(d) as decisions
MATCH (a:AgentVersion)
WITH identities, decisions, count(a) as versions
MATCH (l:Lesson)
RETURN {
  identities: identities,
  decisions: decisions,
  agent_versions: versions,
  lessons_learned: count(l)
} as summary
```
