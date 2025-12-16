#!/bin/bash

# Find and fix port conflicts for Personal Timeline

echo "========================================"
echo "🔍 Checking which processes are using ports..."
echo "========================================"

echo ""
echo "Port 52692 (Frontend):"
sudo lsof -i :52692 || echo "  ✅ Port 52692 is free"

echo ""
echo "Port 57485 (QA API):"
sudo lsof -i :57485 || echo "  ✅ Port 57485 is free"

echo ""
echo "========================================"
echo "🐳 Checking Docker containers..."
echo "========================================"
docker ps -a | grep -E "personal-timeline|52692|57485" || echo "  ✅ No personal-timeline containers found"

echo ""
echo "========================================"
echo "💡 To fix port conflicts, run:"
echo "========================================"
echo ""
echo "Option 1: Kill processes using the ports"
echo "  sudo lsof -i :52692  # Find PID"
echo "  sudo kill -9 <PID>   # Kill the process"
echo ""
echo "Option 2: Use different ports"
echo "  Edit docker-compose.yml and change:"
echo "    52692:3000 → 52693:3000"
echo "    57485:8085 → 57486:8085"
echo ""
echo "Option 3: Find what's already running"
echo "  ps aux | grep -E 'node|react|python.*server'"
echo ""
echo "========================================"
