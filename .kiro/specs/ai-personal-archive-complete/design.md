# Design Document

## Overview

The AI-Augmented Personal Archive is a local, single-user system that transforms personal data into intelligent, searchable narratives. The system processes multi-modal data (photos, health records, location data, social media) locally while leveraging cloud AI APIs for machine learning functionality, using a hierarchical AI provider strategy to deliver high-quality insights while managing costs effectively.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Local System"
        subgraph "Client Layer"
            WEB[Web Frontend]
            API_CLIENT[API Client]
        end
        
        subgraph "Application Services"
            STORY[Story Generation Service]
            PEOPLE[People Intelligence Service]
            GALLERY[Gallery Curation Service]
            QA[Enhanced Q&A Service]
            PLACES[Place Analysis Service]
        end
        
        subgraph "Local Data Layer"
            POSTGRES[(Local PostgreSQL)]
            VECTOR[(Local Vector DB)]
            STORAGE[(Local File Storage)]
        end
        
        subgraph "Processing Pipeline"
            INGEST[Data Ingestion]
            PROCESS[Local Processing]
            INDEX[Vector Indexing]
        end
    end
    
    subgraph "External AI APIs"
        OPENAI[OpenAI GPT-4]
        ANTHROPIC[Anthropic Claude-3]
        GOOGLE[Google AI]
    end
    
    WEB --> STORY
    API_CLIENT --> PEOPLE
    STORY --> GALLERY
    PEOPLE --> QA
    GALLERY --> PLACES
    
    STORY -.->|ML Requests Only| OPENAI
    PEOPLE -.->|ML Requests Only| GOOGLE
    GALLERY -.->|ML Requests Only| ANTHROPIC
    QA -.->|ML Requests Only| OPENAI
    PLACES -.->|ML Requests Only| ANTHROPIC
    
    OPENAI -.-> ANTHROPIC
    ANTHROPIC -.-> GOOGLE
    
    STORY --> POSTGRES
    PEOPLE --> POSTGRES
    GALLERY --> POSTGRES
    QA --> VECTOR
    PLACES --> POSTGRES
    
    INGEST --> PROCESS
    PROCESS --> INDEX
    INDEX --> VECTOR
    PROCESS --> STORAGE
```

### Local Docker Compose Architecture

```mermaid
graph TB
    subgraph "Local Docker Compose Services"
        FRONTEND[Frontend Service<br/>React + Enhanced UI<br/>Port: 3000]
        BACKEND[Backend Service<br/>Python FastAPI<br/>Port: 8000]
        AI_SERVICES[AI Services<br/>Multi-Provider Integration<br/>Port: 8001]
        QA_SERVICE[QA Service<br/>RAG + Vector Search<br/>Port: 8002]
        DATABASE[PostgreSQL<br/>Local Data Storage<br/>Port: 5432]
        VECTOR_DB[Vector Database<br/>Local Embeddings<br/>Port: 5433]
    end
    
    subgraph "Local File System"
        DATA_DIR["/home/user/MyData"<br/>Personal Data Storage]
        ENV_FILE[".env"<br/>API Keys & Config]
    end
    
    subgraph "External AI APIs"
        UV[UV Package Manager<br/>Fast Python Deps]
        APIS[AI Provider APIs<br/>OpenAI, Anthropic, Google]
    end
    
    FRONTEND --> BACKEND
    BACKEND --> AI_SERVICES
    AI_SERVICES --> QA_SERVICE
    AI_SERVICES -.->|API Calls Only| APIS
    BACKEND --> DATABASE
    QA_SERVICE --> VECTOR_DB
    
    DATA_DIR --> BACKEND
    DATA_DIR --> AI_SERVICES
    ENV_FILE --> AI_SERVICES
    
    UV -.-> BACKEND
    UV -.-> AI_SERVICES
    UV -.-> QA_SERVICE
```

## Components and Interfaces

### 1. AI Provider Management

```python
class AIProviderManager:
    """Manages hierarchical AI provider strategy"""
    
    def __init__(self):
        self.providers = {
            'openai': OpenAIProvider(priority=1, cost_tier='high', quality='excellent'),
            'anthropic': AnthropicProvider(priority=2, cost_tier='high', quality='excellent'),
            'google': GoogleProvider(priority=3, cost_tier='medium', quality='good'),
            'local': LocalProvider(priority=4, cost_tier='free', quality='basic')
        }
    
    async def generate_text(self, prompt: str, task_type: str) -> str:
        """Generate text using best available provider"""
        
    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze image using vision-capable provider"""
        
    async def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for vector search"""
```

### 2. Local Data Processing Pipeline

```python
class LocalDataProcessor:
    """Processes multi-modal personal data locally"""
    
    def __init__(self, data_path: str = "/home/user/MyData"):
        self.data_path = Path(data_path)
        self.local_db = LocalDatabase()
        
    async def process_facebook_data(self) -> ProcessingResult:
        """Process Facebook export data locally"""
        
    async def process_google_photos(self) -> ProcessingResult:
        """Process Google Photos data locally"""
        
    async def process_apple_health(self) -> ProcessingResult:
        """Process Apple Health export locally"""
        
    async def process_location_data(self) -> ProcessingResult:
        """Process Google Maps/location data locally"""
        
    def ensure_data_privacy(self) -> bool:
        """Ensure all personal data stays local"""
```

### 3. Intelligence Services

```python
class PeopleIntelligenceService:
    """Analyzes people and relationships"""
    
    async def detect_faces(self, photos: List[str]) -> List[PersonProfile]:
        """Detect and cluster faces into person profiles"""
        
    async def analyze_relationships(self, social_data: Dict) -> RelationshipGraph:
        """Analyze social connections and evolution"""
        
    async def generate_person_insights(self, person_id: str) -> PersonInsights:
        """Generate insights about a specific person"""

class StoryGenerationService:
    """Creates AI-generated narratives"""
    
    async def generate_chronological_story(self, timeframe: DateRange) -> Story:
        """Generate chronological life narrative"""
        
    async def generate_thematic_story(self, theme: str) -> Story:
        """Generate story around specific theme"""
        
    async def generate_people_story(self, person_ids: List[str]) -> Story:
        """Generate story focused on relationships"""

class GalleryCurationService:
    """Creates intelligent photo galleries"""
    
    async def create_thematic_gallery(self, theme: str) -> Gallery:
        """Create gallery based on theme"""
        
    async def create_natural_language_gallery(self, description: str) -> Gallery:
        """Create gallery from natural language description"""
        
    async def suggest_galleries(self, user_data: UserData) -> List[GallerySuggestion]:
        """Suggest potential galleries based on data analysis"""
```

### 4. Enhanced Q&A System

```python
class EnhancedQAService:
    """Conversational memory access with RAG"""
    
    def __init__(self, vector_db: VectorDatabase):
        self.vector_db = vector_db
        self.conversation_context = ConversationContext()
        
    async def answer_question(self, question: str, user_id: str) -> QAResponse:
        """Answer question using RAG and conversation context"""
        
    async def get_related_memories(self, query: str) -> List[Memory]:
        """Find related memories using vector similarity"""
        
    async def maintain_context(self, question: str, answer: str):
        """Maintain conversation context across turns"""
```

## Data Models

### Core Data Models

```python
@dataclass
class PersonProfile:
    id: str
    name: Optional[str]
    representative_photos: List[str]
    face_encodings: List[np.ndarray]  # Stored locally
    interaction_timeline: List[Interaction]
    relationship_strength: float
    privacy_level: PrivacyLevel

@dataclass
class Story:
    id: str
    title: str
    narrative_mode: NarrativeMode
    chapters: List[Chapter]
    media_references: List[str]  # Local file paths
    generated_at: datetime
    quality_score: float

@dataclass
class Gallery:
    id: str
    title: str
    description: str
    theme: str
    photos: List[str]  # Local file paths
    cover_photo: str
    semantic_tags: List[str]
    created_at: datetime

@dataclass
class Memory:
    id: str
    content: str
    timestamp: datetime
    location: Optional[Location]
    people: List[str]
    media: List[str]  # Local file paths
    embedding: np.ndarray  # Stored locally
    confidence: float

@dataclass
class LocalUserData:
    data_sources: List[DataSource]
    processing_status: ProcessingStatus
    privacy_settings: PrivacySettings
    api_usage: APIUsageStats  # Local tracking
    data_path: str  # Local data directory
```

### Local Database Schema

```sql
-- Single user local database
CREATE DATABASE personal_archive_local;

-- Personal data sources
CREATE TABLE data_sources (
    id UUID PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    source_path TEXT NOT NULL,  -- Local file path
    processing_status VARCHAR(20) DEFAULT 'pending',
    processed_at TIMESTAMP
);

-- People profiles (local storage)
CREATE TABLE people (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    representative_photo TEXT,  -- Local file path
    face_encodings JSONB,  -- Stored locally
    interaction_count INTEGER DEFAULT 0,
    relationship_strength DECIMAL(3,2)
);

-- Generated stories
CREATE TABLE stories (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    narrative_mode VARCHAR(20),
    content JSONB,
    local_media_paths JSONB,  -- Local file references
    quality_score DECIMAL(3,2),
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Photo galleries
CREATE TABLE galleries (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    theme VARCHAR(100),
    local_photos JSONB,  -- Local file paths
    created_at TIMESTAMP DEFAULT NOW()
);

-- Local API usage tracking
CREATE TABLE api_usage (
    id UUID PRIMARY KEY,
    provider VARCHAR(50),
    endpoint VARCHAR(100),
    tokens_used INTEGER,
    cost DECIMAL(8,4),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Local memories with embeddings
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    content TEXT,
    timestamp TIMESTAMP,
    location JSONB,
    people JSONB,
    local_media_paths JSONB,  -- Local file references
    embedding VECTOR(1536),  -- Local vector storage
    confidence DECIMAL(3,2)
);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*
### Property Reflection

After reviewing all properties identified in the prework, several areas of redundancy have been identified:

**Redundant Properties Identified:**
- Properties 3.2 and 12.1 both test secure environment variable loading - can be combined
- Properties 3.5, 9.5, and 10.2 all test usage tracking - can be consolidated  
- Properties 2.1, 11.1, 11.2, 11.3, 11.4 all test data processing - can be combined into comprehensive data processing property
- Properties 4.1 and 6.1 both test AI vision analysis - can be consolidated
- Properties 7.2 and 7.5 both test conversation context - can be combined

**Consolidated Properties:**
- Secure credential management (combining 3.2, 12.1, 12.2, 12.3, 12.5)
- Comprehensive usage tracking (combining 3.5, 9.5, 10.2, 10.5)
- Multi-source data processing (combining 2.1, 11.1, 11.2, 11.3, 11.4)
- AI vision analysis (combining 4.1, 6.1)
- Conversation context management (combining 7.2, 7.5)

Property 1: UV package manager integration
*For any* Docker build process, when UV is available, the system should use UV commands instead of pip for all Python dependency installations
**Validates: Requirements 1.1**

Property 2: UV fallback mechanism
*For any* dependency installation, when UV is unavailable or fails, the system should gracefully fallback to pip-based installation
**Validates: Requirements 1.2**

Property 3: Installation performance improvement
*For any* dependency installation using UV, the installation time should be at least 50% faster than equivalent pip installation
**Validates: Requirements 1.3**

Property 4: Build reproducibility
*For any* lockfile generation, building from the same lockfile should produce identical dependency versions across different environments
**Validates: Requirements 1.4**

Property 5: Multi-source data processing
*For any* personal data export (Facebook, Google Photos, Apple Health, Google Maps), the system should automatically detect the format and extract all available data types
**Validates: Requirements 2.1, 11.1, 11.2, 11.3, 11.4**

Property 6: Metadata extraction consistency
*For any* photo with metadata, the system should extract all available GPS coordinates, timestamps, and tagged people information
**Validates: Requirements 2.2**

Property 7: File path resolution across formats
*For any* media file reference in different export formats, the system should successfully resolve and locate the actual file
**Validates: Requirements 2.5**

Property 8: Secure local credential management
*For any* API credential requirement, the system should load credentials only from secure local environment variables, never exposing them in code, logs, or client components
**Validates: Requirements 3.2, 12.1, 12.2, 12.3, 12.5**

Property 9: Provider hierarchy adherence
*For any* AI processing task, the system should attempt providers in quality-priority order (GPT-4, Claude-3, Google) before failing
**Validates: Requirements 3.1, 3.4**

Property 10: Local usage tracking
*For any* API call made, the system should log usage metrics including provider and cost for local monitoring and analytics
**Validates: Requirements 3.5, 9.5**

Property 11: AI vision analysis
*For any* photo processed, the system should use multimodal AI to detect faces, analyze content, and extract semantic information
**Validates: Requirements 4.1, 6.1**

Property 12: Person profile generation
*For any* detected person, the system should create a profile with representative photos, interaction timeline, and relationship data
**Validates: Requirements 4.2**

Property 13: Story generation with context
*For any* story generation request, the system should create narratives that include relevant photos, locations, people, and temporal context
**Validates: Requirements 5.1, 5.3**

Property 14: Multiple narrative modes
*For any* story generation, the system should support chronological, thematic, people-centered, and place-centered narrative modes
**Validates: Requirements 5.2**

Property 15: Natural language gallery creation
*For any* natural language gallery description, the system should create appropriate photo collections with semantic ordering and metadata
**Validates: Requirements 6.3, 6.4, 6.5**

Property 16: RAG-based question answering
*For any* user question, the system should use retrieval-augmented generation with vector embeddings to provide contextual responses with confidence scores
**Validates: Requirements 7.1, 7.4**

Property 17: Conversation context management
*For any* multi-turn conversation, the system should maintain context across questions and provide coherent follow-up responses
**Validates: Requirements 7.2, 7.5**

Property 18: Multi-source information synthesis
*For any* complex query, the system should combine information from multiple data sources to provide comprehensive responses
**Validates: Requirements 7.3**

Property 19: Emotional location analysis
*For any* location data, the system should create emotional layers and identify significant time periods using sentiment analysis
**Validates: Requirements 8.1, 8.2**

Property 20: Place-based narrative generation
*For any* location with sufficient data, the system should generate location-specific stories with historical context and journey visualization
**Validates: Requirements 8.3, 8.4**

Property 21: Multi-provider API integration
*For any* AI provider configuration, the system should support OpenAI, Anthropic, Google, and other major providers with automatic retry and rate limit handling
**Validates: Requirements 9.1, 9.3, 9.4**

Property 22: Local data privacy
*For any* personal data processing, the system should ensure all personal data remains stored locally with secure file permissions and no external data transmission except for ML API requests
**Validates: Requirements 10.1, 10.3**

Property 23: Local resource optimization
*For any* system operation, the system should efficiently manage local resources including storage, memory, and API usage without external scaling dependencies
**Validates: Requirements 10.4**

Property 24: Robust error handling
*For any* data parsing operation, the system should implement graceful error handling and format auto-detection without crashing
**Validates: Requirements 11.5**

Property 25: Local credential rotation
*For any* credential rotation requirement, the system should support updating API keys in local environment configuration without service restart or downtime
**Validates: Requirements 12.4**

## Error Handling

### AI Provider Error Handling

```python
class AIProviderError(Exception):
    """Base exception for AI provider errors"""
    pass

class ProviderUnavailableError(AIProviderError):
    """Raised when AI provider is unavailable"""
    pass

class RateLimitExceededError(AIProviderError):
    """Raised when rate limit is exceeded"""
    pass

class InsufficientCreditsError(AIProviderError):
    """Raised when user has insufficient credits"""
    pass

# Error handling strategy
async def handle_ai_request(request: AIRequest) -> AIResponse:
    for provider in get_provider_hierarchy():
        try:
            return await provider.process(request)
        except RateLimitExceededError:
            await asyncio.sleep(calculate_backoff_delay())
            continue
        except ProviderUnavailableError:
            logger.warning(f"Provider {provider.name} unavailable, trying next")
            continue
        except InsufficientCreditsError:
            await notify_user_insufficient_credits(request.user_id)
            continue
    
    raise AIProviderError("All providers exhausted")
```

### Data Processing Error Handling

```python
class DataProcessingError(Exception):
    """Base exception for data processing errors"""
    pass

class UnsupportedFormatError(DataProcessingError):
    """Raised when data format is not supported"""
    pass

class CorruptedDataError(DataProcessingError):
    """Raised when data is corrupted or invalid"""
    pass

# Graceful error handling for data processing
async def process_data_safely(data_path: str, user_id: str) -> ProcessingResult:
    try:
        return await process_data(data_path, user_id)
    except UnsupportedFormatError as e:
        logger.warning(f"Unsupported format for {data_path}: {e}")
        return ProcessingResult(status="skipped", reason="unsupported_format")
    except CorruptedDataError as e:
        logger.error(f"Corrupted data in {data_path}: {e}")
        return ProcessingResult(status="failed", reason="corrupted_data")
    except Exception as e:
        logger.error(f"Unexpected error processing {data_path}: {e}")
        return ProcessingResult(status="error", reason="unexpected_error")
```

## Testing Strategy

### Dual Testing Approach

The system requires both unit testing and property-based testing to ensure comprehensive coverage:

**Unit Testing:**
- Test specific examples and edge cases
- Verify integration points between components
- Test error conditions and boundary cases
- Validate API endpoint responses
- Test database operations and data integrity

**Property-Based Testing:**
- Verify universal properties across all inputs using Hypothesis (Python)
- Test AI provider fallback mechanisms with random failures
- Validate data processing with various export formats
- Test security properties with different credential configurations
- Verify scaling behavior under random load patterns

**Property-Based Testing Configuration:**
- Use Hypothesis library for Python property-based testing
- Configure minimum 100 iterations per property test
- Each property-based test must reference its corresponding design property using format: `**Feature: ai-personal-archive-complete, Property {number}: {property_text}**`
- Each correctness property must be implemented by a single property-based test

**Testing Requirements:**
- Unit tests cover specific examples, edge cases, and error conditions
- Property tests verify universal properties hold across all inputs
- Both types complement each other: unit tests catch concrete bugs, property tests verify general correctness
- All tests must pass before deployment
- Test coverage must exceed 80% for critical components

### Integration Testing

```python
# Example property-based test structure
from hypothesis import given, strategies as st
import pytest

@given(st.text(min_size=1), st.integers(min_value=1, max_value=1000))
def test_story_generation_property(narrative_content: str, user_id: int):
    """
    **Feature: ai-personal-archive-complete, Property 13: Story generation with context**
    For any story generation request, the system should create narratives 
    that include relevant photos, locations, people, and temporal context
    """
    story = generate_story(narrative_content, user_id)
    
    # Property: Generated stories must have required context elements
    assert story.photos is not None
    assert story.locations is not None  
    assert story.people is not None
    assert story.temporal_context is not None
    assert len(story.content) > 0
```

## Performance Considerations

### AI Provider Performance

- **Response Time Targets:**
  - Text generation: < 5 seconds for short responses
  - Image analysis: < 10 seconds per image
  - Story generation: < 30 seconds for full narratives
  - Q&A responses: < 3 seconds for simple queries

- **Throughput Requirements:**
  - Support 100 concurrent users
  - Process 1000 photos per hour per user
  - Handle 50 Q&A queries per minute per user

### Caching Strategy

```python
class AIResponseCache:
    """Cache AI responses to reduce API costs and improve performance"""
    
    def __init__(self):
        self.redis_client = redis.Redis()
        self.cache_ttl = 3600  # 1 hour
        
    async def get_cached_response(self, request_hash: str) -> Optional[str]:
        """Get cached AI response if available"""
        
    async def cache_response(self, request_hash: str, response: str):
        """Cache AI response for future use"""
        
    def generate_request_hash(self, request: AIRequest) -> str:
        """Generate hash for request caching"""
```

## Local Security Considerations

### API Key Management

- All API keys stored in local .env file (never committed to git)
- Environment variables loaded securely at runtime
- No hardcoded credentials in source code
- Local audit logging of API usage without exposing keys
- Rate limiting to prevent accidental API abuse

### Data Privacy

- All personal data remains on local machine
- Only ML requests (text/image analysis) sent to external APIs
- No personal data transmitted to external services
- Local encryption for sensitive data at rest
- Secure file permissions for data directories

### Local Access Control

```python
class LocalSecurityManager:
    """Manage local security and privacy"""
    
    def __init__(self):
        self.data_path = Path(os.getenv('DATA_PATH', './MyData'))
        
    def ensure_secure_permissions(self):
        """Set secure file permissions for local data"""
        os.chmod(self.data_path, 0o700)  # Owner read/write/execute only
        
    def validate_api_request(self, request_data: dict) -> bool:
        """Ensure API requests don't contain personal data"""
        # Check that only processed/anonymized data is sent to APIs
        
    def log_api_usage_securely(self, provider: str, tokens: int, cost: float):
        """Log API usage without exposing credentials or personal data"""
```

## Local Deployment Strategy

### Docker Compose Configuration

```yaml
version: '3.8'
services:
  frontend:
    build: 
      context: .
      dockerfile: Dockerfile
      args:
        - USE_UV=true
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=http://localhost:8000
    ports:
      - "3000:3000"
    volumes:
      - ./MyData:/app/MyData:ro  # Read-only access to personal data
      
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
      args:
        - USE_UV=true
    environment:
      - DATABASE_URL=postgresql://user:pass@database:5432/personal_archive_local
      - DATA_PATH=/app/MyData
    env_file:
      - .env  # Contains API keys securely
    ports:
      - "8000:8000"
    volumes:
      - ./MyData:/app/MyData:rw  # Read-write access for processing
    depends_on:
      - database
      
  ai-services:
    build:
      context: .
      dockerfile: Dockerfile.ai-services
      args:
        - USE_UV=true
    environment:
      - AI_PROVIDER_HIERARCHY=openai,anthropic,google
      - DATA_PATH=/app/MyData
    env_file:
      - .env  # Contains API keys securely
    ports:
      - "8001:8001"
    volumes:
      - ./MyData:/app/MyData:rw
    depends_on:
      - vector-db
      
  qa-service:
    build:
      context: .
      dockerfile: Dockerfile.qa
      args:
        - USE_UV=true
    environment:
      - VECTOR_DB_URL=postgresql://user:pass@vector-db:5432/vector_store
    env_file:
      - .env
    ports:
      - "8002:8002"
    depends_on:
      - vector-db
      
  database:
    image: postgres:15
    environment:
      - POSTGRES_DB=personal_archive_local
      - POSTGRES_USER=archive_user
      - POSTGRES_PASSWORD=secure_local_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
      
  vector-db:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_DB=vector_store
      - POSTGRES_USER=vector_user
      - POSTGRES_PASSWORD=secure_vector_password
    volumes:
      - vector_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"

volumes:
  postgres_data:
  vector_data:
```

### Local Environment Configuration

```bash
# .env.example - Template for local API keys
# Copy to .env and add your actual API keys

# AI Provider API Keys (required for ML functionality)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Local Database Configuration
DATABASE_URL=postgresql://archive_user:secure_local_password@localhost:5432/personal_archive_local
VECTOR_DB_URL=postgresql://vector_user:secure_vector_password@localhost:5433/vector_store

# Local Data Path
DATA_PATH=/home/user/MyData

# AI Provider Configuration
AI_PROVIDER_HIERARCHY=openai,anthropic,google
DEFAULT_MODEL_OPENAI=gpt-4
DEFAULT_MODEL_ANTHROPIC=claude-3-sonnet-20240229
DEFAULT_MODEL_GOOGLE=gemini-pro

# Local Performance Settings
MAX_CONCURRENT_API_CALLS=5
API_TIMEOUT_SECONDS=30
LOCAL_CACHE_TTL_HOURS=24

# Privacy Settings
ENABLE_USAGE_ANALYTICS=true
ENABLE_ERROR_REPORTING=false
KEEP_API_LOGS_DAYS=7
```

## Local Monitoring and Observability

### Local Metrics Collection

```python
class LocalMetricsCollector:
    """Collect system metrics for local monitoring"""
    
    def __init__(self):
        self.metrics_file = Path('./logs/metrics.json')
        
    def record_ai_request(self, provider: str, duration: float, success: bool, cost: float):
        """Record AI request metrics locally"""
        
    def record_data_processing(self, data_type: str, records_processed: int, duration: float):
        """Record data processing metrics locally"""
        
    def get_usage_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get local usage summary for specified days"""
```

### Local Health Checks

```python
@app.get("/health")
async def local_health_check():
    """Local system health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": await check_local_database_health(),
            "vector_db": await check_local_vector_db_health(),
            "ai_providers": await check_ai_providers_availability(),
            "data_storage": await check_local_storage_health(),
            "api_keys": await check_api_keys_validity()
        },
        "local_stats": {
            "data_processed": await get_processed_data_count(),
            "api_calls_today": await get_todays_api_usage(),
            "storage_used": await get_storage_usage()
        }
    }
    
    if any(not service["healthy"] for service in health_status["services"].values()):
        health_status["status"] = "degraded"
        
    return health_status
```

This updated design now properly reflects a local, single-user system that:

- **Runs entirely locally** using Docker Compose
- **Stores all personal data locally** with secure permissions
- **Uses AI APIs only for ML functionality** (no personal data transmitted)
- **Manages API keys securely** through local environment variables
- **Provides local monitoring and health checks**
- **Maintains privacy** by keeping all personal data on the user's machine
- **Supports UV package management** with pip fallback
- **Includes comprehensive local security measures**