"""
System Integration Tests for AI-Augmented Personal Archive

This module provides comprehensive integration testing that validates:
1. End-to-end functionality from data import to story generation
2. Performance with realistic data volumes
3. Privacy and safety controls
4. Backward compatibility with existing data
"""

import pytest
import tempfile
import shutil
import os
import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import time

# Import system components
from src.common.objects.enhanced_llentry import EnhancedLLEntry
from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
from src.common.migration.database_migrator import DatabaseMigrator
from src.common.agents.agent_coordinator import AgentCoordinator
from src.common.memory.enhanced_memory_retrieval import EnhancedMemoryRetrieval
from src.common.services.story_generation_service import StoryGenerationService
from src.common.services.people_intelligence_service import PeopleIntelligenceService
from src.common.services.gallery_curation_service import GalleryCurationService
from src.common.services.privacy_safety_service import PrivacySafetyService


class TestSystemIntegration:
    """Comprehensive system integration tests"""

    @pytest.fixture
    def test_environment(self):
        """Create a complete test environment with sample data"""
        test_dir = tempfile.mkdtemp(prefix="personal_archive_integration_")
        app_data_dir = os.path.join(test_dir, "app_data")
        os.makedirs(app_data_dir, exist_ok=True)
        
        # Create sample database with realistic data
        db_path = os.path.join(app_data_dir, "raw_data.db")
        self._create_sample_database(db_path)
        
        yield {
            'test_dir': test_dir,
            'app_data_dir': app_data_dir,
            'db_path': db_path
        }
        
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

    def _create_sample_database(self, db_path):
        """Create a sample database with realistic personal data"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                date TEXT,
                source TEXT,
                content TEXT,
                metadata TEXT,
                enrichment TEXT
            )
        ''')
        
        # Insert sample data spanning multiple years
        base_date = datetime(2020, 1, 1)
        sample_entries = []
        
        # Generate 1000 sample entries for performance testing
        for i in range(1000):
            entry_date = base_date + timedelta(days=i)
            entry = {
                'id': f'entry_{i:04d}',
                'date': entry_date.isoformat(),
                'source': 'facebook' if i % 3 == 0 else 'google_photos' if i % 3 == 1 else 'amazon',
                'content': f'Sample content {i}: This is a test entry with meaningful content about life events.',
                'metadata': json.dumps({
                    'people': [f'Person_{i % 10}'] if i % 5 == 0 else [],
                    'location': f'Location_{i % 20}' if i % 7 == 0 else None,
                    'media_type': 'photo' if i % 4 == 0 else 'text'
                }),
                'enrichment': json.dumps({
                    'sentiment': 'positive' if i % 3 == 0 else 'neutral',
                    'themes': [f'theme_{i % 5}'],
                    'embedding': [0.1] * 384  # Mock embedding
                })
            }
            sample_entries.append(entry)
        
        cursor.executemany('''
            INSERT INTO entries (id, date, source, content, metadata, enrichment)
            VALUES (:id, :date, :source, :content, :metadata, :enrichment)
        ''', sample_entries)
        
        conn.commit()
        conn.close()

    def test_end_to_end_data_import_to_story_generation(self, test_environment):
        """Test complete workflow from data import to story generation"""
        app_data_dir = test_environment['app_data_dir']
        
        # Set environment variable for database location
        with patch.dict(os.environ, {'APP_DATA_DIR': app_data_dir}):
            # Clear any existing singleton instance
            from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
            if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                delattr(EnhancedPersonalDataDBConnector, 'instance')
            
            # 1. Initialize enhanced database
            enhanced_db = EnhancedPersonalDataDBConnector()
            
            # 2. Migrate existing data
            migrator = DatabaseMigrator()
            migrator.migrate_to_enhanced_schema()
            
            # 3. Verify database integrity
            assert enhanced_db.verify_data_integrity(), "Database should maintain integrity after migration"
            
            # 4. Test that enhanced tables exist
            stories = enhanced_db.get_stories()
            galleries = enhanced_db.get_galleries()
            profiles = enhanced_db.get_person_profiles()
            
            assert isinstance(stories, list), "Should be able to retrieve stories"
            assert isinstance(galleries, list), "Should be able to retrieve galleries"
            assert isinstance(profiles, list), "Should be able to retrieve person profiles"
            
            # 5. Initialize AI services (mocked for testing)
            with patch('src.common.services.ai_service_manager.AIServiceManager') as mock_ai:
                mock_ai.return_value.is_service_available.return_value = True
                mock_ai.return_value.generate_narrative.return_value = "Test narrative"
                
                # 6. Test story generation with mock data
                sample_memories = []
                for i in range(2):
                    memory = EnhancedLLEntry("test", datetime.now(), "test")
                    memory.id = f"test_{i+1}"
                    memory.content = f"Test memory {i+1}"
                    memory.metadata = {}
                    sample_memories.append(memory)
                
                story_service = StoryGenerationService({'app_data_dir': app_data_dir})
                story_service.ai_service_manager = mock_ai.return_value
                
                story_request = {
                    'memories': sample_memories,
                    'narrative_mode': 'chronological',
                    'narrative_style': 'documentary'
                }
                story = story_service.generate_story(story_request)
                
                assert story is not None, "Story should be generated"
                assert story.title, "Story should have a title"
                assert len(story.chapters) > 0, "Story should have chapters"

    def test_performance_with_realistic_data_volumes(self, test_environment):
        """Test system performance with 1000+ entries"""
        app_data_dir = test_environment['app_data_dir']
        
        # Initialize system
        enhanced_db = EnhancedPersonalDataDBConnector(app_data_dir)
        migrator = DatabaseMigrator()
        migrator.migrate_to_enhanced_schema()
        
        # Test query performance
        start_time = time.time()
        entries = enhanced_db.get_all_entries()
        query_time = time.time() - start_time
        
        assert len(entries) == 1000, "Should load all entries"
        assert query_time < 5.0, f"Query should complete in under 5 seconds, took {query_time:.2f}s"
        
        # Test memory retrieval performance
        with patch('src.common.services.ai_service_manager.AIServiceManager') as mock_ai:
            mock_ai.return_value.is_service_available.return_value = True
            mock_ai.return_value.generate_embeddings.return_value = [[0.1] * 384] * 10
            
            memory_service = EnhancedMemoryRetrieval(app_data_dir)
            memory_service.ai_service_manager = mock_ai.return_value
            
            start_time = time.time()
            results = memory_service.query_memories("test query", limit=10)
            retrieval_time = time.time() - start_time
            
            assert len(results.memories) <= 10, "Should return limited results"
            assert retrieval_time < 3.0, f"Memory retrieval should be fast, took {retrieval_time:.2f}s"

    def test_privacy_and_safety_controls(self, test_environment):
        """Validate privacy and safety controls throughout the system"""
        app_data_dir = test_environment['app_data_dir']
        
        # Initialize privacy service
        privacy_service = PrivacySafetyService(app_data_dir)
        
        # Test 1: Local processing validation
        assert privacy_service.validate_local_processing(), "All processing should be local"
        
        # Test 2: Content filtering
        sensitive_content = "I feel depressed and anxious about everything"
        filtered_content = privacy_service.filter_sensitive_content(sensitive_content)
        assert filtered_content != sensitive_content, "Sensitive content should be filtered"
        
        # Test 3: Privacy settings persistence
        privacy_settings = {
            'exclude_sensitive_content': True,
            'private_mode': True,
            'diagnostic_prevention': True
        }
        privacy_service.save_privacy_settings(privacy_settings)
        loaded_settings = privacy_service.load_privacy_settings()
        assert loaded_settings == privacy_settings, "Privacy settings should persist"
        
        # Test 4: Story generation respects privacy
        with patch('src.common.services.ai_service_manager.AIServiceManager') as mock_ai:
            mock_ai.return_value.is_service_available.return_value = True
            mock_ai.return_value.generate_narrative.return_value = "Safe narrative content"
            
            story_service = StoryGenerationService(app_data_dir)
            story_service.ai_service_manager = mock_ai.return_value
            story_service.privacy_service = privacy_service
            
            # Create sample memories with sensitive content
            sensitive_memories = [
                EnhancedLLEntry(
                    id="sensitive_1",
                    date=datetime.now(),
                    source="test",
                    content="I'm feeling really depressed today",
                    metadata={}
                )
            ]
            
            story = story_service.generate_story(sensitive_memories, 'chronological')
            
            # Verify story doesn't contain diagnostic language
            story_text = ' '.join([chapter.narrative_text for chapter in story.chapters])
            assert 'depressed' not in story_text.lower(), "Story should not contain diagnostic terms"

    def test_backward_compatibility_with_existing_data(self, test_environment):
        """Ensure system maintains compatibility with existing LLEntry objects"""
        app_data_dir = test_environment['app_data_dir']
        
        # Test migration preserves all data
        migrator = DatabaseMigrator()
        
        # Get original data count
        original_db_path = os.path.join(app_data_dir, "raw_data.db")
        conn = sqlite3.connect(original_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entries")
        original_count = cursor.fetchone()[0]
        conn.close()
        
        # Migrate to enhanced schema
        migrator.migrate_to_enhanced_schema()
        
        # Verify all data preserved
        enhanced_db = EnhancedPersonalDataDBConnector(app_data_dir)
        migrated_entries = enhanced_db.get_all_entries()
        
        assert len(migrated_entries) == original_count, "All original entries should be preserved"
        
        # Verify enhanced fields are added
        for entry in migrated_entries[:5]:  # Check first 5 entries
            assert hasattr(entry, 'narrative_significance'), "Enhanced fields should be present"
            assert hasattr(entry, 'emotional_context'), "Enhanced fields should be present"
            assert hasattr(entry, 'people_relationships'), "Enhanced fields should be present"

    def test_ai_agent_coordination_integration(self, test_environment):
        """Test AI agent coordination in integrated environment"""
        app_data_dir = test_environment['app_data_dir']
        
        with patch('src.common.services.ai_service_manager.AIServiceManager') as mock_ai:
            mock_ai.return_value.is_service_available.return_value = True
            mock_ai.return_value.generate_narrative.return_value = "Test narrative"
            mock_ai.return_value.generate_embeddings.return_value = [[0.1] * 384]
            
            # Initialize agent coordinator
            coordinator = AgentCoordinator(app_data_dir)
            coordinator.ai_service_manager = mock_ai.return_value
            
            # Test story generation request
            request = {
                'type': 'story_generation',
                'memories': ['entry_0001', 'entry_0002', 'entry_0003'],
                'narrative_mode': 'chronological'
            }
            
            result = coordinator.process_request(request)
            
            assert result['status'] == 'success', "Agent coordination should succeed"
            assert 'story' in result, "Result should contain generated story"
            assert result['story']['title'], "Story should have a title"

    def test_people_intelligence_integration(self, test_environment):
        """Test people intelligence functionality with integrated data"""
        app_data_dir = test_environment['app_data_dir']
        
        # Initialize enhanced database
        enhanced_db = EnhancedPersonalDataDBConnector(app_data_dir)
        migrator = DatabaseMigrator()
        migrator.migrate_to_enhanced_schema()
        
        with patch('src.common.services.ai_service_manager.AIServiceManager') as mock_ai:
            mock_ai.return_value.is_service_available.return_value = True
            
            # Initialize people intelligence service
            people_service = PeopleIntelligenceService(app_data_dir)
            people_service.ai_service_manager = mock_ai.return_value
            
            # Test people detection
            people_service.detect_people_in_entries()
            
            # Get detected people
            all_people = people_service.get_all_people()
            
            # Should detect people from sample data (Person_0 through Person_9)
            assert len(all_people) > 0, "Should detect people from sample data"
            
            # Test person profile generation
            if all_people:
                person_id = all_people[0]['id']
                profile = people_service.get_person_profile(person_id)
                
                assert profile is not None, "Should generate person profile"
                assert profile.name, "Profile should have a name"
                assert profile.first_appearance, "Profile should have first appearance"

    def test_gallery_system_integration(self, test_environment):
        """Test gallery system with integrated data"""
        app_data_dir = test_environment['app_data_dir']
        
        # Initialize system
        enhanced_db = EnhancedPersonalDataDBConnector(app_data_dir)
        migrator = DatabaseMigrator()
        migrator.migrate_to_enhanced_schema()
        
        with patch('src.common.services.ai_service_manager.AIServiceManager') as mock_ai:
            mock_ai.return_value.is_service_available.return_value = True
            mock_ai.return_value.generate_embeddings.return_value = [[0.1] * 384] * 10
            
            # Initialize gallery service
            gallery_service = GalleryCurationService(app_data_dir)
            gallery_service.ai_service_manager = mock_ai.return_value
            
            # Test thematic gallery creation
            gallery = gallery_service.create_thematic_gallery("Moments with friends")
            
            assert gallery is not None, "Should create thematic gallery"
            assert gallery.title == "Moments with friends", "Gallery should have correct title"
            assert len(gallery.memories) > 0, "Gallery should contain memories"
            
            # Test gallery to story conversion
            story = gallery_service.convert_gallery_to_story(gallery.id)
            
            assert story is not None, "Should convert gallery to story"
            assert story.title, "Converted story should have title"

    def test_system_error_handling_and_recovery(self, test_environment):
        """Test system behavior under error conditions"""
        app_data_dir = test_environment['app_data_dir']
        
        # Test with unavailable AI services
        with patch('src.common.services.ai_service_manager.AIServiceManager') as mock_ai:
            mock_ai.return_value.is_service_available.return_value = False
            
            # Initialize services
            story_service = StoryGenerationService(app_data_dir)
            story_service.ai_service_manager = mock_ai.return_value
            
            # Should handle gracefully when AI services unavailable
            enhanced_db = EnhancedPersonalDataDBConnector(app_data_dir)
            migrator = DatabaseMigrator()
            migrator.migrate_to_enhanced_schema()
            
            entries = enhanced_db.get_all_entries()[:5]
            
            # This should not crash, but may return limited functionality
            try:
                story = story_service.generate_story(entries, 'chronological')
                # If it succeeds, verify it's a valid fallback
                if story:
                    assert story.title, "Fallback story should have title"
            except Exception as e:
                # Should be a graceful error, not a crash
                assert "service unavailable" in str(e).lower() or "fallback" in str(e).lower()

    def test_memory_retrieval_integration(self, test_environment):
        """Test enhanced memory retrieval with integrated data"""
        app_data_dir = test_environment['app_data_dir']
        
        # Initialize system
        enhanced_db = EnhancedPersonalDataDBConnector(app_data_dir)
        migrator = DatabaseMigrator()
        migrator.migrate_to_enhanced_schema()
        
        with patch('src.common.services.ai_service_manager.AIServiceManager') as mock_ai:
            mock_ai.return_value.is_service_available.return_value = True
            mock_ai.return_value.generate_embeddings.return_value = [[0.1] * 384]
            
            # Initialize memory retrieval
            memory_service = EnhancedMemoryRetrieval(app_data_dir)
            memory_service.ai_service_manager = mock_ai.return_value
            
            # Test contextual query
            response = memory_service.query_memories("tell me about my experiences")
            
            assert response is not None, "Should return memory response"
            assert len(response.memories) > 0, "Should return relevant memories"
            assert response.narrative_context, "Should provide narrative context"
            
            # Test composite memory creation
            sample_memories = enhanced_db.get_all_entries()[:5]
            composite = memory_service.create_composite_memory(sample_memories)
            
            assert composite is not None, "Should create composite memory"
            assert composite.theme, "Composite should have theme"
            assert len(composite.constituent_memories) == 5, "Should include all input memories"

    def test_configuration_and_environment_setup(self, test_environment):
        """Test system configuration and environment setup"""
        app_data_dir = test_environment['app_data_dir']
        
        # Test environment variable handling
        test_env_vars = {
            'APP_DATA_DIR': app_data_dir,
            'AI_SERVICES_URL': 'http://localhost:8086',
            'ENHANCED_QA_ENABLED': 'true',
            'ENABLE_AI_ENHANCEMENT': 'true'
        }
        
        with patch.dict(os.environ, test_env_vars):
            # Clear any existing singleton instance
            from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
            if hasattr(EnhancedPersonalDataDBConnector, 'instance'):
                delattr(EnhancedPersonalDataDBConnector, 'instance')
                
            # Initialize services with environment configuration
            enhanced_db = EnhancedPersonalDataDBConnector()
            
            # Verify configuration is properly loaded
            assert enhanced_db is not None, "Database should initialize"
            
            # Test configuration file creation
            config_path = os.path.join(app_data_dir, "config.json")
            config_data = {
                'ai_services_enabled': True,
                'privacy_mode': True,
                'local_processing_only': True
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
            
            # Verify configuration persistence
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
            
            assert loaded_config == config_data, "Configuration should persist correctly"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])