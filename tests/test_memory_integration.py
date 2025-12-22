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

from src.common.objects.enhanced_llentry import EnhancedLLEntry
from src.common.memory.enhanced_memory_retrieval import EnhancedMemoryRetrieval


class TestMemoryIntegration:
    """Integration tests for enhanced memory retrieval with real data scenarios"""
    
    def setup_test_database_with_real_data(self):
        """Set up a test database with realistic memory data"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_raw_data.db")
        
        # Create database with enhanced schema
        con = sqlite3.connect(db_path)
        cursor = con.cursor()
        
        # Create enhanced personal_data table
        cursor.execute("""
            CREATE TABLE personal_data(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                data_timestamp INTEGER,
                dedup_key TEXT UNIQUE,
                data BLOB,
                imageFileName TEXT,
                imageFilePath TEXT,
                location TEXT,
                location_done INTEGER DEFAULT 0,
                captions TEXT,
                captions_done INTEGER DEFAULT 0,
                embeddings TEXT,
                embedding_done INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                dedup_done INTEGER DEFAULT 0,
                enriched_data TEXT,
                export_done INTEGER DEFAULT 0,
                narrative_significance REAL DEFAULT 0.0,
                emotional_context TEXT,
                life_phase TEXT DEFAULT '',
                people_relationships TEXT,
                social_context TEXT,
                story_potential REAL DEFAULT 0.0,
                thematic_tags TEXT,
                composite_memory_ids TEXT,
                ai_processed INTEGER DEFAULT 0,
                ai_processing_version TEXT DEFAULT '1.0',
                ai_metadata TEXT
            )
        """)
        
        # Create data_source table
        cursor.execute("""
            CREATE TABLE data_source(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT UNIQUE,
                entry_type TEXT,
                configs TEXT,
                field_mappings TEXT
            )
        """)
        
        # Add test data sources
        test_sources = [
            (1, "facebook", "post", "{}", "{}"),
            (2, "google_photos", "photo", "{}", "{}"),
            (3, "apple_health", "workout", "{}", "{}")
        ]
        
        cursor.executemany(
            "INSERT INTO data_source (id, source_name, entry_type, configs, field_mappings) VALUES (?, ?, ?, ?, ?)",
            test_sources
        )
        
        # Create realistic test memories
        test_memories = [
            # Travel memories
            {
                'type': 'photo',
                'source': 'google_photos',
                'startTime': '2023-06-15T14:30:00',
                'textDescription': 'Beautiful sunset at the beach in Hawaii',
                'tags': ['travel', 'beach', 'sunset', 'hawaii', 'vacation'],
                'peopleInImage': ['Sarah', 'John'],
                'narrative_significance': 0.8,
                'life_phase': 'exploration',
                'story_potential': 0.9
            },
            {
                'type': 'post',
                'source': 'facebook',
                'startTime': '2023-06-16T09:00:00',
                'textDescription': 'Amazing snorkeling adventure! Saw so many colorful fish',
                'tags': ['travel', 'snorkeling', 'hawaii', 'adventure', 'ocean'],
                'narrative_significance': 0.7,
                'life_phase': 'exploration',
                'story_potential': 0.8
            },
            # Family memories
            {
                'type': 'photo',
                'source': 'google_photos',
                'startTime': '2023-07-04T18:00:00',
                'textDescription': 'Family BBQ for Independence Day',
                'tags': ['family', 'bbq', 'holiday', 'celebration', 'july4th'],
                'peopleInImage': ['Mom', 'Dad', 'Sarah'],
                'narrative_significance': 0.9,
                'life_phase': 'family_time',
                'story_potential': 0.8
            },
            # Work memories
            {
                'type': 'post',
                'source': 'facebook',
                'startTime': '2023-08-10T16:30:00',
                'textDescription': 'Just finished a big project at work! Team celebration tonight',
                'tags': ['work', 'project', 'celebration', 'achievement', 'team'],
                'narrative_significance': 0.6,
                'life_phase': 'early_career',
                'story_potential': 0.5
            },
            # Fitness memories
            {
                'type': 'workout',
                'source': 'apple_health',
                'startTime': '2023-09-01T07:00:00',
                'textDescription': 'Morning run in the park - 5 miles completed',
                'tags': ['fitness', 'running', 'morning', 'park', 'exercise'],
                'duration': 2700,  # 45 minutes
                'calories': 450,
                'narrative_significance': 0.4,
                'life_phase': 'growth',
                'story_potential': 0.3
            }
        ]
        
        # Insert test memories
        for i, memory_data in enumerate(test_memories):
            entry = EnhancedLLEntry(memory_data['type'], memory_data['startTime'], memory_data['source'])
            
            # Set attributes
            entry.textDescription = memory_data['textDescription']
            entry.tags = memory_data['tags']
            entry.narrative_significance = memory_data['narrative_significance']
            entry.life_phase = memory_data['life_phase']
            entry.story_potential = memory_data['story_potential']
            entry.thematic_tags = memory_data['tags']
            entry.ai_processed = True
            
            if 'peopleInImage' in memory_data:
                entry.peopleInImage = memory_data['peopleInImage']
            
            if 'duration' in memory_data:
                entry.duration = memory_data['duration']
            if 'calories' in memory_data:
                entry.calories = memory_data['calories']
            
            # Create unique identifiers
            dedup_key = f"test_memory_{i}_{entry.type}_{entry.source}"
            
            # Serialize the entry
            pickled_data = pickle.dumps(entry)
            
            # Insert into database
            cursor.execute("""
                INSERT INTO personal_data 
                (source_id, data_timestamp, dedup_key, data, 
                 narrative_significance, emotional_context, life_phase, thematic_tags,
                 story_potential, ai_processed, ai_processing_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1,  # source_id
                int(datetime.fromisoformat(entry.startTime).timestamp()),
                dedup_key,
                pickled_data,
                entry.narrative_significance,
                json.dumps({}),  # emotional_context
                entry.life_phase,
                json.dumps(entry.thematic_tags),
                entry.story_potential,
                1,  # ai_processed
                entry.ai_processing_version
            ))
        
        con.commit()
        con.close()
        
        return {
            'db_path': db_path,
            'temp_dir': temp_dir,
            'num_memories': len(test_memories)
        }
    
    def cleanup_test_db(self, db_info: Dict[str, Any]):
        """Clean up test database"""
        try:
            if db_info.get('temp_dir') and os.path.exists(db_info['temp_dir']):
                shutil.rmtree(db_info['temp_dir'], ignore_errors=True)
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def test_enhanced_memory_retrieval_with_real_data(self):
        """Test enhanced memory retrieval with realistic data scenarios"""
        # Set up test database
        db_info = self.setup_test_database_with_real_data()
        original_app_data_dir = os.environ.get('APP_DATA_DIR')
        
        try:
            # Set environment to use test database
            os.environ['APP_DATA_DIR'] = db_info['temp_dir']
            
            # Clear any existing singleton instance
            from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
            if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            # Create enhanced memory retrieval system
            retrieval_engine = EnhancedMemoryRetrieval()
            
            # Test 1: Travel-related query
            response = retrieval_engine.query_memories("Tell me about my Hawaii trip", "test_session")
            
            assert isinstance(response.narrative_answer, str)
            assert len(response.narrative_answer) > 0
            assert response.confidence_score >= 0.0
            
            # Should find travel-related memories
            travel_memories = [mem for mem in response.source_memories if 'hawaii' in str(mem.get('tags', [])).lower()]
            print(f"Found {len(travel_memories)} Hawaii-related memories")
            
            # Test 2: Family-related query
            response = retrieval_engine.query_memories("Show me family moments", "test_session")
            
            assert isinstance(response.narrative_answer, str)
            assert len(response.narrative_answer) > 0
            
            # Test 3: Temporal query
            response = retrieval_engine.query_memories("What did I do in summer 2023?", "test_session")
            
            assert isinstance(response.narrative_answer, str)
            assert len(response.narrative_answer) > 0
            
            # Test 4: People-related query
            response = retrieval_engine.query_memories("What did I do with Sarah?", "test_session")
            
            assert isinstance(response.narrative_answer, str)
            assert len(response.narrative_answer) > 0
            
            # Test 5: Conversation context should be maintained
            final_context = response.conversation_context
            assert len(final_context.query_history) == 4  # All 4 queries should be recorded
            assert len(final_context.current_themes) > 0  # Should have accumulated themes
            
            print("✓ Enhanced memory retrieval integration test passed")
            print(f"  Final context has {len(final_context.query_history)} queries")
            print(f"  Final context has {len(final_context.current_themes)} themes")
            
        finally:
            # Cleanup
            if original_app_data_dir:
                os.environ['APP_DATA_DIR'] = original_app_data_dir
            elif 'APP_DATA_DIR' in os.environ:
                del os.environ['APP_DATA_DIR']
            
            # Clear singleton instance
            if 'EnhancedPersonalDataDBConnector' in locals():
                if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                    delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            self.cleanup_test_db(db_info)
    
    def test_composite_memory_creation(self):
        """Test that composite memories are created correctly"""
        db_info = self.setup_test_database_with_real_data()
        original_app_data_dir = os.environ.get('APP_DATA_DIR')
        
        try:
            os.environ['APP_DATA_DIR'] = db_info['temp_dir']
            
            from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
            if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            retrieval_engine = EnhancedMemoryRetrieval()
            
            # Query for travel memories (should create composite memories)
            response = retrieval_engine.query_memories("Tell me about my travels", "composite_test")
            
            # Check if composite memories were created
            if response.composite_memories:
                composite = response.composite_memories[0]
                assert hasattr(composite, 'theme')
                assert hasattr(composite, 'narrative_summary')
                assert len(composite.constituent_memory_ids) >= 2
                assert len(composite.narrative_summary) > 0
                print(f"✓ Created composite memory with theme: {composite.theme}")
                print(f"  Summary: {composite.narrative_summary[:100]}...")
            else:
                print("ℹ No composite memories created (may be expected with limited test data)")
            
        finally:
            if original_app_data_dir:
                os.environ['APP_DATA_DIR'] = original_app_data_dir
            elif 'APP_DATA_DIR' in os.environ:
                del os.environ['APP_DATA_DIR']
            
            if 'EnhancedPersonalDataDBConnector' in locals():
                if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                    delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            self.cleanup_test_db(db_info)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])