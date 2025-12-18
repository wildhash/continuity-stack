#!/bin/bash
# Stop the Continuity Stack

echo "🛑 Stopping Continuity Stack..."
docker-compose down

echo ""
echo "✓ All services stopped"
echo ""
echo "Note: Data is preserved in ./memmachine_data and ./neo4j_data"
echo "To completely remove all data, run: rm -rf memmachine_data neo4j_data neo4j_logs"
