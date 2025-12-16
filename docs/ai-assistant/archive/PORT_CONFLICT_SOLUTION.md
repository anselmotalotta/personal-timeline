# Port Conflict Solution

## Current Issue

Both ports are being used:
- Port **52692** (Frontend) - already allocated
- Port **57485** (QA API) - already allocated

This suggests something else is already running on these ports.

---

## 🔍 Step 1: Find What's Using the Ports

Run these commands on your terminal:

```bash
# Check port 52692
sudo lsof -i :52692

# Check port 57485
sudo lsof -i :57485

# Alternative method
sudo netstat -tulpn | grep -E "52692|57485"

# Or
sudo ss -tulpn | grep -E "52692|57485"
```

Look for output like:
```
COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
node      1234 anselmo  21u  IPv4  12345      0t0  TCP *:52692 (LISTEN)
```

---

## 🛑 Step 2: Stop the Processes

### Option A: Kill by Process ID
```bash
# Replace 1234 with actual PID from step 1
sudo kill -9 1234
```

### Option B: Kill by Process Name
```bash
# If it's Node.js
pkill -f node

# If it's Python server
pkill -f "python.*server"

# Check if ports are now free
sudo lsof -i :52692
sudo lsof -i :57485
```

---

## 🚀 Step 3: Try Docker Again

```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline
docker compose down
docker compose up -d --build
docker compose ps
```

---

## 🔧 Alternative: Use Different Ports

If you can't or don't want to kill the processes, change the ports:

### Edit `docker-compose.yml`:

```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline
nano docker-compose.yml
```

Change:
```yaml
services:
  frontend:
    ports:
      - "52693:3000"  # Changed from 52692 to 52693
      
  qa:
    ports:
      - "57486:8085"  # Changed from 57485 to 57486
```

Then:
```bash
docker compose up -d --build
```

Access:
- Frontend: http://localhost:52693
- QA API: http://localhost:57486

**Also update** `src/frontend/src/Constants.js`:
```javascript
API_URL: 'http://localhost:57486'  // Change from 57485 to 57486
```

---

## 🎯 Quick Fix Commands

**Run this sequence:**

```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline

# 1. Find and display what's using the ports
echo "=== Checking port 52692 ==="
sudo lsof -i :52692

echo "=== Checking port 57485 ==="
sudo lsof -i :57485

# 2. Kill all node and python server processes (CAUTION!)
echo "=== Stopping Node.js processes ==="
pkill -f "node.*personal-timeline" || echo "No node processes found"

echo "=== Stopping Python server processes ==="
pkill -f "python.*qa.*server" || echo "No python server processes found"

# 3. Verify ports are free
echo "=== Verifying ports are free ==="
sudo lsof -i :52692 || echo "✅ Port 52692 is now free"
sudo lsof -i :57485 || echo "✅ Port 57485 is now free"

# 4. Start Docker
echo "=== Starting Docker containers ==="
docker compose down
docker compose up -d --build

# 5. Check status
echo "=== Container status ==="
docker compose ps
```

---

## 🤔 What Might Be Running?

Common causes:
1. **Previous Docker containers** (should be stopped by `docker compose down`)
2. **React dev server** (`npm start` from a previous session)
3. **Python Flask server** (`python -m src.qa.server` from testing)
4. **Another Personal Timeline instance**
5. **VS Code Live Server** or similar dev tools

---

## 🔍 Detailed Investigation

### Check all Docker containers
```bash
docker ps -a
docker container ls -a
```

### Check all listening ports
```bash
sudo netstat -tulpn | grep LISTEN
```

### Check Node.js processes
```bash
ps aux | grep node
```

### Check Python processes
```bash
ps aux | grep python | grep -v grep
```

---

## 💡 Recommended Solution

**If you don't need what's running on those ports:**

```bash
# Stop everything that might be using the ports
sudo lsof -i :52692 -t | xargs sudo kill -9 2>/dev/null
sudo lsof -i :57485 -t | xargs sudo kill -9 2>/dev/null

# Start Docker
cd ~/workspace/FacebookPostDownloader/personal-timeline
docker compose up -d --build
```

**If you need both running:**

Change Docker ports to 52693 and 57486 as described above.

---

## 🎯 One-Liner Solution

```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline && \
sudo lsof -i :52692 -t | xargs -r sudo kill -9 && \
sudo lsof -i :57485 -t | xargs -r sudo kill -9 && \
docker compose down && \
docker compose up -d --build && \
docker compose ps
```

This will:
1. Kill whatever is using port 52692
2. Kill whatever is using port 57485
3. Stop Docker containers
4. Rebuild and start fresh
5. Show status

---

## ✅ Success Check

After fixing, you should see:

```bash
$ docker compose ps

NAME                          COMMAND                  SERVICE    STATUS
personal-timeline-backend-1   "sh ingestion_startu…"   backend    Exited (0)
personal-timeline-frontend-1  "docker-entrypoint.s…"   frontend   Up
personal-timeline-qa-1        "/bin/sh -c 'python …"   qa         Up
```

Then access:
- **Frontend**: http://localhost:52692
- **QA API**: http://localhost:57485/test

---

## 🚨 If Still Not Working

**Just run the backend** (already tested and working):

```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline

# Set environment
export APP_DATA_DIR=~/workspace/FacebookPostDownloader/MyData/app_data
export ingest_new_data=True

# Run ingestion
python -m src.ingest.workflow
```

This works perfectly without Docker. Frontend and QA are optional - the core functionality (data import) is in the backend which we already tested successfully!

---

**Next step**: Run the investigation commands and let me know what you find!
