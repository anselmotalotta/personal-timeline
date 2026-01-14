"""
AI Story Generation Service
Creates narratives from personal data using advanced language models
"""
import logging
import json
import sqlite3
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib

from .providers import provider_manager
from .config import config

logger = logging.getLogger(__name__)

class NarrativeMode(Enum):
    CHRONOLOGICAL = "chronological"
    THEMATIC = "thematic"
    PEOPLE_CENTERED = "people_centered"
    PLACE_CENTERED = "place_centered"

@dataclass
class StoryChapter:
    """Individual chapter in a story"""
    id: str
    title: str
    content: str
    media_references: List[str]
    people_mentioned: List[str]
    locations: List[str]
    time_period: Tuple[datetime, datetime]
    emotional_tone: str

@dataclass
class Story:
    """Complete story with metadata"""
    id: str
    title: str
    narrative_mode: NarrativeMode
    chapters: List[StoryChapter]
    total_media_references: List[str]
    generation_prompt: str
    quality_score: float
    generated_at: datetime
    customization_params: Dict[str, Any]

@dataclass
class StoryRequest:
    """Request for story generation"""
    narrative_mode: NarrativeMode
    theme: Optional[str] = None
    time_period: Optional[Tuple[datetime, datetime]] = None
    focus_people: Optional[List[str]] = None
    focus_locations: Optional[List[str]] = None
    max_chapters: int = 10
    tone: str = "reflective"

class StoryGenerationService:
    """AI-powered story generation from personal data"""
    
    def __init__(self, data_path: str = "./MyData"):
        self.data_path = Path(data_path)
        self.db_path = self.data_path / "stories.db"
        self._init_database()
        
    def _init_database(self):
        """Initialize story generation database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stories (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    narrative_mode TEXT NOT NULL,
                    chapters TEXT NOT NULL,
                    total_media_references TEXT,
                    generation_prompt TEXT,
                    quality_score REAL,
                    generated_at TEXT,
                    customization_params TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS story_chapters (
                    id TEXT PRIMARY KEY,
                    story_id TEXT NOT NULL,
                    chapter_order INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    media_references TEXT,
                    people_mentioned TEXT,
                    locations TEXT,
                    time_period_start TEXT,
                    time_period_end TEXT,
                    emotional_tone TEXT,
                    FOREIGN KEY (story_id) REFERENCES stories (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS story_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    narrative_mode TEXT NOT NULL,
                    template_prompt TEXT NOT NULL,
                    parameters TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_stories_mode ON stories(narrative_mode)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chapters_story ON story_chapters(story_id)")
    
    async def generate_chronological_story(self, timeframe: Tuple[datetime, datetime], theme: Optional[str] = None) -> Story:
        """Generate chronological life narrative"""
        request = StoryRequest(
            narrative_mode=NarrativeMode.CHRONOLOGICAL,
            theme=theme,
            time_period=timeframe,
            tone="chronological"
        )
        
        return await self._generate_story(request)
    
    async def generate_thematic_story(self, theme: str, time_period: Optional[Tuple[datetime, datetime]] = None) -> Story:
        """Generate story around specific theme"""
        request = StoryRequest(
            narrative_mode=NarrativeMode.THEMATIC,
            theme=theme,
            time_period=time_period,
            tone="thematic"
        )
        
        return await self._generate_story(request)
    
    async def generate_people_story(self, person_ids: List[str], theme: Optional[str] = None) -> Story:
        """Generate story focused on relationships"""
        request = StoryRequest(
            narrative_mode=NarrativeMode.PEOPLE_CENTERED,
            focus_people=person_ids,
            theme=theme,
            tone="relationship-focused"
        )
        
        return await self._generate_story(request)
    
    async def generate_place_story(self, locations: List[str], theme: Optional[str] = None) -> Story:
        """Generate story focused on places"""
        request = StoryRequest(
            narrative_mode=NarrativeMode.PLACE_CENTERED,
            focus_locations=locations,
            theme=theme,
            tone="place-focused"
        )
        
        return await self._generate_story(request)
    
    async def _generate_story(self, request: StoryRequest) -> Story:
        """Generate story based on request parameters"""
        try:
            # Gather relevant data based on request
            story_data = await self._gather_story_data(request)
            
            # Create generation prompt
            generation_prompt = self._create_generation_prompt(request, story_data)
            
            # Generate story using AI
            story_content = await provider_manager.generate_text(
                generation_prompt, 
                task_type="story_generation",
                max_tokens=2000
            )
            
            # Parse generated content into chapters
            chapters = self._parse_story_content(story_content, story_data)
            
            # Create story object
            story = Story(
                id=self._generate_story_id(request),
                title=self._generate_story_title(request, story_data),
                narrative_mode=request.narrative_mode,
                chapters=chapters,
                total_media_references=self._collect_all_media_references(chapters),
                generation_prompt=generation_prompt,
                quality_score=self._assess_story_quality(story_content, chapters),
                generated_at=datetime.now(),
                customization_params=asdict(request)
            )
            
            # Store story in database
            await self._store_story(story)
            
            logger.info(f"Generated {request.narrative_mode.value} story with {len(chapters)} chapters")
            return story
            
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            # Return a fallback story
            return await self._create_fallback_story(request, str(e))
    
    async def _gather_story_data(self, request: StoryRequest) -> Dict[str, Any]:
        """Gather relevant data for story generation"""
        story_data = {
            "photos": [],
            "people": [],
            "locations": [],
            "events": [],
            "time_range": request.time_period
        }
        
        try:
            # Import services to get real data
            from .people_intelligence import people_service
            
            # Get real people data
            people_objects = await people_service.get_all_people()
            story_data["people"] = [
                {
                    "id": person.id,
                    "name": person.name or f"Person {person.id}",
                    "photos": person.representative_photos[:3],  # Limit to 3 photos
                    "relationship_strength": person.relationship_strength,
                    "photo_count": person.photo_count
                }
                for person in people_objects
            ]
            
            # Get available photos from the file system
            photos_found = []
            if self.data_path.exists():
                for photo_path in self.data_path.rglob("*.jpg"):
                    if photo_path.is_file():
                        photos_found.append(str(photo_path))
                        if len(photos_found) >= 10:  # Limit to 10 photos for story context
                            break
            
            story_data["photos"] = photos_found
            
            # Create events from available data
            events = []
            
            # Add photo events
            for i, photo in enumerate(photos_found[:5]):  # Use first 5 photos
                events.append({
                    "type": "photo",
                    "description": f"Photo memory from {Path(photo).name}",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "media_path": photo
                })
            
            # Add people events
            for person in story_data["people"][:3]:  # Use first 3 people
                events.append({
                    "type": "person",
                    "description": f"Memories with {person['name']}",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "person_id": person["id"],
                    "photos": person["photos"]
                })
            
            story_data["events"] = events
            
        except Exception as e:
            logger.warning(f"Failed to gather real data, using fallback: {e}")
            # Fallback to basic data structure
            story_data["events"] = [
                {"type": "memory", "description": "Personal memories and experiences", "date": datetime.now().strftime("%Y-%m-%d")}
            ]
        
        # Add context strings for prompt generation
        if request.time_period:
            start_date, end_date = request.time_period
            story_data["time_context"] = f"from {start_date.strftime('%B %Y')} to {end_date.strftime('%B %Y')}"
        
        if request.focus_people:
            story_data["focus_people"] = request.focus_people
            story_data["people_context"] = f"focusing on relationships with {', '.join(request.focus_people)}"
        
        if request.focus_locations:
            story_data["focus_locations"] = request.focus_locations
            story_data["location_context"] = f"centered around {', '.join(request.focus_locations)}"
        
        if request.theme:
            story_data["theme_context"] = f"exploring the theme of {request.theme}"
        
        return story_data
    
    def _create_generation_prompt(self, request: StoryRequest, story_data: Dict[str, Any]) -> str:
        """Create AI generation prompt based on request and data"""
        base_prompt = f"""
        Create a {request.narrative_mode.value} narrative story based on personal memories and experiences.
        
        Story Parameters:
        - Narrative Mode: {request.narrative_mode.value}
        - Tone: {request.tone}
        """
        
        if request.theme:
            base_prompt += f"\n- Theme: {request.theme}"
        
        if story_data.get("time_context"):
            base_prompt += f"\n- Time Period: {story_data['time_context']}"
        
        if story_data.get("people_context"):
            base_prompt += f"\n- People Focus: {story_data['people_context']}"
        
        if story_data.get("location_context"):
            base_prompt += f"\n- Location Focus: {story_data['location_context']}"
        
        # Add real data context
        if story_data.get("people"):
            people_info = []
            for person in story_data["people"][:3]:  # Limit to 3 people
                people_info.append(f"- {person['name']}: {person['photo_count']} photos, relationship strength {person['relationship_strength']:.1f}")
            if people_info:
                base_prompt += f"\n\nPeople in your life:\n" + "\n".join(people_info)
        
        if story_data.get("photos"):
            base_prompt += f"\n\nAvailable photos: {len(story_data['photos'])} personal photos to reference"
        
        if story_data.get("events"):
            events_info = []
            for event in story_data["events"][:5]:  # Limit to 5 events
                events_info.append(f"- {event['type'].title()}: {event['description']}")
            if events_info:
                base_prompt += f"\n\nMemory events:\n" + "\n".join(events_info)
        
        base_prompt += f"""
        
        Instructions:
        1. Create a compelling narrative with {request.max_chapters} chapters or fewer
        2. Reference the real people, photos, and events mentioned above
        3. Maintain a {request.tone} tone throughout
        4. Each chapter should be 2-3 paragraphs
        5. Include emotional depth and personal reflection
        6. Make the story feel personal and authentic
        7. Structure each chapter as: "Chapter Number: Title | Date" followed by content
        
        Generate the story now:
        """
        
        return base_prompt
    
    def _parse_story_content(self, story_content: str, story_data: Dict[str, Any]) -> List[StoryChapter]:
        """Parse AI-generated content into structured chapters"""
        chapters = []
        
        # Simple parsing - split by chapter markers or paragraphs
        lines = story_content.split('\n')
        current_chapter = None
        current_content = []
        chapter_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this looks like a chapter title
            if (line.startswith('Chapter') or 
                line.startswith('#') or 
                (len(line) < 100 and ':' not in line and len(current_content) > 0)):
                
                # Save previous chapter
                if current_chapter and current_content:
                    chapters.append(StoryChapter(
                        id=f"chapter_{chapter_count}",
                        title=current_chapter,
                        content='\n'.join(current_content),
                        media_references=self._extract_media_references(current_content, story_data),
                        people_mentioned=story_data.get('focus_people', []),
                        locations=story_data.get('focus_locations', []),
                        time_period=self._estimate_chapter_timeframe(story_data),
                        emotional_tone=self._detect_emotional_tone(current_content)
                    ))
                    chapter_count += 1
                
                # Start new chapter
                current_chapter = line.replace('#', '').replace('Chapter', '').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add final chapter
        if current_chapter and current_content:
            chapters.append(StoryChapter(
                id=f"chapter_{chapter_count}",
                title=current_chapter,
                content='\n'.join(current_content),
                media_references=self._extract_media_references(current_content, story_data),
                people_mentioned=story_data.get('focus_people', []),
                locations=story_data.get('focus_locations', []),
                time_period=self._estimate_chapter_timeframe(story_data),
                emotional_tone=self._detect_emotional_tone(current_content)
            ))
        
        # If no chapters were parsed, create a single chapter
        if not chapters:
            chapters.append(StoryChapter(
                id="chapter_0",
                title="My Story",
                content=story_content,
                media_references=self._extract_media_references([story_content], story_data),
                people_mentioned=story_data.get('focus_people', []),
                locations=story_data.get('focus_locations', []),
                time_period=self._estimate_chapter_timeframe(story_data),
                emotional_tone="reflective"
            ))
        
        return chapters
    
    def _extract_media_references(self, content_lines: List[str], story_data: Dict[str, Any] = None) -> List[str]:
        """Extract media references from chapter content"""
        media_references = []
        
        # If we have story data with photos, include some of them
        if story_data and story_data.get("photos"):
            # Include up to 2 photos per chapter
            available_photos = story_data["photos"][:2]
            media_references.extend(available_photos)
        
        # If we have people data with photos, include representative photos
        if story_data and story_data.get("people"):
            for person in story_data["people"][:1]:  # One person per chapter
                if person.get("photos"):
                    media_references.extend(person["photos"][:1])  # One photo per person
        
        return media_references
    
    def _estimate_chapter_timeframe(self, story_data: Dict[str, Any]) -> Tuple[datetime, datetime]:
        """Estimate timeframe for chapter"""
        if story_data.get('time_range'):
            return story_data['time_range']
        
        # Default to current year
        now = datetime.now()
        return (now.replace(month=1, day=1), now)
    
    def _detect_emotional_tone(self, content_lines: List[str]) -> str:
        """Detect emotional tone of chapter content"""
        content = ' '.join(content_lines).lower()
        
        # Simple keyword-based tone detection
        if any(word in content for word in ['happy', 'joy', 'celebration', 'excited']):
            return 'joyful'
        elif any(word in content for word in ['sad', 'loss', 'difficult', 'challenging']):
            return 'melancholic'
        elif any(word in content for word in ['peaceful', 'calm', 'serene', 'quiet']):
            return 'peaceful'
        elif any(word in content for word in ['adventure', 'exciting', 'journey', 'discovery']):
            return 'adventurous'
        else:
            return 'reflective'
    
    def _collect_all_media_references(self, chapters: List[StoryChapter]) -> List[str]:
        """Collect all media references from chapters"""
        all_media = []
        for chapter in chapters:
            all_media.extend(chapter.media_references)
        return list(set(all_media))  # Remove duplicates
    
    def _assess_story_quality(self, story_content: str, chapters: List[StoryChapter]) -> float:
        """Assess the quality of generated story"""
        quality_score = 0.5  # Base score
        
        # Length factor
        if len(story_content) > 500:
            quality_score += 0.2
        
        # Chapter structure
        if len(chapters) > 1:
            quality_score += 0.2
        
        # Content diversity (simple check)
        unique_words = len(set(story_content.lower().split()))
        if unique_words > 100:
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def _generate_story_id(self, request: StoryRequest) -> str:
        """Generate unique story ID"""
        content = f"{request.narrative_mode.value}_{request.theme}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _generate_story_title(self, request: StoryRequest, story_data: Dict[str, Any]) -> str:
        """Generate appropriate story title"""
        if request.theme:
            return f"A Story of {request.theme.title()}"
        elif request.narrative_mode == NarrativeMode.CHRONOLOGICAL:
            if story_data.get('time_context'):
                return f"My Journey: {story_data['time_context']}"
            return "My Life Story"
        elif request.narrative_mode == NarrativeMode.PEOPLE_CENTERED:
            if request.focus_people:
                return f"Stories with {', '.join(request.focus_people)}"
            return "Stories of Connection"
        elif request.narrative_mode == NarrativeMode.PLACE_CENTERED:
            if request.focus_locations:
                return f"Memories from {', '.join(request.focus_locations)}"
            return "Places in My Heart"
        else:
            return "My Personal Story"
    
    async def _create_fallback_story(self, request: StoryRequest, error_message: str) -> Story:
        """Create a fallback story when generation fails"""
        fallback_chapter = StoryChapter(
            id="fallback_chapter",
            title="A Story in Progress",
            content=f"This is a placeholder for your {request.narrative_mode.value} story. "
                   f"The story generation encountered an issue: {error_message}. "
                   f"Your memories and experiences are valuable and deserve to be told. "
                   f"Please try generating the story again.",
            media_references=[],
            people_mentioned=request.focus_people or [],
            locations=request.focus_locations or [],
            time_period=(datetime.now() - timedelta(days=365), datetime.now()),
            emotional_tone="hopeful"
        )
        
        return Story(
            id=self._generate_story_id(request),
            title="Story Generation in Progress",
            narrative_mode=request.narrative_mode,
            chapters=[fallback_chapter],
            total_media_references=[],
            generation_prompt="Fallback story due to generation error",
            quality_score=0.3,
            generated_at=datetime.now(),
            customization_params=asdict(request)
        )
    
    async def _store_story(self, story: Story):
        """Store story in database"""
        with sqlite3.connect(self.db_path) as conn:
            # Store main story record
            conn.execute("""
                INSERT OR REPLACE INTO stories 
                (id, title, narrative_mode, chapters, total_media_references, 
                 generation_prompt, quality_score, generated_at, customization_params)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                story.id,
                story.title,
                story.narrative_mode.value,
                json.dumps([asdict(chapter) for chapter in story.chapters], default=str),
                json.dumps(story.total_media_references),
                story.generation_prompt,
                story.quality_score,
                story.generated_at.isoformat(),
                json.dumps(story.customization_params, default=str)
            ))
            
            # Store individual chapters
            for i, chapter in enumerate(story.chapters):
                conn.execute("""
                    INSERT OR REPLACE INTO story_chapters 
                    (id, story_id, chapter_order, title, content, media_references, 
                     people_mentioned, locations, time_period_start, time_period_end, emotional_tone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chapter.id,
                    story.id,
                    i,
                    chapter.title,
                    chapter.content,
                    json.dumps(chapter.media_references),
                    json.dumps(chapter.people_mentioned),
                    json.dumps(chapter.locations),
                    chapter.time_period[0].isoformat(),
                    chapter.time_period[1].isoformat(),
                    chapter.emotional_tone
                ))
    
    async def get_story_by_id(self, story_id: str) -> Optional[Story]:
        """Retrieve story by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            result = conn.execute("SELECT * FROM stories WHERE id = ?", (story_id,)).fetchone()
            
            if not result:
                return None
            
            # Load chapters
            chapters_data = json.loads(result['chapters'])
            chapters = []
            for chapter_data in chapters_data:
                chapter = StoryChapter(
                    id=chapter_data['id'],
                    title=chapter_data['title'],
                    content=chapter_data['content'],
                    media_references=chapter_data['media_references'],
                    people_mentioned=chapter_data['people_mentioned'],
                    locations=chapter_data['locations'],
                    time_period=(
                        datetime.fromisoformat(chapter_data['time_period'][0]),
                        datetime.fromisoformat(chapter_data['time_period'][1])
                    ),
                    emotional_tone=chapter_data['emotional_tone']
                )
                chapters.append(chapter)
            
            return Story(
                id=result['id'],
                title=result['title'],
                narrative_mode=NarrativeMode(result['narrative_mode']),
                chapters=chapters,
                total_media_references=json.loads(result['total_media_references']),
                generation_prompt=result['generation_prompt'],
                quality_score=result['quality_score'],
                generated_at=datetime.fromisoformat(result['generated_at']),
                customization_params=json.loads(result['customization_params'])
            )
    
    async def get_all_stories(self) -> List[Story]:
        """Get all generated stories"""
        stories = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            results = conn.execute("SELECT * FROM stories ORDER BY generated_at DESC").fetchall()
            
            for result in results:
                story = await self.get_story_by_id(result['id'])
                if story:
                    stories.append(story)
        
        return stories
    
    async def delete_story(self, story_id: str) -> bool:
        """Delete a story and its chapters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM story_chapters WHERE story_id = ?", (story_id,))
                conn.execute("DELETE FROM stories WHERE id = ?", (story_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to delete story {story_id}: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get story generation service status"""
        with sqlite3.connect(self.db_path) as conn:
            story_count = conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0]
            chapter_count = conn.execute("SELECT COUNT(*) FROM story_chapters").fetchone()[0]
            
            # Get story statistics by mode
            mode_stats = {}
            for mode in NarrativeMode:
                count = conn.execute(
                    "SELECT COUNT(*) FROM stories WHERE narrative_mode = ?", 
                    (mode.value,)
                ).fetchone()[0]
                mode_stats[mode.value] = count
            
            return {
                "service": "story_generation",
                "status": "active",
                "statistics": {
                    "total_stories": story_count,
                    "total_chapters": chapter_count,
                    "stories_by_mode": mode_stats
                },
                "database_path": str(self.db_path)
            }

# Global service instance
story_service = StoryGenerationService()