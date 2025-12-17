#!/bin/bash
# Setup and start the Continuity Stack

set -e

echo "🚀 Starting Continuity Stack..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p memmachine_data neo4j_data neo4j_logs
echo "✓ Data directories created"
echo ""

# Start the stack
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check service health
echo ""
echo "🔍 Checking service health..."

# Wait for Neo4j
echo -n "  Waiting for Neo4j..."
for i in {1..30}; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo " ✓"
        break
    fi
    sleep 2
    echo -n "."
done

# Wait for Backend
echo -n "  Waiting for Backend API..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo " ✓"
        break
    fi
    sleep 2
    echo -n "."
done

# Wait for Frontend
echo -n "  Waiting for Frontend..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo " ✓"
        break
    fi
    sleep 2
    echo -n "."
done

echo ""
echo "✅ All services are running!"
echo ""
echo "📊 Access the services:"
echo "  • Lifeline UI:      http://localhost:3000"
echo "  • EchoForge API:    http://localhost:8000"
echo "  • API Docs:         http://localhost:8000/docs"
echo "  • Neo4j Browser:    http://localhost:7474"
echo "    - Username: neo4j"
echo "    - Password: continuity123"
echo ""
echo "🎬 To run the demo scenario, visit http://localhost:3000 and click 'Demo Scenario'"
echo ""
echo "📝 View logs with: docker-compose logs -f [backend|frontend|neo4j]"
echo "🛑 Stop services with: docker-compose down"
echo ""
