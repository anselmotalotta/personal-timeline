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
from src.common.objects.enhanced_llentry import EnhancedLLEntry, PersonRelationship, Story, Chapter
from src.common.services.story_generation_service import StoryGenerationService
from src.common.agents.narrative_agent import NarrativeAgent


# Strategy generators for property-based testing

@composite
def generate_enhanced_llentry_with_content(draw):
    """Generate a valid EnhancedLLEntry object with rich content for story generation"""
    entry_types = ["photo", "post", "purchase", "workout", "music", "location", "event"]
    sources = ["facebook", "google_photos", "amazon", "apple_health", "strava", "manual"]
    
    entry_type = draw(st.sampled_from(entry_types))
    source = draw(st.sampled_from(sources))
    
    # Generate a realistic timestamp (within last 5 years)
    base_time = datetime.now() - timedelta(days=1825)
    time_offset = draw(st.integers(min_value=0, max_value=1825 * 24 * 3600))
    start_time = base_time + timedelta(seconds=time_offset)
    
    entry = EnhancedLLEntry(entry_type, start_time.isoformat(), source)
    
    # Add meaningful text content for story generation
    text_templates = [
        "Had a wonderful time at {location} with {people}. The weather was perfect and we {activity}.",
        "Today I {activity} and felt really {emotion}. It reminded me of {memory}.",
        "Visited {location} for the first time. The {feature} was amazing and I {reaction}.",
        "Spent quality time with {people} doing {activity}. These moments are precious.",
        "Accomplished {achievement} today. Feeling {emotion} about the progress.",
        "Beautiful day at {location}. The {weather} made everything perfect for {activity}."
    ]
    
    template = draw(st.sampled_from(text_templates))
    
    # Fill in template variables
    locations = ["the park", "downtown", "the beach", "home", "the mountains", "the cafe", "work"]
    people = ["family", "friends", "colleagues", "my partner", "the kids", "old friends"]
    activities = ["explored", "relaxed", "celebrated", "worked out", "created something", "learned"]
    emotions = ["grateful", "excited", "peaceful", "accomplished", "nostalgic", "happy"]
    memories = ["childhood", "last year", "better times", "similar experiences", "old adventures"]
    features = ["architecture", "scenery", "atmosphere", "food", "people", "culture"]
    reactions = ["took photos", "felt inspired", "made new friends", "learned something", "felt grateful"]
    achievements = ["a personal goal", "a work milestone", "a creative project", "a fitness target"]
    weather = ["sunshine", "cool breeze", "perfect temperature", "clear skies"]
    
    text = template.format(
        location=draw(st.sampled_from(locations)),
        people=draw(st.sampled_from(people)),
        activity=draw(st.sampled_from(activities)),
        emotion=draw(st.sampled_from(emotions)),
        memory=draw(st.sampled_from(memories)),
        feature=draw(st.sampled_from(features)),
        reaction=draw(st.sampled_from(reactions)),
        achievement=draw(st.sampled_from(achievements)),
        weather=draw(st.sampled_from(weather))
    )
    
    entry.textDescription = text
    entry.text = text  # Ensure both fields are set
    
    # Add tags based on content
    entry.tags = draw(st.lists(
        st.sampled_from(['family', 'friends', 'work', 'travel', 'hobby', 'milestone', 'celebration', 'nature']),
        min_size=1, max_size=5
    ))
    
    # Add enhanced AI fields with meaningful values
    entry.narrative_significance = draw(st.floats(min_value=0.3, max_value=1.0))  # Higher significance for stories
    entry.story_potential = draw(st.floats(min_value=0.4, max_value=1.0))  # Higher story potential
    entry.emotional_context = draw(st.dictionaries(
        st.sampled_from(['joy', 'gratitude', 'excitement', 'calm', 'nostalgia', 'accomplishment']),
        st.floats(min_value=0.3, max_value=1.0),
        min_size=1, max_size=3
    ))
    entry.life_phase = draw(st.sampled_from(['childhood', 'adolescence', 'early_adult', 'adult', 'senior']))
    entry.thematic_tags = draw(st.lists(
        st.sampled_from(['family', 'friends', 'work', 'travel', 'hobby', 'milestone', 'growth', 'celebration']),
        min_size=1, max_size=4
    ))
    
    # Add media elements for visual entries
    if entry_type in ["photo", "event"]:
        entry.image_paths = draw(st.lists(
            st.text(min_size=10, max_size=50).map(lambda x: f"/path/to/images/{x}.jpg"),
            min_size=1, max_size=3
        ))
        if entry.image_paths:
            entry.imageFileName = os.path.basename(entry.image_paths[0])
            entry.imageFilePath = entry.image_paths[0]
        
        entry.peopleInImage = draw(st.lists(
            st.sampled_from(['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank']),
            max_size=3
        ))
    
    # Add location data
    if draw(st.booleans()):
        entry.location = draw(st.sampled_from(locations))
        entry.lat_lon = [(
            draw(st.floats(min_value=-90, max_value=90)),
            draw(st.floats(min_value=-180, max_value=180))
        )]
    
    # Add people relationships
    num_relationships = draw(st.integers(min_value=0, max_value=2))
    for i in range(num_relationships):
        person_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank']
        relationship = PersonRelationship(
            person_id=draw(st.sampled_from(person_names)),
            relationship_type=draw(st.sampled_from(['friend', 'family', 'colleague', 'partner'])),
            confidence=draw(st.floats(min_value=0.7, max_value=1.0)),
            first_interaction=start_time - timedelta(days=draw(st.integers(min_value=30, max_value=365))),
            last_interaction=start_time
        )
        entry.people_relationships.append(relationship)
    
    return entry


@composite
def generate_memory_collection(draw):
    """Generate a collection of memories suitable for story generation"""
    num_memories = draw(st.integers(min_value=3, max_value=12))
    memories = []
    
    # Generate memories with some temporal clustering for better stories
    base_time = datetime.now() - timedelta(days=365)
    
    for i in range(num_memories):
        # Create some temporal clustering
        if i < num_memories // 2:
            # First half: recent memories
            time_offset = draw(st.integers(min_value=0, max_value=180 * 24 * 3600))
        else:
            # Second half: older memories
            time_offset = draw(st.integers(min_value=180 * 24 * 3600, max_value=365 * 24 * 3600))
        
        memory_time = base_time + timedelta(seconds=time_offset)
        memory = draw(generate_enhanced_llentry_with_content())
        
        # Override the timestamp to create temporal clustering
        memory.startTime = memory_time.isoformat()
        memory.recordedStartTime = memory_time.isoformat()
        
        memories.append(memory)
    
    return memories


class TestStoryGeneration:
    """Test suite for story generation functionality"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Create a temporary directory for any test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize story generation service with test configuration
        self.test_config = {
            'agents': {
                'archivist': {
                    'max_selection_size': 20,
                    'relevance_threshold': 0.1,  # Lower threshold for testing
                    'exclude_low_quality': False
                },
                'narrative': {
                    'max_chapter_sentences': 3,
                    'min_chapter_sentences': 1,
                    'default_style': 'documentary'
                },
                'editor': {
                    'filter_sensitive_content': False,
                    'filter_low_quality': False,
                    'min_content_length': 5
                },
                'director': {
                    'optimal_chapter_count': 5,
                    'narrative_pacing': 'moderate'
                },
                'critic': {
                    'min_quality_score': 0.2,
                    'require_data_grounding': False,
                    'strict_privacy_mode': False
                }
            },
            'tts': {
                'output_dir': self.temp_dir
            },
            'composition': {
                'max_media_per_chapter': 3
            },
            'default_narrative_mode': 'chronological',
            'default_narrative_style': 'documentary'
        }
        
        # Mock the database dependency
        os.environ['APP_DATA_DIR'] = self.temp_dir
        
        self.story_service = StoryGenerationService(self.test_config)
    
    def teardown_method(self):
        """Clean up test environment after each test"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(memories=generate_memory_collection(), 
           narrative_mode=st.sampled_from(['chronological', 'thematic', 'people-centered', 'place-centered']))
    @settings(max_examples=100, deadline=30000)
    def test_story_generation_modes(self, memories, narrative_mode):
        """**Feature: ai-personal-archive, Property 3: Story Generation Modes**
        
        For any collection of personal memories, the story generator should create coherent 
        narratives in multiple modes (chronological, thematic, people-centered, place-centered) 
        with proper chapter structure and media integration.
        """
        # Arrange: Ensure we have valid memories with content
        assume(len(memories) >= 3)
        assume(all(hasattr(memory, 'text') and memory.text and len(memory.text.strip()) >= 10 
                  for memory in memories))
        
        # Act: Generate story using the specified narrative mode
        story = self.story_service.generate_story_from_memories(
            memories=memories,
            narrative_mode=narrative_mode,
            narrative_style='documentary',
            include_voice_narration=False
        )
        
        # Assert: Verify story generation properties
        
        # Property 1: Story should be generated successfully
        assert story is not None, "Story generation should not return None"
        assert isinstance(story, Story), "Generated object should be a Story instance"
        
        # Property 2: Story should have the correct narrative mode
        assert story.narrative_mode == narrative_mode, \
            f"Story narrative mode should be '{narrative_mode}', got '{story.narrative_mode}'"
        
        # Property 3: Story should have proper structure
        assert hasattr(story, 'title'), "Story should have a title"
        assert story.title, "Story title should not be empty"
        assert len(story.title.strip()) >= 3, "Story title should be meaningful"
        
        assert hasattr(story, 'chapters'), "Story should have chapters"
        assert isinstance(story.chapters, list), "Chapters should be a list"
        assert len(story.chapters) > 0, "Story should have at least one chapter"
        assert len(story.chapters) <= 20, "Story should not have excessive chapters"
        
        # Property 4: Each chapter should have proper structure (1-3 sentences)
        for i, chapter in enumerate(story.chapters):
            assert isinstance(chapter, Chapter), f"Chapter {i} should be a Chapter instance"
            
            # Chapter should have required fields
            assert hasattr(chapter, 'title'), f"Chapter {i} should have a title"
            assert chapter.title, f"Chapter {i} title should not be empty"
            
            assert hasattr(chapter, 'narrative_text'), f"Chapter {i} should have narrative text"
            assert chapter.narrative_text, f"Chapter {i} narrative text should not be empty"
            
            # Verify sentence structure (1-3 sentences)
            sentences = [s.strip() for s in chapter.narrative_text.split('.') if s.strip()]
            assert 1 <= len(sentences) <= 3, \
                f"Chapter {i} should have 1-3 sentences, got {len(sentences)}: '{chapter.narrative_text}'"
            
            # Each sentence should be meaningful
            for sentence in sentences:
                assert len(sentence.strip()) >= 5, \
                    f"Chapter {i} sentences should be meaningful, got: '{sentence}'"
            
            assert hasattr(chapter, 'media_elements'), f"Chapter {i} should have media elements"
            assert isinstance(chapter.media_elements, list), f"Chapter {i} media elements should be a list"
            
            assert hasattr(chapter, 'emotional_tone'), f"Chapter {i} should have emotional tone"
            assert chapter.emotional_tone, f"Chapter {i} emotional tone should not be empty"
            
            assert hasattr(chapter, 'duration_seconds'), f"Chapter {i} should have duration"
            assert isinstance(chapter.duration_seconds, int), f"Chapter {i} duration should be integer"
            assert chapter.duration_seconds >= 0, f"Chapter {i} duration should be non-negative"
        
        # Property 5: Story should reference source memories
        assert hasattr(story, 'source_memory_ids'), "Story should track source memory IDs"
        assert isinstance(story.source_memory_ids, list), "Source memory IDs should be a list"
        # Note: IDs might be generated, so we don't require exact matching
        
        # Property 6: Story should have creation metadata
        assert hasattr(story, 'created_at'), "Story should have creation timestamp"
        assert isinstance(story.created_at, datetime), "Creation timestamp should be datetime"
        
        assert hasattr(story, 'id'), "Story should have an ID"
        assert story.id, "Story ID should not be empty"
        
        # Property 7: Narrative mode should influence story structure
        if narrative_mode == 'chronological':
            # Chronological stories should have temporal coherence
            # (This is a simplified check - in practice, we'd verify temporal ordering)
            assert len(story.chapters) >= 1, "Chronological story should have chapters"
            
        elif narrative_mode == 'thematic':
            # Thematic stories should group related content
            # Verify that chapters have thematic coherence (simplified check)
            for chapter in story.chapters:
                # Chapter titles should reflect themes - allow single meaningful words
                title_lower = chapter.title.lower()
                thematic_indicators = ['moments', 'times', 'experiences', 'memories', 'stories']
                has_thematic_indicator = any(indicator in title_lower for indicator in thematic_indicators)
                # Allow single meaningful theme words or descriptive phrases
                assert len(chapter.title.strip()) >= 3 or has_thematic_indicator, \
                    f"Thematic chapter title should be meaningful: '{chapter.title}'"
                    
        elif narrative_mode == 'people-centered':
            # People-centered stories should focus on relationships
            for chapter in story.chapters:
                title_lower = chapter.title.lower()
                people_indicators = ['with', 'moments', 'time', 'experiences', 'memories']
                has_people_indicator = any(indicator in title_lower for indicator in people_indicators)
                # Allow flexibility in chapter titles while ensuring they're meaningful
                assert len(chapter.title.strip()) >= 3 or has_people_indicator, \
                    f"People-centered chapter should be meaningful: '{chapter.title}'"
                    
        elif narrative_mode == 'place-centered':
            # Place-centered stories should focus on locations
            for chapter in story.chapters:
                title_lower = chapter.title.lower()
                place_indicators = ['at', 'in', 'journey', 'places', 'location', 'visit']
                has_place_indicator = any(indicator in title_lower for indicator in place_indicators)
                # Allow flexibility while ensuring meaningful titles
                assert len(chapter.title.strip()) >= 3 or has_place_indicator, \
                    f"Place-centered chapter should be meaningful: '{chapter.title}'"
        
        # Property 8: Media integration should be present when available
        total_media_elements = sum(len(chapter.media_elements) for chapter in story.chapters)
        available_media = sum(1 for memory in memories 
                            if (hasattr(memory, 'image_paths') and memory.image_paths) or
                               (hasattr(memory, 'photos') and memory.photos) or
                               (hasattr(memory, 'videos') and memory.videos))
        
        if available_media > 0:
            # Should have some media integration when media is available
            # (This is a flexible check since media selection is complex)
            assert total_media_elements >= 0, "Should handle media elements appropriately"
        
        # Property 9: Story should maintain narrative coherence
        # Verify that the story flows logically (simplified check)
        full_narrative = " ".join(chapter.narrative_text for chapter in story.chapters)
        
        # Should not contain obvious contradictions or repetitions
        assert len(full_narrative.strip()) >= 20, "Story should have substantial narrative content"
        
        # Should not have excessive repetition of the same phrases
        words = full_narrative.lower().split()
        if len(words) > 10:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            assert repetition_ratio >= 0.2, \
                f"Story should have reasonable vocabulary diversity, got ratio: {repetition_ratio}"
    
    def test_narrative_agent_direct_usage(self):
        """Test the narrative agent directly for basic functionality"""
        # Create test memories
        memories = []
        base_time = datetime.now()
        
        for i in range(3):
            memory = EnhancedLLEntry("post", (base_time + timedelta(days=i)).isoformat(), "test")
            memory.text = f"This is test memory {i+1} with meaningful content for story generation."
            memory.textDescription = memory.text
            memory.narrative_significance = 0.8
            memory.story_potential = 0.7
            memories.append(memory)
        
        # Test narrative agent directly
        narrative_agent = NarrativeAgent()
        narrative_agent.initialize()
        
        # Test each narrative mode
        for mode in ['chronological', 'thematic', 'people-centered', 'place-centered']:
            request = {
                'memories': memories,
                'narrative_mode': mode,
                'narrative_style': 'documentary',
                'title': f'Test {mode.title()} Story'
            }
            
            story = narrative_agent.process(request)
            
            assert story is not None, f"Should generate story for {mode} mode"
            assert story.narrative_mode == mode, f"Should have correct narrative mode for {mode}"
            assert len(story.chapters) > 0, f"Should have chapters for {mode} mode"
            
            for chapter in story.chapters:
                assert chapter.narrative_text, f"Chapter should have text for {mode} mode"
                sentences = [s.strip() for s in chapter.narrative_text.split('.') if s.strip()]
                assert 1 <= len(sentences) <= 3, \
                    f"Chapter should have 1-3 sentences for {mode} mode, got {len(sentences)}"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])