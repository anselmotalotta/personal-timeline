#!/bin/bash

# Personal Timeline Teardown Script
# Safely stops all running services

echo "=========================================="
echo "Personal Timeline - Service Teardown"
echo "=========================================="
echo ""

# Function to check if a process is running
check_process() {
    ps aux | grep -E "$1" | grep -v grep > /dev/null 2>&1
    return $?
}

# Stop Frontend (React)
echo "1. Checking for React frontend..."
if check_process "react-scripts"; then
    echo "   Found React frontend, stopping..."
    pkill -f "react-scripts"
    sleep 2
    if check_process "react-scripts"; then
        echo "   ⚠️  Process still running, forcing shutdown..."
        pkill -9 -f "react-scripts"
    fi
    echo "   ✅ Frontend stopped"
else
    echo "   ℹ️  Frontend not running"
fi

echo ""

# Stop QA Server
echo "2. Checking for QA server..."
if check_process "src.qa.server"; then
    echo "   Found QA server, stopping..."
    pkill -f "src.qa.server"
    sleep 2
    if check_process "src.qa.server"; then
        echo "   ⚠️  Process still running, forcing shutdown..."
        pkill -9 -f "src.qa.server"
    fi
    echo "   ✅ QA server stopped"
else
    echo "   ℹ️  QA server not running"
fi

echo ""
echo "=========================================="
echo "Verifying shutdown..."
echo "=========================================="
echo ""

# Verify everything is stopped
if check_process "react-scripts" || check_process "src.qa.server"; then
    echo "⚠️  Warning: Some processes may still be running:"
    ps aux | grep -E "react-scripts|src.qa.server" | grep -v grep
    echo ""
    echo "Run this to see PIDs: ps aux | grep -E 'react-scripts|src.qa.server' | grep -v grep"
    echo "Then manually kill with: kill -9 <PID>"
else
    echo "✅ All services stopped successfully!"
fi

echo ""
echo "=========================================="
echo "Data Status"
echo "=========================================="
echo ""
echo "Your data is preserved in:"
echo "  📁 /workspace/MyData/"
echo "  📁 /workspace/MyData/app_data/"
echo ""
echo "Database location:"
echo "  🗄️  /workspace/MyData/app_data/raw_data.db"
echo ""
echo "To restart services, see CURRENT_SETUP.md or SETUP_COMPLETE.md"
echo ""
