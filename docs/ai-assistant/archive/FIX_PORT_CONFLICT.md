# Fix Port Conflict Issue

## Error
```
Error response from daemon: failed to set up container networking: 
Bind for 0.0.0.0:57485 failed: port is already allocated
```

---

## 🔍 Diagnosis

Port 57485 (QA service) is already in use. This happens when:
1. Previous containers are still running
2. Another process is using the port
3. Docker didn't clean up properly

---

## ✅ Solutions (Try in Order)

### Solution 1: Stop Existing Containers (Most Common)

```bash
cd /workspace/personal-timeline

# Stop all running containers
docker-compose down

# Verify containers are stopped
docker ps

# Rebuild and start
docker-compose up -d --build
```

### Solution 2: Stop Specific Container

```bash
# Find the container using the port
docker ps | grep personal-timeline-qa

# Stop it
docker stop personal-timeline-qa-1

# Remove it
docker rm personal-timeline-qa-1

# Try again
docker-compose up -d --build
```

### Solution 3: Change Port (If Port is Needed by Another Service)

Edit `docker-compose.yml`:

```yaml
qa:
  ports:
    - "58485:8085"  # Change 57485 → 58485
```

Then update frontend to connect to new port:

Edit `src/frontend/src/Constants.js`:
```javascript
API_URL: 'http://localhost:58485'  // Change 57485 → 58485
```

### Solution 4: Find and Kill Process Using Port

```bash
# Find process using port 57485
sudo lsof -i :57485

# Or
sudo netstat -tulpn | grep 57485

# Kill the process (replace PID with actual process ID)
sudo kill -9 <PID>

# Try again
docker-compose up -d --build
```

### Solution 5: Remove All Containers and Rebuild

```bash
# Stop all containers
docker-compose down

# Remove all stopped containers
docker container prune -f

# Remove all unused images
docker image prune -a -f

# Rebuild from scratch
docker-compose up -d --build
```

---

## 🎯 Recommended Approach

**Best Solution**: Solution 1 - Just run `docker-compose down` first

```bash
cd /workspace/personal-timeline

# Stop everything
docker-compose down

# Wait a moment
sleep 2

# Start fresh
docker-compose up -d --build

# Check status
docker-compose ps
```

---

## 📊 Verify It Works

After fixing:

```bash
# Check running containers
docker ps

# Check logs
docker-compose logs -f

# Test frontend
curl http://localhost:52692

# Test QA API
curl http://localhost:57485/test
```

---

## 🚨 If Nothing Works

### Option A: Run Services Individually

```bash
# Build only backend
docker-compose build backend
docker-compose up backend

# No port conflict since backend doesn't expose ports
```

### Option B: Skip Docker, Use Python Directly

You already have this working!

```bash
cd /workspace/personal-timeline
export APP_DATA_DIR=/workspace/MyData/app_data
python -m src.ingest.workflow
```

The backend works perfectly without Docker. Frontend and QA are optional.

---

## 💡 Understanding the Ports

| Service | Internal Port | External Port | URL |
|---------|--------------|---------------|-----|
| Frontend | 3000 | 52692 | http://localhost:52692 |
| QA API | 8085 | 57485 | http://localhost:57485 |
| Backend | N/A | N/A | Runs and exits |

**The conflict is on port 57485 (QA service)**

---

## 🔧 Quick Fix Script

Save as `fix_docker.sh`:

```bash
#!/bin/bash
cd /workspace/personal-timeline

echo "🛑 Stopping all containers..."
docker-compose down

echo "🧹 Cleaning up..."
docker container prune -f

echo "🏗️ Rebuilding..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "✅ Done! Checking status..."
docker-compose ps
```

Run:
```bash
chmod +x fix_docker.sh
./fix_docker.sh
```

---

## 📝 Notes

- The error occurred because containers from a previous `docker-compose up` were still running
- Docker doesn't automatically stop containers when build fails
- Always run `docker-compose down` before `docker-compose up`

---

**Most likely fix**: Just run `docker-compose down` then try again! 🎉
