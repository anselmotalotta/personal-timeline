

# Docker Fixes Summary

## Problem Analysis
The Docker containers were failing with `ModuleNotFoundError` for `geopy` and `flask_cors` even though these packages were in `requirements.txt`.

## Root Causes Identified and Fixed

### 1. **UV Installation Issue** (PRIMARY FIX)
- **Problem**: Using `uv pip install --system` was causing installation issues
- **Solution**: Changed to regular `pip install` in the virtual environment
- **Files Fixed**: `Dockerfile` and `Dockerfile.qa`
- **Change**: `RUN uv pip install --system -r src/requirements.txt` → `RUN pip install --no-cache-dir -r src/requirements.txt`

### 2. **Missing Dependencies in requirements.txt**
- **Problem**: Some required packages were missing from `requirements.txt`
- **Solution**: Added missing packages:
  - `sqlalchemy>=2.0.0`
  - `sqlite-utils>=3.36.0` 
  - `python-magic>=0.4.27`
  - `pyyaml>=6.0.0`
- **File Fixed**: `src/requirements.txt`

### 3. **Docker Build Issues**
- **Problem**: `README.md` missing in build context
- **Solution**: Added `COPY README.md .` to Dockerfiles
- **Problem**: `mkdir` conflicts when directories exist
- **Solution**: Added `|| true` to mkdir commands

### 4. **Package Structure Issue**
- **Problem**: `uv pip install --system .` tried to build package but structure was wrong
- **Solution**: Reverted to installing from `requirements.txt` instead of editable install

## Updated Docker Configuration

### Dockerfile (Backend)
```dockerfile
# Install UV for faster package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies with pip (in the virtual environment)
RUN pip install --no-cache-dir -r src/requirements.txt
```

### Dockerfile.qa (QA Service)
Same structure as above.

## How to Rebuild

### Option 1: Complete Clean Rebuild
```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline

# Stop and remove containers
docker compose down

# Clear Docker build cache
docker builder prune -a -f

# Rebuild without cache
docker compose up -d --build --no-cache
```

### Option 2: Rebuild Specific Services
```bash
cd ~/workspace/FacebookPostDownloader/personal-timeline

# Rebuild backend and QA services
docker compose build --no-cache backend
docker compose build --no-cache qa

# Start services
docker compose up -d
```

### Option 3: If Using Old Images
```bash
# Force pull new base images
docker compose pull

# Rebuild
docker compose up -d --build
```

## Verification

After rebuild, check logs:
```bash
# Check backend logs
docker compose logs -f backend | grep -A5 -B5 "geopy\|flask_cors"

# Check QA logs  
docker compose logs -f qa | tail -20

# Test imports in running container
docker compose exec backend python -c "import geopy; from flask_cors import CORS; print('✅ Dependencies installed')"
```

## Expected Outcome

After applying these fixes:
1. ✅ Docker build should succeed
2. ✅ All dependencies (`geopy`, `flask_cors`, etc.) should be installed
3. ✅ Containers should start without `ModuleNotFoundError`
4. ✅ Services should be accessible:
   - Frontend: http://localhost:52692
   - Backend API: http://localhost:8000
   - QA Service: http://localhost:57485

## Fallback Solution

If issues persist, use the test script:
```bash
chmod +x test_docker_simple.sh
./test_docker_simple.sh
```

This will test basic Docker functionality and dependency installation.

