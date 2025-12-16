

# Docker & UV Setup for Personal Timeline

## Overview

This project has been configured with:
1. **UV** for faster Python package installation
2. **Graceful dependency handling** - optional AI/ML packages won't crash the app
3. **Multi-stage Docker builds** for smaller images
4. **Updated docker-compose.yml** with proper service dependencies

## What Was Fixed

### 1. Dependency Management
- **Before**: `torch`, `langchain`, `spotipy` were required dependencies
- **After**: All AI/ML packages are optional with graceful degradation
- **Code changes**:
  - `src/ingest/workflow.py`: ImageEnricher import inside try-except
  - `src/ingest/ingestion_startup.sh`: Optional script execution with error handling
  - `src/qa/server.py`: QA_AVAILABLE flag, graceful degradation
  - `src/requirements.txt`: AI/ML dependencies commented out as optional

### 2. UV Configuration
- Created `pyproject.toml` with:
  - Core dependencies (18 packages)
  - Optional AI dependencies (10 packages in `[project.optional-dependencies]`)
  - Development dependencies
- UV installs packages 2-10x faster than pip

### 3. Docker Configuration
- **Main Dockerfile**: Uses UV for faster builds, multi-stage for smaller images
- **Dockerfile.qa**: Separate QA service with AI packages
- **docker-compose.yml**: Updated with proper volumes and dependencies

## How to Know You're "In Trouble"

### Signs of Trouble (❌):
- `ImportError` for `torch`/`langchain`/`spotipy` at **module import time** (top of file)
- Docker containers crash immediately on startup
- "ModuleNotFoundError" in logs without graceful fallback
- Workflow stops completely instead of skipping optional features

### Signs of Success (✅):
- Workflow runs with warnings about missing optional dependencies
- Data import works (creates `raw_data.db`)
- Docker containers start and stay running
- Frontend accessible at http://localhost:52692
- QA service accessible (even if Q&A features disabled)

## Quick Start

### Option 1: Docker (Recommended)
```bash
# Build and start all services
docker compose up -d --build

# Check logs
docker compose logs -f

# Stop services
docker compose down
```

### Option 2: UV (Fast Local Development)
```bash
# Install core dependencies only
uv pip install -e .

# Install with AI/ML packages
uv pip install -e .[ai]

# Run workflow
python -m src.ingest.workflow
```

### Option 3: Traditional pip
```bash
# Install from requirements.txt
pip install -r src/requirements.txt

# Or install minimal requirements
pip install -r requirements-minimal.txt
```

## Service Ports

- **Frontend**: http://localhost:52692
- **Backend API**: http://localhost:8000
- **QA Service**: http://localhost:57485

## Testing the Setup

```bash
# Test imports work without optional dependencies
python -c "
import sys
sys.path.insert(0, 'src')
import os
os.environ['APP_DATA_DIR'] = '/tmp/test_data'
from ingest.workflow import *
print('✅ Core imports work')
"

# Test QA service
curl http://localhost:57485/test
```

## Adding AI/ML Features Later

If you want to enable AI features later:

1. **Install packages**:
   ```bash
   uv pip install torch langchain openai spotipy transformers faiss-cpu
   ```

2. **Restart services**:
   ```bash
   docker compose restart backend qa
   ```

3. **The code will automatically detect** and use the available packages.

## Troubleshooting

### Docker won't start
```bash
# Check if Docker daemon is running
sudo systemctl status docker

# Start Docker daemon
sudo systemctl start docker
```

### Permission errors
```bash
# Fix volume permissions
sudo chown -R $USER:$USER /workspace/MyData
```

### Port conflicts
Edit `docker-compose.yml` and change port mappings:
```yaml
ports:
  - "52693:3000"  # Changed from 52692
```

## Project Structure

```
personal-timeline/
├── Dockerfile              # Main service with UV
├── Dockerfile.qa           # QA service with AI packages
├── docker-compose.yml      # Updated compose file
├── pyproject.toml          # UV configuration
├── src/
│   ├── requirements.txt    # Updated with optional deps
│   ├── ingest/
│   │   └── workflow.py     # Fixed imports
│   └── qa/
│       └── server.py       # Graceful degradation
└── MyData/                 # Your data
```

## Support

If you encounter issues:
1. Check Docker logs: `docker compose logs`
2. Verify imports work locally
3. Ensure core dependencies are installed
4. Check the graceful degradation is working

The system is now **dependency-tolerant** - missing optional packages won't break the core functionality.

