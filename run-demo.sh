#!/bin/bash
# Quick test of the demo scenario via API

echo "🎬 Running Continuity Stack Demo Scenario"
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend is not running. Please run ./start.sh first"
    exit 1
fi

echo "✓ Backend is running"
echo ""
echo "Executing demo scenario..."
echo ""

# Run the demo scenario
response=$(curl -s -X POST http://localhost:8000/api/demo/run-scenario)

# Pretty print the response
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"

echo ""
echo "✅ Demo scenario completed!"
echo ""
echo "View the full experience at: http://localhost:3000"
