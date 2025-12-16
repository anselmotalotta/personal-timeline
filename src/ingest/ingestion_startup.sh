#! /bin/bash

echo "==============================================="
echo "Personal Timeline - Ingestion Startup"
echo "==============================================="

# Main workflow (required)
echo "Running main workflow..."
python -m src.ingest.workflow
WORKFLOW_EXIT=$?

if [ $WORKFLOW_EXIT -ne 0 ]; then
    echo "❌ Main workflow failed with exit code $WORKFLOW_EXIT"
    exit $WORKFLOW_EXIT
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
echo "Ingestion startup complete"
echo "==============================================="
