"""
FastAPI endpoints for AI services health and status monitoring
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from .health_monitor import health_monitor
from .providers import provider_manager
from .usage_tracker import usage_tracker
from .config import config
from .facebook_posts_processor import get_facebook_posts_processor

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Personal Archive - AI Services API",
    description="Health monitoring and status endpoints for AI services",
    version="1.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def get_health_status() -> Dict[str, Any]:
    """
    Get comprehensive health status of all AI services including Facebook Timeline
    
    Returns:
        - overall_status: healthy, degraded, or limited
        - api_status: Status of each AI provider
        - services: Health of individual services
        - system_info: System configuration info
    """
    try:
        # Get base health status
        health_status = await health_monitor.comprehensive_health_check()
        
        # Add Facebook Timeline service status
        try:
            processor = get_facebook_posts_processor()
            facebook_status = processor.get_service_status()
            health_status['services']['facebook_timeline'] = facebook_status
        except Exception as e:
            health_status['services']['facebook_timeline'] = {
                "service": "facebook_posts_timeline",
                "status": "error",
                "error": str(e)
            }
        
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/status")
async def get_simple_status() -> Dict[str, Any]:
    """
    Get simplified status for UI display
    
    Returns status indicators for frontend badges
    """
    try:
        # Check API provider availability and test them
        provider_details = {}
        available_providers = []
        working_providers = []
        total_providers = 0
        
        for provider_name in ["openai", "anthropic", "google"]:
            total_providers += 1
            provider_info = {
                "name": provider_name,
                "has_key": config.has_api_key(provider_name),
                "status": "not_configured",
                "error": None,
                "last_test": None
            }
            
            if config.has_api_key(provider_name):
                available_providers.append(provider_name)
                provider_info["status"] = "configured"
                
                # Test if the provider is actually working
                try:
                    test_result = await provider_manager.test_provider_health(provider_name)
                    if test_result:
                        working_providers.append(provider_name)
                        provider_info["status"] = "working"
                        provider_info["last_test"] = "success"
                    else:
                        provider_info["status"] = "failing"
                        provider_info["error"] = "Health test failed"
                        provider_info["last_test"] = "failed"
                except Exception as e:
                    provider_info["status"] = "error"
                    provider_info["error"] = str(e)
                    provider_info["last_test"] = "error"
                    logger.warning(f"Provider {provider_name} test failed: {e}")
            
            provider_details[provider_name] = provider_info
        
        # Create detailed status message
        if len(working_providers) == 0 and len(available_providers) == 0:
            ai_status = "unavailable"
            ai_message = "No API keys configured. Add OpenAI, Anthropic, or Google API keys to enable AI features."
            status_color = "red"
            detailed_message = "To get started: 1) Get an API key from OpenAI, Anthropic, or Google 2) Add it to your .env file 3) Restart the application"
        elif len(working_providers) == 0 and len(available_providers) > 0:
            ai_status = "unavailable"
            failed_providers = [p for p in available_providers if provider_details[p]["status"] != "working"]
            error_details = []
            for provider in failed_providers:
                error = provider_details[provider].get("error", "Unknown error")
                if "rate limit" in error.lower():
                    error_details.append(f"{provider.title()}: Rate limited")
                elif "invalid" in error.lower() or "unauthorized" in error.lower():
                    error_details.append(f"{provider.title()}: Invalid API key")
                else:
                    error_details.append(f"{provider.title()}: {error}")
            
            ai_message = f"Configured providers not working: {', '.join(error_details)}"
            status_color = "red"
            detailed_message = "Check your API keys and account limits. You may need to add credits or wait for rate limits to reset."
        elif len(working_providers) < total_providers:
            ai_status = "partial"
            ai_message = f"AI features available via {', '.join([p.title() for p in working_providers])}"
            status_color = "yellow"
            
            non_working = [p for p in ["openai", "anthropic", "google"] if p not in working_providers]
            non_working_details = []
            for provider in non_working:
                if not provider_details[provider]["has_key"]:
                    non_working_details.append(f"{provider.title()}: No API key")
                else:
                    error = provider_details[provider].get("error", "Not working")
                    non_working_details.append(f"{provider.title()}: {error}")
            
            detailed_message = f"Working: {', '.join([p.title() for p in working_providers])}. Issues: {', '.join(non_working_details)}"
        else:
            ai_status = "full"
            ai_message = "All AI features active"
            status_color = "green"
            detailed_message = f"All providers working: {', '.join([p.title() for p in working_providers])}"
        
        return {
            "ai_status": ai_status,
            "ai_message": ai_message,
            "detailed_message": detailed_message,
            "status_color": status_color,
            "available_providers": working_providers,
            "configured_providers": available_providers,
            "provider_details": provider_details,
            "total_providers": total_providers,
            "features": {
                "story_generation": len(working_providers) > 0,
                "people_intelligence": any(p in working_providers for p in ["openai", "google"]),
                "smart_galleries": len(working_providers) > 0,
                "semantic_search": len(working_providers) > 0
            },
            "recommendations": _get_status_recommendations(provider_details, working_providers, available_providers)
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "ai_status": "error",
            "ai_message": f"Status check failed: {str(e)}",
            "detailed_message": f"System error: {str(e)}",
            "status_color": "red",
            "available_providers": [],
            "total_providers": 0,
            "features": {
                "story_generation": False,
                "people_intelligence": False,
                "smart_galleries": False,
                "semantic_search": False
            },
            "recommendations": ["Check system logs for errors", "Restart the application"]
        }

def _get_status_recommendations(provider_details: Dict, working_providers: List, available_providers: List) -> List[str]:
    """Generate specific recommendations based on provider status"""
    recommendations = []
    
    if len(working_providers) == 0 and len(available_providers) == 0:
        recommendations.extend([
            "Get an API key from OpenAI (https://platform.openai.com/api-keys)",
            "Or get an API key from Anthropic (https://console.anthropic.com/)",
            "Add the key to your .env file as OPENAI_API_KEY=your-key-here",
            "Restart the application"
        ])
    elif len(working_providers) == 0 and len(available_providers) > 0:
        for provider, details in provider_details.items():
            if details["has_key"] and details["status"] != "working":
                error = details.get("error", "")
                if "rate limit" in error.lower():
                    recommendations.append(f"Wait for {provider.title()} rate limits to reset (usually 1 hour)")
                elif "invalid" in error.lower() or "unauthorized" in error.lower():
                    recommendations.append(f"Check your {provider.title()} API key - it may be invalid or expired")
                elif "quota" in error.lower() or "billing" in error.lower():
                    recommendations.append(f"Add credits to your {provider.title()} account")
                else:
                    recommendations.append(f"Check {provider.title()} service status and your account")
    elif len(working_providers) < 3:
        missing_providers = [p for p in ["openai", "anthropic", "google"] if not provider_details[p]["has_key"]]
        if missing_providers:
            recommendations.append(f"Add API keys for {', '.join([p.title() for p in missing_providers])} for redundancy")
    
    if not recommendations:
        recommendations.append("All systems working normally")
    
    return recommendations

@app.get("/usage/summary")
async def get_usage_summary(days: int = 7) -> Dict[str, Any]:
    """
    Get API usage summary for cost monitoring
    
    Args:
        days: Number of days to include in summary (default: 7)
    """
    try:
        summary = usage_tracker.get_usage_summary(days)
        return {
            "period_days": days,
            "summary": summary,
            "cost_breakdown": summary.get("providers", {}),
            "recommendations": _get_cost_recommendations(summary)
        }
    except Exception as e:
        logger.error(f"Usage summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Usage summary failed: {str(e)}")

@app.get("/providers")
async def get_provider_info() -> Dict[str, Any]:
    """
    Get information about available AI providers
    """
    try:
        provider_status = provider_manager.get_provider_status()
        
        provider_info = {}
        for name, status in provider_status.items():
            provider_info[name] = {
                "name": name.title(),
                "has_credentials": config.has_api_key(name),
                "status": status["status"],
                "priority": status["priority"],
                "quality": status["quality"],
                "capabilities": _get_provider_capabilities(name)
            }
        
        return {
            "providers": provider_info,
            "hierarchy": config.provider_hierarchy,
            "setup_instructions": {
                "openai": "Get API key from https://platform.openai.com/api-keys",
                "anthropic": "Get API key from https://console.anthropic.com/",
                "google": "Get API key from https://makersuite.google.com/app/apikey"
            }
        }
        
    except Exception as e:
        logger.error(f"Provider info failed: {e}")
        raise HTTPException(status_code=500, detail=f"Provider info failed: {str(e)}")

@app.get("/metrics")
async def get_service_metrics() -> Dict[str, Any]:
    """
    Get comprehensive service metrics for monitoring
    """
    try:
        metrics = await health_monitor.get_service_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics failed: {str(e)}")

@app.post("/chat")
async def chat_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chat endpoint for natural language queries with personal data context
    """
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Gather context from personal data
        context_info = []
        
        try:
            # Get people data
            from .people_intelligence import people_service
            people_objects = await people_service.get_all_people()
            people_count = len(people_objects)
            context_info.append(f"You have {people_count} people detected in your photos")
            
            # Get stories data
            from .story_generation import story_service
            story_objects = await story_service.get_all_stories()
            stories_count = len(story_objects)
            context_info.append(f"You have {stories_count} generated stories")
            
            # Get photo count from galleries
            # This is a simple way to get photo count without complex data processing
            import os
            from pathlib import Path
            data_path = Path("./MyData")
            photo_count = 0
            if data_path.exists():
                for photo_path in data_path.rglob("*.jpg"):
                    if photo_path.is_file():
                        photo_count += 1
                        if photo_count >= 50:  # Limit counting for performance
                            break
            context_info.append(f"You have approximately {photo_count}+ photos in your archive")
            
        except Exception as context_error:
            logger.warning(f"Failed to gather context: {context_error}")
            context_info.append("Personal data context temporarily unavailable")
        
        # Create context-aware prompt
        context_text = ". ".join(context_info)
        
        # Use real AI for chat responses with personal data context
        try:
            response = await provider_manager.generate_text(
                f"You are a helpful AI assistant for a personal archive system. "
                f"Context about the user's data: {context_text}. "
                f"The user is asking: {message}. "
                f"Provide a helpful, conversational response using the context about their personal data when relevant.",
                task_type="chat",
                max_tokens=200
            )
        except Exception as ai_error:
            logger.warning(f"AI chat failed: {ai_error}")
            # Fallback response when AI is unavailable
            response = (
                f"I'm currently unable to process your message due to AI service limitations. "
                f"Your message was: '{message}'. Please try again later when AI services are available."
            )
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "context_used": context_info
        }
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/qa")
async def qa_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q&A endpoint for semantic search queries with personal data context
    """
    try:
        query = request.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Gather detailed context from personal data
        context_info = []
        detailed_context = {}
        
        try:
            # Get people data with details
            from .people_intelligence import people_service
            people_objects = await people_service.get_all_people()
            people_count = len(people_objects)
            detailed_context["people_count"] = people_count
            
            if people_objects:
                total_photos_with_people = sum(person.photo_count for person in people_objects)
                context_info.append(f"You have {people_count} people detected across {total_photos_with_people} photos")
            
            # Get stories data with details
            from .story_generation import story_service
            story_objects = await story_service.get_all_stories()
            stories_count = len(story_objects)
            detailed_context["stories_count"] = stories_count
            
            if story_objects:
                total_chapters = sum(len(story.chapters) for story in story_objects if story.chapters)
                context_info.append(f"You have {stories_count} generated stories with {total_chapters} total chapters")
            
            # Get photo count and details
            import os
            from pathlib import Path
            data_path = Path("./MyData")
            photo_count = 0
            photo_paths = []
            
            if data_path.exists():
                for photo_path in data_path.rglob("*.jpg"):
                    if photo_path.is_file():
                        photo_count += 1
                        photo_paths.append(str(photo_path))
                        if photo_count >= 20:  # Limit for performance
                            break
            
            detailed_context["photo_count"] = photo_count
            context_info.append(f"You have {photo_count}+ photos in your personal archive")
            
            # Add specific data for common queries
            if "how many" in query.lower() and "photo" in query.lower():
                context_info.append(f"Specific answer: You have {photo_count} photos")
            
            if "people" in query.lower():
                context_info.append(f"Specific answer: You have {people_count} people detected in your photos")
            
            if "stories" in query.lower() or "story" in query.lower():
                context_info.append(f"Specific answer: You have {stories_count} AI-generated stories")
                
        except Exception as context_error:
            logger.warning(f"Failed to gather Q&A context: {context_error}")
            context_info.append("Personal data context temporarily unavailable")
        
        # Create detailed context-aware prompt
        context_text = ". ".join(context_info)
        
        # Use real AI for Q&A responses with rich personal data context
        try:
            response = await provider_manager.generate_text(
                f"You are an AI assistant helping someone explore their personal data archive. "
                f"Context about the user's personal data: {context_text}. "
                f"The user is asking: '{query}'. "
                f"Use the specific context provided to give accurate, data-driven answers. "
                f"If the context contains specific numbers or facts, use them in your response. "
                f"Be conversational but informative.",
                task_type="qa",
                max_tokens=300
            )
            confidence = 0.95 if context_info else 0.7
        except Exception as ai_error:
            logger.warning(f"AI Q&A failed: {ai_error}")
            # Fallback response with available context
            if detailed_context:
                response = f"Based on your personal data: "
                if "photo" in query.lower():
                    response += f"You have {detailed_context.get('photo_count', 0)} photos. "
                if "people" in query.lower():
                    response += f"You have {detailed_context.get('people_count', 0)} people detected. "
                if "stories" in query.lower():
                    response += f"You have {detailed_context.get('stories_count', 0)} generated stories. "
            else:
                response = (
                    f"I'm currently unable to analyze your query '{query}' due to AI service limitations. "
                    f"Please try again later when AI services are available."
                )
            confidence = 0.5 if detailed_context else 0.1
        
        return {
            "answer": response,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence,
            "sources": ["personal_archive"],
            "context_data": detailed_context
        }
        
    except Exception as e:
        logger.error(f"Q&A failed: {e}")
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")

@app.get("/stories/{story_id}")
async def get_story_by_id(story_id: str) -> Dict[str, Any]:
    """
    Get a specific story with its chapters
    """
    # Handle special case for launch endpoint
    if story_id == "launch":
        return {
            "status": "success",
            "message": "Story generation service initialized",
            "service": "story_generation",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        from .story_generation import story_service
        story_obj = await story_service.get_story_by_id(story_id)
        
        if not story_obj:
            raise HTTPException(status_code=404, detail="Story not found")
        
        # Convert Story object to serializable dictionary with chapters
        story_dict = {
            "id": story_obj.id,
            "title": story_obj.title,
            "narrative_mode": story_obj.narrative_mode.value if hasattr(story_obj.narrative_mode, 'value') else str(story_obj.narrative_mode),
            "chapter_count": len(story_obj.chapters) if story_obj.chapters else 0,
            "quality_score": story_obj.quality_score,
            "generated_at": story_obj.generated_at.isoformat() if story_obj.generated_at else None,
            "total_media_references": len(story_obj.total_media_references) if story_obj.total_media_references else 0,
            "chapters": [
                {
                    "id": chapter.id,
                    "title": chapter.title,
                    "content": chapter.content,
                    "narrative_text": chapter.content,  # Alias for frontend compatibility
                    "emotional_tone": chapter.emotional_tone,
                    "media_elements": [{"path": ref, "type": "photo"} for ref in chapter.media_references] if chapter.media_references else []
                }
                for chapter in story_obj.chapters
            ] if story_obj.chapters else []
        }
        
        return story_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get story by ID failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get story failed: {str(e)}")

@app.get("/stories")
async def get_stories() -> Dict[str, Any]:
    """
    Get all generated stories
    """
    try:
        from .story_generation import story_service
        story_objects = await story_service.get_all_stories()
        
        # Convert Story objects to serializable dictionaries
        stories_data = []
        for story in story_objects:
            story_dict = {
                "id": story.id,
                "title": story.title,
                "narrative_mode": story.narrative_mode.value if hasattr(story.narrative_mode, 'value') else str(story.narrative_mode),
                "chapter_count": len(story.chapters) if story.chapters else 0,
                "quality_score": story.quality_score,
                "generated_at": story.generated_at.isoformat() if story.generated_at else None,
                "total_media_references": len(story.total_media_references) if story.total_media_references else 0
            }
            stories_data.append(story_dict)
        
        return {
            "stories": stories_data,
            "count": len(stories_data)
        }
    except Exception as e:
        logger.error(f"Get stories failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get stories failed: {str(e)}")

@app.post("/stories/generate")
async def generate_story(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a new story
    """
    try:
        from .story_generation import story_service
        from datetime import datetime, timedelta
        
        story_type = request.get("type", "chronological")
        theme = request.get("theme", "Life memories")
        
        # Default timeframe - last 3 months
        timeframe = (datetime.now() - timedelta(days=90), datetime.now())
        
        if story_type == "chronological":
            story_obj = await story_service.generate_chronological_story(timeframe, theme)
        else:
            # For other types, use chronological as fallback
            story_obj = await story_service.generate_chronological_story(timeframe, theme)
        
        # Convert Story object to serializable dictionary
        story_dict = {
            "id": story_obj.id,
            "title": story_obj.title,
            "narrative_mode": story_obj.narrative_mode.value if hasattr(story_obj.narrative_mode, 'value') else str(story_obj.narrative_mode),
            "chapter_count": len(story_obj.chapters) if story_obj.chapters else 0,
            "quality_score": story_obj.quality_score,
            "generated_at": story_obj.generated_at.isoformat() if story_obj.generated_at else datetime.now().isoformat(),
            "total_media_references": len(story_obj.total_media_references) if story_obj.total_media_references else 0,
            "chapters": [
                {
                    "id": chapter.id,
                    "title": chapter.title,
                    "content": chapter.content[:500] + "..." if len(chapter.content) > 500 else chapter.content,  # Truncate for API
                    "emotional_tone": chapter.emotional_tone
                }
                for chapter in story_obj.chapters
            ] if story_obj.chapters else []
        }
        
        return {
            "story": story_dict,
            "type": story_type,
            "theme": theme,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Story generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")

@app.get("/people")
async def get_people() -> Dict[str, Any]:
    """
    Get all detected people
    """
    try:
        from .people_intelligence import people_service
        people_objects = await people_service.get_all_people()
        
        # Convert PersonProfile objects to serializable dictionaries
        people_data = []
        for person in people_objects:
            person_dict = {
                "id": person.id,
                "name": person.name,
                "representative_photos": person.representative_photos,
                "photo_count": person.photo_count,
                "relationship_strength": person.relationship_strength,
                "privacy_level": person.privacy_level,
                "first_seen": person.first_seen.isoformat() if person.first_seen else None,
                "last_seen": person.last_seen.isoformat() if person.last_seen else None,
                "interaction_timeline": len(person.interaction_timeline) if person.interaction_timeline else 0
            }
            people_data.append(person_dict)
        
        return {
            "people": people_data,
            "count": len(people_data)
        }
    except Exception as e:
        logger.error(f"Get people failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get people failed: {str(e)}")

@app.get("/people/profiles")
async def get_people_profiles() -> Dict[str, Any]:
    """
    Get all people profiles (frontend compatibility endpoint)
    """
    # Reuse the same logic as /people but with different response format
    people_response = await get_people()
    return {
        "profiles": people_response["people"],
        "count": people_response["count"]
    }

@app.get("/galleries")
async def get_galleries() -> Dict[str, Any]:
    """
    Get photo galleries
    """
    try:
        from ..data_processing.local_processor import LocalDataProcessor
        processor = LocalDataProcessor()
        
        # Get processing status
        status = processor.get_processing_status()
        
        # Look for photos
        photos = []
        if processor.data_path.exists():
            photo_files = list(processor.data_path.rglob("*.jpg")) + list(processor.data_path.rglob("*.jpeg"))
            photos = [{"path": str(p), "name": p.name} for p in photo_files[:10]]  # Limit to 10
        
        return {
            "galleries": [
                {
                    "name": "Recent Photos",
                    "photos": photos,
                    "count": len(photos)
                }
            ],
            "total_photos": len(photos),
            "processing_status": status
        }
        
    except Exception as e:
        logger.error(f"Get galleries failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get galleries failed: {str(e)}")

def _get_cost_recommendations(usage_summary: Dict[str, Any]) -> List[str]:
    """Generate cost optimization recommendations"""
    recommendations = []
    
    total_cost = usage_summary.get("total_cost", 0)
    total_calls = usage_summary.get("total_calls", 0)
    
    if total_cost > 50:  # High usage
        recommendations.append("Consider using local AI models for some tasks to reduce costs")
        recommendations.append("Review API call patterns - some requests might be cacheable")
    
    if total_calls > 1000:  # High volume
        recommendations.append("Enable local caching to reduce redundant API calls")
        recommendations.append("Consider batch processing for similar requests")
    
    if total_cost == 0 and total_calls == 0:
        recommendations.append("No API usage detected - add API keys to enable AI features")
    
    return recommendations

def _get_provider_capabilities(provider_name: str) -> List[str]:
    """Get capabilities for each provider"""
    capabilities = {
        "openai": ["Text Generation", "Image Analysis", "Embeddings", "Vision"],
        "anthropic": ["Text Generation", "Long Context", "Code Analysis"],
        "google": ["Text Generation", "Image Analysis", "Free Tier"]
    }
    
    return capabilities.get(provider_name, [])

# Stub endpoints for frontend service initialization
@app.get("/launch")
async def launch_qa_engine(dataset: str = "Digital") -> Dict[str, Any]:
    """Launch Q&A engine (stub endpoint for frontend compatibility)"""
    return {
        "status": "success",
        "message": f"Q&A engine launched for dataset: {dataset}",
        "dataset": dataset,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/enhanced/launch")
async def launch_enhanced_memory() -> Dict[str, Any]:
    """Launch enhanced memory service (stub endpoint)"""
    return {
        "status": "success",
        "message": "Enhanced memory service initialized",
        "service": "enhanced_memory",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/people/launch")
async def launch_people_intelligence() -> Dict[str, Any]:
    """Launch people intelligence service (stub endpoint)"""
    return {
        "status": "success",
        "message": "People intelligence service initialized",
        "service": "people_intelligence",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/galleries/launch")
async def launch_gallery_curation() -> Dict[str, Any]:
    """Launch gallery curation service (stub endpoint)"""
    return {
        "status": "success",
        "message": "Gallery curation service initialized",
        "service": "gallery_curation",
        "timestamp": datetime.now().isoformat()
    }



@app.get("/places/launch")
async def launch_place_exploration() -> Dict[str, Any]:
    """Launch place exploration service (stub endpoint)"""
    return {
        "status": "success",
        "message": "Place exploration service initialized",
        "service": "place_exploration",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/places")
async def get_places() -> Dict[str, Any]:
    """
    Get places/locations data for map display
    """
    try:
        # For now, return some sample location data
        # In a full implementation, this would extract GPS data from photos
        places = [
            {
                "id": "place_1",
                "name": "Home",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "photo_count": 5,
                "visit_count": 10,
                "description": "Frequent location with multiple photos"
            },
            {
                "id": "place_2", 
                "name": "Work",
                "latitude": 37.7849,
                "longitude": -122.4094,
                "photo_count": 3,
                "visit_count": 8,
                "description": "Regular location with some photos"
            }
        ]
        
        return {
            "places": places,
            "count": len(places),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Get places failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get places failed: {str(e)}")

@app.get("/locations")
async def get_locations() -> Dict[str, Any]:
    """
    Get location data (alias for places)
    """
    return await get_places()

@app.get("/facebook/timeline")
async def get_facebook_timeline(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format")
) -> Dict[str, Any]:
    """
    Get Facebook posts timeline data for chart visualization
    
    Returns timeline data grouped by date with post counts and media counts
    """
    try:
        processor = get_facebook_posts_processor()
        timeline_data = processor.get_timeline_data(start_date, end_date)
        
        return {
            "status": "success",
            "timeline": [
                {
                    "date": item.date,
                    "post_count": item.post_count,
                    "has_media_count": item.has_media_count
                }
                for item in timeline_data
            ],
            "filters": {
                "start_date": start_date,
                "end_date": end_date
            },
            "count": len(timeline_data)
        }
        
    except Exception as e:
        logger.error(f"Get Facebook timeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Timeline failed: {str(e)}")

@app.get("/facebook/posts")
async def get_facebook_posts(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    start_date: Optional[str] = Query(None, description="Start date for range query"),
    end_date: Optional[str] = Query(None, description="End date for range query")
) -> Dict[str, Any]:
    """
    Get Facebook posts for a specific date or date range
    """
    try:
        processor = get_facebook_posts_processor()
        
        if date:
            # Get posts for specific date
            posts = processor.get_posts_for_date(date)
            
            return {
                "status": "success",
                "date": date,
                "post_count": len(posts),
                "posts": [
                    {
                        "id": post.id,
                        "content": post.content,
                        "timestamp": post.timestamp.isoformat(),
                        "post_type": post.post_type,
                        "media_files": post.media_files,
                        "reactions": post.reactions,
                        "comments_count": post.comments_count,
                        "location": post.location,
                        "tagged_people": post.tagged_people
                    }
                    for post in posts
                ]
            }
        else:
            # For range queries, return timeline data
            timeline_data = processor.get_timeline_data(start_date, end_date)
            return {
                "status": "success",
                "timeline": [
                    {
                        "date": item.date,
                        "post_count": item.post_count,
                        "has_media_count": item.has_media_count
                    }
                    for item in timeline_data
                ],
                "filters": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        
    except Exception as e:
        logger.error(f"Get Facebook posts failed: {e}")
        raise HTTPException(status_code=500, detail=f"Posts query failed: {str(e)}")

@app.post("/facebook/process")
async def process_facebook_data() -> Dict[str, Any]:
    """
    Trigger Facebook data processing from export files
    
    Processes Facebook export JSON files and stores posts in database
    """
    try:
        processor = get_facebook_posts_processor()
        result = processor.process_facebook_data()
        
        return {
            "status": "success" if result.success else "error",
            "processing_result": {
                "success": result.success,
                "total_posts": result.total_posts,
                "processed_posts": result.processed_posts,
                "stored_posts": result.stored_posts,
                "skipped_posts": result.skipped_posts,
                "errors": result.errors
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Process Facebook data failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/facebook/stats")
async def get_facebook_stats() -> Dict[str, Any]:
    """
    Get Facebook posting statistics and analytics
    """
    try:
        processor = get_facebook_posts_processor()
        stats = processor.get_timeline_stats()
        service_status = processor.get_service_status()
        
        return {
            "status": "success",
            "statistics": {
                "date": stats.date,
                "post_count": stats.post_count,
                "media_count": stats.media_count,
                "reaction_count": stats.reaction_count,
                "post_types": stats.post_types
            },
            "service_status": service_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get Facebook stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)