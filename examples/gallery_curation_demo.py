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
Gallery Curation Demo

This script demonstrates the intelligent gallery system that replaces basic filtering
with AI-powered thematic galleries, natural language prompt processing, semantic ordering,
and gallery-to-story conversion functionality.
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.common.objects.enhanced_llentry import EnhancedLLEntry, PersonRelationship
from src.common.services.gallery_curation_service import GalleryCurationService


def create_sample_memories() -> List[EnhancedLLEntry]:
    """Create sample memories for gallery curation demonstration"""
    memories = []
    base_time = datetime.now() - timedelta(days=365)
    
    # Sample memory data with different themes
    sample_data = [
        {
            'type': 'photo',
            'text': 'Amazing sunset hike with friends at the mountain trail. The view was breathtaking!',
            'tags': ['friends', 'nature', 'hiking'],
            'people': ['Alice', 'Bob'],
            'location': 'Mountain Trail',
            'theme': 'nature'
        },
        {
            'type': 'post',
            'text': 'Finished my first painting today! So proud of this creative breakthrough.',
            'tags': ['creative', 'art', 'milestone'],
            'people': [],
            'location': 'home',
            'theme': 'creative'
        },
        {
            'type': 'event',
            'text': 'Family dinner celebration for mom\'s birthday. Great food and lots of laughter.',
            'tags': ['family', 'celebration', 'birthday'],
            'people': ['Mom', 'Dad', 'Sister'],
            'location': 'home',
            'theme': 'family'
        },
        {
            'type': 'photo',
            'text': 'Coffee shop work session with the team. Productive brainstorming on the new project.',
            'tags': ['work', 'team', 'professional'],
            'people': ['Charlie', 'Diana'],
            'location': 'Coffee Shop',
            'theme': 'work'
        },
        {
            'type': 'post',
            'text': 'Quiet morning reading in the garden. These peaceful moments are precious.',
            'tags': ['quiet', 'reading', 'peaceful'],
            'people': [],
            'location': 'garden',
            'theme': 'reflection'
        },
        {
            'type': 'photo',
            'text': 'Beach day with friends! Perfect weather for swimming and volleyball.',
            'tags': ['friends', 'beach', 'summer'],
            'people': ['Alice', 'Eve', 'Frank'],
            'location': 'Beach',
            'theme': 'friends'
        },
        {
            'type': 'event',
            'text': 'Completed my first marathon! Months of training finally paid off.',
            'tags': ['achievement', 'fitness', 'milestone'],
            'people': [],
            'location': 'City Marathon Route',
            'theme': 'achievement'
        },
        {
            'type': 'post',
            'text': 'Cooking experiment: homemade pasta from scratch. Turned out delicious!',
            'tags': ['cooking', 'creative', 'home'],
            'people': [],
            'location': 'home',
            'theme': 'creative'
        },
        {
            'type': 'photo',
            'text': 'Weekend camping trip with the adventure crew. Stars were incredible!',
            'tags': ['camping', 'friends', 'nature'],
            'people': ['Bob', 'Charlie'],
            'location': 'National Park',
            'theme': 'nature'
        },
        {
            'type': 'event',
            'text': 'Graduation ceremony! Finally finished my degree after years of hard work.',
            'tags': ['graduation', 'achievement', 'milestone'],
            'people': ['Family', 'Friends'],
            'location': 'University',
            'theme': 'achievement'
        }
    ]
    
    for i, data in enumerate(sample_data):
        # Create memory with temporal spread
        memory_time = base_time + timedelta(days=i * 30)
        memory = EnhancedLLEntry(data['type'], memory_time.isoformat(), 'demo')
        memory.id = f"demo_memory_{i+1}"
        
        # Set text content
        memory.text = data['text']
        memory.textDescription = data['text']
        
        # Set thematic tags
        memory.thematic_tags = data['tags']
        memory.tags = data['tags']
        
        # Set location
        memory.location = data['location']
        
        # Set AI-enhanced fields
        memory.narrative_significance = 0.7 + (i % 3) * 0.1  # Vary significance
        memory.story_potential = 0.6 + (i % 4) * 0.1  # Vary story potential
        memory.life_phase = 'adult'
        
        # Set emotional context based on theme
        if data['theme'] == 'friends':
            memory.emotional_context = {'joy': 0.8, 'excitement': 0.7}
        elif data['theme'] == 'creative':
            memory.emotional_context = {'accomplishment': 0.8, 'inspiration': 0.9}
        elif data['theme'] == 'family':
            memory.emotional_context = {'gratitude': 0.9, 'joy': 0.8}
        elif data['theme'] == 'work':
            memory.emotional_context = {'focus': 0.7, 'accomplishment': 0.6}
        elif data['theme'] == 'reflection':
            memory.emotional_context = {'calm': 0.9, 'gratitude': 0.7}
        elif data['theme'] == 'nature':
            memory.emotional_context = {'peace': 0.8, 'excitement': 0.7}
        elif data['theme'] == 'achievement':
            memory.emotional_context = {'accomplishment': 0.9, 'pride': 0.8}
        
        # Add people relationships
        for person_name in data['people']:
            if person_name not in ['Family', 'Friends']:  # Skip generic terms
                relationship = PersonRelationship(
                    person_id=person_name,
                    relationship_type='friend' if person_name in ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank'] else 'family',
                    confidence=0.8,
                    first_interaction=memory_time - timedelta(days=365),
                    last_interaction=memory_time
                )
                memory.people_relationships.append(relationship)
        
        # Add media elements for photos
        if data['type'] == 'photo':
            memory.image_paths = [f"/demo/images/memory_{i+1}.jpg"]
            memory.imageFileName = f"memory_{i+1}.jpg"
            memory.imageFilePath = memory.image_paths[0]
        
        memories.append(memory)
    
    return memories


def demonstrate_thematic_galleries(gallery_service: GalleryCurationService):
    """Demonstrate thematic gallery creation"""
    print("\n" + "="*60)
    print("THEMATIC GALLERY DEMONSTRATION")
    print("="*60)
    
    # Test different themes
    themes_to_test = [
        "Moments with friends",
        "Creative periods", 
        "Times of growth",
        "Family gatherings"
    ]
    
    for theme in themes_to_test:
        print(f"\n📁 Creating thematic gallery: '{theme}'")
        print("-" * 50)
        
        gallery = gallery_service.create_thematic_gallery(theme)
        
        if gallery:
            print(f"✅ Gallery created successfully!")
            print(f"   Title: {gallery.title}")
            print(f"   Description: {gallery.description}")
            print(f"   Memories: {len(gallery.memory_ids)} items")
            print(f"   Creation method: {gallery.creation_method}")
            print(f"   Semantic ordering: {len(gallery.semantic_ordering)} indices")
        else:
            print(f"❌ Gallery creation failed (insufficient memories)")


def demonstrate_prompt_based_galleries(gallery_service: GalleryCurationService):
    """Demonstrate natural language prompt-based gallery creation"""
    print("\n" + "="*60)
    print("NATURAL LANGUAGE PROMPT DEMONSTRATION")
    print("="*60)
    
    # Test different natural language prompts
    prompts_to_test = [
        "Show me photos from outdoor adventures",
        "Find memories about creative projects and art",
        "Create a gallery of achievements and milestones",
        "Show me quiet and peaceful moments"
    ]
    
    for prompt in prompts_to_test:
        print(f"\n🗣️  Processing prompt: '{prompt}'")
        print("-" * 50)
        
        gallery = gallery_service.generate_from_prompt(prompt)
        
        if gallery:
            print(f"✅ Gallery created from prompt!")
            print(f"   Title: {gallery.title}")
            print(f"   Description: {gallery.description}")
            print(f"   Memories: {len(gallery.memory_ids)} items")
            print(f"   Creation method: {gallery.creation_method}")
            
            # Show how the prompt was understood
            print(f"   Prompt understanding: Gallery relates to '{prompt}'")
        else:
            print(f"❌ Gallery creation failed (insufficient memories)")


def demonstrate_semantic_ordering(gallery_service: GalleryCurationService):
    """Demonstrate semantic ordering capabilities"""
    print("\n" + "="*60)
    print("SEMANTIC ORDERING DEMONSTRATION")
    print("="*60)
    
    # Create a gallery and examine its semantic ordering
    gallery = gallery_service.create_thematic_gallery("Creative periods")
    
    if gallery:
        print(f"📊 Analyzing semantic ordering for: '{gallery.title}'")
        print("-" * 50)
        
        print(f"Memory IDs: {gallery.memory_ids}")
        print(f"Semantic ordering: {gallery.semantic_ordering}")
        
        if gallery.semantic_ordering:
            print("\n🔄 Semantic ordering analysis:")
            print("   - Memories are arranged for optimal narrative flow")
            print("   - Order goes beyond simple chronological arrangement")
            print("   - Each index represents optimal display position")
            print(f"   - Total arrangements: {len(gallery.semantic_ordering)} positions")
        else:
            print("   - Using default chronological ordering")
    else:
        print("❌ Could not create gallery for semantic ordering demo")


def demonstrate_gallery_to_story_conversion(gallery_service: GalleryCurationService):
    """Demonstrate gallery-to-story conversion functionality"""
    print("\n" + "="*60)
    print("GALLERY-TO-STORY CONVERSION DEMONSTRATION")
    print("="*60)
    
    # Create a gallery first
    gallery = gallery_service.create_thematic_gallery("Moments with friends")
    
    if gallery:
        print(f"📖 Converting gallery to story: '{gallery.title}'")
        print("-" * 50)
        
        # Test story conversion
        story = gallery_service.convert_gallery_to_story(
            gallery_id=gallery.id,
            narrative_mode='thematic',
            narrative_style='documentary',
            include_voice_narration=False
        )
        
        if story:
            print(f"✅ Story created from gallery!")
            print(f"   Story title: {story.title}")
            print(f"   Narrative mode: {story.narrative_mode}")
            print(f"   Chapters: {len(story.chapters)}")
            print(f"   Source memories: {len(story.source_memory_ids)}")
            
            # Show first chapter as example
            if story.chapters:
                first_chapter = story.chapters[0]
                print(f"\n📝 First chapter preview:")
                print(f"   Title: {first_chapter.title}")
                print(f"   Text: {first_chapter.narrative_text}")
                print(f"   Emotional tone: {first_chapter.emotional_tone}")
        else:
            print(f"❌ Story conversion failed")
    else:
        print("❌ Could not create gallery for story conversion demo")


def demonstrate_default_gallery_initialization(gallery_service: GalleryCurationService):
    """Demonstrate default gallery initialization to replace basic filtering"""
    print("\n" + "="*60)
    print("DEFAULT GALLERY INITIALIZATION DEMONSTRATION")
    print("="*60)
    
    print("🚀 Initializing default thematic galleries...")
    print("   (This replaces basic date/source filtering)")
    print("-" * 50)
    
    default_galleries = gallery_service.initialize_default_galleries()
    
    print(f"✅ Initialized {len(default_galleries)} default galleries:")
    
    for i, gallery in enumerate(default_galleries, 1):
        print(f"   {i}. {gallery.title}")
        print(f"      └─ {len(gallery.memory_ids)} memories, {gallery.creation_method} method")
    
    if default_galleries:
        print(f"\n📊 Gallery system statistics:")
        total_memories = sum(len(g.memory_ids) for g in default_galleries)
        print(f"   - Total galleries: {len(default_galleries)}")
        print(f"   - Total memories organized: {total_memories}")
        print(f"   - Average memories per gallery: {total_memories / len(default_galleries):.1f}")
    
    # Show supported themes
    themes = gallery_service.get_supported_themes()
    print(f"\n🎨 Supported themes ({len(themes)} total):")
    for theme in themes:
        print(f"   • {theme}")


def main():
    """Main demonstration function"""
    print("🎨 AI-Augmented Personal Archive - Gallery Curation Demo")
    print("=" * 60)
    print("This demo showcases the intelligent gallery system that replaces")
    print("basic filtering with AI-powered thematic galleries, natural language")
    print("prompt processing, semantic ordering, and story conversion.")
    
    # Set up temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    os.environ['APP_DATA_DIR'] = temp_dir
    
    try:
        # Initialize gallery curation service
        print(f"\n🔧 Initializing gallery curation service...")
        config = {
            'max_memories_per_gallery': 20,
            'min_memories_per_gallery': 2,
            'semantic_similarity_threshold': 0.5
        }
        gallery_service = GalleryCurationService(config)
        
        # Create sample memories (simulating existing personal data)
        print(f"📝 Creating sample memories for demonstration...")
        sample_memories = create_sample_memories()
        print(f"   Created {len(sample_memories)} sample memories with various themes")
        
        # Mock the archivist agent to return our sample memories
        # In a real system, this would query the actual database
        def mock_archivist_process(request):
            # Simple filtering based on theme/query
            query = request.get('query', '').lower()
            theme = request.get('theme', '').lower()
            max_results = request.get('max_results', 10)
            
            # Filter memories based on query/theme
            filtered_memories = []
            for memory in sample_memories:
                memory_text = memory.text.lower()
                memory_tags = [tag.lower() for tag in memory.thematic_tags]
                
                # Check if query/theme matches memory content or tags
                if (query in memory_text or 
                    theme in memory_text or
                    any(query in tag for tag in memory_tags) or
                    any(theme in tag for tag in memory_tags) or
                    any(word in memory_text for word in query.split()) or
                    any(word in memory_text for word in theme.split())):
                    filtered_memories.append(memory)
            
            return filtered_memories[:max_results]
        
        # Mock the agent coordinator
        gallery_service.agent_coordinator.process_with_archivist = mock_archivist_process
        
        # Run demonstrations
        demonstrate_default_gallery_initialization(gallery_service)
        demonstrate_thematic_galleries(gallery_service)
        demonstrate_prompt_based_galleries(gallery_service)
        demonstrate_semantic_ordering(gallery_service)
        demonstrate_gallery_to_story_conversion(gallery_service)
        
        print("\n" + "="*60)
        print("✅ GALLERY CURATION DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("Key features demonstrated:")
        print("• Thematic gallery generation with AI-generated collections")
        print("• Natural language prompt processing beyond basic search")
        print("• Semantic ordering for optimal presentation")
        print("• AI-written contextual introductions")
        print("• Gallery-to-story conversion functionality")
        print("• Default gallery initialization replacing basic filtering")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary directory
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()