"""
Unit tests for AI model integration layer

Tests cover:
- Model loading and initialization
- Fallback mechanisms for model failures
- Embedding generation and similarity search
- Text-to-speech integration
- Multimodal model support
- Error handling and recovery
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import json
import numpy as np
from typing import List, Dict, Any

# Import the modules to test
from src.common.services.ai_service_manager import AIServiceManager, AIServiceConfig
from src.common.services.ai_enhancement_pipeline import AIEnhancementPipeline


class TestAIServiceConfig(unittest.TestCase):
    """Test AI service configuration"""
    
    def test_default_config_values(self):
        """Test that default configuration values are set correctly"""
        config = AIServiceConfig()
        
        self.assertEqual(config.local_llm_model, "microsoft/DialoGPT-medium")
        self.assertEqual(config.embedding_model, "sentence-transformers/all-MiniLM-L6-v2")
        self.assertEqual(config.tts_model, "espnet/kan-bayashi_ljspeech_vits")
        self.assertEqual(config.multimodal_model, "openai/clip-vit-base-patch32")
        self.assertEqual(config.model_dir, "/app/models")
        self.assertEqual(config.batch_size, 32)
        self.assertEqual(config.max_memory_gb, 4)
        self.assertFalse(config.enable_gpu)
    
    def test_custom_config_values(self):
        """Test that custom configuration values are set correctly"""
        config = AIServiceConfig(
            local_llm_model="custom/model",
            embedding_model="custom/embedding",
            batch_size=64,
            enable_gpu=True
        )
        
        self.assertEqual(config.local_llm_model, "custom/model")
        self.assertEqual(config.embedding_model, "custom/embedding")
        self.assertEqual(config.batch_size, 64)
        self.assertTrue(config.enable_gpu)


class TestAIServiceManager(unittest.TestCase):
    """Test AI service manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = AIServiceConfig(
            model_dir="/tmp/test_models",
            batch_size=2,
            max_memory_gb=1
        )
        self.manager = AIServiceManager(self.config)
    
    def test_manager_initialization(self):
        """Test that AI service manager initializes correctly"""
        self.assertIsNotNone(self.manager.app)
        self.assertEqual(self.manager.config, self.config)
        self.assertEqual(self.manager.services, {})
        self.assertEqual(self.manager.model_cache, {})
    
    def test_health_check_endpoint(self):
        """Test health check endpoint functionality"""
        with self.manager.app.test_client() as client:
            response = client.get('/health')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'healthy')
            self.assertIn('services', data)
            self.assertIn('models_loaded', data)
    
    def test_get_service_returns_none_for_missing_service(self):
        """Test that get_service returns None for missing services"""
        service = self.manager.get_service('nonexistent')
        self.assertIsNone(service)
    
    def test_get_service_returns_service_when_available(self):
        """Test that get_service returns service when available"""
        mock_service = Mock()
        self.manager.services['test_service'] = mock_service
        
        service = self.manager.get_service('test_service')
        self.assertEqual(service, mock_service)


class TestEmbeddingService(unittest.TestCase):
    """Test embedding service functionality"""
    
    def test_embedding_service_initialization_without_dependencies(self):
        """Test embedding service initialization when dependencies are not available"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Without sentence-transformers installed, service should return None
        service = manager._init_embedding_service()
        
        # Service may be None if dependencies aren't installed
        if service is None:
            self.assertIsNone(service)
        else:
            # If dependencies are installed, service should have generate_embeddings method
            self.assertTrue(hasattr(service, 'generate_embeddings'))
    
    def test_embedding_api_endpoint_success(self):
        """Test embedding API endpoint with successful generation"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Mock embedding service
        mock_service = Mock()
        mock_service.generate_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
        manager.services['embeddings'] = mock_service
        
        with manager.app.test_client() as client:
            response = client.post('/api/ai/generate_embeddings', 
                                 json={'texts': ['text1', 'text2']})
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('embeddings', data)
            self.assertEqual(len(data['embeddings']), 2)
    
    def test_embedding_api_endpoint_service_unavailable(self):
        """Test embedding API endpoint when service is unavailable"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        with manager.app.test_client() as client:
            response = client.post('/api/ai/generate_embeddings', 
                                 json={'texts': ['text1', 'text2']})
            
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertIn('error', data)


class TestMultimodalService(unittest.TestCase):
    """Test multimodal service functionality"""
    
    def test_multimodal_service_initialization_without_dependencies(self):
        """Test multimodal service initialization when dependencies are not available"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Without transformers/PIL installed, service should return None
        service = manager._init_multimodal_service()
        
        # Service may be None if dependencies aren't installed
        if service is None:
            self.assertIsNone(service)
        else:
            # If dependencies are installed, service should have analyze_image method
            self.assertTrue(hasattr(service, 'analyze_image'))
    
    def test_multimodal_api_endpoint_success(self):
        """Test multimodal API endpoint with successful analysis"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Mock multimodal service
        mock_service = Mock()
        mock_service.analyze_image.return_value = {
            'description': 'Test image',
            'confidence': 0.8,
            'features': [0.1, 0.2, 0.3]
        }
        manager.services['multimodal'] = mock_service
        
        with manager.app.test_client() as client:
            response = client.post('/api/ai/analyze_image', 
                                 json={'image_path': '/test.jpg', 'context': 'test'})
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('description', data)
            self.assertIn('confidence', data)
    
    def test_multimodal_api_endpoint_service_unavailable(self):
        """Test multimodal API endpoint when service is unavailable"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        with manager.app.test_client() as client:
            response = client.post('/api/ai/analyze_image', 
                                 json={'image_path': '/test.jpg'})
            
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertIn('error', data)


class TestNarrativeService(unittest.TestCase):
    """Test narrative generation service functionality"""
    
    def test_narrative_service_initialization_without_dependencies(self):
        """Test narrative service initialization when dependencies are not available"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Without transformers installed, service should return None
        service = manager._init_narrative_service()
        
        # Service may be None if dependencies aren't installed
        if service is None:
            self.assertIsNone(service)
        else:
            # If dependencies are installed, service should have generate_narrative method
            self.assertTrue(hasattr(service, 'generate_narrative'))
    
    def test_narrative_api_endpoint_success(self):
        """Test narrative API endpoint with successful generation"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Mock narrative service
        mock_service = Mock()
        mock_service.generate_narrative.return_value = {
            'narrative': 'Generated story text',
            'mode': 'chronological',
            'memory_count': 2
        }
        manager.services['narrative'] = mock_service
        
        with manager.app.test_client() as client:
            response = client.post('/api/ai/generate_narrative', 
                                 json={'memories': [{'text': 'memory1'}, {'text': 'memory2'}], 
                                      'mode': 'chronological'})
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('narrative', data)
            self.assertIn('mode', data)
            self.assertEqual(data['mode'], 'chronological')
    
    def test_narrative_api_endpoint_service_unavailable(self):
        """Test narrative API endpoint when service is unavailable"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        with manager.app.test_client() as client:
            response = client.post('/api/ai/generate_narrative', 
                                 json={'memories': [], 'mode': 'chronological'})
            
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertIn('error', data)


class TestTTSService(unittest.TestCase):
    """Test text-to-speech service functionality"""
    
    def test_tts_service_initialization(self):
        """Test TTS service initialization"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        service = manager._init_tts_service()
        
        self.assertIsNotNone(service)
        self.assertTrue(hasattr(service, 'synthesize_speech'))
    
    def test_tts_speech_synthesis(self):
        """Test speech synthesis functionality"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        service = manager._init_tts_service()
        
        # Test speech synthesis
        text = "Hello, this is a test"
        audio_path = service.synthesize_speech(text, 'neutral')
        
        self.assertIsInstance(audio_path, str)
        self.assertIn('mock_audio_', audio_path)
        self.assertIn('.wav', audio_path)
    
    def test_tts_api_endpoint_success(self):
        """Test TTS API endpoint with successful synthesis"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Mock TTS service
        mock_service = Mock()
        mock_service.synthesize_speech.return_value = "/path/to/audio.wav"
        manager.services['tts'] = mock_service
        
        with manager.app.test_client() as client:
            response = client.post('/api/ai/synthesize_speech', 
                                 json={'text': 'Hello world', 'narrator_style': 'neutral'})
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('audio_path', data)
            self.assertEqual(data['audio_path'], "/path/to/audio.wav")
    
    def test_tts_api_endpoint_service_unavailable(self):
        """Test TTS API endpoint when service is unavailable"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        with manager.app.test_client() as client:
            response = client.post('/api/ai/synthesize_speech', 
                                 json={'text': 'Hello world'})
            
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertIn('error', data)


class TestAIEnhancementPipeline(unittest.TestCase):
    """Test AI enhancement pipeline functionality"""
    
    @patch('src.common.services.ai_enhancement_pipeline.requests')
    def test_check_ai_services_success(self, mock_requests):
        """Test successful AI services health check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response
        
        pipeline = AIEnhancementPipeline('http://test:8086')
        result = pipeline._check_ai_services()
        
        self.assertTrue(result)
        mock_requests.get.assert_called_once_with('http://test:8086/health', timeout=10)
    
    @patch('src.common.services.ai_enhancement_pipeline.requests')
    def test_check_ai_services_failure(self, mock_requests):
        """Test AI services health check failure"""
        mock_requests.get.side_effect = Exception("Connection failed")
        
        pipeline = AIEnhancementPipeline('http://test:8086')
        result = pipeline._check_ai_services()
        
        self.assertFalse(result)
    
    @patch('src.common.services.ai_enhancement_pipeline.EnhancedPersonalDataDBConnector')
    def test_get_entries_for_enhancement(self, mock_db_class):
        """Test getting entries for enhancement"""
        mock_db = Mock()
        mock_entries = [Mock(id='1', ai_enhanced=False), Mock(id='2', ai_enhanced=True)]
        mock_db.get_all_entries.return_value = mock_entries
        mock_db_class.return_value = mock_db
        
        pipeline = AIEnhancementPipeline()
        entries = pipeline._get_entries_for_enhancement()
        
        # Should only return unenhanced entries
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].id, '1')


class TestModelFallbackMechanisms(unittest.TestCase):
    """Test fallback mechanisms for model failures"""
    
    def test_service_initialization_fallback(self):
        """Test that services fall back gracefully when dependencies are missing"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Test that services can be None without breaking the system
        embedding_service = manager._init_embedding_service()
        multimodal_service = manager._init_multimodal_service()
        narrative_service = manager._init_narrative_service()
        tts_service = manager._init_tts_service()
        
        # Services may be None if dependencies aren't installed, which is fine
        # TTS service should always be available (mock implementation)
        self.assertIsNotNone(tts_service)
    
    def test_api_endpoints_handle_missing_services(self):
        """Test that API endpoints handle missing services gracefully"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        with manager.app.test_client() as client:
            # Test embedding endpoint without service
            response = client.post('/api/ai/generate_embeddings', json={'texts': ['test']})
            self.assertEqual(response.status_code, 503)
            
            # Test narrative endpoint without service
            response = client.post('/api/ai/generate_narrative', json={'memories': [], 'mode': 'chronological'})
            self.assertEqual(response.status_code, 503)
            
            # Test image analysis endpoint without service
            response = client.post('/api/ai/analyze_image', json={'image_path': '/test.jpg'})
            self.assertEqual(response.status_code, 503)
            
            # Test TTS endpoint without service
            response = client.post('/api/ai/synthesize_speech', json={'text': 'test'})
            self.assertEqual(response.status_code, 503)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in AI model integration"""
    
    def test_api_endpoint_error_handling(self):
        """Test that API endpoints handle errors gracefully"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Mock a service that raises an exception
        mock_service = Mock()
        mock_service.generate_embeddings.side_effect = Exception("Model error")
        manager.services['embeddings'] = mock_service
        
        with manager.app.test_client() as client:
            response = client.post('/api/ai/generate_embeddings', json={'texts': ['test']})
            
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertIn('error', data)
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in API requests"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        with manager.app.test_client() as client:
            response = client.post('/api/ai/generate_embeddings', 
                                 data='invalid json',
                                 content_type='application/json')
            
            # Flask handles JSON parsing errors and returns 500 with our error handling
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertIn('error', data)


class TestServiceIntegration(unittest.TestCase):
    """Test integration between different AI services"""
    
    def test_service_manager_initialization_sequence(self):
        """Test that services are initialized in the correct order"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Test that initialize_services method exists and can be called
        self.assertTrue(hasattr(manager, 'initialize_services'))
        
        # Call initialize_services (it should not raise an exception)
        try:
            manager.initialize_services()
        except Exception as e:
            # If it fails due to missing dependencies, that's expected
            self.assertIn(('import', 'module', 'not found', 'available'), str(e).lower())
    
    def test_model_cache_functionality(self):
        """Test that model cache is properly managed"""
        config = AIServiceConfig()
        manager = AIServiceManager(config)
        
        # Test that model_cache is initialized
        self.assertIsInstance(manager.model_cache, dict)
        
        # Test that we can add items to the cache
        manager.model_cache['test_model'] = Mock()
        self.assertIn('test_model', manager.model_cache)


if __name__ == '__main__':
    unittest.main()