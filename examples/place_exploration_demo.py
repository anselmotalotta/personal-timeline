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
Place-Based Exploration Demo

This script demonstrates the enhanced place-based exploration functionality that upgrades
the existing GoogleMapComponent with narrative layers, story-driven location exploration,
travel narrative generation, enhanced geo-enrichment, and journey narrative connections.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.common.objects.enhanced_llentry import EnhancedLLEntry, PersonRelationship
from src.common.services.place_exploration_service import PlaceExplorationService


def create_sample_location_memories() -> List[EnhancedLLEntry]:
    """Create sample memories with location data for demonstration"""
    memories = []
    base_time = datetime.now() - timedelta(days=365)
    
    # Sample locations and their associated memories
    location_data = [
        {
            'location': 'Central Park',
            'coordinates': (40.7829, -73.9654),
            'memories': [
                {
                    'text': 'Beautiful morning jog through Central Park. The autumn leaves were stunning and I felt so energized.',
                    'days_ago': 30,
                    'emotions': {'joy': 0.8, 'energy': 0.9},
                    'people': ['Alice']
                },
                {
                    'text': 'Picnic in Central Park with friends. We played frisbee and enjoyed the perfect weather.',
                    'days_ago': 60,
                    'emotions': {'joy': 0.9, 'social': 0.8},
                    'people': ['Alice', 'Bob', 'Charlie']
                },
                {
                    'text': 'Quiet walk in Central Park during lunch break. Needed some peace and nature in the middle of the busy day.',
                    'days_ago': 90,
                    'emotions': {'calm': 0.8, 'gratitude': 0.7},
                    'people': []
                }
            ]
        },
        {
            'location': 'Coffee Shop Downtown',
            'coordinates': (40.7505, -73.9934),
            'memories': [
                {
                    'text': 'Great coffee meeting with Diana to discuss the new project. Really excited about the collaboration.',
                    'days_ago': 15,
                    'emotions': {'excitement': 0.8, 'professional': 0.7},
                    'people': ['Diana']
                },
                {
                    'text': 'Working from the coffee shop today. Love the atmosphere and the background buzz helps me focus.',
                    'days_ago': 45,
                    'emotions': {'focus': 0.7, 'satisfaction': 0.6},
                    'people': []
                }
            ]
        },
        {
            'location': 'Brooklyn Bridge',
            'coordinates': (40.7061, -73.9969),
            'memories': [
                {
                    'text': 'Amazing sunset walk across Brooklyn Bridge with my partner. The city looked magical from up there.',
                    'days_ago': 20,
                    'emotions': {'romance': 0.9, 'awe': 0.8},
                    'people': ['Partner']
                },
                {
                    'text': 'Tourist day! Showed my visiting family around Brooklyn Bridge. They were amazed by the views.',
                    'days_ago': 120,
                    'emotions': {'pride': 0.8, 'family': 0.9},
                    'people': ['Mom', 'Dad', 'Sister']
                }
            ]
        },
        {
            'location': 'Home',
            'coordinates': (40.7282, -73.7949),
            'memories': [
                {
                    'text': 'Cozy evening at home cooking dinner and watching movies. Sometimes the simple moments are the best.',
                    'days_ago': 5,
                    'emotions': {'contentment': 0.8, 'peace': 0.7},
                    'people': []
                },
                {
                    'text': 'Hosted a dinner party at home. Everyone loved the homemade pasta and we had great conversations.',
                    'days_ago': 40,
                    'emotions': {'pride': 0.8, 'social': 0.9},
                    'people': ['Alice', 'Bob', 'Charlie', 'Diana']
                },
                {
                    'text': 'Working from home today. Set up a nice workspace by the window and had a very productive day.',
                    'days_ago': 10,
                    'emotions': {'productivity': 0.8, 'satisfaction': 0.7},
                    'people': []
                }
            ]
        },
        {
            'location': 'Times Square',
            'coordinates': (40.7580, -73.9855),
            'memories': [
                {
                    'text': 'Caught a Broadway show in Times Square. The performance was incredible and the energy was electric.',
                    'days_ago': 80,
                    'emotions': {'excitement': 0.9, 'culture': 0.8},
                    'people': ['Partner']
                }
            ]
        },
        {
            'location': 'Prospect Park',
            'coordinates': (40.6602, -73.9690),
            'memories': [
                {
                    'text': 'Long bike ride through Prospect Park. Discovered some beautiful trails I had never seen before.',
                    'days_ago': 25,
                    'emotions': {'discovery': 0.8, 'adventure': 0.7},
                    'people': []
                }
            ]
        }
    ]
    
    # Convert to EnhancedLLEntry objects
    for location_info in location_data:
        location_name = location_info['location']
        coordinates = location_info['coordinates']
        
        for memory_data in location_info['memories']:
            # Create timestamp
            memory_time = base_time + timedelta(days=365 - memory_data['days_ago'])
            
            # Create memory entry
            memory = EnhancedLLEntry("post", memory_time.isoformat(), "manual")
            memory.text = memory_data['text']
            memory.textDescription = memory_data['text']
            memory.location = location_name
            memory.lat_lon = [coordinates]
            
            # Add AI-enhanced fields
            memory.narrative_significance = 0.7 + (len(memory_data['text']) / 200)  # Based on content richness
            memory.story_potential = 0.6 + (len(memory_data['people']) * 0.1)  # Higher for social memories
            memory.emotional_context = memory_data['emotions']
            memory.life_phase = 'adult'
            
            # Determine thematic tags
            tags = ['daily_life']
            if memory_data['people']:
                tags.append('social')
            if 'work' in memory_data['text'].lower() or 'project' in memory_data['text'].lower():
                tags.append('work')
            if 'nature' in memory_data['text'].lower() or 'park' in memory_data['text'].lower():
                tags.append('nature')
            if 'family' in memory_data['text'].lower():
                tags.append('family')
            
            memory.thematic_tags = tags
            
            # Add people relationships
            for person_name in memory_data['people']:
                relationship_type = 'family' if person_name in ['Mom', 'Dad', 'Sister'] else \
                                 'partner' if person_name == 'Partner' else 'friend'
                
                relationship = PersonRelationship(
                    person_id=person_name,
                    relationship_type=relationship_type,
                    confidence=0.9,
                    first_interaction=memory_time - timedelta(days=365),
                    last_interaction=memory_time
                )
                memory.people_relationships.append(relationship)
            
            memories.append(memory)
    
    return memories


def demonstrate_place_analysis(place_service: PlaceExplorationService, memories: List[EnhancedLLEntry]):
    """Demonstrate place relationship analysis"""
    print("\n" + "="*60)
    print("PLACE RELATIONSHIP ANALYSIS DEMONSTRATION")
    print("="*60)
    
    print("🏙️ Analyzing place relationships from personal memories...")
    place_profiles = place_service.analyze_place_relationships(memories)
    
    print(f"\n📍 Discovered {len(place_profiles)} significant places:")
    print("-" * 50)
    
    for place_id, profile in place_profiles.items():
        print(f"\n🏛️ {profile.name}")
        print(f"   📅 First visit: {profile.first_visit.strftime('%B %d, %Y')}")
        print(f"   📅 Last visit: {profile.last_visit.strftime('%B %d, %Y')}")
        print(f"   🔢 Total visits: {profile.visit_count}")
        print(f"   ⭐ Narrative significance: {profile.narrative_significance:.2f}")
        
        if profile.coordinates:
            print(f"   🌍 Coordinates: {profile.coordinates[0]:.4f}, {profile.coordinates[1]:.4f}")
        
        if profile.emotional_associations:
            emotions = ", ".join([f"{emotion}: {score:.2f}" 
                                for emotion, score in profile.emotional_associations.items()])
            print(f"   💭 Emotional associations: {emotions}")
        
        print(f"   📝 Representative memories: {len(profile.representative_memories)} selected")


def demonstrate_location_exploration(place_service: PlaceExplorationService, memories: List[EnhancedLLEntry]):
    """Demonstrate story-driven location exploration"""
    print("\n" + "="*60)
    print("STORY-DRIVEN LOCATION EXPLORATION DEMONSTRATION")
    print("="*60)
    
    # Find a location with multiple visits
    location_counts = {}
    for memory in memories:
        if memory.location:
            location_counts[memory.location] = location_counts.get(memory.location, 0) + 1
    
    # Pick the location with the most visits
    if location_counts:
        primary_location = max(location_counts.items(), key=lambda x: x[1])[0]
        
        print(f"🎯 Creating story-driven exploration for: {primary_location}")
        print(f"   (Selected because it has {location_counts[primary_location]} visits)")
        
        location_exploration = place_service.create_location_exploration(primary_location, memories)
        
        if location_exploration:
            print(f"\n🗺️ Location Exploration: {location_exploration.location_name}")
            print("-" * 50)
            
            # Show narrative layers
            print(f"\n📚 Narrative Layers ({len(location_exploration.narrative_layers)} layers):")
            for i, layer in enumerate(location_exploration.narrative_layers, 1):
                print(f"   {i}. {layer['title']}")
                print(f"      Type: {layer['type']}")
                print(f"      Description: {layer['description']}")
                
                # Show some layer data
                if 'timeline' in layer['data']:
                    timeline = layer['data']['timeline']
                    print(f"      Timeline entries: {len(timeline)}")
                elif 'dominant_emotions' in layer['data']:
                    emotions = layer['data']['dominant_emotions']
                    if emotions:
                        top_emotion = max(emotions.items(), key=lambda x: x[1])
                        print(f"      Dominant emotion: {top_emotion[0]} ({top_emotion[1]:.2f})")
                elif 'people_count' in layer['data']:
                    people_count = layer['data']['people_count']
                    print(f"      People involved: {people_count}")
                print()
            
            # Show temporal stories
            if location_exploration.temporal_stories:
                print(f"📖 Temporal Stories ({len(location_exploration.temporal_stories)} stories):")
                for story in location_exploration.temporal_stories:
                    print(f"   • {story.title}")
                    print(f"     Chapters: {len(story.chapters)}")
                    if story.chapters:
                        print(f"     Preview: {story.chapters[0].narrative_text[:100]}...")
                print()
            
            # Show relationship evolution
            if location_exploration.relationship_evolution:
                print("💝 Relationship Evolution:")
                evolution = location_exploration.relationship_evolution
                if 'evolution_summary' in evolution:
                    print(f"   Summary: {evolution['evolution_summary']}")
                if 'relationship_trend' in evolution:
                    print(f"   Trend: {evolution['relationship_trend']}")
                print()


def demonstrate_travel_narratives(place_service: PlaceExplorationService, memories: List[EnhancedLLEntry]):
    """Demonstrate travel narrative generation"""
    print("\n" + "="*60)
    print("TRAVEL NARRATIVE GENERATION DEMONSTRATION")
    print("="*60)
    
    print("🚶 Generating travel narratives from memory patterns...")
    
    # Generate different types of narratives
    narrative_types = ['journey', 'exploration', 'routine']
    
    for narrative_type in narrative_types:
        print(f"\n🎭 {narrative_type.title()} Narratives:")
        print("-" * 30)
        
        journey_narratives = place_service.generate_travel_narrative(memories, narrative_type)
        
        if journey_narratives:
            for journey in journey_narratives:
                print(f"   📍 {journey.title}")
                print(f"      Places: {' → '.join(journey.places)}")
                print(f"      Duration: {(journey.temporal_span[1] - journey.temporal_span[0]).days} days")
                print(f"      Narrative: {journey.narrative_text}")
                
                if journey.emotional_arc:
                    avg_intensity = sum(point['intensity'] for point in journey.emotional_arc) / len(journey.emotional_arc)
                    print(f"      Emotional intensity: {avg_intensity:.2f}")
                print()
        else:
            print(f"   No {narrative_type} narratives detected in this timeframe")


def demonstrate_geo_enrichment(place_service: PlaceExplorationService, memories: List[EnhancedLLEntry]):
    """Demonstrate enhanced geo-enrichment"""
    print("\n" + "="*60)
    print("ENHANCED GEO-ENRICHMENT DEMONSTRATION")
    print("="*60)
    
    print("🌍 Enhancing geo-enrichment with semantic understanding...")
    
    # Take a few sample memories and enhance them
    sample_memories = memories[:3]
    
    for i, memory in enumerate(sample_memories, 1):
        print(f"\n📝 Memory {i}: {memory.location}")
        print(f"   Original text: {memory.text[:80]}...")
        
        enhanced_memory = place_service.enhance_geo_enrichment(memory)
        
        if hasattr(enhanced_memory, 'enhanced_location_data'):
            enhanced_data = enhanced_memory.enhanced_location_data
            
            if 'semantic_context' in enhanced_data:
                context = enhanced_data['semantic_context']
                if 'activities' in context and context['activities']:
                    print(f"   🎯 Detected activities: {', '.join(context['activities'])}")
            
            if 'narrative_significance' in enhanced_data:
                significance = enhanced_data['narrative_significance']
                print(f"   ⭐ Location significance: {significance:.2f}")
            
            if 'emotional_associations' in enhanced_data:
                emotions = enhanced_data['emotional_associations']
                if emotions:
                    emotion_str = ", ".join([f"{k}: {v:.2f}" for k, v in emotions.items()])
                    print(f"   💭 Emotional associations: {emotion_str}")
        else:
            print("   ℹ️ No additional enrichment data available")


def demonstrate_map_narrative_layers(place_service: PlaceExplorationService):
    """Demonstrate narrative layers for map display"""
    print("\n" + "="*60)
    print("MAP NARRATIVE LAYERS DEMONSTRATION")
    print("="*60)
    
    print("🗺️ Generating narrative layers for map display...")
    
    # Define bounds that would cover New York City area
    nyc_bounds = {
        'north': 40.9176,
        'south': 40.4774,
        'east': -73.7004,
        'west': -74.2591
    }
    
    narrative_layers = place_service.get_narrative_layers_for_map(nyc_bounds)
    
    print(f"\n📍 Found {len(narrative_layers)} places with narrative layers:")
    print("-" * 50)
    
    for layer_data in narrative_layers:
        print(f"\n🏛️ {layer_data['name']}")
        print(f"   🔢 Visits: {layer_data['visit_count']}")
        print(f"   ⭐ Significance: {layer_data['narrative_significance']:.2f}")
        
        if 'coordinates' in layer_data and layer_data['coordinates']:
            coords = layer_data['coordinates']
            print(f"   🌍 Location: {coords[0]:.4f}, {coords[1]:.4f}")
        
        if 'emotional_associations' in layer_data:
            emotions = layer_data['emotional_associations']
            if emotions:
                top_emotion = max(emotions.items(), key=lambda x: x[1])
                print(f"   💭 Primary emotion: {top_emotion[0]} ({top_emotion[1]:.2f})")
        
        if 'story_preview' in layer_data:
            preview = layer_data['story_preview']
            print(f"   📖 Story preview: {preview}")


def main():
    """Main demonstration function"""
    print("🎨 AI-Augmented Personal Archive - Place-Based Exploration Demo")
    print("=" * 70)
    print("This demo showcases enhanced place-based exploration that upgrades")
    print("the existing GoogleMapComponent with narrative layers, story-driven")
    print("location exploration, travel narratives, and enhanced geo-enrichment.")
    
    # Initialize the place exploration service
    config = {
        'narrative': {
            'min_visits_for_profile': 2,
            'significance_threshold': 0.3,
            'journey_detection_window_days': 30,
            'max_narrative_layers': 5
        }
    }
    
    place_service = PlaceExplorationService(config)
    
    # Create sample memories with location data
    print("\n🏗️ Creating sample location memories...")
    memories = create_sample_location_memories()
    print(f"   Generated {len(memories)} memories across multiple locations")
    
    # Demonstrate each aspect of place-based exploration
    demonstrate_place_analysis(place_service, memories)
    demonstrate_location_exploration(place_service, memories)
    demonstrate_travel_narratives(place_service, memories)
    demonstrate_geo_enrichment(place_service, memories)
    demonstrate_map_narrative_layers(place_service)
    
    print("\n" + "="*70)
    print("🎯 PLACE-BASED EXPLORATION SUMMARY")
    print("="*70)
    print("✅ Place relationship analysis - Creates profiles for significant locations")
    print("✅ Story-driven exploration - Provides narrative context beyond simple listings")
    print("✅ Travel narrative generation - Connects locations into meaningful journeys")
    print("✅ Enhanced geo-enrichment - Adds semantic understanding to location data")
    print("✅ Map narrative layers - Upgrades GoogleMapComponent with story elements")
    print("\n🚀 The enhanced place-based exploration transforms static location data")
    print("   into rich, narrative-driven experiences that help users understand")
    print("   their relationship with places through temporal and emotional context.")


if __name__ == "__main__":
    main()