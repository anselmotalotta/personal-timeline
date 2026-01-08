"""
Health monitoring and status reporting for AI services
"""
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import sqlite3
from pathlib import Path

from .config import config
from .providers import provider_manager
from .people_intelligence import people_service
from .story_generation import story_service
from .usage_tracker import usage_tracker

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitor health and status of all AI services"""
    
    def __init__(self):
        self.last_check = None
        self.health_status = {}
        
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all services"""
        self.last_check = datetime.now()
        
        health_status = {
            "timestamp": self.last_check.isoformat(),
            "overall_status": "healthy",
            "services": {},
            "system_info": await self._get_system_info(),
            "data_status": await self._check_data_status(),
            "api_status": await self._check_api_providers()
        }
        
        # Check individual services
        services_to_check = [
            ("ai_providers", self._check_ai_providers),
            ("people_intelligence", self._check_people_service),
            ("story_generation", self._check_story_service),
            ("data_processing", self._check_data_processing),
            ("usage_tracking", self._check_usage_tracking),
            ("local_storage", self._check_local_storage)
        ]
        
        for service_name, check_func in services_to_check:
            try:
                service_status = await check_func()
                health_status["services"][service_name] = service_status
                
                if not service_status.get("healthy", False):
                    health_status["overall_status"] = "degraded"
                    
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                health_status["services"][service_name] = {
                    "healthy": False,
                    "error": str(e),
                    "status": "error"
                }
                health_status["overall_status"] = "degraded"
        
        self.health_status = health_status
        return health_status
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "data_path": str(config.get_data_path()),
            "data_path_exists": config.get_data_path().exists(),
            "python_version": "3.11+",
            "ai_providers_configured": len([k for k, v in config.api_keys.items() if v]),
            "provider_hierarchy": config.provider_hierarchy
        }
    
    async def _check_data_status(self) -> Dict[str, Any]:
        """Check data directory and permissions"""
        data_path = config.get_data_path()
        
        try:
            # Check if data directory exists and is accessible
            exists = data_path.exists()
            readable = data_path.is_dir() if exists else False
            
            # Check permissions (Unix systems)
            permissions = None
            if exists:
                import os
                stat_info = os.stat(data_path)
                permissions = oct(stat_info.st_mode)[-3:]
            
            return {
                "data_directory_exists": exists,
                "data_directory_readable": readable,
                "permissions": permissions,
                "secure_permissions": permissions == "700" if permissions else False,
                "path": str(data_path)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "data_directory_exists": False,
                "data_directory_readable": False
            }
    
    async def _check_api_providers(self) -> Dict[str, Any]:
        """Check API provider availability and credentials"""
        provider_status = {}
        
        for provider_name, provider in provider_manager.providers.items():
            try:
                has_credentials = config.has_api_key(provider_name)
                is_available = provider.is_available()
                
                provider_status[provider_name] = {
                    "has_credentials": has_credentials,
                    "is_available": is_available,
                    "status": provider.status.value,
                    "priority": provider.priority,
                    "last_error": provider.last_error
                }
                
            except Exception as e:
                provider_status[provider_name] = {
                    "error": str(e),
                    "has_credentials": False,
                    "is_available": False
                }
        
        return provider_status
    
    async def _check_ai_providers(self) -> Dict[str, Any]:
        """Check AI provider manager health"""
        try:
            # Test basic functionality
            provider_status = provider_manager.get_provider_status()
            usage_stats = provider_manager.get_usage_stats(days=1)
            
            return {
                "healthy": True,
                "status": "active",
                "provider_count": len(provider_manager.providers),
                "available_providers": len([p for p in provider_manager.providers.values() if p.is_available()]),
                "recent_usage": usage_stats,
                "provider_details": provider_status
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    async def _check_people_service(self) -> Dict[str, Any]:
        """Check people intelligence service health"""
        try:
            service_status = people_service.get_service_status()
            
            return {
                "healthy": True,
                "status": "active",
                "database_accessible": Path(people_service.db_path).exists(),
                "statistics": service_status["statistics"]
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    async def _check_story_service(self) -> Dict[str, Any]:
        """Check story generation service health"""
        try:
            service_status = story_service.get_service_status()
            
            return {
                "healthy": True,
                "status": "active",
                "database_accessible": Path(story_service.db_path).exists(),
                "statistics": service_status["statistics"]
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    async def _check_data_processing(self) -> Dict[str, Any]:
        """Check data processing capabilities"""
        try:
            from ..data_processing.local_processor import LocalDataProcessor
            
            processor = LocalDataProcessor(str(config.get_data_path()))
            privacy_ok = processor.ensure_data_privacy()
            status = processor.get_processing_status()
            
            return {
                "healthy": True,
                "status": "active",
                "privacy_ensured": privacy_ok,
                "processing_status": status
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    async def _check_usage_tracking(self) -> Dict[str, Any]:
        """Check usage tracking service"""
        try:
            summary = usage_tracker.get_usage_summary(days=1)
            
            return {
                "healthy": True,
                "status": "active",
                "database_accessible": Path(usage_tracker.db_path).exists(),
                "recent_usage": summary
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    async def _check_local_storage(self) -> Dict[str, Any]:
        """Check local storage health"""
        try:
            data_path = config.get_data_path()
            
            # Check disk space (simplified)
            import shutil
            total, used, free = shutil.disk_usage(data_path)
            
            # Check if we have at least 1GB free
            has_space = free > 1024 * 1024 * 1024
            
            return {
                "healthy": has_space,
                "status": "active" if has_space else "low_space",
                "total_space_gb": round(total / (1024**3), 2),
                "used_space_gb": round(used / (1024**3), 2),
                "free_space_gb": round(free / (1024**3), 2),
                "space_warning": not has_space
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    def get_last_health_status(self) -> Dict[str, Any]:
        """Get the last health check results"""
        if not self.health_status:
            return {
                "status": "no_check_performed",
                "message": "No health check has been performed yet"
            }
        
        return self.health_status
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics"""
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "uptime_info": {
                    "last_health_check": self.last_check.isoformat() if self.last_check else None,
                    "health_check_available": self.health_status is not None
                },
                "usage_metrics": usage_tracker.get_usage_summary(days=7),
                "provider_metrics": provider_manager.get_usage_stats(days=7),
                "service_counts": {
                    "people_detected": 0,
                    "stories_generated": 0,
                    "api_calls_today": 0
                }
            }
            
            # Get service-specific metrics
            try:
                people_status = people_service.get_service_status()
                metrics["service_counts"]["people_detected"] = people_status["statistics"]["total_people"]
            except:
                pass
                
            try:
                story_status = story_service.get_service_status()
                metrics["service_counts"]["stories_generated"] = story_status["statistics"]["total_stories"]
            except:
                pass
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global health monitor instance
health_monitor = HealthMonitor()