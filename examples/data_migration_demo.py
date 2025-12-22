#!/usr/bin/env python3
"""
Demo script showing the enhanced data model and migration capabilities.

This script demonstrates:
1. Creating enhanced LLEntry objects
2. Using the enhanced database schema
3. Migration from legacy to enhanced format
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up a temporary directory for the demo
temp_dir = tempfile.mkdtemp()
os.environ['APP_DATA_DIR'] = temp_dir

try:
    from src.common.objects.LLEntry_obj import LLEntry
    from src.common.objects.enhanced_llentry import (
        EnhancedLLEntry, Story, PersonProfile, Gallery, CompositeMemory, Chapter
    )
    from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
    from src.common.migration.database_migrator import DatabaseMigrator

    print("=== AI-Augmented Personal Archive - Data Model Demo ===\n")

    # 1. Create a legacy LLEntry
    print("1. Creating a legacy LLEntry object...")
    legacy_entry = LLEntry("photo", datetime.now().isoformat(), "google_photos")
    legacy_entry.textDescription = "Beautiful sunset at the beach"
    legacy_entry.imageFileName = "sunset_beach.jpg"
    legacy_entry.imageFilePath = "/photos/2024/sunset_beach.jpg"
    legacy_entry.peopleInImage = ["Alice", "Bob"]
    legacy_entry.tags = ["sunset", "beach", "vacation"]
    
    print(f"   Legacy entry: {legacy_entry.type} from {legacy_entry.source}")
    print(f"   Description: {legacy_entry.textDescription}")
    print(f"   People: {legacy_entry.peopleInImage}")

    # 2. Convert to enhanced format
    print("\n2. Converting to enhanced format...")
    enhanced_entry = EnhancedLLEntry.from_llentry(legacy_entry)
    enhanced_entry.narrative_significance = 0.8
    enhanced_entry.emotional_context = {"joy": 0.9, "nostalgia": 0.7}
    enhanced_entry.life_phase = "young_adult_adventures"
    enhanced_entry.thematic_tags = ["friendship", "nature", "memories"]
    enhanced_entry.story_potential = 0.9
    
    print(f"   Enhanced entry with AI fields:")
    print(f"   - Narrative significance: {enhanced_entry.narrative_significance}")
    print(f"   - Emotional context: {enhanced_entry.emotional_context}")
    print(f"   - Life phase: {enhanced_entry.life_phase}")
    print(f"   - Story potential: {enhanced_entry.story_potential}")

    # 3. Initialize enhanced database
    print("\n3. Initializing enhanced database...")
    db = EnhancedPersonalDataDBConnector()
    print(f"   Database schema version: {db.get_schema_version()}")
    print(f"   Data integrity verified: {db.verify_data_integrity()}")

    # 4. Create AI-focused data structures
    print("\n4. Creating AI-focused data structures...")
    
    # Create a story
    chapter = Chapter(
        id="ch1",
        title="Beach Memories",
        narrative_text="The golden hour painted the sky in brilliant oranges and pinks as friends gathered to watch the sunset.",
        media_elements=["/photos/2024/sunset_beach.jpg"],
        duration_seconds=30,
        emotional_tone="nostalgic"
    )
    
    story = Story(
        id="story1",
        title="Summer Adventures",
        narrative_mode="thematic",
        chapters=[chapter],
        source_memory_ids=["entry1"],
        created_at=datetime.now()
    )
    
    print(f"   Created story: '{story.title}' with {len(story.chapters)} chapters")
    
    # Create a person profile
    person_profile = PersonProfile(
        id="person1",
        name="Alice",
        representative_photos=["/photos/alice_1.jpg"],
        first_appearance=datetime(2020, 1, 1),
        last_appearance=datetime.now(),
        interaction_peaks=[datetime(2023, 6, 15), datetime(2024, 8, 20)],
        shared_contexts=["beach trips", "college friends", "photography"],
        relationship_evolution=[
            {"period": "college", "relationship": "classmate"},
            {"period": "post_grad", "relationship": "close_friend"}
        ]
    )
    
    print(f"   Created person profile: '{person_profile.name}' with {len(person_profile.shared_contexts)} shared contexts")
    
    # Create a gallery
    gallery = Gallery(
        id="gallery1",
        title="Beach Memories",
        description="A collection of beautiful beach moments with friends",
        memory_ids=["entry1", "entry2", "entry3"],
        creation_method="thematic",
        semantic_ordering=[0, 2, 1],  # Optimal display order
        created_at=datetime.now()
    )
    
    print(f"   Created gallery: '{gallery.title}' with {len(gallery.memory_ids)} memories")
    
    # Create a composite memory
    composite_memory = CompositeMemory(
        id="composite1",
        theme="Summer Beach Adventures",
        constituent_memory_ids=["entry1", "entry2", "entry3"],
        narrative_summary="A series of beach visits that defined a summer of friendship and discovery.",
        temporal_span=(datetime(2024, 6, 1), datetime(2024, 8, 31)),
        significance_score=0.85
    )
    
    print(f"   Created composite memory: '{composite_memory.theme}' (significance: {composite_memory.significance_score})")

    # 5. Store in database
    print("\n5. Storing AI data structures in database...")
    db.add_story(story)
    db.add_person_profile(person_profile)
    db.add_gallery(gallery)
    db.add_composite_memory(composite_memory)
    
    print("   All data structures stored successfully!")

    # 6. Retrieve and display
    print("\n6. Retrieving data from enhanced database...")
    stories = db.get_stories(limit=5)
    profiles = db.get_person_profiles()
    
    print(f"   Retrieved {len(stories)} stories and {len(profiles)} person profiles")
    
    if stories:
        print(f"   First story: '{stories[0]['title']}' ({stories[0]['narrative_mode']} mode)")
    
    if profiles:
        print(f"   First profile: '{profiles[0]['name']}' (first seen: {profiles[0]['first_appearance']})")

    print("\n=== Demo completed successfully! ===")
    print(f"Enhanced database created at: {temp_dir}/raw_data.db")
    print("The database includes:")
    print("- Enhanced personal_data table with AI fields")
    print("- New tables: stories, person_profiles, galleries, composite_memories")
    print("- Migration tracking with schema_migrations table")

except Exception as e:
    print(f"Demo failed with error: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Cleanup
    if 'temp_dir' in locals():
        print(f"\nCleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Restore environment
    if 'APP_DATA_DIR' in os.environ:
        del os.environ['APP_DATA_DIR']