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
from src.common.objects.enhanced_llentry import EnhancedLLEntry, Story, Chapter


class DirectorAgent(BaseAgent):
    """
    The Director Agent is responsible for sequencing media and pacing for optimal
    user experience. It determines the order of content presentation, timing
    between elements, and overall flow of narrative experiences.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("director", config)
        
        # Sequencing parameters
        self.optimal_chapter_count = self.config.get('optimal_chapter_count', 5)
        self.max_chapter_count = self.config.get('max_chapter_count', 10)
        self.min_chapter_duration = self.config.get('min_chapter_duration', 30)  # seconds
        self.max_chapter_duration = self.config.get('max_chapter_duration', 180)  # seconds
        
        # Pacing parameters
        self.narrative_pacing = self.config.get('narrative_pacing', 'moderate')  # slow, moderate, fast
        self.emotional_flow_weight = self.config.get('emotional_flow_weight', 0.4)
        self.temporal_flow_weight = self.config.get('temporal_flow_weight', 0.3)
        self.thematic_flow_weight = self.config.get('thematic_flow_weight', 0.3)
        
        # Media sequencing
        self.media_distribution_strategy = self.config.get('media_distribution_strategy', 'balanced')
        self.prefer_visual_variety = self.config.get('prefer_visual_variety', True)
        
    def _initialize_agent(self) -> None:
        """Initialize the Director Agent with sequencing and pacing algorithms."""
        self.logger.info("Initializing Director Agent sequencing and pacing algorithms")
        
        # Initialize pacing profiles
        self.pacing_profiles = {
            'slow': {
                'chapter_duration_multiplier': 1.5,
                'transition_weight': 0.6,
                'emotional_smoothing': 0.8
            },
            'moderate': {
                'chapter_duration_multiplier': 1.0,
                'transition_weight': 0.4,
                'emotional_smoothing': 0.5
            },
            'fast': {
                'chapter_duration_multiplier': 0.7,
                'transition_weight': 0.2,
                'emotional_smoothing': 0.2
            }
        }
        
        # Initialize emotional flow patterns
        self.emotional_flow_patterns = {
            'crescendo': ['calm', 'building', 'peak', 'resolution'],
            'journey': ['departure', 'adventure', 'challenge', 'return'],
            'reflection': ['present', 'past', 'insight', 'future'],
            'celebration': ['anticipation', 'joy', 'peak', 'afterglow']
        }
        
        # Initialize media distribution strategies
        self.media_strategies = {
            'balanced': self._balance_media_distribution,
            'front_loaded': self._front_load_media,
            'climactic': self._climactic_media_distribution,
            'scattered': self._scatter_media_evenly
        }
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Sequence and pace content for optimal presentation.
        
        Args:
            input_data: Content to be sequenced and paced
            context: Optional context from other agents
            
        Returns:
            Sequenced and paced content
        """
        if isinstance(input_data, Story):
            return self._direct_story(input_data, context)
        elif isinstance(input_data, list):
            if all(isinstance(item, Chapter) for item in input_data):
                return self._sequence_chapters(input_data, context)
            elif all(isinstance(item, EnhancedLLEntry) for item in input_data):
                return self._sequence_memories(input_data, context)
            else:
                return self._sequence_generic_content(input_data, context)
        elif isinstance(input_data, dict):
            return self._process_sequencing_request(input_data, context)
        else:
            self.logger.warning(f"Unexpected input type: {type(input_data)}")
            return input_data
    
    def _direct_story(self, story: Story, context: Optional[Dict[str, Any]] = None) -> Story:
        """
        Direct the overall flow and pacing of a story.
        
        Args:
            story: Story to direct
            context: Optional context information
            
        Returns:
            Directed story with optimized sequencing
        """
        # Analyze current story structure
        story_analysis = self._analyze_story_structure(story)
        
        # Optimize chapter sequence
        optimized_chapters = self._optimize_chapter_sequence(story.chapters, story_analysis)
        
        # Adjust chapter pacing
        paced_chapters = self._adjust_chapter_pacing(optimized_chapters, story_analysis)
        
        # Distribute media elements optimally
        final_chapters = self._optimize_media_distribution(paced_chapters)
        
        # Update story
        story.chapters = final_chapters
        
        self.logger.info(f"Directed story '{story.title}' with {len(final_chapters)} chapters")
        
        return story
    
    def _sequence_chapters(self, chapters: List[Chapter], 
                         context: Optional[Dict[str, Any]] = None) -> List[Chapter]:
        """
        Sequence chapters for optimal flow.
        
        Args:
            chapters: List of chapters to sequence
            context: Optional context information
            
        Returns:
            Sequenced list of chapters
        """
        if len(chapters) <= 1:
            return chapters
        
        # Calculate flow scores between chapters
        flow_matrix = self._calculate_chapter_flow_matrix(chapters)
        
        # Find optimal sequence using flow scores
        optimal_sequence = self._find_optimal_sequence(chapters, flow_matrix)
        
        # Adjust durations for better pacing
        paced_sequence = self._adjust_sequence_pacing(optimal_sequence)
        
        return paced_sequence
    
    def _sequence_memories(self, memories: List[EnhancedLLEntry], 
                         context: Optional[Dict[str, Any]] = None) -> List[EnhancedLLEntry]:
        """
        Sequence memories for narrative flow.
        
        Args:
            memories: List of memories to sequence
            context: Optional context information
            
        Returns:
            Sequenced list of memories
        """
        if len(memories) <= 1:
            return memories
        
        # Determine sequencing strategy from context
        strategy = 'chronological'  # default
        if context and 'narrative_mode' in context:
            strategy = context['narrative_mode']
        
        # Apply sequencing strategy
        if strategy == 'chronological':
            return self._sequence_chronologically(memories)
        elif strategy == 'thematic':
            return self._sequence_thematically(memories)
        elif strategy == 'emotional':
            return self._sequence_emotionally(memories)
        else:
            return self._sequence_by_narrative_flow(memories)
    
    def _process_sequencing_request(self, request: Dict[str, Any], 
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a sequencing request with specific parameters.
        
        Args:
            request: Sequencing request parameters
            context: Optional context information
            
        Returns:
            Processed sequencing result
        """
        content = request.get('content', [])
        sequencing_mode = request.get('mode', 'optimal')
        pacing_preference = request.get('pacing', self.narrative_pacing)
        
        if not content:
            return request
        
        # Apply sequencing based on content type
        if isinstance(content[0], Chapter):
            sequenced_content = self._sequence_chapters(content, context)
        elif isinstance(content[0], EnhancedLLEntry):
            sequenced_content = self._sequence_memories(content, context)
        else:
            sequenced_content = content
        
        # Update request with sequenced content
        result = request.copy()
        result['content'] = sequenced_content
        result['sequencing_applied'] = True
        result['pacing_used'] = pacing_preference
        
        return result
    
    def _analyze_story_structure(self, story: Story) -> Dict[str, Any]:
        """
        Analyze the structure of a story for optimization.
        
        Args:
            story: Story to analyze
            
        Returns:
            Analysis results
        """
        analysis = {
            'total_chapters': len(story.chapters),
            'total_duration': sum(chapter.duration_seconds for chapter in story.chapters),
            'emotional_arc': self._analyze_emotional_arc(story.chapters),
            'media_distribution': self._analyze_media_distribution(story.chapters),
            'pacing_issues': self._identify_pacing_issues(story.chapters)
        }
        
        return analysis
    
    def _analyze_emotional_arc(self, chapters: List[Chapter]) -> Dict[str, Any]:
        """
        Analyze the emotional arc of chapters.
        
        Args:
            chapters: List of chapters to analyze
            
        Returns:
            Emotional arc analysis
        """
        emotional_progression = []
        emotional_variety = set()
        
        for chapter in chapters:
            tone = getattr(chapter, 'emotional_tone', 'neutral')
            emotional_progression.append(tone)
            emotional_variety.add(tone)
        
        return {
            'progression': emotional_progression,
            'variety_score': len(emotional_variety),
            'dominant_tone': max(set(emotional_progression), key=emotional_progression.count) if emotional_progression else 'neutral'
        }
    
    def _analyze_media_distribution(self, chapters: List[Chapter]) -> Dict[str, Any]:
        """
        Analyze media distribution across chapters.
        
        Args:
            chapters: List of chapters to analyze
            
        Returns:
            Media distribution analysis
        """
        media_counts = []
        total_media = 0
        
        for chapter in chapters:
            media_count = len(getattr(chapter, 'media_elements', []))
            media_counts.append(media_count)
            total_media += media_count
        
        return {
            'total_media': total_media,
            'per_chapter': media_counts,
            'average_per_chapter': total_media / len(chapters) if chapters else 0,
            'distribution_variance': self._calculate_variance(media_counts)
        }
    
    def _identify_pacing_issues(self, chapters: List[Chapter]) -> List[str]:
        """
        Identify potential pacing issues in chapters.
        
        Args:
            chapters: List of chapters to analyze
            
        Returns:
            List of identified issues
        """
        issues = []
        
        # Check for duration imbalances
        durations = [getattr(chapter, 'duration_seconds', 60) for chapter in chapters]
        avg_duration = sum(durations) / len(durations) if durations else 60
        
        for i, duration in enumerate(durations):
            if duration < avg_duration * 0.3:
                issues.append(f"Chapter {i+1} too short ({duration}s)")
            elif duration > avg_duration * 2.5:
                issues.append(f"Chapter {i+1} too long ({duration}s)")
        
        # Check for emotional monotony
        emotional_tones = [getattr(chapter, 'emotional_tone', 'neutral') for chapter in chapters]
        if len(set(emotional_tones)) == 1 and len(emotional_tones) > 2:
            issues.append("Emotional monotony detected")
        
        return issues
    
    def _optimize_chapter_sequence(self, chapters: List[Chapter], 
                                 analysis: Dict[str, Any]) -> List[Chapter]:
        """
        Optimize the sequence of chapters based on analysis.
        
        Args:
            chapters: List of chapters to optimize
            analysis: Story structure analysis
            
        Returns:
            Optimized chapter sequence
        """
        if len(chapters) <= 1:
            return chapters
        
        # Calculate optimal flow pattern
        target_pattern = self._determine_optimal_flow_pattern(analysis)
        
        # Score chapters for each position in the pattern
        position_scores = self._score_chapters_for_positions(chapters, target_pattern)
        
        # Find best assignment of chapters to positions
        optimal_assignment = self._find_optimal_chapter_assignment(chapters, position_scores)
        
        return optimal_assignment
    
    def _determine_optimal_flow_pattern(self, analysis: Dict[str, Any]) -> str:
        """
        Determine the optimal emotional flow pattern for the story.
        
        Args:
            analysis: Story structure analysis
            
        Returns:
            Optimal flow pattern name
        """
        dominant_tone = analysis['emotional_arc']['dominant_tone']
        variety_score = analysis['emotional_arc']['variety_score']
        
        # Choose pattern based on content characteristics
        if dominant_tone in ['joyful', 'celebration']:
            return 'celebration'
        elif variety_score >= 3:
            return 'journey'
        elif dominant_tone in ['reflective', 'nostalgic']:
            return 'reflection'
        else:
            return 'crescendo'
    
    def _score_chapters_for_positions(self, chapters: List[Chapter], 
                                    pattern: str) -> Dict[int, List[Tuple[Chapter, float]]]:
        """
        Score chapters for each position in the target pattern.
        
        Args:
            chapters: List of chapters to score
            pattern: Target flow pattern
            
        Returns:
            Dictionary mapping positions to scored chapters
        """
        pattern_stages = self.emotional_flow_patterns.get(pattern, ['beginning', 'middle', 'end'])
        position_scores = {}
        
        for position, stage in enumerate(pattern_stages):
            chapter_scores = []
            
            for chapter in chapters:
                score = self._calculate_chapter_position_score(chapter, stage, position, len(pattern_stages))
                chapter_scores.append((chapter, score))
            
            # Sort by score (descending)
            chapter_scores.sort(key=lambda x: x[1], reverse=True)
            position_scores[position] = chapter_scores
        
        return position_scores
    
    def _calculate_chapter_position_score(self, chapter: Chapter, stage: str, 
                                        position: int, total_positions: int) -> float:
        """
        Calculate how well a chapter fits a specific position.
        
        Args:
            chapter: Chapter to score
            stage: Target stage for this position
            position: Position index
            total_positions: Total number of positions
            
        Returns:
            Position fit score
        """
        score = 0.0
        
        # Emotional tone matching
        chapter_tone = getattr(chapter, 'emotional_tone', 'neutral')
        tone_compatibility = self._calculate_tone_compatibility(chapter_tone, stage)
        score += tone_compatibility * 0.4
        
        # Duration appropriateness for position
        duration = getattr(chapter, 'duration_seconds', 60)
        duration_score = self._calculate_duration_position_score(duration, position, total_positions)
        score += duration_score * 0.3
        
        # Media richness for position
        media_count = len(getattr(chapter, 'media_elements', []))
        media_score = self._calculate_media_position_score(media_count, position, total_positions)
        score += media_score * 0.3
        
        return score
    
    def _calculate_tone_compatibility(self, chapter_tone: str, target_stage: str) -> float:
        """
        Calculate compatibility between chapter tone and target stage.
        
        Args:
            chapter_tone: Emotional tone of the chapter
            target_stage: Target stage in the flow pattern
            
        Returns:
            Compatibility score between 0 and 1
        """
        compatibility_matrix = {
            'beginning': {'calm': 0.9, 'reflective': 0.8, 'peaceful': 0.9, 'nostalgic': 0.7},
            'building': {'adventurous': 0.9, 'joyful': 0.8, 'growth': 0.9, 'reflective': 0.6},
            'peak': {'joyful': 1.0, 'adventurous': 0.9, 'celebration': 1.0, 'growth': 0.8},
            'resolution': {'peaceful': 1.0, 'reflective': 0.9, 'nostalgic': 0.8, 'growth': 0.7},
            'departure': {'adventurous': 0.9, 'peaceful': 0.7, 'reflective': 0.6},
            'adventure': {'adventurous': 1.0, 'joyful': 0.8, 'growth': 0.7},
            'challenge': {'growth': 0.9, 'adventurous': 0.8, 'reflective': 0.6},
            'return': {'peaceful': 0.9, 'reflective': 1.0, 'nostalgic': 0.8},
            'present': {'reflective': 0.8, 'peaceful': 0.7, 'joyful': 0.6},
            'past': {'nostalgic': 1.0, 'reflective': 0.9, 'peaceful': 0.7},
            'insight': {'reflective': 1.0, 'growth': 0.9, 'peaceful': 0.7},
            'future': {'growth': 0.9, 'adventurous': 0.8, 'joyful': 0.7},
            'anticipation': {'adventurous': 0.8, 'joyful': 0.9, 'growth': 0.7},
            'joy': {'joyful': 1.0, 'celebration': 1.0, 'peaceful': 0.7},
            'afterglow': {'peaceful': 1.0, 'reflective': 0.9, 'nostalgic': 0.8}
        }
        
        stage_compatibility = compatibility_matrix.get(target_stage, {})
        return stage_compatibility.get(chapter_tone, 0.5)  # Default neutral compatibility
    
    def _calculate_duration_position_score(self, duration: int, position: int, total_positions: int) -> float:
        """
        Calculate how appropriate a chapter duration is for its position.
        
        Args:
            duration: Chapter duration in seconds
            position: Position in sequence
            total_positions: Total positions
            
        Returns:
            Duration appropriateness score
        """
        # Generally prefer longer chapters in the middle, shorter at ends
        position_ratio = position / (total_positions - 1) if total_positions > 1 else 0.5
        
        # Optimal duration curve (peaks in middle)
        optimal_multiplier = 0.8 + 0.4 * (1 - abs(position_ratio - 0.5) * 2)
        optimal_duration = 90 * optimal_multiplier  # Base 90 seconds
        
        # Score based on how close to optimal
        duration_diff = abs(duration - optimal_duration)
        max_acceptable_diff = 60  # 1 minute tolerance
        
        if duration_diff <= max_acceptable_diff:
            return 1.0 - (duration_diff / max_acceptable_diff) * 0.5
        else:
            return 0.5  # Penalty for being too far from optimal
    
    def _calculate_media_position_score(self, media_count: int, position: int, total_positions: int) -> float:
        """
        Calculate media richness appropriateness for position.
        
        Args:
            media_count: Number of media elements
            position: Position in sequence
            total_positions: Total positions
            
        Returns:
            Media appropriateness score
        """
        # Generally prefer more media in key positions (beginning, climax, end)
        position_ratio = position / (total_positions - 1) if total_positions > 1 else 0.5
        
        # Key positions get bonus for having media
        is_key_position = position == 0 or position == total_positions - 1 or abs(position_ratio - 0.5) < 0.2
        
        if is_key_position:
            return min(media_count / 3.0, 1.0)  # Up to 3 media elements is optimal
        else:
            return min(media_count / 2.0, 1.0)  # Up to 2 media elements is optimal
    
    def _find_optimal_chapter_assignment(self, chapters: List[Chapter], 
                                       position_scores: Dict[int, List[Tuple[Chapter, float]]]) -> List[Chapter]:
        """
        Find optimal assignment of chapters to positions.
        
        Args:
            chapters: List of chapters to assign
            position_scores: Scores for each chapter at each position
            
        Returns:
            Optimally assigned chapter sequence
        """
        # Simple greedy assignment (in a real implementation, this could use Hungarian algorithm)
        assigned_chapters = [None] * len(chapters)
        used_chapters = set()
        
        # Assign chapters to positions in order of best fit
        for position in range(len(chapters)):
            if position in position_scores:
                for chapter, score in position_scores[position]:
                    if chapter not in used_chapters:
                        assigned_chapters[position] = chapter
                        used_chapters.add(chapter)
                        break
        
        # Fill any remaining positions with unassigned chapters
        remaining_chapters = [ch for ch in chapters if ch not in used_chapters]
        for i, chapter in enumerate(assigned_chapters):
            if chapter is None and remaining_chapters:
                assigned_chapters[i] = remaining_chapters.pop(0)
        
        return [ch for ch in assigned_chapters if ch is not None]
    
    def _adjust_chapter_pacing(self, chapters: List[Chapter], 
                             analysis: Dict[str, Any]) -> List[Chapter]:
        """
        Adjust chapter pacing for better flow.
        
        Args:
            chapters: List of chapters to pace
            analysis: Story structure analysis
            
        Returns:
            Chapters with adjusted pacing
        """
        pacing_profile = self.pacing_profiles.get(self.narrative_pacing, self.pacing_profiles['moderate'])
        
        for i, chapter in enumerate(chapters):
            # Adjust duration based on position and pacing profile
            current_duration = getattr(chapter, 'duration_seconds', 60)
            position_multiplier = self._calculate_position_pacing_multiplier(i, len(chapters))
            
            new_duration = int(current_duration * pacing_profile['chapter_duration_multiplier'] * position_multiplier)
            new_duration = max(self.min_chapter_duration, min(new_duration, self.max_chapter_duration))
            
            chapter.duration_seconds = new_duration
        
        return chapters
    
    def _calculate_position_pacing_multiplier(self, position: int, total_chapters: int) -> float:
        """
        Calculate pacing multiplier based on position in sequence.
        
        Args:
            position: Chapter position
            total_chapters: Total number of chapters
            
        Returns:
            Pacing multiplier
        """
        if total_chapters <= 1:
            return 1.0
        
        position_ratio = position / (total_chapters - 1)
        
        # Create a pacing curve (slower start, faster middle, moderate end)
        if position_ratio < 0.3:
            return 1.2  # Slower start
        elif position_ratio < 0.7:
            return 0.9  # Faster middle
        else:
            return 1.0  # Moderate end
    
    def _optimize_media_distribution(self, chapters: List[Chapter]) -> List[Chapter]:
        """
        Optimize media distribution across chapters.
        
        Args:
            chapters: List of chapters to optimize
            
        Returns:
            Chapters with optimized media distribution
        """
        strategy_func = self.media_strategies.get(self.media_distribution_strategy, 
                                                self.media_strategies['balanced'])
        
        return strategy_func(chapters)
    
    def _balance_media_distribution(self, chapters: List[Chapter]) -> List[Chapter]:
        """
        Balance media distribution evenly across chapters.
        
        Args:
            chapters: List of chapters
            
        Returns:
            Chapters with balanced media
        """
        # Collect all media elements
        all_media = []
        for chapter in chapters:
            all_media.extend(getattr(chapter, 'media_elements', []))
        
        # Distribute evenly
        media_per_chapter = len(all_media) // len(chapters) if chapters else 0
        extra_media = len(all_media) % len(chapters) if chapters else 0
        
        media_index = 0
        for i, chapter in enumerate(chapters):
            chapter_media_count = media_per_chapter + (1 if i < extra_media else 0)
            chapter.media_elements = all_media[media_index:media_index + chapter_media_count]
            media_index += chapter_media_count
        
        return chapters
    
    def _front_load_media(self, chapters: List[Chapter]) -> List[Chapter]:
        """
        Front-load media in earlier chapters.
        
        Args:
            chapters: List of chapters
            
        Returns:
            Chapters with front-loaded media
        """
        # Collect all media
        all_media = []
        for chapter in chapters:
            all_media.extend(getattr(chapter, 'media_elements', []))
        
        # Distribute with decreasing amounts
        media_index = 0
        for i, chapter in enumerate(chapters):
            # More media in earlier chapters
            weight = max(0.1, 1.0 - (i / len(chapters)) * 0.8)
            chapter_media_count = int(len(all_media) * weight / sum(max(0.1, 1.0 - (j / len(chapters)) * 0.8) for j in range(len(chapters))))
            
            chapter.media_elements = all_media[media_index:media_index + chapter_media_count]
            media_index += chapter_media_count
        
        return chapters
    
    def _climactic_media_distribution(self, chapters: List[Chapter]) -> List[Chapter]:
        """
        Distribute media with peak in the middle chapters.
        
        Args:
            chapters: List of chapters
            
        Returns:
            Chapters with climactic media distribution
        """
        # Similar to front_load_media but peaks in middle
        all_media = []
        for chapter in chapters:
            all_media.extend(getattr(chapter, 'media_elements', []))
        
        media_index = 0
        for i, chapter in enumerate(chapters):
            # Peak in middle
            position_ratio = i / (len(chapters) - 1) if len(chapters) > 1 else 0.5
            weight = 0.3 + 0.7 * (1 - abs(position_ratio - 0.5) * 2)
            
            chapter_media_count = int(len(all_media) * weight / sum(0.3 + 0.7 * (1 - abs((j / (len(chapters) - 1) if len(chapters) > 1 else 0.5) - 0.5) * 2) for j in range(len(chapters))))
            
            chapter.media_elements = all_media[media_index:media_index + chapter_media_count]
            media_index += chapter_media_count
        
        return chapters
    
    def _scatter_media_evenly(self, chapters: List[Chapter]) -> List[Chapter]:
        """
        Scatter media evenly with some randomization.
        
        Args:
            chapters: List of chapters
            
        Returns:
            Chapters with scattered media
        """
        # Similar to balanced but with slight randomization
        all_media = []
        for chapter in chapters:
            all_media.extend(getattr(chapter, 'media_elements', []))
        
        # Shuffle media for variety
        random.shuffle(all_media)
        
        # Distribute with slight variation
        base_per_chapter = len(all_media) // len(chapters) if chapters else 0
        
        media_index = 0
        for chapter in chapters:
            variation = random.randint(-1, 1) if base_per_chapter > 1 else 0
            chapter_media_count = max(0, base_per_chapter + variation)
            
            chapter.media_elements = all_media[media_index:media_index + chapter_media_count]
            media_index += chapter_media_count
        
        return chapters
    
    def _calculate_chapter_flow_matrix(self, chapters: List[Chapter]) -> List[List[float]]:
        """
        Calculate flow scores between all pairs of chapters.
        
        Args:
            chapters: List of chapters
            
        Returns:
            Matrix of flow scores
        """
        n = len(chapters)
        flow_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    flow_matrix[i][j] = self._calculate_chapter_flow_score(chapters[i], chapters[j])
        
        return flow_matrix
    
    def _calculate_chapter_flow_score(self, chapter1: Chapter, chapter2: Chapter) -> float:
        """
        Calculate flow score between two chapters.
        
        Args:
            chapter1: First chapter
            chapter2: Second chapter
            
        Returns:
            Flow score between 0 and 1
        """
        score = 0.0
        
        # Emotional flow
        tone1 = getattr(chapter1, 'emotional_tone', 'neutral')
        tone2 = getattr(chapter2, 'emotional_tone', 'neutral')
        emotional_flow = self._calculate_emotional_flow_score(tone1, tone2)
        score += emotional_flow * self.emotional_flow_weight
        
        # Duration balance
        duration1 = getattr(chapter1, 'duration_seconds', 60)
        duration2 = getattr(chapter2, 'duration_seconds', 60)
        duration_balance = self._calculate_duration_balance_score(duration1, duration2)
        score += duration_balance * 0.2
        
        # Media variety
        media1 = len(getattr(chapter1, 'media_elements', []))
        media2 = len(getattr(chapter2, 'media_elements', []))
        media_variety = self._calculate_media_variety_score(media1, media2)
        score += media_variety * 0.1
        
        return score
    
    def _calculate_emotional_flow_score(self, tone1: str, tone2: str) -> float:
        """
        Calculate emotional flow score between two tones.
        
        Args:
            tone1: First emotional tone
            tone2: Second emotional tone
            
        Returns:
            Flow score between 0 and 1
        """
        # Define emotional transitions that flow well
        good_transitions = {
            'peaceful': ['reflective', 'nostalgic', 'growth'],
            'reflective': ['growth', 'peaceful', 'nostalgic'],
            'nostalgic': ['reflective', 'peaceful', 'joyful'],
            'joyful': ['adventurous', 'peaceful', 'celebration'],
            'adventurous': ['joyful', 'growth', 'reflective'],
            'growth': ['reflective', 'peaceful', 'joyful']
        }
        
        if tone2 in good_transitions.get(tone1, []):
            return 0.9
        elif tone1 == tone2:
            return 0.5  # Same tone is neutral
        else:
            return 0.3  # Other transitions are less optimal
    
    def _calculate_duration_balance_score(self, duration1: int, duration2: int) -> float:
        """
        Calculate duration balance score between chapters.
        
        Args:
            duration1: First chapter duration
            duration2: Second chapter duration
            
        Returns:
            Balance score between 0 and 1
        """
        ratio = min(duration1, duration2) / max(duration1, duration2) if max(duration1, duration2) > 0 else 1.0
        return ratio  # Higher score for more balanced durations
    
    def _calculate_media_variety_score(self, media1: int, media2: int) -> float:
        """
        Calculate media variety score between chapters.
        
        Args:
            media1: First chapter media count
            media2: Second chapter media count
            
        Returns:
            Variety score between 0 and 1
        """
        if self.prefer_visual_variety:
            # Prefer alternating media-rich and media-light chapters
            if (media1 > 2 and media2 <= 2) or (media1 <= 2 and media2 > 2):
                return 0.8
            else:
                return 0.5
        else:
            return 0.5  # Neutral if variety not preferred
    
    def _find_optimal_sequence(self, chapters: List[Chapter], 
                             flow_matrix: List[List[float]]) -> List[Chapter]:
        """
        Find optimal sequence using flow matrix (simplified greedy approach).
        
        Args:
            chapters: List of chapters to sequence
            flow_matrix: Matrix of flow scores
            
        Returns:
            Optimally sequenced chapters
        """
        if len(chapters) <= 1:
            return chapters
        
        # Simple greedy approach: start with best opening chapter, then follow best flows
        n = len(chapters)
        used = [False] * n
        sequence = []
        
        # Find best opening chapter (could be enhanced with more sophisticated criteria)
        current_idx = 0
        sequence.append(chapters[current_idx])
        used[current_idx] = True
        
        # Build sequence by following best flow scores
        for _ in range(n - 1):
            best_next_idx = -1
            best_flow_score = -1
            
            for next_idx in range(n):
                if not used[next_idx]:
                    flow_score = flow_matrix[current_idx][next_idx]
                    if flow_score > best_flow_score:
                        best_flow_score = flow_score
                        best_next_idx = next_idx
            
            if best_next_idx != -1:
                sequence.append(chapters[best_next_idx])
                used[best_next_idx] = True
                current_idx = best_next_idx
        
        return sequence
    
    def _adjust_sequence_pacing(self, chapters: List[Chapter]) -> List[Chapter]:
        """
        Adjust pacing of a chapter sequence.
        
        Args:
            chapters: Sequenced chapters
            
        Returns:
            Chapters with adjusted pacing
        """
        # Apply pacing adjustments based on position
        for i, chapter in enumerate(chapters):
            position_multiplier = self._calculate_position_pacing_multiplier(i, len(chapters))
            current_duration = getattr(chapter, 'duration_seconds', 60)
            
            new_duration = int(current_duration * position_multiplier)
            new_duration = max(self.min_chapter_duration, min(new_duration, self.max_chapter_duration))
            
            chapter.duration_seconds = new_duration
        
        return chapters
    
    def _sequence_chronologically(self, memories: List[EnhancedLLEntry]) -> List[EnhancedLLEntry]:
        """Sequence memories chronologically."""
        return sorted(memories, key=lambda m: getattr(m, 'startTime', datetime.min))
    
    def _sequence_thematically(self, memories: List[EnhancedLLEntry]) -> List[EnhancedLLEntry]:
        """Sequence memories thematically."""
        # Group by themes and sequence within groups
        theme_groups = {}
        for memory in memories:
            theme = getattr(memory, 'thematic_tags', ['general'])[0] if hasattr(memory, 'thematic_tags') and memory.thematic_tags else 'general'
            if theme not in theme_groups:
                theme_groups[theme] = []
            theme_groups[theme].append(memory)
        
        # Sequence each group chronologically and combine
        sequenced = []
        for theme in sorted(theme_groups.keys()):
            group = sorted(theme_groups[theme], key=lambda m: getattr(m, 'startTime', datetime.min))
            sequenced.extend(group)
        
        return sequenced
    
    def _sequence_emotionally(self, memories: List[EnhancedLLEntry]) -> List[EnhancedLLEntry]:
        """Sequence memories for emotional flow."""
        # Simple emotional sequencing (could be enhanced)
        return sorted(memories, key=lambda m: getattr(m, 'narrative_significance', 0.0), reverse=True)
    
    def _sequence_by_narrative_flow(self, memories: List[EnhancedLLEntry]) -> List[EnhancedLLEntry]:
        """Sequence memories for optimal narrative flow."""
        # Combine multiple factors for narrative flow
        def narrative_score(memory):
            significance = getattr(memory, 'narrative_significance', 0.0)
            story_potential = getattr(memory, 'story_potential', 0.0)
            return significance * 0.6 + story_potential * 0.4
        
        return sorted(memories, key=narrative_score, reverse=True)
    
    def _sequence_generic_content(self, content: List[Any], 
                                context: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Sequence generic content."""
        # For generic content, maintain original order or apply simple sorting
        return content
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data for the Director Agent.
        
        Args:
            input_data: Data to validate
            
        Returns:
            True if input is valid
        """
        if isinstance(input_data, (Story, list, dict)):
            return True
        
        return False