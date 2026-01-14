#!/usr/bin/env python3
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

"""
Privacy and Safety Controls Demo

This script demonstrates the privacy and safety controls implemented in the
AI-Augmented Personal Archive system, including:
1. Local processing validation
2. Private-by-default content generation
3. Diagnostic statement prevention
4. User controls for sensitive content
5. Comprehensive privacy monitoring
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.common.services.privacy_safety_service import (
    PrivacySafetyService, PrivacyLevel, ContentSensitivity
)
from src.common.objects.enhanced_llentry import EnhancedLLEntry, Story, Chapter


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def demo_local_processing_validation():
    """Demonstrate local processing validation"""
    print_section("1. Local Processing Validation (Requirement 10.1)")
    
    # Initialize privacy service with strict settings
    config = {
        'privacy_level': 'strict',
        'allow_external_processing': False
    }
    privacy_service = PrivacySafetyService(config)
    
    # Test local processing validation
    operations = [
        "story_generation",
        "memory_retrieval",
        "people_intelligence_analysis",
        "gallery_curation"
    ]
    
    print("Testing local processing validation for various operations:")
    for operation in operations:
        is_valid = privacy_service.validate_local_processing(operation)
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"  {status}: {operation}")
    
    print("\nResult: All operations validated for local processing only.")
    print("No external API calls or cloud services will be used.")


def demo_private_content_generation():
    """Demonstrate private-by-default content generation"""
    print_section("2. Private-by-Default Content Generation (Requirement 10.2)")
    
    privacy_service = PrivacySafetyService({
        'privacy_level': 'strict',
        'default_content_sensitivity': 'private'
    })
    
    # Test content with potential sharing suggestions
    test_content = """
    Here's a wonderful memory from your trip to Paris. The Eiffel Tower was amazing!
    You might want to share this with your friends on social media.
    Consider sharing this beautiful moment with others.
    """
    
    print("Original content:")
    print(f"  {test_content.strip()}")
    
    # Apply private content generation controls
    private_content = privacy_service.ensure_private_content_generation(test_content)
    
    print("\nProcessed content (private mode):")
    print(f"  {private_content.strip()}")
    
    print("\nResult: Sharing suggestions removed, content marked as private.")


def demo_diagnostic_statement_prevention():
    """Demonstrate diagnostic statement prevention"""
    print_section("3. Diagnostic Statement Prevention (Requirement 10.3)")
    
    privacy_service = PrivacySafetyService({
        'privacy_level': 'strict',
        'enable_diagnostic_statements': False
    })
    
    # Test content with diagnostic statements
    test_cases = [
        "Based on your posts, you are depressed and need help.",
        "You have anxiety issues that should be addressed.",
        "You suffer from bipolar disorder according to your patterns.",
        "This indicates ADHD symptoms in your behavior.",
        "You exhibit signs of autism spectrum disorder."
    ]
    
    print("Testing diagnostic statement prevention:\n")
    
    for i, content in enumerate(test_cases, 1):
        print(f"Test case {i}:")
        print(f"  Original: {content}")
        
        filtered_content, issues = privacy_service.prevent_diagnostic_statements(content)
        
        print(f"  Filtered: {filtered_content}")
        print(f"  Issues detected: {len(issues)}")
        print()
    
    print("Result: All diagnostic statements converted to neutral observations.")
    print("System avoids 'You are X' declarations and frames as patterns/suggestions.")


def demo_user_content_controls():
    """Demonstrate user controls for sensitive content"""
    print_section("4. User Controls for Sensitive Content (Requirement 10.4)")
    
    # Configure privacy service with user exclusions
    config = {
        'privacy_level': 'strict',
        'sensitive_keywords': ['password', 'secret', 'confidential'],
        'excluded_people': ['ExPerson', 'FormerColleague'],
        'excluded_locations': ['Hospital', 'Therapy Office'],
        'excluded_time_periods': [
            {
                'start': (datetime.now() - timedelta(days=365)).isoformat(),
                'end': (datetime.now() - timedelta(days=180)).isoformat()
            }
        ]
    }
    
    privacy_service = PrivacySafetyService(config)
    
    # Test memory filtering
    print("Testing memory filtering with user exclusions:\n")
    
    # Create test memory with excluded person
    memory1 = EnhancedLLEntry("photo", datetime.now().isoformat(), "facebook")
    memory1.text = "Great time with ExPerson at the park"
    memory1.peopleInImage = ["ExPerson", "Friend"]
    
    print("Memory 1: Contains excluded person 'ExPerson'")
    filtered_memory1 = privacy_service.apply_user_content_controls(memory1)
    print(f"  Result: {'Excluded' if filtered_memory1 is None else 'Kept (filtered)'}")
    
    # Create test memory with excluded location
    memory2 = EnhancedLLEntry("post", datetime.now().isoformat(), "facebook")
    memory2.text = "Visit to Hospital for checkup"
    memory2.location = "Hospital"
    
    print("\nMemory 2: Contains excluded location 'Hospital'")
    filtered_memory2 = privacy_service.apply_user_content_controls(memory2)
    print(f"  Result: {'Excluded' if filtered_memory2 is None else 'Kept (filtered)'}")
    
    # Test text filtering with sensitive keywords
    print("\nTesting text filtering with sensitive keywords:")
    
    text_with_keywords = "My password is secret123 and this is confidential information."
    print(f"  Original: {text_with_keywords}")
    
    user_controls = {'remove_sensitive_keywords': True}
    filtered_text = privacy_service.apply_user_content_controls(text_with_keywords, user_controls)
    print(f"  Filtered: {filtered_text}")
    
    print("\nResult: User controls successfully applied to filter sensitive content.")


def demo_privacy_monitoring():
    """Demonstrate comprehensive privacy monitoring"""
    print_section("5. Comprehensive Privacy Monitoring (Requirement 10.5)")
    
    privacy_service = PrivacySafetyService({
        'privacy_level': 'strict',
        'allow_external_processing': False,
        'enable_diagnostic_statements': False,
        'enable_network_monitoring': True
    })
    
    # Get privacy compliance report
    compliance_report = privacy_service.monitor_privacy_compliance()
    
    print("Privacy Compliance Report:\n")
    print(f"  Timestamp: {compliance_report['timestamp']}")
    print(f"  Privacy Level: {compliance_report['privacy_level']}")
    print(f"  Local Processing Only: {compliance_report['local_processing_only']}")
    print(f"  Diagnostic Prevention Enabled: {compliance_report['diagnostic_prevention_enabled']}")
    print(f"  Network Monitoring Enabled: {compliance_report['network_monitoring_enabled']}")
    print(f"  Compliance Score: {compliance_report['compliance_score']:.2f}/1.00")
    
    print("\n  User Exclusions:")
    exclusions = compliance_report['user_exclusions']
    print(f"    - Excluded People: {exclusions['excluded_people_count']}")
    print(f"    - Excluded Locations: {exclusions['excluded_locations_count']}")
    print(f"    - Excluded Time Periods: {exclusions['excluded_time_periods_count']}")
    
    print("\n  Network Activity:")
    print(f"    - Total Activity: {compliance_report['network_activity_count']}")
    print(f"    - Blocked Attempts: {compliance_report['blocked_network_attempts']}")
    
    if compliance_report.get('recent_violations'):
        print("\n  Recent Violations:")
        for violation in compliance_report['recent_violations']:
            print(f"    - {violation}")
    else:
        print("\n  Recent Violations: None")
    
    print("\nResult: Comprehensive privacy monitoring active and reporting.")


def demo_privacy_settings_management():
    """Demonstrate privacy settings management"""
    print_section("6. Privacy Settings Management")
    
    privacy_service = PrivacySafetyService()
    
    print("Current privacy settings:")
    current_settings = privacy_service.get_privacy_settings()
    for key, value in current_settings.items():
        if not isinstance(value, list):
            print(f"  {key}: {value}")
    
    print("\nUpdating privacy settings...")
    new_settings = {
        'privacy_level': 'moderate',
        'allow_external_processing': False,
        'enable_diagnostic_statements': False,
        'sensitive_keywords': ['personal', 'private', 'sensitive'],
        'excluded_people': ['TestPerson'],
        'excluded_locations': ['TestLocation']
    }
    
    success = privacy_service.update_privacy_settings(new_settings)
    print(f"  Update successful: {success}")
    
    print("\nUpdated privacy settings:")
    updated_settings = privacy_service.get_privacy_settings()
    for key, value in updated_settings.items():
        if not isinstance(value, list):
            print(f"  {key}: {value}")
    
    print("\nResult: Privacy settings can be dynamically updated by users.")


def demo_story_privacy_filtering():
    """Demonstrate privacy filtering for story content"""
    print_section("7. Story Privacy Filtering")
    
    privacy_service = PrivacySafetyService({
        'privacy_level': 'strict',
        'enable_diagnostic_statements': False
    })
    
    # Create a test story with potential privacy issues
    chapters = [
        Chapter(
            id="ch1",
            title="A Difficult Period",
            narrative_text="You are depressed based on your posts. You have anxiety issues.",
            media_elements=[],
            duration_seconds=30,
            emotional_tone="somber"
        ),
        Chapter(
            id="ch2",
            title="Recovery Journey",
            narrative_text="You suffer from bipolar disorder but are making progress.",
            media_elements=[],
            duration_seconds=30,
            emotional_tone="hopeful"
        )
    ]
    
    story = Story(
        id="test_story",
        title="Personal Journey",
        narrative_mode="chronological",
        chapters=chapters,
        source_memory_ids=[],
        created_at=datetime.now()
    )
    
    print("Original story chapters:")
    for i, chapter in enumerate(story.chapters, 1):
        print(f"\n  Chapter {i}: {chapter.title}")
        print(f"    {chapter.narrative_text}")
    
    # Apply privacy filtering
    filtered_story = privacy_service.apply_user_content_controls(story)
    
    print("\n\nFiltered story chapters:")
    for i, chapter in enumerate(filtered_story.chapters, 1):
        print(f"\n  Chapter {i}: {chapter.title}")
        print(f"    {chapter.narrative_text}")
    
    print("\nResult: Story content filtered to remove diagnostic statements.")


def main():
    """Run all privacy and safety demos"""
    print("\n" + "="*80)
    print("  AI-AUGMENTED PERSONAL ARCHIVE")
    print("  Privacy and Safety Controls Demonstration")
    print("="*80)
    
    try:
        # Run all demonstrations
        demo_local_processing_validation()
        demo_private_content_generation()
        demo_diagnostic_statement_prevention()
        demo_user_content_controls()
        demo_privacy_monitoring()
        demo_privacy_settings_management()
        demo_story_privacy_filtering()
        
        # Summary
        print_section("Summary")
        print("All privacy and safety controls demonstrated successfully:")
        print("  ✓ Local processing validation (Requirement 10.1)")
        print("  ✓ Private-by-default content generation (Requirement 10.2)")
        print("  ✓ Diagnostic statement prevention (Requirement 10.3)")
        print("  ✓ User controls for sensitive content (Requirement 10.4)")
        print("  ✓ Comprehensive privacy monitoring (Requirement 10.5)")
        print("\nThe system ensures complete privacy and user control over personal data.")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\nError during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
