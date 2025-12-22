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
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re

from src.common.objects.enhanced_llentry import EnhancedLLEntry, Gallery, Story
from src.common.agents.agent_coordinator import AgentCoordinator
from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
from src.common.services.story_generation_service import StoryGenerationService


class GalleryCurationService:
    """
    Service for creating and managing intelligent galleries that replace basic filtering.
    
    This service provides:
    1. Thematic gallery generation using AI agents
    2. Natural language prompt processing for custom galleries
    3. Semantic ordering algorithms for optimal presentation
    4. AI-written contextual introductions
    5. Gallery-to-story conversion functionality
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
        
        # Initialize story generation service for gallery-to-story conversion
        self.story_service = None  # Lazy initialization to avoid circular dependency
        
        # Predefined thematic galleries
        self.default_thematic_galleries = [
            "Moments with friends",
            "Creative periods", 
            "Times of growth",
            "Travel adventures",
            "Family gatherings",
            "Professional milestones",
            "Seasonal memories",
            "Learning experiences",
            "Celebrations and achievements",
            "Quiet reflections"
        ]
        
        # Gallery generation parameters
        self.max_memories_per_gallery = self.config.get('max_memories_per_gallery', 50)
        self.min_memories_per_gallery = self.config.get('min_memories_per_gallery', 3)
        self.semantic_similarity_threshold = self.config.get('semantic_similarity_threshold', 0.7)
        
        self.logger.info("Gallery Curation Service initialized")
    
    def initialize_default_galleries(self) -> List[Gallery]:
        """
        Initialize default thematic galleries to replace basic filtering.
        
        Returns:
            List of created default galleries
        """
        try:
            self.logger.info("Initializing default thematic galleries")
            
            created_galleries = []
            
            for theme in self.default_thematic_galleries:
                try:
                    gallery = self.create_thematic_gallery(theme)
                    if gallery and len(gallery.memory_ids) >= self.min_memories_per_gallery:
                        created_galleries.append(gallery)
                        self.logger.info(f"Created default gallery '{theme}' with {len(gallery.memory_ids)} memories")
                    else:
                        self.logger.info(f"Skipped gallery '{theme}' - insufficient memories")
                except Exception as e:
                    self.logger.warning(f"Failed to create default gallery '{theme}': {str(e)}")
            
            self.logger.info(f"Successfully initialized {len(created_galleries)} default galleries")
            return created_galleries
            
        except Exception as e:
            self.logger.error(f"Error initializing default galleries: {str(e)}")
            return []
    
    def create_thematic_gallery(self, theme: str) -> Optional[Gallery]:
        """
        Create a thematic gallery using AI-generated collections based on semantic similarity.
        
        Args:
            theme: The thematic focus for the gallery
            
        Returns:
            Created Gallery object or None if creation failed
        """
        try:
            self.logger.info(f"Creating thematic gallery for theme: {theme}")
            
            # Use Archivist Agent to select relevant memories for the theme
            archivist_request = {
                'query': theme,
                'theme': theme,
                'narrative_mode': 'thematic',
                'max_results': self.max_memories_per_gallery
            }
            
            memories = self.agent_coordinator.process_with_archivist(archivist_request)
            
            if not memories or len(memories) < self.min_memories_per_gallery:
                self.logger.warning(f"Insufficient memories found for theme '{theme}': {len(memories) if memories else 0}")
                return None
            
            # Create semantic ordering using Director Agent
            semantic_ordering = self._create_semantic_ordering(memories, theme)
            
            # Generate AI-written contextual introduction using Narrative Agent
            description = self._generate_gallery_description(memories, theme)
            
            # Create gallery object
            gallery = Gallery(
                id=str(uuid.uuid4()),
                title=self._generate_gallery_title(theme, len(memories)),
                description=description,
                memory_ids=[memory.id for memory in memories],
                creation_method='thematic',
                semantic_ordering=semantic_ordering,
                created_at=datetime.now()
            )
            
            # Save gallery to database
            self.db.add_gallery(gallery)
            
            self.logger.info(f"Successfully created thematic gallery '{gallery.title}' with {len(memories)} memories")
            return gallery
            
        except Exception as e:
            self.logger.error(f"Error creating thematic gallery for '{theme}': {str(e)}")
            return None
    
    def generate_from_prompt(self, prompt: str) -> Optional[Gallery]:
        """
        Create a custom gallery from natural language prompt that goes beyond current search capabilities.
        
        Args:
            prompt: Natural language description of desired gallery
            
        Returns:
            Created Gallery object or None if creation failed
        """
        try:
            self.logger.info(f"Creating gallery from prompt: {prompt}")
            
            # Parse the prompt to extract themes and criteria
            parsed_criteria = self._parse_natural_language_prompt(prompt)
            
            # Use Archivist Agent to select memories based on parsed criteria
            archivist_request = {
                'query': prompt,
                'theme': parsed_criteria.get('theme', ''),
                'narrative_mode': parsed_criteria.get('narrative_mode', 'thematic'),
                'time_range': parsed_criteria.get('time_range'),
                'max_results': self.max_memories_per_gallery
            }
            
            memories = self.agent_coordinator.process_with_archivist(archivist_request)
            
            if not memories or len(memories) < self.min_memories_per_gallery:
                self.logger.warning(f"Insufficient memories found for prompt '{prompt}': {len(memories) if memories else 0}")
                return None
            
            # Create semantic ordering
            semantic_ordering = self._create_semantic_ordering(memories, prompt)
            
            # Generate contextual description
            description = self._generate_gallery_description(memories, prompt)
            
            # Generate title from prompt
            title = self._generate_gallery_title_from_prompt(prompt, len(memories))
            
            # Create gallery object
            gallery = Gallery(
                id=str(uuid.uuid4()),
                title=title,
                description=description,
                memory_ids=[memory.id for memory in memories],
                creation_method='prompt',
                semantic_ordering=semantic_ordering,
                created_at=datetime.now()
            )
            
            # Save gallery to database
            self.db.add_gallery(gallery)
            
            self.logger.info(f"Successfully created prompt-based gallery '{gallery.title}' with {len(memories)} memories")
            return gallery
            
        except Exception as e:
            self.logger.error(f"Error creating gallery from prompt '{prompt}': {str(e)}")
            return None
    
    def convert_gallery_to_story(self, gallery_id: str, 
                               narrative_mode: str = 'thematic',
                               narrative_style: str = 'documentary',
                               include_voice_narration: bool = False) -> Optional[Story]:
        """
        Transform a static gallery into a narrative experience.
        
        Args:
            gallery_id: ID of the gallery to convert
            narrative_mode: Narrative mode for story generation
            narrative_style: Narrative style for story generation
            include_voice_narration: Whether to include voice narration
            
        Returns:
            Generated Story object or None if conversion failed
        """
        try:
            self.logger.info(f"Converting gallery {gallery_id} to story")
            
            # Retrieve gallery from database
            gallery = self._get_gallery_by_id(gallery_id)
            if not gallery:
                self.logger.error(f"Gallery {gallery_id} not found")
                return None
            
            # Retrieve memories for the gallery
            memories = self._get_memories_by_ids(gallery.memory_ids)
            if not memories:
                self.logger.error(f"No memories found for gallery {gallery_id}")
                return None
            
            # Order memories according to semantic ordering
            ordered_memories = self._apply_semantic_ordering(memories, gallery.semantic_ordering)
            
            # Initialize story service if not already done
            if not self.story_service:
                self.story_service = StoryGenerationService(self.config.get('story_generation', {}))
            
            # Generate story from ordered memories
            story = self.story_service.generate_story_from_memories(
                memories=ordered_memories,
                narrative_mode=narrative_mode,
                narrative_style=narrative_style,
                include_voice_narration=include_voice_narration
            )
            
            if story:
                # Update story title to reference the gallery
                story.title = f"Story from Gallery: {gallery.title}"
                self.logger.info(f"Successfully converted gallery '{gallery.title}' to story '{story.title}'")
            
            return story
            
        except Exception as e:
            self.logger.error(f"Error converting gallery {gallery_id} to story: {str(e)}")
            return None
    
    def get_all_galleries(self) -> List[Gallery]:
        """
        Retrieve all galleries from the database.
        
        Returns:
            List of Gallery objects
        """
        try:
            # Get galleries from database
            gallery_data = self.db.get_galleries()
            
            galleries = []
            for data in gallery_data:
                gallery = Gallery(
                    id=data['id'],
                    title=data['title'],
                    description=data['description'],
                    memory_ids=data['memory_ids'],
                    creation_method=data['creation_method'],
                    semantic_ordering=data['semantic_ordering'],
                    created_at=datetime.fromisoformat(data['created_at'])
                )
                galleries.append(gallery)
            
            return galleries
            
        except Exception as e:
            self.logger.error(f"Error retrieving galleries: {str(e)}")
            return []
    
    def _create_semantic_ordering(self, memories: List[EnhancedLLEntry], theme: str) -> List[int]:
        """
        Create semantic ordering using intelligent arrangement beyond chronological.
        
        Args:
            memories: List of memories to order
            theme: Theme or context for ordering
            
        Returns:
            List of indices representing optimal display order
        """
        try:
            # Use Director Agent to create optimal sequencing
            director_request = {
                'memories': memories,
                'theme': theme,
                'ordering_strategy': 'semantic',
                'pacing_preference': 'balanced'
            }
            
            # For now, use a simple implementation
            # In a full implementation, this would use the Director Agent
            # to create sophisticated semantic ordering based on:
            # - Narrative flow
            # - Emotional progression
            # - Temporal coherence
            # - Visual composition
            
            # Simple semantic ordering: group by similarity, then chronological within groups
            ordered_indices = list(range(len(memories)))
            
            # Sort by story potential and narrative significance
            ordered_indices.sort(key=lambda i: (
                memories[i].story_potential,
                memories[i].narrative_significance,
                memories[i].startTime
            ), reverse=True)
            
            return ordered_indices
            
        except Exception as e:
            self.logger.warning(f"Error creating semantic ordering: {str(e)}")
            # Fallback to chronological ordering
            return list(range(len(memories)))
    
    def _generate_gallery_description(self, memories: List[EnhancedLLEntry], theme: str) -> str:
        """
        Generate AI-written contextual introduction for the gallery.
        
        Args:
            memories: Memories in the gallery
            theme: Gallery theme
            
        Returns:
            Generated description text
        """
        try:
            # Use Narrative Agent to create contextual introduction
            narrative_request = {
                'memories': memories,
                'theme': theme,
                'task': 'gallery_introduction',
                'style': 'contextual'
            }
            
            # For now, create a simple description
            # In a full implementation, this would use the Narrative Agent
            time_span = self._get_memory_time_span(memories)
            memory_count = len(memories)
            
            if theme in self.default_thematic_galleries:
                description = f"A curated collection of {memory_count} memories exploring {theme.lower()}. "
            else:
                description = f"A personalized gallery of {memory_count} memories centered around {theme}. "
            
            if time_span:
                start_year = time_span[0].year
                end_year = time_span[1].year
                if start_year == end_year:
                    description += f"These moments capture experiences from {start_year}."
                else:
                    description += f"These moments span from {start_year} to {end_year}."
            
            return description
            
        except Exception as e:
            self.logger.warning(f"Error generating gallery description: {str(e)}")
            return f"A collection of {len(memories)} memories about {theme}."
    
    def _generate_gallery_title(self, theme: str, memory_count: int) -> str:
        """Generate a title for a thematic gallery."""
        if theme in self.default_thematic_galleries:
            return f"{theme} ({memory_count} memories)"
        else:
            return f"{theme.title()} Collection ({memory_count} memories)"
    
    def _generate_gallery_title_from_prompt(self, prompt: str, memory_count: int) -> str:
        """Generate a title from a natural language prompt."""
        # Extract key phrases from prompt
        words = prompt.lower().split()
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about', 'show', 'me', 'find', 'get'}
        key_words = [word for word in words if word not in stop_words]
        
        # Take first few key words for title
        title_words = key_words[:3] if len(key_words) >= 3 else key_words
        title = ' '.join(title_words).title()
        
        return f"{title} ({memory_count} memories)"
    
    def _parse_natural_language_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Parse natural language prompt to extract themes and criteria.
        
        Args:
            prompt: Natural language prompt
            
        Returns:
            Dictionary with parsed criteria
        """
        criteria = {}
        prompt_lower = prompt.lower()
        
        # Extract time-related criteria
        if 'last year' in prompt_lower or 'past year' in prompt_lower:
            criteria['time_range'] = 'last_year'
        elif 'last month' in prompt_lower or 'past month' in prompt_lower:
            criteria['time_range'] = 'last_month'
        elif 'this year' in prompt_lower:
            criteria['time_range'] = 'this_year'
        
        # Extract thematic criteria
        if 'friends' in prompt_lower or 'social' in prompt_lower:
            criteria['theme'] = 'social'
        elif 'travel' in prompt_lower or 'trip' in prompt_lower:
            criteria['theme'] = 'travel'
        elif 'work' in prompt_lower or 'professional' in prompt_lower:
            criteria['theme'] = 'professional'
        elif 'family' in prompt_lower:
            criteria['theme'] = 'family'
        else:
            criteria['theme'] = prompt
        
        # Extract narrative mode preferences
        if 'chronological' in prompt_lower or 'timeline' in prompt_lower:
            criteria['narrative_mode'] = 'chronological'
        elif 'people' in prompt_lower:
            criteria['narrative_mode'] = 'people-centered'
        elif 'place' in prompt_lower or 'location' in prompt_lower:
            criteria['narrative_mode'] = 'place-centered'
        else:
            criteria['narrative_mode'] = 'thematic'
        
        return criteria
    
    def _get_memory_time_span(self, memories: List[EnhancedLLEntry]) -> Optional[tuple]:
        """Get the time span covered by a list of memories."""
        if not memories:
            return None
        
        timestamps = []
        for memory in memories:
            if memory.startTime:
                # Handle both datetime objects and ISO format strings
                if isinstance(memory.startTime, datetime):
                    timestamps.append(memory.startTime)
                elif isinstance(memory.startTime, str):
                    try:
                        timestamps.append(datetime.fromisoformat(memory.startTime))
                    except (ValueError, AttributeError):
                        continue
        
        if not timestamps:
            return None
        
        return (min(timestamps), max(timestamps))
    
    def _get_gallery_by_id(self, gallery_id: str) -> Optional[Gallery]:
        """Retrieve a gallery by its ID."""
        try:
            # This would query the database for the specific gallery
            # For now, return None as placeholder
            self.logger.warning("get_gallery_by_id not fully implemented")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving gallery {gallery_id}: {str(e)}")
            return None
    
    def _get_memories_by_ids(self, memory_ids: List[str]) -> List[EnhancedLLEntry]:
        """Retrieve memories by their IDs."""
        try:
            # This would query the database for the specific memories
            # For now, return empty list as placeholder
            self.logger.warning("get_memories_by_ids not fully implemented")
            return []
        except Exception as e:
            self.logger.error(f"Error retrieving memories: {str(e)}")
            return []
    
    def _apply_semantic_ordering(self, memories: List[EnhancedLLEntry], 
                                ordering: List[int]) -> List[EnhancedLLEntry]:
        """Apply semantic ordering to memories."""
        try:
            if not ordering or len(ordering) != len(memories):
                return memories
            
            return [memories[i] for i in ordering if i < len(memories)]
        except Exception as e:
            self.logger.warning(f"Error applying semantic ordering: {str(e)}")
            return memories
    
    def get_supported_themes(self) -> List[str]:
        """Get list of supported thematic gallery themes."""
        return self.default_thematic_galleries.copy()