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

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

from src.common.objects.enhanced_llentry import EnhancedLLEntry, Story, Chapter
from src.common.geo_helper import GeoHelper


@dataclass
class PlaceProfile:
    """Profile for a specific place with narrative context"""
    place_id: str
    name: str
    coordinates: Optional[Tuple[float, float]]
    first_visit: datetime
    last_visit: datetime
    visit_count: int
    emotional_associations: Dict[str, float]
    temporal_patterns: List[Dict[str, Any]]
    narrative_significance: float
    representative_memories: List[str]  # Memory IDs
    journey_connections: List[str]  # Connected place IDs


@dataclass
class JourneyNarrative:
    """A narrative connecting multiple places"""
    journey_id: str
    title: str
    places: List[str]  # Place IDs in order
    narrative_text: str
    temporal_span: Tuple[datetime, datetime]
    journey_type: str  # 'travel', 'routine', 'exploration', 'migration'
    emotional_arc: List[Dict[str, Any]]


@dataclass
class LocationExploration:
    """Story-driven exploration of a specific location"""
    location_id: str
    location_name: str
    narrative_layers: List[Dict[str, Any]]
    temporal_stories: List[Story]
    emotional_timeline: List[Dict[str, Any]]
    relationship_evolution: Dict[str, Any]
    connected_journeys: List[str]  # Journey IDs


class PlaceExplorationService:
    """
    Service for enhanced place-based exploration with narrative layers.
    
    This service upgrades the existing GoogleMapComponent functionality with:
    - Story-driven location exploration
    - Travel narrative generation
    - Enhanced geo-enrichment with semantic understanding
    - Journey narrative connections
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the place exploration service"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.geo_helper = GeoHelper()
        
        # Initialize place and journey storage
        self.place_profiles: Dict[str, PlaceProfile] = {}
        self.journey_narratives: Dict[str, JourneyNarrative] = {}
        
        # Configuration for narrative generation
        self.narrative_config = self.config.get('narrative', {
            'min_visits_for_profile': 2,
            'significance_threshold': 0.3,
            'journey_detection_window_days': 30,
            'max_narrative_layers': 5
        })
    
    def analyze_place_relationships(self, memories: List[EnhancedLLEntry]) -> Dict[str, PlaceProfile]:
        """
        Analyze memories to create place profiles with narrative context.
        
        Args:
            memories: List of enhanced memory entries
            
        Returns:
            Dictionary mapping place IDs to PlaceProfile objects
        """
        self.logger.info(f"Analyzing place relationships for {len(memories)} memories")
        
        # Group memories by location
        place_memories = defaultdict(list)
        
        for memory in memories:
            place_name = self._extract_place_from_memory(memory)
            if place_name and place_name != "unknown":
                place_memories[place_name].append(memory)
        
        # Create place profiles
        place_profiles = {}
        
        for place_name, place_memory_list in place_memories.items():
            if len(place_memory_list) >= self.narrative_config['min_visits_for_profile']:
                profile = self._create_place_profile(place_name, place_memory_list)
                if profile.narrative_significance >= self.narrative_config['significance_threshold']:
                    place_profiles[profile.place_id] = profile
        
        self.place_profiles.update(place_profiles)
        return place_profiles
    
    def create_location_exploration(self, location_id: str, memories: List[EnhancedLLEntry]) -> LocationExploration:
        """
        Create story-driven exploration for a specific location.
        
        Args:
            location_id: Identifier for the location
            memories: Memories associated with this location
            
        Returns:
            LocationExploration object with narrative layers and stories
        """
        self.logger.info(f"Creating location exploration for {location_id}")
        
        # Filter memories for this location
        location_memories = [
            memory for memory in memories 
            if self._extract_place_from_memory(memory) == location_id
        ]
        
        if not location_memories:
            self.logger.warning(f"No memories found for location {location_id}")
            return None
        
        # Create narrative layers
        narrative_layers = self._create_narrative_layers(location_memories)
        
        # Generate temporal stories
        temporal_stories = self._generate_temporal_stories(location_memories)
        
        # Create emotional timeline
        emotional_timeline = self._create_emotional_timeline(location_memories)
        
        # Analyze relationship evolution
        relationship_evolution = self._analyze_relationship_evolution(location_memories)
        
        # Find connected journeys
        connected_journeys = self._find_connected_journeys(location_id)
        
        return LocationExploration(
            location_id=location_id,
            location_name=location_id,  # Could be enhanced with proper name resolution
            narrative_layers=narrative_layers,
            temporal_stories=temporal_stories,
            emotional_timeline=emotional_timeline,
            relationship_evolution=relationship_evolution,
            connected_journeys=connected_journeys
        )
    
    def generate_travel_narrative(self, memories: List[EnhancedLLEntry], 
                                narrative_type: str = 'journey') -> List[JourneyNarrative]:
        """
        Generate travel narratives that connect multiple locations.
        
        Args:
            memories: List of memories to analyze for travel patterns
            narrative_type: Type of narrative ('journey', 'exploration', 'routine')
            
        Returns:
            List of JourneyNarrative objects
        """
        self.logger.info(f"Generating travel narratives of type {narrative_type}")
        
        # Sort memories by time
        sorted_memories = sorted(memories, key=lambda m: self._get_memory_timestamp(m))
        
        # Detect journey patterns
        journey_segments = self._detect_journey_segments(sorted_memories)
        
        # Generate narratives for each journey
        journey_narratives = []
        
        for i, segment in enumerate(journey_segments):
            if len(segment) >= 2:  # Need at least 2 locations for a journey
                narrative = self._create_journey_narrative(
                    journey_id=f"journey_{i}_{narrative_type}",
                    memories=segment,
                    journey_type=narrative_type
                )
                if narrative:
                    journey_narratives.append(narrative)
        
        self.journey_narratives.update({j.journey_id: j for j in journey_narratives})
        return journey_narratives
    
    def enhance_geo_enrichment(self, memory: EnhancedLLEntry) -> EnhancedLLEntry:
        """
        Enhance geo-enrichment with semantic understanding.
        
        Args:
            memory: Memory entry to enhance
            
        Returns:
            Enhanced memory with improved location context
        """
        if not hasattr(memory, 'location') or not memory.location:
            return memory
        
        try:
            # Get enhanced location information
            location_data = self._get_enhanced_location_data(memory.location)
            
            # Add semantic context
            semantic_context = self._extract_semantic_location_context(memory)
            
            # Update memory with enhanced data
            if not hasattr(memory, 'enhanced_location_data'):
                memory.enhanced_location_data = {}
            
            memory.enhanced_location_data.update({
                'enriched_data': location_data,
                'semantic_context': semantic_context,
                'narrative_significance': self._calculate_location_significance(memory),
                'emotional_associations': self._extract_emotional_associations(memory)
            })
            
        except Exception as e:
            self.logger.warning(f"Failed to enhance geo-enrichment for memory: {e}")
        
        return memory
    
    def get_narrative_layers_for_map(self, location_bounds: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Get narrative layers for map display within specified bounds.
        
        Args:
            location_bounds: Dictionary with 'north', 'south', 'east', 'west' bounds
            
        Returns:
            List of narrative layer data for map overlay
        """
        narrative_layers = []
        
        # Get places within bounds
        relevant_places = self._get_places_in_bounds(location_bounds)
        
        for place_id in relevant_places:
            if place_id in self.place_profiles:
                profile = self.place_profiles[place_id]
                
                layer_data = {
                    'place_id': place_id,
                    'name': profile.name,
                    'coordinates': profile.coordinates,
                    'narrative_significance': profile.narrative_significance,
                    'emotional_associations': profile.emotional_associations,
                    'visit_count': profile.visit_count,
                    'temporal_span': {
                        'first_visit': profile.first_visit.isoformat(),
                        'last_visit': profile.last_visit.isoformat()
                    },
                    'story_preview': self._generate_place_story_preview(profile)
                }
                
                narrative_layers.append(layer_data)
        
        return narrative_layers
    
    # Private helper methods
    
    def _extract_place_from_memory(self, memory: EnhancedLLEntry) -> str:
        """Extract place name from memory"""
        if hasattr(memory, 'location') and memory.location:
            if isinstance(memory.location, str):
                return memory.location
            elif isinstance(memory.location, dict) and 'name' in memory.location:
                return memory.location['name']
        
        # Try to extract from text
        if hasattr(memory, 'text') and memory.text:
            # Simple location extraction from text
            text_lower = memory.text.lower()
            location_indicators = ['at ', 'in ', 'near ', 'visiting ']
            for indicator in location_indicators:
                if indicator in text_lower:
                    # Extract potential location after indicator
                    start_idx = text_lower.find(indicator) + len(indicator)
                    location_part = memory.text[start_idx:start_idx + 50]
                    # Simple extraction - take first few words
                    words = location_part.split()[:3]
                    if words:
                        return ' '.join(words).strip('.,!?')
        
        return "unknown"
    
    def _create_place_profile(self, place_name: str, memories: List[EnhancedLLEntry]) -> PlaceProfile:
        """Create a place profile from memories"""
        # Sort memories by time
        sorted_memories = sorted(memories, key=lambda m: self._get_memory_timestamp(m))
        
        first_visit = self._get_memory_timestamp(sorted_memories[0])
        last_visit = self._get_memory_timestamp(sorted_memories[-1])
        
        # Calculate emotional associations
        emotional_associations = self._calculate_emotional_associations(memories)
        
        # Calculate narrative significance
        narrative_significance = self._calculate_place_significance(memories)
        
        # Extract coordinates if available
        coordinates = self._extract_coordinates(memories)
        
        # Create temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(memories)
        
        # Select representative memories
        representative_memories = self._select_representative_memories(memories)
        
        return PlaceProfile(
            place_id=place_name,
            name=place_name,
            coordinates=coordinates,
            first_visit=first_visit,
            last_visit=last_visit,
            visit_count=len(memories),
            emotional_associations=emotional_associations,
            temporal_patterns=temporal_patterns,
            narrative_significance=narrative_significance,
            representative_memories=[m.id if hasattr(m, 'id') else str(hash(m.text or '')) 
                                   for m in representative_memories],
            journey_connections=[]
        )
    
    def _get_memory_timestamp(self, memory: EnhancedLLEntry) -> datetime:
        """Get timestamp from memory"""
        if hasattr(memory, 'startTime') and memory.startTime:
            try:
                return datetime.fromisoformat(memory.startTime.replace('Z', '+00:00'))
            except:
                pass
        
        if hasattr(memory, 'recordedStartTime') and memory.recordedStartTime:
            try:
                return datetime.fromisoformat(memory.recordedStartTime.replace('Z', '+00:00'))
            except:
                pass
        
        return datetime.now()
    
    def _calculate_emotional_associations(self, memories: List[EnhancedLLEntry]) -> Dict[str, float]:
        """Calculate emotional associations for a place"""
        emotions = defaultdict(float)
        
        for memory in memories:
            if hasattr(memory, 'emotional_context') and memory.emotional_context:
                for emotion, score in memory.emotional_context.items():
                    emotions[emotion] += score
        
        # Normalize by number of memories
        if memories:
            for emotion in emotions:
                emotions[emotion] /= len(memories)
        
        return dict(emotions)
    
    def _calculate_place_significance(self, memories: List[EnhancedLLEntry]) -> float:
        """Calculate narrative significance of a place"""
        if not memories:
            return 0.0
        
        # Base significance on visit frequency and memory quality
        visit_frequency_score = min(len(memories) / 10.0, 1.0)  # Cap at 10 visits
        
        # Average narrative significance of memories
        narrative_scores = []
        for memory in memories:
            if hasattr(memory, 'narrative_significance'):
                narrative_scores.append(memory.narrative_significance)
            else:
                narrative_scores.append(0.5)  # Default
        
        avg_narrative_score = sum(narrative_scores) / len(narrative_scores)
        
        # Combine scores
        return (visit_frequency_score * 0.4 + avg_narrative_score * 0.6)
    
    def _extract_coordinates(self, memories: List[EnhancedLLEntry]) -> Optional[Tuple[float, float]]:
        """Extract coordinates from memories"""
        for memory in memories:
            if hasattr(memory, 'lat_lon') and memory.lat_lon:
                if isinstance(memory.lat_lon, list) and len(memory.lat_lon) > 0:
                    coord = memory.lat_lon[0]
                    if isinstance(coord, (list, tuple)) and len(coord) >= 2:
                        return (float(coord[0]), float(coord[1]))
        
        return None
    
    def _analyze_temporal_patterns(self, memories: List[EnhancedLLEntry]) -> List[Dict[str, Any]]:
        """Analyze temporal patterns of visits"""
        patterns = []
        
        # Group by time periods
        timestamps = [self._get_memory_timestamp(m) for m in memories]
        
        # Simple pattern: frequency by month
        month_counts = defaultdict(int)
        for ts in timestamps:
            month_key = f"{ts.year}-{ts.month:02d}"
            month_counts[month_key] += 1
        
        for month, count in month_counts.items():
            patterns.append({
                'period': month,
                'visit_count': count,
                'pattern_type': 'monthly'
            })
        
        return patterns
    
    def _select_representative_memories(self, memories: List[EnhancedLLEntry]) -> List[EnhancedLLEntry]:
        """Select most representative memories for a place"""
        # Sort by narrative significance and select top memories
        scored_memories = []
        
        for memory in memories:
            score = 0.5  # Default score
            if hasattr(memory, 'narrative_significance'):
                score = memory.narrative_significance
            
            # Boost score for memories with rich content
            if hasattr(memory, 'text') and memory.text and len(memory.text) > 50:
                score += 0.1
            
            if hasattr(memory, 'image_paths') and memory.image_paths:
                score += 0.1
            
            scored_memories.append((score, memory))
        
        # Sort by score and take top 3
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for score, memory in scored_memories[:3]]
    
    def _create_narrative_layers(self, memories: List[EnhancedLLEntry]) -> List[Dict[str, Any]]:
        """Create narrative layers for location exploration"""
        layers = []
        
        # Temporal layer
        temporal_layer = {
            'type': 'temporal',
            'title': 'Your Journey Through Time',
            'description': f'How your relationship with this place evolved across {len(memories)} visits',
            'data': self._create_temporal_narrative_data(memories)
        }
        layers.append(temporal_layer)
        
        # Emotional layer
        emotional_layer = {
            'type': 'emotional',
            'title': 'Emotional Landscape',
            'description': 'The feelings and experiences associated with this place',
            'data': self._create_emotional_narrative_data(memories)
        }
        layers.append(emotional_layer)
        
        # Social layer
        social_layer = {
            'type': 'social',
            'title': 'People and Connections',
            'description': 'The relationships and social experiences at this location',
            'data': self._create_social_narrative_data(memories)
        }
        layers.append(social_layer)
        
        return layers
    
    def _generate_temporal_stories(self, memories: List[EnhancedLLEntry]) -> List[Story]:
        """Generate temporal stories for a location"""
        # This would integrate with the story generation service
        # For now, return a placeholder structure
        stories = []
        
        # Group memories by time periods
        sorted_memories = sorted(memories, key=lambda m: self._get_memory_timestamp(m))
        
        if len(sorted_memories) >= 3:
            # Create a simple temporal story
            story = Story(
                id=f"location_story_{hash(str(sorted_memories))}",
                title=f"Your Story at This Place",
                narrative_mode='chronological',
                chapters=[],
                source_memory_ids=[m.id if hasattr(m, 'id') else str(hash(m.text or '')) 
                                 for m in sorted_memories],
                created_at=datetime.now()
            )
            
            # Create simple chapters
            for i, memory in enumerate(sorted_memories[:3]):
                chapter = Chapter(
                    id=f"chapter_{i}",
                    title=f"Visit {i+1}",
                    narrative_text=memory.text[:100] + "..." if memory.text and len(memory.text) > 100 
                                 else memory.text or "A meaningful moment at this place.",
                    media_elements=[],
                    duration_seconds=30,
                    emotional_tone="reflective"
                )
                story.chapters.append(chapter)
            
            stories.append(story)
        
        return stories
    
    def _create_emotional_timeline(self, memories: List[EnhancedLLEntry]) -> List[Dict[str, Any]]:
        """Create emotional timeline for location"""
        timeline = []
        
        for memory in sorted(memories, key=lambda m: self._get_memory_timestamp(m)):
            timestamp = self._get_memory_timestamp(memory)
            
            emotions = {}
            if hasattr(memory, 'emotional_context') and memory.emotional_context:
                emotions = memory.emotional_context
            
            timeline.append({
                'timestamp': timestamp.isoformat(),
                'emotions': emotions,
                'memory_id': memory.id if hasattr(memory, 'id') else str(hash(memory.text or ''))
            })
        
        return timeline
    
    def _analyze_relationship_evolution(self, memories: List[EnhancedLLEntry]) -> Dict[str, Any]:
        """Analyze how relationship with place evolved"""
        if not memories:
            return {}
        
        sorted_memories = sorted(memories, key=lambda m: self._get_memory_timestamp(m))
        
        first_memory = sorted_memories[0]
        last_memory = sorted_memories[-1]
        
        return {
            'first_impression': first_memory.text[:100] if first_memory.text else "Initial visit",
            'recent_experience': last_memory.text[:100] if last_memory.text else "Recent visit",
            'evolution_summary': f"Visited {len(memories)} times over {(self._get_memory_timestamp(last_memory) - self._get_memory_timestamp(first_memory)).days} days",
            'relationship_trend': 'positive' if len(memories) > 2 else 'neutral'
        }
    
    def _find_connected_journeys(self, location_id: str) -> List[str]:
        """Find journeys that include this location"""
        connected = []
        
        for journey_id, journey in self.journey_narratives.items():
            if location_id in journey.places:
                connected.append(journey_id)
        
        return connected
    
    def _detect_journey_segments(self, sorted_memories: List[EnhancedLLEntry]) -> List[List[EnhancedLLEntry]]:
        """Detect journey segments from sorted memories"""
        segments = []
        current_segment = []
        
        window_days = self.narrative_config['journey_detection_window_days']
        
        for memory in sorted_memories:
            if not current_segment:
                current_segment.append(memory)
            else:
                last_timestamp = self._get_memory_timestamp(current_segment[-1])
                current_timestamp = self._get_memory_timestamp(memory)
                
                # If memories are within the window, add to current segment
                if (current_timestamp - last_timestamp).days <= window_days:
                    current_segment.append(memory)
                else:
                    # Start new segment
                    if len(current_segment) >= 2:
                        segments.append(current_segment)
                    current_segment = [memory]
        
        # Add final segment
        if len(current_segment) >= 2:
            segments.append(current_segment)
        
        return segments
    
    def _create_journey_narrative(self, journey_id: str, memories: List[EnhancedLLEntry], 
                                journey_type: str) -> Optional[JourneyNarrative]:
        """Create a journey narrative from memories"""
        if len(memories) < 2:
            return None
        
        # Extract places
        places = []
        for memory in memories:
            place = self._extract_place_from_memory(memory)
            if place and place != "unknown" and place not in places:
                places.append(place)
        
        if len(places) < 2:
            return None
        
        # Create narrative text
        narrative_text = self._generate_journey_narrative_text(memories, places, journey_type)
        
        # Get temporal span
        timestamps = [self._get_memory_timestamp(m) for m in memories]
        temporal_span = (min(timestamps), max(timestamps))
        
        # Create emotional arc
        emotional_arc = self._create_emotional_arc(memories)
        
        return JourneyNarrative(
            journey_id=journey_id,
            title=f"Journey through {', '.join(places[:3])}{'...' if len(places) > 3 else ''}",
            places=places,
            narrative_text=narrative_text,
            temporal_span=temporal_span,
            journey_type=journey_type,
            emotional_arc=emotional_arc
        )
    
    def _generate_journey_narrative_text(self, memories: List[EnhancedLLEntry], 
                                       places: List[str], journey_type: str) -> str:
        """Generate narrative text for a journey"""
        if journey_type == 'travel':
            return f"A journey that took you through {len(places)} places, from {places[0]} to {places[-1]}, creating lasting memories along the way."
        elif journey_type == 'exploration':
            return f"An exploration of {len(places)} different locations, discovering new experiences and perspectives."
        else:
            return f"A meaningful journey connecting {len(places)} places in your life story."
    
    def _create_emotional_arc(self, memories: List[EnhancedLLEntry]) -> List[Dict[str, Any]]:
        """Create emotional arc for journey"""
        arc = []
        
        for i, memory in enumerate(memories):
            emotions = {}
            if hasattr(memory, 'emotional_context') and memory.emotional_context:
                emotions = memory.emotional_context
            
            arc.append({
                'sequence': i,
                'emotions': emotions,
                'intensity': sum(emotions.values()) / len(emotions) if emotions else 0.5
            })
        
        return arc
    
    def _get_enhanced_location_data(self, location: str) -> Dict[str, Any]:
        """Get enhanced location data using geo helper"""
        try:
            # Use existing geo helper for location enrichment
            location_obj = self.geo_helper.geocode(location)
            
            if location_obj:
                return {
                    'name': location_obj.address,
                    'coordinates': (location_obj.latitude, location_obj.longitude),
                    'raw_data': location_obj.raw
                }
        except Exception as e:
            self.logger.warning(f"Failed to get enhanced location data: {e}")
        
        return {'name': location}
    
    def _extract_semantic_location_context(self, memory: EnhancedLLEntry) -> Dict[str, Any]:
        """Extract semantic context about location from memory"""
        context = {}
        
        if hasattr(memory, 'text') and memory.text:
            text_lower = memory.text.lower()
            
            # Detect activity types
            activities = []
            activity_keywords = {
                'dining': ['restaurant', 'cafe', 'dinner', 'lunch', 'food', 'eating'],
                'recreation': ['park', 'beach', 'hiking', 'walking', 'playing'],
                'work': ['office', 'meeting', 'work', 'conference', 'business'],
                'social': ['friends', 'family', 'party', 'gathering', 'celebration'],
                'travel': ['hotel', 'airport', 'vacation', 'trip', 'visiting']
            }
            
            for activity, keywords in activity_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    activities.append(activity)
            
            context['activities'] = activities
        
        return context
    
    def _calculate_location_significance(self, memory: EnhancedLLEntry) -> float:
        """Calculate narrative significance of location in memory"""
        significance = 0.5  # Base significance
        
        # Boost for explicit location mentions
        if hasattr(memory, 'location') and memory.location:
            significance += 0.2
        
        # Boost for rich text content
        if hasattr(memory, 'text') and memory.text and len(memory.text) > 50:
            significance += 0.1
        
        # Boost for media content
        if hasattr(memory, 'image_paths') and memory.image_paths:
            significance += 0.1
        
        return min(significance, 1.0)
    
    def _extract_emotional_associations(self, memory: EnhancedLLEntry) -> Dict[str, float]:
        """Extract emotional associations with location"""
        if hasattr(memory, 'emotional_context') and memory.emotional_context:
            return memory.emotional_context
        
        # Default neutral emotions
        return {'neutral': 0.5}
    
    def _get_places_in_bounds(self, bounds: Dict[str, float]) -> List[str]:
        """Get places within geographic bounds"""
        # For now, return all known places
        # In a real implementation, this would filter by coordinates
        return list(self.place_profiles.keys())
    
    def _generate_place_story_preview(self, profile: PlaceProfile) -> str:
        """Generate a short story preview for a place"""
        return f"You've visited {profile.name} {profile.visit_count} times, creating meaningful memories from {profile.first_visit.strftime('%B %Y')} to {profile.last_visit.strftime('%B %Y')}."
    
    def _create_temporal_narrative_data(self, memories: List[EnhancedLLEntry]) -> Dict[str, Any]:
        """Create temporal narrative data"""
        sorted_memories = sorted(memories, key=lambda m: self._get_memory_timestamp(m))
        
        return {
            'timeline': [
                {
                    'timestamp': self._get_memory_timestamp(m).isoformat(),
                    'summary': m.text[:50] + "..." if m.text and len(m.text) > 50 else m.text or "A moment in time"
                }
                for m in sorted_memories
            ],
            'span_days': (self._get_memory_timestamp(sorted_memories[-1]) - 
                         self._get_memory_timestamp(sorted_memories[0])).days if len(sorted_memories) > 1 else 0
        }
    
    def _create_emotional_narrative_data(self, memories: List[EnhancedLLEntry]) -> Dict[str, Any]:
        """Create emotional narrative data"""
        all_emotions = defaultdict(list)
        
        for memory in memories:
            if hasattr(memory, 'emotional_context') and memory.emotional_context:
                for emotion, score in memory.emotional_context.items():
                    all_emotions[emotion].append(score)
        
        # Calculate averages
        emotion_averages = {}
        for emotion, scores in all_emotions.items():
            emotion_averages[emotion] = sum(scores) / len(scores)
        
        return {
            'dominant_emotions': emotion_averages,
            'emotional_evolution': 'positive' if len(memories) > 1 else 'stable'
        }
    
    def _create_social_narrative_data(self, memories: List[EnhancedLLEntry]) -> Dict[str, Any]:
        """Create social narrative data"""
        people_mentioned = set()
        
        for memory in memories:
            if hasattr(memory, 'people_relationships'):
                for relationship in memory.people_relationships:
                    people_mentioned.add(relationship.person_id)
            
            if hasattr(memory, 'peopleInImage') and memory.peopleInImage:
                people_mentioned.update(memory.peopleInImage)
        
        return {
            'people_count': len(people_mentioned),
            'people_list': list(people_mentioned),
            'social_context': 'social' if people_mentioned else 'solitary'
        }