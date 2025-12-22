# 🚀 AI-Augmented Personal Archive - Quick Start Guide

## Prerequisites

1. **Docker & Docker Compose** installed
2. **Personal data** in `../MyData` directory (or sample data will be created)

## 🎯 Quick Start (2 minutes)

### 1. Start the Application
```bash
# Option A: Use the restart script (recommended)
./scripts/RESTART_DOCKER.sh

# Option B: Manual start
docker-compose up -d --build
```

### 2. Access the Application
Once services are running, open these URLs:

- **🎨 Main Application:** http://localhost:52692
  - Enhanced timeline with story generation
  - People intelligence dashboard  
  - Smart gallery browser
  - Interactive map with narratives

- **🤖 AI Chat Interface:** http://localhost:57485
  - Enhanced memory retrieval
  - Conversational exploration
  - Contextual memory suggestions

- **⚙️ Backend API:** http://localhost:8000
  - REST endpoints for all services
  - Health checks and status

- **🧠 AI Services:** http://localhost:8086
  - Local AI model endpoints
  - Embedding generation
  - Story generation APIs

### 3. Check System Status
```bash
# View all services
docker-compose ps

# Check logs
docker-compose logs -f

# Check specific service
docker-compose logs frontend
```

## 🎮 Testing the Features

### A. Story Generation
1. Go to http://localhost:52692
2. Click "Generate Story" 
3. Select narrative mode (chronological, thematic, people-centered)
4. Watch AI create chapters with your memories

### B. People Intelligence  
1. Navigate to "People" tab
2. See auto-detected people from your data
3. View interaction timelines and relationship evolution
4. Generate "best of us" compilations

### C. Smart Galleries
1. Go to "Galleries" section
2. Try natural language prompts like:
   - "Show me creative moments"
   - "Find travel adventures"
   - "Quiet reflective times"
3. Convert galleries to stories

### D. Enhanced Memory Chat
1. Visit http://localhost:57485
2. Ask questions like:
   - "Tell me about my experiences with friends"
   - "What were my highlights this year?"
   - "Show me memories from travel"
3. Get contextual, narrative responses

### E. Place-Based Exploration
1. Use the enhanced map component
2. Click locations to see narrative layers
3. Explore journey connections between places

## 🔧 Troubleshooting

### Services Won't Start
```bash
# Check Docker daemon
docker info

# Restart everything
./scripts/RESTART_DOCKER.sh

# Check for port conflicts
lsof -i :52692
lsof -i :57485
lsof -i :8000
lsof -i :8086
```

### AI Services Not Working
```bash
# Check AI service logs
docker-compose logs ai-services

# Verify AI service health
curl http://localhost:8086/health
```

### Frontend Not Loading
```bash
# Check frontend logs
docker-compose logs frontend

# Verify frontend is running
curl http://localhost:52692
```

### No Data Showing
The system will work with sample data if no personal data is found. To add your own data:

1. Place exported data in `../MyData/` directory
2. Restart services: `./scripts/RESTART_DOCKER.sh`
3. Check ingestion logs: `docker-compose logs backend`

## 🎯 Key Features to Test

### ✅ Core AI Features
- **Story Generation:** Multiple narrative modes with AI-written chapters
- **People Intelligence:** Auto-detection and relationship analysis  
- **Smart Galleries:** Natural language gallery creation
- **Memory Resurfacing:** Contextual memory suggestions
- **Enhanced Search:** Semantic understanding beyond keywords

### ✅ Privacy & Safety
- **Local Processing:** All AI runs locally, no external calls
- **Content Filtering:** Sensitive content automatically filtered
- **User Controls:** Full control over privacy settings
- **Data Ownership:** Your data stays on your machine

### ✅ Enhanced Experience
- **Narrative Interface:** Stories instead of raw timelines
- **Conversational Memory:** Chat with your personal archive
- **Multimodal Understanding:** Text, images, and location context
- **Proactive Insights:** Gentle memory resurfacing and reflection prompts

## 🛑 Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (careful - removes data!)
docker-compose down -v
```

## 📊 System Status

After starting, you should see:
- ✅ 4 services running (frontend, backend, qa, ai-services)
- ✅ All health checks passing
- ✅ No error messages in logs
- ✅ Web interfaces accessible

## 🎉 Success Indicators

You'll know it's working when:
1. **Frontend loads** at http://localhost:52692 with enhanced UI
2. **Stories generate** with AI-written chapters and media
3. **People profiles** show relationship timelines
4. **Galleries create** from natural language prompts
5. **Memory chat** provides contextual, narrative responses
6. **All processing stays local** (check network traffic)

---

**Need help?** Check the logs with `docker-compose logs -f` or refer to the SYSTEM_INTEGRATION_REPORT.md for detailed test results.