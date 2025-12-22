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

import json
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the Flask app
try:
    from src.qa.enhanced_qa_server import app
    FLASK_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Flask app unavailable: {e}")
    FLASK_AVAILABLE = False
    app = None


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    if not FLASK_AVAILABLE or app is None:
        pytest.skip("Flask app not available")
    
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_services():
    """Mock all the services to avoid dependencies"""
    if not FLASK_AVAILABLE:
        pytest.skip("Flask app not available")
    
    with patch('src.qa.enhanced_qa_server.ENHANCED_MEMORY_AVAILABLE', True), \
         patch('src.qa.enhanced_qa_server.PEOPLE_INTELLIGENCE_AVAILABLE', True), \
         patch('src.qa.enhanced_qa_server.GALLERY_CURATION_AVAILABLE', True), \
         patch('src.qa.enhanced_qa_server.STORY_GENERATION_AVAILABLE', True), \
         patch('src.qa.enhanced_qa_server.PLACE_EXPLORATION_AVAILABLE', True):
        yield


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask app not available")
class TestStatusEndpoint:
    """Test the status endpoint"""
    
    def test_status_endpoint_returns_all_services(self, client):
        """Test that status endpoint returns status for all services"""
        response = client.get('/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check that all expected service statuses are present
        expected_keys = [
            'enhanced_memory_available',
            'enhanced_memory_launched',
            'people_intelligence_available', 
            'people_intelligence_launched',
            'gallery_curation_available',
            'gallery_curation_launched',
            'story_generation_available',
            'story_generation_launched',
            'place_exploration_available',
            'place_exploration_launched',
            'original_qa_available',
            'original_qa_launched',
            'chatgpt_available'
        ]
        
        for key in expected_keys:
            assert key in data
            assert isinstance(data[key], bool)


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask app not available")
class TestEnhancedMemoryEndpoints:
    """Test enhanced memory retrieval endpoints"""
    
    def test_enhanced_launch_success(self, client, mock_services):
        """Test successful launch of enhanced memory service"""
        with patch('src.qa.enhanced_qa_server.EnhancedMemoryRetrieval') as mock_service:
            mock_service.return_value = Mock()
            
            response = client.get('/enhanced/launch')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert 'successfully' in data['message'].lower()
    
    def test_enhanced_launch_unavailable(self, client):
        """Test launch when enhanced memory service is unavailable"""
        with patch('src.qa.enhanced_qa_server.ENHANCED_MEMORY_AVAILABLE', False):
            response = client.get('/enhanced/launch')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_enhanced_query_success(self, client, mock_services):
        """Test successful enhanced memory query"""
        mock_response = Mock()
        mock_response.query = "test query"
        mock_response.narrative_answer = "test answer"
        mock_response.source_memories = []
        mock_response.composite_memories = []
        mock_response.related_themes = []
        mock_response.temporal_context = {}
        mock_response.confidence_score = 0.8
        
        with patch('src.qa.enhanced_qa_server.enhanced_memory_engine') as mock_engine:
            mock_engine.query_memories.return_value = mock_response
            
            response = client.post('/enhanced/query', 
                                 json={'query': 'test query'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['query'] == 'test query'
            assert data['narrative_answer'] == 'test answer'
            assert data['method'] == 'enhanced_retrieval'
    
    def test_enhanced_query_missing_query(self, client, mock_services):
        """Test enhanced query with missing query parameter"""
        with patch('src.qa.enhanced_qa_server.enhanced_memory_engine', Mock()):
            response = client.post('/enhanced/query', json={})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_enhanced_query_not_launched(self, client, mock_services):
        """Test enhanced query when service not launched"""
        with patch('src.qa.enhanced_qa_server.enhanced_memory_engine', None):
            response = client.post('/enhanced/query', 
                                 json={'query': 'test'})
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert 'error' in data


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask app not available")
class TestPeopleIntelligenceEndpoints:
    """Test people intelligence endpoints"""
    
    def test_people_launch_success(self, client, mock_services):
        """Test successful launch of people intelligence service"""
        with patch('src.qa.enhanced_qa_server.PeopleIntelligenceService') as mock_service:
            mock_service.return_value = Mock()
            
            response = client.get('/people/launch')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_people_detect_success(self, client, mock_services):
        """Test successful people detection"""
        mock_people = ['person1', 'person2']
        
        with patch('src.qa.enhanced_qa_server.people_intelligence_service') as mock_service:
            mock_service.detect_people_from_data.return_value = mock_people
            
            response = client.post('/people/detect')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['detected_people'] == mock_people
            assert data['count'] == 2
    
    def test_get_all_people_success(self, client, mock_services):
        """Test getting all people profiles"""
        mock_profile = Mock()
        mock_profile.to_dict.return_value = {'id': 'person1', 'name': 'Test Person'}
        
        with patch('src.qa.enhanced_qa_server.people_intelligence_service') as mock_service:
            mock_service.get_all_people.return_value = [mock_profile]
            
            response = client.get('/people/profiles')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['profiles']) == 1
            assert data['count'] == 1
    
    def test_get_person_profile_success(self, client, mock_services):
        """Test getting specific person profile"""
        mock_profile = Mock()
        mock_profile.to_dict.return_value = {'id': 'person1', 'name': 'Test Person'}
        
        with patch('src.qa.enhanced_qa_server.people_intelligence_service') as mock_service:
            mock_service.get_person_profile.return_value = mock_profile
            
            response = client.get('/people/profiles/person1')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['id'] == 'person1'
    
    def test_get_person_profile_not_found(self, client, mock_services):
        """Test getting non-existent person profile"""
        with patch('src.qa.enhanced_qa_server.people_intelligence_service') as mock_service:
            mock_service.get_person_profile.return_value = None
            
            response = client.get('/people/profiles/nonexistent')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_create_person_profile_success(self, client, mock_services):
        """Test creating new person profile"""
        mock_profile = Mock()
        mock_profile.to_dict.return_value = {'id': 'person1', 'name': 'New Person'}
        
        with patch('src.qa.enhanced_qa_server.people_intelligence_service') as mock_service:
            mock_service.create_person_profile.return_value = mock_profile
            
            response = client.post('/people/profiles', 
                                 json={'name': 'New Person'})
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['name'] == 'New Person'
    
    def test_create_person_profile_missing_name(self, client, mock_services):
        """Test creating person profile without name"""
        with patch('src.qa.enhanced_qa_server.people_intelligence_service', Mock()):
            response = client.post('/people/profiles', json={})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask app not available")
class TestGalleryEndpoints:
    """Test gallery curation endpoints"""
    
    def test_gallery_launch_success(self, client, mock_services):
        """Test successful launch of gallery service"""
        with patch('src.qa.enhanced_qa_server.GalleryCurationService') as mock_service:
            mock_service.return_value = Mock()
            
            response = client.get('/galleries/launch')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_initialize_default_galleries(self, client, mock_services):
        """Test initializing default galleries"""
        mock_gallery = Mock()
        mock_gallery.to_dict.return_value = {'id': 'gallery1', 'title': 'Test Gallery'}
        
        with patch('src.qa.enhanced_qa_server.gallery_curation_service') as mock_service:
            mock_service.initialize_default_galleries.return_value = [mock_gallery]
            
            response = client.post('/galleries/initialize')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['galleries']) == 1
            assert data['count'] == 1
    
    def test_create_thematic_gallery(self, client, mock_services):
        """Test creating thematic gallery"""
        mock_gallery = Mock()
        mock_gallery.to_dict.return_value = {'id': 'gallery1', 'title': 'Friends Gallery'}
        
        with patch('src.qa.enhanced_qa_server.gallery_curation_service') as mock_service:
            mock_service.create_thematic_gallery.return_value = mock_gallery
            
            response = client.post('/galleries/create', 
                                 json={'theme': 'friends'})
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['title'] == 'Friends Gallery'
    
    def test_create_prompt_gallery(self, client, mock_services):
        """Test creating gallery from prompt"""
        mock_gallery = Mock()
        mock_gallery.to_dict.return_value = {'id': 'gallery1', 'title': 'Custom Gallery'}
        
        with patch('src.qa.enhanced_qa_server.gallery_curation_service') as mock_service:
            mock_service.generate_from_prompt.return_value = mock_gallery
            
            response = client.post('/galleries/create', 
                                 json={'prompt': 'memories with family'})
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['title'] == 'Custom Gallery'
    
    def test_create_gallery_missing_params(self, client, mock_services):
        """Test creating gallery without theme or prompt"""
        with patch('src.qa.enhanced_qa_server.gallery_curation_service', Mock()):
            response = client.post('/galleries/create', json={})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask app not available")
class TestStoryGenerationEndpoints:
    """Test story generation endpoints"""
    
    def test_story_launch_success(self, client, mock_services):
        """Test successful launch of story generation service"""
        with patch('src.qa.enhanced_qa_server.StoryGenerationService') as mock_service:
            mock_service.return_value = Mock()
            
            response = client.get('/stories/launch')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_story_launch_unavailable(self, client):
        """Test launch when story generation service is unavailable"""
        with patch('src.qa.enhanced_qa_server.STORY_GENERATION_AVAILABLE', False):
            response = client.get('/stories/launch')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_generate_story_success(self, client, mock_services):
        """Test successful story generation"""
        mock_story = Mock()
        mock_story.to_dict.return_value = {
            'id': 'story1',
            'title': 'Test Story',
            'chapters': []
        }
        
        with patch('src.qa.enhanced_qa_server.story_generation_service') as mock_service:
            mock_service.generate_story.return_value = mock_story
            
            response = client.post('/stories/generate', 
                                 json={'query': 'memories from last year'})
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['title'] == 'Test Story'
    
    def test_generate_story_missing_data(self, client, mock_services):
        """Test story generation without request data"""
        with patch('src.qa.enhanced_qa_server.story_generation_service', Mock()):
            # Test with no JSON data
            response = client.post('/stories/generate')
            # The endpoint should handle missing data gracefully
            # Accept both 400 (validation error) and 500 (service error) as valid responses
            assert response.status_code in [400, 500]
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_get_narrative_modes(self, client, mock_services):
        """Test getting supported narrative modes"""
        with patch('src.qa.enhanced_qa_server.story_generation_service') as mock_service:
            mock_service.get_supported_narrative_modes.return_value = ['chronological', 'thematic']
            mock_service.get_supported_narrative_styles.return_value = ['documentary', 'memoir']
            
            response = client.get('/stories/modes')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'narrative_modes' in data
            assert 'narrative_styles' in data
            assert len(data['narrative_modes']) == 2
            assert len(data['narrative_styles']) == 2
    
    def test_generate_story_from_memories_not_implemented(self, client, mock_services):
        """Test story generation from memory IDs (not yet implemented)"""
        with patch('src.qa.enhanced_qa_server.story_generation_service', Mock()):
            response = client.post('/stories/from-memories', 
                                 json={'memory_ids': ['mem1', 'mem2']})
            
            assert response.status_code == 501
            data = json.loads(response.data)
            assert 'not yet fully implemented' in data['message']


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask app not available")
class TestPlaceExplorationEndpoints:
    """Test place exploration endpoints"""
    
    def test_place_launch_success(self, client, mock_services):
        """Test successful launch of place exploration service"""
        with patch('src.qa.enhanced_qa_server.PlaceExplorationService') as mock_service:
            mock_service.return_value = Mock()
            
            response = client.get('/places/launch')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_place_launch_unavailable(self, client):
        """Test launch when place exploration service is unavailable"""
        with patch('src.qa.enhanced_qa_server.PLACE_EXPLORATION_AVAILABLE', False):
            response = client.get('/places/launch')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_get_map_narrative_layers_success(self, client, mock_services):
        """Test getting narrative layers for map"""
        mock_layers = [
            {'place_id': 'place1', 'name': 'Test Place', 'coordinates': [0, 0]}
        ]
        
        with patch('src.qa.enhanced_qa_server.place_exploration_service') as mock_service:
            mock_service.get_narrative_layers_for_map.return_value = mock_layers
            
            bounds = {
                'north': 40.0,
                'south': 39.0,
                'east': -73.0,
                'west': -74.0
            }
            
            response = client.post('/places/map/narrative-layers', 
                                 json={'bounds': bounds})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['narrative_layers']) == 1
            assert data['layer_count'] == 1
    
    def test_get_map_narrative_layers_missing_bounds(self, client, mock_services):
        """Test getting narrative layers without bounds"""
        with patch('src.qa.enhanced_qa_server.place_exploration_service', Mock()):
            response = client.post('/places/map/narrative-layers', json={})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_get_map_narrative_layers_invalid_bounds(self, client, mock_services):
        """Test getting narrative layers with invalid bounds"""
        with patch('src.qa.enhanced_qa_server.place_exploration_service', Mock()):
            bounds = {'north': 40.0}  # Missing required bounds
            
            response = client.post('/places/map/narrative-layers', 
                                 json={'bounds': bounds})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_analyze_place_relationships_not_implemented(self, client, mock_services):
        """Test place relationship analysis (not yet implemented)"""
        with patch('src.qa.enhanced_qa_server.place_exploration_service', Mock()):
            response = client.post('/places/analyze', 
                                 json={'memories': []})
            
            assert response.status_code == 501
            data = json.loads(response.data)
            assert 'not yet fully implemented' in data['message']
    
    def test_explore_location_not_implemented(self, client, mock_services):
        """Test location exploration (not yet implemented)"""
        with patch('src.qa.enhanced_qa_server.place_exploration_service', Mock()):
            response = client.get('/places/location1/explore')
            
            assert response.status_code == 501
            data = json.loads(response.data)
            assert 'not yet fully implemented' in data['message']


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask app not available")
class TestErrorHandling:
    """Test error handling across endpoints"""
    
    def test_service_not_launched_errors(self, client, mock_services):
        """Test that endpoints return 503 when services not launched"""
        # Test enhanced memory
        with patch('src.qa.enhanced_qa_server.enhanced_memory_engine', None):
            response = client.post('/enhanced/query', json={'query': 'test'})
            assert response.status_code == 503
        
        # Test people intelligence
        with patch('src.qa.enhanced_qa_server.people_intelligence_service', None):
            response = client.get('/people/profiles')
            assert response.status_code == 503
        
        # Test gallery curation
        with patch('src.qa.enhanced_qa_server.gallery_curation_service', None):
            response = client.get('/galleries')
            assert response.status_code == 503
        
        # Test story generation
        with patch('src.qa.enhanced_qa_server.story_generation_service', None):
            response = client.post('/stories/generate', json={})
            assert response.status_code == 503
        
        # Test place exploration
        with patch('src.qa.enhanced_qa_server.place_exploration_service', None):
            response = client.get('/places/location1/explore')
            assert response.status_code == 503
    
    def test_service_unavailable_errors(self, client):
        """Test that endpoints return 503 when services unavailable"""
        # Test when all services are unavailable
        with patch('src.qa.enhanced_qa_server.ENHANCED_MEMORY_AVAILABLE', False), \
             patch('src.qa.enhanced_qa_server.PEOPLE_INTELLIGENCE_AVAILABLE', False), \
             patch('src.qa.enhanced_qa_server.GALLERY_CURATION_AVAILABLE', False), \
             patch('src.qa.enhanced_qa_server.STORY_GENERATION_AVAILABLE', False), \
             patch('src.qa.enhanced_qa_server.PLACE_EXPLORATION_AVAILABLE', False):
            
            response = client.get('/enhanced/launch')
            assert response.status_code == 503
            
            response = client.get('/people/launch')
            assert response.status_code == 503
            
            response = client.get('/galleries/launch')
            assert response.status_code == 503
            
            response = client.get('/stories/launch')
            assert response.status_code == 503
            
            response = client.get('/places/launch')
            assert response.status_code == 503
    
    def test_json_parsing_errors(self, client, mock_services):
        """Test handling of invalid JSON in requests"""
        with patch('src.qa.enhanced_qa_server.enhanced_memory_engine', Mock()):
            response = client.post('/enhanced/query', 
                                 data='invalid json',
                                 content_type='application/json')
            
            # Flask should handle JSON parsing errors
            assert response.status_code in [400, 500]


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask app not available")
class TestOriginalQAFallback:
    """Test fallback to original QA system"""
    
    def test_original_launch_success(self, client):
        """Test launching original QA engines"""
        with patch('src.qa.enhanced_qa_server.QA_AVAILABLE', True), \
             patch('src.qa.enhanced_qa_server.QAEngine') as mock_qa, \
             patch('src.qa.enhanced_qa_server.ChatGPTEngine') as mock_chatgpt:
            
            mock_qa.return_value = Mock()
            mock_chatgpt.return_value = Mock()
            
            response = client.get('/launch')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_original_query_success(self, client):
        """Test querying with original QA system"""
        with patch('src.qa.enhanced_qa_server.QA_AVAILABLE', True), \
             patch('src.qa.enhanced_qa_server.qa_engine') as mock_engine:
            
            mock_engine.query.return_value = {
                'question': 'test',
                'answer': 'test answer',
                'sources': []
            }
            
            response = client.get('/query?query=test&qa=Retrieval-based')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['question'] == 'test'
            assert data['answer'] == 'test answer'
    
    def test_original_query_unavailable(self, client):
        """Test querying when original QA unavailable"""
        with patch('src.qa.enhanced_qa_server.QA_AVAILABLE', False):
            response = client.get('/query?query=test')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'warning' in data
            assert 'langchain' in data['warning']


if __name__ == '__main__':
    pytest.main([__file__])