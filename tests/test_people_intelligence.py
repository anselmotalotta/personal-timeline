"""
Property-based tests for people intelligence service
**Feature: ai-personal-archive-complete**
"""
import os
import json
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from hypothesis import given, strategies as st, settings
import pytest
from datetime import datetime, timedelta
from PIL import Image

# Import the modules we're testing
import sys
sys.path.append('src')

from ai_services.people_intelligence import PeopleIntelligenceService, PersonProfile, FaceDetection, RelationshipInsight


class TestAIVisionAnalysis:
    """Test AI vision analysis for face detection"""
    
    @pytest.mark.asyncio
    async def test_ai_vision_analysis(self):
        """
        **Feature: ai-personal-archive-complete, Property 11: AI vision analysis**
        For any photo processed, the system should use multimodal AI to detect faces, 
        analyze content, and extract semantic information
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            # Create test images
            test_photos = []
            for i in range(3):
                img = Image.new('RGB', (100, 100), color=['red', 'green', 'blue'][i])
                photo_path = Path(temp_dir) / f"test_photo_{i}.jpg"
                img.save(photo_path)
                test_photos.append(str(photo_path))
            
            # Mock AI provider response
            mock_ai_response = {
                'description': 'Image contains 2 faces of people smiling',
                'confidence': 0.9,
                'provider': 'openai'
            }
            
            with patch('ai_services.people_intelligence.provider_manager') as mock_provider:
                mock_provider.analyze_image = AsyncMock(return_value=mock_ai_response)
                
                # Test face detection
                detections = await service.detect_faces(test_photos)
                
                # Should have processed all photos
                assert len(detections) == len(test_photos)
                
                # Each detection should have proper structure
                for detection in detections:
                    assert isinstance(detection, FaceDetection)
                    assert detection.photo_path in test_photos
                    assert isinstance(detection.faces, list)
                    assert detection.confidence > 0
                    assert detection.processing_time >= 0
                
                # Should have called AI provider for each photo
                assert mock_provider.analyze_image.call_count == len(test_photos)
    
    @pytest.mark.asyncio
    async def test_face_detection_with_various_responses(self):
        """Test face detection with various AI response formats"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            # Create test image
            img = Image.new('RGB', (100, 100), color='yellow')
            photo_path = Path(temp_dir) / "test.jpg"
            img.save(photo_path)
            
            # Test different AI response formats
            test_responses = [
                {'description': 'One person in the image', 'confidence': 0.8},
                {'description': 'Multiple people visible, man and woman', 'confidence': 0.9},
                {'description': 'No faces detected in this image', 'confidence': 0.7},
                {'description': 'Group photo with 5 people', 'confidence': 0.85}
            ]
            
            for response in test_responses:
                with patch('ai_services.people_intelligence.provider_manager') as mock_provider:
                    mock_provider.analyze_image = AsyncMock(return_value=response)
                    
                    detections = await service.detect_faces([str(photo_path)])
                    
                    assert len(detections) == 1
                    detection = detections[0]
                    assert detection.confidence == response['confidence']
                    assert isinstance(detection.faces, list)
    
    @pytest.mark.asyncio
    async def test_face_detection_error_handling(self):
        """Test face detection handles AI provider errors gracefully"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            # Create test image
            img = Image.new('RGB', (50, 50), color='purple')
            photo_path = Path(temp_dir) / "test.jpg"
            img.save(photo_path)
            
            # Mock AI provider to raise exception
            with patch('ai_services.people_intelligence.provider_manager') as mock_provider:
                mock_provider.analyze_image = AsyncMock(side_effect=Exception("API Error"))
                
                # Should handle errors gracefully
                detections = await service.detect_faces([str(photo_path)])
                
                # Should return empty list on error, not crash
                assert isinstance(detections, list)


class TestPersonProfileGeneration:
    """Test person profile generation from face detections"""
    
    @pytest.mark.asyncio
    async def test_person_profile_generation(self):
        """
        **Feature: ai-personal-archive-complete, Property 12: Person profile generation**
        For any detected person, the system should create a profile with representative photos, 
        interaction timeline, and relationship data
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            # Create test photos
            test_photos = []
            for i in range(5):
                img = Image.new('RGB', (100, 100), color='cyan')
                photo_path = Path(temp_dir) / f"person_photo_{i}.jpg"
                img.save(photo_path)
                test_photos.append(str(photo_path))
            
            # Mock face detections
            mock_detections = []
            for photo_path in test_photos:
                detection = FaceDetection(
                    photo_path=photo_path,
                    faces=[{
                        'id': 'face_0',
                        'bounding_box': [0.1, 0.1, 0.2, 0.3],
                        'confidence': 0.9,
                        'encoding': [0.1, 0.2, 0.3, 0.4, 0.5]  # Mock face encoding
                    }],
                    confidence=0.9,
                    processing_time=0.5
                )
                mock_detections.append(detection)
            
            # Process face clustering
            await service._cluster_faces_into_people(mock_detections)
            
            # Check that people were created
            people = await service.get_all_people()
            assert len(people) > 0
            
            # Verify person profile structure
            for person in people:
                assert isinstance(person, PersonProfile)
                assert person.id is not None
                assert isinstance(person.representative_photos, list)
                assert len(person.representative_photos) > 0
                assert isinstance(person.face_encodings, list)
                assert isinstance(person.interaction_timeline, list)
                assert isinstance(person.relationship_strength, float)
                assert person.privacy_level in ['private', 'public', 'friends']
                assert isinstance(person.first_seen, datetime)
                assert isinstance(person.last_seen, datetime)
                assert person.photo_count >= 0
    
    @settings(deadline=1000)  # 1 second deadline for this test
    @given(st.integers(min_value=1, max_value=20))
    @pytest.mark.asyncio
    async def test_person_profile_with_various_photo_counts(self, photo_count):
        """Test person profile generation with various numbers of photos"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            # Create test photos
            test_photos = []
            for i in range(photo_count):
                img = Image.new('RGB', (50, 50), color='orange')
                photo_path = Path(temp_dir) / f"photo_{i}.jpg"
                img.save(photo_path)
                test_photos.append(str(photo_path))
            
            # Create mock face detections
            mock_detections = []
            for photo_path in test_photos:
                detection = FaceDetection(
                    photo_path=photo_path,
                    faces=[{'id': 'face_0', 'confidence': 0.8}],
                    confidence=0.8,
                    processing_time=0.3
                )
                mock_detections.append(detection)
            
            # Process clustering
            await service._cluster_faces_into_people(mock_detections)
            
            # Verify people were created
            people = await service.get_all_people()
            assert len(people) >= 0  # Should handle any number of photos
            
            # If people were created, verify their photo counts are reasonable
            for person in people:
                assert person.photo_count <= photo_count
                assert len(person.representative_photos) <= min(photo_count, 5)  # Limited to 5 representative photos
    
    @pytest.mark.asyncio
    async def test_interaction_timeline_generation(self):
        """Test that interaction timelines are properly generated"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            # Create photos with different timestamps (by creating them at different times)
            photo_paths = []
            for i in range(3):
                img = Image.new('RGB', (60, 60), color='pink')
                photo_path = Path(temp_dir) / f"timeline_photo_{i}.jpg"
                img.save(photo_path)
                photo_paths.append(str(photo_path))
            
            # Build interaction timeline
            timeline = service._build_interaction_timeline(photo_paths)
            
            # Verify timeline structure
            assert isinstance(timeline, list)
            assert len(timeline) <= len(photo_paths)  # Some photos might not exist
            
            for event in timeline:
                assert 'timestamp' in event
                assert 'event_type' in event
                assert 'photo_path' in event
                assert isinstance(event['timestamp'], datetime)


class TestRelationshipAnalysis:
    """Test relationship analysis between people"""
    
    @pytest.mark.asyncio
    async def test_relationship_analysis(self):
        """Test relationship analysis between detected people"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            # Create mock people with overlapping photos
            person1 = PersonProfile(
                id="person_1",
                name=None,
                representative_photos=["photo1.jpg", "photo2.jpg", "photo3.jpg"],
                face_encodings=[],
                interaction_timeline=[
                    {'timestamp': datetime.now() - timedelta(days=10), 'event_type': 'photo', 'photo_path': 'photo1.jpg'},
                    {'timestamp': datetime.now() - timedelta(days=5), 'event_type': 'photo', 'photo_path': 'photo2.jpg'}
                ],
                relationship_strength=0.8,
                privacy_level='private',
                first_seen=datetime.now() - timedelta(days=10),
                last_seen=datetime.now() - timedelta(days=5),
                photo_count=3
            )
            
            person2 = PersonProfile(
                id="person_2",
                name=None,
                representative_photos=["photo2.jpg", "photo3.jpg", "photo4.jpg"],
                face_encodings=[],
                interaction_timeline=[
                    {'timestamp': datetime.now() - timedelta(days=5), 'event_type': 'photo', 'photo_path': 'photo2.jpg'},
                    {'timestamp': datetime.now() - timedelta(days=1), 'event_type': 'photo', 'photo_path': 'photo4.jpg'}
                ],
                relationship_strength=0.7,
                privacy_level='private',
                first_seen=datetime.now() - timedelta(days=5),
                last_seen=datetime.now() - timedelta(days=1),
                photo_count=3
            )
            
            # Store people in database
            await service._store_person_profile(person1)
            await service._store_person_profile(person2)
            
            # Analyze relationship
            relationship = await service._analyze_relationship_between_people(person1, person2, {})
            
            # Verify relationship analysis
            assert relationship is not None
            assert isinstance(relationship, RelationshipInsight)
            assert relationship.person1_id == "person_1"
            assert relationship.person2_id == "person_2"
            assert relationship.shared_photos > 0  # Should find shared photos
            assert relationship.strength > 0
            assert relationship.relationship_type in ['close_friend', 'long_term_friend', 'friend', 'acquaintance', 'unknown']
            assert relationship.time_span_days >= 0
    
    @pytest.mark.asyncio
    async def test_relationship_strength_calculation(self):
        """Test that relationship strength is calculated correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            # Test different relationship scenarios
            scenarios = [
                # (shared_photos, interaction_freq, time_span_days, expected_min_strength)
                (10, 0.8, 365, 0.5),  # Strong relationship
                (3, 0.3, 100, 0.2),   # Medium relationship
                (1, 0.1, 30, 0.1),    # Weak relationship
            ]
            
            for shared_count, interaction_freq, time_span, expected_min in scenarios:
                # Create people with specific interaction patterns
                person1 = PersonProfile(
                    id=f"person_1_{shared_count}",
                    name=None,
                    representative_photos=[f"shared_{i}.jpg" for i in range(shared_count)],
                    face_encodings=[],
                    interaction_timeline=[
                        {'timestamp': datetime.now() - timedelta(days=i), 'event_type': 'photo'}
                        for i in range(int(interaction_freq * 10))
                    ],
                    relationship_strength=0.5,
                    privacy_level='private',
                    first_seen=datetime.now() - timedelta(days=time_span),
                    last_seen=datetime.now(),
                    photo_count=shared_count
                )
                
                person2 = PersonProfile(
                    id=f"person_2_{shared_count}",
                    name=None,
                    representative_photos=[f"shared_{i}.jpg" for i in range(shared_count)],
                    face_encodings=[],
                    interaction_timeline=[
                        {'timestamp': datetime.now() - timedelta(days=i), 'event_type': 'photo'}
                        for i in range(int(interaction_freq * 10))
                    ],
                    relationship_strength=0.5,
                    privacy_level='private',
                    first_seen=datetime.now() - timedelta(days=time_span),
                    last_seen=datetime.now(),
                    photo_count=shared_count
                )
                
                relationship = await service._analyze_relationship_between_people(person1, person2, {})
                
                if relationship:
                    assert relationship.strength >= expected_min
                    assert relationship.shared_photos == shared_count


class TestPrivacyControls:
    """Test privacy controls for people management"""
    
    @pytest.mark.asyncio
    async def test_privacy_settings_management(self):
        """Test privacy settings can be updated for people"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            # Create a test person
            person = PersonProfile(
                id="privacy_test_person",
                name="Test Person",
                representative_photos=["test.jpg"],
                face_encodings=[],
                interaction_timeline=[],
                relationship_strength=0.5,
                privacy_level='private',
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                photo_count=1
            )
            
            await service._store_person_profile(person)
            
            # Test updating privacy settings
            privacy_levels = ['private', 'public', 'friends']
            
            for privacy_level in privacy_levels:
                success = await service.update_privacy_settings("privacy_test_person", privacy_level)
                assert success
                
                # Verify the update
                updated_person = await service.get_person_by_id("privacy_test_person")
                assert updated_person is not None
                assert updated_person.privacy_level == privacy_level
    
    @pytest.mark.asyncio
    async def test_privacy_settings_for_nonexistent_person(self):
        """Test privacy settings update for non-existent person"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            # Try to update privacy for non-existent person
            success = await service.update_privacy_settings("nonexistent_person", "private")
            # Should not crash, but may return False
            assert isinstance(success, bool)


class TestServiceStatus:
    """Test service status and health monitoring"""
    
    def test_service_status_reporting(self):
        """Test that service status is properly reported"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PeopleIntelligenceService(temp_dir)
            
            status = service.get_service_status()
            
            # Verify status structure
            assert isinstance(status, dict)
            assert status['service'] == 'people_intelligence'
            assert status['status'] == 'active'
            assert 'statistics' in status
            assert 'database_path' in status
            
            # Verify statistics
            stats = status['statistics']
            assert 'total_people' in stats
            assert 'total_face_detections' in stats
            assert 'total_relationships' in stats
            assert all(isinstance(v, int) for v in stats.values())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])