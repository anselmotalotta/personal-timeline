"""
AI-Powered People Intelligence Service
Uses AI vision APIs for face detection and relationship analysis
"""
import logging
import json
import sqlite3
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import numpy as np
from collections import defaultdict, Counter

from .providers import provider_manager
from .config import config

logger = logging.getLogger(__name__)

@dataclass
class PersonProfile:
    """Person profile with face encodings and interaction data"""
    id: str
    name: Optional[str]
    representative_photos: List[str]
    face_encodings: List[List[float]]  # Stored as lists for JSON serialization
    interaction_timeline: List[Dict[str, Any]]
    relationship_strength: float
    privacy_level: str
    first_seen: datetime
    last_seen: datetime
    photo_count: int

@dataclass
class FaceDetection:
    """Face detection result from AI vision API"""
    photo_path: str
    faces: List[Dict[str, Any]]
    confidence: float
    processing_time: float

@dataclass
class RelationshipInsight:
    """Relationship analysis between people"""
    person1_id: str
    person2_id: str
    relationship_type: str
    strength: float
    shared_photos: int
    interaction_frequency: float
    time_span_days: int

class PeopleIntelligenceService:
    """AI-powered people detection and relationship analysis"""
    
    def __init__(self, data_path: str = "./MyData"):
        self.data_path = Path(data_path)
        self.db_path = self.data_path / "people_intelligence.db"
        self._init_database()
        
    def _init_database(self):
        """Initialize people intelligence database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS people (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    representative_photos TEXT,
                    face_encodings TEXT,
                    interaction_timeline TEXT,
                    relationship_strength REAL,
                    privacy_level TEXT DEFAULT 'private',
                    first_seen TEXT,
                    last_seen TEXT,
                    photo_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS face_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    photo_path TEXT NOT NULL,
                    person_id TEXT,
                    face_encoding TEXT,
                    bounding_box TEXT,
                    confidence REAL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (person_id) REFERENCES people (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person1_id TEXT NOT NULL,
                    person2_id TEXT NOT NULL,
                    relationship_type TEXT,
                    strength REAL,
                    shared_photos INTEGER DEFAULT 0,
                    interaction_frequency REAL DEFAULT 0.0,
                    time_span_days INTEGER DEFAULT 0,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (person1_id) REFERENCES people (id),
                    FOREIGN KEY (person2_id) REFERENCES people (id)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_face_detections_photo ON face_detections(photo_path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_face_detections_person ON face_detections(person_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_persons ON relationships(person1_id, person2_id)")
    
    async def detect_faces(self, photos: List[str]) -> List[FaceDetection]:
        """Detect and cluster faces into person profiles using AI vision APIs"""
        face_detections = []
        
        for photo_path in photos:
            try:
                start_time = datetime.now()
                
                # Use AI provider for face detection
                detection_result = await provider_manager.analyze_image(
                    photo_path, 
                    "Detect and describe all faces in this image. For each face, provide bounding box coordinates and any identifying features."
                )
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Parse AI response to extract face information
                faces = self._parse_face_detection_response(detection_result)
                
                detection = FaceDetection(
                    photo_path=photo_path,
                    faces=faces,
                    confidence=detection_result.get('confidence', 0.8),
                    processing_time=processing_time
                )
                
                face_detections.append(detection)
                
                # Store face detections in database
                await self._store_face_detections(detection)
                
                logger.info(f"Detected {len(faces)} faces in {photo_path}")
                
            except Exception as e:
                logger.error(f"Face detection failed for {photo_path}: {e}")
                continue
        
        # Cluster faces into person profiles
        await self._cluster_faces_into_people(face_detections)
        
        return face_detections
    
    def _parse_face_detection_response(self, ai_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse AI response to extract structured face information"""
        faces = []
        
        # This would parse the AI response to extract face information
        # For now, we'll create a mock response structure
        description = ai_response.get('description', '')
        
        # Simple heuristic: count mentions of "face", "person", "man", "woman", etc.
        face_indicators = ['face', 'person', 'man', 'woman', 'child', 'people']
        face_count = sum(description.lower().count(indicator) for indicator in face_indicators)
        
        # Create mock face detections
        for i in range(min(face_count, 5)):  # Limit to 5 faces per image
            faces.append({
                'id': f"face_{i}",
                'bounding_box': [0.1 + i * 0.2, 0.1, 0.2, 0.3],  # Mock coordinates
                'confidence': 0.8 + (i * 0.05),
                'features': {
                    'age_estimate': 'adult',
                    'gender_estimate': 'unknown',
                    'emotion': 'neutral'
                }
            })
        
        return faces
    
    async def _store_face_detections(self, detection: FaceDetection):
        """Store face detection results in database"""
        with sqlite3.connect(self.db_path) as conn:
            for face in detection.faces:
                conn.execute("""
                    INSERT INTO face_detections 
                    (photo_path, face_encoding, bounding_box, confidence)
                    VALUES (?, ?, ?, ?)
                """, (
                    detection.photo_path,
                    json.dumps(face.get('encoding', [])),
                    json.dumps(face.get('bounding_box', [])),
                    face.get('confidence', 0.0)
                ))
    
    async def _cluster_faces_into_people(self, face_detections: List[FaceDetection]):
        """Cluster detected faces into person profiles using similarity"""
        # This would implement face clustering using embeddings
        # For now, we'll create a simple clustering based on photo co-occurrence
        
        photo_faces = {}
        for detection in face_detections:
            photo_faces[detection.photo_path] = detection.faces
        
        # Simple clustering: group faces that appear in multiple photos together
        face_groups = self._simple_face_clustering(photo_faces)
        
        # Create person profiles from face groups
        for group_id, face_group in enumerate(face_groups):
            person_id = f"person_{group_id}"
            
            # Get representative photos
            representative_photos = list(set(face['photo_path'] for face in face_group if 'photo_path' in face))[:5]
            
            # Calculate interaction timeline
            interaction_timeline = self._build_interaction_timeline(representative_photos)
            
            # Create person profile
            person = PersonProfile(
                id=person_id,
                name=None,  # Would be populated from social media tags
                representative_photos=representative_photos,
                face_encodings=[face.get('encoding', []) for face in face_group],
                interaction_timeline=interaction_timeline,
                relationship_strength=len(representative_photos) / 10.0,  # Simple strength calculation
                privacy_level='private',
                first_seen=min(interaction['timestamp'] for interaction in interaction_timeline) if interaction_timeline else datetime.now(),
                last_seen=max(interaction['timestamp'] for interaction in interaction_timeline) if interaction_timeline else datetime.now(),
                photo_count=len(representative_photos)
            )
            
            # Store person profile
            await self._store_person_profile(person)
    
    def _simple_face_clustering(self, photo_faces: Dict[str, List[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
        """Simple face clustering based on co-occurrence in photos"""
        # This is a simplified clustering approach
        # In production, this would use actual face embeddings and similarity metrics
        
        all_faces = []
        for photo_path, faces in photo_faces.items():
            for face in faces:
                face['photo_path'] = photo_path
                all_faces.append(face)
        
        # Group faces by simple heuristics (this would be replaced with actual face recognition)
        # For now, just create groups based on photo co-occurrence patterns
        groups = []
        used_faces = set()
        
        for i, face in enumerate(all_faces):
            if i in used_faces:
                continue
                
            group = [face]
            used_faces.add(i)
            
            # Find similar faces (mock similarity based on photo proximity)
            for j, other_face in enumerate(all_faces[i+1:], i+1):
                if j in used_faces:
                    continue
                    
                # Mock similarity check
                if self._faces_might_be_same_person(face, other_face):
                    group.append(other_face)
                    used_faces.add(j)
            
            if len(group) >= 1:  # Only create groups with at least 1 face
                groups.append(group)
        
        return groups
    
    def _faces_might_be_same_person(self, face1: Dict[str, Any], face2: Dict[str, Any]) -> bool:
        """Mock similarity check between faces"""
        # This would use actual face embeddings in production
        # For now, use simple heuristics
        
        # If faces are from photos taken close in time, they might be the same person
        # This is a very simplified approach
        return abs(hash(face1['photo_path']) - hash(face2['photo_path'])) % 100 < 20
    
    def _build_interaction_timeline(self, photo_paths: List[str]) -> List[Dict[str, Any]]:
        """Build interaction timeline from photo timestamps"""
        timeline = []
        
        for photo_path in photo_paths:
            # Extract timestamp from photo (would use actual EXIF data)
            # For now, use file modification time
            try:
                from pathlib import Path
                photo_file = Path(photo_path)
                if photo_file.exists():
                    timestamp = datetime.fromtimestamp(photo_file.stat().st_mtime)
                else:
                    timestamp = datetime.now()
                    
                timeline.append({
                    'timestamp': timestamp,
                    'event_type': 'photo',
                    'photo_path': photo_path,
                    'context': 'appeared_in_photo'
                })
            except:
                continue
        
        return sorted(timeline, key=lambda x: x['timestamp'])
    
    async def _store_person_profile(self, person: PersonProfile):
        """Store person profile in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO people 
                (id, name, representative_photos, face_encodings, interaction_timeline, 
                 relationship_strength, privacy_level, first_seen, last_seen, photo_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person.id,
                person.name,
                json.dumps(person.representative_photos),
                json.dumps(person.face_encodings),
                json.dumps(person.interaction_timeline, default=str),
                person.relationship_strength,
                person.privacy_level,
                person.first_seen.isoformat(),
                person.last_seen.isoformat(),
                person.photo_count
            ))
    
    async def analyze_relationships(self, social_data: Dict[str, Any]) -> List[RelationshipInsight]:
        """Analyze social connections and evolution"""
        relationships = []
        
        # Get all people from database
        people = await self.get_all_people()
        
        # Analyze relationships between all pairs of people
        for i, person1 in enumerate(people):
            for person2 in people[i+1:]:
                relationship = await self._analyze_relationship_between_people(person1, person2, social_data)
                if relationship and relationship.strength > 0.1:  # Only include meaningful relationships
                    relationships.append(relationship)
        
        # Store relationships in database
        for relationship in relationships:
            await self._store_relationship(relationship)
        
        return relationships
    
    async def _analyze_relationship_between_people(self, person1: PersonProfile, person2: PersonProfile, social_data: Dict[str, Any]) -> Optional[RelationshipInsight]:
        """Analyze relationship between two people"""
        # Find shared photos
        shared_photos = set(person1.representative_photos) & set(person2.representative_photos)
        
        if not shared_photos:
            return None
        
        # Calculate interaction frequency
        person1_timeline = person1.interaction_timeline
        person2_timeline = person2.interaction_timeline
        
        # Find overlapping time periods
        overlapping_events = 0
        for event1 in person1_timeline:
            for event2 in person2_timeline:
                if abs((event1['timestamp'] - event2['timestamp']).total_seconds()) < 3600:  # Within 1 hour
                    overlapping_events += 1
        
        interaction_frequency = overlapping_events / max(len(person1_timeline), len(person2_timeline), 1)
        
        # Calculate time span
        all_dates = []
        for event in person1_timeline + person2_timeline:
            all_dates.append(event['timestamp'])
        
        if all_dates:
            time_span_days = (max(all_dates) - min(all_dates)).days
        else:
            time_span_days = 0
        
        # Determine relationship type based on interaction patterns
        relationship_type = self._determine_relationship_type(
            len(shared_photos), interaction_frequency, time_span_days
        )
        
        # Calculate relationship strength
        strength = min(1.0, (len(shared_photos) * 0.2) + (interaction_frequency * 0.5) + (min(time_span_days / 365, 1) * 0.3))
        
        return RelationshipInsight(
            person1_id=person1.id,
            person2_id=person2.id,
            relationship_type=relationship_type,
            strength=strength,
            shared_photos=len(shared_photos),
            interaction_frequency=interaction_frequency,
            time_span_days=time_span_days
        )
    
    def _determine_relationship_type(self, shared_photos: int, interaction_frequency: float, time_span_days: int) -> str:
        """Determine relationship type based on interaction patterns"""
        if shared_photos >= 10 and interaction_frequency > 0.5:
            return "close_friend"
        elif shared_photos >= 5 and time_span_days > 365:
            return "long_term_friend"
        elif shared_photos >= 3:
            return "friend"
        elif shared_photos >= 1:
            return "acquaintance"
        else:
            return "unknown"
    
    async def _store_relationship(self, relationship: RelationshipInsight):
        """Store relationship analysis in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO relationships 
                (person1_id, person2_id, relationship_type, strength, shared_photos, 
                 interaction_frequency, time_span_days)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                relationship.person1_id,
                relationship.person2_id,
                relationship.relationship_type,
                relationship.strength,
                relationship.shared_photos,
                relationship.interaction_frequency,
                relationship.time_span_days
            ))
    
    async def generate_person_insights(self, person_id: str) -> Dict[str, Any]:
        """Generate insights about a specific person"""
        person = await self.get_person_by_id(person_id)
        if not person:
            return {"error": "Person not found"}
        
        # Get relationships for this person
        relationships = await self.get_relationships_for_person(person_id)
        
        # Generate insights using AI
        insights_prompt = f"""
        Analyze this person's profile and generate insights:
        - Photos: {person.photo_count}
        - Time span: {(person.last_seen - person.first_seen).days} days
        - Relationships: {len(relationships)}
        - Activity timeline: {len(person.interaction_timeline)} events
        
        Provide insights about their social patterns, activity levels, and relationship dynamics.
        """
        
        try:
            ai_insights = await provider_manager.generate_text(insights_prompt, "person_analysis")
            
            return {
                "person_id": person_id,
                "basic_stats": {
                    "photo_count": person.photo_count,
                    "relationship_count": len(relationships),
                    "activity_span_days": (person.last_seen - person.first_seen).days,
                    "relationship_strength": person.relationship_strength
                },
                "relationships": [
                    {
                        "other_person": rel.person2_id if rel.person1_id == person_id else rel.person1_id,
                        "type": rel.relationship_type,
                        "strength": rel.strength
                    }
                    for rel in relationships
                ],
                "ai_insights": ai_insights,
                "timeline_summary": self._summarize_timeline(person.interaction_timeline)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate insights for person {person_id}: {e}")
            return {
                "person_id": person_id,
                "error": "Failed to generate AI insights",
                "basic_stats": {
                    "photo_count": person.photo_count,
                    "relationship_count": len(relationships)
                }
            }
    
    def _summarize_timeline(self, timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize person's activity timeline"""
        if not timeline:
            return {"total_events": 0}
        
        event_types = Counter(event.get('event_type', 'unknown') for event in timeline)
        
        return {
            "total_events": len(timeline),
            "event_types": dict(event_types),
            "first_activity": timeline[0]['timestamp'].isoformat() if timeline else None,
            "last_activity": timeline[-1]['timestamp'].isoformat() if timeline else None,
            "activity_span_days": (timeline[-1]['timestamp'] - timeline[0]['timestamp']).days if len(timeline) > 1 else 0
        }
    
    async def get_all_people(self) -> List[PersonProfile]:
        """Get all people from database"""
        people = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            results = conn.execute("SELECT * FROM people ORDER BY photo_count DESC").fetchall()
            
            for row in results:
                person = PersonProfile(
                    id=row['id'],
                    name=row['name'],
                    representative_photos=json.loads(row['representative_photos']) if row['representative_photos'] else [],
                    face_encodings=json.loads(row['face_encodings']) if row['face_encodings'] else [],
                    interaction_timeline=json.loads(row['interaction_timeline']) if row['interaction_timeline'] else [],
                    relationship_strength=row['relationship_strength'],
                    privacy_level=row['privacy_level'],
                    first_seen=datetime.fromisoformat(row['first_seen']),
                    last_seen=datetime.fromisoformat(row['last_seen']),
                    photo_count=row['photo_count']
                )
                people.append(person)
        
        return people
    
    async def get_person_by_id(self, person_id: str) -> Optional[PersonProfile]:
        """Get specific person by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            result = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
            
            if not result:
                return None
            
            return PersonProfile(
                id=result['id'],
                name=result['name'],
                representative_photos=json.loads(result['representative_photos']) if result['representative_photos'] else [],
                face_encodings=json.loads(result['face_encodings']) if result['face_encodings'] else [],
                interaction_timeline=json.loads(result['interaction_timeline']) if result['interaction_timeline'] else [],
                relationship_strength=result['relationship_strength'],
                privacy_level=result['privacy_level'],
                first_seen=datetime.fromisoformat(result['first_seen']),
                last_seen=datetime.fromisoformat(result['last_seen']),
                photo_count=result['photo_count']
            )
    
    async def get_relationships_for_person(self, person_id: str) -> List[RelationshipInsight]:
        """Get all relationships for a specific person"""
        relationships = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            results = conn.execute("""
                SELECT * FROM relationships 
                WHERE person1_id = ? OR person2_id = ?
                ORDER BY strength DESC
            """, (person_id, person_id)).fetchall()
            
            for row in results:
                relationship = RelationshipInsight(
                    person1_id=row['person1_id'],
                    person2_id=row['person2_id'],
                    relationship_type=row['relationship_type'],
                    strength=row['strength'],
                    shared_photos=row['shared_photos'],
                    interaction_frequency=row['interaction_frequency'],
                    time_span_days=row['time_span_days']
                )
                relationships.append(relationship)
        
        return relationships
    
    async def update_privacy_settings(self, person_id: str, privacy_level: str) -> bool:
        """Update privacy settings for a person"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE people SET privacy_level = ? WHERE id = ?",
                    (privacy_level, person_id)
                )
            return True
        except Exception as e:
            logger.error(f"Failed to update privacy settings for {person_id}: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get people intelligence service status"""
        with sqlite3.connect(self.db_path) as conn:
            people_count = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
            face_detections_count = conn.execute("SELECT COUNT(*) FROM face_detections").fetchone()[0]
            relationships_count = conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
            
            return {
                "service": "people_intelligence",
                "status": "active",
                "statistics": {
                    "total_people": people_count,
                    "total_face_detections": face_detections_count,
                    "total_relationships": relationships_count
                },
                "database_path": str(self.db_path)
            }

# Global service instance
people_service = PeopleIntelligenceService()