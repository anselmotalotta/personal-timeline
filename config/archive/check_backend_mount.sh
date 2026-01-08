#!/bin/bash

echo "Checking backend container mounts..."
echo ""

echo "1. Is /app/MyData mounted?"
docker compose exec -T backend ls -la /app/ | grep MyData

echo ""
echo "2. Does /app/MyData/facebook exist?"
docker compose exec -T backend ls -la /app/MyData/ 2>&1 | grep -E "(facebook|No such)"

echo ""
echo "3. What's in /app/MyData/facebook?"
docker compose exec -T backend ls -la /app/MyData/facebook/ 2>&1

echo ""
echo "4. What's in /app/MyData/facebook/posts?"
docker compose exec -T backend ls -la /app/MyData/facebook/posts/ 2>&1 | head -10

echo ""
echo "5. Can we find JSON files?"
docker compose exec -T backend find /app/MyData/facebook -name "*.json" -type f 2>&1 | head -5

echo ""
echo "6. What's the working directory?"
docker compose exec -T backend pwd

echo ""
echo "7. Does the relative path work?"
docker compose exec -T backend ls -la MyData/facebook/posts/ 2>&1 | head -5
