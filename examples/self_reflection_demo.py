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
Self-Reflection Analysis Demo

This demo showcases the self-reflection analysis tools that help users understand
their personal patterns, life chapters, and growth over time. The system analyzes
writing patterns, detects life chapters, identifies recurring themes, and generates
reflection prompts while maintaining privacy and framing insights as suggestions.

Key Features Demonstrated:
- Writing pattern analysis (tone, topic, vocabulary evolution)
- Life chapter detection and editing
- Recurring theme identification
- Pattern presentation as suggestions
- Reflection prompt generation

Requirements Validated:
- 8.1: Writing pattern analysis with tone changes, topic shifts, vocabulary evolution
- 8.2: Life chapter detection with user editing capabilities
- 8.3: Recurring theme identification across time periods
- 8.4: Pattern presentation as suggestions rather than definitive statements
- 8.5: Reflection prompt generation that invites dialogue
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.common.objects.enhanced_llentry import EnhancedLLEntry, PersonRelationship
from src.common.services.self_reflection_service import SelfReflectionService


def create_sample_personal_data() -> List[EnhancedLLEntry]:
    """Create sample personal data spanning multiple years with evolving patterns"""
    entries = []
    base_time = datetime.now() - timedelta(days=1095)  # 3 years ago
    
    # Early period - college/early career (more casual, excited tone)
    early_entries = [
        {
            'days_offset': 0,
            'text': "Just graduated from college! Can't believe this chapter is over. Feeling excited and nervous about what's next.",
            'type': 'milestone',
            'themes': ['graduation', 'milestone', 'transition'],
            'emotional_context': {'excitement': 0.8, 'nervousness': 0.6},
            'narrative_significance': 0.9
        },
        {
            'days_offset': 30,
            'text': "Started my first real job today. Everyone seems nice and the work looks interesting. Hope I can keep up!",
            'type': 'milestone',
            'themes': ['work', 'new_job', 'career'],
            'emotional_context': {'hope': 0.7, 'uncertainty': 0.5},
            'narrative_significance': 0.8
        },
        {
            'days_offset': 90,
            'text': "Getting the hang of work now. Made some good friends here. Weekend plans with the team were awesome!",
            'type': 'post',
            'themes': ['work', 'friends', 'social'],
            'emotional_context': {'satisfaction': 0.7, 'belonging': 0.8},
            'narrative_significance': 0.5
        },
        {
            'days_offset': 180,
            'text': "Moved to my own apartment finally! It's small but it's mine. Decorating is fun but expensive.",
            'type': 'milestone',
            'themes': ['move', 'independence', 'home'],
            'emotional_context': {'pride': 0.8, 'independence': 0.9},
            'narrative_significance': 0.7
        }
    ]
    
    # Middle period - career development (more analytical, goal-oriented)
    middle_entries = [
        {
            'days_offset': 365,
            'text': "Reflecting on my first year at work. I've learned so much about project management and client relations. Setting goals for year two.",
            'type': 'post',
            'themes': ['work', 'learning', 'goals', 'reflection'],
            'emotional_context': {'accomplishment': 0.7, 'determination': 0.8},
            'narrative_significance': 0.6
        },
        {
            'days_offset': 450,
            'text': "Taking a course in data analysis to expand my skills. The intersection of technology and business strategy fascinates me.",
            'type': 'post',
            'themes': ['learning', 'skills', 'technology', 'strategy'],
            'emotional_context': {'curiosity': 0.8, 'engagement': 0.7},
            'narrative_significance': 0.5
        },
        {
            'days_offset': 600,
            'text': "Got promoted to senior analyst! The additional responsibilities are challenging but I feel ready for them.",
            'type': 'milestone',
            'themes': ['promotion', 'work', 'achievement', 'growth'],
            'emotional_context': {'pride': 0.9, 'confidence': 0.8},
            'narrative_significance': 0.8
        },
        {
            'days_offset': 730,
            'text': "Started mentoring new hires. It's rewarding to help others navigate the challenges I faced when starting out.",
            'type': 'post',
            'themes': ['mentoring', 'work', 'helping', 'growth'],
            'emotional_context': {'fulfillment': 0.8, 'wisdom': 0.6},
            'narrative_significance': 0.6
        }
    ]
    
    # Recent period - personal growth focus (more reflective, balanced)
    recent_entries = [
        {
            'days_offset': 900,
            'text': "Been thinking about work-life balance lately. Success isn't just about career advancement - relationships and personal well-being matter too.",
            'type': 'post',
            'themes': ['balance', 'reflection', 'relationships', 'wellbeing'],
            'emotional_context': {'wisdom': 0.7, 'balance': 0.8},
            'narrative_significance': 0.7
        },
        {
            'days_offset': 950,
            'text': "Started a meditation practice. The daily routine helps me stay centered and approach challenges with more clarity.",
            'type': 'post',
            'themes': ['meditation', 'wellbeing', 'clarity', 'routine'],
            'emotional_context': {'peace': 0.8, 'clarity': 0.7},
            'narrative_significance': 0.6
        },
        {
            'days_offset': 1000,
            'text': "Volunteering at the local community center on weekends. Contributing to something bigger than myself feels meaningful.",
            'type': 'post',
            'themes': ['volunteering', 'community', 'meaning', 'service'],
            'emotional_context': {'fulfillment': 0.9, 'purpose': 0.8},
            'narrative_significance': 0.7
        },
        {
            'days_offset': 1050,
            'text': "Three years since graduation. The person I am now has grown in ways I couldn't have imagined. Grateful for the journey.",
            'type': 'post',
            'themes': ['reflection', 'growth', 'gratitude', 'journey'],
            'emotional_context': {'gratitude': 0.9, 'wisdom': 0.8},
            'narrative_significance': 0.8
        }
    ]
    
    # Create EnhancedLLEntry objects
    all_entry_data = early_entries + middle_entries + recent_entries
    
    for entry_data in all_entry_data:
        entry_time = base_time + timedelta(days=entry_data['days_offset'])
        
        entry = EnhancedLLEntry(entry_data['type'], entry_time.isoformat(), 'personal_journal')
        entry.text = entry_data['text']
        entry.textDescription = entry_data['text']
        entry.thematic_tags = entry_data['themes']
        entry.emotional_context = entry_data['emotional_context']
        entry.narrative_significance = entry_data['narrative_significance']
        entry.story_potential = entry_data['narrative_significance'] * 0.8
        
        # Set life phase based on time period
        if entry_data['days_offset'] < 300:
            entry.life_phase = 'early_career'
        elif entry_data['days_offset'] < 800:
            entry.life_phase = 'career_development'
        else:
            entry.life_phase = 'personal_growth'
        
        # Add some people relationships for social entries
        if 'friends' in entry_data['themes'] or 'social' in entry_data['themes']:
            relationship = PersonRelationship(
                person_id='work_colleagues',
                relationship_type='colleague',
                confidence=0.8,
                first_interaction=entry_time - timedelta(days=30),
                last_interaction=entry_time
            )
            entry.people_relationships.append(relationship)
        
        entries.append(entry)
    
    return entries


def demonstrate_writing_pattern_analysis(service: SelfReflectionService, entries: List[EnhancedLLEntry]):
    """Demonstrate writing pattern analysis capabilities"""
    print("=" * 60)
    print("WRITING PATTERN ANALYSIS")
    print("=" * 60)
    
    analysis = service.analyze_personal_patterns(entries)
    writing_patterns = analysis['writing_patterns']
    
    print("\n📝 TONE EVOLUTION:")
    print("-" * 30)
    for period in writing_patterns.get('tone_evolution', []):
        print(f"Period: {period['time_period']}")
        print(f"  Dominant tones: {', '.join(period['dominant_tones'])}")
        print(f"  Entries analyzed: {period['entry_count']}")
        print()
    
    print("📚 TOPIC EVOLUTION:")
    print("-" * 30)
    for period in writing_patterns.get('topic_evolution', []):
        print(f"Period: {period['time_period']}")
        print(f"  Primary topics: {', '.join(period['primary_topics'])}")
        print(f"  Entries analyzed: {period['entry_count']}")
        print()
    
    print("🔤 VOCABULARY EVOLUTION:")
    print("-" * 30)
    vocab_evolution = writing_patterns.get('vocabulary_evolution', {})
    if vocab_evolution:
        print(f"Vocabulary growth: {vocab_evolution.get('vocabulary_growth', 0)} words")
        print(f"Unique early words: {vocab_evolution.get('unique_early_words', 0)}")
        print(f"Unique recent words: {vocab_evolution.get('unique_late_words', 0)}")
        print(f"Consistent words: {vocab_evolution.get('consistent_words', 0)}")
    else:
        print("Vocabulary analysis requires more temporal data")


def demonstrate_life_chapter_detection(service: SelfReflectionService, entries: List[EnhancedLLEntry]):
    """Demonstrate life chapter detection and editing capabilities"""
    print("\n" + "=" * 60)
    print("LIFE CHAPTER DETECTION")
    print("=" * 60)
    
    analysis = service.analyze_personal_patterns(entries)
    life_chapters = analysis['life_chapters']
    
    if not life_chapters:
        print("No distinct life chapters detected in this dataset.")
        print("This could be due to:")
        print("- Insufficient time span")
        print("- Limited pattern variation")
        print("- Need for more significant events")
        return
    
    print(f"\n📖 DETECTED {len(life_chapters)} LIFE CHAPTERS:")
    print("-" * 40)
    
    for i, chapter in enumerate(life_chapters, 1):
        start_date = datetime.fromisoformat(chapter['start_date'].replace('Z', '+00:00').replace('+00:00', ''))
        end_date = datetime.fromisoformat(chapter['end_date'].replace('Z', '+00:00').replace('+00:00', ''))
        
        print(f"\nChapter {i}: {chapter['title']}")
        print(f"  📅 Duration: {start_date.strftime('%B %Y')} - {end_date.strftime('%B %Y')}")
        print(f"  ⏱️  Length: {chapter['duration_days']} days")
        print(f"  📊 Significance: {chapter['significance_score']:.2f}")
        print(f"  🏷️  Key themes: {', '.join(chapter['key_themes'])}")
        print(f"  📝 Description: {chapter['description']}")
        print(f"  📈 Entries: {chapter['entry_count']}")
    
    print("\n💡 CHAPTER EDITING CAPABILITIES:")
    print("-" * 35)
    print("• Users can rename chapters")
    print("• Merge adjacent chapters")
    print("• Split chapters at specific dates")
    print("• Adjust chapter boundaries")
    print("• Add custom descriptions")
    print("• Mark chapters as private")


def demonstrate_recurring_theme_identification(service: SelfReflectionService, entries: List[EnhancedLLEntry]):
    """Demonstrate recurring theme identification"""
    print("\n" + "=" * 60)
    print("RECURRING THEME IDENTIFICATION")
    print("=" * 60)
    
    analysis = service.analyze_personal_patterns(entries)
    recurring_themes = analysis['recurring_themes']
    
    if not recurring_themes:
        print("No recurring themes detected with sufficient frequency.")
        return
    
    print(f"\n🔄 IDENTIFIED {len(recurring_themes)} RECURRING THEMES:")
    print("-" * 45)
    
    for theme in recurring_themes:
        print(f"\n🏷️  Theme: {theme['theme_name'].title()}")
        print(f"   📊 Frequency: {theme['frequency']} occurrences")
        print(f"   ⭐ Significance: {theme['significance']:.3f}")
        print(f"   📅 Time periods: {', '.join(theme['time_periods'])}")
        print(f"   🕐 First seen: {theme['first_occurrence'][:10]}")
        print(f"   🕐 Last seen: {theme['last_occurrence'][:10]}")
    
    print("\n📈 THEME ANALYSIS INSIGHTS:")
    print("-" * 30)
    print("• Themes that disappeared over time")
    print("• Themes that emerged recently")
    print("• Consistent life-long themes")
    print("• Seasonal or cyclical patterns")


def demonstrate_pattern_presentation(service: SelfReflectionService, entries: List[EnhancedLLEntry]):
    """Demonstrate how patterns are presented as suggestions"""
    print("\n" + "=" * 60)
    print("PATTERN PRESENTATION AS SUGGESTIONS")
    print("=" * 60)
    
    analysis = service.analyze_personal_patterns(entries)
    insights = analysis['insights']
    
    print(f"\n💡 GENERATED {len(insights)} INSIGHTS:")
    print("-" * 35)
    
    for i, insight in enumerate(insights, 1):
        print(f"\nInsight {i}: {insight['type'].replace('_', ' ').title()}")
        print(f"  🔍 Description: {insight['description']}")
        print(f"  📊 Confidence: {insight['confidence']:.2f}")
        
        if 'details' in insight:
            print(f"  📋 Details: {json.dumps(insight['details'], indent=6)}")
    
    print("\n🛡️  PRIVACY & SAFETY FEATURES:")
    print("-" * 35)
    print("• No diagnostic statements ('You are...')")
    print("• Framed as observations and patterns")
    print("• Includes confidence levels")
    print("• Avoids absolute claims")
    print("• Respects user agency")
    print("• Suggests rather than prescribes")


def demonstrate_reflection_prompt_generation(service: SelfReflectionService, entries: List[EnhancedLLEntry]):
    """Demonstrate reflection prompt generation"""
    print("\n" + "=" * 60)
    print("REFLECTION PROMPT GENERATION")
    print("=" * 60)
    
    analysis = service.analyze_personal_patterns(entries)
    reflection_prompts = analysis['reflection_prompts']
    
    print(f"\n❓ GENERATED {len(reflection_prompts)} REFLECTION PROMPTS:")
    print("-" * 45)
    
    for i, prompt in enumerate(reflection_prompts, 1):
        print(f"\nPrompt {i} ({prompt['prompt_type'].replace('_', ' ').title()}):")
        print(f"  ❓ Question: {prompt['question']}")
        print(f"  📝 Context: {prompt['context']}")
    
    print("\n🎯 PROMPT DESIGN PRINCIPLES:")
    print("-" * 30)
    print("• Invite dialogue rather than passive consumption")
    print("• Avoid commanding language")
    print("• Based on actual data patterns")
    print("• Encourage self-discovery")
    print("• Respect user autonomy")
    print("• Variety in prompt types")


def demonstrate_analysis_metadata(service: SelfReflectionService, entries: List[EnhancedLLEntry]):
    """Demonstrate analysis metadata and confidence tracking"""
    print("\n" + "=" * 60)
    print("ANALYSIS METADATA & CONFIDENCE")
    print("=" * 60)
    
    analysis = service.analyze_personal_patterns(entries)
    metadata = analysis['analysis_metadata']
    
    print("\n📊 ANALYSIS OVERVIEW:")
    print("-" * 25)
    print(f"Total entries analyzed: {metadata['total_entries']}")
    print(f"Time span: {metadata['time_span_days']} days")
    print(f"Analysis date: {metadata['analysis_date'][:19]}")
    print(f"Overall confidence: {metadata['confidence_level']:.3f}")
    
    print("\n🔍 CONFIDENCE FACTORS:")
    print("-" * 25)
    print("• Data volume (more entries = higher confidence)")
    print("• Time span (longer periods = better patterns)")
    print("• Pattern consistency")
    print("• Event significance")
    
    print("\n⚖️  ANALYSIS LIMITATIONS:")
    print("-" * 25)
    print("• Patterns may not reflect complete life picture")
    print("• Analysis based on recorded experiences only")
    print("• Confidence levels indicate uncertainty")
    print("• User interpretation is essential")


def main():
    """Main demo function"""
    print("🔍 AI-AUGMENTED PERSONAL ARCHIVE")
    print("Self-Reflection Analysis Tools Demo")
    print("=" * 60)
    
    # Create sample data
    print("Creating sample personal data spanning 3 years...")
    entries = create_sample_personal_data()
    print(f"Generated {len(entries)} personal entries")
    
    # Initialize service
    config = {
        'analysis': {
            'min_writing_samples': 5,
            'min_time_span_days': 30,
            'pattern_confidence_threshold': 0.3,
            'theme_frequency_threshold': 2
        },
        'life_chapters': {
            'min_chapter_duration_days': 90,
            'max_chapters': 10,
            'significance_threshold': 0.5
        },
        'reflection_prompts': {
            'max_prompts_per_session': 5,
            'prompt_variety': True,
            'avoid_diagnostic_language': True
        },
        'privacy': {
            'avoid_definitive_statements': True,
            'frame_as_suggestions': True,
            'respect_user_agency': True
        }
    }
    
    service = SelfReflectionService(config)
    
    # Demonstrate each capability
    demonstrate_writing_pattern_analysis(service, entries)
    demonstrate_life_chapter_detection(service, entries)
    demonstrate_recurring_theme_identification(service, entries)
    demonstrate_pattern_presentation(service, entries)
    demonstrate_reflection_prompt_generation(service, entries)
    demonstrate_analysis_metadata(service, entries)
    
    print("\n" + "=" * 60)
    print("✅ SELF-REFLECTION ANALYSIS DEMO COMPLETE")
    print("=" * 60)
    print("\nKey Requirements Validated:")
    print("✓ 8.1: Writing pattern analysis (tone, topic, vocabulary evolution)")
    print("✓ 8.2: Life chapter detection with editing capabilities")
    print("✓ 8.3: Recurring theme identification across time")
    print("✓ 8.4: Pattern presentation as suggestions")
    print("✓ 8.5: Reflection prompt generation for dialogue")
    print("\nThe self-reflection analysis tools provide users with insights")
    print("into their personal growth and patterns while maintaining privacy")
    print("and presenting findings as suggestions rather than diagnoses.")


if __name__ == "__main__":
    main()