# Docker Data Setup

## Important: Data Directory Structure

The Docker setup expects data to be in `./MyData/` relative to the `docker-compose.yml` file (i.e., `/workspace/personal-timeline/MyData/`).

If your data is in a different location (e.g., `/workspace/MyData/`), you need to create symlinks.

### Quick Setup

If your data is in `/workspace/MyData/` and you're running Docker from `/workspace/personal-timeline/`:

```bash
cd /workspace/personal-timeline/MyData

# Link Facebook data
ln -s /workspace/MyData/facebook ./facebook

# Link Google Photos (if you have it)
ln -s /workspace/MyData/google_photos ./google_photos

# Verify
ls -la
```

You should see symlinks pointing to your actual data directories.

### Verify Data is Accessible

```bash
# Should list JSON files
ls MyData/facebook/posts/*.json

# Should list photos
ls MyData/facebook/posts/media/
```

### Alternative: Update docker-compose.yml

Instead of symlinks, you can modify the volume mounts in `docker-compose.yml` to point to your actual data location:

```yaml
# BEFORE:
volumes:
  - ./MyData:/app/MyData

# AFTER (if data is in /workspace/MyData):
volumes:
  - ../MyData:/app/MyData
```

But symlinks are cleaner and don't require changing the docker-compose file.

## Database Location

The app_data directory (containing `raw_data.db`) can be in `/workspace/personal-timeline/MyData/app_data/`.

If you want to use the existing database from `/workspace/MyData/app_data/`, you can:

1. **Copy the database files** (recommended for Docker):
   ```bash
   cp /workspace/MyData/app_data/raw_data.db /workspace/personal-timeline/MyData/app_data/
   ```

2. **Or symlink the entire app_data directory** (simpler but shared state):
   ```bash
   cd /workspace/personal-timeline/MyData
   rm -rf app_data
   ln -s /workspace/MyData/app_data ./app_data
   ```

## Current Setup (Already Applied)

✅ Symlinks created:
- `MyData/facebook` → `/workspace/MyData/facebook`
- `MyData/google_photos` → `/workspace/MyData/google_photos`

✅ Separate databases:
- Docker: `/workspace/personal-timeline/MyData/app_data/raw_data.db`
- Non-Docker: `/workspace/MyData/app_data/raw_data.db`
