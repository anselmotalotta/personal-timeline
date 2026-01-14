# Quick Reference - AI Personal Archive

## 🚀 Quick Commands

### Start/Stop Services
```bash
./start_app.sh                    # Start all services
docker compose down               # Stop all services
docker compose restart [service] # Restart specific service
```

### Testing
```bash
python tests/run_all_tests.py     # Run all tests
python -m pytest tests/unit/ -v   # Unit tests only
cd src/frontend && npm test       # Frontend tests
```

### Debugging
```bash
docker compose logs -f ai-services     # View AI service logs
curl http://localhost:8086/health      # Check AI service health
open tools/browser_functionality_test.html  # Manual testing
```

## 📁 Key Directories

| Directory | Purpose | When to Edit |
|-----------|---------|--------------|
| `src/ai_services/` | AI logic & APIs | Adding AI features |
| `src/frontend/src/components/` | React components | UI changes |
| `src/data_processing/` | Data import/processing | Data handling |
| `tests/` | Test suite | Adding tests |
| `config/` | Configuration & scripts | Setup changes |
| `tools/` | Debug & development tools | Debugging |

## 🔧 Common Tasks

### Add New AI Feature
1. Edit: `src/ai_services/api.py` (add endpoint)
2. Edit: `src/ai_services/[service].py` (add logic)
3. Test: `python -m pytest tests/unit/test_[service].py`
4. Restart: `docker compose restart ai-services`

### Fix Frontend Issue
1. Edit: `src/frontend/src/components/[Component].js`
2. Test: `cd src/frontend && npm test`
3. View: `http://localhost:52692`
4. Debug: Check browser console, network tab

### Add New Data Source
1. Edit: `src/data_processing/local_processor.py`
2. Add: New processing method
3. Test: `python -m pytest tests/test_data_processing.py`
4. Restart: `docker compose restart backend`

## 🌐 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:52692 | Main UI |
| AI Services | http://localhost:8086 | AI APIs |
| Backend | http://localhost:8000 | Data APIs |
| QA Service | http://localhost:57485 | Chat interface |

## 🔍 Troubleshooting Checklist

### Services Not Starting
- [ ] Docker Desktop running?
- [ ] Ports available (52692, 8086, 8000, 57485)?
- [ ] `.env` file exists?
- [ ] Check: `docker compose ps`

### Frontend Empty/Not Loading
- [ ] AI services running? `curl http://localhost:8086/health`
- [ ] Check browser console for errors
- [ ] Check network tab for failed API calls
- [ ] Verify: `src/frontend/src/Constants.js` has correct API URL

### AI Features Not Working
- [ ] API keys in `.env`? `cat .env | grep API_KEY`
- [ ] Check: `curl http://localhost:8086/status`
- [ ] View logs: `docker compose logs ai-services`

### No Data/Empty Results
- [ ] Data files in `MyData/`?
- [ ] Check: `docker compose logs backend`
- [ ] Verify data processing: `curl http://localhost:8086/people`

## 📊 Data Flow Quick Reference

```
Personal Data Files (MyData/)
    ↓
local_processor.py (processes & stores)
    ↓
Database (SQLite/PostgreSQL)
    ↓
AI Services (story_generation.py, people_intelligence.py)
    ↓
AI Providers (OpenAI, Anthropic) [ML only]
    ↓
Generated Content (stories, insights)
    ↓
Frontend Components (StoryInterface, PeopleDashboard)
    ↓
User Interface
```

## 🎯 File Quick Access

### Most Important Files
- `src/ai_services/api.py` - Main API endpoints
- `src/ai_services/story_generation.py` - Story creation
- `src/frontend/src/components/StoryInterface.js` - Story UI
- `docker-compose.yml` - Service configuration
- `.env` - API keys & configuration

### Configuration Files
- `.env.example` - Configuration template
- `pyproject.toml` - Python dependencies
- `config/ingest.conf` - Data processing settings
- `src/frontend/package.json` - Frontend dependencies

### Debug Tools
- `tools/browser_functionality_test.html` - Manual testing
- `tools/debug_openai_error.py` - AI debugging
- `tests/run_all_tests.py` - Comprehensive testing