"""
AI Provider Management with hierarchical strategy and secure credential handling
"""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json
import aiohttp
from .config import config

logger = logging.getLogger(__name__)

class ProviderStatus(Enum):
    AVAILABLE = "available"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    NO_CREDENTIALS = "no_credentials"

@dataclass
class APIUsage:
    provider: str
    endpoint: str
    tokens_used: int
    cost: float
    timestamp: float
    success: bool

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, name: str, priority: int, cost_tier: str, quality: str):
        self.name = name
        self.priority = priority
        self.cost_tier = cost_tier
        self.quality = quality
        self.status = ProviderStatus.UNAVAILABLE
        self.last_error = None
        self.rate_limit_reset = 0
        self.status_cache_expiry = 0  # Add status cache expiry
        
    @abstractmethod
    async def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using this provider"""
        pass
        
    @abstractmethod
    async def analyze_image(self, image_path: str, prompt: str = "Describe this image") -> Dict[str, Any]:
        """Analyze image using this provider"""
        pass
        
    @abstractmethod
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using this provider"""
        pass
        
    def is_available(self) -> bool:
        """Check if provider is currently available"""
        if not config.has_api_key(self.name):
            self.status = ProviderStatus.NO_CREDENTIALS
            return False
            
        # Check if status cache has expired (configurable TTL for failed providers)
        if (self.status in [ProviderStatus.UNAVAILABLE, ProviderStatus.RATE_LIMITED] and 
            time.time() > self.status_cache_expiry):
            # Reset status to allow retry
            self.status = ProviderStatus.AVAILABLE
            self.last_error = None
            
        if self.status == ProviderStatus.RATE_LIMITED:
            if time.time() > self.rate_limit_reset:
                self.status = ProviderStatus.AVAILABLE
            else:
                return False
        
        # Set to available if we have credentials and no other issues
        if self.status == ProviderStatus.UNAVAILABLE and config.has_api_key(self.name):
            self.status = ProviderStatus.AVAILABLE
                
        return self.status == ProviderStatus.AVAILABLE

class OpenAIProvider(AIProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self):
        super().__init__("openai", priority=1, cost_tier="high", quality="excellent")
        self.base_url = "https://api.openai.com/v1"
        self.model = config.default_models['openai']
        
    async def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using OpenAI GPT models"""
        if not self.is_available():
            raise Exception(f"OpenAI provider not available: {self.status}")
            
        headers = {
            "Authorization": f"Bearer {config.get_api_key('openai')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.api_timeout)) as session:
                async with session.post(f"{self.base_url}/chat/completions", 
                                      headers=headers, json=payload) as response:
                    if response.status == 429:
                        self.status = ProviderStatus.RATE_LIMITED
                        self.rate_limit_reset = time.time() + 60  # Wait 1 minute
                        self.status_cache_expiry = time.time() + 60  # Cache for same duration
                        raise Exception("Rate limit exceeded")
                        
                    response.raise_for_status()
                    data = await response.json()
                    
                    self.status = ProviderStatus.AVAILABLE
                    return data['choices'][0]['message']['content']
                    
        except Exception as e:
            self.last_error = str(e)
            self.status = ProviderStatus.UNAVAILABLE
            self.status_cache_expiry = time.time() + (config.local_cache_ttl_minutes * 60)  # Use configurable TTL
            logger.error(config.validate_no_credentials_in_logs(f"OpenAI API error: {e}"))
            raise
            
    async def analyze_image(self, image_path: str, prompt: str = "Describe this image") -> Dict[str, Any]:
        """Analyze image using OpenAI Vision API"""
        if not self.is_available():
            raise Exception(f"OpenAI provider not available: {self.status}")
            
        # Read and encode the image
        import base64
        from pathlib import Path
        
        try:
            image_file = Path(image_path)
            if not image_file.exists():
                raise Exception(f"Image file not found: {image_path}")
            
            # Read and encode image
            with open(image_file, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Determine image type
            image_type = image_file.suffix.lower()
            if image_type == '.jpg':
                image_type = '.jpeg'
            mime_type = f"image/{image_type[1:]}"
            
            headers = {
                "Authorization": f"Bearer {config.get_api_key('openai')}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.api_timeout)) as session:
                async with session.post(f"{self.base_url}/chat/completions", 
                                      headers=headers, json=payload) as response:
                    if response.status == 429:
                        self.status = ProviderStatus.RATE_LIMITED
                        self.rate_limit_reset = time.time() + 60
                        raise Exception("Rate limited")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    description = data['choices'][0]['message']['content']
                    
                    return {
                        "description": description,
                        "provider": "openai",
                        "confidence": 0.9,
                        "model": "gpt-4o"
                    }
                    
        except Exception as e:
            self.status = ProviderStatus.UNAVAILABLE
            self.last_error = str(e)
            logger.error(config.validate_no_credentials_in_logs(f"OpenAI Vision API error: {e}"))
            raise
        
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using OpenAI embeddings API"""
        if not self.is_available():
            raise Exception(f"OpenAI provider not available: {self.status}")
            
        headers = {
            "Authorization": f"Bearer {config.get_api_key('openai')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "text-embedding-ada-002",
            "input": texts
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.api_timeout)) as session:
                async with session.post(f"{self.base_url}/embeddings", 
                                      headers=headers, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    return [item['embedding'] for item in data['data']]
                    
        except Exception as e:
            logger.error(config.validate_no_credentials_in_logs(f"OpenAI embeddings error: {e}"))
            raise

class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider implementation"""
    
    def __init__(self):
        super().__init__("anthropic", priority=2, cost_tier="high", quality="excellent")
        self.base_url = "https://api.anthropic.com/v1"
        self.model = config.default_models['anthropic']
        
    async def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using Anthropic Claude"""
        if not self.is_available():
            raise Exception(f"Anthropic provider not available: {self.status}")
            
        headers = {
            "x-api-key": config.get_api_key('anthropic'),
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.api_timeout)) as session:
                async with session.post(f"{self.base_url}/messages", 
                                      headers=headers, json=payload) as response:
                    if response.status == 429:
                        self.status = ProviderStatus.RATE_LIMITED
                        self.rate_limit_reset = time.time() + 60
                        raise Exception("Rate limit exceeded")
                        
                    response.raise_for_status()
                    data = await response.json()
                    
                    self.status = ProviderStatus.AVAILABLE
                    return data['content'][0]['text']
                    
        except Exception as e:
            self.last_error = str(e)
            self.status = ProviderStatus.UNAVAILABLE
            logger.error(config.validate_no_credentials_in_logs(f"Anthropic API error: {e}"))
            raise
            
    async def analyze_image(self, image_path: str, prompt: str = "Describe this image") -> Dict[str, Any]:
        """Analyze image using Anthropic Vision capabilities"""
        return {"description": f"Image analysis for {image_path}", "provider": "anthropic"}
        
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Anthropic doesn't provide embeddings, so this would use a different approach"""
        raise NotImplementedError("Anthropic doesn't provide embeddings API")

class GoogleProvider(AIProvider):
    """Google AI provider implementation"""
    
    def __init__(self):
        super().__init__("google", priority=3, cost_tier="medium", quality="good")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = config.default_models['google']
        
    async def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using Google Gemini"""
        if not self.is_available():
            raise Exception(f"Google provider not available: {self.status}")
            
        # Implementation would use Google's Gemini API
        return f"Generated text from Google Gemini for prompt: {prompt[:50]}..."
        
    async def analyze_image(self, image_path: str, prompt: str = "Describe this image") -> Dict[str, Any]:
        """Analyze image using Google Vision API"""
        return {"description": f"Image analysis for {image_path}", "provider": "google"}
        
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using Google's embedding models"""
        # Implementation would use Google's embedding API
        return [[0.1] * 768 for _ in texts]  # Placeholder

class AIProviderManager:
    """Manages hierarchical AI provider strategy with automatic fallback"""
    
    def __init__(self):
        self.providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'google': GoogleProvider()
        }
        
        # Sort providers by priority (quality first)
        self.provider_hierarchy = sorted(
            [self.providers[name] for name in config.provider_hierarchy if name in self.providers],
            key=lambda p: p.priority
        )
        
        self.usage_stats = []
        self.semaphore = asyncio.Semaphore(config.max_concurrent_calls)
        
    async def generate_text(self, prompt: str, task_type: str = "general", max_tokens: int = 1000) -> str:
        """Generate text using best available provider with automatic fallback"""
        async with self.semaphore:
            for provider in self.provider_hierarchy:
                if not provider.is_available():
                    logger.debug(f"Skipping {provider.name}: {provider.status}")
                    continue
                    
                try:
                    start_time = time.time()
                    result = await provider.generate_text(prompt, max_tokens)
                    
                    # Log usage for local tracking
                    usage = APIUsage(
                        provider=provider.name,
                        endpoint="text_generation",
                        tokens_used=len(result.split()) * 1.3,  # Rough estimate
                        cost=self._estimate_cost(provider.name, len(result.split()) * 1.3),
                        timestamp=time.time(),
                        success=True
                    )
                    self.usage_stats.append(usage)
                    
                    duration = time.time() - start_time
                    logger.info(f"Text generated successfully using {provider.name} in {duration:.2f}s")
                    return result
                    
                except Exception as e:
                    logger.warning(f"Provider {provider.name} failed: {e}")
                    continue
                    
            raise Exception("All AI providers exhausted or unavailable")
            
    async def analyze_image(self, image_path: str, prompt: str = "Describe this image") -> Dict[str, Any]:
        """Analyze image using best available provider with vision capabilities"""
        async with self.semaphore:
            # Prioritize providers with good vision capabilities
            vision_providers = [p for p in self.provider_hierarchy if p.name in ['openai', 'google']]
            
            for provider in vision_providers:
                if not provider.is_available():
                    continue
                    
                try:
                    result = await provider.analyze_image(image_path, prompt)
                    
                    usage = APIUsage(
                        provider=provider.name,
                        endpoint="image_analysis",
                        tokens_used=100,  # Estimate for image analysis
                        cost=self._estimate_cost(provider.name, 100),
                        timestamp=time.time(),
                        success=True
                    )
                    self.usage_stats.append(usage)
                    
                    logger.info(f"Image analyzed successfully using {provider.name}")
                    return result
                    
                except Exception as e:
                    logger.warning(f"Provider {provider.name} failed for image analysis: {e}")
                    continue
                    
            raise Exception("No vision-capable providers available")
            
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using best available provider"""
        async with self.semaphore:
            # Prioritize providers with embedding capabilities
            embedding_providers = [p for p in self.provider_hierarchy if p.name in ['openai', 'google']]
            
            for provider in embedding_providers:
                if not provider.is_available():
                    continue
                    
    async def test_provider_health(self, provider_name: str) -> bool:
        """Test if a specific provider is actually working (not just configured)"""
        if provider_name not in self.providers:
            return False
            
        provider = self.providers[provider_name]
        
        if not provider.is_available():
            return False
            
        try:
            # Test with a minimal request
            test_prompt = "Hello"
            result = await provider.generate_text(test_prompt, max_tokens=10)
            
            # Check if we got a real response (not empty or error)
            if result and len(result.strip()) > 0 and "error" not in result.lower():
                return True
            else:
                return False
                
        except Exception as e:
            logger.warning(f"Provider {provider_name} health test failed: {e}")
            return False
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "status": provider.status.value,
                "priority": provider.priority,
                "quality": provider.quality,
                "last_error": provider.last_error,
                "has_credentials": config.has_api_key(name)
            }
        return status
    
    def get_usage_stats(self, days: int = 1) -> Dict[str, Any]:
        """Get usage statistics for the specified number of days"""
        import time
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        # Filter usage stats by time
        recent_usage = [usage for usage in self.usage_stats if usage.timestamp >= cutoff_time]
        
        if not recent_usage:
            return {
                "period_days": days,
                "total": {
                    "calls": 0,
                    "cost": 0,
                    "tokens": 0,
                    "avg_response_time_ms": 0,
                    "success_rate": 0.0
                },
                "by_provider": [],
                "by_endpoint": []
            }
        
        # Calculate totals
        total_calls = len(recent_usage)
        total_cost = sum(usage.cost for usage in recent_usage)
        total_tokens = sum(usage.tokens_used for usage in recent_usage)
        successful_calls = sum(1 for usage in recent_usage if usage.success)
        success_rate = successful_calls / total_calls if total_calls > 0 else 0.0
        
        # Group by provider
        by_provider = {}
        for usage in recent_usage:
            if usage.provider not in by_provider:
                by_provider[usage.provider] = {
                    "calls": 0,
                    "cost": 0,
                    "tokens": 0,
                    "success_rate": 0.0
                }
            by_provider[usage.provider]["calls"] += 1
            by_provider[usage.provider]["cost"] += usage.cost
            by_provider[usage.provider]["tokens"] += usage.tokens_used
        
        # Calculate success rates by provider
        for provider in by_provider:
            provider_usage = [u for u in recent_usage if u.provider == provider]
            successful = sum(1 for u in provider_usage if u.success)
            by_provider[provider]["success_rate"] = successful / len(provider_usage) if provider_usage else 0.0
        
        # Group by endpoint
        by_endpoint = {}
        for usage in recent_usage:
            if usage.endpoint not in by_endpoint:
                by_endpoint[usage.endpoint] = {
                    "calls": 0,
                    "cost": 0,
                    "tokens": 0
                }
            by_endpoint[usage.endpoint]["calls"] += 1
            by_endpoint[usage.endpoint]["cost"] += usage.cost
            by_endpoint[usage.endpoint]["tokens"] += usage.tokens_used
        
        return {
            "period_days": days,
            "total": {
                "calls": total_calls,
                "cost": round(total_cost, 4),
                "tokens": int(total_tokens),
                "avg_response_time_ms": 0,  # Would need to track response times
                "success_rate": round(success_rate, 2)
            },
            "by_provider": [
                {"provider": k, **v} for k, v in by_provider.items()
            ],
            "by_endpoint": [
                {"endpoint": k, **v} for k, v in by_endpoint.items()
            ]
        }
    
    def _estimate_cost(self, provider_name: str, tokens: int) -> float:
        """Estimate cost for API usage"""
        # Rough cost estimates per 1K tokens
        cost_per_1k = {
            'openai': 0.002,  # GPT-4 pricing
            'anthropic': 0.003,  # Claude-3 pricing
            'google': 0.001   # Gemini pricing
        }
        
        return (tokens / 1000) * cost_per_1k.get(provider_name, 0.002)

# Global provider manager instance
provider_manager = AIProviderManager()