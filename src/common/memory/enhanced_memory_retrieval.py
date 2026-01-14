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
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import sqlite3
import pickle

from src.common.objects.enhanced_llentry import EnhancedLLEntry, CompositeMemory
from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector


@dataclass
class ConversationContext:
    """Manages conversational context for memory retrieval"""
    session_id: str
    query_history: List[str]
    retrieved_memory_ids: List[str]
    current_themes: List[str]
    temporal_focus: Optional[Tuple[datetime, datetime]]
    created_at: datetime
    
    def add_query(self, query: str, memory_ids: List[str], themes: List[str]):
        """Add a query and its results to the conversation context"""
        self.query_history.append(query)
        self.retrieved_memory_ids.extend(memory_ids)
        self.current_themes.extend(themes)
        # Keep only unique themes
        self.current_themes = list(set(self.current_themes))
        
        # Keep only recent queries (last 10)
        if len(self.query_history) > 10:
            self.query_history = self.query_history[-10:]
        
        # Keep only recent memory IDs (last 50)
        if len(self.retrieved_memory_ids) > 50:
            self.retrieved_memory_ids = self.retrieved_memory_ids[-50:]


@dataclass
class MemoryResponse:
    """Enhanced response structure for memory queries"""
    query: str
    narrative_answer: str
    source_memories: List[Dict[str, Any]]
    composite_memories: List[CompositeMemory]
    related_themes: List[str]
    temporal_context: Optional[str]
    confidence_score: float
    conversation_context: ConversationContext


class EnhancedMemoryRetrieval:
    """Enhanced memory retrieval engine with semantic understanding and narrative formatting"""
    
    def __init__(self, data_path: str = None):
        self.db = EnhancedPersonalDataDBConnector()
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        
        # Initialize semantic similarity thresholds
        self.similarity_threshold = 0.7
        self.composite_memory_threshold = 0.6
        
        # Cache for frequently accessed data
        self._memory_cache: Dict[str, EnhancedLLEntry] = {}
        self._theme_cache: Dict[str, List[str]] = {}
    
    def query_memories(self, 
                      query: str, 
                      session_id: str = "default",
                      context: Optional[ConversationContext] = None) -> MemoryResponse:
        """
        Enhanced memory query with semantic understanding and narrative context
        
        Args:
            query: Natural language query about memories
            session_id: Session identifier for conversation context
            context: Optional existing conversation context
            
        Returns:
            MemoryResponse with narrative answer and contextual information
        """
        # Get or create conversation context
        if context is None:
            context = self.conversation_contexts.get(session_id)
            if context is None:
                context = ConversationContext(
                    session_id=session_id,
                    query_history=[],
                    retrieved_memory_ids=[],
                    current_themes=[],
                    temporal_focus=None,
                    created_at=datetime.now()
                )
                self.conversation_contexts[session_id] = context
        
        # Extract semantic themes and temporal context from query
        themes = self._extract_themes_from_query(query)
        temporal_context = self._extract_temporal_context(query)
        
        # Retrieve relevant memories using multiple strategies
        memories = self._retrieve_memories_multi_strategy(query, context, themes, temporal_context)
        
        # Create composite memories from related memories
        composite_memories = self._create_composite_memories(memories, themes)
        
        # Generate narrative response
        narrative_answer = self._generate_narrative_response(query, memories, composite_memories, context)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(memories, themes, query)
        
        # Update conversation context
        memory_ids = [mem.get('id', '') for mem in memories]
        context.add_query(query, memory_ids, themes)
        
        # Format temporal context description
        temporal_desc = self._format_temporal_context(temporal_context) if temporal_context else None
        
        return MemoryResponse(
            query=query,
            narrative_answer=narrative_answer,
            source_memories=memories,
            composite_memories=composite_memories,
            related_themes=themes,
            temporal_context=temporal_desc,
            confidence_score=confidence_score,
            conversation_context=context
        )
    
    def _retrieve_memories_multi_strategy(self, 
                                        query: str, 
                                        context: ConversationContext,
                                        themes: List[str],
                                        temporal_context: Optional[Tuple[datetime, datetime]]) -> List[Dict[str, Any]]:
        """Retrieve memories using multiple complementary strategies"""
        all_memories = []
        
        # Strategy 1: Semantic similarity based on themes
        theme_memories = self._retrieve_by_themes(themes)
        all_memories.extend(theme_memories)
        
        # Strategy 2: Temporal context if specified
        if temporal_context:
            temporal_memories = self._retrieve_by_temporal_context(temporal_context)
            all_memories.extend(temporal_memories)
        
        # Strategy 3: Conversational context (related to previous queries)
        if context.current_themes:
            context_memories = self._retrieve_by_conversation_context(context)
            all_memories.extend(context_memories)
        
        # Strategy 4: Text similarity (fallback to existing QA system approach)
        text_memories = self._retrieve_by_text_similarity(query)
        all_memories.extend(text_memories)
        
        # Deduplicate and rank memories
        unique_memories = self._deduplicate_and_rank_memories(all_memories, query, themes)
        
        # Limit to top 20 memories for performance
        return unique_memories[:20]
    
    def _retrieve_by_themes(self, themes: List[str]) -> List[Dict[str, Any]]:
        """Retrieve memories based on thematic similarity"""
        if not themes:
            return []
        
        memories = []
        
        # Query database for memories with matching thematic tags
        for theme in themes:
            cursor = self.db.search_personal_data(
                "id, data, thematic_tags, narrative_significance",
                {"thematic_tags": f"LIKE '%{theme}%'"}
            )
            
            for row in cursor.fetchall():
                if row[1]:  # data field exists
                    try:
                        entry = pickle.loads(row[1])
                        memory_dict = self._entry_to_memory_dict(entry, row[0])
                        memory_dict['retrieval_strategy'] = 'theme'
                        memory_dict['matching_theme'] = theme
                        memories.append(memory_dict)
                    except Exception as e:
                        print(f"Error unpickling memory {row[0]}: {e}")
        
        return memories
    
    def _retrieve_by_temporal_context(self, temporal_context: Tuple[datetime, datetime]) -> List[Dict[str, Any]]:
        """Retrieve memories within a specific time range"""
        start_time, end_time = temporal_context
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        
        cursor = self.db.search_personal_data(
            "id, data, data_timestamp",
            {
                "data_timestamp": f">= {start_timestamp}",
                "data_timestamp": f"<= {end_timestamp}"
            }
        )
        
        memories = []
        for row in cursor.fetchall():
            if row[1]:  # data field exists
                try:
                    entry = pickle.loads(row[1])
                    memory_dict = self._entry_to_memory_dict(entry, row[0])
                    memory_dict['retrieval_strategy'] = 'temporal'
                    memories.append(memory_dict)
                except Exception as e:
                    print(f"Error unpickling memory {row[0]}: {e}")
        
        return memories
    
    def _retrieve_by_conversation_context(self, context: ConversationContext) -> List[Dict[str, Any]]:
        """Retrieve memories related to current conversation themes"""
        memories = []
        
        # Get memories related to current conversation themes
        for theme in context.current_themes[-5:]:  # Last 5 themes
            theme_memories = self._retrieve_by_themes([theme])
            memories.extend(theme_memories)
        
        # Mark as context-based retrieval
        for memory in memories:
            memory['retrieval_strategy'] = 'conversation_context'
        
        return memories
    
    def _retrieve_by_text_similarity(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve memories using text similarity (fallback method)"""
        # Simple text matching as fallback
        cursor = self.db.search_personal_data("id, data")
        
        memories = []
        query_words = set(query.lower().split())
        
        for row in cursor.fetchall():
            if row[1]:  # data field exists
                try:
                    entry = pickle.loads(row[1])
                    
                    # Check text description for word matches
                    text_desc = getattr(entry, 'textDescription', '').lower()
                    if text_desc:
                        text_words = set(text_desc.split())
                        overlap = len(query_words.intersection(text_words))
                        
                        if overlap > 0:
                            memory_dict = self._entry_to_memory_dict(entry, row[0])
                            memory_dict['retrieval_strategy'] = 'text_similarity'
                            memory_dict['text_overlap_score'] = overlap / len(query_words)
                            memories.append(memory_dict)
                            
                except Exception as e:
                    print(f"Error unpickling memory {row[0]}: {e}")
        
        return memories
    
    def _entry_to_memory_dict(self, entry: Any, memory_id: str) -> Dict[str, Any]:
        """Convert an LLEntry to a memory dictionary"""
        return {
            'id': memory_id,
            'type': getattr(entry, 'type', 'unknown'),
            'startTime': getattr(entry, 'startTime', ''),
            'source': getattr(entry, 'source', ''),
            'textDescription': getattr(entry, 'textDescription', ''),
            'tags': getattr(entry, 'tags', []),
            'imageFilePath': getattr(entry, 'imageFilePath', ''),
            'peopleInImage': getattr(entry, 'peopleInImage', []),
            'narrative_significance': getattr(entry, 'narrative_significance', 0.0),
            'emotional_context': getattr(entry, 'emotional_context', {}),
            'life_phase': getattr(entry, 'life_phase', ''),
            'entry_object': entry
        }
    
    def _deduplicate_and_rank_memories(self, 
                                     memories: List[Dict[str, Any]], 
                                     query: str, 
                                     themes: List[str]) -> List[Dict[str, Any]]:
        """Remove duplicates and rank memories by relevance"""
        # Deduplicate by ID
        seen_ids = set()
        unique_memories = []
        
        for memory in memories:
            memory_id = memory.get('id')
            if memory_id and memory_id not in seen_ids:
                seen_ids.add(memory_id)
                unique_memories.append(memory)
        
        # Rank by relevance score
        for memory in unique_memories:
            memory['relevance_score'] = self._calculate_memory_relevance(memory, query, themes)
        
        # Sort by relevance score (descending)
        unique_memories.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return unique_memories
    
    def _calculate_memory_relevance(self, memory: Dict[str, Any], query: str, themes: List[str]) -> float:
        """Calculate relevance score for a memory"""
        score = 0.0
        
        # Base score from narrative significance
        score += memory.get('narrative_significance', 0.0) * 0.3
        
        # Theme matching bonus
        memory_tags = memory.get('tags', [])
        theme_matches = len(set(themes).intersection(set(memory_tags)))
        score += theme_matches * 0.2
        
        # Text similarity bonus
        if 'text_overlap_score' in memory:
            score += memory['text_overlap_score'] * 0.3
        
        # Retrieval strategy bonus
        strategy_bonuses = {
            'theme': 0.2,
            'temporal': 0.15,
            'conversation_context': 0.1,
            'text_similarity': 0.05
        }
        strategy = memory.get('retrieval_strategy', 'text_similarity')
        score += strategy_bonuses.get(strategy, 0.0)
        
        return score
    
    def _create_composite_memories(self, 
                                 memories: List[Dict[str, Any]], 
                                 themes: List[str]) -> List[CompositeMemory]:
        """Create composite memories by clustering related memories"""
        if len(memories) < 2:
            return []
        
        composite_memories = []
        
        # Group memories by theme
        theme_groups = defaultdict(list)
        for memory in memories:
            memory_themes = memory.get('tags', [])
            for theme in themes:
                if theme in memory_themes:
                    theme_groups[theme].append(memory)
        
        # Create composite memories for themes with multiple memories
        for theme, theme_memories in theme_groups.items():
            if len(theme_memories) >= 2:
                composite = self._create_composite_memory_from_group(theme, theme_memories)
                if composite:
                    composite_memories.append(composite)
        
        return composite_memories
    
    def _create_composite_memory_from_group(self, 
                                          theme: str, 
                                          memories: List[Dict[str, Any]]) -> Optional[CompositeMemory]:
        """Create a composite memory from a group of related memories"""
        if len(memories) < 2:
            return None
        
        # Extract temporal span
        timestamps = []
        for memory in memories:
            start_time = memory.get('startTime')
            if start_time:
                try:
                    timestamps.append(datetime.fromisoformat(start_time))
                except ValueError:
                    continue
        
        if not timestamps:
            return None
        
        temporal_span = (min(timestamps), max(timestamps))
        
        # Generate narrative summary
        narrative_summary = self._generate_composite_narrative(theme, memories)
        
        # Calculate significance score
        significance_scores = [mem.get('narrative_significance', 0.0) for mem in memories]
        avg_significance = sum(significance_scores) / len(significance_scores) if significance_scores else 0.0
        
        return CompositeMemory(
            id=f"composite_{theme}_{len(memories)}_{int(datetime.now().timestamp())}",
            theme=theme,
            constituent_memory_ids=[mem.get('id', '') for mem in memories],
            narrative_summary=narrative_summary,
            temporal_span=temporal_span,
            significance_score=avg_significance
        )
    
    def _generate_composite_narrative(self, theme: str, memories: List[Dict[str, Any]]) -> str:
        """Generate a narrative summary for a composite memory"""
        if not memories:
            return f"A collection of memories related to {theme}."
        
        # Simple narrative generation (can be enhanced with LLM later)
        memory_count = len(memories)
        time_span = ""
        
        # Extract time information
        timestamps = []
        for memory in memories:
            start_time = memory.get('startTime')
            if start_time:
                try:
                    timestamps.append(datetime.fromisoformat(start_time))
                except ValueError:
                    continue
        
        if timestamps:
            timestamps.sort()
            start_date = timestamps[0].strftime("%B %Y")
            end_date = timestamps[-1].strftime("%B %Y")
            if start_date == end_date:
                time_span = f" from {start_date}"
            else:
                time_span = f" spanning from {start_date} to {end_date}"
        
        # Generate basic narrative
        narrative = f"A collection of {memory_count} memories about {theme}{time_span}. "
        
        # Add context from memory descriptions
        descriptions = [mem.get('textDescription', '') for mem in memories[:3]]  # First 3
        descriptions = [desc for desc in descriptions if desc and len(desc) > 10]
        
        if descriptions:
            narrative += "These memories include: " + "; ".join(descriptions[:2]) + "."
        
        return narrative
    
    def _generate_narrative_response(self, 
                                   query: str, 
                                   memories: List[Dict[str, Any]], 
                                   composite_memories: List[CompositeMemory],
                                   context: ConversationContext) -> str:
        """Generate a narrative response to the memory query"""
        if not memories and not composite_memories:
            return f"I couldn't find any memories related to '{query}'. You might want to try a different search term or time period."
        
        response_parts = []
        
        # Start with query acknowledgment
        response_parts.append(f"Based on your question about '{query}', here's what I found in your memories:")
        
        # Add composite memory insights if available
        if composite_memories:
            composite = composite_memories[0]  # Use the first/most relevant composite
            response_parts.append(f"\n{composite.narrative_summary}")
        
        # Add specific memory highlights
        if memories:
            top_memories = memories[:3]  # Top 3 most relevant
            
            response_parts.append(f"\nSpecific memories include:")
            for i, memory in enumerate(top_memories, 1):
                time_str = ""
                if memory.get('startTime'):
                    try:
                        dt = datetime.fromisoformat(memory['startTime'])
                        time_str = f" from {dt.strftime('%B %d, %Y')}"
                    except ValueError:
                        pass
                
                desc = memory.get('textDescription', '')
                if desc:
                    # Truncate long descriptions
                    if len(desc) > 100:
                        desc = desc[:97] + "..."
                    response_parts.append(f"{i}. {desc}{time_str}")
                else:
                    response_parts.append(f"{i}. A {memory.get('type', 'memory')}{time_str}")
        
        # Add conversational context if relevant
        if len(context.query_history) > 1:
            response_parts.append(f"\nThis relates to your previous questions about {', '.join(context.current_themes[-3:])}.")
        
        return "\n".join(response_parts)
    
    def _calculate_confidence_score(self, 
                                  memories: List[Dict[str, Any]], 
                                  themes: List[str], 
                                  query: str) -> float:
        """Calculate confidence score for the response"""
        if not memories:
            return 0.0
        
        # Base confidence from number of memories found
        base_confidence = min(len(memories) / 10.0, 1.0)  # Max confidence at 10+ memories
        
        # Boost confidence for theme matches
        theme_matches = 0
        for memory in memories:
            memory_themes = set(memory.get('tags', []))
            theme_matches += len(memory_themes.intersection(set(themes)))
        
        theme_confidence = min(theme_matches / (len(themes) * 2), 0.3)  # Max 0.3 boost
        
        # Boost confidence for high narrative significance
        significance_scores = [mem.get('narrative_significance', 0.0) for mem in memories]
        avg_significance = sum(significance_scores) / len(significance_scores) if significance_scores else 0.0
        significance_confidence = avg_significance * 0.2  # Max 0.2 boost
        
        total_confidence = base_confidence + theme_confidence + significance_confidence
        return min(total_confidence, 1.0)
    
    def _extract_themes_from_query(self, query: str) -> List[str]:
        """Extract thematic keywords from the query"""
        # Simple keyword extraction (can be enhanced with NLP later)
        query_lower = query.lower()
        
        # Common theme keywords
        theme_keywords = {
            'travel': ['travel', 'trip', 'vacation', 'journey', 'visit', 'flew', 'airport'],
            'food': ['food', 'restaurant', 'meal', 'dinner', 'lunch', 'breakfast', 'cooking'],
            'friends': ['friends', 'friend', 'social', 'party', 'gathering', 'hangout'],
            'family': ['family', 'mom', 'dad', 'parent', 'sibling', 'brother', 'sister'],
            'work': ['work', 'job', 'office', 'meeting', 'project', 'career'],
            'exercise': ['exercise', 'workout', 'gym', 'run', 'running', 'fitness'],
            'photos': ['photo', 'picture', 'image', 'selfie', 'camera'],
            'music': ['music', 'song', 'concert', 'band', 'album', 'listen'],
            'celebration': ['birthday', 'anniversary', 'celebration', 'party', 'holiday']
        }
        
        extracted_themes = []
        for theme, keywords in theme_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                extracted_themes.append(theme)
        
        # Also extract direct nouns/keywords from query
        words = query_lower.split()
        meaningful_words = [word for word in words if len(word) > 3 and word not in 
                          ['what', 'when', 'where', 'who', 'how', 'did', 'was', 'were', 'have', 'had']]
        extracted_themes.extend(meaningful_words[:3])  # Add up to 3 meaningful words
        
        return list(set(extracted_themes))  # Remove duplicates
    
    def _extract_temporal_context(self, query: str) -> Optional[Tuple[datetime, datetime]]:
        """Extract temporal context from the query"""
        query_lower = query.lower()
        now = datetime.now()
        
        # Simple temporal extraction
        if 'last week' in query_lower:
            start = now - timedelta(weeks=1)
            return (start, now)
        elif 'last month' in query_lower:
            start = now - timedelta(days=30)
            return (start, now)
        elif 'last year' in query_lower:
            start = now - timedelta(days=365)
            return (start, now)
        elif 'this year' in query_lower:
            start = datetime(now.year, 1, 1)
            return (start, now)
        elif 'yesterday' in query_lower:
            start = now - timedelta(days=1)
            end = now - timedelta(days=1) + timedelta(hours=23, minutes=59)
            return (start, end)
        
        # Look for specific years
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', query)
        if year_match:
            year = int(year_match.group())
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31, 23, 59, 59)
            return (start, end)
        
        return None
    
    def _format_temporal_context(self, temporal_context: Tuple[datetime, datetime]) -> str:
        """Format temporal context for display"""
        start, end = temporal_context
        
        if start.date() == end.date():
            return f"on {start.strftime('%B %d, %Y')}"
        elif start.year == end.year:
            if start.month == end.month:
                return f"in {start.strftime('%B %Y')}"
            else:
                return f"from {start.strftime('%B')} to {end.strftime('%B %Y')}"
        else:
            return f"from {start.strftime('%B %Y')} to {end.strftime('%B %Y')}"
    
    def find_related_memories(self, 
                            memory_id: str, 
                            relationship_type: str = "semantic") -> List[Dict[str, Any]]:
        """Find memories related to a specific memory"""
        # Get the source memory
        cursor = self.db.search_personal_data("id, data, thematic_tags", {"id": f"= {memory_id}"})
        source_row = cursor.fetchone()
        
        if not source_row or not source_row[1]:
            return []
        
        try:
            source_entry = pickle.loads(source_row[1])
            source_memory = self._entry_to_memory_dict(source_entry, source_row[0])
        except Exception:
            return []
        
        # Find related memories based on relationship type
        if relationship_type == "semantic":
            return self._find_semantically_related_memories(source_memory)
        elif relationship_type == "temporal":
            return self._find_temporally_related_memories(source_memory)
        elif relationship_type == "people":
            return self._find_people_related_memories(source_memory)
        else:
            return []
    
    def _find_semantically_related_memories(self, source_memory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find memories with semantic similarity"""
        source_tags = set(source_memory.get('tags', []))
        if not source_tags:
            return []
        
        related_memories = []
        cursor = self.db.search_personal_data("id, data")
        
        for row in cursor.fetchall():
            if row[0] == source_memory['id'] or not row[1]:
                continue
            
            try:
                entry = pickle.loads(row[1])
                memory_dict = self._entry_to_memory_dict(entry, row[0])
                
                memory_tags = set(memory_dict.get('tags', []))
                overlap = len(source_tags.intersection(memory_tags))
                
                if overlap > 0:
                    memory_dict['semantic_similarity'] = overlap / len(source_tags.union(memory_tags))
                    related_memories.append(memory_dict)
                    
            except Exception:
                continue
        
        # Sort by similarity and return top 10
        related_memories.sort(key=lambda x: x.get('semantic_similarity', 0), reverse=True)
        return related_memories[:10]
    
    def _find_temporally_related_memories(self, source_memory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find memories from around the same time period"""
        source_time_str = source_memory.get('startTime')
        if not source_time_str:
            return []
        
        try:
            source_time = datetime.fromisoformat(source_time_str)
        except ValueError:
            return []
        
        # Look for memories within +/- 7 days
        start_range = source_time - timedelta(days=7)
        end_range = source_time + timedelta(days=7)
        
        return self._retrieve_by_temporal_context((start_range, end_range))
    
    def _find_people_related_memories(self, source_memory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find memories involving the same people"""
        source_people = source_memory.get('peopleInImage', [])
        if not source_people:
            return []
        
        related_memories = []
        cursor = self.db.search_personal_data("id, data")
        
        for row in cursor.fetchall():
            if row[0] == source_memory['id'] or not row[1]:
                continue
            
            try:
                entry = pickle.loads(row[1])
                memory_dict = self._entry_to_memory_dict(entry, row[0])
                
                memory_people = set(memory_dict.get('peopleInImage', []))
                source_people_set = set(source_people)
                
                overlap = len(source_people_set.intersection(memory_people))
                if overlap > 0:
                    memory_dict['people_overlap'] = overlap
                    related_memories.append(memory_dict)
                    
            except Exception:
                continue
        
        # Sort by people overlap and return top 10
        related_memories.sort(key=lambda x: x.get('people_overlap', 0), reverse=True)
        return related_memories[:10]