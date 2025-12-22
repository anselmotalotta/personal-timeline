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

import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import statistics

from src.common.objects.enhanced_llentry import EnhancedLLEntry, PersonRelationship


class MemoryResurfacingService:
    """Service for proactive but gentle memory resurfacing based on contextual patterns"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.contextual_config = config.get('contextual_suggestions', {})
        self.reflection_config = config.get('reflection_prompts', {})
        self.presentation_config = config.get('presentation', {})
        self.pattern_config = config.get('pattern_detection', {})
        self.privacy_config = config.get('privacy', {})
        
        # Contextual suggestion settings
        self.max_suggestions = self.contextual_config.get('max_suggestions_per_session', 5)
        self.similarity_threshold = self.contextual_config.get('similarity_threshold', 0.3)
        self.recency_weight = self.contextual_config.get('recency_weight', 0.3)
        self.relevance_weight = self.contextual_config.get('relevance_weight', 0.4)
        self.novelty_weight = self.contextual_config.get('novelty_weight', 0.3)
        
        # Reflection prompt settings
        self.max_prompts = self.reflection_config.get('max_prompts_per_session', 3)
        self.prompt_variety = self.reflection_config.get('prompt_variety', True)
        self.avoid_repetitive = self.reflection_config.get('avoid_repetitive_prompts', True)
        self.dialogue_oriented = self.reflection_config.get('dialogue_oriented', True)
        
        # Presentation settings
        self.gentle_approach = self.presentation_config.get('gentle_approach', True)
        self.non_intrusive = self.presentation_config.get('non_intrusive', True)
        self.respect_user_agency = self.presentation_config.get('respect_user_agency', True)
        self.suggestion_framing = self.presentation_config.get('suggestion_framing', True)
        
        # Pattern detection settings
        self.connection_types = self.pattern_config.get('connection_types', 
            ['thematic', 'temporal', 'people', 'location', 'emotional'])
        self.min_pattern_strength = self.pattern_config.get('min_pattern_strength', 0.2)
        self.max_connections_per_memory = self.pattern_config.get('max_connections_per_memory', 3)
    
    def generate_contextual_suggestions(self, exploration_session: Dict[str, Any], 
                                      memory_collection: List[EnhancedLLEntry]) -> Dict[str, Any]:
        """
        Generate contextual memory suggestions based on current exploration patterns.
        
        Args:
            exploration_session: Current user exploration context
            memory_collection: Available memories to suggest from
            
        Returns:
            Dictionary containing suggested memories, reflection prompts, and pattern connections
        """
        if not memory_collection:
            return self._empty_suggestions_response()
        
        # Extract current context
        current_themes = set(exploration_session.get('current_themes', []))
        session_type = exploration_session.get('session_type', 'general')
        current_emotion = exploration_session.get('current_emotion', 'neutral')
        recently_viewed = set(exploration_session.get('recently_viewed', []))
        
        # Generate different types of suggestions
        suggested_memories = self._find_contextually_relevant_memories(
            memory_collection, current_themes, session_type, current_emotion, recently_viewed
        )
        
        unvisited_gems = self._find_unvisited_memories(
            memory_collection, current_themes, recently_viewed
        )
        
        reflection_prompts = self._create_reflection_prompts(
            exploration_session, suggested_memories + unvisited_gems
        )
        
        pattern_connections = self._detect_pattern_connections(
            memory_collection, current_themes, exploration_session
        )
        
        # Create presentation metadata
        presentation_metadata = self._create_presentation_metadata()
        
        # Create user controls
        user_controls = self._create_user_controls()
        
        return {
            'suggested_memories': suggested_memories,
            'unvisited_gems': unvisited_gems,
            'reflection_prompts': reflection_prompts,
            'pattern_connections': pattern_connections,
            'presentation_metadata': presentation_metadata,
            'user_controls': user_controls,
            'generation_timestamp': datetime.now().isoformat(),
            'session_context': exploration_session
        }
    
    def _find_contextually_relevant_memories(self, memories: List[EnhancedLLEntry], 
                                           current_themes: Set[str], session_type: str,
                                           current_emotion: str, recently_viewed: Set[str]) -> List[Dict[str, Any]]:
        """Find memories that are contextually relevant to current exploration"""
        relevant_memories = []
        
        for memory in memories:
            # Skip recently viewed memories
            memory_id = getattr(memory, 'id', str(hash(memory.text)))
            if memory_id in recently_viewed:
                continue
            
            # Calculate relevance score
            relevance_score = self._calculate_memory_relevance(
                memory, current_themes, session_type, current_emotion
            )
            
            if relevance_score >= self.similarity_threshold:
                # Determine connection reason and type
                connection_reason, suggestion_type = self._determine_connection_reason(
                    memory, current_themes, session_type, current_emotion
                )
                
                relevant_memories.append({
                    'memory': memory,
                    'relevance_score': relevance_score,
                    'connection_reason': connection_reason,
                    'suggestion_type': suggestion_type
                })
        
        # Sort by relevance and limit results
        relevant_memories.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_memories[:3]  # Reduce to 3 to avoid overwhelming
    
    def _calculate_memory_relevance(self, memory: EnhancedLLEntry, current_themes: Set[str],
                                  session_type: str, current_emotion: str) -> float:
        """Calculate how relevant a memory is to the current context"""
        relevance_score = 0.0
        
        # Thematic relevance
        memory_themes = set(getattr(memory, 'thematic_tags', []))
        if memory_themes and current_themes:
            theme_overlap = len(memory_themes.intersection(current_themes))
            theme_union = len(memory_themes.union(current_themes))
            if theme_union > 0:
                thematic_similarity = theme_overlap / theme_union
                relevance_score += thematic_similarity * self.relevance_weight
        
        # Emotional relevance
        if hasattr(memory, 'emotional_context') and memory.emotional_context:
            memory_emotion = memory.emotional_context.get('primary_emotion', '')
            if memory_emotion and current_emotion:
                # Simple emotion matching (could be enhanced with emotion similarity)
                if memory_emotion == current_emotion:
                    relevance_score += 0.3 * self.relevance_weight
                elif self._emotions_are_similar(memory_emotion, current_emotion):
                    relevance_score += 0.15 * self.relevance_weight
        
        # Narrative significance
        if hasattr(memory, 'narrative_significance'):
            significance = getattr(memory, 'narrative_significance', 0.5)
            relevance_score += significance * 0.2
        
        # Recency factor (older memories get slight boost for rediscovery)
        if hasattr(memory, 'startTime'):
            try:
                memory_time = datetime.fromisoformat(memory.startTime.replace('Z', '+00:00').replace('+00:00', ''))
                days_ago = (datetime.now() - memory_time).days
                
                # Slight preference for memories from 30-365 days ago (not too recent, not too old)
                if 30 <= days_ago <= 365:
                    relevance_score += 0.1 * self.recency_weight
                elif days_ago > 365:
                    relevance_score += 0.05 * self.recency_weight
            except (ValueError, AttributeError):
                pass
        
        # Novelty factor (memories not accessed recently get boost)
        if hasattr(memory, 'last_accessed') and memory.last_accessed:
            days_since_access = (datetime.now() - memory.last_accessed).days
            if days_since_access >= 90:
                novelty_boost = min(0.3, days_since_access / 365.0)
                relevance_score += novelty_boost * self.novelty_weight
        
        return min(1.0, relevance_score)
    
    def _emotions_are_similar(self, emotion1: str, emotion2: str) -> bool:
        """Check if two emotions are similar"""
        emotion_groups = {
            'positive': ['joy', 'happiness', 'excitement', 'gratitude', 'love', 'peace'],
            'contemplative': ['curiosity', 'wonder', 'thoughtful', 'reflective'],
            'energetic': ['excitement', 'enthusiasm', 'motivated'],
            'calm': ['peace', 'contentment', 'serene', 'peaceful']
        }
        
        for group in emotion_groups.values():
            if emotion1 in group and emotion2 in group:
                return True
        return False
    
    def _determine_connection_reason(self, memory: EnhancedLLEntry, current_themes: Set[str],
                                   session_type: str, current_emotion: str) -> Tuple[str, str]:
        """Determine why this memory is being suggested"""
        memory_themes = set(getattr(memory, 'thematic_tags', []))
        
        # Check for thematic connections
        theme_overlap = memory_themes.intersection(current_themes)
        if theme_overlap:
            themes_str = ', '.join(list(theme_overlap)[:2])
            reason = f"This memory connects to your current exploration of {themes_str}. " \
                    f"It might offer a different perspective or remind you of related experiences."
            return reason, 'thematic_connection'
        
        # Check for emotional connections
        if hasattr(memory, 'emotional_context') and memory.emotional_context:
            memory_emotion = memory.emotional_context.get('primary_emotion', '')
            if memory_emotion == current_emotion:
                reason = f"This memory shares a similar emotional tone to your current exploration. " \
                        f"It might resonate with how you're feeling right now."
                return reason, 'emotional_resonance'
        
        # Check for people connections
        if hasattr(memory, 'people_relationships') and memory.people_relationships:
            people_names = [rel.person_id for rel in memory.people_relationships[:2]]
            if people_names:
                people_str = ', '.join(people_names)
                reason = f"This memory involves {people_str}, who might be relevant to your current exploration. " \
                        f"It could spark thoughts about relationships and shared experiences."
                return reason, 'people_connection'
        
        # Check for location connections
        if hasattr(memory, 'location') and memory.location:
            reason = f"This memory from {memory.location} might offer a different spatial context " \
                    f"that connects to your current exploration."
            return reason, 'location_connection'
        
        # Default to interest evolution
        reason = "This memory might represent an earlier phase of interests or experiences " \
                "that could provide insight into how your perspectives have evolved."
        return reason, 'interest_evolution'
    
    def _find_unvisited_memories(self, memories: List[EnhancedLLEntry], 
                               current_themes: Set[str], recently_viewed: Set[str]) -> List[Dict[str, Any]]:
        """Find memories that haven't been revisited recently but might be valuable"""
        unvisited_gems = []
        
        for memory in memories:
            # Skip recently viewed
            memory_id = getattr(memory, 'id', str(hash(memory.text)))
            if memory_id in recently_viewed:
                continue
            
            # Check if memory hasn't been accessed recently
            if hasattr(memory, 'last_accessed') and memory.last_accessed:
                days_since_access = (datetime.now() - memory.last_accessed).days
                
                if days_since_access >= 30:  # Not accessed in last 30 days
                    # Calculate rediscovery value
                    rediscovery_score = self._calculate_rediscovery_value(memory, current_themes)
                    
                    if rediscovery_score >= 0.3:
                        rediscovery_reason = self._generate_rediscovery_reason(memory, days_since_access)
                        
                        unvisited_gems.append({
                            'memory': memory,
                            'rediscovery_reason': rediscovery_reason,
                            'time_since_last_access': days_since_access,
                            'rediscovery_score': rediscovery_score
                        })
        
        # Sort by rediscovery score and limit results
        unvisited_gems.sort(key=lambda x: x['rediscovery_score'], reverse=True)
        return unvisited_gems[:2]  # Limit to 2 unvisited gems
    
    def _calculate_rediscovery_value(self, memory: EnhancedLLEntry, current_themes: Set[str]) -> float:
        """Calculate how valuable it would be to rediscover this memory"""
        value_score = 0.0
        
        # Narrative significance
        if hasattr(memory, 'narrative_significance'):
            value_score += getattr(memory, 'narrative_significance', 0.5) * 0.4
        
        # Thematic relevance to current interests
        memory_themes = set(getattr(memory, 'thematic_tags', []))
        if memory_themes and current_themes:
            theme_overlap = len(memory_themes.intersection(current_themes))
            if theme_overlap > 0:
                value_score += 0.3
        
        # Emotional richness
        if hasattr(memory, 'emotional_context') and memory.emotional_context:
            emotional_intensity = memory.emotional_context.get('intensity', 0.5)
            value_score += emotional_intensity * 0.2
        
        # Social connections
        if hasattr(memory, 'people_relationships') and memory.people_relationships:
            value_score += 0.1
        
        return min(1.0, value_score)
    
    def _generate_rediscovery_reason(self, memory: EnhancedLLEntry, days_since_access: int) -> str:
        """Generate a reason for why this memory is worth rediscovering"""
        time_phrase = self._get_time_phrase(days_since_access)
        
        # Base reason on memory characteristics
        if hasattr(memory, 'narrative_significance') and memory.narrative_significance > 0.7:
            return f"This significant memory from {time_phrase} might offer valuable perspective " \
                   f"on your journey and growth."
        
        if hasattr(memory, 'people_relationships') and memory.people_relationships:
            return f"This memory involving important people from {time_phrase} could spark " \
                   f"thoughts about relationships and shared experiences."
        
        if hasattr(memory, 'thematic_tags') and memory.thematic_tags:
            themes = ', '.join(memory.thematic_tags[:2])
            return f"This memory about {themes} from {time_phrase} might connect to your " \
                   f"current interests in unexpected ways."
        
        return f"This memory from {time_phrase} might offer a fresh perspective " \
               f"or remind you of forgotten insights."
    
    def _get_time_phrase(self, days_ago: int) -> str:
        """Convert days ago to a human-readable time phrase"""
        if days_ago < 60:
            return "a couple months ago"
        elif days_ago < 120:
            return "a few months ago"
        elif days_ago < 365:
            return "earlier this year"
        elif days_ago < 730:
            return "about a year ago"
        else:
            years = days_ago // 365
            return f"about {years} year{'s' if years > 1 else ''} ago"
    
    def _create_reflection_prompts(self, exploration_session: Dict[str, Any], 
                                 relevant_memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create AI-generated reflection prompts that invite dialogue"""
        if not relevant_memories:
            return []
        
        prompts = []
        current_themes = exploration_session.get('current_themes', [])
        session_type = exploration_session.get('session_type', 'general')
        
        # Generate different types of prompts
        prompt_generators = [
            self._generate_pattern_recognition_prompt,
            self._generate_connection_discovery_prompt,
            self._generate_perspective_invitation_prompt
        ]
        
        for generator in prompt_generators[:2]:  # Limit to 2 prompts
            if len(prompts) >= 2:
                break
                
            prompt = generator(current_themes, relevant_memories, session_type)
            if prompt:
                prompts.append(prompt)
        
        return prompts
    
    def _generate_pattern_recognition_prompt(self, current_themes: List[str], 
                                           relevant_memories: List[Dict[str, Any]], 
                                           session_type: str) -> Optional[Dict[str, Any]]:
        """Generate a prompt that helps users recognize patterns"""
        if not current_themes or not relevant_memories:
            return None
        
        theme = current_themes[0] if current_themes else "your experiences"
        
        questions = [
            f"Looking at your memories around {theme}, what patterns do you notice in how your approach has evolved?",
            f"How do you think your relationship with {theme} has changed over time?",
            f"What would you tell your past self about {theme} based on what you've learned?",
            f"When you look back at your {theme} experiences, what surprises you most about your journey?"
        ]
        
        question = random.choice(questions)
        
        return {
            'question': question,
            'context_connection': f"This question emerges from patterns in your {theme}-related memories",
            'prompt_style': 'pattern_recognition',
            'dialogue_invitation': True
        }
    
    def _generate_connection_discovery_prompt(self, current_themes: List[str], 
                                            relevant_memories: List[Dict[str, Any]], 
                                            session_type: str) -> Optional[Dict[str, Any]]:
        """Generate a prompt that helps users discover connections"""
        if not relevant_memories:
            return None
        
        questions = [
            "What connections do you see between these memories and your current interests?",
            "How do these past experiences relate to what you're exploring now?",
            "What threads run through these different moments in your life?",
            "If these memories were having a conversation, what would they be discussing?"
        ]
        
        question = random.choice(questions)
        
        return {
            'question': question,
            'context_connection': "This question is inspired by connections between your past and present experiences",
            'prompt_style': 'connection_discovery',
            'dialogue_invitation': True
        }
    
    def _generate_perspective_invitation_prompt(self, current_themes: List[str], 
                                              relevant_memories: List[Dict[str, Any]], 
                                              session_type: str) -> Optional[Dict[str, Any]]:
        """Generate a prompt that invites perspective sharing"""
        questions = [
            "What perspective do these memories offer on your current situation?",
            "How do you feel about these memories now compared to when they happened?",
            "What would you want to remember about this period of your life?",
            "If you could have a conversation with yourself from these memories, what would you discuss?"
        ]
        
        question = random.choice(questions)
        
        return {
            'question': question,
            'context_connection': "This question invites you to reflect on how your perspective has evolved",
            'prompt_style': 'perspective_invitation',
            'dialogue_invitation': True
        }
    
    def _detect_pattern_connections(self, memories: List[EnhancedLLEntry], 
                                  current_themes: Set[str], 
                                  exploration_session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect patterns and connections between past and present experiences"""
        connections = []
        
        # Group memories by themes
        theme_groups = defaultdict(list)
        for memory in memories:
            if hasattr(memory, 'thematic_tags') and memory.thematic_tags:
                for theme in memory.thematic_tags:
                    theme_groups[theme].append(memory)
        
        # Look for theme evolution patterns
        for theme in current_themes:
            if theme in theme_groups and len(theme_groups[theme]) >= 2:
                connection = self._analyze_theme_evolution(theme, theme_groups[theme])
                if connection:
                    connections.append(connection)
        
        # Look for people continuity patterns
        people_connections = self._analyze_people_continuity(memories, current_themes)
        connections.extend(people_connections)
        
        # Look for emotional patterns
        emotional_connections = self._analyze_emotional_patterns(memories, exploration_session)
        connections.extend(emotional_connections)
        
        # Sort by connection strength and limit results
        connections.sort(key=lambda x: x['connection_strength'], reverse=True)
        return connections[:3]  # Limit to 3 connections
    
    def _analyze_theme_evolution(self, theme: str, theme_memories: List[EnhancedLLEntry]) -> Optional[Dict[str, Any]]:
        """Analyze how a theme has evolved over time"""
        if len(theme_memories) < 2:
            return None
        
        # Sort memories by time
        sorted_memories = sorted(theme_memories, 
                               key=lambda m: datetime.fromisoformat(m.startTime.replace('Z', '+00:00').replace('+00:00', '')))
        
        earliest = sorted_memories[0]
        latest = sorted_memories[-1]
        
        # Calculate time span
        earliest_time = datetime.fromisoformat(earliest.startTime.replace('Z', '+00:00').replace('+00:00', ''))
        latest_time = datetime.fromisoformat(latest.startTime.replace('Z', '+00:00').replace('+00:00', ''))
        time_span = (latest_time - earliest_time).days
        
        if time_span < 30:  # Too short to be meaningful
            return None
        
        # Analyze evolution
        connection_strength = min(1.0, len(theme_memories) / 10.0 + time_span / 365.0)
        
        narrative_bridge = f"Your relationship with {theme} appears to have evolved over time. " \
                          f"Looking at {len(theme_memories)} memories spanning {self._get_time_phrase(time_span)}, " \
                          f"there might be interesting patterns in how your approach or perspective has shifted."
        
        return {
            'connection_type': 'theme_recurrence',
            'past_element': f"Earlier {theme} experiences",
            'present_element': f"Current {theme} exploration",
            'connection_strength': connection_strength,
            'narrative_bridge': narrative_bridge,
            'supporting_memories': len(theme_memories)
        }
    
    def _analyze_people_continuity(self, memories: List[EnhancedLLEntry], 
                                 current_themes: Set[str]) -> List[Dict[str, Any]]:
        """Analyze continuity in relationships and people connections"""
        connections = []
        
        # Group memories by people
        people_groups = defaultdict(list)
        for memory in memories:
            if hasattr(memory, 'people_relationships') and memory.people_relationships:
                for relationship in memory.people_relationships:
                    people_groups[relationship.person_id].append(memory)
        
        # Look for people who appear across different themes/times
        for person_id, person_memories in people_groups.items():
            if len(person_memories) >= 3:  # Person appears in multiple memories
                # Check if person appears in both past and recent memories
                sorted_memories = sorted(person_memories, 
                                       key=lambda m: datetime.fromisoformat(m.startTime.replace('Z', '+00:00').replace('+00:00', '')))
                
                earliest_time = datetime.fromisoformat(sorted_memories[0].startTime.replace('Z', '+00:00').replace('+00:00', ''))
                latest_time = datetime.fromisoformat(sorted_memories[-1].startTime.replace('Z', '+00:00').replace('+00:00', ''))
                time_span = (latest_time - earliest_time).days
                
                if time_span >= 90:  # Relationship spans at least 3 months
                    connection_strength = min(1.0, len(person_memories) / 15.0 + time_span / 730.0)
                    
                    narrative_bridge = f"Your connection with {person_id} seems to be a recurring " \
                                      f"element across different periods of your life. This relationship " \
                                      f"might offer insights into how your social connections have evolved."
                    
                    connections.append({
                        'connection_type': 'people_continuity',
                        'past_element': f"Earlier memories with {person_id}",
                        'present_element': f"Ongoing relationship with {person_id}",
                        'connection_strength': connection_strength,
                        'narrative_bridge': narrative_bridge,
                        'supporting_memories': len(person_memories)
                    })
        
        return connections[:2]  # Limit to 2 people connections
    
    def _analyze_emotional_patterns(self, memories: List[EnhancedLLEntry], 
                                  exploration_session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze emotional patterns across memories"""
        connections = []
        current_emotion = exploration_session.get('current_emotion', 'neutral')
        
        # Group memories by emotional context
        emotional_memories = []
        for memory in memories:
            if hasattr(memory, 'emotional_context') and memory.emotional_context:
                emotional_memories.append(memory)
        
        if len(emotional_memories) < 5:
            return connections
        
        # Look for emotional evolution patterns
        emotion_timeline = []
        for memory in emotional_memories:
            try:
                memory_time = datetime.fromisoformat(memory.startTime.replace('Z', '+00:00').replace('+00:00', ''))
                emotion_data = memory.emotional_context
                emotion_timeline.append((memory_time, emotion_data, memory))
            except (ValueError, AttributeError):
                continue
        
        if len(emotion_timeline) >= 5:
            emotion_timeline.sort(key=lambda x: x[0])  # Sort by time
            
            # Analyze emotional journey
            connection_strength = min(1.0, len(emotion_timeline) / 20.0)
            
            narrative_bridge = f"Your emotional journey shows interesting patterns over time. " \
                              f"Looking at the emotional context of your memories might reveal " \
                              f"how your emotional landscape has evolved and what brings you joy or peace."
            
            connections.append({
                'connection_type': 'emotional_pattern',
                'past_element': "Earlier emotional experiences",
                'present_element': f"Current emotional exploration ({current_emotion})",
                'connection_strength': connection_strength,
                'narrative_bridge': narrative_bridge,
                'supporting_memories': len(emotion_timeline)
            })
        
        return connections
    
    def _create_presentation_metadata(self) -> Dict[str, Any]:
        """Create metadata about how suggestions should be presented"""
        return {
            'approach': 'gentle and respectful',
            'user_agency_respected': True,
            'intrusion_level': 'minimal',
            'suggestion_framing': True,
            'privacy_preserved': True,
            'local_processing_only': True
        }
    
    def _create_user_controls(self) -> Dict[str, Any]:
        """Create user control options for memory resurfacing"""
        return {
            'dismiss_suggestions': True,
            'adjust_frequency': ['more_often', 'less_often', 'pause'],
            'customize_themes': True,
            'exclude_time_periods': True,
            'exclude_people': True,
            'privacy_controls': True
        }
    
    def _empty_suggestions_response(self) -> Dict[str, Any]:
        """Return empty response when no memories are available"""
        return {
            'suggested_memories': [],
            'unvisited_gems': [],
            'reflection_prompts': [],
            'pattern_connections': [],
            'presentation_metadata': self._create_presentation_metadata(),
            'user_controls': self._create_user_controls(),
            'generation_timestamp': datetime.now().isoformat(),
            'session_context': {}
        }
    
    def create_reflection_prompts(self, context: Dict[str, Any], 
                                memories: List[EnhancedLLEntry]) -> List[Dict[str, Any]]:
        """Create standalone reflection prompts based on context and memories"""
        return self._create_reflection_prompts(context, [{'memory': m} for m in memories])
    
    def detect_pattern_connections(self, memories: List[EnhancedLLEntry], 
                                 themes: Set[str]) -> List[Dict[str, Any]]:
        """Detect standalone pattern connections"""
        mock_session = {'current_themes': list(themes), 'session_type': 'pattern_analysis'}
        return self._detect_pattern_connections(memories, themes, mock_session)
    
    def find_unvisited_memories(self, memories: List[EnhancedLLEntry], 
                              themes: Set[str]) -> List[Dict[str, Any]]:
        """Find standalone unvisited memories"""
        return self._find_unvisited_memories(memories, themes, set())