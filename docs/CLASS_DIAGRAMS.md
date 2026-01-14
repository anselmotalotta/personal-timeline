# Class Diagrams - AI Personal Archive

## 🏗️ Core Class Structure

### AI Services Class Hierarchy

```mermaid
classDiagram
    class AIProviderManager {
        +providers: Dict[str, Provider]
        +generate_text(prompt: str) str
        +analyze_image(image_path: str) Dict
        +create_embeddings(texts: List[str]) ndarray
        +test_provider_health(provider: str) bool
    }
    
    class StoryGenerationService {
        +data_path: Path
        +db_path: Path
        +generate_chronological_story(timeframe: Tuple) Story
        +generate_thematic_story(theme: str) Story
        +generate_people_story(person_ids: List[str]) Story
        +_gather_story_data(request: StoryRequest) Dict
        +_create_generation_prompt(request: StoryRequest) str
        +_parse_story_content(content: str) List[StoryChapter]
    }
    
    class PeopleIntelligenceService {
        +data_path: Path
        +db_path: Path
        +detect_faces(photos: List[str]) List[PersonProfile]
        +analyze_relationships(social_data: Dict) RelationshipGraph
        +generate_person_insights(person_id: str) PersonInsights
        +_cluster_faces(face_encodings: List) List[PersonProfile]
    }
    
    class LocalDataProcessor {
        +data_path: Path
        +db_path: Path
        +process_facebook_data() ProcessingResult
        +process_google_photos() ProcessingResult
        +extract_photo_metadata(image_path: str) PhotoMetadata
        +ensure_data_privacy() bool
    }
    
    class HealthMonitor {
        +check_ai_providers() Dict
        +check_database_health() bool
        +check_storage_health() Dict
        +comprehensive_health_check() Dict
    }
    
    AIProviderManager --> StoryGenerationService
    AIProviderManager --> PeopleIntelligenceService
    LocalDataProcessor --> PeopleIntelligenceService
    LocalDataProcessor --> StoryGenerationService
    HealthMonitor --> AIProviderManager
```

### Data Models

```mermaid
classDiagram
    class Story {
        +id: str
        +title: str
        +narrative_mode: NarrativeMode
        +chapters: List[StoryChapter]
        +total_media_references: List[str]
        +quality_score: float
        +generated_at: datetime
    }
    
    class StoryChapter {
        +id: str
        +title: str
        +content: str
        +media_references: List[str]
        +people_mentioned: List[str]
        +locations: List[str]
        +emotional_tone: str
    }
    
    class PersonProfile {
        +id: str
        +name: Optional[str]
        +representative_photos: List[str]
        +face_encodings: List[List[float]]
        +relationship_strength: float
        +photo_count: int
        +first_seen: datetime
        +last_seen: datetime
    }
    
    class PhotoMetadata {
        +file_path: str
        +gps_coordinates: Optional[Tuple[float, float]]
        +timestamp: Optional[datetime]
        +tagged_people: List[str]
        +camera_info: Dict[str, Any]
        +file_size: int
        +dimensions: Tuple[int, int]
    }
    
    class ProcessingResult {
        +success: bool
        +records_processed: int
        +errors: List[str]
        +data_type: str
        +processing_time: float
        +file_paths: List[str]
    }
    
    Story --> StoryChapter
    PersonProfile --> PhotoMetadata
    LocalDataProcessor --> ProcessingResult
```

### Frontend Component Hierarchy

```mermaid
classDiagram
    class EnhancedApp {
        +aiStatus: AIStatus
        +tracks: Array
        +memories: Array
        +activeView: string
        +initializeAIServices() void
        +handleViewChange(view: string) void
    }
    
    class StoryInterface {
        +stories: Array[Story]
        +selectedStory: Story
        +isGenerating: boolean
        +loadExistingStories() void
        +generateStory() void
        +loadFullStory(storyId: string) void
    }
    
    class PeopleDashboard {
        +people: Array[PersonProfile]
        +selectedPerson: PersonProfile
        +loadPeople() void
        +analyzePersonRelationships(personId: string) void
        +generateBestOfUs(personId: string) void
    }
    
    class GalleryBrowser {
        +galleries: Array[Gallery]
        +thematicGalleries: Array[Theme]
        +isCreatingGallery: boolean
        +loadGalleries() void
        +loadThematicGalleries() void
        +createNaturalLanguageGallery(description: string) void
    }
    
    class AIStatusBadge {
        +aiStatus: AIStatus
        +refreshStatus() void
        +getStatusColor() string
        +getStatusMessage() string
    }
    
    class useAIStatus {
        +aiStatus: AIStatus
        +loading: boolean
        +checkAIStatus() void
        +refreshStatus() void
        +isAIAvailable: boolean
    }
    
    EnhancedApp --> StoryInterface
    EnhancedApp --> PeopleDashboard
    EnhancedApp --> GalleryBrowser
    EnhancedApp --> AIStatusBadge
    AIStatusBadge --> useAIStatus
    StoryInterface --> useAIStatus
    PeopleDashboard --> useAIStatus
    GalleryBrowser --> useAIStatus
```

## 🔄 Service Interaction Patterns

### API Request Flow

```mermaid
sequenceDiagram
    participant F as Frontend Component
    participant A as API Router (api.py)
    participant S as Service Class
    participant P as AI Provider
    participant D as Database
    
    F->>A: HTTP Request
    A->>S: Call service method
    S->>D: Query local data
    D-->>S: Return data
    S->>P: AI API call (if needed)
    P-->>S: AI response
    S->>D: Store results
    S-->>A: Return processed data
    A-->>F: HTTP Response
```

### Data Processing Flow

```mermaid
sequenceDiagram
    participant U as User Data Files
    participant L as LocalDataProcessor
    participant P as PeopleIntelligenceService
    participant S as StoryGenerationService
    participant D as Database
    
    U->>L: Raw data files
    L->>L: Extract & validate
    L->>D: Store processed data
    L->>P: Trigger face detection
    P->>D: Store people profiles
    P->>S: Notify data ready
    S->>D: Query for story generation
    D-->>S: Return enriched data
```

## 🎯 Key Design Patterns

### 1. Service Layer Pattern
```python
# Each major functionality is encapsulated in a service class
class StoryGenerationService:
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self._init_database()
    
    async def generate_story(self, request: StoryRequest) -> Story:
        # Business logic here
        pass
```

### 2. Provider Pattern
```python
# AI providers are abstracted behind a common interface
class AIProviderManager:
    def __init__(self):
        self.providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'google': GoogleProvider()
        }
    
    async def generate_text(self, prompt: str) -> str:
        # Try providers in order of preference
        pass
```

### 3. Repository Pattern
```python
# Data access is abstracted through repository-like methods
class LocalDataProcessor:
    def process_facebook_data(self) -> ProcessingResult:
        # Data processing logic
        pass
    
    def extract_photo_metadata(self, image_path: str) -> PhotoMetadata:
        # Metadata extraction logic
        pass
```

### 4. Hook Pattern (Frontend)
```javascript
// Custom hooks encapsulate stateful logic
function useAIStatus() {
    const [aiStatus, setAiStatus] = useState(initialState);
    
    const checkAIStatus = async () => {
        // Status checking logic
    };
    
    return { aiStatus, checkAIStatus, isAIAvailable };
}
```

## 🔧 Extension Points

### Adding New AI Provider
1. Create provider class implementing common interface
2. Add to `AIProviderManager.providers` dict
3. Update configuration in `config.py`
4. Add tests in `tests/unit/test_ai_providers.py`

### Adding New Data Source
1. Add processing method to `LocalDataProcessor`
2. Create data model classes if needed
3. Update database schema if required
4. Add tests in `tests/test_data_processing.py`

### Adding New Frontend Component
1. Create component in `src/frontend/src/components/`
2. Add to `EnhancedApp.js` routing/navigation
3. Create corresponding CSS file
4. Add tests in `tests/component/`

### Adding New API Endpoint
1. Add route to `src/ai_services/api.py`
2. Implement business logic in appropriate service class
3. Add request/response models using Pydantic
4. Add tests in `tests/integration/test_api_endpoints.py`