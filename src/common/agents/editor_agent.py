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

from typing import Any, Dict, List, Optional, Union
import re

from .base_agent import BaseAgent
from src.common.objects.enhanced_llentry import EnhancedLLEntry, Story, Chapter


class EditorAgent(BaseAgent):
    """
    The Editor Agent is responsible for filtering and organizing selected materials
    appropriately. It ensures content quality, removes inappropriate material,
    and organizes content for optimal presentation while maintaining privacy
    and safety standards.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("editor", config)
        
        # Content filtering parameters
        self.min_content_length = self.config.get('min_content_length', 10)
        self.max_content_length = self.config.get('max_content_length', 5000)
        self.filter_sensitive_content = self.config.get('filter_sensitive_content', True)
        self.filter_low_quality = self.config.get('filter_low_quality', True)
        
        # Organization parameters
        self.max_items_per_group = self.config.get('max_items_per_group', 20)
        self.prefer_media_content = self.config.get('prefer_media_content', True)
        
        # Safety parameters
        self.avoid_diagnostic_language = self.config.get('avoid_diagnostic_language', True)
        self.privacy_protection = self.config.get('privacy_protection', True)
        
    def _initialize_agent(self) -> None:
        """Initialize the Editor Agent with content filtering and organization capabilities."""
        self.logger.info("Initializing Editor Agent content filtering and organization")
        
        # Initialize content filters
        self.sensitive_patterns = [
            r'\b(depressed|anxiety|mental health|therapy|medication)\b',
            r'\b(personal information|ssn|social security|credit card)\b',
            r'\b(password|login|account|private)\b'
        ]
        
        # Initialize quality indicators
        self.quality_indicators = {
            'positive': ['photo', 'video', 'image', 'picture', 'memory', 'moment'],
            'negative': ['spam', 'advertisement', 'promotional', 'error', 'failed']
        }
        
        # Initialize diagnostic language patterns to avoid
        self.diagnostic_patterns = [
            r'\byou are\b',
            r'\byou have\b',
            r'\byou suffer from\b',
            r'\byou need\b',
            r'\bdiagnosis\b',
            r'\bdisorder\b',
            r'\bcondition\b'
        ]
        
        # Initialize organization categories
        self.content_categories = {
            'high_priority': ['milestone', 'celebration', 'achievement', 'first_time'],
            'medium_priority': ['social', 'travel', 'work', 'hobby'],
            'low_priority': ['routine', 'daily', 'mundane']
        }
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Filter and organize content based on the input type.
        
        Args:
            input_data: Content to be filtered and organized
            context: Optional context from other agents
            
        Returns:
            Filtered and organized content
        """
        if isinstance(input_data, list):
            if all(isinstance(item, EnhancedLLEntry) for item in input_data):
                return self._filter_and_organize_memories(input_data, context)
            else:
                return self._filter_generic_list(input_data, context)
        elif isinstance(input_data, Story):
            return self._edit_story(input_data, context)
        elif isinstance(input_data, Chapter):
            return self._edit_chapter(input_data, context)
        elif isinstance(input_data, dict):
            return self._filter_content_request(input_data, context)
        else:
            self.logger.warning(f"Unexpected input type: {type(input_data)}")
            return input_data
    
    def _filter_and_organize_memories(self, memories: List[EnhancedLLEntry], 
                                    context: Optional[Dict[str, Any]] = None) -> List[EnhancedLLEntry]:
        """
        Filter and organize a list of memories.
        
        Args:
            memories: List of memories to filter and organize
            context: Optional context information
            
        Returns:
            Filtered and organized list of memories
        """
        # Step 1: Apply content filters
        filtered_memories = []
        for memory in memories:
            if self._passes_content_filters(memory):
                filtered_memories.append(memory)
            else:
                self.logger.debug(f"Memory filtered out: {getattr(memory, 'id', 'unknown')}")
        
        # Step 2: Apply quality filters
        quality_filtered = []
        for memory in filtered_memories:
            if self._passes_quality_filters(memory):
                quality_filtered.append(memory)
            else:
                self.logger.debug(f"Memory failed quality filter: {getattr(memory, 'id', 'unknown')}")
        
        # Step 3: Organize by priority and relevance
        organized_memories = self._organize_memories_by_priority(quality_filtered)
        
        # Step 4: Apply final limits
        final_memories = organized_memories[:self.max_items_per_group]
        
        self.logger.info(f"Filtered {len(memories)} memories down to {len(final_memories)}")
        
        return final_memories
    
    def _edit_story(self, story: Story, context: Optional[Dict[str, Any]] = None) -> Story:
        """
        Edit and improve a story for quality and safety.
        
        Args:
            story: Story to edit
            context: Optional context information
            
        Returns:
            Edited story
        """
        # Edit each chapter
        edited_chapters = []
        for chapter in story.chapters:
            edited_chapter = self._edit_chapter(chapter, context)
            if edited_chapter:  # Only include if chapter passes editing
                edited_chapters.append(edited_chapter)
        
        # Update story with edited chapters
        story.chapters = edited_chapters
        
        # Edit story title if needed
        story.title = self._edit_text_content(story.title)
        
        self.logger.info(f"Edited story '{story.title}' with {len(edited_chapters)} chapters")
        
        return story
    
    def _edit_chapter(self, chapter: Chapter, context: Optional[Dict[str, Any]] = None) -> Optional[Chapter]:
        """
        Edit a chapter for quality and safety.
        
        Args:
            chapter: Chapter to edit
            context: Optional context information
            
        Returns:
            Edited chapter or None if chapter should be removed
        """
        # Edit narrative text
        edited_text = self._edit_narrative_text(chapter.narrative_text)
        
        if not edited_text or len(edited_text.strip()) < self.min_content_length:
            self.logger.debug(f"Chapter '{chapter.title}' removed due to insufficient content")
            return None
        
        # Filter media elements
        filtered_media = self._filter_media_elements(chapter.media_elements)
        
        # Update chapter
        chapter.narrative_text = edited_text
        chapter.media_elements = filtered_media
        chapter.title = self._edit_text_content(chapter.title)
        
        return chapter
    
    def _filter_content_request(self, request: Dict[str, Any], 
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Filter a content request for safety and appropriateness.
        
        Args:
            request: Content request to filter
            context: Optional context information
            
        Returns:
            Filtered request
        """
        filtered_request = request.copy()
        
        # Filter query text if present
        if 'query' in filtered_request:
            filtered_request['query'] = self._edit_text_content(filtered_request['query'])
        
        # Filter theme if present
        if 'theme' in filtered_request:
            filtered_request['theme'] = self._edit_text_content(filtered_request['theme'])
        
        # Apply safety limits
        if 'max_results' in filtered_request:
            filtered_request['max_results'] = min(filtered_request['max_results'], self.max_items_per_group)
        
        return filtered_request
    
    def _passes_content_filters(self, memory: EnhancedLLEntry) -> bool:
        """
        Check if a memory passes content safety filters.
        
        Args:
            memory: Memory to check
            
        Returns:
            True if memory passes filters
        """
        if not hasattr(memory, 'text') or not memory.text:
            return True  # No text to filter
        
        text_lower = memory.text.lower()
        
        # Check for sensitive content patterns
        if self.filter_sensitive_content:
            for pattern in self.sensitive_patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return False
        
        # Check content length
        if len(memory.text.strip()) < self.min_content_length:
            return False
        
        if len(memory.text) > self.max_content_length:
            return False
        
        return True
    
    def _passes_quality_filters(self, memory: EnhancedLLEntry) -> bool:
        """
        Check if a memory passes quality filters.
        
        Args:
            memory: Memory to check
            
        Returns:
            True if memory passes quality filters
        """
        if not self.filter_low_quality:
            return True
        
        if not hasattr(memory, 'text') or not memory.text:
            # If no text, check if it has media
            has_media = (hasattr(memory, 'photos') and memory.photos) or \
                       (hasattr(memory, 'videos') and memory.videos)
            return has_media
        
        text_lower = memory.text.lower()
        
        # Check for quality indicators
        positive_score = sum(1 for indicator in self.quality_indicators['positive'] 
                           if indicator in text_lower)
        negative_score = sum(1 for indicator in self.quality_indicators['negative'] 
                           if indicator in text_lower)
        
        # Prefer content with media
        if self.prefer_media_content:
            has_media = (hasattr(memory, 'photos') and memory.photos) or \
                       (hasattr(memory, 'videos') and memory.videos)
            if has_media:
                positive_score += 2
        
        # Simple quality scoring
        quality_score = positive_score - negative_score
        
        return quality_score >= 0
    
    def _organize_memories_by_priority(self, memories: List[EnhancedLLEntry]) -> List[EnhancedLLEntry]:
        """
        Organize memories by priority and relevance.
        
        Args:
            memories: List of memories to organize
            
        Returns:
            Organized list of memories
        """
        # Score memories by priority
        scored_memories = []
        
        for memory in memories:
            priority_score = self._calculate_priority_score(memory)
            scored_memories.append((memory, priority_score))
        
        # Sort by priority score (descending)
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        return [memory for memory, _ in scored_memories]
    
    def _calculate_priority_score(self, memory: EnhancedLLEntry) -> float:
        """
        Calculate priority score for a memory.
        
        Args:
            memory: Memory to score
            
        Returns:
            Priority score
        """
        score = 0.0
        
        # Use existing scores if available
        if hasattr(memory, 'narrative_significance'):
            score += memory.narrative_significance * 0.4
        
        if hasattr(memory, 'story_potential'):
            score += memory.story_potential * 0.3
        
        # Check for high-priority content categories
        if hasattr(memory, 'text') and memory.text:
            text_lower = memory.text.lower()
            
            for category, keywords in self.content_categories.items():
                matches = sum(1 for keyword in keywords if keyword in text_lower)
                if matches > 0:
                    if category == 'high_priority':
                        score += 0.3
                    elif category == 'medium_priority':
                        score += 0.2
                    else:  # low_priority
                        score += 0.1
        
        # Media bonus
        if hasattr(memory, 'photos') and memory.photos:
            score += 0.1
        if hasattr(memory, 'videos') and memory.videos:
            score += 0.15
        
        return score
    
    def _edit_narrative_text(self, text: str) -> str:
        """
        Edit narrative text for safety and quality.
        
        Args:
            text: Text to edit
            
        Returns:
            Edited text
        """
        if not text:
            return text
        
        edited_text = text
        
        # Remove diagnostic language if configured
        if self.avoid_diagnostic_language:
            for pattern in self.diagnostic_patterns:
                edited_text = re.sub(pattern, '[content edited]', edited_text, flags=re.IGNORECASE)
        
        # Clean up formatting
        edited_text = self._clean_text_formatting(edited_text)
        
        return edited_text
    
    def _edit_text_content(self, text: str) -> str:
        """
        Edit general text content for safety.
        
        Args:
            text: Text to edit
            
        Returns:
            Edited text
        """
        if not text:
            return text
        
        # Apply basic safety filters
        edited_text = text
        
        # Remove sensitive patterns
        for pattern in self.sensitive_patterns:
            edited_text = re.sub(pattern, '[redacted]', edited_text, flags=re.IGNORECASE)
        
        return edited_text.strip()
    
    def _clean_text_formatting(self, text: str) -> str:
        """
        Clean up text formatting issues.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', text)
        
        # Remove excessive punctuation
        cleaned = re.sub(r'[.]{3,}', '...', cleaned)
        cleaned = re.sub(r'[!]{2,}', '!', cleaned)
        cleaned = re.sub(r'[?]{2,}', '?', cleaned)
        
        # Ensure proper sentence endings
        cleaned = cleaned.strip()
        if cleaned and not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'
        
        return cleaned
    
    def _filter_media_elements(self, media_elements: List[str]) -> List[str]:
        """
        Filter media elements for safety and appropriateness.
        
        Args:
            media_elements: List of media file paths
            
        Returns:
            Filtered list of media elements
        """
        filtered_media = []
        
        for media_path in media_elements:
            if self._is_safe_media_path(media_path):
                filtered_media.append(media_path)
            else:
                self.logger.debug(f"Media filtered out: {media_path}")
        
        return filtered_media
    
    def _is_safe_media_path(self, media_path: str) -> bool:
        """
        Check if a media path is safe to include.
        
        Args:
            media_path: Media file path to check
            
        Returns:
            True if media path is safe
        """
        if not media_path:
            return False
        
        # Check for valid file extensions
        safe_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi']
        has_safe_extension = any(media_path.lower().endswith(ext) for ext in safe_extensions)
        
        if not has_safe_extension:
            return False
        
        # Check for suspicious path patterns
        suspicious_patterns = ['../', '~/', '/etc/', '/var/', 'system']
        for pattern in suspicious_patterns:
            if pattern in media_path.lower():
                return False
        
        return True
    
    def _filter_generic_list(self, items: List[Any], 
                           context: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Filter a generic list of items.
        
        Args:
            items: List of items to filter
            context: Optional context information
            
        Returns:
            Filtered list
        """
        # Apply basic length limits
        return items[:self.max_items_per_group]
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data for the Editor Agent.
        
        Args:
            input_data: Data to validate
            
        Returns:
            True if input is valid
        """
        if isinstance(input_data, (list, Story, Chapter, dict)):
            return True
        
        return False