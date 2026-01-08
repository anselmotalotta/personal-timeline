"""
Unit tests for story generation functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from src.ai_services.story_generation import StoryGenerationService, NarrativeMode, StoryRequest

class TestStoryGeneration:
    
    def setup_method(self):
        """Setup test environment"""
        self.service = StoryGenerationService(data_path="./test_data")
    
    def test_story_request_creation(self):
        """Test story request object creation"""
        request = StoryRequest(
            narrative_mode=NarrativeMode.CHRONOLOGICAL,
            theme="Family memories",
            max_chapters=5
        )
        
        assert request.narrative_mode == NarrativeMode.CHRONOLOGICAL
        assert request.theme == "Family memories"
        assert request.max_chapters == 5
        assert request.tone == "reflective"  # default
    
    def test_story_id_generation(self):
        """Test that story IDs are generated uniquely"""
        request1 = StoryRequest(narrative_mode=NarrativeMode.CHRONOLOGICAL, theme="test1")
        request2 = StoryRequest(narrative_mode=NarrativeMode.CHRONOLOGICAL, theme="test2")
        
        id1 = self.service._generate_story_id(request1)
        id2 = self.service._generate_story_id(request2)
        
        assert id1 != id2
        assert len(id1) == 12  # MD5 hash truncated to 12 chars
        assert len(id2) == 12
    
    def test_story_title_generation(self):
        """Test story title generation based on request parameters"""
        # Test themed story
        request = StoryRequest(narrative_mode=NarrativeMode.CHRONOLOGICAL, theme="adventure")
        story_data = {}
        title = self.service._generate_story_title(request, story_data)
        assert "Adventure" in title
        
        # Test people-centered story
        request = StoryRequest(
            narrative_mode=NarrativeMode.PEOPLE_CENTERED,
            focus_people=["Alice", "Bob"]
        )
        title = self.service._generate_story_title(request, story_data)
        assert "Alice" in title and "Bob" in title
    
    def test_content_parsing(self):
        """Test parsing of AI-generated content into chapters"""
        story_content = """
        Chapter 1: The Beginning
        This is the first chapter content.
        It has multiple lines.
        
        Chapter 2: The Middle
        This is the second chapter.
        More content here.
        
        Chapter 3: The End
        Final chapter content.
        """
        
        story_data = {"focus_people": ["Alice"], "focus_locations": ["Home"]}
        chapters = self.service._parse_story_content(story_content, story_data)
        
        assert len(chapters) == 3
        assert chapters[0].title == "1: The Beginning"
        assert "first chapter content" in chapters[0].content
        assert chapters[1].title == "2: The Middle"
        assert chapters[2].title == "3: The End"
        
        # Check that metadata is populated
        for chapter in chapters:
            assert chapter.people_mentioned == ["Alice"]
            assert chapter.locations == ["Home"]
    
    def test_emotional_tone_detection(self):
        """Test emotional tone detection in content"""
        # Test joyful content
        joyful_content = ["We had a happy celebration with lots of joy and excitement"]
        tone = self.service._detect_emotional_tone(joyful_content)
        assert tone == "joyful"
        
        # Test melancholic content
        sad_content = ["It was a difficult time filled with loss and sadness"]
        tone = self.service._detect_emotional_tone(sad_content)
        assert tone == "melancholic"
        
        # Test default reflective tone
        neutral_content = ["This is just some regular content"]
        tone = self.service._detect_emotional_tone(neutral_content)
        assert tone == "reflective"
    
    def test_quality_assessment(self):
        """Test story quality assessment"""
        # High quality story (long, multiple chapters)
        long_content = "This is a very long story with many words. " * 50
        chapters = [Mock(), Mock(), Mock()]  # 3 chapters
        quality = self.service._assess_story_quality(long_content, chapters)
        assert quality > 0.8
        
        # Low quality story (short, single chapter)
        short_content = "Short story."
        single_chapter = [Mock()]
        quality = self.service._assess_story_quality(short_content, single_chapter)
        assert quality < 0.8
    
    @pytest.mark.asyncio
    async def test_fallback_story_creation(self):
        """Test creation of fallback story when generation fails"""
        request = StoryRequest(
            narrative_mode=NarrativeMode.CHRONOLOGICAL,
            theme="test theme"
        )
        
        fallback = await self.service._create_fallback_story(request, "Test error")
        
        assert fallback.title == "Story Generation in Progress"
        assert len(fallback.chapters) == 1
        assert "Test error" in fallback.chapters[0].content
        assert fallback.quality_score == 0.3
        assert fallback.narrative_mode == NarrativeMode.CHRONOLOGICAL
    
    @pytest.mark.asyncio
    async def test_story_storage_and_retrieval(self):
        """Test storing and retrieving stories from database"""
        # Create a test story
        request = StoryRequest(narrative_mode=NarrativeMode.CHRONOLOGICAL)
        story = await self.service._create_fallback_story(request, "Test")
        
        # Store it
        await self.service._store_story(story)
        
        # Retrieve it
        retrieved = await self.service.get_story_by_id(story.id)
        
        assert retrieved is not None
        assert retrieved.id == story.id
        assert retrieved.title == story.title
        assert len(retrieved.chapters) == len(story.chapters)
    
    def teardown_method(self):
        """Clean up test data"""
        import os
        if os.path.exists("./test_data/stories.db"):
            os.remove("./test_data/stories.db")