#! /bin/bash

echo "==============================================="
echo "Personal Timeline - Enhanced Ingestion Startup"
echo "==============================================="

# Check if AI services are enabled
if [ "${ENABLE_AI_ENHANCEMENT:-true}" = "true" ]; then
    echo "AI enhancement enabled, waiting for AI services..."
    
    # Wait for AI services to be ready
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -f "${AI_SERVICES_URL:-http://ai-services:8086}/health" >/dev/null 2>&1; then
            echo "✓ AI services are ready"
            break
        fi
        echo "Waiting for AI services... (attempt $((attempt + 1))/$max_attempts)"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo "⚠️  AI services not ready, continuing without AI enhancement"
        export ENABLE_AI_ENHANCEMENT=false
    fi
else
    echo "AI enhancement disabled"
fi

# Main workflow (required)
echo "Running main workflow..."
python -m src.ingest.workflow
WORKFLOW_EXIT=$?

if [ $WORKFLOW_EXIT -ne 0 ]; then
    echo "❌ Main workflow failed with exit code $WORKFLOW_EXIT"
    exit $WORKFLOW_EXIT
fi

# Enhanced AI processing if enabled
if [ "${ENABLE_AI_ENHANCEMENT:-false}" = "true" ]; then
    echo "Running AI enhancement pipeline..."
    python -m src.common.migration.database_migrator || echo "⚠️  Database migration skipped"
    python -m src.common.services.ai_enhancement_pipeline || echo "⚠️  AI enhancement pipeline failed"
fi

# Optional: Offline processing (requires torch)
# echo "Running offline processing..."
# python -m src.ingest.offline_processing || echo "⚠️  Offline processing skipped (missing dependencies)"

# Optional: Create episodes (requires spotipy)
echo "Running create_episodes..."
python -m src.ingest.create_episodes || echo "⚠️  create_episodes skipped (missing spotipy)"

# Optional: Derive episodes (requires langchain)
echo "Running derive_episodes..."
python -m src.ingest.derive_episodes || echo "⚠️  derive_episodes skipped (missing langchain)"

# Split enriched data for frontend consumption
echo "Splitting enriched data for frontend..."
python -m src.ingest.split_enriched_data || echo "⚠️  split_enriched_data failed"

echo "==============================================="
echo "Enhanced ingestion startup complete"
echo "==============================================="
