# 🚀 Running Personal Timeline Locally

## ✅ Current Status

Your Facebook data is already prepared at:
- **Location:** `~/personal-data/facebook/posts/`
- **Sample data:** `~/personal-data/app_data/`
- **Project:** `/workspace/personal-timeline/`

---

## 📋 Run These Commands in Your Local Terminal

### Step 1: Navigate to the Project
```bash
cd /workspace/personal-timeline
```

### Step 2: Verify Your Facebook Data is There
```bash
ls -la ~/personal-data/facebook/posts/
```

You should see files like:
- `your_posts__check_ins__photos_and_videos_1.json`
- `media/` folder with photos
- Other JSON files

### Step 3: Start with Sample Data (Test First)
This will test the UI with sample data before processing your real data:

```bash
# Start just the frontend with sample data
docker compose up -d frontend
```

### Step 4: Access the UI
Open your browser to:
- **Timeline UI:** http://localhost:52692
- (We remapped port 3000 → 52692 for your setup)

### Step 5: Check If It's Working
```bash
# See running containers
docker ps

# Check frontend logs
docker compose logs frontend

# If you see errors, show me the output!
```

---

## 🔄 Process Your Real Facebook Data

Once the frontend works with sample data, process your actual posts:

### Option 1: Full Pipeline (Recommended)
This runs everything: ingestion + enrichment + frontend + QA

```bash
# Stop current containers
docker compose down

# Start everything
docker compose up -d --build

# This will:
# 1. Process your Facebook posts (backend container)
# 2. Start the web UI (frontend container)
# 3. Start QA system (qa container)
```

### Option 2: Backend Only (Just Process Data)
If you only want to process data without the UI:

```bash
docker compose up backend
```

Watch the logs to see progress. When done, you'll have:
- SQLite database: `~/personal-data/app_data/raw_data.db`
- CSV exports in: `~/personal-data/app_data/`

---

## 📊 Monitoring Progress

### Check Container Status
```bash
docker ps
```

### View Backend Logs (Processing)
```bash
docker compose logs -f backend
```

### View Frontend Logs
```bash
docker compose logs -f frontend
```

### View QA Logs
```bash
docker compose logs -f qa
```

---

## 🎯 What to Expect

### Processing Time for Your Data:
- You have **1 year** of Facebook data (41 MB ZIP)
- Estimated processing: **10-20 minutes**
- Backend will:
  1. Read JSON files
  2. Extract posts, photos, timestamps
  3. Process images (EXIF data, locations)
  4. Create episodes (grouped events)
  5. Generate SQLite DB + CSV exports

### Services & Ports:
- **Frontend (Timeline UI):** http://localhost:52692
- **QA (Question Answering):** http://localhost:57485

---

## 🐛 Troubleshooting

### Container Won't Start?
```bash
# Check for errors
docker compose logs <service-name>

# Rebuild from scratch
docker compose down
docker compose up -d --build
```

### Permission Errors?
```bash
# Make sure you own the data directory
ls -la ~/personal-data/

# Fix permissions if needed
chmod -R 755 ~/personal-data/
```

### No Posts Showing Up?
1. Check backend logs: `docker compose logs backend`
2. Verify JSON files exist: `ls ~/personal-data/facebook/posts/*.json`
3. Check database was created: `ls -lh ~/personal-data/app_data/raw_data.db`

### Port Already in Use?
If ports 52692 or 57485 are busy:
```bash
# Kill whatever is using the port
lsof -ti:52692 | xargs kill -9
lsof -ti:57485 | xargs kill -9
```

---

## 🧪 Verification Steps

After starting containers, verify everything works:

```bash
# 1. Check all containers are running
docker ps

# 2. Test frontend is responding
curl http://localhost:52692

# 3. Check if data is being processed
ls -lh ~/personal-data/app_data/

# 4. View some sample data
head ~/personal-data/app_data/episodes.json
```

---

## 🔧 Configuration (Optional)

### Add API Keys for Full Features

If you want the QA system to work with OpenAI:

```bash
# Edit the environment file
nano env/frontend.env.list

# Add this line:
OPENAI_API_KEY=your-key-here

# Save and restart
docker compose restart qa
```

### For Google Maps Integration:
```bash
echo 'GOOGLE_MAP_API=your-key-here' >> env/frontend.env.list
docker compose restart frontend
```

---

## 📂 Your Data Structure

After processing, you'll have:

```
~/personal-data/
├── facebook/
│   └── posts/
│       ├── your_posts__check_ins__photos_and_videos_1.json
│       ├── media/
│       │   └── *.jpg
│       └── ... (other JSON files)
│
└── app_data/
    ├── raw_data.db           # SQLite database (all data)
    ├── episodes.json         # Grouped events
    ├── episodes.csv          # CSV export
    ├── photos.sampled.csv    # Photo metadata
    ├── places.sampled.csv    # Location data
    └── ... (other exports)
```

---

## 🎬 Quick Start Summary

**Fastest path to see it working:**

```bash
cd /workspace/personal-timeline
docker compose up -d frontend
# Wait 30 seconds
open http://localhost:52692
```

**Full pipeline with your data:**

```bash
cd /workspace/personal-timeline
docker compose up -d --build
# Wait 10-20 minutes
docker compose logs -f backend  # Watch progress
open http://localhost:52692
```

---

## ❓ Need Help?

If you see errors, share:
1. Output of `docker compose logs <service>`
2. Any error messages
3. What step failed

I'll help you debug! 🚀

---

## 🎯 Expected Results

### Sample Data Test:
- Timeline UI shows anonymized data
- Multiple data sources (books, photos, places)
- Interactive browsing by date

### Your Facebook Data:
- Your posts from the past year
- Photos you uploaded
- Dates and locations
- Searchable timeline
- QA system to ask questions

Ready to go! Run the commands above and let me know how it goes! 🎉
