# Debug Docker Port Issue

## Run these commands to investigate:

### 1. Check ALL Docker containers (running and stopped)
```bash
docker ps -a
```

### 2. Check if there are multiple compose projects
```bash
docker ps -a --filter "name=personal-timeline"
```

### 3. Nuclear option - Stop and remove ALL containers
```bash
docker stop $(docker ps -aq) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null
```

### 4. Check ports again
```bash
sudo lsof -i :52692
sudo lsof -i :57485
```

### 5. Then try Docker again
```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline
docker compose up -d --build
```

---

## OR: Simplest Solution - Just Change the Ports!

Edit `docker-compose.yml` and use different ports that aren't conflicting:

```yaml
services:
  frontend:
    ports:
      - "3000:3000"  # Use 3000 instead of 52692
      
  qa:
    ports:
      - "8085:8085"  # Use 8085 instead of 57485
```

Then:
```bash
docker compose up -d --build
```

Access:
- Frontend: http://localhost:3000
- QA API: http://localhost:8085

This avoids the port conflict entirely!
