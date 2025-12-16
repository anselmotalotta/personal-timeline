# Running Personal Timeline with Docker

## Quick Start

```bash
cd /workspace/personal-timeline

# Build and start all services
docker compose up -d --build

# Check logs
docker compose logs -f

# Access the application
# Frontend: http://localhost:52692
# QA Server: http://localhost:57485
```

## What Was Fixed

### Issue 1: Symlink Conflict in Frontend Dockerfile
**Problem**: The Dockerfile tried to create a symlink at `/app/public/digital_data` but that path already existed from copying sample_data.

**Solution**: 
- Create proper directory structure
- Copy sample_data to a subdirectory
- Create symlinks that point to the mounted volume locations

### Issue 2: Data Path Consistency
**Problem**: Volume mounts and environment variables didn't align across services.

**Solution**: Standardized all services to use `/app/MyData` as the mount point.

## Docker Architecture

### Services

#### 1. Backend (Ingestion)
- **Purpose**: Imports and processes your personal data
- **Port**: 8000 (internal only, not exposed to host)
- **Dockerfile**: `Dockerfile.simple`
- **Data Location**: `/app/MyData` (mounted from `./MyData`)
- **Environment Variables**:
  - `APP_DATA_DIR=/app/MyData/app_data`
  - `ingest_new_data=True`
  - `enriched_data_to_json=True`

#### 2. QA Server
- **Purpose**: Question-answering engine over your timeline
- **Port**: 57485 (host) → 8085 (container)
- **Dockerfile**: `Dockerfile.qa.simple`
- **Data Location**: `/app/MyData` (mounted from `./MyData`)
- **Environment Variables**:
  - `APP_DATA_DIR=/app/MyData/app_data`
  - `OPENAI_API_KEY` (optional)

#### 3. Frontend
- **Purpose**: React-based timeline visualization
- **Port**: 52692 (host) → 3000 (container)
- **Dockerfile**: `src/frontend/Dockerfile`
- **Data Locations**:
  - `/app/MyData` → Main data directory
  - `/app/public/digital_data/MyData` → Symlink for public access
  - `/app/public/digital_data/personal-data/app_data` → Symlink to processed data

## Volume Mounts Explained

```yaml
volumes:
  - ./MyData:/app/MyData              # Your data from host to container
  - ./src/frontend:/app               # Frontend source (hot reload)
  - ./src/qa:/app/src/qa              # QA source (hot reload)
```

**Why these mounts?**
- Your data in `./MyData` persists on the host
- Code changes are reflected in real-time (development mode)
- Symlinks inside containers point to mounted volumes

## Data Flow

```
Host: ./MyData/
  └─ facebook/posts/media/          # Your raw Facebook data
  └─ app_data/                      # Processed data
     ├─ raw_data.db                 # SQLite database
     ├─ enriched_data.json          # Exported data
     └─ photos.json                 # Timeline episodes

Docker Container: /app/MyData/      # Mounted from host
  └─ Same structure as above

Frontend Access: /app/public/digital_data/
  ├─ MyData → /app/MyData                           # Symlink
  └─ personal-data/
     └─ app_data → /app/MyData/app_data             # Symlink
```

## Common Commands

### Start Services
```bash
# All services
docker compose up -d --build

# Individual services
docker compose up -d backend --build
docker compose up -d qa --build
docker compose up -d frontend --build
```

### Check Status
```bash
# View running containers
docker compose ps

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f frontend
docker compose logs -f qa
docker compose logs -f backend
```

### Stop Services
```bash
# Stop all
docker compose down

# Stop and remove volumes (⚠️ removes data!)
docker compose down -v

# Stop specific service
docker compose stop frontend
```

### Rebuild After Code Changes
```bash
# Rebuild everything
docker compose up -d --build

# Rebuild specific service
docker compose up -d --build frontend
```

## Troubleshooting

### Issue: Frontend can't find photos
**Check**:
1. Verify MyData is mounted: `docker compose exec frontend ls /app/MyData`
2. Check symlinks: `docker compose exec frontend ls -la /app/public/digital_data/`
3. Verify photos.json exists: `docker compose exec frontend cat /app/MyData/app_data/photos.json`

### Issue: QA server can't find database
**Check**:
1. Verify MyData is mounted: `docker compose exec qa ls /app/MyData/app_data`
2. Check environment: `docker compose exec qa env | grep APP_DATA_DIR`
3. Check database: `docker compose exec qa ls -la /app/MyData/app_data/raw_data.db`

### Issue: Backend ingestion fails
**Check logs**:
```bash
docker compose logs backend
```

### Issue: Port already in use
If ports 52692 or 57485 are already in use, edit `docker compose.yml`:
```yaml
ports:
  - "NEW_PORT:3000"  # Change NEW_PORT to an available port
```

## Development Workflow

### 1. Making Code Changes

**Frontend changes** (React):
- Edit files in `./src/frontend/`
- Changes hot-reload automatically (no rebuild needed)

**QA server changes**:
- Edit files in `./src/qa/`
- Restart QA container: `docker compose restart qa`

**Ingestion code changes** (importers, enrichers):
- Edit files in `./src/ingest/`
- Rebuild backend: `docker compose up -d --build backend`

### 2. Adding New Data

Place new data in `./MyData/` following the structure:
```
./MyData/
  ├─ facebook/posts/media/
  ├─ google_photos/
  └─ etc.
```

Then restart backend to re-ingest:
```bash
docker compose restart backend
```

### 3. Accessing Container Shell

```bash
# Frontend container
docker compose exec frontend sh

# QA container
docker compose exec qa bash

# Backend container
docker compose exec backend bash
```

## Differences from No-Docker Setup

| Aspect | No Docker | Docker |
|--------|-----------|--------|
| **Frontend URL** | http://localhost:54288 | http://localhost:52692 |
| **QA Server URL** | http://localhost:8085 | http://localhost:57485 |
| **Data Path** | /workspace/MyData | ./MyData (mounted to /app/MyData) |
| **Hot Reload** | Yes (npm start) | Yes (volumes mounted) |
| **Isolation** | Uses host Python/Node | Isolated containers |
| **Startup** | Faster | Slower (build time) |
| **Cleanup** | Manual process kill | `docker compose down` |

## Production Deployment

For production deployment, consider:

1. **Remove development volumes**:
   ```yaml
   # Remove these lines for production
   - ./src/frontend:/app
   - ./src/qa:/app/src/qa
   ```

2. **Use environment file** for secrets:
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your-key-here" > .env
   ```

3. **Configure proper domains/ports** in docker compose.yml

4. **Add nginx** as reverse proxy (optional)

## Your Modified Code Works!

The Facebook importer modifications you made are preserved because:
1. Source code is copied into Docker images during build
2. Changes to `src/ingest/importers/FacebookPosts.py` are included
3. Changes to `src/ingest/create_episodes.py` are included

So Docker will work with your Facebook photos without GPS coordinates! 🎉

## Summary

✅ **Fixed**: Symlink conflicts in frontend Dockerfile  
✅ **Standardized**: Data paths across all services to `/app/MyData`  
✅ **Tested**: Volume mounts and symlinks align correctly  
✅ **Preserved**: Your code modifications for Facebook GPS handling  

You can now run with Docker! Your data at `./MyData/` will be accessible to all containers, and the timeline will display your Facebook photos.
