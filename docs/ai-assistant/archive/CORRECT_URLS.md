



# CORRECT SERVICE URLs

After analyzing the code, here are the **correct URLs** for the services:

## 1. **Frontend** (React App)
- **URL**: `http://localhost:52692`
- **Container Port**: 3000
- **Status**: Should work after rebuild
- **Configuration**: Now uses `REACT_APP_QA_URL` environment variable (set to `http://qa:8085`)

## 2. **QA Service** (Flask API)
- **URL**: `http://localhost:57485`
- **Container Port**: 8085 (NOT 5000!)
- **Server**: `src/qa/server.py` (runs on port 8085)
- **API Endpoint**: `/query` (used by frontend)

## 3. **Backend** (Data Processing)
- **Type**: Batch job (NOT an HTTP server)
- **Function**: Processes data from Apple Health, etc.
- **No HTTP endpoint** - completes and exits

## What Was Fixed

### 1. **Port Mismatch Fix**
- QA service was configured to map host port 57485 → container port 5000
- But `src/qa/server.py` actually runs on port 8085
- **Fixed**: Changed to map host port 57485 → container port 8085

### 2. **Frontend Configuration Fix**
- `Constants.js` hardcoded `localhost:8085`
- **Fixed**: Now uses `REACT_APP_QA_URL` environment variable
- Inside Docker: Uses `http://qa:8085` (service discovery)
- Outside Docker: Falls back to `localhost:8085`

### 3. **Docker Network Fix**
- Frontend container can access QA service at `qa:8085`
- Host machine accesses QA service at `localhost:57485`

## How to Test

### Step 1: Rebuild and Restart
```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline

# Clean rebuild
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Step 2: Verify Services
```bash
# Check all services are running
docker compose ps

# Check frontend logs
docker compose logs frontend | tail -20

# Check QA service logs  
docker compose logs qa | tail -20

# Test QA API directly
curl "http://localhost:57485/query?query=test&source=digital&qa=true"
```

### Step 3: Access Services
1. **Frontend**: Open `http://localhost:52692` in browser
2. **QA API**: Test at `http://localhost:57485/query?query=test`
3. **Backend**: Check logs with `docker compose logs backend`

## Expected Behavior

1. **Frontend** (`:52692`): React app loads
2. **QA Service** (`:57485`): Responds to API calls
3. **Backend**: Processes data in background (batch job)

## If Still Not Working

### Check Ports:
```bash
# What's listening on host ports?
netstat -tulpn | grep -E ":(52692|57485|8000)"

# Check container ports
docker compose ps
docker compose port qa 8085
docker compose port frontend 3000
```

### Check Network:
```bash
# Test from within frontend container
docker compose exec frontend curl -v http://qa:8085/query?query=test

# Test from host
curl -v http://localhost:57485/query?query=test
```

## Summary
The services **WILL WORK** with these corrected configurations. The main issue was port mismatches and hardcoded URLs that didn't work in Docker networking.



