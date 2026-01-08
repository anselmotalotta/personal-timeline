"""
AI Services Configuration Management
Handles secure local environment variable loading for API keys
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment variables

logger = logging.getLogger(__name__)

class AIConfig:
    """Centralized AI configuration with secure local token management"""
    
    def __init__(self):
        self.data_path = Path(os.getenv('DATA_PATH', './MyData'))
        self.debug_logging = os.getenv('DEBUG_LOGGING', 'false').lower() == 'true'
        
        # AI provider configuration
        self.provider_hierarchy = os.getenv('AI_PROVIDER_HIERARCHY', 'openai,anthropic,google').split(',')
        
        # API configuration (secure local loading)
        self.api_keys = self._load_api_keys_securely()
        
        # Processing configuration
        self.max_concurrent_calls = int(os.getenv('MAX_CONCURRENT_API_CALLS', '5'))
        self.api_timeout = int(os.getenv('API_TIMEOUT_SECONDS', '30'))
        self.local_cache_ttl_minutes = int(os.getenv('LOCAL_CACHE_TTL_MINUTES', '5'))  # Changed to minutes, default 5
        
        # Model configuration
        self.default_models = {
            'openai': os.getenv('DEFAULT_MODEL_OPENAI', 'gpt-4'),
            'anthropic': os.getenv('DEFAULT_MODEL_ANTHROPIC', 'claude-3-sonnet-20240229'),
            'google': os.getenv('DEFAULT_MODEL_GOOGLE', 'gemini-pro')
        }
        
        # Privacy settings
        self.enable_usage_analytics = os.getenv('ENABLE_USAGE_ANALYTICS', 'true').lower() == 'true'
        self.enable_error_reporting = os.getenv('ENABLE_ERROR_REPORTING', 'false').lower() == 'true'
        self.keep_api_logs_days = int(os.getenv('KEEP_API_LOGS_DAYS', '7'))
        
    def _load_api_keys_securely(self) -> Dict[str, Optional[str]]:
        """Securely load API keys from local environment variables only"""
        keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY'),
            'google': os.getenv('GOOGLE_API_KEY')
        }
        
        # Log which keys are available (without exposing values)
        available_keys = [k for k, v in keys.items() if v]
        if available_keys:
            logger.info(f"API keys loaded for providers: {', '.join(available_keys)}")
        else:
            logger.warning("No API keys found in environment variables")
            
        # Validate keys are not hardcoded or exposed
        for provider, key in keys.items():
            if key and (len(key) < 10 or key.startswith('your_') or key == 'placeholder'):
                logger.error(f"Invalid or placeholder API key detected for {provider}")
                keys[provider] = None
                
        return keys
    
    def has_api_key(self, provider: str) -> bool:
        """Check if API key is available for provider"""
        return self.api_keys.get(provider) is not None
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for provider (never log or expose)"""
        return self.api_keys.get(provider)
    
    def get_data_path(self) -> Path:
        """Get the local data directory path"""
        return self.data_path
    
    def ensure_data_path(self) -> Path:
        """Ensure local data path exists and return it"""
        self.data_path.mkdir(parents=True, exist_ok=True)
        return self.data_path
    
    def validate_no_credentials_in_logs(self, log_message: str) -> str:
        """Ensure no credentials are exposed in log messages"""
        # Remove any potential API keys from log messages
        for provider, key in self.api_keys.items():
            if key and key in log_message:
                log_message = log_message.replace(key, f"[{provider.upper()}_API_KEY_REDACTED]")
        return log_message

# Global configuration instance
config = AIConfig()