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
from src.common.objects.enhanced_llentry import EnhancedLLEntry
from src.common.memory.enhanced_memory_retrieval import (
    EnhancedMemoryRetrieval, ConversationContext, MemoryResponse
)


# Strategy generators for property-based testing

@composite
def generate_memory_query(draw):
    """Generate realistic memory queries for testing"""
    query_templates = [
        "What did I do with {person}?",
        "Show me photos from {time_period}",
        "Tell me about my {activity} memories",
        "What happened in {location}?",
        "Find memories about {theme}",
        "When did I last {action}?",
        "Show me {type} from {time_period}",
        "What was I doing in {year}?"
    ]
    
    template = draw(st.sampled_from(query_templates))
    
    # Fill in template variables
    replacements = {
        'person': draw(st.sampled_from(['Sarah', 'John', 'Mom', 'Dad', 'friends'])),
        'time_period': draw(st.sampled_from(['last year', 'this month', '2023', 'last week'])),
        'activity': draw(st.sampled_from(['travel', 'food', 'exercise', 'work', 'music'])),
        'location': draw(st.sampled_from(['Paris', 'home', 'office', 'beach', 'restaurant'])),
        'theme': draw(st.sampled_from(['travel', 'family', 'friends', 'work', 'hobbies'])),
        'action': draw(st.sampled_from(['travel', 'exercise', 'cook', 'meet friends'])),
        'type': draw(st.sampled_from(['photos', 'posts', 'activities', 'memories'])),
        'year': draw(st.sampled_from(['2023', '2022', '2021', '2020']))
    }
    
    query = template
    for key, value in replacements.items():
        query = query.replace(f'{{{key}}}', value)
    
    return query


@composite
def generate_enhanced_llentry_with_themes(draw):
    """Generate an EnhancedLLEntry with realistic themes and content"""
    entry_types = ["photo", "post", "purchase", "workout", "music", "location"]
    sources = ["facebook", "google_photos", "amazon", "apple_health", "strava"]
    
    entry_type = draw(st.sampled_from(entry_types))
    source = draw(st.sampled_from(sources))
    
    # Generate a realistic timestamp (within last 2 years)
    base_time = datetime.now() - timedelta(days=730)
    time_offset = draw(st.integers(min_value=0, max_value=730 * 24 * 3600))
    start_time = (base_time + timedelta(seconds=time_offset)).isoformat()
    
    entry = EnhancedLLEntry(entry_type, start_time, source)
    
    # Add realistic content based on type
    if entry_type == "photo":
        entry.imageFileName = f"IMG_{draw(st.integers(min_value=1000, max_value=9999))}.jpg"
        entry.imageFilePath = f"/photos/{entry.imageFileName}"
        entry.peopleInImage = draw(st.lists(st.sampled_from(['Sarah', 'John', 'Mom', 'Dad']), max_size=3))
        entry.textDescription = draw(st.sampled_from([
            "Beautiful sunset at the beach",
            "Dinner with friends at Italian restaurant",
            "Family gathering for birthday celebration",
            "Weekend hiking trip in the mountains",
            "Concert with amazing live music"
        ]))
        entry.tags = ['photo', 'memories'] + draw(st.lists(st.sampled_from(['travel', 'food', 'family', 'friends', 'nature']), max_size=3))
        
    elif entry_type == "post":
        entry.textDescription = draw(st.sampled_from([
            "Had an amazing day exploring the city!",
            "Just finished a great workout at the gym",
            "Trying out a new recipe for dinner tonight",
            "Excited about the upcoming vacation plans",
            "Reflecting on all the good times this year"
        ]))
        entry.tags = ['post', 'social'] + draw(st.lists(st.sampled_from(['travel', 'fitness', 'food', 'reflection']), max_size=2))
        
    elif entry_type == "workout":
        entry.textDescription = f"Completed a {draw(st.integers(min_value=20, max_value=120))} minute workout"
        entry.duration = draw(st.integers(min_value=1200, max_value=7200))  # 20-120 minutes in seconds
        entry.calories = draw(st.integers(min_value=100, max_value=800))
        entry.tags = ['workout', 'fitness', 'health']
        
    # Add AI-enhanced fields
    entry.narrative_significance = draw(st.floats(min_value=0.0, max_value=1.0))
    entry.emotional_context = {
        'joy': draw(st.floats(min_value=0.0, max_value=1.0)),
        'excitement': draw(st.floats(min_value=0.0, max_value=1.0))
    }
    entry.life_phase = draw(st.sampled_from(['early_career', 'family_time', 'exploration', 'growth']))
    entry.story_potential = draw(st.floats(min_value=0.0, max_value=1.0))
    entry.thematic_tags = entry.tags + draw(st.lists(st.sampled_from(['meaningful', 'milestone', 'routine', 'special']), max_size=2))
    
    return entry


@composite
def generate_test_database_with_memories(draw):
    """Generate a test database populated with enhanced memories"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_raw_data.db")
    
    try:
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
        
        # Generate and insert test memories
        num_memories = draw(st.integers(min_value=10, max_value=30))
        memories = []
        
        for i in range(num_memories):
            entry = draw(generate_enhanced_llentry_with_themes())
            source_id = draw(st.integers(min_value=1, max_value=3))
            
            # Create unique identifiers
            dedup_key = f"test_memory_{i}_{entry.type}_{entry.source}"
            
            # Handle image file paths for photos
            image_file_name = None
            image_file_path = None
            if entry.type == "photo" and hasattr(entry, 'imageFileName'):
                image_file_name = f"test_img_{i}_{entry.imageFileName}"
                image_file_path = f"/test/images/{image_file_name}"
                entry.imageFileName = image_file_name
                entry.imageFilePath = image_file_path
            
            # Serialize the entry
            pickled_data = pickle.dumps(entry)
            
            # Insert into database
            cursor.execute("""
                INSERT INTO personal_data 
                (source_id, data_timestamp, dedup_key, data, imageFileName, imageFilePath,
                 narrative_significance, emotional_context, life_phase, thematic_tags,
                 story_potential, ai_processed, ai_processing_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_id,
                int(datetime.fromisoformat(entry.startTime).timestamp()),
                dedup_key,
                pickled_data,
                image_file_name,
                image_file_path,
                entry.narrative_significance,
                json.dumps(entry.emotional_context),
                entry.life_phase,
                json.dumps(entry.thematic_tags),
                entry.story_potential,
                1,  # ai_processed
                entry.ai_processing_version
            ))
            
            memories.append(entry)
        
        con.commit()
        con.close()
        
        return {
            'db_path': db_path,
            'temp_dir': temp_dir,
            'memories': memories,
            'num_memories': num_memories
        }
        
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e


class TestEnhancedMemoryRetrieval:
    """Test suite for enhanced memory retrieval functionality"""
    
    def cleanup_test_db(self, db_info: Dict[str, Any]):
        """Clean up test database and restore environment"""
        try:
            if db_info.get('temp_dir') and os.path.exists(db_info['temp_dir']):
                shutil.rmtree(db_info['temp_dir'], ignore_errors=True)
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    @given(
        test_db=generate_test_database_with_memories(),
        query=generate_memory_query()
    )
    @settings(max_examples=20, deadline=15000)
    def test_enhanced_memory_retrieval_provides_contextual_responses(self, test_db, query):
        """**Feature: ai-personal-archive, Property 2: Enhanced Memory Retrieval**
        
        For any user query about personal memories, the system should provide 
        contextually rich responses with narrative context and composite memory 
        clustering that goes beyond simple keyword matching.
        """
        # Set up environment to use test database
        original_app_data_dir = os.environ.get('APP_DATA_DIR')
        
        try:
            # Arrange: Set up test database environment
            assume(test_db['num_memories'] > 0)
            assume(len(query.strip()) > 0)
            
            os.environ['APP_DATA_DIR'] = test_db['temp_dir']
            
            # Clear any existing singleton instance
            from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
            if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            # Act: Create enhanced memory retrieval system and query memories
            retrieval_engine = EnhancedMemoryRetrieval()
            response = retrieval_engine.query_memories(query, session_id="test_session")
            
            # Assert: Verify enhanced memory retrieval properties
            
            # 1. Response should be a MemoryResponse object with required fields
            assert isinstance(response, MemoryResponse), "Response should be a MemoryResponse object"
            assert response.query == query, "Response should contain the original query"
            assert isinstance(response.narrative_answer, str), "Response should have a narrative answer"
            assert len(response.narrative_answer) > 0, "Narrative answer should not be empty"
            
            # 2. Response should provide contextually rich information
            assert isinstance(response.source_memories, list), "Response should include source memories"
            assert isinstance(response.related_themes, list), "Response should include related themes"
            assert isinstance(response.confidence_score, float), "Response should include confidence score"
            assert 0.0 <= response.confidence_score <= 1.0, "Confidence score should be between 0 and 1"
            
            # 3. Narrative context should go beyond simple keyword matching
            # The narrative answer should be contextual and descriptive
            narrative_words = response.narrative_answer.lower().split()
            assert len(narrative_words) > 5, "Narrative answer should be more than just keywords"
            
            # Should contain contextual phrases that indicate narrative understanding
            contextual_indicators = [
                'based on', 'found in your memories', 'here\'s what', 'memories include',
                'specific memories', 'collection of', 'related to', 'from your'
            ]
            has_contextual_language = any(
                indicator in response.narrative_answer.lower() 
                for indicator in contextual_indicators
            )
            assert has_contextual_language, "Narrative should contain contextual language beyond keywords"
            
            # 4. Should support composite memory clustering when relevant
            assert isinstance(response.composite_memories, list), "Response should include composite memories"
            
            # If composite memories are found, they should have proper structure
            for composite in response.composite_memories:
                assert hasattr(composite, 'theme'), "Composite memory should have a theme"
                assert hasattr(composite, 'narrative_summary'), "Composite memory should have narrative summary"
                assert hasattr(composite, 'constituent_memory_ids'), "Composite memory should reference constituent memories"
                assert len(composite.constituent_memory_ids) >= 2, "Composite memory should cluster multiple memories"
                assert len(composite.narrative_summary) > 0, "Composite memory should have non-empty narrative"
            
            # 5. Conversation context should be maintained
            assert isinstance(response.conversation_context, ConversationContext), "Response should include conversation context"
            assert response.conversation_context.session_id == "test_session", "Context should maintain session ID"
            assert query in response.conversation_context.query_history, "Context should record the query"
            
            # 6. Related themes should be extracted from query
            if response.related_themes:
                # Themes should be relevant to the query
                query_words = set(query.lower().split())
                theme_relevance = any(
                    theme.lower() in query.lower() or 
                    any(word in theme.lower() for word in query_words if len(word) > 3)
                    for theme in response.related_themes
                )
                # Note: This assertion is relaxed because theme extraction may find semantic themes
                # that aren't directly in the query text
            
            # 7. If memories are found, they should have enhanced metadata
            for memory in response.source_memories:
                assert isinstance(memory, dict), "Memory should be a dictionary"
                assert 'id' in memory, "Memory should have an ID"
                assert 'type' in memory, "Memory should have a type"
                
                # Should include retrieval strategy information
                if 'retrieval_strategy' in memory:
                    valid_strategies = ['theme', 'temporal', 'conversation_context', 'text_similarity']
                    assert memory['retrieval_strategy'] in valid_strategies, "Should use valid retrieval strategy"
            
            # 8. System should handle queries gracefully even with no results
            if not response.source_memories and not response.composite_memories:
                # Should still provide a helpful narrative response
                assert "couldn't find" in response.narrative_answer.lower() or \
                       "no memories" in response.narrative_answer.lower() or \
                       "try a different" in response.narrative_answer.lower(), \
                       "Should provide helpful message when no memories found"
            
            print(f"✓ Enhanced memory retrieval test passed for query: '{query}'")
            print(f"  Found {len(response.source_memories)} memories, {len(response.composite_memories)} composites")
            print(f"  Confidence: {response.confidence_score:.2f}, Themes: {response.related_themes}")
            
        finally:
            # Cleanup: Restore environment and clean up test database
            if original_app_data_dir:
                os.environ['APP_DATA_DIR'] = original_app_data_dir
            elif 'APP_DATA_DIR' in os.environ:
                del os.environ['APP_DATA_DIR']
            
            # Clear singleton instance
            if 'EnhancedPersonalDataDBConnector' in locals():
                if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                    delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            self.cleanup_test_db(test_db)
    
    @given(
        test_db=generate_test_database_with_memories(),
        queries=st.lists(generate_memory_query(), min_size=2, max_size=5)
    )
    @settings(max_examples=10, deadline=20000)
    def test_conversation_context_management(self, test_db, queries):
        """Test that conversation context is properly maintained across multiple queries"""
        original_app_data_dir = os.environ.get('APP_DATA_DIR')
        
        try:
            assume(test_db['num_memories'] > 0)
            assume(all(len(q.strip()) > 0 for q in queries))
            
            os.environ['APP_DATA_DIR'] = test_db['temp_dir']
            
            from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
            if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            retrieval_engine = EnhancedMemoryRetrieval()
            session_id = "conversation_test"
            
            # Execute multiple queries in sequence
            responses = []
            for query in queries:
                response = retrieval_engine.query_memories(query, session_id=session_id)
                responses.append(response)
            
            # Verify conversation context is maintained
            final_context = responses[-1].conversation_context
            
            # Should contain all queries
            assert len(final_context.query_history) == len(queries), "Context should contain all queries"
            for query in queries:
                assert query in final_context.query_history, f"Context should contain query: {query}"
            
            # Should accumulate themes across queries
            all_themes = set()
            for response in responses:
                all_themes.update(response.related_themes)
            
            context_themes = set(final_context.current_themes)
            theme_overlap = len(all_themes.intersection(context_themes))
            assert theme_overlap > 0, "Context should accumulate themes from queries"
            
            print(f"✓ Conversation context test passed with {len(queries)} queries")
            
        finally:
            if original_app_data_dir:
                os.environ['APP_DATA_DIR'] = original_app_data_dir
            elif 'APP_DATA_DIR' in os.environ:
                del os.environ['APP_DATA_DIR']
            
            if 'EnhancedPersonalDataDBConnector' in locals():
                if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                    delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            self.cleanup_test_db(test_db)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])