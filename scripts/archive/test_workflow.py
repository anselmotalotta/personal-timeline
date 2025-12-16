#!/usr/bin/env python3
"""
Test the full workflow with Facebook data
Mimics what happens in Docker container
"""

import sys
import os

# Set up environment variables as they would be in Docker
os.environ['APP_DATA_DIR'] = '/workspace/MyData/app_data'
os.environ['ingest_new_data'] = 'True'
os.environ['incremental_geo_enrich'] = 'False'  # Disable for now
os.environ['incremental_image_enrich'] = 'False'  # Disable for now  
os.environ['incremental_export'] = 'True'
os.environ['enriched_data_to_json'] = 'True'

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 70)
print("PERSONAL TIMELINE - WORKFLOW TEST")
print("=" * 70)
print(f"APP_DATA_DIR: {os.environ['APP_DATA_DIR']}")
print(f"ingest_new_data: {os.environ['ingest_new_data']}")
print("=" * 70)

# Update data source config to point to our data
import json
data_source_path = 'src/common/bootstrap/data_source.json'
with open(data_source_path, 'r') as f:
    data_sources = json.load(f)

# Update Facebook path
for ds in data_sources:
    if ds['source_name'] == 'FacebookPosts':
        old_path = ds['configs']['input_directory']
        new_path = '/workspace/MyData/facebook'
        ds['configs']['input_directory'] = new_path
        print(f"✅ Updated Facebook path: {old_path} → {new_path}")
        break

# Save updated config
with open(data_source_path, 'w') as f:
    json.dump(data_sources, f, indent=2)

print("\n🚀 Starting workflow...\n")

try:
    from src.ingest.importers.generic_importer_workflow import GenericImportOrchestrator
    
    print("--------------Data Import Start--------------")
    gip = GenericImportOrchestrator()
    
    if os.getenv("ingest_new_data") == "True":
        print("✅ Ingest new Data is set to true")
        gip.start_import()
    else:
        print("⚠️  Ingest is disabled")
    
    print("\n--------------Data Import Complete--------------")
    
    # Print stats
    from src.common.persistence.personal_data_db import PersonalDataDBConnector
    print("\n------------------------------------------------")
    print("--------------Data Stats By Source--------------")
    print("------------------------------------------------")
    PersonalDataDBConnector().print_data_stats_by_source()
    
except Exception as e:
    print(f"\n❌ Error during workflow: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Workflow test complete!")
