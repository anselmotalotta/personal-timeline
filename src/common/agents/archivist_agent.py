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

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import random

from .base_agent import BaseAgent
from src.common.objects.enhanced_llentry import EnhancedLLEntry


class ArchivistAgent(BaseAgent):
    """
    The Archivist Agent is responsible for selecting and curating relevant material
    from the personal archive based on user requests, themes, or narrative needs.
    
    This agent implements intelligent content selection algorithms that go beyond
    simple keyword matching to understand semantic relevance, temporal significance,
    and narrative potential.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("archivist", config)
        
        # Selection parameters
        self.max_selection_size = self.config.get('max_selection_size', 100)
        self.relevance_threshold = self.config.get('relevance_threshold', 0.3)
        self.temporal_weight = self.config.get('temporal_weight', 0.2)
        self.narrative_weight = self.config.get('narrative_weight', 0.4)
        self.diversity_weight = self.config.get('diversity_weight', 0.4)
        
        # Content filters
        self.exclude_low_quality = self.config.get('exclude_low_quality', True)
        self.include_media_preference = self.config.get('include_media_preference', True)
        
    def _initialize_agent(self) -> None:
        """Initialize the Archivist Agent with content indexing capabilities."""
        self.logger.info("Initializing Archivist Agent content selection algorithms")
        
        # Initialize content categorization
        self.content_categories = {
            'social': ['friend', 'family', 'party', 'gathering', 'celebration'],
            'travel': ['trip', 'vacation', 'journey', 'explore', 'visit'],
            'work': ['office', 'meeting', 'project', 'career', 'professional'],
            'personal': ['reflection', 'thought', 'feeling', 'memory', 'experience'],
            'creative': ['art', 'music', 'writing', 'create', 'design'],
            'milestone': ['birthday', 'graduation', 'wedding', 'achievement', 'first']
        }
        
        # Initialize temporal significance patterns
        self.temporal_patterns = {
            'recent': timedelta(days=30),
            'seasonal': timedelta(days=90),
            'yearly': timedelta(days=365),
            'milestone': timedelta(days=1095)  # 3 years
        }
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> List[EnhancedLLEntry]:
        """
        Select relevant memories from the archive based on the request.
        
        Args:
            input_data: Selection request containing query, theme, or criteria
            context: Optional context from other agents
            
        Returns:
            List of selected EnhancedLLEntry objects
        """
        if isinstance(input_data, dict):
            return self._process_selection_request(input_data, context)
        elif isinstance(input_data, list):
            return self._filter_and_rank_memories(input_data, context)
        else:
            self.logger.warning(f"Unexpected input type: {type(input_data)}")
            return []
    
    def _process_selection_request(self, request: Dict[str, Any], 
                                 context: Optional[Dict[str, Any]] = None) -> List[EnhancedLLEntry]:
        """
        Process a selection request with specific criteria.
        
        Args:
            request: Dictionary containing selection criteria
            context: Optional context information
            
        Returns:
            List of selected memories
        """
        # Extract request parameters
        query = request.get('query', '')
        theme = request.get('theme', '')
        time_range = request.get('time_range', None)
        narrative_mode = request.get('narrative_mode', 'chronological')
        max_results = request.get('max_results', self.max_selection_size)
        
        # Get available memories (this would typically come from the database)
        available_memories = request.get('available_memories', [])
        
        if not available_memories:
            self.logger.warning("No available memories provided in selection request")
            return []
        
        # Apply filters
        filtered_memories = self._apply_filters(available_memories, time_range)
        
        # Score memories based on relevance
        scored_memories = self._score_memories(filtered_memories, query, theme, narrative_mode)
        
        # Select top memories
        selected_memories = self._select_top_memories(scored_memories, max_results)
        
        self.logger.info(f"Selected {len(selected_memories)} memories from {len(available_memories)} available")
        
        return selected_memories
    
    def _filter_and_rank_memories(self, memories: List[EnhancedLLEntry], 
                                context: Optional[Dict[str, Any]] = None) -> List[EnhancedLLEntry]:
        """
        Filter and rank a list of memories for narrative potential.
        
        Args:
            memories: List of memories to filter and rank
            context: Optional context information
            
        Returns:
            Filtered and ranked list of memories
        """
        # Apply quality filters
        filtered_memories = []
        for memory in memories:
            if self._passes_quality_filter(memory):
                filtered_memories.append(memory)
        
        # Rank by narrative potential
        ranked_memories = sorted(filtered_memories, 
                               key=lambda m: self._calculate_narrative_score(m), 
                               reverse=True)
        
        return ranked_memories[:self.max_selection_size]
    
    def _apply_filters(self, memories: List[EnhancedLLEntry], 
                      time_range: Optional[Tuple[datetime, datetime]] = None) -> List[EnhancedLLEntry]:
        """
        Apply temporal and quality filters to memories.
        
        Args:
            memories: List of memories to filter
            time_range: Optional time range filter
            
        Returns:
            Filtered list of memories
        """
        filtered = []
        
        for memory in memories:
            # Apply time range filter
            if time_range:
                start_time, end_time = time_range
                if not (start_time <= memory.startTime <= end_time):
                    continue
            
            # Apply quality filter
            if self.exclude_low_quality and not self._passes_quality_filter(memory):
                continue
                
            filtered.append(memory)
        
        return filtered
    
    def _passes_quality_filter(self, memory: EnhancedLLEntry) -> bool:
        """
        Check if a memory passes quality filters.
        
        Args:
            memory: Memory to check
            
        Returns:
            True if memory passes quality filters
        """
        # Check for minimum content
        if not hasattr(memory, 'text') or not memory.text or len(memory.text.strip()) < 10:
            return False
        
        # Check for spam-like content
        spam_indicators = ['spam', 'advertisement', 'promotional']
        text_lower = memory.text.lower()
        if any(indicator in text_lower for indicator in spam_indicators):
            return False
        
        # Prefer memories with media if configured
        if self.include_media_preference:
            has_media = (hasattr(memory, 'photos') and memory.photos) or \
                       (hasattr(memory, 'videos') and memory.videos)
            if has_media:
                return True
        
        return True
    
    def _score_memories(self, memories: List[EnhancedLLEntry], query: str, 
                       theme: str, narrative_mode: str) -> List[Tuple[EnhancedLLEntry, float]]:
        """
        Score memories based on relevance to the request.
        
        Args:
            memories: List of memories to score
            query: Search query
            theme: Thematic focus
            narrative_mode: Type of narrative being created
            
        Returns:
            List of (memory, score) tuples
        """
        scored_memories = []
        
        for memory in memories:
            score = 0.0
            
            # Query relevance score
            if query:
                score += self._calculate_query_relevance(memory, query) * 0.4
            
            # Theme relevance score
            if theme:
                score += self._calculate_theme_relevance(memory, theme) * 0.3
            
            # Narrative potential score
            score += self._calculate_narrative_score(memory) * self.narrative_weight
            
            # Temporal significance score
            score += self._calculate_temporal_significance(memory) * self.temporal_weight
            
            # Diversity bonus (to avoid too similar content)
            score += self._calculate_diversity_bonus(memory, [m for m, _ in scored_memories]) * self.diversity_weight
            
            scored_memories.append((memory, score))
        
        return scored_memories
    
    def _calculate_query_relevance(self, memory: EnhancedLLEntry, query: str) -> float:
        """
        Calculate how relevant a memory is to a search query.
        
        Args:
            memory: Memory to score
            query: Search query
            
        Returns:
            Relevance score between 0 and 1
        """
        if not query or not hasattr(memory, 'text') or not memory.text:
            return 0.0
        
        query_lower = query.lower()
        text_lower = memory.text.lower()
        
        # Simple keyword matching (in a real implementation, this would use embeddings)
        query_words = query_lower.split()
        text_words = text_lower.split()
        
        matches = sum(1 for word in query_words if word in text_words)
        return min(matches / len(query_words), 1.0) if query_words else 0.0
    
    def _calculate_theme_relevance(self, memory: EnhancedLLEntry, theme: str) -> float:
        """
        Calculate how relevant a memory is to a thematic focus.
        
        Args:
            memory: Memory to score
            theme: Thematic focus
            
        Returns:
            Theme relevance score between 0 and 1
        """
        if not theme or not hasattr(memory, 'text') or not memory.text:
            return 0.0
        
        theme_lower = theme.lower()
        text_lower = memory.text.lower()
        
        # Check against content categories
        for category, keywords in self.content_categories.items():
            if theme_lower in keywords or any(keyword in theme_lower for keyword in keywords):
                # Check if memory matches this category
                category_matches = sum(1 for keyword in keywords if keyword in text_lower)
                if category_matches > 0:
                    return min(category_matches / len(keywords), 1.0)
        
        # Direct theme matching
        return 1.0 if theme_lower in text_lower else 0.0
    
    def _calculate_narrative_score(self, memory: EnhancedLLEntry) -> float:
        """
        Calculate the narrative potential of a memory.
        
        Args:
            memory: Memory to score
            
        Returns:
            Narrative score between 0 and 1
        """
        score = 0.0
        
        # Use existing narrative significance if available
        if hasattr(memory, 'narrative_significance'):
            score += memory.narrative_significance * 0.5
        
        # Use story potential if available
        if hasattr(memory, 'story_potential'):
            score += memory.story_potential * 0.3
        
        # Check for narrative indicators in text
        if hasattr(memory, 'text') and memory.text:
            narrative_indicators = ['remember', 'felt', 'realized', 'discovered', 'learned', 'changed']
            text_lower = memory.text.lower()
            indicator_matches = sum(1 for indicator in narrative_indicators if indicator in text_lower)
            score += min(indicator_matches / len(narrative_indicators), 0.2)
        
        # Media bonus
        if hasattr(memory, 'photos') and memory.photos:
            score += 0.1
        if hasattr(memory, 'videos') and memory.videos:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_temporal_significance(self, memory: EnhancedLLEntry) -> float:
        """
        Calculate the temporal significance of a memory.
        
        Args:
            memory: Memory to score
            
        Returns:
            Temporal significance score between 0 and 1
        """
        if not hasattr(memory, 'startTime') or not memory.startTime:
            return 0.0
        
        now = datetime.now()
        memory_time = memory.startTime
        
        # Convert string to datetime if needed
        if isinstance(memory_time, str):
            try:
                memory_time = datetime.fromisoformat(memory_time)
            except ValueError:
                return 0.0
        
        # Recent memories get higher scores
        time_diff = now - memory_time
        
        if time_diff <= self.temporal_patterns['recent']:
            return 0.8
        elif time_diff <= self.temporal_patterns['seasonal']:
            return 0.6
        elif time_diff <= self.temporal_patterns['yearly']:
            return 0.4
        else:
            return 0.2
    
    def _calculate_diversity_bonus(self, memory: EnhancedLLEntry, 
                                 already_selected: List[EnhancedLLEntry]) -> float:
        """
        Calculate diversity bonus to avoid selecting too similar content.
        
        Args:
            memory: Memory being considered
            already_selected: Memories already selected
            
        Returns:
            Diversity bonus score between 0 and 1
        """
        if not already_selected:
            return 1.0
        
        # Simple diversity check based on time and content
        diversity_score = 1.0
        
        for selected in already_selected:
            # Time diversity
            if hasattr(memory, 'startTime') and hasattr(selected, 'startTime'):
                memory_time = memory.startTime
                selected_time = selected.startTime
                
                # Convert strings to datetime if needed
                if isinstance(memory_time, str):
                    try:
                        memory_time = datetime.fromisoformat(memory_time)
                    except ValueError:
                        continue
                
                if isinstance(selected_time, str):
                    try:
                        selected_time = datetime.fromisoformat(selected_time)
                    except ValueError:
                        continue
                
                time_diff = abs((memory_time - selected_time).days)
                if time_diff < 7:  # Same week
                    diversity_score *= 0.8
            
            # Content similarity (simple check)
            if hasattr(memory, 'text') and hasattr(selected, 'text'):
                if memory.text and selected.text:
                    memory_words = set(memory.text.lower().split())
                    selected_words = set(selected.text.lower().split())
                    overlap = len(memory_words & selected_words)
                    total = len(memory_words | selected_words)
                    if total > 0 and overlap / total > 0.5:
                        diversity_score *= 0.7
        
        return diversity_score
    
    def _select_top_memories(self, scored_memories: List[Tuple[EnhancedLLEntry, float]], 
                           max_results: int) -> List[EnhancedLLEntry]:
        """
        Select the top-scoring memories.
        
        Args:
            scored_memories: List of (memory, score) tuples
            max_results: Maximum number of memories to select
            
        Returns:
            List of selected memories
        """
        # Sort by score (descending)
        sorted_memories = sorted(scored_memories, key=lambda x: x[1], reverse=True)
        
        # Filter by threshold and limit
        selected = []
        for memory, score in sorted_memories:
            if score >= self.relevance_threshold and len(selected) < max_results:
                selected.append(memory)
        
        return selected
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data for the Archivist Agent.
        
        Args:
            input_data: Data to validate
            
        Returns:
            True if input is valid
        """
        if isinstance(input_data, dict):
            # Selection request validation
            return 'available_memories' in input_data or 'query' in input_data or 'theme' in input_data
        elif isinstance(input_data, list):
            # Memory list validation
            return all(isinstance(item, EnhancedLLEntry) for item in input_data)
        
        return False