# 🚀 Quick Start Guide - Personal Timeline

## ✅ Status: Ready to Test!

I've shut down the Next.js app and prepared personal-timeline for deployment.

---

## 📥 Step 1: Upload Your Facebook Data

You mentioned you have a local Facebook download. Here's how to use it:

### Option A: If Your Data is Already on This Machine

1. **Locate your Facebook export folder** (it should contain a `posts` subfolder)
2. **Copy the `posts` folder** to: `~/personal-data/facebook/`
3. The structure should be:
   ```
   ~/personal-data/facebook/posts/
       ├── your_posts_1.json
       ├── your_posts_2.json
       └── ... (and any associated photos)
   ```

Run this to copy (adjust the path):
```bash
cp -r /path/to/your/facebook-export/posts ~/personal-data/facebook/
```

### Option B: If Your Data is on Another Machine

You'll need to transfer it. The easiest way:

**Using the workspace file system:**
1. I can create an upload area
2. You upload your Facebook export ZIP
3. I'll extract it to the right location

**Let me know which option works for you!**

---

## 🔧 Step 2: Configure Environment Variables (Optional)

The app works with minimal config, but for full features:

### Required for QA System:
```bash
echo 'OPENAI_API_KEY=your-key-here' >> env/frontend.env.list
```

### Optional (for map visualization):
```bash
echo 'GOOGLE_MAP_API=your-key-here' >> env/frontend.env.list
```

### Optional (for Spotify embeds):
```bash
echo 'SPOTIFY_TOKEN=your-token' >> env/frontend.env.list
echo 'SPOTIFY_SECRET=your-secret' >> env/frontend.env.list
```

**You can skip these for now and test with Facebook data only!**

---

## 🐳 Step 3: Deploy with Docker

### Prerequisites:
- Docker Desktop must be installed and running
- Check with: `docker ps`

### Option A: Test with Sample Data First (Recommended)
```bash
# Copy sample data to test
cp -r sample_data/* ~/personal-data/app_data/

# Start just the frontend (uses pre-processed data)
docker-compose up -d frontend --build
```

Then visit: **http://localhost:3000**

### Option B: Full Pipeline with Your Facebook Data
```bash
# Run everything (ingestion + frontend + QA)
docker-compose up -d --build
```

This will:
1. **Backend**: Process your Facebook data (~5-30 min depending on data size)
2. **Frontend**: Start UI at http://localhost:3000
3. **QA**: Start question-answering at http://localhost:8085

### Check Progress:
```bash
# See running containers
docker ps

# Watch backend logs
docker logs -f <container-id-from-docker-ps>
```

---

## 🎯 Step 4: Use the Timeline!

### Timeline Visualization (Port 3000)
Browse your posts chronologically with:
- Date filtering
- Location maps
- Image galleries
- Episode grouping

### Question Answering (Port 8085)
Ask questions like:
- "Show me posts from my trip to Japan"
- "What did I post about in April 2023?"
- "Find photos of my dog"

---

## 🧪 Testing Recommendations

### Phase 1: Quick Test (5 minutes)
1. ✅ Use sample data (already in repo)
2. ✅ Start frontend only
3. ✅ Verify UI works

### Phase 2: Your Data Test (30+ minutes)
1. Upload your Facebook data
2. Run full pipeline
3. Check if posts are imported correctly

### Phase 3: Full Features (optional)
1. Add API keys for maps/QA
2. Test question answering
3. Explore all features

---

## 📊 What to Expect

### Supported Facebook Data:
- ✅ **Posts** with text content
- ✅ **Photos** with EXIF data
- ✅ **Timestamps**
- ✅ **Tagged people**
- ✅ **GPS coordinates** (if available)

### Processing Time:
- **100 posts**: ~2 minutes
- **1000 posts**: ~10-20 minutes
- **10000+ posts**: 30+ minutes
- (Depends on photo processing)

### Output:
- SQLite database in `~/personal-data/app_data/raw_data.db`
- CSV exports for posts/photos
- Searchable timeline UI

---

## 🔍 Troubleshooting

### Docker not installed?
```bash
# Check if Docker is available
docker --version

# If not, you'll need to install Docker Desktop
# https://www.docker.com/products/docker-desktop/
```

### Container won't start?
```bash
# Check logs
docker logs <container-id>

# Rebuild from scratch
docker-compose down
docker-compose up -d --build
```

### No posts showing up?
1. Check Facebook data is in: `~/personal-data/facebook/posts/`
2. Check backend logs for errors
3. Verify JSON files are in correct format

### Dependencies issues?
The Docker containers handle all dependencies automatically!

---

## 🎬 What's Next?

**Tell me:**
1. **Do you have Docker installed?** (`docker --version`)
2. **Where is your Facebook data?** (local machine or need to upload)
3. **Want to test with sample data first?** (safest option)

**Then I'll help you:**
- Transfer/upload your Facebook data
- Run the appropriate docker commands
- Monitor the processing
- Access the timeline UI

Ready when you are! 🚀

