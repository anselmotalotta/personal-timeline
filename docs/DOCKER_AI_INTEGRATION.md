# Docker AI Integration Guide

## Overview

This document describes the Docker infrastructure integration for the AI-Augmented Personal Archive system. The enhanced Docker setup adds AI services while maintaining compatibility with the existing architecture.

## Architecture

### Services

The system now consists of four main services:

1. **Frontend** (Port 52692)
   - React application with enhanced UI components
   - Communicates with backend, QA, and AI services

2. **Backend** (Port 8000)
   - Python ingestion pipeline
   - Data processing and storage
   - Integrates with AI services for enhancement

3. **QA Service** (Port 57485)
   - Enhanced question-answering system
   - Uses AI services for semantic understanding
   - Provides conversational memory access

4. **AI Services** (Port 8086) - NEW
   - Local LLM for narrative generation
   - Embedding generation for semantic search
   - Multimodal image understanding
   - Text-to-speech synthesis

### Service Dependencies

```
Frontend → Backend, QA, AI Services
QA → Backend, AI Services
Backend → AI Services
AI Services → (standalone)
```

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Key configuration options:

#### AI Model Configuration
- `LOCAL_LLM_MODEL`: Model for narrative generation (default: microsoft/DialoGPT-medium)
- `EMBEDDING_MODEL`: Model for semantic search (default: sentence-transformers/all-MiniLM-L6-v2)
- `TTS_MODEL`: Text-to-speech model (default: espnet/kan-bayashi_ljspeech_vits)
- `MULTIMODAL_MODEL`: Image understanding model (default: openai/clip-vit-base-patch32)

#### Processing Configuration
- `AI_PROCESSING_BATCH_SIZE`: Batch size for AI operations (default: 32)
- `AI_MAX_MEMORY_GB`: Maximum memory for AI models (default: 4)
- `ENABLE_GPU`: Enable GPU acceleration (default: false)

#### Feature Toggles
- `ENABLE_AI_ENHANCEMENT`: Enable AI enhancement during ingestion (default: true)
- `ENHANCED_QA_ENABLED`: Enable enhanced QA with AI services (default: true)

### Volume Mounts

The system uses the following volume mounts:

1. **MyData Volume**: `../MyData:/app/MyData`
   - Shared across all services
   - Contains personal data and databases
   - Persists across container restarts

2. **AI Models Volume**: `ai-models:/app/models`
   - Stores downloaded AI models
   - Persists across container restarts
   - Reduces model download time

3. **Source Code Mounts**: `./src:/app/src`
   - Development-time code mounting
   - Allows hot-reloading during development

## Deployment

### Starting the System

```bash
# Start all services
docker-compose up -d

# Start with rebuild
docker-compose up -d --build

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f ai-services
```

### Verification

Run the verification script to check system health:

```bash
bash scripts/verify_enhanced_docker_setup.sh
```

This script checks:
- Container status
- Service endpoints
- Volume mounts
- AI services health
- Data persistence
- Environment configuration

### Stopping the System

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## AI Services

### Health Check

The AI services provide a health endpoint:

```bash
curl http://localhost:8086/health
```

Response:
```json
{
  "status": "healthy",
  "services": ["embeddings", "multimodal", "narrative", "tts"],
  "models_loaded": ["sentence-transformers/all-MiniLM-L6-v2", ...]
}
```

### API Endpoints

#### Generate Narrative
```bash
POST http://localhost:8086/api/ai/generate_narrative
Content-Type: application/json

{
  "memories": [...],
  "mode": "chronological"
}
```

#### Generate Embeddings
```bash
POST http://localhost:8086/api/ai/generate_embeddings
Content-Type: application/json

{
  "texts": ["text1", "text2", ...]
}
```

#### Analyze Image
```bash
POST http://localhost:8086/api/ai/analyze_image
Content-Type: application/json

{
  "image_path": "/path/to/image.jpg",
  "context": "optional context"
}
```

#### Synthesize Speech
```bash
POST http://localhost:8086/api/ai/synthesize_speech
Content-Type: application/json

{
  "text": "Text to synthesize",
  "narrator_style": "neutral"
}
```

## Data Persistence

### Database Migration

The system automatically migrates existing databases to support enhanced features:

1. Existing LLEntry objects are preserved
2. New tables are created for:
   - Stories and chapters
   - People profiles
   - Galleries
   - Composite memories
3. Enhanced indexes are built for semantic search

### Backup and Restore

Before major updates, backup your data:

```bash
# Backup MyData directory
cp -r ../MyData ../MyData.backup

# Restore if needed
rm -rf ../MyData
cp -r ../MyData.backup ../MyData
```

## Troubleshooting

### AI Services Not Starting

1. Check logs:
   ```bash
   docker-compose logs ai-services
   ```

2. Verify model downloads:
   ```bash
   docker exec personal-timeline-ai-services-1 ls -la /app/models
   ```

3. Check memory limits:
   - Increase `AI_MAX_MEMORY_GB` in `.env`
   - Ensure Docker has sufficient memory allocated

### Service Communication Issues

1. Verify network connectivity:
   ```bash
   docker-compose exec backend curl http://ai-services:8086/health
   ```

2. Check service dependencies:
   ```bash
   docker-compose ps
   ```

3. Restart services in order:
   ```bash
   docker-compose restart ai-services
   docker-compose restart backend
   docker-compose restart qa
   docker-compose restart frontend
   ```

### Volume Mount Issues

1. Verify MyData directory exists:
   ```bash
   ls -la ../MyData
   ```

2. Check volume mounts:
   ```bash
   docker-compose exec backend ls -la /app/MyData
   ```

3. Recreate volumes if needed:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

## Performance Optimization

### Model Caching

AI models are cached in the `ai-models` volume. First startup will be slow as models download. Subsequent startups will be faster.

### GPU Acceleration

To enable GPU acceleration:

1. Install NVIDIA Docker runtime
2. Set `ENABLE_GPU=true` in `.env`
3. Rebuild containers:
   ```bash
   docker-compose up -d --build
   ```

### Memory Management

Adjust memory limits based on available resources:

- Minimum: 4GB RAM for AI services
- Recommended: 8GB RAM for optimal performance
- With GPU: 16GB RAM + 4GB VRAM

## Development

### Hot Reloading

Source code is mounted for development:

- Backend: `./src:/app/src`
- QA: `./src/qa:/app/src/qa`
- AI Services: `./src:/app/src`

Changes to Python files will be reflected after service restart.

### Testing

Run integration tests:

```bash
# Configuration tests (fast)
python -m pytest tests/test_docker_config.py -v

# Full integration tests (requires Docker)
python -m pytest tests/test_docker_integration.py -v
```

### Debugging

Access container shells:

```bash
# Backend
docker-compose exec backend bash

# AI Services
docker-compose exec ai-services bash

# QA
docker-compose exec qa bash
```

## Migration from Previous Version

If upgrading from the original Personal Timeline:

1. Backup existing data:
   ```bash
   cp -r ../MyData ../MyData.backup
   ```

2. Pull latest changes:
   ```bash
   git pull origin main
   ```

3. Update Docker Compose:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

4. Verify migration:
   ```bash
   bash scripts/verify_enhanced_docker_setup.sh
   ```

5. Check data integrity:
   - Verify existing entries are accessible
   - Check that new AI features are available
   - Test story generation and enhanced QA

## Security Considerations

### Local Processing

All AI processing happens locally:
- No data sent to external services
- Models run within Docker containers
- Network isolation between services

### API Keys

Optional external API keys (e.g., OpenAI) are only used as fallback:
- Set `OPENAI_API_KEY` only if needed
- Local models are preferred
- External calls are logged

### Data Privacy

- All personal data stays in MyData volume
- No telemetry or analytics
- User controls for sensitive content

## Support

For issues or questions:

1. Check logs: `docker-compose logs -f`
2. Run verification: `bash scripts/verify_enhanced_docker_setup.sh`
3. Review troubleshooting section above
4. Check existing GitHub issues
5. Create new issue with logs and configuration