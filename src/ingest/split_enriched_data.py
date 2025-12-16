#!/usr/bin/env python3
"""
Split enriched_data.json into separate files by source type for frontend consumption.
Also converts camelCase field names to snake_case for frontend compatibility.
"""

import json
import os
import re
from collections import defaultdict

def camel_to_snake(name):
    """Convert camelCase to snake_case."""
    # Insert underscore before capital letters
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Insert underscore before capital letters followed by lowercase  
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def convert_keys(obj):
    """Recursively convert all dictionary keys from camelCase to snake_case."""
    if isinstance(obj, dict):
        return {camel_to_snake(k): convert_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_keys(item) for item in obj]
    else:
        return obj

def split_enriched_data():
    """Split enriched_data.json into separate category files."""
    
    app_data_dir = os.environ.get("APP_DATA_DIR", "/app/MyData/app_data")
    enriched_path = os.path.join(app_data_dir, "enriched_data.json")
    
    if not os.path.exists(enriched_path):
        print(f"❌ enriched_data.json not found at {enriched_path}")
        return
    
    print(f"📖 Reading {enriched_path}")
    with open(enriched_path, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Total entries: {len(data)}")
    
    # Group data by source and convert keys
    by_source = defaultdict(list)
    for entry in data:
        # Convert camelCase to snake_case for frontend compatibility
        entry = convert_keys(entry)
        source = entry.get('source', 'unknown')
        by_source[source].append(entry)
    
    print(f"📁 Found {len(by_source)} data sources")
    
    # Mapping from source names to frontend expected file names
    source_to_file = {
        'FacebookPosts': 'photos.json',
        'GooglePhotos': 'photos.json',
        'ApplePhotos': 'photos.json',
        'GoogleBooks': 'books.json',
        'KindleBooks': 'books.json',
        'AppleBooks': 'books.json',
        'Strava': 'exercise.json',
        'AppleHealth': 'exercise.json',
        'AppleMusic': 'streaming.json',
        'Spotify': 'streaming.json',
        'GoogleMaps': 'places.json',
        'AppleMaps': 'places.json',
        'AmazonPurchase': 'purchase.json',
        'Trips': 'trips.json',
    }
    
    # Aggregate sources that map to same file
    by_file = defaultdict(list)
    for source, entries in by_source.items():
        filename = source_to_file.get(source, f'{source.lower()}.json')
        by_file[filename].extend(entries)
        print(f"  {source}: {len(entries)} entries → {filename}")
    
    # Write separate files
    print(f"\n📝 Writing {len(by_file)} JSON files...")
    for filename, entries in by_file.items():
        filepath = os.path.join(app_data_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(entries, f, indent=2)
        print(f"  ✅ {filepath} ({len(entries)} entries)")
    
    print(f"\n✨ Split complete! Created {len(by_file)} category files.")
    print(f"🔄 Field names converted from camelCase to snake_case for frontend.")

if __name__ == "__main__":
    split_enriched_data()
