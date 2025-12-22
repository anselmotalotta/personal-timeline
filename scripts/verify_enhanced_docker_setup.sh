#!/bin/bash

# Enhanced Docker Setup Verification Script
# Verifies that all services including AI services are running correctly

echo "=================================================="
echo "AI-Augmented Personal Archive - Setup Verification"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local endpoint=$3
    
    echo -n "Checking $service_name on port $port... "
    
    if curl -f -s "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not responding${NC}"
        return 1
    fi
}

# Function to check Docker container status
check_container() {
    local container_name=$1
    
    echo -n "Checking container $container_name... "
    
    if docker ps --format '{{.Names}}' | grep -q "$container_name"; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Function to check volume mounting
check_volume() {
    local container_name=$1
    local mount_path=$2
    
    echo -n "Checking volume mount $mount_path in $container_name... "
    
    if docker exec "$container_name" test -d "$mount_path" 2>/dev/null; then
        echo -e "${GREEN}✓ Mounted${NC}"
        return 0
    else
        echo -e "${RED}✗ Not mounted${NC}"
        return 1
    fi
}

echo ""
echo "1. Checking Docker Containers"
echo "------------------------------"

check_container "personal-timeline-frontend-1" || check_container "frontend"
check_container "personal-timeline-backend-1" || check_container "backend"
check_container "personal-timeline-qa-1" || check_container "qa"
check_container "personal-timeline-ai-services-1" || check_container "ai-services"

echo ""
echo "2. Checking Service Endpoints"
echo "------------------------------"

check_service "Frontend" "52692" "/"
check_service "Backend" "8000" "/"
check_service "QA Service" "57485" "/health"
check_service "AI Services" "8086" "/health"

echo ""
echo "3. Checking Volume Mounts"
echo "-------------------------"

# Try both possible container names
FRONTEND_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E '(frontend|personal-timeline-frontend)' | head -1)
BACKEND_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E '(backend|personal-timeline-backend)' | head -1)
QA_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E '(qa|personal-timeline-qa)' | head -1)
AI_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E '(ai-services|personal-timeline-ai-services)' | head -1)

if [ -n "$FRONTEND_CONTAINER" ]; then
    check_volume "$FRONTEND_CONTAINER" "/app/MyData"
fi

if [ -n "$BACKEND_CONTAINER" ]; then
    check_volume "$BACKEND_CONTAINER" "/app/MyData"
    check_volume "$BACKEND_CONTAINER" "/app/src"
fi

if [ -n "$QA_CONTAINER" ]; then
    check_volume "$QA_CONTAINER" "/app/MyData"
fi

if [ -n "$AI_CONTAINER" ]; then
    check_volume "$AI_CONTAINER" "/app/MyData"
    check_volume "$AI_CONTAINER" "/app/models"
    
    # Check ai-models volume specifically
    echo -n "Checking ai-models volume... "
    if docker volume ls | grep -q "ai-models"; then
        echo -e "${GREEN}✓ ai-models volume exists${NC}"
    else
        echo -e "${YELLOW}⚠ ai-models volume not found${NC}"
    fi
fi

echo ""
echo "4. Checking AI Services Health"
echo "-------------------------------"

AI_HEALTH=$(curl -s http://localhost:8086/health 2>/dev/null)

if [ -n "$AI_HEALTH" ]; then
    echo "AI Services Status:"
    echo "$AI_HEALTH" | python3 -m json.tool 2>/dev/null || echo "$AI_HEALTH"
else
    echo -e "${RED}✗ AI Services not responding${NC}"
fi

echo ""
echo "5. Checking Data Persistence"
echo "-----------------------------"

if [ -d "../MyData/app_data" ]; then
    echo -e "${GREEN}✓ MyData directory exists${NC}"
    
    if [ -f "../MyData/app_data/raw_data.db" ]; then
        echo -e "${GREEN}✓ Database file exists${NC}"
    else
        echo -e "${YELLOW}⚠ Database file not found (may be first run)${NC}"
    fi
else
    echo -e "${RED}✗ MyData directory not found${NC}"
fi

echo ""
echo "6. Checking Environment Configuration"
echo "--------------------------------------"

if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
    
    # Check for key environment variables
    if grep -q "LOCAL_LLM_MODEL" .env; then
        echo -e "${GREEN}✓ AI model configuration found${NC}"
    else
        echo -e "${YELLOW}⚠ AI model configuration not found in .env${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env file not found (using defaults)${NC}"
    echo "  Consider copying .env.example to .env and customizing"
fi

echo ""
echo "=================================================="
echo "Verification Complete"
echo "=================================================="

echo ""
echo "Next Steps:"
echo "1. If all checks passed, access the application at http://localhost:52692"
echo "2. If any checks failed, run: docker-compose logs <service-name>"
echo "3. To restart services: docker-compose restart"
echo "4. To rebuild services: docker-compose up --build -d"
echo ""