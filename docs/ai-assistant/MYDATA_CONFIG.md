# MyData Folder Configuration

## ✅ Configuration Updated!

Your personal data has been moved to `/workspace/MyData/` and the Docker configuration has been updated to point to this location.

---

## 📂 Current Data Structure

```
/workspace/MyData/
├── facebook/posts/          ← Your Facebook posts (35KB JSON + media)
│   ├── your_posts__check_ins__photos_and_videos_1.json
│   ├── places_you_have_been_tagged_in.json
│   ├── media/ (photos/videos)
│   └── album/
├── app_data/                ← Processed data (SQLite DB, CSVs)
│   ├── books.sampled.json
│   ├── episodes.json
│   ├── photos.sampled.json
│   └── images/
└── your_facebook_activity/  ← Original Facebook export
    ├── posts/
    ├── messages/
    └── ... (all other FB data)
```

---

## 🔧 What Was Changed

### 1. Docker Compose Volumes
**File:** `docker-compose.yml`

**Before:**
```yaml
volumes:
  - ./personal-data/:/app/personal-data/
```

**After:**
```yaml
volumes:
  - /workspace/MyData/:/app/personal-data/
```

This change was applied to all three services:
- ✅ `frontend` (Timeline UI)
- ✅ `qa` (Q&A interface)
- ✅ `backend` (Data processing)

### 2. Data Organization
- Copied Facebook posts from `your_facebook_activity/posts/` to `MyData/facebook/posts/`
- Copied sample data to `MyData/app_data/` for testing
- All containers now mount `/workspace/MyData/` as `/app/personal-data/`

---

## 🚀 Running the Application

Everything works the same way, just with your new data location!

### Quick Test (Sample Data)
```bash
cd /workspace/personal-timeline
docker compose up -d frontend
```
Visit: http://localhost:52692

### Full Pipeline (Your Facebook Data)
```bash
cd /workspace/personal-timeline
docker compose up -d --build
docker compose logs -f backend
```
Visit: http://localhost:52692

---

## 📊 Data Flow

1. **Input:** `/workspace/MyData/facebook/posts/*.json`
   - Raw Facebook export data

2. **Processing:** Backend ingests and processes data
   - Extracts posts, photos, timestamps
   - Generates SQLite database

3. **Output:** `/workspace/MyData/app_data/`
   - `views_db.sqlite` - Searchable database
   - CSV exports for each data type
   - Processed images

4. **UI:** Frontend reads from `app_data/`
   - Timeline visualization
   - Search functionality
   - Photo gallery

---

## 🔍 Verify Configuration

Check that Docker sees your data:
```bash
docker compose config | grep -A 2 volumes
```

Should show:
```
volumes:
  - /workspace/MyData/:/app/personal-data/
```

---

## 📝 Environment Variables

The `APP_DATA_DIR` environment variable tells the application where to find/write data:

```yaml
environment:
  - APP_DATA_DIR=/app/personal-data/app_data
```

This maps to `/workspace/MyData/app_data/` on your host system.

---

## 🎯 Why This Structure?

**Benefits:**
- ✅ All your personal data in one organized location
- ✅ Easy to backup: just copy `/workspace/MyData/`
- ✅ Clean separation from application code
- ✅ Original Facebook export preserved
- ✅ Processed data stored separately

**Data Safety:**
- Original Facebook data remains untouched in `your_facebook_activity/`
- Processing only reads from `facebook/posts/`
- Output goes to `app_data/`

---

## 🛠️ Troubleshooting

### If containers can't find data:

1. **Check volume mount:**
   ```bash
   docker compose config | grep volumes
   ```

2. **Verify data exists:**
   ```bash
   ls -lh /workspace/MyData/facebook/posts/
   ls -lh /workspace/MyData/app_data/
   ```

3. **Check container logs:**
   ```bash
   docker compose logs frontend
   docker compose logs backend
   ```

### If you need to change the location again:

Just edit `docker-compose.yml` and update all three volume paths:
```yaml
volumes:
  - /your/new/path/:/app/personal-data/
```

Then restart:
```bash
docker compose down
docker compose up -d --build
```

---

## ✅ Ready to Go!

Your configuration is set up and ready. The application will:
1. Read your Facebook posts from `/workspace/MyData/facebook/posts/`
2. Process them using the backend service
3. Store results in `/workspace/MyData/app_data/`
4. Display them in the timeline UI at http://localhost:52692

**Next Step:** Run the commands from QUICKSTART.txt! 🚀
