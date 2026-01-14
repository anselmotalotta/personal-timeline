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
Memory Resurfacing Demo

This demo showcases the proactive memory resurfacing capabilities of the AI-Augmented Personal Archive.
It demonstrates how the system can:

1. Generate contextual memory suggestions based on current exploration patterns
2. Create AI-generated reflection prompts that invite dialogue
3. Surface connections between past and present interests
4. Maintain gentle, non-intrusive presentation
5. Respect user privacy and control

The demo simulates a user exploring their memories around themes like family and travel,
and shows how the system proactively suggests relevant memories and reflection opportunities.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.common.objects.enhanced_llentry import EnhancedLLEntry, PersonRelationship
from src.common.services.memory_resurfacing_service import MemoryResurfacingService


def create_sample_memories() -> List[EnhancedLLEntry]:
    """Create a collection of sample memories for demonstration"""
    memories = []
    base_time = datetime.now() - timedelta(days=365)  # One year ago
    
    # Family memories
    family_memory_1 = EnhancedLLEntry("post", (base_time + timedelta(days=30)).isoformat(), "personal_journal")
    family_memory_1.text = "Had a wonderful family dinner today. Mom made her famous lasagna and we all shared stories from our week. These moments feel so precious."
    family_memory_1.textDescription = family_memory_1.text
    family_memory_1.thematic_tags = ["family", "relationships"]
    family_memory_1.narrative_significance = 0.8
    family_memory_1.emotional_context = {
        'primary_emotion': 'gratitude',
        'valence': 0.9,
        'intensity': 0.7
    }
    family_memory_1.last_accessed = datetime.now() - timedelta(days=120)  # Not accessed recently
    memories.append(family_memory_1)
    
    family_memory_2 = EnhancedLLEntry("post", (base_time + timedelta(days=180)).isoformat(), "personal_journal")
    family_memory_2.text = "Celebrating Dad's birthday with the whole family. He's getting older but his spirit is still so young. Grateful for these traditions."
    family_memory_2.textDescription = family_memory_2.text
    family_memory_2.thematic_tags = ["family", "celebrations"]
    family_memory_2.narrative_significance = 0.9
    family_memory_2.emotional_context = {
        'primary_emotion': 'love',
        'valence': 0.8,
        'intensity': 0.8
    }
    family_memory_2.people_relationships = [
        PersonRelationship(
            person_id="Dad",
            relationship_type="family",
            confidence=1.0,
            first_interaction=base_time,
            last_interaction=base_time + timedelta(days=180)
        )
    ]
    family_memory_2.last_accessed = datetime.now() - timedelta(days=90)
    memories.append(family_memory_2)
    
    # Travel memories
    travel_memory_1 = EnhancedLLEntry("post", (base_time + timedelta(days=60)).isoformat(), "personal_journal")
    travel_memory_1.text = "Exploring the mountains today. The view from the summit was breathtaking. There's something about being in nature that puts everything in perspective."
    travel_memory_1.textDescription = travel_memory_1.text
    travel_memory_1.thematic_tags = ["travel", "nature", "growth"]
    travel_memory_1.narrative_significance = 0.7
    travel_memory_1.location = "mountains"
    travel_memory_1.emotional_context = {
        'primary_emotion': 'peace',
        'valence': 0.8,
        'intensity': 0.6
    }
    travel_memory_1.last_accessed = datetime.now() - timedelta(days=150)
    memories.append(travel_memory_1)
    
    travel_memory_2 = EnhancedLLEntry("post", (base_time + timedelta(days=200)).isoformat(), "personal_journal")
    travel_memory_2.text = "Walking through the old city streets with Sarah. Every corner has a story. Travel really opens your mind to different ways of living."
    travel_memory_2.textDescription = travel_memory_2.text
    travel_memory_2.thematic_tags = ["travel", "relationships", "learning"]
    travel_memory_2.narrative_significance = 0.6
    travel_memory_2.location = "old city"
    travel_memory_2.people_relationships = [
        PersonRelationship(
            person_id="Sarah",
            relationship_type="friend",
            confidence=0.9,
            first_interaction=base_time,
            last_interaction=base_time + timedelta(days=200)
        )
    ]
    travel_memory_2.emotional_context = {
        'primary_emotion': 'curiosity',
        'valence': 0.7,
        'intensity': 0.5
    }
    travel_memory_2.last_accessed = datetime.now() - timedelta(days=60)
    memories.append(travel_memory_2)
    
    # Work and creativity memories
    work_memory = EnhancedLLEntry("post", (base_time + timedelta(days=100)).isoformat(), "personal_journal")
    work_memory.text = "Finished a challenging project today. The creative process was intense but rewarding. Learning to balance perfectionism with progress."
    work_memory.textDescription = work_memory.text
    work_memory.thematic_tags = ["work", "creativity", "growth"]
    work_memory.narrative_significance = 0.5
    work_memory.emotional_context = {
        'primary_emotion': 'satisfaction',
        'valence': 0.6,
        'intensity': 0.7
    }
    work_memory.last_accessed = datetime.now() - timedelta(days=200)
    memories.append(work_memory)
    
    # Recent memory (should not be suggested as unvisited)
    recent_memory = EnhancedLLEntry("post", (base_time + timedelta(days=350)).isoformat(), "personal_journal")
    recent_memory.text = "Reflecting on the year. So much growth and change. Family and travel have been the highlights."
    recent_memory.textDescription = recent_memory.text
    recent_memory.thematic_tags = ["growth", "family", "travel"]
    recent_memory.narrative_significance = 0.8
    recent_memory.emotional_context = {
        'primary_emotion': 'reflective',
        'valence': 0.7,
        'intensity': 0.6
    }
    recent_memory.last_accessed = datetime.now() - timedelta(days=5)  # Recently accessed
    memories.append(recent_memory)
    
    return memories


def create_exploration_session() -> Dict[str, Any]:
    """Create a sample exploration session"""
    return {
        'session_type': 'memory_search',
        'current_themes': ['family', 'travel'],
        'session_duration_minutes': 25,
        'activities_count': 3,
        'recently_viewed': [],
        'current_emotion': 'nostalgic',
        'timestamp': datetime.now()
    }


def print_section_header(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_subsection_header(title: str):
    """Print a formatted subsection header"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")


def display_suggested_memories(suggested_memories: List[Dict[str, Any]]):
    """Display suggested memories in a user-friendly format"""
    if not suggested_memories:
        print("No contextual memory suggestions at this time.")
        return
    
    for i, suggestion in enumerate(suggested_memories, 1):
        memory = suggestion['memory']
        print(f"\n{i}. Memory Suggestion (Relevance: {suggestion['relevance_score']:.2f})")
        print(f"   Type: {suggestion['suggestion_type']}")
        print(f"   Content: \"{memory.text[:100]}{'...' if len(memory.text) > 100 else ''}\"")
        print(f"   Themes: {', '.join(memory.thematic_tags)}")
        print(f"   Why suggested: {suggestion['connection_reason']}")


def display_unvisited_gems(unvisited_gems: List[Dict[str, Any]]):
    """Display unvisited memory gems"""
    if not unvisited_gems:
        print("No unvisited gems found.")
        return
    
    for i, gem in enumerate(unvisited_gems, 1):
        memory = gem['memory']
        days_ago = gem['time_since_last_access']
        print(f"\n{i}. Rediscovered Memory (Last accessed {days_ago} days ago)")
        print(f"   Content: \"{memory.text[:100]}{'...' if len(memory.text) > 100 else ''}\"")
        print(f"   Themes: {', '.join(memory.thematic_tags)}")
        print(f"   Why rediscover: {gem['rediscovery_reason']}")


def display_reflection_prompts(reflection_prompts: List[Dict[str, Any]]):
    """Display AI-generated reflection prompts"""
    if not reflection_prompts:
        print("No reflection prompts generated.")
        return
    
    for i, prompt in enumerate(reflection_prompts, 1):
        print(f"\n{i}. Reflection Question ({prompt['prompt_style']})")
        print(f"   Question: {prompt['question']}")
        print(f"   Context: {prompt['context_connection']}")


def display_pattern_connections(pattern_connections: List[Dict[str, Any]]):
    """Display detected pattern connections"""
    if not pattern_connections:
        print("No pattern connections detected.")
        return
    
    for i, connection in enumerate(pattern_connections, 1):
        print(f"\n{i}. Pattern Connection (Strength: {connection['connection_strength']:.2f})")
        print(f"   Type: {connection['connection_type']}")
        print(f"   Past: {connection['past_element']}")
        print(f"   Present: {connection['present_element']}")
        print(f"   Connection: {connection['narrative_bridge']}")


def display_user_controls(user_controls: Dict[str, Any]):
    """Display available user controls"""
    print("\nUser Controls Available:")
    print(f"• Dismiss suggestions: {user_controls.get('dismiss_suggestions', 'Available')}")
    print(f"• Adjust frequency: {', '.join(user_controls.get('adjust_frequency', []))}")
    print(f"• Customize themes: {user_controls.get('customize_themes', 'Available')}")
    print(f"• Privacy controls: {user_controls.get('privacy_controls', 'Available')}")


def main():
    """Main demo function"""
    print_section_header("AI-Augmented Personal Archive: Memory Resurfacing Demo")
    
    print("\nThis demo showcases proactive memory resurfacing capabilities.")
    print("The system analyzes your current exploration context and suggests relevant memories,")
    print("reflection prompts, and pattern connections in a gentle, non-intrusive way.")
    
    # Initialize the memory resurfacing service
    config = {
        'contextual_suggestions': {
            'max_suggestions_per_session': 5,
            'similarity_threshold': 0.3,
            'recency_weight': 0.3,
            'relevance_weight': 0.4,
            'novelty_weight': 0.3
        },
        'reflection_prompts': {
            'max_prompts_per_session': 3,
            'prompt_variety': True,
            'avoid_repetitive_prompts': True,
            'dialogue_oriented': True
        },
        'presentation': {
            'gentle_approach': True,
            'non_intrusive': True,
            'respect_user_agency': True,
            'suggestion_framing': True
        },
        'pattern_detection': {
            'connection_types': ['thematic', 'temporal', 'people', 'location', 'emotional'],
            'min_pattern_strength': 0.2,
            'max_connections_per_memory': 3
        },
        'privacy': {
            'local_processing_only': True,
            'no_external_calls': True,
            'user_control_priority': True
        }
    }
    
    resurfacing_service = MemoryResurfacingService(config)
    
    # Create sample data
    print_subsection_header("Setting up sample data")
    memories = create_sample_memories()
    exploration_session = create_exploration_session()
    
    print(f"Created {len(memories)} sample memories spanning the past year")
    print(f"Current exploration context: {exploration_session['current_themes']} (feeling {exploration_session['current_emotion']})")
    
    # Generate contextual suggestions
    print_section_header("Generating Contextual Memory Suggestions")
    
    suggestions_result = resurfacing_service.generate_contextual_suggestions(
        exploration_session, memories
    )
    
    # Display results
    print_subsection_header("Contextually Relevant Memories")
    display_suggested_memories(suggestions_result['suggested_memories'])
    
    print_subsection_header("Unvisited Memory Gems")
    display_unvisited_gems(suggestions_result['unvisited_gems'])
    
    print_subsection_header("AI-Generated Reflection Prompts")
    display_reflection_prompts(suggestions_result['reflection_prompts'])
    
    print_subsection_header("Pattern Connections")
    display_pattern_connections(suggestions_result['pattern_connections'])
    
    print_subsection_header("Presentation Approach")
    presentation = suggestions_result['presentation_metadata']
    print(f"Approach: {presentation['approach']}")
    print(f"User agency respected: {presentation['user_agency_respected']}")
    print(f"Intrusion level: {presentation['intrusion_level']}")
    print(f"Privacy preserved: {presentation['privacy_preserved']}")
    
    print_subsection_header("User Controls")
    display_user_controls(suggestions_result['user_controls'])
    
    # Summary
    print_section_header("Demo Summary")
    
    total_suggestions = (
        len(suggestions_result['suggested_memories']) +
        len(suggestions_result['unvisited_gems']) +
        len(suggestions_result['reflection_prompts']) +
        len(suggestions_result['pattern_connections'])
    )
    
    print(f"Total suggestions generated: {total_suggestions}")
    print(f"• Contextual memories: {len(suggestions_result['suggested_memories'])}")
    print(f"• Unvisited gems: {len(suggestions_result['unvisited_gems'])}")
    print(f"• Reflection prompts: {len(suggestions_result['reflection_prompts'])}")
    print(f"• Pattern connections: {len(suggestions_result['pattern_connections'])}")
    
    print("\nKey Features Demonstrated:")
    print("✓ Contextual relevance based on current exploration themes")
    print("✓ Rediscovery of memories not accessed recently")
    print("✓ AI-generated reflection questions that invite dialogue")
    print("✓ Pattern detection connecting past and present interests")
    print("✓ Gentle, non-intrusive presentation approach")
    print("✓ Complete user control and privacy protection")
    print("✓ Local processing without external service calls")
    
    print("\nThe memory resurfacing system successfully provides proactive but gentle")
    print("suggestions that help users rediscover forgotten moments and reflect on")
    print("their personal journey without feeling overwhelmed.")
    
    print(f"\n{'='*60}")
    print(" Demo completed successfully!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()