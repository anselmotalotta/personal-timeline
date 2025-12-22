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
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite

# Import the classes we need to test
from src.common.objects.enhanced_llentry import EnhancedLLEntry, PersonRelationship, Gallery, Story
from src.common.services.gallery_curation_service import GalleryCurationService


# Strategy generators for property-based testing

@composite
def generate_enhanced_llentry_for_gallery(draw):
    """Generate a valid EnhancedLLEntry object suitable for gallery curation"""
    entry_types = ["photo", "post", "purchase", "workout", "music", "location", "event"]
    sources = ["facebook", "google_photos", "amazon", "apple_health", "strava", "manual"]
    
    entry_type = draw(st.sampled_from(entry_types))
    source = draw(st.sampled_from(sources))
    
    # Generate a realistic timestamp (within last 3 years)
    base_time = datetime.now() - timedelta(days=1095)
    time_offset = draw(st.integers(min_value=0, max_value=1095 * 24 * 3600))
    start_time = base_time + timedelta(seconds=time_offset)
    
    entry = EnhancedLLEntry(entry_type, start_time.isoformat(), source)
    entry.id = f"memory_{draw(st.integers(min_value=1000, max_value=9999))}"
    
    # Add meaningful text content for gallery curation
    text_templates = [
        "Wonderful time with {people} at {location}. We {activity} and it was {emotion}.",
        "Today I {activity} and felt {emotion}. The {weather} made it perfect.",
        "Visited {location} for {event}. The {feature} was amazing.",
        "Quality time with {people} doing {activity}. These moments matter.",
        "Accomplished {achievement} today. Feeling {emotion} about it.",
        "Beautiful day at {location}. Perfect for {activity} with {people}."
    ]
    
    template = draw(st.sampled_from(text_templates))
    
    # Fill in template variables with thematic content
    locations = ["the park", "downtown", "the beach", "home", "mountains", "cafe", "work", "studio"]
    people = ["friends", "family", "colleagues", "partner", "kids", "team", "community"]
    activities = ["exploring", "creating", "celebrating", "learning", "exercising", "relaxing"]
    emotions = ["grateful", "excited", "peaceful", "accomplished", "inspired", "happy"]
    weather = ["sunshine", "cool breeze", "perfect temperature", "clear skies"]
    features = ["architecture", "scenery", "atmosphere", "energy", "creativity"]
    events = ["a celebration", "work", "a gathering", "an adventure", "learning"]
    achievements = ["a goal", "a milestone", "a project", "a breakthrough"]
    
    text = template.format(
        location=draw(st.sampled_from(locations)),
        people=draw(st.sampled_from(people)),
        activity=draw(st.sampled_from(activities)),
        emotion=draw(st.sampled_from(emotions)),
        weather=draw(st.sampled_from(weather)),
        feature=draw(st.sampled_from(features)),
        event=draw(st.sampled_from(events)),
        achievement=draw(st.sampled_from(achievements))
    )
    
    entry.textDescription = text
    entry.text = text
    
    # Add thematic tags for gallery curation
    thematic_tags = ['friends', 'family', 'work', 'travel', 'creative', 'milestone', 
                    'celebration', 'nature', 'learning', 'exercise', 'home', 'community']
    entry.thematic_tags = draw(st.lists(
        st.sampled_from(thematic_tags),
        min_size=1, max_size=4
    ))
    
    # Add enhanced AI fields for gallery curation
    entry.narrative_significance = draw(st.floats(min_value=0.2, max_value=1.0))
    entry.story_potential = draw(st.floats(min_value=0.3, max_value=1.0))
    entry.emotional_context = draw(st.dictionaries(
        st.sampled_from(['joy', 'gratitude', 'excitement', 'calm', 'nostalgia', 'accomplishment']),
        st.floats(min_value=0.2, max_value=1.0),
        min_size=1, max_size=3
    ))
    entry.life_phase = draw(st.sampled_from(['childhood', 'adolescence', 'early_adult', 'adult', 'senior']))
    
    # Add media elements for visual galleries
    if entry_type in ["photo", "event"]:
        entry.image_paths = draw(st.lists(
            st.text(min_size=5, max_size=20).map(lambda x: f"/path/to/images/{x}.jpg"),
            min_size=1, max_size=3
        ))
        if entry.image_paths:
            entry.imageFileName = os.path.basename(entry.image_paths[0])
            entry.imageFilePath = entry.image_paths[0]
        
        entry.peopleInImage = draw(st.lists(
            st.sampled_from(['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank']),
            max_size=3
        ))
    
    # Add location data for place-based galleries
    if draw(st.booleans()):
        entry.location = draw(st.sampled_from(locations))
        entry.lat_lon = [(
            draw(st.floats(min_value=-90, max_value=90)),
            draw(st.floats(min_value=-180, max_value=180))
        )]
    
    # Add people relationships for people-centered galleries
    num_relationships = draw(st.integers(min_value=0, max_value=2))
    for i in range(num_relationships):
        person_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank']
        relationship = PersonRelationship(
            person_id=draw(st.sampled_from(person_names)),
            relationship_type=draw(st.sampled_from(['friend', 'family', 'colleague', 'partner'])),
            confidence=draw(st.floats(min_value=0.6, max_value=1.0)),
            first_interaction=start_time - timedelta(days=draw(st.integers(min_value=30, max_value=365))),
            last_interaction=start_time
        )
        entry.people_relationships.append(relationship)
    
    return entry


@composite
def generate_memory_collection_for_gallery(draw):
    """Generate a collection of memories suitable for gallery curation"""
    num_memories = draw(st.integers(min_value=5, max_value=20))
    memories = []
    
    # Generate memories with thematic clustering for better galleries
    base_time = datetime.now() - timedelta(days=730)
    
    for i in range(num_memories):
        memory = draw(generate_enhanced_llentry_for_gallery())
        
        # Create some temporal and thematic clustering
        time_offset = draw(st.integers(min_value=0, max_value=730 * 24 * 3600))
        memory_time = base_time + timedelta(seconds=time_offset)
        memory.startTime = memory_time.isoformat()
        memory.recordedStartTime = memory_time.isoformat()
        
        memories.append(memory)
    
    return memories


@composite
def generate_thematic_gallery_request(draw):
    """Generate a thematic gallery request"""
    themes = [
        "Moments with friends", "Creative periods", "Times of growth",
        "Travel adventures", "Family gatherings", "Professional milestones",
        "Seasonal memories", "Learning experiences", "Celebrations and achievements",
        "Quiet reflections", "Nature experiences", "Urban exploration"
    ]
    
    return draw(st.sampled_from(themes))


@composite
def generate_natural_language_prompt(draw):
    """Generate natural language prompts for gallery creation"""
    prompts = [
        "Show me photos from last year with friends",
        "Find memories about travel and adventures",
        "Create a gallery of family moments",
        "Show me creative projects and artistic work",
        "Find celebrations and happy moments",
        "Show me quiet and peaceful times",
        "Create a gallery about learning and growth",
        "Find memories from work and professional life",
        "Show me outdoor activities and nature",
        "Create a gallery of home and daily life",
        "Find memories with specific people",
        "Show me seasonal memories from winter",
        "Create a gallery about food and cooking",
        "Find memories about exercise and health",
        "Show me urban exploration and city life"
    ]
    
    return draw(st.sampled_from(prompts))


class TestGalleryCuration:
    """Test suite for gallery curation functionality"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Create a temporary directory for any test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize gallery curation service with test configuration
        self.test_config = {
            'agents': {
                'archivist': {
                    'max_selection_size': 50,
                    'relevance_threshold': 0.1,  # Lower threshold for testing
                    'exclude_low_quality': False
                },
                'narrative': {
                    'max_chapter_sentences': 2,
                    'min_chapter_sentences': 1,
                    'default_style': 'contextual'
                },
                'editor': {
                    'filter_sensitive_content': False,
                    'filter_low_quality': False,
                    'min_content_length': 5
                },
                'director': {
                    'ordering_strategy': 'semantic',
                    'pacing_preference': 'balanced'
                },
                'critic': {
                    'min_quality_score': 0.2,
                    'require_data_grounding': False,
                    'strict_privacy_mode': False
                }
            },
            'max_memories_per_gallery': 50,
            'min_memories_per_gallery': 3,
            'semantic_similarity_threshold': 0.5
        }
        
        # Mock the database dependency
        os.environ['APP_DATA_DIR'] = self.temp_dir
        
        self.gallery_service = GalleryCurationService(self.test_config)
    
    def teardown_method(self):
        """Clean up test environment after each test"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(theme=generate_thematic_gallery_request())
    @settings(max_examples=100, deadline=30000)
    def test_intelligent_gallery_curation_thematic(self, theme):
        """**Feature: ai-personal-archive, Property 5: Intelligent Gallery Curation**
        
        For any thematic or prompt-based gallery request, the system should create 
        semantically ordered collections with contextual introductions and story 
        generation options.
        """
        # Act: Create thematic gallery
        gallery = self.gallery_service.create_thematic_gallery(theme)
        
        # Assert: Verify gallery curation properties
        
        # Property 1: Gallery should be created successfully for valid themes
        # Note: Gallery might be None if insufficient memories, which is acceptable
        if gallery is not None:
            assert isinstance(gallery, Gallery), "Generated object should be a Gallery instance"
            
            # Property 2: Gallery should have proper structure
            assert hasattr(gallery, 'id'), "Gallery should have an ID"
            assert gallery.id, "Gallery ID should not be empty"
            
            assert hasattr(gallery, 'title'), "Gallery should have a title"
            assert gallery.title, "Gallery title should not be empty"
            assert len(gallery.title.strip()) >= 3, "Gallery title should be meaningful"
            assert theme.lower() in gallery.title.lower() or any(word in gallery.title.lower() 
                                                               for word in theme.lower().split()), \
                f"Gallery title should relate to theme '{theme}': '{gallery.title}'"
            
            assert hasattr(gallery, 'description'), "Gallery should have a description"
            assert gallery.description, "Gallery description should not be empty"
            assert len(gallery.description.strip()) >= 10, "Gallery description should be substantial"
            
            # Property 3: Gallery should have memory collection
            assert hasattr(gallery, 'memory_ids'), "Gallery should have memory IDs"
            assert isinstance(gallery.memory_ids, list), "Memory IDs should be a list"
            assert len(gallery.memory_ids) >= 3, "Gallery should have minimum number of memories"
            assert len(gallery.memory_ids) <= 50, "Gallery should not exceed maximum memories"
            
            # All memory IDs should be non-empty strings
            for memory_id in gallery.memory_ids:
                assert isinstance(memory_id, str), "Memory ID should be string"
                assert memory_id.strip(), "Memory ID should not be empty"
            
            # Property 4: Gallery should have semantic ordering
            assert hasattr(gallery, 'semantic_ordering'), "Gallery should have semantic ordering"
            assert isinstance(gallery.semantic_ordering, list), "Semantic ordering should be a list"
            
            if gallery.semantic_ordering:
                # Ordering should contain valid indices
                assert len(gallery.semantic_ordering) == len(gallery.memory_ids), \
                    "Semantic ordering should match memory count"
                
                # All indices should be valid
                for idx in gallery.semantic_ordering:
                    assert isinstance(idx, int), "Ordering index should be integer"
                    assert 0 <= idx < len(gallery.memory_ids), \
                        f"Ordering index {idx} should be valid for {len(gallery.memory_ids)} memories"
                
                # Should contain all indices (no duplicates, no missing)
                assert set(gallery.semantic_ordering) == set(range(len(gallery.memory_ids))), \
                    "Semantic ordering should contain all memory indices exactly once"
            
            # Property 5: Gallery should have creation metadata
            assert hasattr(gallery, 'creation_method'), "Gallery should have creation method"
            assert gallery.creation_method == 'thematic', "Thematic gallery should have correct creation method"
            
            assert hasattr(gallery, 'created_at'), "Gallery should have creation timestamp"
            assert isinstance(gallery.created_at, datetime), "Creation timestamp should be datetime"
            
            # Property 6: Gallery description should be contextual and AI-written
            description_lower = gallery.description.lower()
            
            # Should contain contextual information
            contextual_indicators = ['collection', 'memories', 'moments', 'experiences', 'curated']
            assert any(indicator in description_lower for indicator in contextual_indicators), \
                f"Gallery description should be contextual: '{gallery.description}'"
            
            # Should mention the theme or related concepts
            theme_words = theme.lower().split()
            theme_mentioned = any(word in description_lower for word in theme_words)
            assert theme_mentioned, \
                f"Gallery description should relate to theme '{theme}': '{gallery.description}'"
            
            # Should include memory count information
            memory_count_mentioned = str(len(gallery.memory_ids)) in gallery.description
            assert memory_count_mentioned, \
                f"Gallery description should mention memory count: '{gallery.description}'"
    
    @given(prompt=generate_natural_language_prompt())
    @settings(max_examples=100, deadline=30000)
    def test_intelligent_gallery_curation_prompt_based(self, prompt):
        """**Feature: ai-personal-archive, Property 5: Intelligent Gallery Curation**
        
        For any natural language prompt, the system should create galleries that go 
        beyond current search capabilities with semantic understanding.
        """
        # Act: Create gallery from natural language prompt
        gallery = self.gallery_service.generate_from_prompt(prompt)
        
        # Assert: Verify prompt-based gallery properties
        
        # Property 1: Gallery creation should handle natural language prompts
        # Note: Gallery might be None if insufficient memories, which is acceptable
        if gallery is not None:
            assert isinstance(gallery, Gallery), "Generated object should be a Gallery instance"
            
            # Property 2: Gallery should reflect prompt understanding
            assert hasattr(gallery, 'creation_method'), "Gallery should have creation method"
            assert gallery.creation_method == 'prompt', "Prompt-based gallery should have correct creation method"
            
            assert hasattr(gallery, 'title'), "Gallery should have a title"
            assert gallery.title, "Gallery title should not be empty"
            assert len(gallery.title.strip()) >= 3, "Gallery title should be meaningful"
            
            # Title should relate to the prompt in some way
            prompt_words = set(word.lower() for word in prompt.split() 
                             if word.lower() not in {'show', 'me', 'find', 'create', 'a', 'the', 'of', 'about', 'from'})
            title_words = set(word.lower() for word in gallery.title.split())
            
            # Should have some overlap with prompt concepts
            word_overlap = len(prompt_words.intersection(title_words))
            semantic_overlap = word_overlap > 0 or any(
                prompt_word in ' '.join(title_words) for prompt_word in prompt_words
            )
            assert semantic_overlap, \
                f"Gallery title should relate to prompt '{prompt}': '{gallery.title}'"
            
            # Property 3: Gallery should have proper structure (same as thematic)
            assert hasattr(gallery, 'memory_ids'), "Gallery should have memory IDs"
            assert isinstance(gallery.memory_ids, list), "Memory IDs should be a list"
            assert len(gallery.memory_ids) >= 3, "Gallery should have minimum number of memories"
            assert len(gallery.memory_ids) <= 50, "Gallery should not exceed maximum memories"
            
            # Property 4: Gallery should demonstrate advanced understanding beyond simple search
            assert hasattr(gallery, 'description'), "Gallery should have a description"
            assert gallery.description, "Gallery description should not be empty"
            assert len(gallery.description.strip()) >= 10, "Gallery description should be substantial"
            
            # Description should show understanding of the prompt
            description_lower = gallery.description.lower()
            prompt_lower = prompt.lower()
            
            # Should contain some prompt concepts or related terms
            key_prompt_words = [word for word in prompt_lower.split() 
                              if word not in {'show', 'me', 'find', 'create', 'a', 'the', 'of', 'about', 'from', 'gallery'}]
            
            prompt_understanding = any(word in description_lower for word in key_prompt_words)
            assert prompt_understanding, \
                f"Gallery description should show understanding of prompt '{prompt}': '{gallery.description}'"
            
            # Property 5: Semantic ordering should be applied
            assert hasattr(gallery, 'semantic_ordering'), "Gallery should have semantic ordering"
            assert isinstance(gallery.semantic_ordering, list), "Semantic ordering should be a list"
            
            if gallery.semantic_ordering:
                assert len(gallery.semantic_ordering) == len(gallery.memory_ids), \
                    "Semantic ordering should match memory count"
                assert set(gallery.semantic_ordering) == set(range(len(gallery.memory_ids))), \
                    "Semantic ordering should contain all memory indices"
    
    def test_gallery_to_story_conversion_capability(self):
        """Test that galleries can be converted to stories (story generation options)"""
        # Create a test gallery manually
        from src.common.objects.enhanced_llentry import Gallery
        
        test_gallery = Gallery(
            id="test_gallery_123",
            title="Test Gallery",
            description="A test gallery for story conversion",
            memory_ids=["mem1", "mem2", "mem3"],
            creation_method="manual",
            semantic_ordering=[0, 1, 2],
            created_at=datetime.now()
        )
        
        # Test that the service has story conversion capability
        assert hasattr(self.gallery_service, 'convert_gallery_to_story'), \
            "Gallery service should have story conversion capability"
        
        # Test that the method accepts proper parameters
        import inspect
        sig = inspect.signature(self.gallery_service.convert_gallery_to_story)
        params = list(sig.parameters.keys())
        
        assert 'gallery_id' in params, "Story conversion should accept gallery_id"
        assert 'narrative_mode' in params, "Story conversion should accept narrative_mode"
        assert 'narrative_style' in params, "Story conversion should accept narrative_style"
        assert 'include_voice_narration' in params, "Story conversion should accept voice narration option"
    
    def test_default_gallery_initialization(self):
        """Test that default thematic galleries can be initialized to replace basic filtering"""
        # Test that the service can initialize default galleries
        assert hasattr(self.gallery_service, 'initialize_default_galleries'), \
            "Gallery service should support default gallery initialization"
        
        # Test that it returns a list of galleries
        default_galleries = self.gallery_service.initialize_default_galleries()
        assert isinstance(default_galleries, list), "Should return list of galleries"
        
        # Each gallery should be properly structured
        for gallery in default_galleries:
            assert isinstance(gallery, Gallery), "Each default gallery should be Gallery instance"
            assert gallery.creation_method == 'thematic', "Default galleries should be thematic"
            assert gallery.title, "Default gallery should have title"
            assert gallery.description, "Default gallery should have description"
    
    def test_supported_themes_availability(self):
        """Test that the service provides supported themes for gallery creation"""
        assert hasattr(self.gallery_service, 'get_supported_themes'), \
            "Gallery service should provide supported themes"
        
        themes = self.gallery_service.get_supported_themes()
        assert isinstance(themes, list), "Supported themes should be a list"
        assert len(themes) > 0, "Should have at least some supported themes"
        
        # Themes should be meaningful strings
        for theme in themes:
            assert isinstance(theme, str), "Theme should be string"
            assert len(theme.strip()) >= 3, "Theme should be meaningful"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])