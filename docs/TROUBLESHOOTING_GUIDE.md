

# TROUBLESHOOTING GUIDE

## Current Issues & Solutions

### Issue 1: QA Service Error
**Error**: `"Q&A features unavailable - missing langchain/openai dependencies"`

**Root Cause**: LangChain version incompatibility. The code uses old import patterns.

**Solution Applied**: ✅ Fixed
- Updated `src/qa/qa_engine.py` with fallback imports
- Updated `src/qa/chatgpt_engine.py` with fallback imports
- Code now tries new imports first, falls back to old ones

**Next Steps**: Rebuild QA service:
```bash
docker compose build qa
docker compose up -d qa
```

### Issue 2: Frontend Not Loading
**Symptom**: `http://localhost:52692/` shows nothing

**Possible Causes**:
1. Frontend container not running
2. React build failed
3. Port mapping incorrect
4. Node modules not installed

**Diagnosis Steps**:

```bash
# 1. Check if containers are running
docker compose ps

# 2. Check frontend logs
docker compose logs frontend --tail=50

# 3. Check if React is building
docker compose exec frontend ls -la node_modules/ | head -5

# 4. Check if server is responding
curl -I http://localhost:52692
```

**Quick Fixes**:
```bash
# Restart frontend
docker compose restart frontend

# Rebuild frontend
docker compose build frontend
docker compose up -d frontend

# Check frontend from inside container
docker compose exec frontend curl http://localhost:3000
```

### Issue 3: Backend Data Import Errors
**Errors**: `"NotFound: Data expected in..."`, `"TypeError: 'NoneType' object is not iterable"`

**Root Cause**: Expected data directories are empty. This is NORMAL for fresh setup.

**Solution**: The backend is a batch job that processes data. It expects data in specific directories. You can:
1. Add your own data to `MyData/` directory
2. Use sample data from `sample_data/` directory
3. Ignore these errors - they don't affect frontend/QA services

**To skip data import errors** (optional):
```bash
# Create minimal data structure
mkdir -p MyData/facebook
touch MyData/facebook/dummy.json
```

## Complete Reset & Test

```bash
# 1. Stop everything
docker compose down

# 2. Rebuild with fixes
docker compose build --no-cache qa frontend

# 3. Start services
docker compose up -d

# 4. Check status
docker compose ps

# 5. Test QA service
curl "http://localhost:57485/query?query=test&source=digital&qa=true"

# 6. Test frontend
curl -I http://localhost:52692
```

## Expected Results After Fix

### QA Service (`:57485`)
- Should return a response (not the dependency error)
- May return empty results if no data, but NOT dependency error

### Frontend (`:52692`)
- Should show React loading screen
- May show errors about missing data (expected)

### Backend
- Will show data import errors (expected for fresh setup)
- Does NOT affect frontend/QA functionality

## If Still Having Issues

### Check Docker Logs:
```bash
# All logs
docker compose logs

# Specific service
docker compose logs frontend
docker compose logs qa
docker compose logs backend
```

### Check Ports:
```bash
# What's listening?
netstat -tulpn | grep -E ":(52692|57485)"

# Test from container
docker compose exec frontend curl -v http://qa:8085/query?query=test
```

### Manual Testing:
```bash
# Enter QA container
docker compose exec qa bash

# Inside container, test Python
python3 -c "from qa_engine import QAEngine; print('Import OK')"
python3 -c "from chatgpt_engine import ChatGPTEngine; print('Import OK')"

# Exit container
exit
```

## Summary
The main fix was updating LangChain imports. The frontend should work if the container is running. Backend data errors are expected without actual data files.

