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
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite

# Import the classes we need to test
from src.common.objects.enhanced_llentry import EnhancedLLEntry, PersonRelationship
from src.common.agents.agent_coordinator import AgentCoordinator


# Strategy generators for property-based testing

@composite
def generate_enhanced_llentry(draw):
    """Generate a valid EnhancedLLEntry object for testing"""
    entry_types = ["photo", "post", "purchase", "workout", "music", "location"]
    sources = ["facebook", "google_photos", "amazon", "apple_health", "strava"]
    
    entry_type = draw(st.sampled_from(entry_types))
    source = draw(st.sampled_from(sources))
    
    # Generate a realistic timestamp (within last 10 years)
    base_time = datetime.now() - timedelta(days=3650)
    time_offset = draw(st.integers(min_value=0, max_value=3650 * 24 * 3600))
    start_time = base_time + timedelta(seconds=time_offset)
    
    entry = EnhancedLLEntry(entry_type, start_time.isoformat(), source)
    
    # Add basic data
    entry.text = draw(st.text(min_size=10, max_size=500))
    entry.tags = draw(st.lists(st.text(min_size=1, max_size=50), max_size=10))
    
    # Add enhanced AI fields
    entry.narrative_significance = draw(st.floats(min_value=0.0, max_value=1.0))
    entry.story_potential = draw(st.floats(min_value=0.0, max_value=1.0))
    entry.emotional_context = draw(st.dictionaries(
        st.sampled_from(['joy', 'sadness', 'excitement', 'calm', 'nostalgia']),
        st.floats(min_value=0.0, max_value=1.0),
        max_size=3
    ))
    entry.life_phase = draw(st.sampled_from(['childhood', 'adolescence', 'early_adult', 'adult', 'senior']))
    entry.thematic_tags = draw(st.lists(
        st.sampled_from(['family', 'friends', 'work', 'travel', 'hobby', 'milestone']),
        max_size=5
    ))
    
    # Add media elements for some entries
    if entry_type == "photo":
        entry.photos = draw(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5))
        entry.imageFileName = entry.photos[0] if entry.photos else None
        entry.imageFilePath = f"/path/to/{entry.imageFileName}" if entry.imageFileName else None
        entry.peopleInImage = draw(st.lists(st.text(min_size=1, max_size=50), max_size=5))
    
    if entry_type == "post":
        entry.videos = draw(st.lists(st.text(min_size=1, max_size=100), max_size=2))
    
    # Add location data for some entries
    if draw(st.booleans()):
        entry.location = draw(st.text(min_size=5, max_size=100))
        entry.latitude = draw(st.floats(min_value=-90, max_value=90))
        entry.longitude = draw(st.floats(min_value=-180, max_value=180))
    
    # Add people relationships
    num_relationships = draw(st.integers(min_value=0, max_value=3))
    for i in range(num_relationships):
        relationship = PersonRelationship(
            person_id=f"person_{i}",
            relationship_type=draw(st.sampled_from(['friend', 'family', 'colleague', 'partner'])),
            confidence=draw(st.floats(min_value=0.5, max_value=1.0)),
            first_interaction=start_time - timedelta(days=draw(st.integers(min_value=0, max_value=365))),
            last_interaction=start_time
        )
        entry.people_relationships.append(relationship)
    
    return entry


@composite
def generate_story_request(draw):
    """Generate a valid story generation request"""
    # Generate a collection of memories
    num_memories = draw(st.integers(min_value=3, max_value=15))
    memories = [draw(generate_enhanced_llentry()) for _ in range(num_memories)]
    
    request = {
        'available_memories': memories,
        'narrative_mode': draw(st.sampled_from(['chronological', 'thematic', 'people-centered', 'place-centered'])),
        'narrative_style': draw(st.sampled_from(['documentary', 'memoir', 'minimalist'])),
        'max_results': draw(st.integers(min_value=3, max_value=min(num_memories, 10))),
        'title': draw(st.text(min_size=5, max_size=100))
    }
    
    # Add optional query and theme
    if draw(st.booleans()):
        request['query'] = draw(st.text(min_size=5, max_size=200))
    
    if draw(st.booleans()):
        request['theme'] = draw(st.sampled_from(['family', 'travel', 'work', 'celebration', 'growth']))
    
    return request


@composite
def generate_gallery_request(draw):
    """Generate a valid gallery generation request"""
    # Generate a collection of memories
    num_memories = draw(st.integers(min_value=5, max_value=20))
    memories = [draw(generate_enhanced_llentry()) for _ in range(num_memories)]
    
    request = {
        'available_memories': memories,
        'max_results': draw(st.integers(min_value=5, max_value=min(num_memories, 15))),
        'creation_method': draw(st.sampled_from(['thematic', 'prompt', 'manual']))
    }
    
    # Add optional prompt for prompt-based galleries
    if request['creation_method'] == 'prompt':
        request['prompt'] = draw(st.text(min_size=10, max_size=200))
    
    # Add optional theme for thematic galleries
    if request['creation_method'] == 'thematic':
        request['theme'] = draw(st.sampled_from(['moments with friends', 'creative periods', 'times of growth']))
    
    return request


class TestAgentCoordination:
    """Test suite for AI agent coordination functionality"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Create a temporary directory for any test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize agent coordinator with test configuration
        self.test_config = {
            'archivist': {
                'max_selection_size': 50,
                'relevance_threshold': 0.2,  # Lower threshold for testing
                'exclude_low_quality': False  # Allow all content for testing
            },
            'narrative': {
                'max_chapter_sentences': 3,
                'default_style': 'documentary'
            },
            'editor': {
                'filter_sensitive_content': False,  # Disable for testing
                'filter_low_quality': False,
                'max_items_per_group': 100
            },
            'director': {
                'optimal_chapter_count': 5,
                'narrative_pacing': 'moderate'
            },
            'critic': {
                'min_quality_score': 0.3,  # Lower threshold for testing
                'require_data_grounding': False,  # Disable for testing
                'strict_privacy_mode': False
            },
            'max_iterations': 2,
            'quality_threshold': 0.3,
            'require_critic_approval': True
        }
        
        self.coordinator = AgentCoordinator(self.test_config)
    
    def teardown_method(self):
        """Clean up test environment after each test"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(story_request=generate_story_request())
    @settings(max_examples=10, deadline=30000)  # Increased deadline for complex operations
    def test_ai_agent_coordination_story_generation(self, story_request):
        """**Feature: ai-personal-archive, Property 7: AI Agent Coordination**
        
        For any user request or content generation task, the AI agents should work together 
        to select, curate, create, sequence, and quality-check outputs while maintaining 
        grounding in actual user data.
        """
        # Arrange: Ensure we have valid input data
        assume(len(story_request['available_memories']) >= 3)
        assume(all(hasattr(memory, 'text') and memory.text for memory in story_request['available_memories']))
        
        # Initialize the coordinator
        initialization_success = self.coordinator.initialize()
        assume(initialization_success)  # Skip test if initialization fails
        
        # Act: Generate story using agent coordination
        result = self.coordinator.generate_story(story_request)
        
        # Assert: Verify agent coordination properties
        
        # Property 1: Workflow should complete successfully or fail gracefully
        assert 'success' in result, "Result must indicate success/failure status"
        assert 'workflow_id' in result, "Result must include workflow tracking ID"
        assert 'workflow_steps' in result, "Result must include workflow step history"
        
        # Property 2: If successful, all agents should have participated
        if result['success']:
            workflow_steps = result['workflow_steps']
            step_names = [step['step_name'] for step in workflow_steps]
            
            # Verify key agents participated in the workflow
            expected_steps = ['archivist_selection', 'editor_filtering', 'narrative_generation', 
                            'director_optimization', 'critic_review']
            
            for expected_step in expected_steps:
                assert any(expected_step in step_name for step_name in step_names), \
                    f"Expected workflow step '{expected_step}' not found in {step_names}"
            
            # Verify story was generated
            assert 'story' in result, "Successful result must include generated story"
            story = result['story']
            assert story is not None, "Generated story must not be None"
            assert hasattr(story, 'chapters'), "Story must have chapters"
            assert len(story.chapters) > 0, "Story must have at least one chapter"
            assert hasattr(story, 'title'), "Story must have a title"
            assert story.title, "Story title must not be empty"
        
        # Property 3: Memory processing should be consistent
        original_count = len(story_request['available_memories'])
        if 'memories_processed' in result:
            assert result['memories_processed'] == original_count, \
                "Processed memory count should match input"
        
        if result['success']:
            if 'memories_selected' in result:
                selected_count = result['memories_selected']
                # Selection should not exceed original count
                assert selected_count <= original_count, \
                    "Selected memories should not exceed available memories"
            
            if 'memories_filtered' in result:
                filtered_count = result['memories_filtered']
                if 'memories_selected' in result:
                    # Filtering should not increase count
                    assert filtered_count <= result['memories_selected'], \
                        "Filtered memories should not exceed selected memories"
                
                # Should have some memories remaining after filtering
                assert filtered_count > 0, "Should have at least some memories after filtering"
        
        # Property 4: Critic approval should be recorded
        assert 'critic_approval' in result, "Result must include critic approval status"
        if result['success']:
            critic_approval = result['critic_approval']
            assert isinstance(critic_approval, dict), "Critic approval must be a dictionary"
            assert 'approved' in critic_approval, "Critic approval must indicate approval status"
        
        # Property 5: Workflow should be traceable
        assert 'workflow_duration' in result, "Result must include workflow duration"
        assert isinstance(result['workflow_duration'], (int, float)), "Duration must be numeric"
        assert result['workflow_duration'] >= 0, "Duration must be non-negative"
        
        # Property 6: Agent coordination should maintain data safety
        if result['success']:
            story = result['story']
            for chapter in story.chapters:
                # Check that narrative text doesn't contain obvious safety violations
                narrative_text = chapter.narrative_text.lower()
                
                # Should not contain diagnostic language
                diagnostic_patterns = ['you are', 'you have', 'you suffer from']
                for pattern in diagnostic_patterns:
                    assert pattern not in narrative_text, \
                        f"Narrative contains diagnostic language: '{pattern}'"
                
                # Should not contain first-person impersonation
                impersonation_patterns = ['i felt', 'i thought', 'my feelings']
                for pattern in impersonation_patterns:
                    assert pattern not in narrative_text, \
                        f"Narrative contains impersonation: '{pattern}'"
    
    @given(gallery_request=generate_gallery_request())
    @settings(max_examples=10, deadline=20000)
    def test_ai_agent_coordination_gallery_generation(self, gallery_request):
        """Test agent coordination for gallery generation"""
        # Arrange: Ensure valid input
        assume(len(gallery_request['available_memories']) >= 5)
        
        # Initialize the coordinator
        initialization_success = self.coordinator.initialize()
        assume(initialization_success)
        
        # Act: Generate gallery using agent coordination
        result = self.coordinator.generate_gallery(gallery_request)
        
        # Assert: Verify coordination properties for gallery generation
        
        # Basic result structure
        assert 'success' in result
        assert 'workflow_id' in result
        assert 'workflow_steps' in result
        
        # If successful, verify gallery properties
        if result['success']:
            assert 'memories' in result
            memories = result['memories']
            assert isinstance(memories, list)
            assert len(memories) > 0, "Gallery should contain at least one memory"
            
            # Verify all memories are valid EnhancedLLEntry objects
            for memory in memories:
                assert isinstance(memory, EnhancedLLEntry), \
                    "All gallery memories should be EnhancedLLEntry objects"
            
            # Verify memory count constraints
            max_results = gallery_request.get('max_results', 15)
            assert len(memories) <= max_results, \
                "Gallery should not exceed max_results limit"
        
        # Verify workflow participation
        workflow_steps = result['workflow_steps']
        step_names = [step['step_name'] for step in workflow_steps]
        
        # Gallery workflow should include key steps
        expected_steps = ['archivist_selection', 'editor_filtering', 'director_sequencing']
        for expected_step in expected_steps:
            assert any(expected_step in step_name for step_name in step_names), \
                f"Expected gallery workflow step '{expected_step}' not found"
    
    def test_agent_initialization_coordination(self):
        """Test that all agents initialize properly in coordination"""
        # Test agent coordinator initialization
        coordinator = AgentCoordinator(self.test_config)
        
        # Verify all agents are created
        assert coordinator.archivist is not None
        assert coordinator.narrative is not None
        assert coordinator.editor is not None
        assert coordinator.director is not None
        assert coordinator.critic is not None
        
        # Test initialization
        success = coordinator.initialize()
        assert success, "Agent coordinator should initialize successfully"
        assert coordinator.is_initialized, "Coordinator should be marked as initialized"
        
        # Verify agent status
        status = coordinator.get_agent_status()
        assert status['coordinator_initialized'] == True
        assert 'agents' in status
        
        # Verify all agents are initialized
        for agent_name, agent_status in status['agents'].items():
            assert agent_status['is_initialized'] == True, \
                f"Agent {agent_name} should be initialized"
    
    def test_request_validation(self):
        """Test request validation functionality"""
        coordinator = AgentCoordinator(self.test_config)
        
        # Test valid request
        valid_memories = [EnhancedLLEntry("post", datetime.now().isoformat(), "test")]
        valid_request = {'available_memories': valid_memories}
        
        is_valid, issues = coordinator.validate_request(valid_request)
        assert is_valid, f"Valid request should pass validation: {issues}"
        assert len(issues) == 0, "Valid request should have no issues"
        
        # Test invalid requests
        invalid_requests = [
            {},  # Missing available_memories
            {'available_memories': []},  # Empty memories
            {'available_memories': [1, 2, 3]},  # Invalid memory objects
            {'available_memories': valid_memories, 'narrative_mode': 'invalid'},  # Invalid mode
            {'available_memories': valid_memories, 'max_results': -1}  # Invalid max_results
        ]
        
        for invalid_request in invalid_requests:
            is_valid, issues = coordinator.validate_request(invalid_request)
            assert not is_valid, f"Invalid request should fail validation: {invalid_request}"
            assert len(issues) > 0, "Invalid request should have issues"
    
    def test_agent_reset_functionality(self):
        """Test agent reset functionality"""
        coordinator = AgentCoordinator(self.test_config)
        coordinator.initialize()
        
        # Generate some workflow history
        test_memories = [EnhancedLLEntry("post", datetime.now().isoformat(), "test")]
        test_request = {'available_memories': test_memories}
        
        # This will create workflow history
        coordinator.generate_story(test_request)
        
        # Verify history exists
        assert len(coordinator.workflow_history) > 0, "Should have workflow history"
        
        # Reset all agents
        coordinator.reset_all_agents()
        
        # Verify history is cleared
        assert len(coordinator.workflow_history) == 0, "Workflow history should be cleared"
        
        # Verify agents are still functional
        status = coordinator.get_agent_status()
        assert status['coordinator_initialized'] == True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])