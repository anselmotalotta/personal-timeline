# Docker Commands - Quick Reference

## ⚠️ Important: Use `docker compose` (with space), not `docker-compose`

You have Docker Compose V2, which uses `docker compose` instead of `docker-compose`.

---

## 🔧 Fix Port Conflict

### Step 1: Stop existing containers
```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline
docker compose down
```

### Step 2: Clean up (optional)
```bash
docker container prune -f
```

### Step 3: Rebuild and start
```bash
docker compose up -d --build
```

### Step 4: Check status
```bash
docker compose ps
```

---

## 📋 Common Commands

### View running containers
```bash
docker compose ps
```

### View logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f qa
```

### Stop services
```bash
docker compose down
```

### Restart services
```bash
docker compose restart
```

### Rebuild specific service
```bash
docker compose build backend
docker compose up -d backend
```

### Remove everything and start fresh
```bash
docker compose down
docker system prune -f
docker compose up -d --build
```

---

## 🚀 Quick Fix for Your Port Error

Run these commands in order:

```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline

# 1. Stop everything
docker compose down

# 2. Wait a moment
sleep 2

# 3. Start fresh
docker compose up -d --build

# 4. Check status
docker compose ps
```

---

## 📊 After Starting

### Check if services are running
```bash
docker compose ps
```

Expected output:
```
NAME                          COMMAND                  SERVICE    STATUS
personal-timeline-backend-1   "sh ingestion_startu…"   backend    Exited (0)
personal-timeline-frontend-1  "docker-entrypoint.s…"   frontend   Up
personal-timeline-qa-1        "/bin/sh -c 'python …"   qa         Up
```

### Access services
- **Frontend**: http://localhost:52692
- **QA API**: http://localhost:57485

### Test QA API
```bash
curl http://localhost:57485/test
```

### Test Frontend
```bash
curl http://localhost:52692
```

---

## 🐛 Troubleshooting

### If port still conflicts
```bash
# Find what's using port 57485
sudo lsof -i :57485

# Or
sudo ss -tulpn | grep 57485

# Kill the process if needed (replace <PID>)
sudo kill -9 <PID>
```

### If services crash
```bash
# Check logs
docker compose logs qa
docker compose logs frontend

# Check specific service
docker compose logs --tail=50 qa
```

### If build fails
```bash
# Clean everything
docker compose down -v
docker system prune -a -f

# Rebuild from scratch
docker compose build --no-cache
docker compose up -d
```

---

## 💡 Alternative: Run Without Docker

If Docker continues to have issues, you can run the Python backend directly (already tested and working):

```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline

# Set environment
export APP_DATA_DIR=~/workspace/FacebookPostDownloader/MyData/app_data
export ingest_new_data=True

# Run ingestion
python -m src.ingest.workflow
```

This works perfectly and doesn't require Docker! Frontend and QA are optional.

---

## 🎯 Most Common Issue = Solution

**Your error**: Port 57485 already allocated

**Fix**: 
```bash
docker compose down
docker compose up -d --build
```

That's it! The containers from your previous attempt are still running. Just stop them first.

---

## 📝 Notes

- `docker-compose` (old) → `docker compose` (new)
- Always run `docker compose down` before rebuilding
- Backend service runs once and exits (this is normal)
- Frontend and QA stay running

---

**Try this now:**

```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline
docker compose down
docker compose up -d --build
docker compose ps
```

✅ Should work!
