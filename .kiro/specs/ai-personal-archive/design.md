# AI-Augmented Personal Archive - Design Document

## Overview

This design document outlines the transformation of the existing Personal Timeline application into an AI-Augmented Personal Archive. The current system provides basic data import, timeline visualization, and Q&A capabilities. The revamp will enhance these foundations with sophisticated AI agents, narrative generation, and reflective experiences while preserving the existing data infrastructure and Docker-based architecture.

The enhanced system will maintain the current three-tier architecture (backend ingestion, frontend React app, QA service) while introducing new AI-powered components that transform raw personal data into meaningful stories, insights, and interactive experiences.

## Architecture

### Current System Foundation
The existing architecture provides a solid foundation:
- **Backend**: Python-based ingestion pipeline with SQLite storage
- **Frontend**: React application with timeline visualization and maps
- **QA Service**: Flask-based RAG system with embedding search
- **Data Model**: LLEntry objects with rich metadata and enrichment
- **Infrastructure**: Docker Compose with volume mounting for data persistence

### Enhanced Architecture Components

#### 1. AI Agent Layer (New)
A collection of specialized AI agents that work behind the scenes:
- **Archivist Agent**: Selects and curates relevant memories
- **Narrative Agent**: Creates coherent stories from personal data
- **Editor Agent**: Filters and organizes content for optimal presentation
- **Director Agent**: Sequences media and pacing for storytelling
- **Critic Agent**: Ensures quality, safety, and grounding in actual data

#### 2. Enhanced Memory Engine
Upgrades to the existing QA system:
- **Semantic Memory Retrieval**: Beyond keyword matching to contextual understanding
- **Composite Memory Generation**: Clustering related experiences across time
- **Conversational Context**: Maintaining dialogue state for deeper exploration
- **Multimodal Understanding**: Integrating text, image, and temporal signals

#### 3. Story Generation Pipeline (New)
Transforms static data into narrative experiences:
- **Narrative Modes**: Chronological, thematic, people-centered, place-centered
- **Chapter Generation**: Short, coherent segments with media integration
- **Voice Synthesis**: Text-to-speech with multiple narrator styles
- **Multimodal Composition**: Combining text, images, and audio

#### 4. People Intelligence Module (New)
Analyzes relationships and social patterns:
- **Person Profiling**: Automatic generation of relationship summaries
- **Interaction Analysis**: Detecting patterns and evolution over time
- **Social Graph Construction**: Understanding connections between people
- **Privacy Controls**: User management of people data and visibility

#### 5. Enhanced Gallery System
Replaces basic filtering with intelligent curation:
- **Thematic Galleries**: AI-generated collections based on semantic similarity
- **Prompt-Driven Creation**: Natural language gallery generation
- **Semantic Ordering**: Intelligent arrangement beyond chronological
- **Story Conversion**: Transform galleries into narrative experiences

## Components and Interfaces

### Data Layer Enhancements

#### Enhanced LLEntry Model
Extends the existing LLEntry class with new fields:
```python
class EnhancedLLEntry(LLEntry):
    # Narrative context
    narrative_significance: float
    emotional_context: Dict[str, float]
    life_phase: str
    
    # People intelligence
    people_relationships: List[PersonRelationship]
    social_context: Dict[str, Any]
    
    # Story elements
    story_potential: float
    thematic_tags: List[str]
    composite_memory_ids: List[str]
```

#### Memory Graph Database
Supplement SQLite with graph relationships:
- **Nodes**: Enhanced LLEntry objects, People, Places, Themes
- **Edges**: Temporal, spatial, social, and semantic relationships
- **Indexes**: Multi-dimensional for fast narrative retrieval

### Service Layer Architecture

#### 1. Memory Retrieval Service
Enhances the existing QA engine:
```python
class EnhancedMemoryRetrieval:
    def query_memories(self, query: str, context: ConversationContext) -> MemoryResponse
    def create_composite_memory(self, seed_memories: List[LLEntry]) -> CompositeMemory
    def find_related_memories(self, memory: LLEntry, relationship_type: str) -> List[LLEntry]
```

#### 2. Story Generation Service (New)
```python
class StoryGenerationService:
    def generate_narrative(self, memories: List[LLEntry], mode: NarrativeMode) -> Story
    def create_chapters(self, story: Story) -> List[Chapter]
    def synthesize_voice(self, text: str, narrator_style: str) -> AudioFile
```

#### 3. People Intelligence Service (New)
```python
class PeopleIntelligenceService:
    def analyze_relationships(self, person_id: str) -> PersonProfile
    def detect_interaction_patterns(self, person_id: str) -> InteractionAnalysis
    def generate_relationship_summary(self, person_id: str) -> str
```

#### 4. Gallery Curation Service (New)
```python
class GalleryCurationService:
    def create_thematic_gallery(self, theme: str) -> Gallery
    def generate_from_prompt(self, prompt: str) -> Gallery
    def order_semantically(self, memories: List[LLEntry]) -> List[LLEntry]
```

### API Layer

#### Enhanced REST Endpoints
Building on the existing Flask structure:

```python
# Enhanced memory retrieval
@app.route('/api/memories/query', methods=['POST'])
def enhanced_memory_query()

# Story generation
@app.route('/api/stories/generate', methods=['POST'])
def generate_story()

# People intelligence
@app.route('/api/people/<person_id>/profile', methods=['GET'])
def get_person_profile()

# Gallery management
@app.route('/api/galleries/create', methods=['POST'])
def create_gallery()

# Narrative experiences
@app.route('/api/narratives/<story_id>/chapters', methods=['GET'])
def get_story_chapters()
```

## Data Models

### Core Data Structures

#### Story Model
```python
@dataclass
class Story:
    id: str
    title: str
    narrative_mode: NarrativeMode
    chapters: List[Chapter]
    source_memories: List[str]  # LLEntry IDs
    created_at: datetime
    voice_narration: Optional[str]  # Audio file path
```

#### Chapter Model
```python
@dataclass
class Chapter:
    id: str
    title: str
    narrative_text: str
    media_elements: List[MediaElement]
    duration_seconds: int
    emotional_tone: str
```

#### Composite Memory Model
```python
@dataclass
class CompositeMemory:
    id: str
    theme: str
    constituent_memories: List[str]  # LLEntry IDs
    narrative_summary: str
    temporal_span: Tuple[datetime, datetime]
    significance_score: float
```

#### Person Profile Model
```python
@dataclass
class PersonProfile:
    id: str
    name: str
    representative_photos: List[str]
    first_appearance: datetime
    last_appearance: datetime
    interaction_peaks: List[datetime]
    shared_contexts: List[str]
    relationship_evolution: List[RelationshipPhase]
```

#### Gallery Model
```python
@dataclass
class Gallery:
    id: str
    title: str
    description: str
    memories: List[str]  # LLEntry IDs
    creation_method: str  # 'thematic', 'prompt', 'manual'
    semantic_ordering: List[int]  # Indices for optimal display order
```

### Database Schema Extensions

#### New Tables
```sql
-- Story management
CREATE TABLE stories (
    id TEXT PRIMARY KEY,
    title TEXT,
    narrative_mode TEXT,
    source_memory_ids TEXT,  -- JSON array
    created_at TIMESTAMP,
    voice_narration_path TEXT
);

-- People intelligence
CREATE TABLE person_profiles (
    id TEXT PRIMARY KEY,
    name TEXT,
    first_appearance TIMESTAMP,
    last_appearance TIMESTAMP,
    profile_data TEXT  -- JSON
);

-- Gallery system
CREATE TABLE galleries (
    id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    memory_ids TEXT,  -- JSON array
    creation_method TEXT,
    created_at TIMESTAMP
);

-- Composite memories
CREATE TABLE composite_memories (
    id TEXT PRIMARY KEY,
    theme TEXT,
    constituent_memory_ids TEXT,  -- JSON array
    narrative_summary TEXT,
    significance_score REAL
);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

<function_calls>
<invoke name="prework">
<parameter name="featureName">ai-personal-archive

### Property Reflection

After reviewing all identified properties, several can be consolidated to eliminate redundancy:

**Consolidations:**
- Properties 1.1-1.5 (data compatibility) can be combined into a comprehensive data migration property
- Properties 2.1-2.5 (memory retrieval) can be consolidated into enhanced retrieval capabilities
- Properties 7.1-7.5 (AI agents) can be combined into agent coordination and quality control
- Properties 10.1-10.5 (privacy) can be unified into comprehensive privacy protection

**Unique Properties Retained:**
- Story generation capabilities (3.1-3.5)
- People intelligence functionality (4.1-4.5) 
- Gallery system features (5.1-5.5)
- Place-based exploration (6.1-6.5)
- Self-reflection tools (8.1-8.5)
- Proactive experiences (9.1-9.5)

Property 1: Data Migration and Compatibility
*For any* existing Personal Timeline database with LLEntry objects, the enhanced system should preserve all data while adding new AI capabilities without requiring re-import
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

Property 2: Enhanced Memory Retrieval
*For any* user query about personal memories, the system should provide contextually rich responses with narrative context and composite memory clustering that goes beyond simple keyword matching
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 3: Story Generation Modes
*For any* collection of personal memories, the story generator should create coherent narratives in multiple modes (chronological, thematic, people-centered, place-centered) with proper chapter structure and media integration
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

Property 4: People Intelligence Profiles
*For any* person who appears multiple times in the personal data, the system should generate comprehensive profiles with interaction timelines, shared contexts, and relationship evolution analysis
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

Property 5: Intelligent Gallery Curation
*For any* thematic or prompt-based gallery request, the system should create semantically ordered collections with contextual introductions and story generation options
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

Property 6: Place-Based Narrative Exploration
*For any* location in the personal data, the system should provide story-driven exploration showing temporal and emotional relationships rather than just listing associated entries
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

Property 7: AI Agent Coordination
*For any* user request or content generation task, the AI agents should work together to select, curate, create, sequence, and quality-check outputs while maintaining grounding in actual user data
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

Property 8: Self-Reflection Analysis
*For any* personal writing or behavioral patterns in the data, the system should detect changes over time and present insights as suggestions and patterns rather than definitive assessments
**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

Property 9: Contextual Memory Resurfacing
*For any* user exploration session, the system should suggest relevant memories and generate reflection prompts based on current context rather than simple date-based reminders
**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

Property 10: Privacy and User Control
*For any* personal data processing or content generation, the system should operate locally, default to private mode, avoid diagnostic statements, and provide user controls over sensitive content
**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

## Error Handling

### Data Migration Errors
- **Corrupted LLEntry Objects**: Graceful handling with data recovery attempts
- **Missing Media Files**: Placeholder generation with user notification
- **Schema Incompatibilities**: Automatic migration with rollback capabilities

### AI Processing Errors
- **Model Loading Failures**: Fallback to simpler processing with user notification
- **Generation Timeouts**: Partial results with retry options
- **Quality Check Failures**: Content rejection with explanation to user

### Privacy and Safety Errors
- **Sensitive Content Detection**: Automatic filtering with user override options
- **External Service Calls**: Prevention and logging of any attempted external communication
- **User Control Failures**: Immediate system halt with error reporting

### Resource Management
- **Memory Constraints**: Intelligent batching and processing prioritization
- **Storage Limitations**: Automatic cleanup of temporary files and caching
- **Processing Timeouts**: Graceful degradation with progress preservation

## Testing Strategy

### Dual Testing Approach

The system requires both unit testing and property-based testing to ensure correctness:

**Unit Testing Focus:**
- Integration points between existing and new components
- Specific error conditions and edge cases
- API endpoint functionality
- Database migration procedures
- UI component behavior

**Property-Based Testing Requirements:**
- **Testing Library**: Use Hypothesis for Python components and fast-check for JavaScript/React components
- **Test Configuration**: Minimum 100 iterations per property test to ensure statistical confidence
- **Property Tagging**: Each property-based test must include a comment with the exact format: `**Feature: ai-personal-archive, Property {number}: {property_text}**`
- **Coverage**: Each correctness property must be implemented by exactly one property-based test

**Property-Based Test Examples:**

```python
# Property 1: Data Migration and Compatibility
@given(existing_database=generate_legacy_database())
def test_data_migration_preserves_all_data(existing_database):
    """**Feature: ai-personal-archive, Property 1: Data Migration and Compatibility**"""
    enhanced_system = PersonalArchiveSystem(existing_database)
    enhanced_system.migrate_data()
    
    # Verify all original data is preserved
    assert enhanced_system.count_entries() == existing_database.count_entries()
    assert enhanced_system.verify_data_integrity()

# Property 3: Story Generation Modes  
@given(memories=generate_memory_collection(), mode=sampled_from(NarrativeMode))
def test_story_generation_creates_coherent_narratives(memories, mode):
    """**Feature: ai-personal-archive, Property 3: Story Generation Modes**"""
    story = StoryGenerator().create_story(memories, mode)
    
    assert story.narrative_mode == mode
    assert 1 <= len(story.chapters) <= 20
    assert all(1 <= len(chapter.narrative_text.split('.')) <= 3 for chapter in story.chapters)
    assert story.has_media_integration()
```

**Integration Testing:**
- End-to-end story generation workflows
- Memory retrieval with narrative context
- Gallery creation and story conversion
- People intelligence profile generation
- Cross-component data flow validation

**Performance Testing:**
- Large dataset processing (10k+ memories)
- Concurrent user story generation
- Memory retrieval response times
- AI agent coordination efficiency

**Privacy Testing:**
- Network traffic monitoring (no external calls)
- Data locality verification
- User control functionality
- Sensitive content handling

The testing strategy ensures that both concrete functionality and universal properties are thoroughly validated, providing confidence in the system's correctness and reliability.
