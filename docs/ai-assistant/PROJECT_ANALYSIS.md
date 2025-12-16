# 📊 Personal Timeline Project Analysis

## 🎯 What This Project Does

**TimelineBuilder** is a Facebook Research project that creates a **searchable personal timeline** from your digital data across multiple services (Google Photos, Spotify, Amazon, Facebook, etc.).

### Key Features:
1. **Data Ingestion** - Import data from 9+ sources
2. **Enrichment** - Add AI-powered metadata (object detection, OCR, geolocation)
3. **Visualization** - ReactJS frontend to browse your timeline
4. **Question Answering** - LLM-powered QA system to query your personal data

---

## 🏗️ Architecture

### Three Main Components:

```
┌─────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   BACKEND    │  │   FRONTEND   │  │      QA      │ │
│  │  (Ingestion) │  │   (ReactJS)  │  │  (PostText)  │ │
│  │              │  │              │  │              │ │
│  │ Port: N/A    │  │ Port: 3000   │  │ Port: 8085   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                            │                            │
│                     ┌──────▼───────┐                   │
│                     │  SQLite DB    │                   │
│                     │ (raw_data.db) │                   │
│                     └───────────────┘                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
personal-timeline/
├── src/
│   ├── ingest/               # Backend: Data importers & enrichment
│   │   ├── importers/        # 9+ data source importers
│   │   │   ├── create_facebook_LLEntries.py
│   │   │   ├── create_google_photo_LLEntries.py
│   │   │   ├── create_amazon_LLEntries.py
│   │   │   └── ... (more importers)
│   │   ├── enrichment/       # AI-powered enrichment
│   │   │   ├── image_enrichment.py (object detection)
│   │   │   ├── geo_enrichment.py (location data)
│   │   │   └── socratic/ (CLIP-based image understanding)
│   │   └── derive_episodes.py # Group entries into episodes
│   │
│   ├── frontend/             # ReactJS visualization UI
│   │   └── (React components for timeline view)
│   │
│   └── qa/                   # PostText QA engine
│       └── (LLM-based question answering)
│
├── personal-data/            # User data directory (created in ~/personal-data)
│   ├── google_photos/
│   ├── facebook/
│   ├── spotify/
│   ├── amazon/
│   └── app_data/            # Processed data (SQLite DB + CSVs)
│
├── sample_data/             # Anonymized test dataset
├── notebooks/               # Jupyter tutorials
├── docker-compose.yml       # Orchestration
└── conf/ingest.conf        # Configuration
```

---

## 🔄 Data Flow

### 1. Data Ingestion Pipeline

```
Raw Data (JSON/CSV/XML)
    ↓
Importers (parse & normalize)
    ↓
SQLite DB (raw_data.db)
    ↓
Enrichment (AI analysis)
    ↓
Episodes (grouped events)
    ↓
CSV exports + DB
```

### 2. Supported Data Sources

| Source | Input Format | Key Data | Notes |
|--------|-------------|----------|-------|
| **Facebook** | JSON (from Download Your Information) | Posts + Photos | ✅ Uses official FB export! |
| **Google Photos** | Takeout ZIP | Photos + metadata | Includes EXIF, location |
| **Google Timeline** | Takeout JSON | Location history | Semantic locations |
| **Spotify** | JSON export | Streaming history | Songs, albums, artists |
| **Amazon** | CSV | Purchase history | Retail orders |
| **Kindle** | CSV | Books | Digital purchases |
| **Apple Health** | XML | Exercise, calories | iWatch data |
| **Venmo** | CSV | Transactions | Payment history |
| **Libby** | JSON | Library books | Borrowed books |

---

## 🤖 AI/ML Components

### 1. Image Enrichment (`image_enrichment.py`)
- **Object Detection** - Detects objects in photos
- **OCR** - Extracts text from images
- Uses pre-trained models (CLIP, vision transformers)

### 2. Socratic Module (`socratic/`)
- CLIP-based image understanding
- Generates natural language descriptions
- Extracts visual features for search

### 3. Geo Enrichment (`geo_enrichment.py`)
- Reverse geocoding (lat/long → address)
- Timezone detection
- Location clustering

### 4. PostText QA Engine
- Three modes:
  - **ChatGPT** - General knowledge (no personal context)
  - **Retrieval-based** - Top-k relevant episodes
  - **View-based** - SQL queries over tabular data
- Can answer:
  - "Show me photos of plants in my neighborhood"
  - "How many books did I buy in April?"
  - "When did I last travel to Japan?"

---

## 🔧 Key Technologies

- **Backend**: Python 3.10
- **Frontend**: ReactJS
- **Database**: SQLite
- **ML Libraries**: 
  - PyTorch, torchvision
  - Transformers (Hugging Face)
  - CLIP (OpenAI)
  - sentence-transformers
  - FAISS (vector search)
- **LLM Integration**: 
  - OpenAI API (GPT-3.5-turbo, GPT-4)
  - LangChain
- **Containerization**: Docker + Docker Compose
- **APIs Used**:
  - Google Maps API
  - Spotify API
  - OpenAI API

---

## 📊 Database Schema

The project creates:
1. **SQLite DB** (`raw_data.db`) - Raw imported data
2. **CSV Exports** - Processed views:
   - `books.csv`
   - `exercise.csv`
   - `photos.csv`
   - `places.csv`
   - `purchase.csv`
   - `streaming.csv`
   - `trips.csv`

---

## 🚀 How It Works (Step-by-Step)

### Setup Phase:
1. User runs `init.sh` → creates `~/personal-data/` directory
2. User downloads data from services (FB, Google, Spotify, etc.)
3. User places data in appropriate folders
4. User sets API keys (Google Maps, Spotify, OpenAI)

### Ingestion Phase:
1. Run `docker-compose up -d backend`
2. Backend reads data from `personal-data/` folders
3. Importers parse each data source
4. Data is normalized and stored in SQLite
5. Enrichment runs (AI analysis on photos)
6. Episodes are derived (grouping related events)
7. CSV exports are generated

### Usage Phase:
1. **Visualization**: Browse timeline at `http://localhost:3000`
2. **QA**: Ask questions at `http://localhost:8085`

---

## ✅ Is It Working?

### Project Status: **ARCHIVED**

**Good News:**
- ✅ Complete, well-documented codebase
- ✅ Sample data provided for testing
- ✅ Docker setup simplifies deployment
- ✅ **FACEBOOK IMPORTER EXISTS** and uses official FB export!

**Potential Issues:**
- ⚠️ Archived = No active maintenance
- ⚠️ Dependencies may be outdated (OpenAI 0.28.1 is old)
- ⚠️ Some API endpoints might have changed
- ⚠️ Docker images need to be built (not pre-built)

**Can We Run It?**
- **YES**, but may need:
  - Dependency updates (OpenAI library v1.x is current, code uses 0.28.1)
  - API key updates
  - Docker Desktop installed
  - Sample data for testing (provided in repo)

---

## 🎯 Most Relevant to Your Use Case

### **FACEBOOK POSTS IMPORTER** (`create_facebook_LLEntries.py`)

**How it works:**
1. Expects Facebook data from "Download Your Information" feature
2. Reads JSON files from `~/personal-data/facebook/posts/`
3. Extracts:
   - Posts with timestamps
   - Photos with EXIF data
   - Tagged people
   - GPS coordinates (if available)
4. Stores in SQLite for searching

**Key Code:**
```python
# Reads JSON files from Facebook export
json_files = self.get_type_files_deep(json_filepath, ...)
for json_file in json_files:
    post_data = json.loads(r)
    # Extracts media with timestamps
    all_media = self.find_all_in_haystack("timestamp", post_data, True)
    # Creates searchable entries
    obj = self.create_LLEntry(uri, latitude, longitude, taken_timestamp, tagged_people)
```

---

## 🧪 Testing Strategy

### Option 1: Use Sample Data (Fastest)
The repo includes anonymized sample data in `sample_data/`:
- Pre-processed SQLite DB
- Sample CSVs
- Test images

### Option 2: Test with Your Facebook Export
1. Download your Facebook data (JSON format)
2. Place in `~/personal-data/facebook/posts/`
3. Run the backend ingestion
4. See if it parses correctly

---

## 🔍 Next Steps

### To Test If It Works:

1. **Check sample data** (no setup needed)
2. **Run with Docker** (requires Docker Desktop)
3. **Try notebooks** (easier than full Docker setup)

**Which would you like to try first?**

---

## 💡 Key Insights

1. **This is EXACTLY what you needed!** - Parses Facebook export (the "Download Your Information" feature)
2. **No API needed** - Uses your downloaded data directly
3. **More than posts** - Also handles photos, location, enrichment
4. **QA system** - Can search/query your posts naturally
5. **Production-quality** - From Facebook Research, well-architected

---

## ⚠️ Limitations

1. **Archived** - No updates since archival
2. **Setup complexity** - Requires Docker, multiple API keys
3. **Heavy dependencies** - PyTorch, CLIP, transformers (large downloads)
4. **Privacy** - Runs locally but uses OpenAI API (data leaves machine)
5. **FB export only** - Can't fetch live data (but that's what you wanted!)

---

## 🤔 Verdict

**Is it complete?** YES - Full working system

**Does it work?** PROBABLY - May need minor updates

**Is it useful?** YES - Does exactly what you need for Facebook posts

**Worth testing?** ABSOLUTELY - Best solution for parsing FB exports

