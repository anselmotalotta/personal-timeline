"""
Integration tests for API endpoints
Tests the actual HTTP API responses and data flow
"""
import pytest
import requests
import json
import time
from typing import Dict, Any

class TestAPIEndpoints:
    
    @classmethod
    def setup_class(cls):
        """Setup for all tests"""
        cls.base_url = "http://localhost:8086"
        cls.timeout = 10
        
        # Wait for services to be ready
        cls._wait_for_service()
    
    @classmethod
    def _wait_for_service(cls, max_attempts=30):
        """Wait for the API service to be ready"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{cls.base_url}/health", timeout=5)
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)
        
        raise Exception("API service not ready after 30 seconds")
    
    def test_health_endpoint(self):
        """Test health check endpoint returns proper structure"""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "overall_status" in data
        assert "services" in data
        assert "system_info" in data
        assert data["overall_status"] in ["healthy", "degraded", "limited"]
        
        # Check that key services are reported
        services = data["services"]
        expected_services = ["ai_providers", "people_intelligence", "story_generation"]
        for service in expected_services:
            assert service in services
            assert "healthy" in services[service]
            assert "status" in services[service]
    
    def test_status_endpoint(self):
        """Test status endpoint provides AI provider information"""
        response = requests.get(f"{self.base_url}/status", timeout=self.timeout)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        required_fields = ["ai_status", "ai_message", "available_providers", "features"]
        for field in required_fields:
            assert field in data
        
        # Check AI status is valid
        assert data["ai_status"] in ["unavailable", "partial", "full", "error"]
        
        # Check features structure
        features = data["features"]
        expected_features = ["story_generation", "people_intelligence", "smart_galleries", "semantic_search"]
        for feature in expected_features:
            assert feature in features
            assert isinstance(features[feature], bool)
    
    def test_people_endpoint(self):
        """Test people endpoint returns proper data structure"""
        response = requests.get(f"{self.base_url}/people", timeout=self.timeout)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "people" in data
        assert "count" in data
        assert isinstance(data["people"], list)
        assert data["count"] == len(data["people"])
        
        # If people exist, validate their structure
        if data["people"]:
            person = data["people"][0]
            required_fields = ["id", "name", "photo_count", "relationship_strength"]
            for field in required_fields:
                assert field in person
    
    def test_stories_endpoint(self):
        """Test stories endpoint returns proper data structure"""
        response = requests.get(f"{self.base_url}/stories", timeout=self.timeout)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "stories" in data
        assert "count" in data
        assert isinstance(data["stories"], list)
        assert data["count"] == len(data["stories"])
        
        # If stories exist, validate their structure
        if data["stories"]:
            story = data["stories"][0]
            required_fields = ["id", "title", "narrative_mode", "chapter_count"]
            for field in required_fields:
                assert field in story
    
    def test_individual_story_endpoint(self):
        """Test retrieving individual stories with chapters"""
        # First get list of stories
        response = requests.get(f"{self.base_url}/stories", timeout=self.timeout)
        stories_data = response.json()
        
        if not stories_data["stories"]:
            pytest.skip("No stories available to test individual retrieval")
        
        story_id = stories_data["stories"][0]["id"]
        
        # Get individual story
        response = requests.get(f"{self.base_url}/stories/{story_id}", timeout=self.timeout)
        
        assert response.status_code == 200
        story = response.json()
        
        # Validate full story structure
        required_fields = ["id", "title", "chapters", "narrative_mode"]
        for field in required_fields:
            assert field in story
        
        # Validate chapters structure
        if story["chapters"]:
            chapter = story["chapters"][0]
            chapter_fields = ["id", "title", "content", "emotional_tone"]
            for field in chapter_fields:
                assert field in chapter
    
    def test_story_generation_endpoint(self):
        """Test story generation creates valid stories"""
        payload = {
            "type": "chronological",
            "theme": "test story for integration"
        }
        
        response = requests.post(
            f"{self.base_url}/stories/generate",
            json=payload,
            timeout=30  # Story generation can take longer
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "story" in data
        assert "type" in data
        assert "theme" in data
        
        story = data["story"]
        assert "id" in story
        assert "title" in story
        assert "chapters" in story
        assert len(story["chapters"]) > 0
        
        # Validate chapter structure
        chapter = story["chapters"][0]
        assert "title" in chapter
        assert "content" in chapter
        assert len(chapter["content"]) > 0
    
    def test_chat_endpoint(self):
        """Test chat endpoint processes messages correctly"""
        payload = {"message": "Hello, can you help me with my personal timeline?"}
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=payload,
            timeout=15
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "response" in data
        assert "timestamp" in data
        assert "status" in data
        
        # Response should be non-empty
        assert len(data["response"]) > 0
        assert data["status"] == "success"
    
    def test_qa_endpoint(self):
        """Test Q&A endpoint processes queries correctly"""
        payload = {"query": "What kind of data do I have in my timeline?"}
        
        response = requests.post(
            f"{self.base_url}/qa",
            json=payload,
            timeout=15
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "answer" in data
        assert "query" in data
        assert "confidence" in data
        
        # Answer should be non-empty
        assert len(data["answer"]) > 0
        assert data["query"] == payload["query"]
        assert 0 <= data["confidence"] <= 1
    
    def test_galleries_endpoint(self):
        """Test galleries endpoint returns photo data"""
        response = requests.get(f"{self.base_url}/galleries", timeout=self.timeout)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "galleries" in data
        assert "total_photos" in data
        assert isinstance(data["galleries"], list)
        assert isinstance(data["total_photos"], int)
    
    def test_providers_endpoint(self):
        """Test providers endpoint returns AI provider information"""
        response = requests.get(f"{self.base_url}/providers", timeout=self.timeout)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "providers" in data
        assert "hierarchy" in data
        
        # Check provider information
        providers = data["providers"]
        expected_providers = ["openai", "anthropic", "google"]
        for provider in expected_providers:
            assert provider in providers
            provider_info = providers[provider]
            assert "has_credentials" in provider_info
            assert "status" in provider_info
    
    def test_launch_endpoints(self):
        """Test service launch endpoints work correctly"""
        launch_endpoints = [
            "/launch?dataset=Digital",
            "/enhanced/launch",
            "/people/launch",
            "/galleries/launch",
            "/places/launch"
        ]
        
        for endpoint in launch_endpoints:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=self.timeout)
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert data["status"] == "success"
    
    def test_stories_launch_endpoint(self):
        """Test stories launch endpoint (POST method)"""
        response = requests.post(f"{self.base_url}/stories/launch", timeout=self.timeout)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
    
    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        headers = {
            'Origin': 'http://localhost:52692',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{self.base_url}/status", headers=headers)
        
        # CORS should allow the request
        assert response.status_code in [200, 204]
        
        # Check actual request with CORS headers
        response = requests.get(f"{self.base_url}/status", headers={'Origin': 'http://localhost:52692'})
        assert response.status_code == 200
        
        # Should have CORS headers
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        assert cors_origin in ['*', 'http://localhost:52692']
    
    def test_error_handling(self):
        """Test API error handling for invalid requests"""
        # Test invalid story ID
        response = requests.get(f"{self.base_url}/stories/invalid-id", timeout=self.timeout)
        assert response.status_code == 404
        
        # Test invalid chat request
        response = requests.post(f"{self.base_url}/chat", json={}, timeout=self.timeout)
        assert response.status_code == 400
        
        # Test invalid Q&A request
        response = requests.post(f"{self.base_url}/qa", json={}, timeout=self.timeout)
        assert response.status_code == 400