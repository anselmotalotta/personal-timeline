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

import os
import sys
import inspect
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path for imports
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# Import enhanced memory retrieval
try:
    from src.common.memory.enhanced_memory_retrieval import EnhancedMemoryRetrieval
    ENHANCED_MEMORY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Enhanced memory retrieval unavailable: {e}")
    ENHANCED_MEMORY_AVAILABLE = False
    EnhancedMemoryRetrieval = None

# Import people intelligence service
try:
    from src.common.services.people_intelligence_service import PeopleIntelligenceService
    PEOPLE_INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ People intelligence service unavailable: {e}")
    PEOPLE_INTELLIGENCE_AVAILABLE = False
    PeopleIntelligenceService = None

# Import gallery curation service
try:
    from src.common.services.gallery_curation_service import GalleryCurationService
    GALLERY_CURATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Gallery curation service unavailable: {e}")
    GALLERY_CURATION_AVAILABLE = False
    GalleryCurationService = None

# Import story generation service
try:
    from src.common.services.story_generation_service import StoryGenerationService
    STORY_GENERATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Story generation service unavailable: {e}")
    STORY_GENERATION_AVAILABLE = False
    StoryGenerationService = None

# Import place exploration service
try:
    from src.common.services.place_exploration_service import PlaceExplorationService
    PLACE_EXPLORATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Place exploration service unavailable: {e}")
    PLACE_EXPLORATION_AVAILABLE = False
    PlaceExplorationService = None

# Import original QA engines for fallback
try:
    from qa_engine import QAEngine
    from chatgpt_engine import ChatGPTEngine
    QA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Original QA engines unavailable: {e}")
    QA_AVAILABLE = False
    QAEngine = None
    ChatGPTEngine = None

app = Flask(__name__)
CORS(app)

# Enhanced memory retrieval engine
enhanced_memory_engine = None

# People intelligence service
people_intelligence_service = None

# Gallery curation service
gallery_curation_service = None

# Story generation service
story_generation_service = None

# Place exploration service
place_exploration_service = None

# Original QA engines (for fallback)
qa_engine = None
chatgpt_engine = None


@app.route('/enhanced/launch', methods=['GET'])
def launch_enhanced():
    """Launch the enhanced memory retrieval engine"""
    global enhanced_memory_engine
    
    if not ENHANCED_MEMORY_AVAILABLE:
        return {'error': 'Enhanced memory retrieval unavailable'}, 503
    
    try:
        enhanced_memory_engine = EnhancedMemoryRetrieval()
        return {'message': 'Enhanced memory retrieval engine launched successfully'}
    except Exception as e:
        return {'error': f'Failed to initialize enhanced memory engine: {str(e)}'}, 500


@app.route('/enhanced/query', methods=['POST'])
def enhanced_query():
    """Query memories using the enhanced retrieval system"""
    if not ENHANCED_MEMORY_AVAILABLE or enhanced_memory_engine is None:
        return {'error': 'Enhanced memory retrieval not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return {'error': 'Query parameter required'}, 400
        
        query = data['query']
        session_id = data.get('session_id', 'default')
        
        # Query the enhanced memory system
        response = enhanced_memory_engine.query_memories(query, session_id)
        
        # Convert response to JSON-serializable format
        result = {
            'query': response.query,
            'narrative_answer': response.narrative_answer,
            'source_memories': response.source_memories,
            'composite_memories': [comp.to_dict() for comp in response.composite_memories],
            'related_themes': response.related_themes,
            'temporal_context': response.temporal_context,
            'confidence_score': response.confidence_score,
            'session_id': session_id,
            'method': 'enhanced_retrieval'
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Enhanced query failed: {str(e)}'}, 500


@app.route('/enhanced/related', methods=['POST'])
def find_related_memories():
    """Find memories related to a specific memory"""
    if not ENHANCED_MEMORY_AVAILABLE or enhanced_memory_engine is None:
        return {'error': 'Enhanced memory retrieval not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data or 'memory_id' not in data:
            return {'error': 'memory_id parameter required'}, 400
        
        memory_id = data['memory_id']
        relationship_type = data.get('relationship_type', 'semantic')
        
        # Find related memories
        related_memories = enhanced_memory_engine.find_related_memories(
            memory_id, relationship_type
        )
        
        result = {
            'memory_id': memory_id,
            'relationship_type': relationship_type,
            'related_memories': related_memories,
            'count': len(related_memories)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Related memories query failed: {str(e)}'}, 500


@app.route('/enhanced/context', methods=['GET'])
def get_conversation_context():
    """Get current conversation context for a session"""
    if not ENHANCED_MEMORY_AVAILABLE or enhanced_memory_engine is None:
        return {'error': 'Enhanced memory retrieval not available or not launched'}, 503
    
    try:
        session_id = request.args.get('session_id', 'default')
        
        context = enhanced_memory_engine.conversation_contexts.get(session_id)
        if not context:
            return {'error': f'No context found for session {session_id}'}, 404
        
        result = {
            'session_id': context.session_id,
            'query_history': context.query_history,
            'current_themes': context.current_themes,
            'retrieved_memory_count': len(context.retrieved_memory_ids),
            'created_at': context.created_at.isoformat(),
            'temporal_focus': [
                context.temporal_focus[0].isoformat(),
                context.temporal_focus[1].isoformat()
            ] if context.temporal_focus else None
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Context retrieval failed: {str(e)}'}, 500


# People Intelligence API endpoints

@app.route('/people/launch', methods=['GET'])
def launch_people_intelligence():
    """Launch the people intelligence service"""
    global people_intelligence_service
    
    if not PEOPLE_INTELLIGENCE_AVAILABLE:
        return {'error': 'People intelligence service unavailable'}, 503
    
    try:
        people_intelligence_service = PeopleIntelligenceService()
        return {'message': 'People intelligence service launched successfully'}
    except Exception as e:
        return {'error': f'Failed to initialize people intelligence service: {str(e)}'}, 500


@app.route('/people/detect', methods=['POST'])
def detect_people():
    """Detect people from existing personal data"""
    if not PEOPLE_INTELLIGENCE_AVAILABLE or people_intelligence_service is None:
        return {'error': 'People intelligence service not available or not launched'}, 503
    
    try:
        detected_people = people_intelligence_service.detect_people_from_data()
        
        result = {
            'detected_people': detected_people,
            'count': len(detected_people),
            'method': 'people_detection'
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'People detection failed: {str(e)}'}, 500


@app.route('/people/profiles', methods=['GET'])
def get_all_people():
    """Get all person profiles"""
    if not PEOPLE_INTELLIGENCE_AVAILABLE or people_intelligence_service is None:
        return {'error': 'People intelligence service not available or not launched'}, 503
    
    try:
        profiles = people_intelligence_service.get_all_people()
        
        result = {
            'profiles': [profile.to_dict() for profile in profiles],
            'count': len(profiles)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Failed to retrieve people profiles: {str(e)}'}, 500


@app.route('/people/profiles/<person_id>', methods=['GET'])
def get_person_profile(person_id):
    """Get a specific person profile"""
    if not PEOPLE_INTELLIGENCE_AVAILABLE or people_intelligence_service is None:
        return {'error': 'People intelligence service not available or not launched'}, 503
    
    try:
        profile = people_intelligence_service.get_person_profile(person_id)
        
        if not profile:
            return {'error': f'Person profile not found for ID: {person_id}'}, 404
        
        return jsonify(profile.to_dict())
        
    except Exception as e:
        return {'error': f'Failed to retrieve person profile: {str(e)}'}, 500


@app.route('/people/profiles', methods=['POST'])
def create_person_profile():
    """Create a new person profile"""
    if not PEOPLE_INTELLIGENCE_AVAILABLE or people_intelligence_service is None:
        return {'error': 'People intelligence service not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return {'error': 'Person name required'}, 400
        
        person_name = data['name']
        profile = people_intelligence_service.create_person_profile(person_name)
        
        return jsonify(profile.to_dict()), 201
        
    except Exception as e:
        return {'error': f'Failed to create person profile: {str(e)}'}, 500


@app.route('/people/profiles/<person_id>', methods=['PUT'])
def update_person_profile(person_id):
    """Update a person profile"""
    if not PEOPLE_INTELLIGENCE_AVAILABLE or people_intelligence_service is None:
        return {'error': 'People intelligence service not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data:
            return {'error': 'Update data required'}, 400
        
        success = people_intelligence_service.update_person_profile(person_id, data)
        
        if not success:
            return {'error': f'Person profile not found for ID: {person_id}'}, 404
        
        # Return updated profile
        updated_profile = people_intelligence_service.get_person_profile(person_id)
        return jsonify(updated_profile.to_dict())
        
    except Exception as e:
        return {'error': f'Failed to update person profile: {str(e)}'}, 500


@app.route('/people/profiles/<person_id>', methods=['DELETE'])
def delete_person_profile(person_id):
    """Delete a person profile"""
    if not PEOPLE_INTELLIGENCE_AVAILABLE or people_intelligence_service is None:
        return {'error': 'People intelligence service not available or not launched'}, 503
    
    try:
        success = people_intelligence_service.delete_person_profile(person_id)
        
        if not success:
            return {'error': f'Person profile not found for ID: {person_id}'}, 404
        
        return {'message': f'Person profile {person_id} deleted successfully'}
        
    except Exception as e:
        return {'error': f'Failed to delete person profile: {str(e)}'}, 500


@app.route('/people/profiles/<person_id>/analysis', methods=['GET'])
def analyze_person_relationships(person_id):
    """Analyze relationships and interaction patterns for a person"""
    if not PEOPLE_INTELLIGENCE_AVAILABLE or people_intelligence_service is None:
        return {'error': 'People intelligence service not available or not launched'}, 503
    
    try:
        analysis = people_intelligence_service.analyze_relationships(person_id)
        patterns = people_intelligence_service.detect_interaction_patterns(person_id)
        
        result = {
            'person_id': analysis.person_id,
            'person_name': analysis.person_name,
            'total_interactions': analysis.total_interactions,
            'interaction_timeline': [dt.isoformat() for dt in analysis.interaction_timeline],
            'interaction_peaks': [dt.isoformat() for dt in analysis.interaction_peaks],
            'shared_contexts': analysis.shared_contexts,
            'relationship_phases': analysis.relationship_phases,
            'representative_photos': analysis.representative_photos,
            'patterns': patterns
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Failed to analyze person relationships: {str(e)}'}, 500


@app.route('/people/profiles/<person_id>/summary', methods=['GET'])
def get_relationship_summary(person_id):
    """Get a natural language summary of the relationship with a person"""
    if not PEOPLE_INTELLIGENCE_AVAILABLE or people_intelligence_service is None:
        return {'error': 'People intelligence service not available or not launched'}, 503
    
    try:
        summary = people_intelligence_service.generate_relationship_summary(person_id)
        
        result = {
            'person_id': person_id,
            'summary': summary
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Failed to generate relationship summary: {str(e)}'}, 500


@app.route('/people/profiles/<person_id>/compilation', methods=['GET'])
def get_best_of_compilation(person_id):
    """Generate a 'best of us' compilation for a person"""
    if not PEOPLE_INTELLIGENCE_AVAILABLE or people_intelligence_service is None:
        return {'error': 'People intelligence service not available or not launched'}, 503
    
    try:
        limit = request.args.get('limit', 10, type=int)
        compilation = people_intelligence_service.generate_best_of_compilation(person_id, limit)
        
        return jsonify(compilation)
        
    except Exception as e:
        return {'error': f'Failed to generate best of compilation: {str(e)}'}, 500


@app.route('/people/profiles/<primary_id>/merge/<secondary_id>', methods=['POST'])
def merge_person_profiles(primary_id, secondary_id):
    """Merge two person profiles"""
    if not PEOPLE_INTELLIGENCE_AVAILABLE or people_intelligence_service is None:
        return {'error': 'People intelligence service not available or not launched'}, 503
    
    try:
        success = people_intelligence_service.merge_person_profiles(primary_id, secondary_id)
        
        if not success:
            return {'error': 'Failed to merge profiles - one or both profiles not found'}, 404
        
        # Return the merged profile
        merged_profile = people_intelligence_service.get_person_profile(primary_id)
        return jsonify({
            'message': f'Successfully merged profile {secondary_id} into {primary_id}',
            'merged_profile': merged_profile.to_dict()
        })
        
    except Exception as e:
        return {'error': f'Failed to merge person profiles: {str(e)}'}, 500


# Gallery Curation API endpoints

@app.route('/galleries/launch', methods=['GET'])
def launch_gallery_curation():
    """Launch the gallery curation service"""
    global gallery_curation_service
    
    if not GALLERY_CURATION_AVAILABLE:
        return {'error': 'Gallery curation service unavailable'}, 503
    
    try:
        gallery_curation_service = GalleryCurationService()
        return {'message': 'Gallery curation service launched successfully'}
    except Exception as e:
        return {'error': f'Failed to initialize gallery curation service: {str(e)}'}, 500


@app.route('/galleries/initialize', methods=['POST'])
def initialize_default_galleries():
    """Initialize default thematic galleries to replace basic filtering"""
    if not GALLERY_CURATION_AVAILABLE or gallery_curation_service is None:
        return {'error': 'Gallery curation service not available or not launched'}, 503
    
    try:
        galleries = gallery_curation_service.initialize_default_galleries()
        
        result = {
            'galleries': [gallery.to_dict() for gallery in galleries],
            'count': len(galleries),
            'message': 'Default thematic galleries initialized successfully'
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Failed to initialize default galleries: {str(e)}'}, 500


@app.route('/galleries', methods=['GET'])
def get_all_galleries():
    """Get all galleries"""
    if not GALLERY_CURATION_AVAILABLE or gallery_curation_service is None:
        return {'error': 'Gallery curation service not available or not launched'}, 503
    
    try:
        galleries = gallery_curation_service.get_all_galleries()
        
        result = {
            'galleries': [gallery.to_dict() for gallery in galleries],
            'count': len(galleries)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Failed to retrieve galleries: {str(e)}'}, 500


@app.route('/galleries/create', methods=['POST'])
def create_gallery():
    """Create a new gallery from thematic request or natural language prompt"""
    if not GALLERY_CURATION_AVAILABLE or gallery_curation_service is None:
        return {'error': 'Gallery curation service not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data:
            return {'error': 'Request data required'}, 400
        
        # Check if it's a thematic gallery or prompt-based gallery
        if 'theme' in data:
            # Thematic gallery creation
            theme = data['theme']
            gallery = gallery_curation_service.create_thematic_gallery(theme)
        elif 'prompt' in data:
            # Natural language prompt-based gallery creation
            prompt = data['prompt']
            gallery = gallery_curation_service.generate_from_prompt(prompt)
        else:
            return {'error': 'Either theme or prompt parameter required'}, 400
        
        if not gallery:
            return {'error': 'Failed to create gallery - insufficient memories found'}, 404
        
        return jsonify(gallery.to_dict()), 201
        
    except Exception as e:
        return {'error': f'Failed to create gallery: {str(e)}'}, 500


@app.route('/galleries/<gallery_id>', methods=['GET'])
def get_gallery(gallery_id):
    """Get a specific gallery by ID"""
    if not GALLERY_CURATION_AVAILABLE or gallery_curation_service is None:
        return {'error': 'Gallery curation service not available or not launched'}, 503
    
    try:
        # This would need to be implemented in the service
        # For now, return a placeholder response
        return {'error': 'Gallery retrieval by ID not yet implemented'}, 501
        
    except Exception as e:
        return {'error': f'Failed to retrieve gallery: {str(e)}'}, 500


@app.route('/galleries/<gallery_id>/story', methods=['POST'])
def convert_gallery_to_story(gallery_id):
    """Transform a static gallery into a narrative experience"""
    if not GALLERY_CURATION_AVAILABLE or gallery_curation_service is None:
        return {'error': 'Gallery curation service not available or not launched'}, 503
    
    try:
        data = request.get_json() or {}
        
        narrative_mode = data.get('narrative_mode', 'thematic')
        narrative_style = data.get('narrative_style', 'documentary')
        include_voice_narration = data.get('include_voice_narration', False)
        
        story = gallery_curation_service.convert_gallery_to_story(
            gallery_id=gallery_id,
            narrative_mode=narrative_mode,
            narrative_style=narrative_style,
            include_voice_narration=include_voice_narration
        )
        
        if not story:
            return {'error': f'Failed to convert gallery {gallery_id} to story'}, 404
        
        return jsonify(story.to_dict())
        
    except Exception as e:
        return {'error': f'Failed to convert gallery to story: {str(e)}'}, 500


@app.route('/galleries/themes', methods=['GET'])
def get_supported_themes():
    """Get list of supported thematic gallery themes"""
    if not GALLERY_CURATION_AVAILABLE or gallery_curation_service is None:
        return {'error': 'Gallery curation service not available or not launched'}, 503
    
    try:
        themes = gallery_curation_service.get_supported_themes()
        
        result = {
            'themes': themes,
            'count': len(themes)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Failed to retrieve supported themes: {str(e)}'}, 500


# Story Generation API endpoints

@app.route('/stories/launch', methods=['GET'])
def launch_story_generation():
    """Launch the story generation service"""
    global story_generation_service
    
    if not STORY_GENERATION_AVAILABLE:
        return {'error': 'Story generation service unavailable'}, 503
    
    try:
        story_generation_service = StoryGenerationService()
        return {'message': 'Story generation service launched successfully'}
    except Exception as e:
        return {'error': f'Failed to initialize story generation service: {str(e)}'}, 500


@app.route('/stories/generate', methods=['POST'])
def generate_story():
    """Generate a story from personal memories"""
    if not STORY_GENERATION_AVAILABLE or story_generation_service is None:
        return {'error': 'Story generation service not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data:
            return {'error': 'Request data required'}, 400
        
        # Generate story using the service
        story = story_generation_service.generate_story(data)
        
        if not story:
            return {'error': 'Failed to generate story'}, 500
        
        return jsonify(story.to_dict()), 201
        
    except Exception as e:
        return {'error': f'Failed to generate story: {str(e)}'}, 500


@app.route('/stories/from-memories', methods=['POST'])
def generate_story_from_memories():
    """Generate a story from a specific list of memory IDs"""
    if not STORY_GENERATION_AVAILABLE or story_generation_service is None:
        return {'error': 'Story generation service not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data or 'memory_ids' not in data:
            return {'error': 'memory_ids parameter required'}, 400
        
        memory_ids = data['memory_ids']
        narrative_mode = data.get('narrative_mode', 'chronological')
        narrative_style = data.get('narrative_style', 'documentary')
        include_voice_narration = data.get('include_voice_narration', False)
        
        # For now, we'll need to retrieve memories by IDs
        # This would require implementing memory retrieval by ID
        # For the API structure, we'll return a placeholder response
        
        result = {
            'message': 'Story generation from memory IDs not yet fully implemented',
            'requested_memories': len(memory_ids),
            'narrative_mode': narrative_mode,
            'narrative_style': narrative_style,
            'include_voice_narration': include_voice_narration
        }
        
        return jsonify(result), 501  # Not implemented yet
        
    except Exception as e:
        return {'error': f'Failed to generate story from memories: {str(e)}'}, 500


@app.route('/stories/modes', methods=['GET'])
def get_narrative_modes():
    """Get supported narrative modes"""
    if not STORY_GENERATION_AVAILABLE or story_generation_service is None:
        return {'error': 'Story generation service not available or not launched'}, 503
    
    try:
        modes = story_generation_service.get_supported_narrative_modes()
        styles = story_generation_service.get_supported_narrative_styles()
        
        result = {
            'narrative_modes': modes,
            'narrative_styles': styles
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Failed to retrieve narrative modes: {str(e)}'}, 500


@app.route('/stories/<story_id>', methods=['GET'])
def get_story(story_id):
    """Get a specific story by ID"""
    if not STORY_GENERATION_AVAILABLE or story_generation_service is None:
        return {'error': 'Story generation service not available or not launched'}, 503
    
    try:
        # This would need to be implemented in the service
        # For now, return a placeholder response
        return {'error': 'Story retrieval by ID not yet implemented'}, 501
        
    except Exception as e:
        return {'error': f'Failed to retrieve story: {str(e)}'}, 500


@app.route('/stories/<story_id>/chapters', methods=['GET'])
def get_story_chapters(story_id):
    """Get chapters for a specific story"""
    if not STORY_GENERATION_AVAILABLE or story_generation_service is None:
        return {'error': 'Story generation service not available or not launched'}, 503
    
    try:
        # This would need to be implemented in the service
        # For now, return a placeholder response
        return {'error': 'Story chapters retrieval not yet implemented'}, 501
        
    except Exception as e:
        return {'error': f'Failed to retrieve story chapters: {str(e)}'}, 500


@app.route('/stories/<story_id>/narration', methods=['POST'])
def generate_story_narration(story_id):
    """Generate voice narration for a story"""
    if not STORY_GENERATION_AVAILABLE or story_generation_service is None:
        return {'error': 'Story generation service not available or not launched'}, 503
    
    try:
        data = request.get_json() or {}
        narrator_style = data.get('narrator_style', 'documentary')
        voice_settings = data.get('voice_settings', {})
        
        # This would need to be implemented in the service
        # For now, return a placeholder response
        result = {
            'story_id': story_id,
            'narrator_style': narrator_style,
            'voice_settings': voice_settings,
            'message': 'Voice narration generation not yet implemented'
        }
        
        return jsonify(result), 501
        
    except Exception as e:
        return {'error': f'Failed to generate story narration: {str(e)}'}, 500


# Place Exploration API endpoints

@app.route('/places/launch', methods=['GET'])
def launch_place_exploration():
    """Launch the place exploration service"""
    global place_exploration_service
    
    if not PLACE_EXPLORATION_AVAILABLE:
        return {'error': 'Place exploration service unavailable'}, 503
    
    try:
        place_exploration_service = PlaceExplorationService()
        return {'message': 'Place exploration service launched successfully'}
    except Exception as e:
        return {'error': f'Failed to initialize place exploration service: {str(e)}'}, 500


@app.route('/places/analyze', methods=['POST'])
def analyze_place_relationships():
    """Analyze place relationships from memories"""
    if not PLACE_EXPLORATION_AVAILABLE or place_exploration_service is None:
        return {'error': 'Place exploration service not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data or 'memories' not in data:
            return {'error': 'memories parameter required'}, 400
        
        # For now, we'll need to handle memory data structure
        # This would require proper memory object handling
        result = {
            'message': 'Place relationship analysis not yet fully implemented',
            'memory_count': len(data['memories']) if isinstance(data['memories'], list) else 0
        }
        
        return jsonify(result), 501
        
    except Exception as e:
        return {'error': f'Failed to analyze place relationships: {str(e)}'}, 500


@app.route('/places/<location_id>/explore', methods=['GET'])
def explore_location(location_id):
    """Create story-driven exploration for a specific location"""
    if not PLACE_EXPLORATION_AVAILABLE or place_exploration_service is None:
        return {'error': 'Place exploration service not available or not launched'}, 503
    
    try:
        # This would need to retrieve memories for the location
        # For now, return a placeholder response
        result = {
            'location_id': location_id,
            'message': 'Location exploration not yet fully implemented'
        }
        
        return jsonify(result), 501
        
    except Exception as e:
        return {'error': f'Failed to explore location: {str(e)}'}, 500


@app.route('/places/journeys/generate', methods=['POST'])
def generate_travel_narratives():
    """Generate travel narratives from memories"""
    if not PLACE_EXPLORATION_AVAILABLE or place_exploration_service is None:
        return {'error': 'Place exploration service not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data or 'memories' not in data:
            return {'error': 'memories parameter required'}, 400
        
        narrative_type = data.get('narrative_type', 'journey')
        
        # For now, return a placeholder response
        result = {
            'narrative_type': narrative_type,
            'memory_count': len(data['memories']) if isinstance(data['memories'], list) else 0,
            'message': 'Travel narrative generation not yet fully implemented'
        }
        
        return jsonify(result), 501
        
    except Exception as e:
        return {'error': f'Failed to generate travel narratives: {str(e)}'}, 500


@app.route('/places/map/narrative-layers', methods=['POST'])
def get_map_narrative_layers():
    """Get narrative layers for map display within specified bounds"""
    if not PLACE_EXPLORATION_AVAILABLE or place_exploration_service is None:
        return {'error': 'Place exploration service not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data or 'bounds' not in data:
            return {'error': 'bounds parameter required'}, 400
        
        bounds = data['bounds']
        
        # Validate bounds structure
        required_bounds = ['north', 'south', 'east', 'west']
        if not all(key in bounds for key in required_bounds):
            return {'error': f'bounds must contain: {required_bounds}'}, 400
        
        narrative_layers = place_exploration_service.get_narrative_layers_for_map(bounds)
        
        result = {
            'bounds': bounds,
            'narrative_layers': narrative_layers,
            'layer_count': len(narrative_layers)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': f'Failed to get map narrative layers: {str(e)}'}, 500


@app.route('/places/<location_id>/enhance', methods=['POST'])
def enhance_location_geo_data(location_id):
    """Enhance geo-enrichment for a specific location"""
    if not PLACE_EXPLORATION_AVAILABLE or place_exploration_service is None:
        return {'error': 'Place exploration service not available or not launched'}, 503
    
    try:
        data = request.get_json()
        if not data or 'memory' not in data:
            return {'error': 'memory parameter required'}, 400
        
        # For now, return a placeholder response
        result = {
            'location_id': location_id,
            'message': 'Location geo-enhancement not yet fully implemented'
        }
        
        return jsonify(result), 501
        
    except Exception as e:
        return {'error': f'Failed to enhance location geo data: {str(e)}'}, 500


# Fallback routes to original QA system
@app.route('/launch', methods=['GET'])
def launch_original():
    """Launch original QA engines (fallback)"""
    if not QA_AVAILABLE:
        return {'error': 'Original Q&A features unavailable'}, 503
    
    global qa_engine, chatgpt_engine
    
    try:
        qa_engine = QAEngine('personal-data/app_data/')
        chatgpt_engine = ChatGPTEngine()
        return {'message': 'Original QA engines launched successfully'}
    except Exception as e:
        return {'error': f'Failed to initialize original QA engines: {str(e)}'}, 500


@app.route('/query', methods=['GET'])
def query_original():
    """Query using original QA system (fallback)"""
    query = request.args.get('query')
    method = request.args.get('qa', 'Retrieval-based')
    
    if not QA_AVAILABLE:
        return {
            "question": query,
            "method": method,
            "answer": f"Original Q&A features require dependencies. Query was: '{query}'",
            "sources": [],
            "warning": "Install langchain, openai, and faiss-cpu for full Q&A functionality"
        }
    
    if method == 'ChatGPT' and chatgpt_engine:
        return {
            "question": query,
            "method": method,
            "answer": chatgpt_engine.query(query),
            "sources": []
        }
    
    if qa_engine:
        res = qa_engine.query(query, method=method)
        res["method"] = method
        return res
    
    return {
        "question": query,
        "method": method,
        "answer": f"Basic response (QA engine not initialized): '{query}'",
        "sources": []
    }


@app.route('/status', methods=['GET'])
def get_status():
    """Get status of all available engines"""
    status = {
        'enhanced_memory_available': ENHANCED_MEMORY_AVAILABLE,
        'enhanced_memory_launched': enhanced_memory_engine is not None,
        'people_intelligence_available': PEOPLE_INTELLIGENCE_AVAILABLE,
        'people_intelligence_launched': people_intelligence_service is not None,
        'gallery_curation_available': GALLERY_CURATION_AVAILABLE,
        'gallery_curation_launched': gallery_curation_service is not None,
        'story_generation_available': STORY_GENERATION_AVAILABLE,
        'story_generation_launched': story_generation_service is not None,
        'place_exploration_available': PLACE_EXPLORATION_AVAILABLE,
        'place_exploration_launched': place_exploration_service is not None,
        'original_qa_available': QA_AVAILABLE,
        'original_qa_launched': qa_engine is not None,
        'chatgpt_available': chatgpt_engine is not None
    }
    
    return jsonify(status)


if __name__ == '__main__':
    app.run(host="::", port=8085, debug=True)