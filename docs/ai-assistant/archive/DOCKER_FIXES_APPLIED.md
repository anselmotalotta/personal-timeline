# Docker Fixes Applied

## Issues Found & Fixed

### Issue 1: Frontend Not Starting
**Error**: `Could not find a required file. Name: index.html. Searched in: /app/public`

**Root Cause**: 
- Volume mount `./src/frontend:/app` was overwriting the entire `/app` directory
- This removed `node_modules` and `public` folders that were created during Docker build
- Frontend couldn't find index.html because public folder was gone

**Fix Applied** (`docker-compose.yml`):
```yaml
# BEFORE (BROKEN):
volumes:
  - ./src/frontend:/app              # ❌ Overwrites everything!
  - ./public:/app/public
  - ./src/common:/app/src/common
  - ./src/ingest:/app/src/ingest
  - ./src/qa:/app/src/qa
  - ./MyData:/app/MyData

# AFTER (FIXED):
volumes:
  # Mount only source files for hot reload, preserve node_modules and public
  - ./src/frontend/src:/app/src      # ✅ Only mount src directory
  - ./src/frontend/package.json:/app/package.json
  - ./MyData:/app/MyData
```

**Why This Works**:
- Preserves `node_modules` installed during build
- Preserves `public` folder with index.html and symlinks
- Still allows hot reload for React source code changes
- Adds `WDS_SOCKET_PORT` environment variable for proper webpack dev server connection

---

### Issue 2: Backend Can't Find Facebook Data
**Error**: 
```
Using path: /workspace/MyData/facebook
All json files in path: None
TypeError: 'NoneType' object is not iterable
```

**Root Cause**:
- Configuration file had hardcoded absolute path: `/workspace/MyData/facebook`
- Inside Docker container, the path should be relative to the working directory
- Volume mounts: `./MyData:/app/MyData` (host → container)
- Container working directory: `/app`
- So the path inside container should be: `MyData/facebook` (relative) or `/app/MyData/facebook` (absolute)

**Fix Applied** (`src/common/bootstrap/data_source.json`):
```json
// BEFORE (BROKEN):
{
  "id": 9,
  "source_name": "FacebookPosts",
  "entry_type": "photo",
  "configs": {
    "input_directory": "/workspace/MyData/facebook",  // ❌ Wrong for Docker
    ...
  }
}

// AFTER (FIXED):
{
  "id": 9,
  "source_name": "FacebookPosts",
  "entry_type": "photo",
  "configs": {
    "input_directory": "MyData/facebook",  // ✅ Works for both Docker and non-Docker
    ...
  }
}
```

**Why This Works**:
- Relative path works in Docker (resolves to `/app/MyData/facebook`)
- Also works in non-Docker setup (resolves to `/workspace/personal-timeline/MyData/facebook`)
- The working directory in both environments makes this path valid

---

## How to Apply These Fixes

### Option 1: Quick Restart (Recommended)
```bash
cd /workspace/personal-timeline

# Stop, rebuild, and restart
docker compose down
docker compose up -d --build

# Watch logs
docker compose logs -f
```

### Option 2: Use the Script
```bash
cd /workspace/personal-timeline
bash RESTART_DOCKER.sh
```

---

## Verification Steps

After restarting, verify everything works:

### 1. Check All Containers Are Running
```bash
docker compose ps
```
Expected: All 3 services (frontend, qa, backend) should be "Up"

### 2. Check Frontend
```bash
# Check logs
docker compose logs frontend --tail 20

# Should see:
# "webpack compiled successfully"
# "Compiled successfully!"
```

**Access**: http://localhost:52692

### 3. Check Backend
```bash
# Check logs
docker compose logs backend --tail 30

# Should see:
# Data import completed
# Export completed
# No "TypeError: 'NoneType' object is not iterable"
```

### 4. Check QA Server
```bash
# Check logs
docker compose logs qa --tail 20

# Should see:
# "Running on http://..."
```

**Test**: http://localhost:57485/test (should return "okay")

### 5. Verify Data Access
```bash
# Check frontend can see MyData
docker compose exec frontend ls -la /app/MyData/app_data/

# Check symlinks
docker compose exec frontend ls -la /app/public/digital_data/

# Check backend can see Facebook data  
docker compose exec backend ls -la /app/MyData/facebook/posts/
```

---

## What to Expect

After these fixes:

✅ **Frontend**: 
- Should start successfully
- Accessible at http://localhost:52692
- Should display your 2 Facebook photos

✅ **Backend**:
- Should find Facebook data
- Should complete ingestion without errors
- Should generate JSON files in `/app/MyData/app_data/`

✅ **QA Server**:
- Should start and respond to requests
- Accessible at http://localhost:57485/test

---

## If Issues Persist

### Frontend Still Not Working
```bash
# Check if node_modules exists
docker compose exec frontend ls -la /app/node_modules | head

# Check if public folder exists
docker compose exec frontend ls -la /app/public

# Rebuild without cache
docker compose build --no-cache frontend
docker compose up -d frontend
```

### Backend Still Can't Find Data
```bash
# Verify volume mount
docker compose exec backend ls -la /app/MyData/facebook/posts/

# Check working directory
docker compose exec backend pwd

# Verify the data exists on host
ls -la ./MyData/facebook/posts/
```

---

## Updated Documentation

These fixes are now documented in:
- `DOCKER_SETUP.md` - Updated with correct volume mount patterns
- `DOCKER_FIXES_APPLIED.md` - This file (detailed explanation)
- `RESTART_DOCKER.sh` - Quick restart script
- `DEBUG_DOCKER.sh` - Debugging helper script

---

## Summary

Two critical issues fixed:
1. ✅ Frontend volume mount - now preserves build artifacts
2. ✅ Backend data path - now uses relative path

Both issues stemmed from differences between the development environment (`/workspace`) and the Docker environment (`/app`). The fixes make the configuration work in both environments.
