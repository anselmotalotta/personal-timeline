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

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from src.common.objects.enhanced_llentry import EnhancedLLEntry, Story, Chapter
from src.common.agents.agent_coordinator import AgentCoordinator
from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector


class StoryGenerationService:
    """
    Service for generating stories from personal memories using AI agents.
    
    This service coordinates the story generation pipeline:
    1. Archivist Agent selects relevant memories
    2. Narrative Agent creates the story structure
    3. Editor Agent refines content for quality and safety
    4. Director Agent optimizes sequencing and pacing
    5. Critic Agent performs final quality checks
    6. Text-to-speech generates voice narration (optional)
    7. Multimodal composition creates final experience
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize agent coordinator
        self.agent_coordinator = AgentCoordinator(self.config.get('agents', {}))
        
        # Initialize the agent coordinator
        if not self.agent_coordinator.initialize():
            self.logger.warning("Failed to initialize agent coordinator")
        
        # Initialize database connection
        self.db = EnhancedPersonalDataDBConnector()
        
        # Initialize text-to-speech service
        self.tts_service = TextToSpeechService(self.config.get('tts', {}))
        
        # Initialize multimodal composition engine
        self.composition_engine = MultimodalCompositionEngine(self.config.get('composition', {}))
        
        # Story generation parameters
        self.supported_narrative_modes = ['chronological', 'thematic', 'people-centered', 'place-centered']
        self.supported_narrative_styles = ['documentary', 'memoir', 'minimalist']
        self.default_narrative_mode = self.config.get('default_narrative_mode', 'chronological')
        self.default_narrative_style = self.config.get('default_narrative_style', 'documentary')
        
        self.logger.info("Story Generation Service initialized")
    
    def generate_story(self, request: Dict[str, Any]) -> Story:
        """
        Generate a story from a story generation request.
        
        Args:
            request: Dictionary containing:
                - query: Optional search query for memory selection
                - theme: Optional thematic focus
                - narrative_mode: One of supported narrative modes
                - narrative_style: One of supported narrative styles
                - time_range: Optional tuple of (start_date, end_date)
                - max_memories: Maximum number of memories to include
                - include_voice_narration: Whether to generate voice narration
                - memory_ids: Optional list of specific memory IDs to use
                
        Returns:
            Generated Story object
        """
        try:
            self.logger.info(f"Starting story generation with request: {request}")
            
            # Validate request
            self._validate_story_request(request)
            
            # Step 1: Select memories using Archivist Agent
            memories = self._select_memories(request)
            
            if not memories:
                self.logger.warning("No memories selected for story generation")
                return self._create_empty_story("No memories found")
            
            # Step 2: Generate initial story using Narrative Agent
            story = self._generate_narrative(memories, request)
            
            # Step 3: Edit and refine using Editor Agent
            story = self._edit_story(story, request)
            
            # Step 4: Optimize sequencing using Director Agent
            story = self._direct_story(story, request)
            
            # Step 5: Final quality check using Critic Agent
            story = self._critique_story(story, request)
            
            # Step 6: Generate voice narration if requested
            if request.get('include_voice_narration', False):
                story = self._generate_voice_narration(story, request)
            
            # Step 7: Create multimodal composition
            story = self._create_multimodal_composition(story, request)
            
            # Step 8: Save story to database
            self.db.add_story(story)
            
            self.logger.info(f"Successfully generated story '{story.title}' with {len(story.chapters)} chapters")
            
            return story
            
        except Exception as e:
            self.logger.error(f"Error generating story: {str(e)}")
            return self._create_empty_story(f"Error: {str(e)}")
    
    def generate_story_from_memories(self, memories: List[EnhancedLLEntry], 
                                   narrative_mode: str = None,
                                   narrative_style: str = None,
                                   include_voice_narration: bool = False) -> Story:
        """
        Generate a story from a specific list of memories.
        
        Args:
            memories: List of memories to create story from
            narrative_mode: Narrative mode to use
            narrative_style: Narrative style to use
            include_voice_narration: Whether to generate voice narration
            
        Returns:
            Generated Story object
        """
        try:
            # Use the narrative agent directly for simpler story generation
            narrative_request = {
                'memories': memories,
                'narrative_mode': narrative_mode or self.default_narrative_mode,
                'narrative_style': narrative_style or self.default_narrative_style,
                'title': ''
            }
            
            # Generate story using narrative agent
            story = self.agent_coordinator.process_with_narrative(narrative_request)
            
            if not story:
                return self._create_empty_story("Failed to generate story from memories")
            
            # Apply basic editing (skip director for now due to Chapter hashing issue)
            story = self.agent_coordinator.process_with_editor(story)
            # story = self.agent_coordinator.process_with_director(story)  # Skip for now
            
            # Generate voice narration if requested
            if include_voice_narration:
                story = self._generate_voice_narration(story, {'narrator_style': narrative_style})
            
            # Create multimodal composition
            story = self._create_multimodal_composition(story, {})
            
            # Save story to database
            try:
                self.db.add_story(story)
            except Exception as e:
                self.logger.warning(f"Failed to save story to database: {str(e)}")
            
            self.logger.info(f"Successfully generated story '{story.title}' with {len(story.chapters)} chapters")
            
            return story
            
        except Exception as e:
            self.logger.error(f"Error generating story from memories: {str(e)}")
            return self._create_empty_story(f"Error: {str(e)}")
    
    def _validate_story_request(self, request: Dict[str, Any]) -> None:
        """Validate story generation request parameters."""
        narrative_mode = request.get('narrative_mode', self.default_narrative_mode)
        narrative_style = request.get('narrative_style', self.default_narrative_style)
        
        if narrative_mode not in self.supported_narrative_modes:
            raise ValueError(f"Unsupported narrative mode: {narrative_mode}")
        
        if narrative_style not in self.supported_narrative_styles:
            raise ValueError(f"Unsupported narrative style: {narrative_style}")
    
    def _select_memories(self, request: Dict[str, Any]) -> List[EnhancedLLEntry]:
        """Select memories using the Archivist Agent."""
        # If specific memory IDs are provided, use those
        if 'memory_ids' in request:
            return self._get_memories_by_ids(request['memory_ids'])
        
        # If memories are directly provided, use those
        if 'memories' in request:
            return request['memories']
        
        # Otherwise, use Archivist Agent to select memories
        archivist_request = {
            'query': request.get('query', ''),
            'theme': request.get('theme', ''),
            'narrative_mode': request.get('narrative_mode', self.default_narrative_mode),
            'time_range': request.get('time_range'),
            'max_results': request.get('max_memories', 20)
        }
        
        return self.agent_coordinator.process_with_archivist(archivist_request)
    
    def _generate_narrative(self, memories: List[EnhancedLLEntry], 
                          request: Dict[str, Any]) -> Story:
        """Generate narrative using the Narrative Agent."""
        narrative_request = {
            'memories': memories,
            'narrative_mode': request.get('narrative_mode', self.default_narrative_mode),
            'narrative_style': request.get('narrative_style', self.default_narrative_style),
            'title': request.get('title', '')
        }
        
        return self.agent_coordinator.process_with_narrative(narrative_request)
    
    def _edit_story(self, story: Story, request: Dict[str, Any]) -> Story:
        """Edit and refine story using the Editor Agent."""
        context = {
            'safety_level': request.get('safety_level', 'high'),
            'content_guidelines': request.get('content_guidelines', {})
        }
        
        return self.agent_coordinator.process_with_editor(story, context)
    
    def _direct_story(self, story: Story, request: Dict[str, Any]) -> Story:
        """Optimize story sequencing using the Director Agent."""
        context = {
            'pacing_preference': request.get('pacing_preference', 'balanced'),
            'media_distribution': request.get('media_distribution', 'even')
        }
        
        return self.agent_coordinator.process_with_director(story, context)
    
    def _critique_story(self, story: Story, request: Dict[str, Any]) -> Story:
        """Perform final quality check using the Critic Agent."""
        context = {
            'quality_standards': request.get('quality_standards', {}),
            'grounding_check': request.get('grounding_check', True)
        }
        
        return self.agent_coordinator.process_with_critic(story, context)
    
    def _generate_voice_narration(self, story: Story, request: Dict[str, Any]) -> Story:
        """Generate voice narration for the story."""
        try:
            narrator_style = request.get('narrator_style', 'documentary')
            voice_settings = request.get('voice_settings', {})
            
            # Generate narration for each chapter
            for chapter in story.chapters:
                audio_path = self.tts_service.synthesize_speech(
                    text=chapter.narrative_text,
                    style=narrator_style,
                    settings=voice_settings
                )
                
                if audio_path:
                    # Update chapter duration based on actual audio
                    chapter.duration_seconds = self.tts_service.get_audio_duration(audio_path)
            
            # Generate overall story narration file path
            story_audio_path = self.tts_service.create_story_audio(story, narrator_style)
            story.voice_narration_path = story_audio_path
            
            self.logger.info(f"Generated voice narration for story '{story.title}'")
            
        except Exception as e:
            self.logger.warning(f"Failed to generate voice narration: {str(e)}")
        
        return story
    
    def _create_multimodal_composition(self, story: Story, request: Dict[str, Any]) -> Story:
        """Create multimodal composition combining text, audio, and media."""
        try:
            composition_settings = request.get('composition_settings', {})
            
            # Enhance each chapter with multimodal elements
            for chapter in story.chapters:
                enhanced_chapter = self.composition_engine.compose_chapter(
                    chapter=chapter,
                    settings=composition_settings
                )
                
                # Update chapter with enhanced media elements
                chapter.media_elements = enhanced_chapter.media_elements
            
            self.logger.info(f"Created multimodal composition for story '{story.title}'")
            
        except Exception as e:
            self.logger.warning(f"Failed to create multimodal composition: {str(e)}")
        
        return story
    
    def _get_memories_by_ids(self, memory_ids: List[str]) -> List[EnhancedLLEntry]:
        """Retrieve memories by their IDs."""
        # For now, return empty list since we don't have this method implemented
        # In a real implementation, this would query the database
        self.logger.warning("get_memory_by_id not implemented, returning empty list")
        return []
    
    def _create_empty_story(self, reason: str) -> Story:
        """Create an empty story for error cases."""
        return Story(
            id=str(uuid.uuid4()),
            title=f"Empty Story: {reason}",
            narrative_mode='chronological',
            chapters=[],
            source_memory_ids=[],
            created_at=datetime.now()
        )
    
    def get_supported_narrative_modes(self) -> List[str]:
        """Get list of supported narrative modes."""
        return self.supported_narrative_modes.copy()
    
    def get_supported_narrative_styles(self) -> List[str]:
        """Get list of supported narrative styles."""
        return self.supported_narrative_styles.copy()


class TextToSpeechService:
    """Service for generating voice narration from text."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # TTS configuration
        self.output_dir = self.config.get('output_dir', 'personal-data/app_data/audio')
        self.sample_rate = self.config.get('sample_rate', 22050)
        self.voice_models = self.config.get('voice_models', {
            'documentary': 'neutral_narrator',
            'memoir': 'warm_narrator', 
            'minimalist': 'calm_narrator'
        })
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.logger.info("Text-to-Speech Service initialized")
    
    def synthesize_speech(self, text: str, style: str = 'documentary', 
                         settings: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            style: Narrator style
            settings: Additional TTS settings
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            # For now, create a placeholder implementation
            # In a real implementation, this would use a TTS library like:
            # - pyttsx3 for offline TTS
            # - gTTS for Google Text-to-Speech
            # - Azure Cognitive Services Speech SDK
            # - Amazon Polly SDK
            
            audio_filename = f"narration_{uuid.uuid4().hex[:8]}.wav"
            audio_path = os.path.join(self.output_dir, audio_filename)
            
            # Placeholder: Create empty audio file
            # In real implementation, generate actual audio
            with open(audio_path, 'w') as f:
                f.write(f"# Audio placeholder for: {text[:50]}...")
            
            self.logger.info(f"Generated speech synthesis placeholder: {audio_path}")
            return audio_path
            
        except Exception as e:
            self.logger.error(f"Failed to synthesize speech: {str(e)}")
            return None
    
    def get_audio_duration(self, audio_path: str) -> int:
        """Get duration of audio file in seconds."""
        # Placeholder implementation
        # In real implementation, use audio library to get actual duration
        return 30  # Default 30 seconds
    
    def create_story_audio(self, story: Story, style: str) -> Optional[str]:
        """Create combined audio file for entire story."""
        try:
            story_audio_filename = f"story_{story.id}.wav"
            story_audio_path = os.path.join(self.output_dir, story_audio_filename)
            
            # Placeholder: Create story audio file
            with open(story_audio_path, 'w') as f:
                f.write(f"# Story audio placeholder for: {story.title}")
            
            return story_audio_path
            
        except Exception as e:
            self.logger.error(f"Failed to create story audio: {str(e)}")
            return None


class MultimodalCompositionEngine:
    """Engine for creating multimodal compositions combining text, audio, and media."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Composition parameters
        self.max_media_per_chapter = self.config.get('max_media_per_chapter', 5)
        self.media_selection_strategy = self.config.get('media_selection_strategy', 'relevance')
        self.supported_media_types = self.config.get('supported_media_types', 
                                                    ['image', 'video', 'audio'])
        
        self.logger.info("Multimodal Composition Engine initialized")
    
    def compose_chapter(self, chapter: Chapter, 
                       settings: Optional[Dict[str, Any]] = None) -> Chapter:
        """
        Create multimodal composition for a chapter.
        
        Args:
            chapter: Chapter to enhance
            settings: Composition settings
            
        Returns:
            Enhanced chapter with optimized media elements
        """
        try:
            settings = settings or {}
            
            # Filter and optimize media elements
            optimized_media = self._optimize_media_selection(
                chapter.media_elements, 
                chapter.narrative_text,
                settings
            )
            
            # Update chapter with optimized media
            enhanced_chapter = Chapter(
                id=chapter.id,
                title=chapter.title,
                narrative_text=chapter.narrative_text,
                media_elements=optimized_media,
                duration_seconds=chapter.duration_seconds,
                emotional_tone=chapter.emotional_tone
            )
            
            return enhanced_chapter
            
        except Exception as e:
            self.logger.error(f"Failed to compose chapter: {str(e)}")
            return chapter
    
    def _optimize_media_selection(self, media_elements: List[str], 
                                 narrative_text: str,
                                 settings: Dict[str, Any]) -> List[str]:
        """Optimize media selection for the chapter."""
        if not media_elements:
            return []
        
        # Limit number of media elements
        max_media = settings.get('max_media_per_chapter', self.max_media_per_chapter)
        
        # For now, simple selection - take first N elements
        # In real implementation, this would use semantic similarity,
        # relevance scoring, and composition rules
        optimized_media = media_elements[:max_media]
        
        self.logger.debug(f"Optimized media selection: {len(optimized_media)} elements")
        
        return optimized_media