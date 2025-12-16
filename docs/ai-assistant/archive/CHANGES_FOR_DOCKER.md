# Docker Configuration Fixes

## Summary
Fixed Docker setup to work with the existing Facebook data import modifications.

## Files Modified

### 1. `src/frontend/Dockerfile`
**Problem**: Symlink conflict - tried to create `/app/public/digital_data` but it already existed from copying sample_data.

**Changes**:
```dockerfile
# Before (BROKEN):
COPY sample_data public/digital_data
RUN ln -s /app/personal-data /app/public/digital_data  # ❌ FAILS: path exists

# After (FIXED):
RUN mkdir -p /app/public/digital_data/personal-data
COPY sample_data /app/public/digital_data/sample_data
RUN ln -sf /app/MyData /app/public/digital_data/MyData && \
    ln -sf /app/MyData/app_data /app/public/digital_data/personal-data/app_data
```

**Why**: 
- Creates proper directory structure first
- Sample data goes to subdirectory
- Symlinks align with docker compose volume mounts

### 2. `docker compose.yml` - QA Service
**Problem**: Volume mount path inconsistency

**Changes**:
```yaml
# Before:
volumes:
  - ./MyData:/app/personal-data  # Different path
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY:-}

# After:
volumes:
  - ./MyData:/app/MyData  # Consistent path
environment:
  - APP_DATA_DIR=/app/MyData/app_data  # Explicit
  - OPENAI_API_KEY=${OPENAI_API_KEY:-}
```

**Why**: Standardizes data location to `/app/MyData` across all services

### 3. `Dockerfile.qa.simple`
**Problem**: Environment variable didn't match docker compose mount

**Changes**:
```dockerfile
# Before:
RUN mkdir -p /app/personal-data || true
ENV APP_DATA_DIR=/app/personal-data/app_data

# After:
RUN mkdir -p /app/MyData/app_data || true
ENV APP_DATA_DIR=/app/MyData/app_data
```

**Why**: Aligns with docker compose.yml volume mount path

## Testing

After these changes, you should be able to run:

```bash
cd /workspace/personal-timeline
docker compose up -d --build
```

And access:
- Frontend: http://localhost:52692
- QA Server: http://localhost:57485

## Data Path Alignment

All services now use consistent paths:

| Service | Container Path | Host Path (mounted) |
|---------|---------------|---------------------|
| Backend | /app/MyData | ./MyData |
| QA | /app/MyData | ./MyData |
| Frontend | /app/MyData | ./MyData |

## Verification Checklist

After starting with Docker, verify:

- [ ] All containers start: `docker compose ps`
- [ ] No errors in logs: `docker compose logs`
- [ ] Frontend accessible: http://localhost:52692
- [ ] QA server responds: http://localhost:57485/test
- [ ] Photos visible in timeline
- [ ] Symlinks correct: `docker compose exec frontend ls -la /app/public/digital_data/`

## Rollback

If you need to revert changes:
```bash
git checkout src/frontend/Dockerfile
git checkout docker compose.yml
git checkout Dockerfile.qa.simple
```

## Notes

- Your Facebook importer modifications are preserved in source code
- No data is lost - it stays in `./MyData/` on the host
- Hot reload still works for development
- These changes make Docker work consistently with the no-Docker setup
