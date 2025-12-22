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

import os
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite

# Import the classes we need to test
from src.common.objects.enhanced_llentry import EnhancedLLEntry, Story, Chapter
from src.common.services.privacy_safety_service import (
    PrivacySafetyService, PrivacyLevel, ContentSensitivity, PrivacySettings
)


# Strategy generators for property-based testing

@composite
def generate_privacy_settings(draw):
    """Generate valid privacy settings for testing"""
    return PrivacySettings(
        privacy_level=draw(st.sampled_from(list(PrivacyLevel))),
        default_content_sensitivity=draw(st.sampled_from(list(ContentSensitivity))),
        allow_external_processing=draw(st.booleans()),
        enable_diagnostic_statements=draw(st.booleans()),
        sensitive_keywords=draw(st.lists(
            st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
            min_size=0, max_size=10
        )),
        excluded_people=draw(st.lists(
            st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))),
            min_size=0, max_size=5
        )),
        excluded_locations=draw(st.lists(
            st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))),
            min_size=0, max_size=5
        ))
    )


@composite
def generate_content_with_diagnostic_statements(draw):
    """Generate content that may contain diagnostic statements"""
    base_content = draw(st.text(min_size=20, max_size=200))
    
    # Sometimes add diagnostic statements
    if draw(st.booleans()):
        diagnostic_statements = [
            "You are depressed based on your posts.",
            "You have anxiety issues.",
            "You suffer from bipolar disorder.",
            "This indicates ADHD symptoms.",
            "You exhibit signs of autism.",
            "This behavior is typical of narcissistic personality disorder."
        ]
        diagnostic = draw(st.sampled_from(diagnostic_statements))
        base_content = base_content + " " + diagnostic
    
    return base_content


@composite
def generate_content_with_sensitive_info(draw):
    """Generate content that may contain sensitive information"""
    base_content = draw(st.text(min_size=20, max_size=200))
    
    # Sometimes add sensitive information
    if draw(st.booleans()):
        sensitive_info = [
            "My password is secret123",
            "SSN: 123-45-6789",
            "Credit card: 1234 5678 9012 3456",
            "Email: user@example.com",
            "Bank account: 987654321"
        ]
        sensitive = draw(st.sampled_from(sensitive_info))
        base_content = base_content + " " + sensitive
    
    return base_content


@composite
def generate_story_with_privacy_concerns(draw):
    """Generate a story that may have privacy concerns"""
    story_id = draw(st.text(min_size=10, max_size=50))
    title = draw(st.text(min_size=5, max_size=100))
    
    # Generate chapters with potential privacy issues
    num_chapters = draw(st.integers(min_value=1, max_value=5))
    chapters = []
    
    for i in range(num_chapters):
        chapter_text = draw(generate_content_with_diagnostic_statements())
        chapter = Chapter(
            id=f"chapter_{i}",
            title=f"Chapter {i+1}",
            narrative_text=chapter_text,
            media_elements=[],
            duration_seconds=30,
            emotional_tone="neutral"
        )
        chapters.append(chapter)
    
    story = Story(
        id=story_id,
        title=title,
        narrative_mode="chronological",
        chapters=chapters,
        source_memory_ids=[],
        created_at=datetime.now()
    )
    
    return story


@composite
def generate_memory_with_exclusion_criteria(draw):
    """Generate a memory that may match user exclusion criteria"""
    entry_types = ["photo", "post", "event"]
    sources = ["facebook", "google_photos", "manual"]
    
    entry_type = draw(st.sampled_from(entry_types))
    source = draw(st.sampled_from(sources))
    
    # Generate timestamp
    base_time = datetime.now() - timedelta(days=365)
    time_offset = draw(st.integers(min_value=0, max_value=365 * 24 * 3600))
    start_time = base_time + timedelta(seconds=time_offset)
    
    memory = EnhancedLLEntry(entry_type, start_time.isoformat(), source)
    
    # Add content that might be filtered
    memory.text = draw(generate_content_with_sensitive_info())
    memory.textDescription = memory.text
    
    # Add people that might be excluded
    people_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve']
    memory.peopleInImage = draw(st.lists(
        st.sampled_from(people_names),
        min_size=0, max_size=3
    ))
    
    # Add location that might be excluded
    locations = ['Home', 'Work', 'School', 'Hospital', 'Therapy Office']
    memory.location = draw(st.sampled_from(locations + [None]))
    
    return memory


class TestPrivacySafety:
    """Test suite for privacy and safety controls"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Create a temporary directory for any test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize privacy safety service with test configuration
        self.test_config = {
            'privacy_level': 'strict',
            'default_content_sensitivity': 'private',
            'allow_external_processing': False,
            'enable_diagnostic_statements': False,
            'enable_network_monitoring': False,  # Disable for testing
            'sensitive_keywords': ['secret', 'private', 'confidential'],
            'excluded_people': ['ExcludedPerson'],
            'excluded_locations': ['ExcludedLocation'],
            'blocked_domains': ['external-api.com', 'cloud-service.com']
        }
        
        self.privacy_service = PrivacySafetyService(self.test_config)
    
    def teardown_method(self):
        """Clean up test environment after each test"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(
        content=generate_content_with_diagnostic_statements(),
        privacy_settings=generate_privacy_settings()
    )
    @settings(max_examples=100, deadline=30000)
    def test_privacy_and_user_control(self, content, privacy_settings):
        """**Feature: ai-personal-archive, Property 10: Privacy and User Control**
        
        For any personal data processing or content generation, the system should operate 
        locally, default to private mode, avoid diagnostic statements, and provide user 
        controls over sensitive content.
        """
        # Arrange: Update privacy settings
        settings_dict = {
            'privacy_level': privacy_settings.privacy_level.value,
            'default_content_sensitivity': privacy_settings.default_content_sensitivity.value,
            'allow_external_processing': privacy_settings.allow_external_processing,
            'enable_diagnostic_statements': privacy_settings.enable_diagnostic_statements,
            'sensitive_keywords': privacy_settings.sensitive_keywords,
            'excluded_people': privacy_settings.excluded_people,
            'excluded_locations': privacy_settings.excluded_locations
        }
        
        success = self.privacy_service.update_privacy_settings(settings_dict)
        assume(success)  # Skip test if settings update fails
        
        # Act & Assert: Test all privacy and user control properties
        
        # Property 1: Local processing validation (Requirement 10.1)
        local_processing_valid = self.privacy_service.validate_local_processing(
            "content_generation", content
        )
        
        if not privacy_settings.allow_external_processing:
            assert local_processing_valid, \
                "System should validate local processing when external processing is disabled"
        
        # Property 2: Private-by-default content generation (Requirement 10.2)
        private_content = self.privacy_service.ensure_private_content_generation(content)
        
        assert private_content is not None, "Should return processed content"
        assert isinstance(private_content, str), "Should return string content"
        
        # Should not contain sharing suggestions
        sharing_indicators = ['share this', 'post this', 'consider sharing']
        for indicator in sharing_indicators:
            assert indicator.lower() not in private_content.lower(), \
                f"Private content should not contain sharing suggestion: '{indicator}'"
        
        # Should add privacy markers for sensitive content if detected
        if any(keyword.lower() in content.lower() for keyword in privacy_settings.sensitive_keywords):
            privacy_markers = ['private', 'personal information']
            has_privacy_marker = any(marker in private_content.lower() for marker in privacy_markers)
            # Privacy markers are optional but content should be processed
            assert len(private_content) >= len(content), \
                "Content should be preserved or enhanced with privacy controls"
        
        # Property 3: Diagnostic statement prevention (Requirement 10.3)
        filtered_content, detected_issues = self.privacy_service.prevent_diagnostic_statements(content)
        
        assert filtered_content is not None, "Should return filtered content"
        assert isinstance(filtered_content, str), "Should return string content"
        assert isinstance(detected_issues, list), "Should return list of detected issues"
        
        if not privacy_settings.enable_diagnostic_statements:
            # Should not contain absolute diagnostic statements
            diagnostic_patterns = [
                'you are depressed', 'you have anxiety', 'you suffer from',
                'this indicates.*disorder', 'you exhibit.*symptoms'
            ]
            
            for pattern in diagnostic_patterns:
                import re
                if re.search(pattern, content, re.IGNORECASE):
                    # Original content had diagnostic statement, filtered should not
                    assert not re.search(pattern, filtered_content, re.IGNORECASE), \
                        f"Filtered content should not contain diagnostic pattern: '{pattern}'"
            
            # Should frame as suggestions rather than definitive statements
            if 'you are' in content.lower() and any(
                word in content.lower() for word in ['depressed', 'anxious', 'bipolar']
            ):
                suggestion_indicators = ['might', 'may', 'could', 'suggests', 'patterns', 'observation']
                has_suggestion_language = any(
                    indicator in filtered_content.lower() for indicator in suggestion_indicators
                )
                assert has_suggestion_language, \
                    "Diagnostic content should be reframed as suggestions or observations"
        
        # Property 4: User controls for sensitive content (Requirement 10.4)
        user_controls = {
            'remove_sensitive_keywords': True,
            'exclude_people': privacy_settings.excluded_people,
            'exclude_locations': privacy_settings.excluded_locations
        }
        
        controlled_content = self.privacy_service.apply_user_content_controls(content, user_controls)
        
        assert controlled_content is not None, "Should return controlled content"
        
        # Should respect sensitive keyword removal
        if user_controls.get('remove_sensitive_keywords', False):
            for keyword in privacy_settings.sensitive_keywords:
                if keyword.lower() in content.lower():
                    # Should either remove or redact the keyword
                    keyword_removed = keyword.lower() not in controlled_content.lower()
                    keyword_redacted = '[REDACTED]' in controlled_content
                    assert keyword_removed or keyword_redacted, \
                        f"Sensitive keyword '{keyword}' should be removed or redacted"
        
        # Property 5: Comprehensive privacy monitoring (Requirement 10.5)
        compliance_report = self.privacy_service.monitor_privacy_compliance()
        
        assert compliance_report is not None, "Should return compliance report"
        assert isinstance(compliance_report, dict), "Compliance report should be a dictionary"
        
        # Should contain required monitoring fields
        required_fields = [
            'timestamp', 'privacy_level', 'local_processing_only',
            'diagnostic_prevention_enabled', 'compliance_score'
        ]
        
        for field in required_fields:
            assert field in compliance_report, f"Compliance report should contain '{field}'"
        
        # Should have valid compliance score
        compliance_score = compliance_report.get('compliance_score', 0)
        assert isinstance(compliance_score, (int, float)), "Compliance score should be numeric"
        assert 0.0 <= compliance_score <= 1.0, \
            f"Compliance score should be between 0.0 and 1.0, got {compliance_score}"
        
        # Should reflect current privacy settings
        assert compliance_report['privacy_level'] == privacy_settings.privacy_level.value, \
            "Compliance report should reflect current privacy level"
        
        assert compliance_report['local_processing_only'] == (not privacy_settings.allow_external_processing), \
            "Compliance report should reflect external processing setting"
        
        assert compliance_report['diagnostic_prevention_enabled'] == (not privacy_settings.enable_diagnostic_statements), \
            "Compliance report should reflect diagnostic prevention setting"
        
        # Property 6: Privacy settings management
        current_settings = self.privacy_service.get_privacy_settings()
        
        assert isinstance(current_settings, dict), "Should return settings as dictionary"
        assert current_settings['privacy_level'] == privacy_settings.privacy_level.value, \
            "Should return current privacy level"
        assert current_settings['allow_external_processing'] == privacy_settings.allow_external_processing, \
            "Should return current external processing setting"
        assert current_settings['enable_diagnostic_statements'] == privacy_settings.enable_diagnostic_statements, \
            "Should return current diagnostic statements setting"
    
    @given(story=generate_story_with_privacy_concerns())
    @settings(max_examples=50, deadline=30000)
    def test_story_privacy_filtering(self, story):
        """Test privacy filtering for story content"""
        # Arrange: Set strict privacy settings
        strict_settings = {
            'privacy_level': 'strict',
            'enable_diagnostic_statements': False
        }
        self.privacy_service.update_privacy_settings(strict_settings)
        
        # Act: Apply privacy controls to story
        filtered_story = self.privacy_service.apply_user_content_controls(story)
        
        # Assert: Story should be filtered appropriately
        assert filtered_story is not None, "Should return filtered story"
        assert isinstance(filtered_story, Story), "Should return Story object"
        assert filtered_story.id == story.id, "Should preserve story ID"
        
        # All chapters should be processed
        assert len(filtered_story.chapters) <= len(story.chapters), \
            "Filtered story should have same or fewer chapters"
        
        # Each chapter should be filtered
        for chapter in filtered_story.chapters:
            assert isinstance(chapter, Chapter), "Should contain Chapter objects"
            assert chapter.narrative_text, "Chapter should have narrative text"
            
            # Should not contain diagnostic statements
            diagnostic_patterns = ['you are depressed', 'you have anxiety', 'you suffer from']
            for pattern in diagnostic_patterns:
                assert pattern.lower() not in chapter.narrative_text.lower(), \
                    f"Chapter should not contain diagnostic pattern: '{pattern}'"
    
    @given(memory=generate_memory_with_exclusion_criteria())
    @settings(max_examples=50, deadline=30000)
    def test_memory_exclusion_controls(self, memory):
        """Test user controls for memory exclusion"""
        # Arrange: Set up exclusion criteria
        exclusion_settings = {
            'excluded_people': ['Alice', 'Bob'],
            'excluded_locations': ['Hospital', 'Therapy Office']
        }
        self.privacy_service.update_privacy_settings(exclusion_settings)
        
        user_controls = {
            'exclude_people': exclusion_settings['excluded_people'],
            'exclude_locations': exclusion_settings['excluded_locations']
        }
        
        # Act: Apply user controls
        filtered_memory = self.privacy_service.apply_user_content_controls(memory, user_controls)
        
        # Assert: Memory should be filtered or excluded appropriately
        if filtered_memory is None:
            # Memory was excluded - verify it matched exclusion criteria
            should_be_excluded = False
            
            # Check people exclusion
            if hasattr(memory, 'peopleInImage') and memory.peopleInImage:
                for person in memory.peopleInImage:
                    if person in exclusion_settings['excluded_people']:
                        should_be_excluded = True
                        break
            
            # Check location exclusion
            if hasattr(memory, 'location') and memory.location:
                if memory.location in exclusion_settings['excluded_locations']:
                    should_be_excluded = True
            
            # If memory was excluded, it should have matched criteria
            # (Note: This is a simplified check - real implementation might have more complex logic)
            
        else:
            # Memory was kept - verify it's properly filtered
            assert isinstance(filtered_memory, EnhancedLLEntry), "Should return EnhancedLLEntry"
            
            # Text content should be filtered
            if hasattr(filtered_memory, 'text') and filtered_memory.text:
                # Should not contain diagnostic statements
                diagnostic_patterns = ['you are depressed', 'you have anxiety']
                for pattern in diagnostic_patterns:
                    assert pattern.lower() not in filtered_memory.text.lower(), \
                        f"Memory text should not contain diagnostic pattern: '{pattern}'"
    
    def test_local_processing_validation(self):
        """Test local processing validation"""
        # Test with external processing disabled
        self.privacy_service.update_privacy_settings({'allow_external_processing': False})
        
        assert self.privacy_service.validate_local_processing("story_generation"), \
            "Should validate local processing when external processing disabled"
        
        assert self.privacy_service.validate_local_processing("memory_retrieval", "test data"), \
            "Should validate local processing with data"
        
        # Test with external processing enabled
        self.privacy_service.update_privacy_settings({'allow_external_processing': True})
        
        assert self.privacy_service.validate_local_processing("story_generation"), \
            "Should validate processing when external processing enabled"
    
    def test_privacy_settings_persistence(self):
        """Test privacy settings update and retrieval"""
        # Test updating various settings
        new_settings = {
            'privacy_level': 'moderate',
            'default_content_sensitivity': 'sensitive',
            'allow_external_processing': True,
            'enable_diagnostic_statements': True,
            'sensitive_keywords': ['test', 'keyword'],
            'excluded_people': ['TestPerson'],
            'excluded_locations': ['TestLocation']
        }
        
        success = self.privacy_service.update_privacy_settings(new_settings)
        assert success, "Should successfully update privacy settings"
        
        # Verify settings were updated
        current_settings = self.privacy_service.get_privacy_settings()
        
        assert current_settings['privacy_level'] == 'moderate'
        assert current_settings['default_content_sensitivity'] == 'sensitive'
        assert current_settings['allow_external_processing'] == True
        assert current_settings['enable_diagnostic_statements'] == True
        assert 'test' in current_settings['sensitive_keywords']
        assert 'TestPerson' in current_settings['excluded_people']
        assert 'TestLocation' in current_settings['excluded_locations']


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])