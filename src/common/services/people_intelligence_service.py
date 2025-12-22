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

import uuid
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

from src.common.objects.enhanced_llentry import PersonProfile, EnhancedLLEntry
from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector


class InteractionAnalysis:
    """Analysis of interactions with a specific person"""
    
    def __init__(self, person_id: str, person_name: str):
        self.person_id = person_id
        self.person_name = person_name
        self.total_interactions = 0
        self.interaction_timeline: List[datetime] = []
        self.interaction_peaks: List[datetime] = []
        self.shared_contexts: List[str] = []
        self.relationship_phases: List[Dict[str, Any]] = []
        self.representative_photos: List[str] = []


class PeopleIntelligenceService:
    """Service for analyzing and organizing information about people in the user's life"""
    
    def __init__(self):
        self.db = EnhancedPersonalDataDBConnector()
        self._person_cache: Dict[str, PersonProfile] = {}
        self._name_variations: Dict[str, Set[str]] = defaultdict(set)
    
    def detect_people_from_data(self) -> List[str]:
        """Detect and extract people from existing personal data"""
        people_mentions = defaultdict(list)
        
        # Get all entries from the database
        cursor = self.db.cursor.execute("""
            SELECT id, data, imageFileName, data_timestamp 
            FROM personal_data 
            WHERE data IS NOT NULL
            ORDER BY data_timestamp
        """)
        
        for row in cursor.fetchall():
            entry_id, pickled_data, image_filename, timestamp = row
            
            try:
                import pickle
                entry = pickle.loads(pickled_data)
                entry_datetime = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
                
                # Extract people from various fields
                people_in_entry = self._extract_people_from_entry(entry)
                
                for person_name in people_in_entry:
                    people_mentions[person_name].append({
                        'entry_id': entry_id,
                        'timestamp': entry_datetime,
                        'context': self._get_context_from_entry(entry),
                        'image_filename': image_filename
                    })
                    
            except Exception as e:
                print(f"Error processing entry {entry_id}: {e}")
                continue
        
        # Filter out people with too few mentions (likely noise)
        significant_people = {
            name: mentions for name, mentions in people_mentions.items()
            if len(mentions) >= 2  # At least 2 mentions to be considered significant
        }
        
        return list(significant_people.keys())
    
    def _extract_people_from_entry(self, entry) -> Set[str]:
        """Extract people names from an LLEntry object"""
        people = set()
        
        # Check peopleInImage field (for photos)
        if hasattr(entry, 'peopleInImage') and entry.peopleInImage:
            for person in entry.peopleInImage:
                if isinstance(person, str) and len(person.strip()) > 0:
                    people.add(person.strip())
        
        # Check tags for people mentions
        if hasattr(entry, 'tags') and entry.tags:
            for tag in entry.tags:
                if isinstance(tag, str) and self._looks_like_person_name(tag):
                    people.add(tag.strip())
        
        # Check text description for people mentions
        if hasattr(entry, 'textDescription') and entry.textDescription:
            extracted_names = self._extract_names_from_text(entry.textDescription)
            people.update(extracted_names)
        
        # Check captions for people mentions
        if hasattr(entry, 'captions') and entry.captions:
            try:
                if isinstance(entry.captions, str):
                    captions_data = json.loads(entry.captions)
                else:
                    captions_data = entry.captions
                
                if isinstance(captions_data, list):
                    for caption in captions_data:
                        if isinstance(caption, str):
                            extracted_names = self._extract_names_from_text(caption)
                            people.update(extracted_names)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return people
    
    def _looks_like_person_name(self, text: str) -> bool:
        """Heuristic to determine if a string looks like a person's name"""
        if not text or len(text.strip()) < 2:
            return False
        
        text = text.strip()
        
        # Skip if it's all uppercase (likely not a name)
        if text.isupper() and len(text) > 3:
            return False
        
        # Skip if it contains numbers or special characters
        if re.search(r'[0-9@#$%^&*()_+=\[\]{}|;:,.<>?/~`]', text):
            return False
        
        # Skip common non-name words
        non_names = {
            'me', 'myself', 'i', 'you', 'we', 'us', 'they', 'them',
            'photo', 'picture', 'image', 'video', 'post', 'status',
            'home', 'work', 'school', 'family', 'friends', 'party',
            'birthday', 'wedding', 'vacation', 'trip', 'dinner'
        }
        
        if text.lower() in non_names:
            return False
        
        # Must start with capital letter
        if not text[0].isupper():
            return False
        
        # Should be mostly alphabetic
        alpha_ratio = sum(c.isalpha() for c in text) / len(text)
        if alpha_ratio < 0.7:
            return False
        
        return True
    
    def _extract_names_from_text(self, text: str) -> Set[str]:
        """Extract potential person names from text using simple heuristics"""
        if not text:
            return set()
        
        names = set()
        
        # Look for patterns like "with John", "and Sarah", etc.
        patterns = [
            r'\bwith\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
            r'\band\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+and\s+I\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+joined\b',
            r'\bmet\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if self._looks_like_person_name(match):
                    names.add(match.strip())
        
        # Also look for capitalized words that might be names
        words = text.split()
        for i, word in enumerate(words):
            if self._looks_like_person_name(word):
                # Check if it's followed by another capitalized word (full name)
                if i + 1 < len(words) and words[i + 1][0].isupper() and words[i + 1].isalpha():
                    full_name = f"{word} {words[i + 1]}"
                    if self._looks_like_person_name(full_name):
                        names.add(full_name)
                else:
                    names.add(word)
        
        return names
    
    def _get_context_from_entry(self, entry) -> str:
        """Extract context information from an entry"""
        contexts = []
        
        if hasattr(entry, 'type'):
            contexts.append(entry.type)
        
        if hasattr(entry, 'location') and entry.location:
            try:
                if isinstance(entry.location, str):
                    location_data = json.loads(entry.location)
                else:
                    location_data = entry.location
                
                if isinstance(location_data, dict) and 'name' in location_data:
                    contexts.append(f"at {location_data['name']}")
            except (json.JSONDecodeError, TypeError):
                pass
        
        if hasattr(entry, 'tags') and entry.tags:
            for tag in entry.tags[:3]:  # Limit to first 3 tags
                if isinstance(tag, str) and not self._looks_like_person_name(tag):
                    contexts.append(tag)
        
        return ", ".join(contexts) if contexts else "general"
    
    def create_person_profile(self, person_name: str) -> PersonProfile:
        """Create a comprehensive profile for a person"""
        person_id = str(uuid.uuid4())
        
        # Get all mentions of this person
        mentions = self._get_person_mentions(person_name)
        
        if not mentions:
            # Return minimal profile if no mentions found
            profile = PersonProfile(
                id=person_id,
                name=person_name,
                representative_photos=[],
                first_appearance=datetime.now(),
                last_appearance=datetime.now(),
                interaction_peaks=[],
                shared_contexts=[],
                relationship_evolution=[]
            )
            
            # Cache and store the minimal profile
            self._person_cache[person_id] = profile
            self.db.add_person_profile(profile)
            
            return profile
        
        # Sort mentions by timestamp
        mentions.sort(key=lambda x: x['timestamp'])
        
        first_appearance = mentions[0]['timestamp']
        last_appearance = mentions[-1]['timestamp']
        
        # Find representative photos
        representative_photos = []
        for mention in mentions:
            if mention.get('image_filename'):
                representative_photos.append(mention['image_filename'])
                if len(representative_photos) >= 5:  # Limit to 5 representative photos
                    break
        
        # Analyze interaction patterns
        interaction_peaks = self._find_interaction_peaks(mentions)
        
        # Extract shared contexts
        contexts = [mention['context'] for mention in mentions if mention['context']]
        context_counts = Counter(contexts)
        shared_contexts = [context for context, count in context_counts.most_common(10)]
        
        # Analyze relationship evolution
        relationship_evolution = self._analyze_relationship_evolution(mentions)
        
        profile = PersonProfile(
            id=person_id,
            name=person_name,
            representative_photos=representative_photos,
            first_appearance=first_appearance,
            last_appearance=last_appearance,
            interaction_peaks=interaction_peaks,
            shared_contexts=shared_contexts,
            relationship_evolution=relationship_evolution
        )
        
        # Cache the profile
        self._person_cache[person_id] = profile
        
        # Store in database
        self.db.add_person_profile(profile)
        
        return profile
    
    def _get_person_mentions(self, person_name: str) -> List[Dict[str, Any]]:
        """Get all mentions of a specific person from the database"""
        mentions = []
        
        cursor = self.db.cursor.execute("""
            SELECT id, data, imageFileName, data_timestamp 
            FROM personal_data 
            WHERE data IS NOT NULL
            ORDER BY data_timestamp
        """)
        
        for row in cursor.fetchall():
            entry_id, pickled_data, image_filename, timestamp = row
            
            try:
                import pickle
                entry = pickle.loads(pickled_data)
                entry_datetime = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
                
                # Check if this entry mentions the person
                people_in_entry = self._extract_people_from_entry(entry)
                
                if person_name in people_in_entry or any(
                    self._names_match(person_name, mentioned_name) 
                    for mentioned_name in people_in_entry
                ):
                    mentions.append({
                        'entry_id': entry_id,
                        'timestamp': entry_datetime,
                        'context': self._get_context_from_entry(entry),
                        'image_filename': image_filename,
                        'entry': entry
                    })
                    
            except Exception as e:
                print(f"Error processing entry {entry_id}: {e}")
                continue
        
        return mentions
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two names refer to the same person"""
        if name1.lower() == name2.lower():
            return True
        
        # Check if one is a substring of the other (e.g., "John" matches "John Smith")
        name1_parts = name1.lower().split()
        name2_parts = name2.lower().split()
        
        # If one name is contained in the other
        if set(name1_parts).issubset(set(name2_parts)) or set(name2_parts).issubset(set(name1_parts)):
            return True
        
        return False
    
    def _find_interaction_peaks(self, mentions: List[Dict[str, Any]]) -> List[datetime]:
        """Find periods of high interaction with a person"""
        if len(mentions) < 3:
            return []
        
        # Group mentions by month
        monthly_counts = defaultdict(int)
        for mention in mentions:
            month_key = mention['timestamp'].strftime('%Y-%m')
            monthly_counts[month_key] += 1
        
        # Find months with above-average activity
        if not monthly_counts:
            return []
        
        avg_monthly = sum(monthly_counts.values()) / len(monthly_counts)
        peak_months = [
            month for month, count in monthly_counts.items()
            if count > avg_monthly * 1.5  # 50% above average
        ]
        
        # Convert back to datetime objects
        peaks = []
        for month_str in peak_months:
            try:
                peak_date = datetime.strptime(month_str + '-01', '%Y-%m-%d')
                peaks.append(peak_date)
            except ValueError:
                continue
        
        return sorted(peaks)
    
    def _analyze_relationship_evolution(self, mentions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze how the relationship with a person evolved over time"""
        if len(mentions) < 2:
            return []
        
        evolution = []
        
        # Divide timeline into phases
        total_span = mentions[-1]['timestamp'] - mentions[0]['timestamp']
        if total_span.days < 30:  # Less than a month of data
            return [{
                'phase': 'recent',
                'start_date': mentions[0]['timestamp'].isoformat(),
                'end_date': mentions[-1]['timestamp'].isoformat(),
                'interaction_frequency': len(mentions),
                'primary_contexts': list(set(m['context'] for m in mentions))[:3]
            }]
        
        # Create phases based on time periods
        phase_duration = total_span / 3  # Divide into 3 phases
        
        for i in range(3):
            phase_start = mentions[0]['timestamp'] + (phase_duration * i)
            phase_end = mentions[0]['timestamp'] + (phase_duration * (i + 1))
            
            phase_mentions = [
                m for m in mentions 
                if phase_start <= m['timestamp'] < phase_end
            ]
            
            if phase_mentions:
                phase_contexts = [m['context'] for m in phase_mentions]
                context_counts = Counter(phase_contexts)
                
                evolution.append({
                    'phase': f'phase_{i + 1}',
                    'start_date': phase_start.isoformat(),
                    'end_date': phase_end.isoformat(),
                    'interaction_frequency': len(phase_mentions),
                    'primary_contexts': [ctx for ctx, _ in context_counts.most_common(3)]
                })
        
        return evolution
    
    def analyze_relationships(self, person_id: str) -> InteractionAnalysis:
        """Analyze relationships and interaction patterns for a specific person"""
        # Get person profile
        profile = self.get_person_profile(person_id)
        if not profile:
            raise ValueError(f"Person profile not found for ID: {person_id}")
        
        analysis = InteractionAnalysis(person_id, profile.name)
        
        # Get all mentions for detailed analysis
        mentions = self._get_person_mentions(profile.name)
        
        analysis.total_interactions = len(mentions)
        analysis.interaction_timeline = [m['timestamp'] for m in mentions]
        analysis.interaction_peaks = profile.interaction_peaks
        analysis.shared_contexts = profile.shared_contexts
        analysis.relationship_phases = profile.relationship_evolution
        analysis.representative_photos = profile.representative_photos
        
        return analysis
    
    def detect_interaction_patterns(self, person_id: str) -> Dict[str, Any]:
        """Detect patterns in interactions with a specific person"""
        analysis = self.analyze_relationships(person_id)
        
        patterns = {
            'total_interactions': analysis.total_interactions,
            'interaction_frequency': 'regular' if analysis.total_interactions > 10 else 'occasional',
            'peak_periods': len(analysis.interaction_peaks),
            'relationship_duration_days': 0,
            'primary_contexts': analysis.shared_contexts[:5],
            'interaction_trend': 'stable'  # Could be enhanced with more sophisticated analysis
        }
        
        if analysis.interaction_timeline:
            duration = analysis.interaction_timeline[-1] - analysis.interaction_timeline[0]
            patterns['relationship_duration_days'] = duration.days
        
        return patterns
    
    def generate_relationship_summary(self, person_id: str) -> str:
        """Generate a natural language summary of the relationship with a person"""
        analysis = self.analyze_relationships(person_id)
        patterns = self.detect_interaction_patterns(person_id)
        
        if analysis.total_interactions == 0:
            return f"No recorded interactions with {analysis.person_name}."
        
        # Build summary components
        summary_parts = []
        
        # Basic interaction info
        if analysis.total_interactions == 1:
            summary_parts.append(f"You have one recorded interaction with {analysis.person_name}")
        else:
            summary_parts.append(f"You have {analysis.total_interactions} recorded interactions with {analysis.person_name}")
        
        # Timeline info
        if analysis.interaction_timeline:
            first_date = analysis.interaction_timeline[0].strftime('%B %Y')
            last_date = analysis.interaction_timeline[-1].strftime('%B %Y')
            
            if first_date == last_date:
                summary_parts.append(f"from {first_date}")
            else:
                summary_parts.append(f"spanning from {first_date} to {last_date}")
        
        # Context info
        if analysis.shared_contexts:
            top_contexts = analysis.shared_contexts[:3]
            if len(top_contexts) == 1:
                summary_parts.append(f"primarily in the context of {top_contexts[0]}")
            elif len(top_contexts) == 2:
                summary_parts.append(f"primarily in contexts of {top_contexts[0]} and {top_contexts[1]}")
            else:
                context_str = ", ".join(top_contexts[:-1]) + f", and {top_contexts[-1]}"
                summary_parts.append(f"in various contexts including {context_str}")
        
        # Peak periods
        if analysis.interaction_peaks:
            if len(analysis.interaction_peaks) == 1:
                peak_date = analysis.interaction_peaks[0].strftime('%B %Y')
                summary_parts.append(f"with a notable period of increased interaction in {peak_date}")
            else:
                summary_parts.append(f"with {len(analysis.interaction_peaks)} notable periods of increased interaction")
        
        return ". ".join(summary_parts) + "."
    
    def generate_best_of_compilation(self, person_id: str, limit: int = 10) -> Dict[str, Any]:
        """Generate a 'best of us' compilation for a person"""
        profile = self.get_person_profile(person_id)
        if not profile:
            return {'error': f'Person profile not found for ID: {person_id}'}
        
        mentions = self._get_person_mentions(profile.name)
        
        # Sort by various criteria to find "best" moments
        photo_mentions = [m for m in mentions if m.get('image_filename')]
        
        # Select diverse moments across time
        if len(photo_mentions) <= limit:
            selected_moments = photo_mentions
        else:
            # Sample across the timeline
            selected_moments = []
            step = len(photo_mentions) // limit
            for i in range(0, len(photo_mentions), step):
                if len(selected_moments) < limit:
                    selected_moments.append(photo_mentions[i])
        
        compilation = {
            'person_name': profile.name,
            'total_moments': len(mentions),
            'selected_moments': len(selected_moments),
            'moments': []
        }
        
        for moment in selected_moments:
            moment_data = {
                'timestamp': moment['timestamp'].isoformat(),
                'image_filename': moment.get('image_filename'),
                'context': moment['context'],
                'description': getattr(moment.get('entry'), 'textDescription', '') if moment.get('entry') else ''
            }
            compilation['moments'].append(moment_data)
        
        return compilation
    
    def get_person_profile(self, person_id: str) -> Optional[PersonProfile]:
        """Retrieve a person profile by ID"""
        # Check cache first
        if person_id in self._person_cache:
            return self._person_cache[person_id]
        
        # Query database
        cursor = self.db.cursor.execute(
            "SELECT * FROM person_profiles WHERE id = ?", (person_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Reconstruct PersonProfile object
        profile = PersonProfile(
            id=row[0],
            name=row[1],
            representative_photos=json.loads(row[2]) if row[2] else [],
            first_appearance=datetime.fromisoformat(row[3]),
            last_appearance=datetime.fromisoformat(row[4]),
            interaction_peaks=[datetime.fromisoformat(ts) for ts in json.loads(row[5])] if row[5] else [],
            shared_contexts=json.loads(row[6]) if row[6] else [],
            relationship_evolution=json.loads(row[7]) if row[7] else []
        )
        
        # Cache for future use
        self._person_cache[person_id] = profile
        
        return profile
    
    def get_all_people(self) -> List[PersonProfile]:
        """Get all person profiles"""
        profiles = []
        cursor = self.db.cursor.execute("SELECT * FROM person_profiles ORDER BY name")
        
        for row in cursor.fetchall():
            profile = PersonProfile(
                id=row[0],
                name=row[1],
                representative_photos=json.loads(row[2]) if row[2] else [],
                first_appearance=datetime.fromisoformat(row[3]),
                last_appearance=datetime.fromisoformat(row[4]),
                interaction_peaks=[datetime.fromisoformat(ts) for ts in json.loads(row[5])] if row[5] else [],
                shared_contexts=json.loads(row[6]) if row[6] else [],
                relationship_evolution=json.loads(row[7]) if row[7] else []
            )
            profiles.append(profile)
        
        return profiles
    
    def update_person_profile(self, person_id: str, updates: Dict[str, Any]) -> bool:
        """Update a person profile with user modifications"""
        profile = self.get_person_profile(person_id)
        if not profile:
            return False
        
        # Apply updates
        if 'name' in updates:
            profile.name = updates['name']
        
        # Update in database
        self.db.add_person_profile(profile)
        
        # Update cache
        self._person_cache[person_id] = profile
        
        return True
    
    def delete_person_profile(self, person_id: str) -> bool:
        """Delete a person profile"""
        try:
            self.db.execute_write("DELETE FROM person_profiles WHERE id = ?", (person_id,))
            
            # Remove from cache
            if person_id in self._person_cache:
                del self._person_cache[person_id]
            
            return True
        except Exception as e:
            print(f"Error deleting person profile {person_id}: {e}")
            return False
    
    def merge_person_profiles(self, primary_id: str, secondary_id: str) -> bool:
        """Merge two person profiles (combine secondary into primary)"""
        primary_profile = self.get_person_profile(primary_id)
        secondary_profile = self.get_person_profile(secondary_id)
        
        if not primary_profile or not secondary_profile:
            return False
        
        # Merge data
        primary_profile.representative_photos.extend(secondary_profile.representative_photos)
        primary_profile.representative_photos = list(set(primary_profile.representative_photos))  # Remove duplicates
        
        primary_profile.shared_contexts.extend(secondary_profile.shared_contexts)
        primary_profile.shared_contexts = list(set(primary_profile.shared_contexts))
        
        primary_profile.interaction_peaks.extend(secondary_profile.interaction_peaks)
        primary_profile.interaction_peaks = sorted(list(set(primary_profile.interaction_peaks)))
        
        # Update timestamps
        if secondary_profile.first_appearance < primary_profile.first_appearance:
            primary_profile.first_appearance = secondary_profile.first_appearance
        
        if secondary_profile.last_appearance > primary_profile.last_appearance:
            primary_profile.last_appearance = secondary_profile.last_appearance
        
        # Update primary profile
        self.db.add_person_profile(primary_profile)
        
        # Delete secondary profile
        self.delete_person_profile(secondary_id)
        
        return True