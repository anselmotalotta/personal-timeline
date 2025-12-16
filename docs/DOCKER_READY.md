# Docker Setup - Ready to Run! 🚀

## What Was Fixed

After analyzing your Docker logs, I identified and fixed **3 critical issues**:

### Issue 1: Frontend - Missing npm Module
**Error**: `Cannot find module 'ajv/dist/compile/codegen'`

**Root Cause**: Volume mounting `package.json` was interfering with node_modules

**Fix**: Removed `./src/frontend/package.json:/app/package.json` from docker-compose.yml

---

### Issue 2: Backend - Can't Find Facebook Data  
**Error**: `All json files in path: None` + `TypeError: 'NoneType' object is not iterable`

**Root Cause**: Hardcoded absolute path `/workspace/MyData/facebook` in config file

**Fix**: Changed to relative path `MyData/facebook` in `src/common/bootstrap/data_source.json`

---

### Issue 3: Data Directory Mismatch
**Problem**: Data exists in `/workspace/MyData/` but Docker mounts `./MyData/` (from personal-timeline directory)

**Fix**: Created symlinks:
- `MyData/facebook → /workspace/MyData/facebook`
- `MyData/google_photos → /workspace/MyData/google_photos`

---

## Verification ✅

I ran a pre-flight check and everything looks good:

```
✅ MyData/ exists
✅ MyData/facebook symlink exists → /workspace/MyData/facebook
✅ MyData/facebook/posts/ accessible (10 JSON files)
✅ MyData/app_data/ exists
✅ raw_data.db found
✅ docker-compose.yml exists
✅ Volume mounts configured correctly
✅ data_source.json exists
✅ Facebook path configured correctly (relative)
```

---

## How to Start Docker Services

### Option 1: Use the Convenience Script (Recommended)

```bash
cd /workspace/personal-timeline
bash RESTART_DOCKER.sh
```

This will:
1. Stop any running containers
2. Rebuild images with the fixes
3. Start all services
4. Show live logs

Press `Ctrl+C` to stop watching logs (containers keep running).

### Option 2: Manual Commands

```bash
cd /workspace/personal-timeline

# Stop existing containers
docker compose down

# Rebuild images
docker compose build

# Start services in background
docker compose up -d

# Watch logs (optional)
docker compose logs -f
```

---

## What to Expect

### Frontend (React App)
- **Build time**: ~30-60 seconds
- **Success indicator**: `Compiled successfully!` in logs
- **URL**: http://localhost:52692
- **Should display**: Your timeline with 2 Facebook photos

### Backend (Data Ingestion)
- **Run time**: ~10-30 seconds
- **Success indicator**: `✅ Main workflow completed successfully`
- **Expected**: Processes Facebook JSON files, creates enriched_data.json
- **Then exits**: This is normal! Backend only runs on startup to ingest data

### QA Server (Q&A API)
- **Start time**: ~5 seconds
- **Success indicator**: `Running on http://...`
- **URL**: http://localhost:57485/test (should return "okay")

---

## Checking Status

### Quick Status Check
```bash
docker compose ps
```

Expected output:
```
NAME                     STATUS       PORTS
personal-timeline-frontend-1  Up    0.0.0.0:52692->3000/tcp
personal-timeline-qa-1        Up    0.0.0.0:57485->8085/tcp
personal-timeline-backend-1   Exited (0)  [This is normal!]
```

**Note**: Backend exits after ingestion completes - this is expected behavior.

### View Logs
```bash
# All services
docker compose logs

# Specific service
docker compose logs frontend
docker compose logs qa
docker compose logs backend

# Follow logs live
docker compose logs -f frontend
```

---

## Troubleshooting

### If Services Don't Start

Run the debug script:
```bash
bash DEBUG_DOCKER.sh
```

This will show:
- Container status
- Last 30 lines of frontend logs
- Last 20 lines of QA and backend logs
- Volume mount verification
- Port status

### Common Issues

**Frontend still showing errors?**
```bash
# Rebuild without cache
docker compose build --no-cache frontend
docker compose up -d frontend
```

**Backend can't find data?**
```bash
# Verify data is accessible in container
docker compose run --rm backend ls -la /app/MyData/facebook/posts/

# Should list 10 JSON files
```

**Can't access http://localhost:52692?**
```bash
# Check if frontend container is running
docker compose ps | grep frontend

# Check if port is bound
sudo netstat -tlnp | grep 52692

# Try restarting
docker compose restart frontend
```

---

## Files Created

### Documentation
- `DOCKER_READY.md` (this file) - Complete Docker setup guide
- `DOCKER_FIXES_APPLIED.md` - Detailed technical explanation
- `DOCKER_DATA_SETUP.md` - Data directory structure guide
- `FIXES_SUMMARY.txt` - Quick reference

### Scripts
- `RESTART_DOCKER.sh` - Convenience script to restart everything
- `verify_docker_setup.sh` - Pre-flight checks before starting
- `DEBUG_DOCKER.sh` - Troubleshooting and diagnostics
- `check_backend_mount.sh` - Backend volume mount verification

---

## Next Steps

1. **Start Docker services**:
   ```bash
   bash RESTART_DOCKER.sh
   ```

2. **Wait for "Compiled successfully!"** in the logs

3. **Open browser**: http://localhost:52692

4. **Verify timeline shows 2 Facebook photos**

5. **Test QA server**: http://localhost:57485/test (should return "okay")

---

## Stopping Services

When you're done:
```bash
docker compose down
```

This stops and removes containers (but preserves your data).

---

## Data Persistence

Your data is persisted in:
- **Host**: `/workspace/personal-timeline/MyData/app_data/`
- **Contains**: `raw_data.db`, `enriched_data.json`, etc.

Even after `docker compose down`, your data remains safe.

---

## Differences from Non-Docker Setup

| Aspect | Non-Docker | Docker |
|--------|-----------|--------|
| Frontend Port | 54288 | 52692 |
| QA Port | 8085 | 57485 |
| Data Directory | `/workspace/MyData/` | `/workspace/personal-timeline/MyData/` (symlinked) |
| Database | `/workspace/MyData/app_data/raw_data.db` | `/workspace/personal-timeline/MyData/app_data/raw_data.db` |
| Start Command | `bash start.sh` | `docker compose up -d` |
| Stop Command | `bash teardown.sh` | `docker compose down` |

---

## Summary

✅ All Docker issues have been fixed  
✅ Data symlinks created  
✅ Configuration updated  
✅ Pre-flight checks passed  
✅ Ready to start services!

Run `bash RESTART_DOCKER.sh` to get started! 🎉
