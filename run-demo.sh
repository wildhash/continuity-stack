#!/bin/bash
# Continuity Stack Demo Runner
# Executes the fail → reflect → learn → succeed cycle

set -e

echo "🎬 Continuity Stack Demo Runner"
echo "================================"
echo ""

# Check if backend is running
echo "Checking services..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend is not running."
    echo "   Starting services with docker compose..."
    docker compose up -d
    echo "   Waiting for services to be ready (30 seconds)..."
    sleep 30
fi

# Check backend health
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend still not responding. Please check logs:"
    echo "   docker compose logs backend"
    exit 1
fi

echo "✅ Backend is running at http://localhost:8000"

# Check frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running at http://localhost:3000"
else
    echo "⚠️  Frontend might not be ready yet"
fi

# Check Neo4j
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo "✅ Neo4j is running at http://localhost:7474"
else
    echo "⚠️  Neo4j might not be available (optional)"
fi

echo ""
echo "Running Demo Scenario..."
echo "========================"
echo ""

# Run the demo scenario
response=$(curl -s -X POST http://localhost:8000/api/demo/run-scenario)

# Pretty print the response
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"

echo ""
echo "✅ Demo scenario completed!"
echo ""
echo "📊 What just happened:"
echo "  1. Agent attempted validation_task WITHOUT capability → FAILED"
echo "  2. Agent REFLECTED on failure and learned a lesson"
echo "  3. Agent GAINED new capability (handle_validation_task)"
echo "  4. Agent VERSION incremented (1.0.0 → 1.0.1)"
echo "  5. Lesson stored in MemMachine + Neo4j graph"
echo "  6. Agent retried task WITH capability → SUCCESS"
echo ""
echo "🌐 Explore the results:"
echo "  • Lifeline UI:   http://localhost:3000"
echo "  • API Docs:      http://localhost:8000/docs"
echo "  • Neo4j Browser: http://localhost:7474"
echo ""
echo "🔍 Try these Cypher queries in Neo4j:"
echo "  MATCH (a:AgentVersion)-[:LEARNED]->(l:Lesson)"
echo "  RETURN a.version, collect(l.content) as lessons"
echo ""
echo "  MATCH (r:Run)-[:MADE_DECISION]->(d:Decision)-[:LED_TO]->(o:Outcome)"
echo "  RETURN r.task_type, d.choice, o.success"
echo ""

