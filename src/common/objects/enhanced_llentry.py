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
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from src.common.objects.LLEntry_obj import LLEntry


@dataclass
class PersonRelationship:
    """Represents a relationship between the user and another person"""
    person_id: str
    relationship_type: str
    confidence: float
    first_interaction: datetime
    last_interaction: datetime


class EnhancedLLEntry(LLEntry):
    """Enhanced version of LLEntry with AI-focused fields for narrative generation"""
    
    def __init__(self, type: str, startTime, source: str):
        super().__init__(type, startTime, source)
        
        # Narrative context fields
        self.narrative_significance: float = 0.0
        self.emotional_context: Dict[str, float] = {}
        self.life_phase: str = ""
        
        # People intelligence fields
        self.people_relationships: List[PersonRelationship] = []
        self.social_context: Dict[str, Any] = {}
        
        # Story elements
        self.story_potential: float = 0.0
        self.thematic_tags: List[str] = []
        self.composite_memory_ids: List[str] = []
        
        # AI processing metadata
        self.ai_processed: bool = False
        self.ai_processing_version: str = "1.0"
        self.ai_metadata: Dict[str, Any] = {}
    
    def to_enhanced_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including enhanced fields"""
        base_dict = self.toDict()
        
        # Add enhanced fields
        enhanced_fields = {
            'narrative_significance': self.narrative_significance,
            'emotional_context': self.emotional_context,
            'life_phase': self.life_phase,
            'people_relationships': [asdict(rel) for rel in self.people_relationships],
            'social_context': self.social_context,
            'story_potential': self.story_potential,
            'thematic_tags': self.thematic_tags,
            'composite_memory_ids': self.composite_memory_ids,
            'ai_processed': self.ai_processed,
            'ai_processing_version': self.ai_processing_version,
            'ai_metadata': self.ai_metadata
        }
        
        base_dict.update(enhanced_fields)
        return base_dict
    
    def to_enhanced_json(self) -> str:
        """Convert to JSON including enhanced fields"""
        return json.dumps(self.to_enhanced_dict(), default=str)
    
    @classmethod
    def from_llentry(cls, llentry: LLEntry) -> 'EnhancedLLEntry':
        """Create an EnhancedLLEntry from an existing LLEntry"""
        enhanced = cls(llentry.type, llentry.startTime, llentry.source)
        
        # Copy all attributes from the original LLEntry
        for attr_name in dir(llentry):
            if not attr_name.startswith('_') and hasattr(enhanced, attr_name):
                setattr(enhanced, attr_name, getattr(llentry, attr_name))
        
        return enhanced


@dataclass
class Story:
    """Represents a generated story from personal memories"""
    id: str
    title: str
    narrative_mode: str
    chapters: List['Chapter']
    source_memory_ids: List[str]
    created_at: datetime
    voice_narration_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'narrative_mode': self.narrative_mode,
            'chapters': [chapter.to_dict() for chapter in self.chapters],
            'source_memory_ids': self.source_memory_ids,
            'created_at': self.created_at.isoformat(),
            'voice_narration_path': self.voice_narration_path
        }


@dataclass
class Chapter:
    """Represents a chapter within a story"""
    id: str
    title: str
    narrative_text: str
    media_elements: List[str]  # File paths to media
    duration_seconds: int
    emotional_tone: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PersonProfile:
    """Represents a person profile for people intelligence"""
    id: str
    name: str
    representative_photos: List[str]
    first_appearance: datetime
    last_appearance: datetime
    interaction_peaks: List[datetime]
    shared_contexts: List[str]
    relationship_evolution: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'representative_photos': self.representative_photos,
            'first_appearance': self.first_appearance.isoformat(),
            'last_appearance': self.last_appearance.isoformat(),
            'interaction_peaks': [peak.isoformat() for peak in self.interaction_peaks],
            'shared_contexts': self.shared_contexts,
            'relationship_evolution': self.relationship_evolution
        }


@dataclass
class Gallery:
    """Represents a curated gallery of memories"""
    id: str
    title: str
    description: str
    memory_ids: List[str]
    creation_method: str  # 'thematic', 'prompt', 'manual'
    semantic_ordering: List[int]  # Indices for optimal display order
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'memory_ids': self.memory_ids,
            'creation_method': self.creation_method,
            'semantic_ordering': self.semantic_ordering,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class CompositeMemory:
    """Represents a cluster of related memories"""
    id: str
    theme: str
    constituent_memory_ids: List[str]
    narrative_summary: str
    temporal_span: tuple  # (start_datetime, end_datetime)
    significance_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'theme': self.theme,
            'constituent_memory_ids': self.constituent_memory_ids,
            'narrative_summary': self.narrative_summary,
            'temporal_span': [self.temporal_span[0].isoformat(), self.temporal_span[1].isoformat()],
            'significance_score': self.significance_score
        }