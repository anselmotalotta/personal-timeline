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

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import re

from .base_agent import BaseAgent
from src.common.objects.enhanced_llentry import EnhancedLLEntry, Story, Chapter


class NarrativeAgent(BaseAgent):
    """
    The Narrative Agent is responsible for creating coherent stories and narratives
    from selected personal memories. It transforms raw data into engaging,
    contextual stories that respect the user's privacy and actual experiences.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("narrative", config)
        
        # Narrative generation parameters
        self.max_chapter_sentences = self.config.get('max_chapter_sentences', 3)
        self.min_chapter_sentences = self.config.get('min_chapter_sentences', 1)
        self.narrative_styles = self.config.get('narrative_styles', ['documentary', 'memoir', 'minimalist'])
        self.default_style = self.config.get('default_style', 'documentary')
        
        # Content guidelines
        self.avoid_diagnostic_language = self.config.get('avoid_diagnostic_language', True)
        self.use_first_person = self.config.get('use_first_person', False)  # Narrator should not impersonate user
        self.grounding_required = self.config.get('grounding_required', True)
        
    def _initialize_agent(self) -> None:
        """Initialize the Narrative Agent with story generation capabilities."""
        self.logger.info("Initializing Narrative Agent story generation algorithms")
        
        # Initialize narrative templates
        self.narrative_templates = {
            'documentary': {
                'opening': "During this period, {subject} experienced {theme}.",
                'transition': "Following this, {subject} {action}.",
                'reflection': "This moment captured {significance}."
            },
            'memoir': {
                'opening': "Looking back, this was a time when {theme} shaped the experience.",
                'transition': "What followed was {action}.",
                'reflection': "The significance of this moment was {significance}."
            },
            'minimalist': {
                'opening': "{theme}.",
                'transition': "{action}.",
                'reflection': "{significance}."
            }
        }
        
        # Initialize emotional tone mapping
        self.emotional_tones = {
            'joyful': ['celebration', 'happiness', 'excitement', 'delight'],
            'reflective': ['contemplation', 'introspection', 'thoughtfulness', 'consideration'],
            'nostalgic': ['remembrance', 'wistfulness', 'longing', 'reminiscence'],
            'adventurous': ['exploration', 'discovery', 'journey', 'adventure'],
            'peaceful': ['tranquility', 'serenity', 'calm', 'contentment'],
            'growth': ['learning', 'development', 'progress', 'evolution']
        }
        
        # Initialize narrative modes
        self.narrative_modes = {
            'chronological': self._create_chronological_narrative,
            'thematic': self._create_thematic_narrative,
            'people-centered': self._create_people_centered_narrative,
            'place-centered': self._create_place_centered_narrative
        }
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Story:
        """
        Generate a narrative story from selected memories.
        
        Args:
            input_data: Story generation request or list of memories
            context: Optional context from other agents
            
        Returns:
            Generated Story object
        """
        if isinstance(input_data, dict):
            return self._process_story_request(input_data, context)
        elif isinstance(input_data, list):
            return self._create_story_from_memories(input_data, context)
        else:
            self.logger.warning(f"Unexpected input type: {type(input_data)}")
            return self._create_empty_story()
    
    def _process_story_request(self, request: Dict[str, Any], 
                             context: Optional[Dict[str, Any]] = None) -> Story:
        """
        Process a story generation request.
        
        Args:
            request: Dictionary containing story generation parameters
            context: Optional context information
            
        Returns:
            Generated Story object
        """
        memories = request.get('memories', [])
        narrative_mode = request.get('narrative_mode', 'chronological')
        narrative_style = request.get('narrative_style', self.default_style)
        title = request.get('title', '')
        
        if not memories:
            self.logger.warning("No memories provided for story generation")
            return self._create_empty_story()
        
        # Generate the story using the specified narrative mode
        if narrative_mode in self.narrative_modes:
            story = self.narrative_modes[narrative_mode](memories, narrative_style, title)
        else:
            self.logger.warning(f"Unknown narrative mode: {narrative_mode}, using chronological")
            story = self._create_chronological_narrative(memories, narrative_style, title)
        
        # Add metadata
        story.source_memory_ids = [getattr(memory, 'id', str(uuid.uuid4())) for memory in memories]
        story.created_at = datetime.now()
        
        self.logger.info(f"Generated story '{story.title}' with {len(story.chapters)} chapters")
        
        return story
    
    def _create_story_from_memories(self, memories: List[EnhancedLLEntry], 
                                  context: Optional[Dict[str, Any]] = None) -> Story:
        """
        Create a story from a list of memories using default settings.
        
        Args:
            memories: List of memories to create story from
            context: Optional context information
            
        Returns:
            Generated Story object
        """
        request = {
            'memories': memories,
            'narrative_mode': 'chronological',
            'narrative_style': self.default_style,
            'title': self._generate_title_from_memories(memories)
        }
        
        return self._process_story_request(request, context)
    
    def _create_chronological_narrative(self, memories: List[EnhancedLLEntry], 
                                      style: str, title: str) -> Story:
        """
        Create a chronological narrative from memories.
        
        Args:
            memories: List of memories to include
            style: Narrative style to use
            title: Story title
            
        Returns:
            Generated Story object
        """
        # Sort memories by time
        sorted_memories = sorted(memories, key=lambda m: getattr(m, 'startTime', datetime.min))
        
        # Group memories into chapters (by time periods or natural breaks)
        chapter_groups = self._group_memories_by_time(sorted_memories)
        
        # Generate chapters
        chapters = []
        for i, memory_group in enumerate(chapter_groups):
            chapter = self._create_chapter_from_memories(memory_group, style, f"Chapter {i+1}")
            chapters.append(chapter)
        
        story = Story(
            id=str(uuid.uuid4()),
            title=title or self._generate_title_from_memories(memories),
            narrative_mode='chronological',
            chapters=chapters,
            source_memory_ids=[],
            created_at=datetime.now()
        )
        
        return story
    
    def _create_thematic_narrative(self, memories: List[EnhancedLLEntry], 
                                 style: str, title: str) -> Story:
        """
        Create a thematic narrative from memories.
        
        Args:
            memories: List of memories to include
            style: Narrative style to use
            title: Story title
            
        Returns:
            Generated Story object
        """
        # Group memories by themes
        theme_groups = self._group_memories_by_theme(memories)
        
        # Generate chapters for each theme
        chapters = []
        for theme, memory_group in theme_groups.items():
            chapter = self._create_chapter_from_memories(memory_group, style, theme.title())
            chapters.append(chapter)
        
        story = Story(
            id=str(uuid.uuid4()),
            title=title or self._generate_thematic_title(list(theme_groups.keys())),
            narrative_mode='thematic',
            chapters=chapters,
            source_memory_ids=[],
            created_at=datetime.now()
        )
        
        return story
    
    def _create_people_centered_narrative(self, memories: List[EnhancedLLEntry], 
                                        style: str, title: str) -> Story:
        """
        Create a people-centered narrative from memories.
        
        Args:
            memories: List of memories to include
            style: Narrative style to use
            title: Story title
            
        Returns:
            Generated Story object
        """
        # Group memories by people mentioned
        people_groups = self._group_memories_by_people(memories)
        
        # Generate chapters for each person/relationship
        chapters = []
        for person, memory_group in people_groups.items():
            chapter_title = f"Moments with {person}" if person else "Solo Experiences"
            chapter = self._create_chapter_from_memories(memory_group, style, chapter_title)
            chapters.append(chapter)
        
        story = Story(
            id=str(uuid.uuid4()),
            title=title or "Stories of Connection",
            narrative_mode='people-centered',
            chapters=chapters,
            source_memory_ids=[],
            created_at=datetime.now()
        )
        
        return story
    
    def _create_place_centered_narrative(self, memories: List[EnhancedLLEntry], 
                                       style: str, title: str) -> Story:
        """
        Create a place-centered narrative from memories.
        
        Args:
            memories: List of memories to include
            style: Narrative style to use
            title: Story title
            
        Returns:
            Generated Story object
        """
        # Group memories by locations
        place_groups = self._group_memories_by_place(memories)
        
        # Generate chapters for each place
        chapters = []
        for place, memory_group in place_groups.items():
            chapter_title = f"At {place}" if place else "Unknown Places"
            chapter = self._create_chapter_from_memories(memory_group, style, chapter_title)
            chapters.append(chapter)
        
        story = Story(
            id=str(uuid.uuid4()),
            title=title or "A Journey Through Places",
            narrative_mode='place-centered',
            chapters=chapters,
            source_memory_ids=[],
            created_at=datetime.now()
        )
        
        return story
    
    def _create_chapter_from_memories(self, memories: List[EnhancedLLEntry], 
                                    style: str, chapter_title: str) -> Chapter:
        """
        Create a chapter from a group of memories.
        
        Args:
            memories: List of memories for this chapter
            style: Narrative style to use
            chapter_title: Title for the chapter
            
        Returns:
            Generated Chapter object
        """
        # Generate narrative text
        narrative_text = self._generate_chapter_narrative(memories, style)
        
        # Extract media elements
        media_elements = self._extract_media_elements(memories)
        
        # Determine emotional tone
        emotional_tone = self._determine_emotional_tone(memories)
        
        # Estimate duration (for voice narration)
        duration_seconds = self._estimate_narration_duration(narrative_text)
        
        chapter = Chapter(
            id=str(uuid.uuid4()),
            title=chapter_title,
            narrative_text=narrative_text,
            media_elements=media_elements,
            duration_seconds=duration_seconds,
            emotional_tone=emotional_tone
        )
        
        return chapter
    
    def _generate_chapter_narrative(self, memories: List[EnhancedLLEntry], style: str) -> str:
        """
        Generate narrative text for a chapter.
        
        Args:
            memories: List of memories to narrate
            style: Narrative style to use
            
        Returns:
            Generated narrative text
        """
        if not memories:
            return "This chapter contains no memories."
        
        # Get narrative templates for the style
        templates = self.narrative_templates.get(style, self.narrative_templates['documentary'])
        
        # Generate sentences (1-3 per chapter)
        sentences = []
        
        # Opening sentence
        if len(memories) == 1:
            memory = memories[0]
            theme = self._extract_theme_from_memory(memory)
            opening = templates['opening'].format(
                subject="the experience",
                theme=theme
            )
            sentences.append(opening)
        else:
            # Multiple memories - create a connecting narrative
            theme = self._extract_common_theme(memories)
            opening = templates['opening'].format(
                subject="this period",
                theme=theme
            )
            sentences.append(opening)
        
        # Add transition or reflection if we have space
        if len(sentences) < self.max_chapter_sentences and len(memories) > 1:
            action = self._extract_key_action(memories)
            transition = templates['transition'].format(
                subject="the experience",
                action=action
            )
            sentences.append(transition)
        
        # Add reflection if we have space
        if len(sentences) < self.max_chapter_sentences:
            significance = self._extract_significance(memories)
            reflection = templates['reflection'].format(
                significance=significance
            )
            sentences.append(reflection)
        
        return " ".join(sentences)
    
    def _extract_theme_from_memory(self, memory: EnhancedLLEntry) -> str:
        """Extract the main theme from a single memory."""
        if hasattr(memory, 'thematic_tags') and memory.thematic_tags:
            return memory.thematic_tags[0]
        
        if hasattr(memory, 'text') and memory.text:
            # Simple theme extraction based on keywords
            text_lower = memory.text.lower()
            for theme, keywords in [
                ('celebration', ['party', 'birthday', 'celebration', 'anniversary']),
                ('travel', ['trip', 'vacation', 'journey', 'visit']),
                ('work', ['office', 'meeting', 'work', 'project']),
                ('family', ['family', 'mom', 'dad', 'sister', 'brother']),
                ('friends', ['friend', 'friends', 'hanging out']),
                ('reflection', ['thinking', 'realized', 'learned', 'felt'])
            ]:
                if any(keyword in text_lower for keyword in keywords):
                    return theme
        
        return "a meaningful moment"
    
    def _extract_common_theme(self, memories: List[EnhancedLLEntry]) -> str:
        """Extract a common theme from multiple memories."""
        themes = [self._extract_theme_from_memory(memory) for memory in memories]
        
        # Find most common theme
        theme_counts = {}
        for theme in themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        if theme_counts:
            most_common = max(theme_counts.items(), key=lambda x: x[1])
            return most_common[0]
        
        return "various experiences"
    
    def _extract_key_action(self, memories: List[EnhancedLLEntry]) -> str:
        """Extract a key action or event from memories."""
        actions = []
        
        for memory in memories:
            if hasattr(memory, 'text') and memory.text:
                text_lower = memory.text.lower()
                # Look for action verbs
                action_patterns = [
                    ('explored', ['explored', 'discovered', 'found']),
                    ('celebrated', ['celebrated', 'enjoyed', 'partied']),
                    ('traveled', ['went to', 'visited', 'traveled']),
                    ('connected', ['met', 'talked', 'shared']),
                    ('created', ['made', 'created', 'built']),
                    ('learned', ['learned', 'realized', 'understood'])
                ]
                
                for action, keywords in action_patterns:
                    if any(keyword in text_lower for keyword in keywords):
                        actions.append(action)
                        break
        
        if actions:
            return actions[0]
        
        return "continued the journey"
    
    def _extract_significance(self, memories: List[EnhancedLLEntry]) -> str:
        """Extract the significance or meaning from memories."""
        # Look for emotional or reflective content
        significance_indicators = [
            'growth and discovery',
            'connection and community',
            'joy and celebration',
            'learning and reflection',
            'adventure and exploration',
            'peace and contentment'
        ]
        
        # Simple selection based on memory content
        for memory in memories:
            if hasattr(memory, 'emotional_context') and memory.emotional_context:
                # Use emotional context if available
                emotions = list(memory.emotional_context.keys())
                if 'joy' in emotions or 'happiness' in emotions:
                    return 'joy and celebration'
                elif 'reflection' in emotions or 'contemplation' in emotions:
                    return 'learning and reflection'
                elif 'adventure' in emotions or 'excitement' in emotions:
                    return 'adventure and exploration'
        
        # Default significance
        return 'meaningful moments in life'
    
    def _group_memories_by_time(self, memories: List[EnhancedLLEntry]) -> List[List[EnhancedLLEntry]]:
        """Group memories into time-based chapters."""
        if not memories:
            return []
        
        # Simple grouping: max 5 memories per chapter
        groups = []
        current_group = []
        
        for memory in memories:
            current_group.append(memory)
            if len(current_group) >= 5:
                groups.append(current_group)
                current_group = []
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _group_memories_by_theme(self, memories: List[EnhancedLLEntry]) -> Dict[str, List[EnhancedLLEntry]]:
        """Group memories by thematic content."""
        theme_groups = {}
        
        for memory in memories:
            theme = self._extract_theme_from_memory(memory)
            if theme not in theme_groups:
                theme_groups[theme] = []
            theme_groups[theme].append(memory)
        
        return theme_groups
    
    def _group_memories_by_people(self, memories: List[EnhancedLLEntry]) -> Dict[str, List[EnhancedLLEntry]]:
        """Group memories by people mentioned."""
        people_groups = {}
        
        for memory in memories:
            # Extract people from memory (simplified)
            people = self._extract_people_from_memory(memory)
            
            if not people:
                key = "solo"
            else:
                key = people[0]  # Use first person mentioned
            
            if key not in people_groups:
                people_groups[key] = []
            people_groups[key].append(memory)
        
        return people_groups
    
    def _group_memories_by_place(self, memories: List[EnhancedLLEntry]) -> Dict[str, List[EnhancedLLEntry]]:
        """Group memories by location."""
        place_groups = {}
        
        for memory in memories:
            place = self._extract_place_from_memory(memory)
            
            if place not in place_groups:
                place_groups[place] = []
            place_groups[place].append(memory)
        
        return place_groups
    
    def _extract_people_from_memory(self, memory: EnhancedLLEntry) -> List[str]:
        """Extract people mentioned in a memory."""
        people = []
        
        if hasattr(memory, 'people_relationships') and memory.people_relationships:
            people = [rel.person_id for rel in memory.people_relationships]
        elif hasattr(memory, 'text') and memory.text:
            # Simple name extraction (in a real implementation, this would use NER)
            text = memory.text
            # Look for common relationship terms
            relationship_terms = ['friend', 'family', 'colleague', 'partner']
            for term in relationship_terms:
                if term in text.lower():
                    people.append(term)
        
        return people
    
    def _extract_place_from_memory(self, memory: EnhancedLLEntry) -> str:
        """Extract location from a memory."""
        if hasattr(memory, 'location') and memory.location:
            return memory.location
        elif hasattr(memory, 'text') and memory.text:
            # Simple location extraction
            text_lower = memory.text.lower()
            location_indicators = ['at', 'in', 'near', 'visiting']
            for indicator in location_indicators:
                if indicator in text_lower:
                    return "various locations"
        
        return "unknown location"
    
    def _extract_media_elements(self, memories: List[EnhancedLLEntry]) -> List[str]:
        """Extract media file paths from memories."""
        media_elements = []
        
        for memory in memories:
            if hasattr(memory, 'photos') and memory.photos:
                media_elements.extend(memory.photos)
            if hasattr(memory, 'videos') and memory.videos:
                media_elements.extend(memory.videos)
        
        return media_elements
    
    def _determine_emotional_tone(self, memories: List[EnhancedLLEntry]) -> str:
        """Determine the emotional tone of a chapter."""
        # Analyze emotional context from memories
        emotion_scores = {}
        
        for memory in memories:
            if hasattr(memory, 'emotional_context') and memory.emotional_context:
                for emotion, score in memory.emotional_context.items():
                    emotion_scores[emotion] = emotion_scores.get(emotion, 0) + score
        
        if emotion_scores:
            dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            
            # Map to narrative tones
            for tone, emotions in self.emotional_tones.items():
                if dominant_emotion in emotions:
                    return tone
        
        return 'reflective'  # Default tone
    
    def _estimate_narration_duration(self, text: str) -> int:
        """Estimate narration duration in seconds."""
        # Rough estimate: 150 words per minute
        words = len(text.split())
        minutes = words / 150
        return int(minutes * 60)
    
    def _generate_title_from_memories(self, memories: List[EnhancedLLEntry]) -> str:
        """Generate a title from memories."""
        if not memories:
            return "Untitled Story"
        
        # Extract common themes or time periods
        themes = [self._extract_theme_from_memory(memory) for memory in memories]
        most_common_theme = max(set(themes), key=themes.count) if themes else "memories"
        
        # Create title based on theme
        theme_titles = {
            'celebration': 'Moments of Joy',
            'travel': 'Journey Stories',
            'work': 'Professional Chapters',
            'family': 'Family Memories',
            'friends': 'Friendship Chronicles',
            'reflection': 'Reflective Moments'
        }
        
        return theme_titles.get(most_common_theme, f"Stories of {most_common_theme.title()}")
    
    def _generate_thematic_title(self, themes: List[str]) -> str:
        """Generate a title from multiple themes."""
        if len(themes) == 1:
            return f"Stories of {themes[0].title()}"
        elif len(themes) == 2:
            return f"{themes[0].title()} and {themes[1].title()}"
        else:
            return "A Collection of Life Stories"
    
    def _create_empty_story(self) -> Story:
        """Create an empty story for error cases."""
        return Story(
            id=str(uuid.uuid4()),
            title="Empty Story",
            narrative_mode='chronological',
            chapters=[],
            source_memory_ids=[],
            created_at=datetime.now()
        )
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data for the Narrative Agent.
        
        Args:
            input_data: Data to validate
            
        Returns:
            True if input is valid
        """
        if isinstance(input_data, dict):
            return 'memories' in input_data
        elif isinstance(input_data, list):
            return all(isinstance(item, EnhancedLLEntry) for item in input_data)
        
        return False