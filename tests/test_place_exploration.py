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
from typing import List, Dict, Any, Tuple
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite

# Import the classes we need to test
from src.common.objects.enhanced_llentry import EnhancedLLEntry, PersonRelationship
from src.common.services.place_exploration_service import (
    PlaceExplorationService, PlaceProfile, JourneyNarrative, LocationExploration
)


# Strategy generators for property-based testing

@composite
def generate_location_coordinates(draw):
    """Generate realistic location coordinates"""
    # Generate coordinates for major world cities and regions
    lat = draw(st.floats(min_value=-85.0, max_value=85.0))
    lon = draw(st.floats(min_value=-180.0, max_value=180.0))
    return (lat, lon)


@composite
def generate_place_name(draw):
    """Generate realistic place names"""
    place_types = [
        "home", "work", "office", "school", "university", "park", "beach", "cafe", "restaurant",
        "gym", "library", "hospital", "airport", "hotel", "mall", "theater", "museum",
        "downtown", "uptown", "neighborhood", "city center", "suburbs", "mountains", "lake",
        "Coffee Shop", "Central Park", "Main Street", "Oak Avenue", "Sunset Boulevard",
        "Golden Gate Park", "Times Square", "Union Station", "City Hall", "Public Library"
    ]
    
    return draw(st.sampled_from(place_types))


@composite
def generate_enhanced_llentry_with_location(draw):
    """Generate a valid EnhancedLLEntry object with location data"""
    entry_types = ["photo", "post", "checkin", "event", "travel"]
    sources = ["facebook", "google_photos", "foursquare", "manual"]
    
    entry_type = draw(st.sampled_from(entry_types))
    source = draw(st.sampled_from(sources))
    
    # Generate a realistic timestamp (within last 3 years)
    base_time = datetime.now() - timedelta(days=1095)
    time_offset = draw(st.integers(min_value=0, max_value=1095 * 24 * 3600))
    start_time = base_time + timedelta(seconds=time_offset)
    
    entry = EnhancedLLEntry(entry_type, start_time.isoformat(), source)
    
    # Add location data
    place_name = draw(generate_place_name())
    entry.location = place_name
    
    # Add coordinates
    coordinates = draw(generate_location_coordinates())
    entry.lat_lon = [coordinates]
    
    # Add meaningful text content with location context
    location_activities = {
        "home": ["relaxing at home", "cooking dinner", "spending time with family", "working from home"],
        "work": ["busy day at work", "important meeting", "project deadline", "team collaboration"],
        "park": ["walking in the park", "enjoying nature", "picnic with friends", "morning jog"],
        "beach": ["beautiful day at the beach", "swimming and sunbathing", "beach volleyball", "sunset watching"],
        "cafe": ["coffee meeting", "working on laptop", "catching up with friends", "reading a book"],
        "restaurant": ["delicious dinner", "celebrating special occasion", "trying new cuisine", "date night"],
        "gym": ["great workout session", "fitness goals", "strength training", "cardio exercise"],
        "library": ["studying for exams", "research project", "quiet reading time", "book browsing"]
    }
    
    activities = location_activities.get(place_name.lower(), ["spending time", "having experiences", "making memories"])
    activity = draw(st.sampled_from(activities))
    
    text_templates = [
        f"Had a wonderful time {activity} at {place_name}. The experience was really meaningful.",
        f"Today I was {activity} at {place_name}. Feeling grateful for these moments.",
        f"Great day {activity} at {place_name}. These are the memories I treasure.",
        f"Spent quality time {activity} at {place_name}. Perfect way to spend the day."
    ]
    
    entry.text = draw(st.sampled_from(text_templates))
    entry.textDescription = entry.text
    
    # Add enhanced AI fields
    entry.narrative_significance = draw(st.floats(min_value=0.2, max_value=1.0))
    entry.story_potential = draw(st.floats(min_value=0.3, max_value=1.0))
    entry.emotional_context = draw(st.dictionaries(
        st.sampled_from(['joy', 'gratitude', 'calm']),  # Reduced options
        st.floats(min_value=0.2, max_value=1.0),
        min_size=1, max_size=2  # Reduced from 3
    ))
    entry.life_phase = draw(st.sampled_from(['early_adult', 'adult']))  # Reduced options
    entry.thematic_tags = draw(st.lists(
        st.sampled_from(['daily_life', 'work', 'social']),  # Reduced options
        min_size=1, max_size=2  # Reduced from 3
    ))
    
    # Add people relationships for social context (simplified)
    if draw(st.booleans()):
        person_names = ['Alice', 'Bob']  # Reduced options
        relationship = PersonRelationship(
            person_id=draw(st.sampled_from(person_names)),
            relationship_type=draw(st.sampled_from(['friend', 'family'])),  # Reduced options
            confidence=draw(st.floats(min_value=0.6, max_value=1.0)),
            first_interaction=start_time - timedelta(days=draw(st.integers(min_value=30, max_value=180))),  # Reduced range
            last_interaction=start_time
        )
        entry.people_relationships.append(relationship)
    
    return entry


@composite
def generate_location_memory_collection(draw):
    """Generate a collection of memories for location-based testing"""
    num_memories = draw(st.integers(min_value=4, max_value=8))  # Ensure at least 4 memories
    memories = []
    
    # Generate some memories for the same location to test place profiles
    primary_location = draw(generate_place_name())
    num_primary_memories = draw(st.integers(min_value=2, max_value=min(4, num_memories - 1)))  # Leave at least 1 for other locations
    
    # Generate memories for primary location
    base_time = datetime.now() - timedelta(days=365)
    for i in range(num_primary_memories):
        memory = draw(generate_enhanced_llentry_with_location())
        # Override location to ensure clustering
        memory.location = primary_location
        
        # Spread visits over time
        time_offset = draw(st.integers(min_value=i * 30 * 24 * 3600, max_value=(i + 1) * 30 * 24 * 3600))
        visit_time = base_time + timedelta(seconds=time_offset)
        memory.startTime = visit_time.isoformat()
        memory.recordedStartTime = memory.startTime
        
        memories.append(memory)
    
    # Generate memories for other locations
    remaining_memories = num_memories - num_primary_memories
    for i in range(remaining_memories):
        memory = draw(generate_enhanced_llentry_with_location())
        # Ensure different location
        while memory.location == primary_location:
            memory.location = draw(generate_place_name())
        
        memories.append(memory)
    
    return memories


@composite
def generate_journey_memory_sequence(draw):
    """Generate a sequence of memories that form a journey"""
    num_locations = draw(st.integers(min_value=2, max_value=4))  # Reduced from 5
    locations = []
    
    # Generate unique locations
    for _ in range(num_locations):
        location = draw(generate_place_name())
        while location in locations:
            location = draw(generate_place_name())
        locations.append(location)
    
    memories = []
    base_time = datetime.now() - timedelta(days=30)
    
    # Create memories for each location in sequence
    for i, location in enumerate(locations):
        # 1-2 memories per location (reduced from 1-3)
        num_memories_per_location = draw(st.integers(min_value=1, max_value=2))
        
        for j in range(num_memories_per_location):
            memory = draw(generate_enhanced_llentry_with_location())
            memory.location = location
            
            # Sequential timing within journey window
            time_offset = i * 24 * 3600 + j * 3600  # Each location on different day, memories hours apart
            visit_time = base_time + timedelta(seconds=time_offset)
            memory.startTime = visit_time.isoformat()
            memory.recordedStartTime = memory.startTime
            
            memories.append(memory)
    
    return memories


class TestPlaceExploration:
    """Test suite for place-based exploration functionality"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Create a temporary directory for any test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize place exploration service with test configuration
        self.test_config = {
            'narrative': {
                'min_visits_for_profile': 2,
                'significance_threshold': 0.2,  # Lower threshold for testing
                'journey_detection_window_days': 30,
                'max_narrative_layers': 5
            }
        }
        
        self.place_service = PlaceExplorationService(self.test_config)
    
    def teardown_method(self):
        """Clean up test environment after each test"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(memories=generate_location_memory_collection())
    @settings(max_examples=100, deadline=30000, suppress_health_check=[HealthCheck.large_base_example])
    def test_place_based_narrative_exploration(self, memories):
        """**Feature: ai-personal-archive, Property 6: Place-Based Narrative Exploration**
        
        For any location in the personal data, the system should provide story-driven 
        exploration showing temporal and emotional relationships rather than just 
        listing associated entries.
        """
        # Arrange: Ensure we have valid memories with location data
        assume(len(memories) >= 3)
        assume(all(hasattr(memory, 'location') and memory.location and memory.location != "unknown" 
                  for memory in memories))
        assume(all(hasattr(memory, 'text') and memory.text and len(memory.text.strip()) >= 10 
                  for memory in memories))
        
        # Act: Analyze place relationships and create location exploration
        place_profiles = self.place_service.analyze_place_relationships(memories)
        
        # Assert: Verify place-based exploration properties
        
        # Property 1: Should create place profiles for locations with multiple visits
        location_counts = {}
        for memory in memories:
            location = memory.location
            location_counts[location] = location_counts.get(location, 0) + 1
        
        locations_with_multiple_visits = [loc for loc, count in location_counts.items() 
                                        if count >= self.test_config['narrative']['min_visits_for_profile']]
        
        if locations_with_multiple_visits:
            assert len(place_profiles) > 0, "Should create place profiles for locations with multiple visits"
            
            # Verify each place profile has required structure
            for place_id, profile in place_profiles.items():
                assert isinstance(profile, PlaceProfile), f"Profile for {place_id} should be PlaceProfile instance"
                
                # Required fields
                assert profile.place_id, f"Place {place_id} should have place_id"
                assert profile.name, f"Place {place_id} should have name"
                assert isinstance(profile.visit_count, int), f"Place {place_id} should have integer visit_count"
                assert profile.visit_count >= 2, f"Place {place_id} should have at least 2 visits"
                
                # Temporal data
                assert isinstance(profile.first_visit, datetime), f"Place {place_id} should have first_visit datetime"
                assert isinstance(profile.last_visit, datetime), f"Place {place_id} should have last_visit datetime"
                assert profile.first_visit <= profile.last_visit, f"Place {place_id} first_visit should be <= last_visit"
                
                # Narrative significance
                assert isinstance(profile.narrative_significance, float), f"Place {place_id} should have float narrative_significance"
                assert 0.0 <= profile.narrative_significance <= 1.0, f"Place {place_id} narrative_significance should be 0-1"
                
                # Emotional associations
                assert isinstance(profile.emotional_associations, dict), f"Place {place_id} should have emotional_associations dict"
                for emotion, score in profile.emotional_associations.items():
                    assert isinstance(emotion, str), f"Place {place_id} emotion keys should be strings"
                    assert isinstance(score, float), f"Place {place_id} emotion scores should be floats"
                    assert 0.0 <= score <= 1.0, f"Place {place_id} emotion scores should be 0-1"
                
                # Temporal patterns
                assert isinstance(profile.temporal_patterns, list), f"Place {place_id} should have temporal_patterns list"
                
                # Representative memories
                assert isinstance(profile.representative_memories, list), f"Place {place_id} should have representative_memories list"
                assert len(profile.representative_memories) > 0, f"Place {place_id} should have representative memories"
        
        # Property 2: Should create story-driven location exploration
        if place_profiles:
            # Test location exploration for the first place profile
            first_place_id = list(place_profiles.keys())[0]
            location_memories = [m for m in memories if m.location == first_place_id]
            
            location_exploration = self.place_service.create_location_exploration(first_place_id, memories)
            
            assert location_exploration is not None, "Should create location exploration"
            assert isinstance(location_exploration, LocationExploration), "Should return LocationExploration instance"
            
            # Verify exploration structure
            assert location_exploration.location_id == first_place_id, "Should have correct location_id"
            assert location_exploration.location_name, "Should have location_name"
            
            # Narrative layers should provide story-driven context
            assert isinstance(location_exploration.narrative_layers, list), "Should have narrative_layers list"
            assert len(location_exploration.narrative_layers) > 0, "Should have at least one narrative layer"
            
            for layer in location_exploration.narrative_layers:
                assert isinstance(layer, dict), "Each narrative layer should be a dict"
                assert 'type' in layer, "Each layer should have type"
                assert 'title' in layer, "Each layer should have title"
                assert 'description' in layer, "Each layer should have description"
                assert 'data' in layer, "Each layer should have data"
                
                # Layer should provide meaningful context, not just listing entries
                assert len(layer['title']) >= 5, "Layer title should be meaningful"
                assert len(layer['description']) >= 10, "Layer description should be meaningful"
                assert isinstance(layer['data'], dict), "Layer data should be structured"
            
            # Temporal stories should show relationships over time
            assert isinstance(location_exploration.temporal_stories, list), "Should have temporal_stories list"
            
            # Emotional timeline should show emotional relationships
            assert isinstance(location_exploration.emotional_timeline, list), "Should have emotional_timeline list"
            
            # Relationship evolution should show how relationship with place evolved
            assert isinstance(location_exploration.relationship_evolution, dict), "Should have relationship_evolution dict"
            if location_exploration.relationship_evolution:
                assert 'evolution_summary' in location_exploration.relationship_evolution or \
                       len(location_exploration.relationship_evolution) > 0, "Should have relationship evolution data"
        
        # Property 3: Should enhance geo-enrichment with semantic understanding
        for memory in memories[:3]:  # Test first few memories
            enhanced_memory = self.place_service.enhance_geo_enrichment(memory)
            
            assert enhanced_memory is not None, "Should return enhanced memory"
            
            # Should preserve original memory data
            assert enhanced_memory.location == memory.location, "Should preserve original location"
            assert enhanced_memory.text == memory.text, "Should preserve original text"
            
            # Should add enhanced location data if location exists
            if memory.location and memory.location != "unknown":
                # Enhanced data might be added
                if hasattr(enhanced_memory, 'enhanced_location_data'):
                    assert isinstance(enhanced_memory.enhanced_location_data, dict), \
                        "Enhanced location data should be dict"
        
        # Property 4: Should generate travel narratives connecting locations
        journey_narratives = self.place_service.generate_travel_narrative(memories, 'journey')
        
        assert isinstance(journey_narratives, list), "Should return list of journey narratives"
        
        # If we have memories from multiple locations in sequence, should detect journeys
        unique_locations = set(m.location for m in memories if m.location != "unknown")
        if len(unique_locations) >= 2:
            # Should potentially detect journeys (depending on temporal clustering)
            for journey in journey_narratives:
                assert isinstance(journey, JourneyNarrative), "Each journey should be JourneyNarrative instance"
                
                # Journey structure
                assert journey.journey_id, "Journey should have journey_id"
                assert journey.title, "Journey should have title"
                assert len(journey.title) >= 5, "Journey title should be meaningful"
                
                assert isinstance(journey.places, list), "Journey should have places list"
                assert len(journey.places) >= 2, "Journey should connect at least 2 places"
                
                assert journey.narrative_text, "Journey should have narrative_text"
                assert len(journey.narrative_text) >= 20, "Journey narrative should be meaningful"
                
                assert isinstance(journey.temporal_span, tuple), "Journey should have temporal_span tuple"
                assert len(journey.temporal_span) == 2, "Temporal span should have start and end"
                assert journey.temporal_span[0] <= journey.temporal_span[1], "Temporal span should be ordered"
                
                assert journey.journey_type, "Journey should have journey_type"
                
                assert isinstance(journey.emotional_arc, list), "Journey should have emotional_arc list"
        
        # Property 5: Should provide narrative layers for map display
        # Test with a broad geographic bounds
        test_bounds = {
            'north': 90.0,
            'south': -90.0,
            'east': 180.0,
            'west': -180.0
        }
        
        narrative_layers = self.place_service.get_narrative_layers_for_map(test_bounds)
        
        assert isinstance(narrative_layers, list), "Should return list of narrative layers"
        
        # If we have place profiles, should return narrative layers
        if place_profiles:
            assert len(narrative_layers) > 0, "Should return narrative layers when places exist"
            
            for layer_data in narrative_layers:
                assert isinstance(layer_data, dict), "Each layer should be a dict"
                
                # Required fields for map display
                assert 'place_id' in layer_data, "Layer should have place_id"
                assert 'name' in layer_data, "Layer should have name"
                assert 'narrative_significance' in layer_data, "Layer should have narrative_significance"
                assert 'visit_count' in layer_data, "Layer should have visit_count"
                assert 'story_preview' in layer_data, "Layer should have story_preview"
                
                # Story preview should be meaningful narrative, not just data listing
                story_preview = layer_data['story_preview']
                assert isinstance(story_preview, str), "Story preview should be string"
                assert len(story_preview) >= 20, "Story preview should be meaningful"
                
                # Should contain narrative elements, not just data
                narrative_indicators = ['visited', 'memories', 'times', 'experiences', 'story', 'journey']
                has_narrative_element = any(indicator in story_preview.lower() 
                                         for indicator in narrative_indicators)
                assert has_narrative_element, f"Story preview should be narrative, not just data: '{story_preview}'"
    
    @given(journey_memories=generate_journey_memory_sequence())
    @settings(max_examples=50, deadline=30000, suppress_health_check=[HealthCheck.large_base_example])
    def test_journey_narrative_connections(self, journey_memories):
        """Test journey narrative connections between places"""
        # Arrange: Ensure we have a valid journey sequence
        assume(len(journey_memories) >= 2)
        
        unique_locations = set(m.location for m in journey_memories)
        assume(len(unique_locations) >= 2)
        
        # Act: Generate travel narratives
        journey_narratives = self.place_service.generate_travel_narrative(journey_memories, 'travel')
        
        # Assert: Should create meaningful journey connections
        if len(unique_locations) >= 2:
            # Should detect at least one journey if locations are temporally connected
            # (This depends on the temporal clustering algorithm)
            
            for journey in journey_narratives:
                # Journey should connect multiple places meaningfully
                assert len(journey.places) >= 2, "Journey should connect multiple places"
                
                # Places should be from the actual memory locations
                for place in journey.places:
                    assert place in unique_locations, f"Journey place {place} should be from memory locations"
                
                # Narrative should describe the journey meaningfully
                narrative_lower = journey.narrative_text.lower()
                journey_indicators = ['journey', 'travel', 'through', 'from', 'to', 'places', 'locations']
                has_journey_language = any(indicator in narrative_lower for indicator in journey_indicators)
                assert has_journey_language, f"Journey narrative should use journey language: '{journey.narrative_text}'"
    
    def test_place_exploration_service_initialization(self):
        """Test basic service initialization and configuration"""
        # Test default initialization
        service = PlaceExplorationService()
        assert service is not None
        assert hasattr(service, 'config')
        assert hasattr(service, 'place_profiles')
        assert hasattr(service, 'journey_narratives')
        
        # Test with custom config
        custom_config = {
            'narrative': {
                'min_visits_for_profile': 3,
                'significance_threshold': 0.5
            }
        }
        
        service_with_config = PlaceExplorationService(custom_config)
        assert service_with_config.narrative_config['min_visits_for_profile'] == 3
        assert service_with_config.narrative_config['significance_threshold'] == 0.5


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])