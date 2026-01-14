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
import re
from datetime import datetime

from .base_agent import BaseAgent
from src.common.objects.enhanced_llentry import EnhancedLLEntry, Story, Chapter


class CriticAgent(BaseAgent):
    """
    The Critic Agent is responsible for checking tone, safety, and grounding
    in actual user data. It serves as the final quality control layer,
    ensuring all generated content meets privacy, safety, and accuracy standards.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("critic", config)
        
        # Quality control parameters
        self.min_quality_score = self.config.get('min_quality_score', 0.7)
        self.require_data_grounding = self.config.get('require_data_grounding', True)
        self.strict_privacy_mode = self.config.get('strict_privacy_mode', True)
        
        # Safety parameters
        self.avoid_diagnostic_language = self.config.get('avoid_diagnostic_language', True)
        self.avoid_impersonation = self.config.get('avoid_impersonation', True)
        self.filter_sensitive_content = self.config.get('filter_sensitive_content', True)
        
        # Tone parameters
        self.preferred_tones = self.config.get('preferred_tones', ['respectful', 'thoughtful', 'grounded'])
        self.avoid_tones = self.config.get('avoid_tones', ['diagnostic', 'presumptuous', 'invasive'])
        
    def _initialize_agent(self) -> None:
        """Initialize the Critic Agent with quality control and safety checks."""
        self.logger.info("Initializing Critic Agent quality control and safety systems")
        
        # Initialize safety patterns
        self.diagnostic_patterns = [
            r'\byou are\s+\w+',  # "you are depressed", "you are anxious"
            r'\byou have\s+\w+',  # "you have issues", "you have problems"
            r'\byou suffer from\b',
            r'\byou need\s+(help|therapy|treatment)\b',
            r'\bdiagnosis\b',
            r'\bdisorder\b',
            r'\bcondition\b',
            r'\bsymptoms?\b'
        ]
        
        # Initialize impersonation patterns
        self.impersonation_patterns = [
            r'\bi\s+(felt|thought|believed|wanted|needed)\b',  # First person from narrator
            r'\bmy\s+\w+',  # "my feelings", "my thoughts"
            r'\bi\s+(am|was|will be)\b'
        ]
        
        # Initialize sensitive content patterns
        self.sensitive_patterns = [
            r'\b(ssn|social security number|credit card|password)\b',
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b',  # Credit card pattern
            r'\b(private|confidential|secret)\s+\w+\b'
        ]
        
        # Initialize quality indicators
        self.quality_indicators = {
            'positive': [
                'grounded in', 'based on', 'from the data', 'according to',
                'memory shows', 'experience indicates', 'moment captured'
            ],
            'negative': [
                'probably', 'likely', 'seems like', 'appears to be',
                'suggests that you', 'indicates you are', 'shows you have'
            ]
        }
        
        # Initialize tone analysis patterns
        self.tone_patterns = {
            'respectful': [r'\bexperience\b', r'\bmoment\b', r'\bmemory\b', r'\btime\b'],
            'thoughtful': [r'\breflect\b', r'\bconsider\b', r'\bthought\b', r'\binsight\b'],
            'grounded': [r'\bdata shows\b', r'\bmemory indicates\b', r'\brecord shows\b'],
            'diagnostic': [r'\byou are\b', r'\byou have\b', r'\byou need\b'],
            'presumptuous': [r'\bobviously\b', r'\bclearly you\b', r'\byou must\b'],
            'invasive': [r'\bpersonal issues\b', r'\bproblems\b', r'\bmental health\b']
        }
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform quality control and safety checks on content.
        
        Args:
            input_data: Content to be reviewed
            context: Optional context from other agents
            
        Returns:
            Review results with approval status and feedback
        """
        if isinstance(input_data, Story):
            return self._review_story(input_data, context)
        elif isinstance(input_data, Chapter):
            return self._review_chapter(input_data, context)
        elif isinstance(input_data, list):
            if all(isinstance(item, EnhancedLLEntry) for item in input_data):
                return self._review_memory_selection(input_data, context)
            else:
                return self._review_generic_content(input_data, context)
        elif isinstance(input_data, str):
            return self._review_text_content(input_data, context)
        elif isinstance(input_data, dict):
            return self._review_content_request(input_data, context)
        else:
            self.logger.warning(f"Unexpected input type: {type(input_data)}")
            return self._create_review_result(False, "Unsupported content type", {})
    
    def _review_story(self, story: Story, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Review a complete story for quality and safety.
        
        Args:
            story: Story to review
            context: Optional context information
            
        Returns:
            Review results
        """
        issues = []
        quality_scores = []
        
        # Review story title
        title_review = self._review_text_content(story.title, context)
        if not title_review['approved']:
            issues.extend(title_review['issues'])
        quality_scores.append(title_review['quality_score'])
        
        # Review each chapter
        chapter_reviews = []
        for i, chapter in enumerate(story.chapters):
            chapter_review = self._review_chapter(chapter, context)
            chapter_reviews.append(chapter_review)
            
            if not chapter_review['approved']:
                issues.append(f"Chapter {i+1}: {', '.join(chapter_review['issues'])}")
            quality_scores.append(chapter_review['quality_score'])
        
        # Check story structure
        structure_issues = self._check_story_structure(story)
        issues.extend(structure_issues)
        
        # Check data grounding
        grounding_issues = self._check_story_grounding(story, context)
        issues.extend(grounding_issues)
        
        # Calculate overall quality score
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Determine approval
        approved = len(issues) == 0 and overall_quality >= self.min_quality_score
        
        review_result = self._create_review_result(
            approved=approved,
            issues=issues,
            metadata={
                'story_id': story.id,
                'chapter_count': len(story.chapters),
                'chapter_reviews': chapter_reviews,
                'overall_quality_score': overall_quality,
                'structure_check': len(structure_issues) == 0,
                'grounding_check': len(grounding_issues) == 0
            }
        )
        
        self.logger.info(f"Reviewed story '{story.title}': {'APPROVED' if approved else 'REJECTED'} "
                        f"(Quality: {overall_quality:.2f}, Issues: {len(issues)})")
        
        return review_result
    
    def _review_chapter(self, chapter: Chapter, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Review a chapter for quality and safety.
        
        Args:
            chapter: Chapter to review
            context: Optional context information
            
        Returns:
            Review results
        """
        issues = []
        
        # Review chapter title
        title_issues = self._check_text_safety(chapter.title)
        issues.extend(title_issues)
        
        # Review narrative text
        narrative_issues = self._check_narrative_text(chapter.narrative_text)
        issues.extend(narrative_issues)
        
        # Check tone appropriateness
        tone_issues = self._check_tone_appropriateness(chapter.narrative_text)
        issues.extend(tone_issues)
        
        # Check media elements
        media_issues = self._check_media_elements(chapter.media_elements)
        issues.extend(media_issues)
        
        # Check chapter structure
        structure_issues = self._check_chapter_structure(chapter)
        issues.extend(structure_issues)
        
        # Calculate quality score
        quality_score = self._calculate_chapter_quality_score(chapter)
        
        # Determine approval
        approved = len(issues) == 0 and quality_score >= self.min_quality_score
        
        return self._create_review_result(
            approved=approved,
            issues=issues,
            metadata={
                'chapter_id': chapter.id,
                'quality_score': quality_score,
                'narrative_length': len(chapter.narrative_text),
                'media_count': len(chapter.media_elements),
                'emotional_tone': chapter.emotional_tone
            }
        )
    
    def _review_memory_selection(self, memories: List[EnhancedLLEntry], 
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Review a selection of memories for appropriateness.
        
        Args:
            memories: List of memories to review
            context: Optional context information
            
        Returns:
            Review results
        """
        issues = []
        quality_scores = []
        
        for i, memory in enumerate(memories):
            # Check memory content safety
            if hasattr(memory, 'text') and memory.text:
                text_issues = self._check_text_safety(memory.text)
                if text_issues:
                    issues.append(f"Memory {i+1}: {', '.join(text_issues)}")
            
            # Check data grounding
            if self.require_data_grounding:
                if not self._is_memory_well_grounded(memory):
                    issues.append(f"Memory {i+1}: Insufficient data grounding")
            
            # Calculate quality score for this memory
            memory_quality = self._calculate_memory_quality_score(memory)
            quality_scores.append(memory_quality)
        
        # Check selection diversity and balance
        selection_issues = self._check_selection_quality(memories)
        issues.extend(selection_issues)
        
        # Calculate overall quality
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Determine approval
        approved = len(issues) == 0 and overall_quality >= self.min_quality_score
        
        return self._create_review_result(
            approved=approved,
            issues=issues,
            metadata={
                'memory_count': len(memories),
                'overall_quality_score': overall_quality,
                'individual_scores': quality_scores,
                'selection_diversity': self._calculate_selection_diversity(memories)
            }
        )
    
    def _review_text_content(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Review text content for safety and appropriateness.
        
        Args:
            text: Text to review
            context: Optional context information
            
        Returns:
            Review results
        """
        issues = []
        
        # Check basic safety
        safety_issues = self._check_text_safety(text)
        issues.extend(safety_issues)
        
        # Check tone
        tone_issues = self._check_tone_appropriateness(text)
        issues.extend(tone_issues)
        
        # Calculate quality score
        quality_score = self._calculate_text_quality_score(text)
        
        # Determine approval
        approved = len(issues) == 0 and quality_score >= self.min_quality_score
        
        return self._create_review_result(
            approved=approved,
            issues=issues,
            metadata={
                'text_length': len(text),
                'quality_score': quality_score,
                'tone_analysis': self._analyze_text_tone(text)
            }
        )
    
    def _review_content_request(self, request: Dict[str, Any], 
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Review a content request for safety and appropriateness.
        
        Args:
            request: Content request to review
            context: Optional context information
            
        Returns:
            Review results
        """
        issues = []
        
        # Review query text if present
        if 'query' in request and request['query']:
            query_issues = self._check_text_safety(request['query'])
            if query_issues:
                issues.extend([f"Query: {issue}" for issue in query_issues])
        
        # Review theme if present
        if 'theme' in request and request['theme']:
            theme_issues = self._check_text_safety(request['theme'])
            if theme_issues:
                issues.extend([f"Theme: {issue}" for issue in theme_issues])
        
        # Check request parameters
        param_issues = self._check_request_parameters(request)
        issues.extend(param_issues)
        
        # Determine approval
        approved = len(issues) == 0
        
        return self._create_review_result(
            approved=approved,
            issues=issues,
            metadata={
                'request_type': request.get('type', 'unknown'),
                'has_query': 'query' in request,
                'has_theme': 'theme' in request
            }
        )
    
    def _review_generic_content(self, content: List[Any], 
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Review generic content list.
        
        Args:
            content: Content list to review
            context: Optional context information
            
        Returns:
            Review results
        """
        issues = []
        
        # Basic validation
        if len(content) == 0:
            issues.append("Empty content list")
        elif len(content) > 100:  # Reasonable limit
            issues.append("Content list too large")
        
        # Determine approval
        approved = len(issues) == 0
        
        return self._create_review_result(
            approved=approved,
            issues=issues,
            metadata={
                'content_count': len(content),
                'content_type': type(content[0]).__name__ if content else 'empty'
            }
        )
    
    def _check_text_safety(self, text: str) -> List[str]:
        """
        Check text for safety issues.
        
        Args:
            text: Text to check
            
        Returns:
            List of safety issues found
        """
        issues = []
        
        if not text:
            return issues
        
        text_lower = text.lower()
        
        # Check for diagnostic language
        if self.avoid_diagnostic_language:
            for pattern in self.diagnostic_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append("Contains diagnostic language")
                    break
        
        # Check for impersonation
        if self.avoid_impersonation:
            for pattern in self.impersonation_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append("Contains narrator impersonation")
                    break
        
        # Check for sensitive content
        if self.filter_sensitive_content:
            for pattern in self.sensitive_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append("Contains sensitive information")
                    break
        
        return issues
    
    def _check_narrative_text(self, text: str) -> List[str]:
        """
        Check narrative text for specific narrative quality issues.
        
        Args:
            text: Narrative text to check
            
        Returns:
            List of issues found
        """
        issues = []
        
        if not text:
            issues.append("Empty narrative text")
            return issues
        
        # Check length appropriateness
        if len(text.strip()) < 20:
            issues.append("Narrative text too short")
        elif len(text) > 1000:
            issues.append("Narrative text too long")
        
        # Check for proper grounding language
        grounding_indicators = self.quality_indicators['positive']
        has_grounding = any(indicator in text.lower() for indicator in grounding_indicators)
        
        if self.require_data_grounding and not has_grounding:
            issues.append("Lacks proper data grounding")
        
        # Check for problematic language
        problematic_indicators = self.quality_indicators['negative']
        has_problematic = any(indicator in text.lower() for indicator in problematic_indicators)
        
        if has_problematic:
            issues.append("Contains speculative or presumptuous language")
        
        return issues
    
    def _check_tone_appropriateness(self, text: str) -> List[str]:
        """
        Check if text tone is appropriate.
        
        Args:
            text: Text to check
            
        Returns:
            List of tone issues found
        """
        issues = []
        
        if not text:
            return issues
        
        text_lower = text.lower()
        
        # Check for inappropriate tones
        for tone in self.avoid_tones:
            if tone in self.tone_patterns:
                patterns = self.tone_patterns[tone]
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        issues.append(f"Inappropriate {tone} tone detected")
                        break
        
        return issues
    
    def _check_media_elements(self, media_elements: List[str]) -> List[str]:
        """
        Check media elements for safety and appropriateness.
        
        Args:
            media_elements: List of media file paths
            
        Returns:
            List of issues found
        """
        issues = []
        
        for media_path in media_elements:
            if not media_path:
                issues.append("Empty media path")
                continue
            
            # Check for safe file extensions
            safe_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi', '.webp']
            if not any(media_path.lower().endswith(ext) for ext in safe_extensions):
                issues.append(f"Unsafe media file type: {media_path}")
            
            # Check for suspicious paths
            if '../' in media_path or media_path.startswith('/'):
                issues.append(f"Suspicious media path: {media_path}")
        
        return issues
    
    def _check_story_structure(self, story: Story) -> List[str]:
        """
        Check story structure for quality issues.
        
        Args:
            story: Story to check
            
        Returns:
            List of structural issues found
        """
        issues = []
        
        # Check chapter count
        if len(story.chapters) == 0:
            issues.append("Story has no chapters")
        elif len(story.chapters) > 20:
            issues.append("Story has too many chapters")
        
        # Check for empty chapters
        empty_chapters = [i for i, ch in enumerate(story.chapters) 
                         if not ch.narrative_text or len(ch.narrative_text.strip()) < 10]
        if empty_chapters:
            issues.append(f"Empty chapters found: {empty_chapters}")
        
        # Check total duration reasonableness
        total_duration = sum(ch.duration_seconds for ch in story.chapters)
        if total_duration < 60:  # Less than 1 minute
            issues.append("Story too short")
        elif total_duration > 1800:  # More than 30 minutes
            issues.append("Story too long")
        
        return issues
    
    def _check_story_grounding(self, story: Story, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Check if story is properly grounded in actual data.
        
        Args:
            story: Story to check
            context: Optional context information
            
        Returns:
            List of grounding issues found
        """
        issues = []
        
        if not self.require_data_grounding:
            return issues
        
        # Check if story has source memory IDs
        if not story.source_memory_ids:
            issues.append("Story lacks source memory references")
        
        # Check if chapters reference actual data
        for i, chapter in enumerate(story.chapters):
            if not self._is_chapter_grounded(chapter):
                issues.append(f"Chapter {i+1} lacks proper data grounding")
        
        return issues
    
    def _check_chapter_structure(self, chapter: Chapter) -> List[str]:
        """
        Check chapter structure for quality issues.
        
        Args:
            chapter: Chapter to check
            
        Returns:
            List of structural issues found
        """
        issues = []
        
        # Check title
        if not chapter.title or len(chapter.title.strip()) < 3:
            issues.append("Chapter title too short or missing")
        
        # Check narrative text structure
        if chapter.narrative_text:
            sentences = chapter.narrative_text.split('.')
            sentence_count = len([s for s in sentences if s.strip()])
            
            if sentence_count > 5:
                issues.append("Chapter narrative too long (>5 sentences)")
            elif sentence_count == 0:
                issues.append("Chapter has no complete sentences")
        
        # Check duration reasonableness
        if chapter.duration_seconds < 10:
            issues.append("Chapter duration too short")
        elif chapter.duration_seconds > 300:  # 5 minutes
            issues.append("Chapter duration too long")
        
        return issues
    
    def _check_selection_quality(self, memories: List[EnhancedLLEntry]) -> List[str]:
        """
        Check quality of memory selection.
        
        Args:
            memories: List of selected memories
            
        Returns:
            List of selection quality issues
        """
        issues = []
        
        if len(memories) == 0:
            issues.append("Empty memory selection")
            return issues
        
        # Check for temporal diversity
        if len(memories) > 1:
            time_spans = []
            for memory in memories:
                if hasattr(memory, 'startTime') and memory.startTime:
                    time_spans.append(memory.startTime)
            
            if len(set(time_spans)) == 1:
                issues.append("All memories from same time period")
        
        # Check for content diversity
        if len(memories) > 3:
            text_contents = []
            for memory in memories:
                if hasattr(memory, 'text') and memory.text:
                    text_contents.append(memory.text[:100].lower())  # First 100 chars
            
            # Simple similarity check
            unique_contents = set(text_contents)
            if len(unique_contents) < len(text_contents) * 0.7:
                issues.append("Low content diversity in selection")
        
        return issues
    
    def _check_request_parameters(self, request: Dict[str, Any]) -> List[str]:
        """
        Check request parameters for safety and reasonableness.
        
        Args:
            request: Request to check
            
        Returns:
            List of parameter issues found
        """
        issues = []
        
        # Check max_results parameter
        if 'max_results' in request:
            max_results = request['max_results']
            if not isinstance(max_results, int) or max_results < 1:
                issues.append("Invalid max_results parameter")
            elif max_results > 1000:
                issues.append("max_results too large")
        
        # Check time_range parameter
        if 'time_range' in request:
            time_range = request['time_range']
            if not isinstance(time_range, (list, tuple)) or len(time_range) != 2:
                issues.append("Invalid time_range parameter")
        
        return issues
    
    def _calculate_chapter_quality_score(self, chapter: Chapter) -> float:
        """
        Calculate quality score for a chapter.
        
        Args:
            chapter: Chapter to score
            
        Returns:
            Quality score between 0 and 1
        """
        score = 0.0
        
        # Narrative text quality
        if chapter.narrative_text:
            text_score = self._calculate_text_quality_score(chapter.narrative_text)
            score += text_score * 0.5
        
        # Structure quality
        structure_score = 1.0
        if not chapter.title or len(chapter.title.strip()) < 3:
            structure_score -= 0.3
        
        if chapter.duration_seconds < 10 or chapter.duration_seconds > 300:
            structure_score -= 0.2
        
        score += max(0, structure_score) * 0.3
        
        # Media quality
        media_score = min(len(chapter.media_elements) / 3.0, 1.0)  # Up to 3 media elements is optimal
        score += media_score * 0.2
        
        return min(score, 1.0)
    
    def _calculate_memory_quality_score(self, memory: EnhancedLLEntry) -> float:
        """
        Calculate quality score for a memory.
        
        Args:
            memory: Memory to score
            
        Returns:
            Quality score between 0 and 1
        """
        score = 0.0
        
        # Use existing quality indicators if available
        if hasattr(memory, 'narrative_significance'):
            score += memory.narrative_significance * 0.4
        
        if hasattr(memory, 'story_potential'):
            score += memory.story_potential * 0.3
        
        # Text content quality
        if hasattr(memory, 'text') and memory.text:
            text_score = self._calculate_text_quality_score(memory.text)
            score += text_score * 0.2
        
        # Media presence bonus
        has_media = (hasattr(memory, 'photos') and memory.photos) or \
                   (hasattr(memory, 'videos') and memory.videos)
        if has_media:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_text_quality_score(self, text: str) -> float:
        """
        Calculate quality score for text content.
        
        Args:
            text: Text to score
            
        Returns:
            Quality score between 0 and 1
        """
        if not text:
            return 0.0
        
        score = 0.5  # Base score
        
        # Length appropriateness
        length = len(text.strip())
        if 20 <= length <= 500:
            score += 0.2
        elif length < 20:
            score -= 0.3
        elif length > 1000:
            score -= 0.2
        
        # Positive quality indicators
        positive_count = sum(1 for indicator in self.quality_indicators['positive'] 
                           if indicator in text.lower())
        score += min(positive_count * 0.1, 0.2)
        
        # Negative quality indicators
        negative_count = sum(1 for indicator in self.quality_indicators['negative'] 
                           if indicator in text.lower())
        score -= min(negative_count * 0.1, 0.3)
        
        # Safety deductions
        safety_issues = self._check_text_safety(text)
        score -= len(safety_issues) * 0.2
        
        return max(0.0, min(score, 1.0))
    
    def _calculate_selection_diversity(self, memories: List[EnhancedLLEntry]) -> float:
        """
        Calculate diversity score for memory selection.
        
        Args:
            memories: List of memories
            
        Returns:
            Diversity score between 0 and 1
        """
        if len(memories) <= 1:
            return 1.0
        
        # Time diversity
        time_diversity = 0.0
        if all(hasattr(m, 'startTime') and m.startTime for m in memories):
            time_spans = [m.startTime for m in memories]
            unique_days = len(set(t.date() for t in time_spans))
            time_diversity = min(unique_days / len(memories), 1.0)
        
        # Content diversity (simple check)
        content_diversity = 0.0
        if all(hasattr(m, 'text') and m.text for m in memories):
            text_samples = [m.text[:50].lower() for m in memories]  # First 50 chars
            unique_samples = len(set(text_samples))
            content_diversity = unique_samples / len(memories)
        
        # Combine diversities
        return (time_diversity + content_diversity) / 2.0
    
    def _analyze_text_tone(self, text: str) -> Dict[str, float]:
        """
        Analyze the tone of text content.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of tone scores
        """
        tone_scores = {}
        
        if not text:
            return tone_scores
        
        text_lower = text.lower()
        
        for tone, patterns in self.tone_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            
            # Normalize by text length
            tone_scores[tone] = min(score / max(len(text.split()) / 10, 1), 1.0)
        
        return tone_scores
    
    def _is_memory_well_grounded(self, memory: EnhancedLLEntry) -> bool:
        """
        Check if a memory is well-grounded in actual data.
        
        Args:
            memory: Memory to check
            
        Returns:
            True if memory is well-grounded
        """
        # Check for basic data presence
        has_text = hasattr(memory, 'text') and memory.text
        has_time = hasattr(memory, 'startTime') and memory.startTime
        has_source = hasattr(memory, 'source') and memory.source
        
        return has_text and has_time and has_source
    
    def _is_chapter_grounded(self, chapter: Chapter) -> bool:
        """
        Check if a chapter is grounded in actual data.
        
        Args:
            chapter: Chapter to check
            
        Returns:
            True if chapter is grounded
        """
        if not chapter.narrative_text:
            return False
        
        # Look for grounding indicators in the text
        grounding_indicators = self.quality_indicators['positive']
        return any(indicator in chapter.narrative_text.lower() for indicator in grounding_indicators)
    
    def _create_review_result(self, approved: bool, issues: List[str], 
                            metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a standardized review result.
        
        Args:
            approved: Whether content is approved
            issues: List of issues found
            metadata: Additional metadata
            
        Returns:
            Review result dictionary
        """
        return {
            'approved': approved,
            'issues': issues,
            'quality_score': metadata.get('quality_score', 0.0),
            'metadata': metadata,
            'reviewed_at': datetime.now(),
            'reviewer': self.agent_name
        }
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data for the Critic Agent.
        
        Args:
            input_data: Data to validate
            
        Returns:
            True if input is valid
        """
        # Critic agent can review almost any type of content
        return input_data is not None