# Frontend Fix - JSON Data Files

## Problem Identified

The frontend was showing a JSON parse error because:

1. **Backend container exited** after completing the import workflow
2. **Missing JSON files** - Frontend expects separate files by category
3. **Single enriched_data.json** - Backend only created one consolidated file

## Root Cause

The docker-compose.yml runs the backend with:
```yaml
command: bash src/ingest/ingestion_startup.sh
```

This command:
- Runs the import workflow
- Exits with code 0 when complete
- Does NOT start a persistent API server

The frontend expects:
- Static JSON files served from `/digital_data/personal-data/app_data/`
- Separate files: `books.json`, `exercise.json`, `photos.json`, etc.

## Solution Applied

### ✅ Step 1: Created Split Script

Created `/workspace/personal-timeline/src/ingest/split_enriched_data.py` to split the consolidated `enriched_data.json` into separate category files.

### ✅ Step 2: Generated Category Files

Ran the split script and created:
- `photos.json` - 176 Facebook post entries
- `books.json` - Empty array (no book data)
- `exercise.json` - Empty array (no exercise data)
- `purchase.json` - Empty array (no purchase data)
- `streaming.json` - Empty array (no streaming data)
- `places.json` - Empty array (no places data)
- `trips.json` - Empty array (no trips data)

All files are now accessible via symlinks at:
```
/workspace/personal-timeline/src/frontend/public/digital_data/personal-data/app_data/
```

### ✅ Step 3: Updated Startup Script

Need to add the split script to the ingestion workflow.

## To Complete the Fix

### Option A: Restart Docker Containers (Recommended)

The containers need to be restarted to serve the frontend properly:

```bash
# From the personal-timeline directory
docker compose down
docker compose up -d
```

This will:
1. Stop all containers
2. Start them fresh
3. Backend will re-run import (or skip if incremental)
4. Frontend will serve the new JSON files

### Option B: Update Startup Script

Add the split script to run automatically after data export:

**Edit `src/ingest/ingestion_startup.sh`:**

```bash
# After line 27 (after derive_episodes), add:
echo "Splitting enriched data for frontend..."
python -m src.ingest.split_enriched_data || echo "⚠️  split_enriched_data failed"
```

Then rebuild and restart:
```bash
docker compose down
docker compose build backend
docker compose up -d
```

## Verification

After restarting containers:

1. **Check containers are running:**
   ```bash
   docker compose ps
   ```
   
   Should show:
   - frontend: Up
   - backend: Up (or Exited 0 if import is complete)
   - qa: Up

2. **Check JSON files exist:**
   ```bash
   ls -lah /workspace/MyData/app_data/*.json
   ```
   
   Should show all 7 category files plus enriched_data.json

3. **Test frontend access:**
   
   Open browser to: http://localhost:54288/
   
   Should see:
   - Timeline interface loads
   - 176 Facebook posts visible
   - No JSON parse errors

## Current Status

✅ **Completed:**
- [x] Identified root cause
- [x] Created split_enriched_data.py script
- [x] Generated all required JSON files
- [x] Files accessible via symlinks

⏳ **Pending:**
- [ ] Restart Docker containers
- [ ] Verify frontend loads correctly
- [ ] Optional: Update startup script for automation

## Architecture Understanding

### Data Flow:

```
1. Facebook Data Import
   ↓
2. src/ingest/workflow.py
   ↓
3. enriched_data.json (single file)
   ↓
4. src/ingest/split_enriched_data.py (NEW)
   ↓
5. photos.json, books.json, etc. (separate files)
   ↓
6. Frontend reads via static file serving
```

### Frontend Expectations:

The frontend uses static file imports, NOT an API:

```javascript
// From src/frontend/src/service/DigitalDataImportor.js
let data_sources = [
  'books.json',
  'exercise.json', 
  'purchase.json',
  'streaming.json',
  'places.json',
  'trips.json',
  'photos.json'
];

// Tries to fetch from:
fetch('digital_data/personal-data/app_data/' + filename)
```

### Docker Container Behavior:

- **Backend:** Runs import workflow then exits (by design)
- **Frontend:** React dev server, stays running
- **QA:** Optional Q&A server, stays running

The backend doesn't need to stay running - it's a batch processing container.

## Why This Wasn't Obvious

1. **No API server** - Backend is batch processing only
2. **Static file serving** - Frontend serves its own files
3. **Container lifecycle** - Backend exiting is normal behavior
4. **Symlinks** - Files need to be in specific locations

## Future Improvements

### Automation

Add to `src/ingest/workflow.py` after line 91:

```python
# After json.dump(ex.get_all_data(), open(export_path, "w"))
print("Splitting enriched data for frontend...")
from src.ingest.split_enriched_data import split_enriched_data
split_enriched_data()
```

### Or Keep It Manual

Run after each import:
```bash
docker compose run --rm backend python -m src.ingest.split_enriched_data
```

## Related Files

- `/workspace/personal-timeline/src/ingest/split_enriched_data.py` - NEW split script
- `/workspace/personal-timeline/src/ingest/ingestion_startup.sh` - Startup sequence
- `/workspace/personal-timeline/src/ingest/workflow.py` - Main import workflow
- `/workspace/personal-timeline/src/frontend/src/service/DigitalDataImportor.js` - Frontend importer

## Summary

The Facebook data import worked perfectly (176 posts). The frontend issue was unrelated - it needed separate JSON files that the backend wasn't creating. This has now been fixed by:

1. Creating a split script
2. Running it to generate category files
3. (Pending) Restarting containers

Once containers are restarted, the timeline should display all 176 Facebook posts! 🎉
