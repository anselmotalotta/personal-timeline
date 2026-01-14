#!/usr/bin/env python3
"""
Minimal test to identify required dependencies for personal-timeline
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 70)
print("TESTING CORE IMPORTS")
print("=" * 70)

# Test core Python imports
try:
    import json
    import sqlite3
    import csv
    import datetime
    print("✅ Core Python libs: json, sqlite3, csv, datetime")
except ImportError as e:
    print(f"❌ Core Python libs failed: {e}")
    sys.exit(1)

# Test third-party imports one by one
dependencies = {
    'pandas': 'pandas',
    'numpy': 'numpy',
    'tqdm': 'tqdm',
    'pytz': 'pytz',
    'flask': 'flask',
    'flask-cors': 'flask_cors',
    'Pillow': 'PIL',
    'requests': 'requests',
    'geopy': 'geopy',
}

failed = []
for package_name, import_name in dependencies.items():
    try:
        __import__(import_name)
        print(f"✅ {package_name}")
    except ImportError as e:
        print(f"❌ {package_name}: {e}")
        failed.append(package_name)

# Test optional/heavy dependencies
optional_deps = {
    'torch': 'torch',
    'transformers': 'transformers',
    'openai': 'openai',
    'langchain': 'langchain',
    'sentence-transformers': 'sentence_transformers',
    'clip': 'clip',
    'faiss-cpu': 'faiss',
}

print("\n" + "=" * 70)
print("TESTING OPTIONAL/HEAVY DEPENDENCIES")
print("=" * 70)

for package_name, import_name in optional_deps.items():
    try:
        __import__(import_name)
        print(f"✅ {package_name}")
    except ImportError as e:
        print(f"⚠️  {package_name}: Not installed (optional)")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
if failed:
    print(f"❌ Missing required dependencies: {', '.join(failed)}")
    sys.exit(1)
else:
    print("✅ All required dependencies available!")
    print("\n🎯 Ready to test Facebook importer...")

# Try importing the Facebook importer
try:
    from src.ingest.importers.create_facebook_LLEntries import FacebookPhotosImporter
    print("✅ Facebook importer loaded successfully!")
except Exception as e:
    print(f"❌ Facebook importer failed: {e}")
    import traceback
    traceback.print_exc()
