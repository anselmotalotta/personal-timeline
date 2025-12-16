# Facebook Data Setup Guide

## Overview

The Personal Timeline application now includes **automatic detection** of Facebook data structure, making it resilient to different Facebook export formats.

## Supported Facebook Export Formats

The application automatically detects and handles multiple Facebook export structures:

### ✅ Format 1: Full Facebook Export (Recommended)
Facebook's complete data download:
```
MyData/
├── your_facebook_activity/
│   ├── posts/
│   │   ├── your_posts__check_ins__photos_and_videos_1.json
│   │   ├── posts_on_other_pages_and_profiles.json
│   │   ├── your_uncategorized_photos.json
│   │   ├── your_videos.json
│   │   └── media/
│   │       └── [photo and video files]
│   ├── messages/
│   ├── comments_and_reactions/
│   └── ... (other folders)
├── ads_information/
├── connections/
└── ... (other Facebook data)
```

### ✅ Format 2: Old/Custom Organization
Manually organized or older exports:
```
MyData/
└── facebook/
    └── posts/
        ├── *.json
        └── media/
```

### ✅ Format 3: Direct Posts Folder
Simplified structure:
```
MyData/
└── posts/
    ├── *.json
    └── media/
```

### ✅ Format 4: Root Level
JSON files directly in MyData:
```
MyData/
├── *.json
└── media/
```

## How It Works

### Automatic Detection

When the application starts, it:

1. **Searches** for Facebook posts in multiple known locations
2. **Detects** which structure you're using
3. **Logs** the found location and file count
4. **Processes** your data from the detected location

**Example console output:**
```
🔍 Auto-detecting Facebook data structure in: /app/MyData
   ⏭️  Checked your_facebook_activity/posts - no JSON files
   ⏭️  Checked facebook/posts - no JSON files
✅ Found Facebook data at: your_facebook_activity/posts
   📄 12 JSON file(s) detected
📂 Using detected path: /app/MyData/your_facebook_activity/posts
```

### Resilient Media File Resolution

The application also handles different media file path formats:

**Facebook may reference media files with different prefixes:**
- `your_facebook_activity/posts/media/photo.jpg`
- `posts/media/photo.jpg`
- `media/photo.jpg`

**The application tries multiple strategies:**
1. Use the path as-is from the base directory
2. Strip known prefixes and retry
3. Try relative to the JSON file location
4. Search common media directories

This ensures media files are found regardless of the export format.

## Setup Instructions

### Option A: Full Facebook Export (Easiest)

1. **Download your Facebook data:**
   - Go to Facebook Settings → Your Facebook Information
   - Click "Download Your Information"
   - Select format: **JSON** (recommended)
   - Select date range and quality
   - Click "Create File"

2. **Extract and place the data:**
   ```bash
   # Extract the downloaded ZIP
   unzip facebook-[your_name].zip
   
   # Copy/move the entire extracted folder to MyData
   mv facebook-[your_name]/* ../MyData/
   ```

3. **Verify structure:**
   ```bash
   ls ../MyData/your_facebook_activity/posts/
   # Should show: *.json files and media/ directory
   ```

4. **Start Docker:**
   ```bash
   docker compose up -d
   ```

The application will automatically detect and use the correct paths!

### Option B: Selective Files

If you only want to use specific files:

1. **Create directory structure:**
   ```bash
   mkdir -p ../MyData/your_facebook_activity/posts
   ```

2. **Copy your files:**
   ```bash
   # Copy JSON files
   cp your_posts*.json ../MyData/your_facebook_activity/posts/
   
   # Copy media folder
   cp -r media/ ../MyData/your_facebook_activity/posts/
   ```

3. **Start Docker:**
   ```bash
   docker compose up -d
   ```

## Troubleshooting

### No Facebook Data Found

If you see this message:
```
❌ No Facebook posts found in any known location
   Searched paths relative to /app/MyData:
   - your_facebook_activity/posts
   - facebook/posts
   - posts
   - (root)
```

**Solutions:**

1. **Verify data location:**
   ```bash
   # Check what's in MyData
   ls -la ../MyData/
   
   # Look for posts directory
   find ../MyData -name "posts" -type d
   
   # Look for JSON files
   find ../MyData -name "*.json" | head
   ```

2. **Check JSON files exist:**
   ```bash
   # Should find Facebook JSON files
   find ../MyData -name "*posts*.json"
   ```

3. **Ensure correct placement:**
   - JSON files should be in one of the supported locations
   - Media files should be in a `media/` subdirectory

4. **Check file permissions:**
   ```bash
   # Files should be readable
   ls -la ../MyData/your_facebook_activity/posts/
   ```

### Media Files Not Found

If photos aren't showing up:

1. **Check media directory exists:**
   ```bash
   ls ../MyData/your_facebook_activity/posts/media/
   ```

2. **Verify file paths in JSON:**
   ```bash
   # Check how Facebook references files
   grep -o '"uri"[^,]*' ../MyData/your_facebook_activity/posts/*.json | head
   ```

3. **Enable debug logging** (edit `src/ingest/importers/create_facebook_LLEntries.py`):
   ```python
   # Uncomment these lines to see path resolution attempts
   print(f"Trying to resolve: {media_uri}")
   print(f"Checked paths: {possible_paths}")
   ```

## Configuration

The Facebook data source is configured in `src/common/bootstrap/data_source.json`:

```json
{
  "id": 9,
  "source_name": "FacebookPosts",
  "entry_type": "photo",
  "configs": {
    "input_directory": "MyData",
    "filetype": "json",
    ...
  }
}
```

**Note:** The `input_directory` is set to `MyData` (parent directory), and the application auto-detects the posts subdirectory.

## Future Facebook Export Formats

If Facebook changes their export format in the future:

### For Users:
Simply place your data in `../MyData/` and the application will attempt to detect it.

### For Developers:
To add support for a new format, edit `src/ingest/importers/create_facebook_LLEntries.py`:

1. **Add new path to detection list:**
   ```python
   possible_paths = [
       "your_facebook_activity/posts",
       "facebook/posts",
       "NEW_FORMAT_PATH_HERE",  # Add new format
       "posts",
       "",
   ]
   ```

2. **Add new media path prefix if needed:**
   ```python
   for prefix in [
       "your_facebook_activity/posts/",
       "facebook/posts/",
       "NEW_FORMAT_PREFIX/",  # Add new prefix
       "posts/"
   ]:
   ```

3. **Test with new export format**

4. **Update this documentation**

## Testing Auto-Detection

To see the auto-detection in action:

```bash
# Start with logs
docker compose up

# Watch for these lines:
# 🔍 Auto-detecting Facebook data structure in: /app/MyData
# ✅ Found Facebook data at: [detected path]
# 📂 Using detected path: [full path]
# 📋 Processing X JSON file(s)
```

## Benefits of This Approach

✅ **Resilient:** Works with multiple Facebook export formats
✅ **User-friendly:** No manual configuration needed
✅ **Future-proof:** Easy to add support for new formats
✅ **Transparent:** Logs show exactly what was detected
✅ **Graceful fallback:** Clear error messages if data not found

---

**Questions or issues?** Check the logs for detection output, or see `docs/TROUBLESHOOTING_GUIDE.md` for more help.
