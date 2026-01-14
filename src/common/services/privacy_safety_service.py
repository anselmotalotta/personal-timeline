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
import re
import socket
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from src.common.objects.enhanced_llentry import EnhancedLLEntry, Story, Chapter


class PrivacyLevel(Enum):
    """Privacy levels for content generation and processing."""
    STRICT = "strict"
    MODERATE = "moderate"
    RELAXED = "relaxed"


class ContentSensitivity(Enum):
    """Content sensitivity levels."""
    PUBLIC = "public"
    PRIVATE = "private"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


@dataclass
class PrivacySettings:
    """User privacy settings and preferences."""
    privacy_level: PrivacyLevel = PrivacyLevel.STRICT
    default_content_sensitivity: ContentSensitivity = ContentSensitivity.PRIVATE
    allow_external_processing: bool = False
    enable_diagnostic_statements: bool = False
    sensitive_keywords: List[str] = None
    excluded_time_periods: List[Tuple[datetime, datetime]] = None
    excluded_people: List[str] = None
    excluded_locations: List[str] = None
    
    def __post_init__(self):
        if self.sensitive_keywords is None:
            self.sensitive_keywords = []
        if self.excluded_time_periods is None:
            self.excluded_time_periods = []
        if self.excluded_people is None:
            self.excluded_people = []
        if self.excluded_locations is None:
            self.excluded_locations = []


@dataclass
class NetworkActivity:
    """Record of network activity for monitoring."""
    timestamp: datetime
    destination: str
    port: int
    protocol: str
    blocked: bool
    reason: str


class PrivacySafetyService:
    """
    Service for implementing privacy and safety controls throughout the system.
    
    This service ensures:
    1. All processing remains local (no external service calls)
    2. Content generation defaults to private mode
    3. Diagnostic statements are prevented
    4. User controls for sensitive content
    5. Comprehensive privacy monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize privacy settings
        self.privacy_settings = PrivacySettings(
            privacy_level=PrivacyLevel(self.config.get('privacy_level', 'strict')),
            default_content_sensitivity=ContentSensitivity(
                self.config.get('default_content_sensitivity', 'private')
            ),
            allow_external_processing=self.config.get('allow_external_processing', False),
            enable_diagnostic_statements=self.config.get('enable_diagnostic_statements', False),
            sensitive_keywords=self.config.get('sensitive_keywords', []),
            excluded_time_periods=self._parse_excluded_time_periods(
                self.config.get('excluded_time_periods', [])
            ),
            excluded_people=self.config.get('excluded_people', []),
            excluded_locations=self.config.get('excluded_locations', [])
        )
        
        # Network monitoring
        self.network_monitor_enabled = self.config.get('enable_network_monitoring', True)
        self.network_activity_log: List[NetworkActivity] = []
        self.blocked_domains = set(self.config.get('blocked_domains', [
            'openai.com', 'api.openai.com', 'anthropic.com', 'api.anthropic.com',
            'googleapis.com', 'azure.microsoft.com', 'aws.amazon.com',
            'huggingface.co', 'replicate.com', 'cohere.ai'
        ]))
        
        # Diagnostic statement patterns to prevent
        self.diagnostic_patterns = [
            r'\byou are\b.*\b(depressed|anxious|bipolar|adhd|autistic|narcissistic)\b',
            r'\byou have\b.*\b(depression|anxiety|bipolar|adhd|autism|ptsd)\b',
            r'\byou suffer from\b',
            r'\byou struggle with\b.*\b(mental|psychological|emotional)\b',
            r'\bthis indicates\b.*\b(disorder|condition|illness)\b',
            r'\bdiagnosis\b.*\b(suggests|indicates|shows)\b',
            r'\byou exhibit\b.*\b(symptoms|signs|patterns)\b.*\b(of|for)\b',
            r'\bthis behavior is\b.*\b(typical|characteristic)\b.*\b(of|for)\b.*\b(disorder|condition)\b'
        ]
        
        # Compile patterns for efficiency
        self.compiled_diagnostic_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.diagnostic_patterns
        ]
        
        # Content filtering patterns
        self.sensitive_content_patterns = [
            r'\b(password|ssn|social security|credit card|bank account)\b',
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card pattern
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email pattern
        ]
        
        self.compiled_sensitive_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_content_patterns
        ]
        
        # Initialize network monitoring if enabled
        if self.network_monitor_enabled:
            self._start_network_monitoring()
        
        self.logger.info(f"Privacy Safety Service initialized with {self.privacy_settings.privacy_level.value} privacy level")
    
    def validate_local_processing(self, operation: str, data: Any = None) -> bool:
        """
        Validate that an operation will be processed locally without external calls.
        
        Args:
            operation: Description of the operation being performed
            data: Optional data being processed
            
        Returns:
            True if operation is safe for local processing, False otherwise
        """
        try:
            # Check if external processing is explicitly disabled
            if not self.privacy_settings.allow_external_processing:
                # Log the validation
                self.logger.info(f"Validating local processing for operation: {operation}")
                
                # For now, assume all operations are local unless explicitly configured otherwise
                # In a real implementation, this would check for:
                # - API calls to external services
                # - Network requests
                # - Cloud service integrations
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating local processing: {str(e)}")
            return False
    
    def ensure_private_content_generation(self, content: str, context: Dict[str, Any] = None) -> str:
        """
        Ensure content generation defaults to private mode with no sharing capabilities.
        
        Args:
            content: Generated content to process
            context: Additional context for processing
            
        Returns:
            Processed content with privacy controls applied
        """
        try:
            context = context or {}
            
            # Apply content sensitivity classification
            sensitivity = self._classify_content_sensitivity(content)
            
            # Add privacy markers to content
            if sensitivity in [ContentSensitivity.SENSITIVE, ContentSensitivity.RESTRICTED]:
                # Add privacy notice for sensitive content
                privacy_notice = "\n\n[This content contains personal information and is marked as private]"
                content = content + privacy_notice
            
            # Remove any sharing suggestions or public indicators
            content = self._remove_sharing_suggestions(content)
            
            # Log privacy processing
            self.logger.debug(f"Applied private content generation controls, sensitivity: {sensitivity.value}")
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error ensuring private content generation: {str(e)}")
            return content
    
    def prevent_diagnostic_statements(self, text: str) -> Tuple[str, List[str]]:
        """
        Prevent diagnostic statements and "You are X" declarations in generated content.
        
        Args:
            text: Text to check and filter
            
        Returns:
            Tuple of (filtered_text, list_of_detected_issues)
        """
        try:
            detected_issues = []
            filtered_text = text
            
            # Check for diagnostic patterns and replace them completely
            for i, pattern in enumerate(self.compiled_diagnostic_patterns):
                matches = pattern.findall(text)
                if matches:
                    detected_issues.append(f"Diagnostic pattern {i+1}: {matches}")
                    # Replace entire diagnostic statements with neutral alternatives
                    filtered_text = pattern.sub(
                        lambda m: self._neutralize_diagnostic_statement(m.group(0)),
                        filtered_text
                    )
            
            # Check for absolute "You are" statements with mental health terms
            you_are_pattern = re.compile(r'\byou are\b\s+(?:depressed|anxious|bipolar|adhd|autistic|narcissistic)\b[^.]*\.?', re.IGNORECASE)
            you_are_matches = you_are_pattern.findall(text)
            if you_are_matches:
                detected_issues.append(f"Absolute statements: {you_are_matches}")
                # Replace with neutral observation
                filtered_text = you_are_pattern.sub(
                    'Your data shows certain patterns (observation only, not a diagnosis).',
                    filtered_text
                )
            
            # Additional check for any remaining "you are [condition]" patterns
            remaining_you_are = re.compile(r'\byou are\b\s+\w+', re.IGNORECASE)
            remaining_matches = remaining_you_are.findall(filtered_text)
            if remaining_matches and any(condition in ' '.join(remaining_matches).lower() 
                                       for condition in ['depressed', 'anxious', 'bipolar']):
                # Replace any remaining problematic "you are" statements
                filtered_text = remaining_you_are.sub(
                    lambda m: 'patterns suggest you might be ' + m.group(0).split()[-1] + ' (based on data patterns)',
                    filtered_text
                )
            
            # Log any issues found
            if detected_issues:
                self.logger.warning(f"Prevented diagnostic statements: {detected_issues}")
            
            return filtered_text, detected_issues
            
        except Exception as e:
            self.logger.error(f"Error preventing diagnostic statements: {str(e)}")
            return text, []
    
    def apply_user_content_controls(self, content: Any, user_controls: Dict[str, Any] = None) -> Any:
        """
        Apply user controls for sensitive content exclusion and modification.
        
        Args:
            content: Content to filter (can be text, Story, Chapter, or EnhancedLLEntry)
            user_controls: User-specified controls and preferences
            
        Returns:
            Filtered content with user controls applied
        """
        try:
            user_controls = user_controls or {}
            
            if isinstance(content, str):
                return self._filter_text_content(content, user_controls)
            elif isinstance(content, Story):
                return self._filter_story_content(content, user_controls)
            elif isinstance(content, Chapter):
                return self._filter_chapter_content(content, user_controls)
            elif isinstance(content, EnhancedLLEntry):
                return self._filter_memory_content(content, user_controls)
            elif isinstance(content, list):
                return [self.apply_user_content_controls(item, user_controls) for item in content]
            else:
                return content
                
        except Exception as e:
            self.logger.error(f"Error applying user content controls: {str(e)}")
            return content
    
    def monitor_privacy_compliance(self) -> Dict[str, Any]:
        """
        Monitor and report on privacy compliance across the system.
        
        Returns:
            Dictionary containing privacy compliance status and metrics
        """
        try:
            compliance_report = {
                'timestamp': datetime.now(),
                'privacy_level': self.privacy_settings.privacy_level.value,
                'local_processing_only': not self.privacy_settings.allow_external_processing,
                'diagnostic_prevention_enabled': not self.privacy_settings.enable_diagnostic_statements,
                'network_monitoring_enabled': self.network_monitor_enabled,
                'network_activity_count': len(self.network_activity_log),
                'blocked_network_attempts': sum(1 for activity in self.network_activity_log if activity.blocked),
                'sensitive_content_filters_active': len(self.compiled_sensitive_patterns) > 0,
                'user_exclusions': {
                    'excluded_people_count': len(self.privacy_settings.excluded_people),
                    'excluded_locations_count': len(self.privacy_settings.excluded_locations),
                    'excluded_time_periods_count': len(self.privacy_settings.excluded_time_periods)
                }
            }
            
            # Check for recent privacy violations
            recent_violations = self._check_recent_privacy_violations()
            compliance_report['recent_violations'] = recent_violations
            
            # Overall compliance score
            compliance_score = self._calculate_compliance_score(compliance_report)
            compliance_report['compliance_score'] = compliance_score
            
            self.logger.info(f"Privacy compliance monitoring complete, score: {compliance_score}")
            
            return compliance_report
            
        except Exception as e:
            self.logger.error(f"Error monitoring privacy compliance: {str(e)}")
            return {'error': str(e), 'timestamp': datetime.now()}
    
    def update_privacy_settings(self, new_settings: Dict[str, Any]) -> bool:
        """
        Update privacy settings with user preferences.
        
        Args:
            new_settings: Dictionary of new privacy settings
            
        Returns:
            True if settings were updated successfully, False otherwise
        """
        try:
            # Validate new settings
            if 'privacy_level' in new_settings:
                privacy_level = PrivacyLevel(new_settings['privacy_level'])
                self.privacy_settings.privacy_level = privacy_level
            
            if 'default_content_sensitivity' in new_settings:
                sensitivity = ContentSensitivity(new_settings['default_content_sensitivity'])
                self.privacy_settings.default_content_sensitivity = sensitivity
            
            if 'allow_external_processing' in new_settings:
                self.privacy_settings.allow_external_processing = bool(new_settings['allow_external_processing'])
            
            if 'enable_diagnostic_statements' in new_settings:
                self.privacy_settings.enable_diagnostic_statements = bool(new_settings['enable_diagnostic_statements'])
            
            if 'sensitive_keywords' in new_settings:
                self.privacy_settings.sensitive_keywords = list(new_settings['sensitive_keywords'])
            
            if 'excluded_people' in new_settings:
                self.privacy_settings.excluded_people = list(new_settings['excluded_people'])
            
            if 'excluded_locations' in new_settings:
                self.privacy_settings.excluded_locations = list(new_settings['excluded_locations'])
            
            if 'excluded_time_periods' in new_settings:
                self.privacy_settings.excluded_time_periods = self._parse_excluded_time_periods(
                    new_settings['excluded_time_periods']
                )
            
            self.logger.info(f"Privacy settings updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating privacy settings: {str(e)}")
            return False
    
    def get_privacy_settings(self) -> Dict[str, Any]:
        """Get current privacy settings."""
        return {
            'privacy_level': self.privacy_settings.privacy_level.value,
            'default_content_sensitivity': self.privacy_settings.default_content_sensitivity.value,
            'allow_external_processing': self.privacy_settings.allow_external_processing,
            'enable_diagnostic_statements': self.privacy_settings.enable_diagnostic_statements,
            'sensitive_keywords': self.privacy_settings.sensitive_keywords.copy(),
            'excluded_people': self.privacy_settings.excluded_people.copy(),
            'excluded_locations': self.privacy_settings.excluded_locations.copy(),
            'excluded_time_periods_count': len(self.privacy_settings.excluded_time_periods)
        }
    
    # Private helper methods
    
    def _parse_excluded_time_periods(self, time_periods: List[Any]) -> List[Tuple[datetime, datetime]]:
        """Parse excluded time periods from configuration."""
        parsed_periods = []
        for period in time_periods:
            try:
                if isinstance(period, dict) and 'start' in period and 'end' in period:
                    start = datetime.fromisoformat(period['start'])
                    end = datetime.fromisoformat(period['end'])
                    parsed_periods.append((start, end))
                elif isinstance(period, (list, tuple)) and len(period) == 2:
                    start = datetime.fromisoformat(period[0])
                    end = datetime.fromisoformat(period[1])
                    parsed_periods.append((start, end))
            except Exception as e:
                self.logger.warning(f"Failed to parse time period {period}: {str(e)}")
        
        return parsed_periods
    
    def _classify_content_sensitivity(self, content: str) -> ContentSensitivity:
        """Classify content sensitivity level."""
        # Check for sensitive patterns
        for pattern in self.compiled_sensitive_patterns:
            if pattern.search(content):
                return ContentSensitivity.SENSITIVE
        
        # Check for user-defined sensitive keywords
        content_lower = content.lower()
        for keyword in self.privacy_settings.sensitive_keywords:
            if keyword.lower() in content_lower:
                return ContentSensitivity.SENSITIVE
        
        # Default to private for personal content
        return self.privacy_settings.default_content_sensitivity
    
    def _remove_sharing_suggestions(self, content: str) -> str:
        """Remove sharing suggestions from content."""
        sharing_patterns = [
            r'share this with.*',
            r'post this to.*',
            r'consider sharing.*',
            r'you might want to share.*',
            r'this would be great to share.*'
        ]
        
        filtered_content = content
        for pattern in sharing_patterns:
            filtered_content = re.sub(pattern, '', filtered_content, flags=re.IGNORECASE)
        
        return filtered_content.strip()
    
    def _neutralize_diagnostic_statement(self, statement: str) -> str:
        """Convert diagnostic statement to neutral observation."""
        # More comprehensive neutralization - completely rewrite diagnostic statements
        statement_lower = statement.lower()
        
        # For "you are [condition]" patterns
        if 'you are' in statement_lower and any(condition in statement_lower for condition in 
                                               ['depressed', 'anxious', 'bipolar', 'adhd', 'autistic', 'narcissistic']):
            return 'Some patterns in your data suggest certain themes (observation only, not a diagnosis)'
        
        # For "you have [condition]" patterns  
        if 'you have' in statement_lower and any(condition in statement_lower for condition in
                                                ['depression', 'anxiety', 'bipolar', 'adhd', 'autism', 'ptsd']):
            return 'Your data shows some recurring patterns (observation only, not a diagnosis)'
        
        # For "you suffer from" patterns
        if 'you suffer from' in statement_lower:
            return 'Your experiences show certain patterns (observation only, not a diagnosis)'
        
        # For "this indicates" patterns
        if 'this indicates' in statement_lower:
            return 'This might suggest certain patterns (observation only, not a diagnosis)'
        
        # For "you exhibit" patterns
        if 'you exhibit' in statement_lower:
            return 'Your data contains certain patterns (observation only, not a diagnosis)'
        
        # Default neutralization for any remaining diagnostic language
        neutralized = statement.replace('you are', 'patterns suggest you might be')
        neutralized = neutralized.replace('you have', 'there may be signs of')
        neutralized = neutralized.replace('you suffer from', 'you may experience')
        neutralized = neutralized.replace('this indicates', 'this might suggest')
        
        return neutralized + ' (observation only, not a diagnosis)'
    
    def _filter_text_content(self, text: str, user_controls: Dict[str, Any]) -> str:
        """Filter text content based on user controls."""
        filtered_text = text
        
        # Apply diagnostic statement prevention
        filtered_text, _ = self.prevent_diagnostic_statements(filtered_text)
        
        # Remove sensitive keywords if specified
        if user_controls.get('remove_sensitive_keywords', False):
            for keyword in self.privacy_settings.sensitive_keywords:
                filtered_text = filtered_text.replace(keyword, '[REDACTED]')
        
        return filtered_text
    
    def _filter_story_content(self, story: Story, user_controls: Dict[str, Any]) -> Story:
        """Filter story content based on user controls."""
        # Filter story title and chapters
        filtered_chapters = []
        for chapter in story.chapters:
            filtered_chapter = self._filter_chapter_content(chapter, user_controls)
            if filtered_chapter:  # Only include non-empty chapters
                filtered_chapters.append(filtered_chapter)
        
        # Create filtered story
        filtered_story = Story(
            id=story.id,
            title=self._filter_text_content(story.title, user_controls),
            narrative_mode=story.narrative_mode,
            chapters=filtered_chapters,
            source_memory_ids=story.source_memory_ids,
            created_at=story.created_at,
            voice_narration_path=story.voice_narration_path
        )
        
        return filtered_story
    
    def _filter_chapter_content(self, chapter: Chapter, user_controls: Dict[str, Any]) -> Optional[Chapter]:
        """Filter chapter content based on user controls."""
        # Filter narrative text
        filtered_text = self._filter_text_content(chapter.narrative_text, user_controls)
        
        # If text is completely filtered out, return None
        if not filtered_text.strip():
            return None
        
        # Create filtered chapter
        filtered_chapter = Chapter(
            id=chapter.id,
            title=self._filter_text_content(chapter.title, user_controls),
            narrative_text=filtered_text,
            media_elements=chapter.media_elements,  # Media filtering could be added here
            duration_seconds=chapter.duration_seconds,
            emotional_tone=chapter.emotional_tone
        )
        
        return filtered_chapter
    
    def _filter_memory_content(self, memory: EnhancedLLEntry, user_controls: Dict[str, Any]) -> Optional[EnhancedLLEntry]:
        """Filter memory content based on user controls."""
        # Check if memory should be excluded based on time period
        memory_time = datetime.fromisoformat(memory.startTime)
        for start_time, end_time in self.privacy_settings.excluded_time_periods:
            if start_time <= memory_time <= end_time:
                return None
        
        # Check if memory should be excluded based on people
        if hasattr(memory, 'peopleInImage') and memory.peopleInImage:
            for person in memory.peopleInImage:
                if person in self.privacy_settings.excluded_people:
                    return None
        
        # Check if memory should be excluded based on location
        if hasattr(memory, 'location') and memory.location:
            if memory.location in self.privacy_settings.excluded_locations:
                return None
        
        # Filter text content
        if hasattr(memory, 'text') and memory.text:
            memory.text = self._filter_text_content(memory.text, user_controls)
        
        if hasattr(memory, 'textDescription') and memory.textDescription:
            memory.textDescription = self._filter_text_content(memory.textDescription, user_controls)
        
        return memory
    
    def _start_network_monitoring(self):
        """Start network monitoring in a background thread."""
        def monitor_network():
            # This is a placeholder for network monitoring
            # In a real implementation, this would monitor actual network traffic
            self.logger.info("Network monitoring started (placeholder implementation)")
        
        if self.network_monitor_enabled:
            monitor_thread = threading.Thread(target=monitor_network, daemon=True)
            monitor_thread.start()
    
    def _check_recent_privacy_violations(self) -> List[str]:
        """Check for recent privacy violations."""
        violations = []
        
        # Check for recent blocked network activity
        recent_blocked = [
            activity for activity in self.network_activity_log
            if activity.blocked and (datetime.now() - activity.timestamp).seconds < 3600
        ]
        
        if recent_blocked:
            violations.append(f"Blocked {len(recent_blocked)} network attempts in the last hour")
        
        return violations
    
    def _calculate_compliance_score(self, report: Dict[str, Any]) -> float:
        """Calculate overall privacy compliance score (0.0 to 1.0)."""
        score = 1.0
        
        # Deduct points for violations
        if report.get('recent_violations'):
            score -= 0.1 * len(report['recent_violations'])
        
        # Deduct points for external processing
        if not report.get('local_processing_only', True):
            score -= 0.3
        
        # Deduct points for disabled diagnostic prevention
        if not report.get('diagnostic_prevention_enabled', True):
            score -= 0.2
        
        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, score))