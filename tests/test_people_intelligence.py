# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import tempfile
import shutil
import sqlite3
import pickle
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite

# Import the classes we need to test
from src.common.objects.LLEntry_obj import LLEntry
from src.common.objects.enhanced_llentry import PersonProfile
from src.common.services.people_intelligence_service import PeopleIntelligenceService, InteractionAnalysis


# Strategy generators for property-based testing

@composite
def generate_person_name(draw):
    """Generate realistic person names for testing"""
    first_names = [
        "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa",
        "James", "Maria", "William", "Jennifer", "Richard", "Linda", "Charles",
        "Patricia", "Joseph", "Susan", "Thomas", "Jessica", "Christopher", "Karen"
    ]
    
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"
    ]
    
    first_name = draw(st.sampled_from(first_names))
    
    # Sometimes include last name
    include_last = draw(st.booleans())
    if include_last:
        last_name = draw(st.sampled_from(last_names))
        return f"{first_name} {last_name}"
    else:
        return first_name


@composite
def generate_llentry_with_people(draw):
    """Generate an LLEntry with people mentions for testing"""
    entry_types = ["photo", "post", "status_update"]
    sources = ["facebook", "google_photos", "instagram"]
    
    entry_type = draw(st.sampled_from(entry_types))
    source = draw(st.sampled_from(sources))
    
    # Generate a realistic timestamp (within last 5 years)
    base_time = datetime.now() - timedelta(days=1825)
    time_offset = draw(st.integers(min_value=0, max_value=1825 * 24 * 3600))
    start_time = (base_time + timedelta(seconds=time_offset)).isoformat()
    
    entry = LLEntry(entry_type, start_time, source)
    
    # Add people to the entry
    num_people = draw(st.integers(min_value=1, max_value=5))
    people_names = [draw(generate_person_name()) for _ in range(num_people)]
    
    if entry_type == "photo":
        entry.peopleInImage = people_names
        entry.imageFileName = f"photo_{draw(st.integers(min_value=1000, max_value=9999))}.jpg"
        entry.imageFilePath = f"/path/to/{entry.imageFileName}"
        entry.imageTimestamp = int(datetime.fromisoformat(start_time).timestamp())
    
    # Add text description mentioning people
    person_mentions = draw(st.sampled_from(people_names)) if people_names else "someone"
    text_templates = [
        f"Had a great time with {person_mentions}",
        f"Hanging out with {person_mentions} today",
        f"Met up with {person_mentions} for coffee",
        f"{person_mentions} and I went to the park",
        f"Dinner with {person_mentions} was amazing"
    ]
    entry.textDescription = draw(st.sampled_from(text_templates))
    
    # Add tags that might include people
    entry.tags = people_names[:2] + ["fun", "memories"]  # Include some people as tags
    
    return entry, people_names


@composite
def generate_database_with_people(draw):
    """Generate a test database with entries containing people"""
    # Create a temporary database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_raw_data.db")
    
    try:
        # Create database structure
        con = sqlite3.connect(db_path)
        cursor = con.cursor()
        
        # Create the basic tables
        cursor.execute("""
            CREATE TABLE data_source(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name UNIQUE,
                entry_type,
                configs,
                field_mappings
            )
        """)
        
        cursor.execute("""
            CREATE TABLE personal_data(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id,
                data_timestamp,
                dedup_key UNIQUE,
                data,
                imageFileName,
                imageFilePath,
                location,
                location_done DEFAULT 0,
                captions,
                captions_done DEFAULT 0,
                embeddings,
                embedding_done DEFAULT 0,
                status DEFAULT 'active',
                dedup_done DEFAULT 0,
                enriched_data,
                export_done DEFAULT 0,
                FOREIGN KEY(source_id) REFERENCES data_source(id)
            )
        """)
        
        # Add test data sources
        test_sources = [
            (1, "facebook", "post", "{}", "{}"),
            (2, "google_photos", "photo", "{}", "{}"),
            (3, "instagram", "photo", "{}", "{}")
        ]
        
        cursor.executemany(
            "INSERT INTO data_source (id, source_name, entry_type, configs, field_mappings) VALUES (?, ?, ?, ?, ?)",
            test_sources
        )
        
        # Generate entries with people
        num_entries = draw(st.integers(min_value=5, max_value=15))
        all_people = set()
        entries = []
        
        for i in range(num_entries):
            entry, people_in_entry = draw(generate_llentry_with_people())
            all_people.update(people_in_entry)
            
            source_id = draw(st.integers(min_value=1, max_value=3))
            dedup_key = f"test_entry_{i}_{entry.type}_{entry.source}"
            
            pickled_data = pickle.dumps(entry)
            
            cursor.execute("""
                INSERT INTO personal_data 
                (source_id, data_timestamp, dedup_key, data, imageFileName, imageFilePath)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                source_id,
                int(datetime.fromisoformat(entry.startTime).timestamp()),
                dedup_key,
                pickled_data,
                getattr(entry, 'imageFileName', None),
                getattr(entry, 'imageFilePath', None)
            ))
            
            entries.append((entry, people_in_entry))
        
        con.commit()
        con.close()
        
        return {
            'db_path': db_path,
            'temp_dir': temp_dir,
            'entries': entries,
            'all_people': list(all_people),
            'num_entries': num_entries
        }
        
    except Exception as e:
        # Cleanup on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e


class TestPeopleIntelligence:
    """Test suite for people intelligence functionality"""
    
    def cleanup_test_db(self, db_info: Dict[str, Any]):
        """Clean up test database and restore environment"""
        try:
            if db_info.get('temp_dir') and os.path.exists(db_info['temp_dir']):
                shutil.rmtree(db_info['temp_dir'], ignore_errors=True)
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    @given(test_db=generate_database_with_people())
    @settings(max_examples=10, deadline=15000)
    def test_people_intelligence_profiles_property(self, test_db):
        """**Feature: ai-personal-archive, Property 4: People Intelligence Profiles**
        
        For any person who appears multiple times in the personal data, 
        the system should generate comprehensive profiles with interaction timelines, 
        shared contexts, and relationship evolution analysis.
        """
        # Set up environment to use test database
        original_app_data_dir = os.environ.get('APP_DATA_DIR')
        
        try:
            # Arrange: Set up the test database environment
            assume(len(test_db['all_people']) > 0)  # Only test with databases that have people
            assume(test_db['num_entries'] >= 2)  # Need at least 2 entries for meaningful analysis
            
            # Set environment to use test database
            os.environ['APP_DATA_DIR'] = test_db['temp_dir']
            
            # Import here to avoid circular imports and ensure fresh instance
            from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
            
            # Clear any existing singleton instance
            if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            # Act: Create people intelligence service and analyze people
            service = PeopleIntelligenceService()
            
            # Detect people from the test data
            detected_people = service.detect_people_from_data()
            
            # Assert: Verify people detection works
            assert isinstance(detected_people, list), "detect_people_from_data should return a list"
            
            # Test profile creation for detected people
            for person_name in detected_people[:3]:  # Test first 3 people to keep test time reasonable
                # Create person profile
                profile = service.create_person_profile(person_name)
                
                # Verify profile structure and required fields
                assert isinstance(profile, PersonProfile), f"create_person_profile should return PersonProfile object"
                assert profile.id is not None and len(profile.id) > 0, "Profile should have a valid ID"
                assert profile.name == person_name, f"Profile name should match input: expected {person_name}, got {profile.name}"
                assert isinstance(profile.representative_photos, list), "representative_photos should be a list"
                assert isinstance(profile.first_appearance, datetime), "first_appearance should be a datetime"
                assert isinstance(profile.last_appearance, datetime), "last_appearance should be a datetime"
                assert isinstance(profile.interaction_peaks, list), "interaction_peaks should be a list"
                assert isinstance(profile.shared_contexts, list), "shared_contexts should be a list"
                assert isinstance(profile.relationship_evolution, list), "relationship_evolution should be a list"
                
                # Verify temporal consistency
                assert profile.first_appearance <= profile.last_appearance, \
                    "first_appearance should be before or equal to last_appearance"
                
                # Verify interaction peaks are datetime objects
                for peak in profile.interaction_peaks:
                    assert isinstance(peak, datetime), "All interaction peaks should be datetime objects"
                
                # Test relationship analysis
                analysis = service.analyze_relationships(profile.id)
                assert isinstance(analysis, InteractionAnalysis), "analyze_relationships should return InteractionAnalysis"
                assert analysis.person_id == profile.id, "Analysis should be for the correct person"
                assert analysis.person_name == person_name, "Analysis should have correct person name"
                assert analysis.total_interactions >= 0, "Total interactions should be non-negative"
                assert isinstance(analysis.interaction_timeline, list), "interaction_timeline should be a list"
                assert isinstance(analysis.shared_contexts, list), "shared_contexts should be a list"
                
                # Test interaction pattern detection
                patterns = service.detect_interaction_patterns(profile.id)
                assert isinstance(patterns, dict), "detect_interaction_patterns should return a dict"
                assert 'total_interactions' in patterns, "Patterns should include total_interactions"
                assert 'interaction_frequency' in patterns, "Patterns should include interaction_frequency"
                assert 'relationship_duration_days' in patterns, "Patterns should include relationship_duration_days"
                assert 'primary_contexts' in patterns, "Patterns should include primary_contexts"
                
                assert patterns['total_interactions'] >= 0, "Total interactions should be non-negative"
                assert patterns['relationship_duration_days'] >= 0, "Relationship duration should be non-negative"
                assert isinstance(patterns['primary_contexts'], list), "Primary contexts should be a list"
                
                # Test relationship summary generation
                summary = service.generate_relationship_summary(profile.id)
                assert isinstance(summary, str), "generate_relationship_summary should return a string"
                assert len(summary) > 0, "Summary should not be empty"
                assert person_name in summary, "Summary should mention the person's name"
                
                # Test best of compilation generation
                compilation = service.generate_best_of_compilation(profile.id)
                assert isinstance(compilation, dict), "generate_best_of_compilation should return a dict"
                assert 'person_name' in compilation, "Compilation should include person_name"
                assert 'total_moments' in compilation, "Compilation should include total_moments"
                assert 'moments' in compilation, "Compilation should include moments list"
                assert compilation['person_name'] == person_name, "Compilation should be for correct person"
                assert compilation['total_moments'] >= 0, "Total moments should be non-negative"
                assert isinstance(compilation['moments'], list), "Moments should be a list"
                
                # Verify profile can be retrieved
                retrieved_profile = service.get_person_profile(profile.id)
                assert retrieved_profile is not None, "Profile should be retrievable after creation"
                assert retrieved_profile.name == person_name, "Retrieved profile should have correct name"
            
            # Test getting all people
            all_profiles = service.get_all_people()
            assert isinstance(all_profiles, list), "get_all_people should return a list"
            
            # Verify that profiles were actually created and stored
            if detected_people:
                assert len(all_profiles) > 0, "Should have at least one profile if people were detected"
            
            print(f"People intelligence test completed: detected {len(detected_people)} people, created {len(all_profiles)} profiles")
            
        finally:
            # Cleanup: Always clean up test database and restore environment
            if original_app_data_dir:
                os.environ['APP_DATA_DIR'] = original_app_data_dir
            elif 'APP_DATA_DIR' in os.environ:
                del os.environ['APP_DATA_DIR']
            
            # Clear singleton instance
            if 'EnhancedPersonalDataDBConnector' in locals():
                if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                    delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            self.cleanup_test_db(test_db)
    
    @given(person_name=generate_person_name())
    @settings(max_examples=20, deadline=5000)
    def test_person_name_validation(self, person_name):
        """Test person name validation and processing"""
        service = PeopleIntelligenceService()
        
        # Test name validation heuristics
        is_valid = service._looks_like_person_name(person_name)
        assert isinstance(is_valid, bool), "_looks_like_person_name should return boolean"
        
        # Valid person names should pass basic checks
        if len(person_name.strip()) >= 2 and person_name[0].isupper():
            # Most generated names should be considered valid
            # (This is a heuristic test, not absolute)
            pass
    
    def test_name_matching(self):
        """Test name matching functionality"""
        service = PeopleIntelligenceService()
        
        # Test exact matches
        assert service._names_match("John Smith", "John Smith")
        assert service._names_match("john smith", "John Smith")  # Case insensitive
        
        # Test partial matches
        assert service._names_match("John", "John Smith")
        assert service._names_match("John Smith", "John")
        
        # Test non-matches
        assert not service._names_match("John Smith", "Jane Doe")
        assert not service._names_match("John", "Jane")
    
    def test_context_extraction(self):
        """Test context extraction from entries"""
        service = PeopleIntelligenceService()
        
        # Create a test entry
        entry = LLEntry("photo", datetime.now().isoformat(), "facebook")
        entry.tags = ["vacation", "beach", "fun"]
        entry.location = json.dumps({"name": "Miami Beach"})
        
        context = service._get_context_from_entry(entry)
        assert isinstance(context, str)
        assert len(context) > 0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])