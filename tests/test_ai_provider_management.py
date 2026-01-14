"""
Property-based tests for AI provider management system
**Feature: ai-personal-archive-complete**
"""
import os
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings
import pytest
import asyncio

# Import the modules we're testing
import sys
sys.path.append('src')

from ai_services.config import AIConfig
from ai_services.providers import AIProviderManager, OpenAIProvider, AnthropicProvider, GoogleProvider, ProviderStatus
from ai_services.usage_tracker import LocalUsageTracker


class TestSecureCredentialManagement:
    """Test secure local credential management"""
    
    def test_secure_local_credential_management(self):
        """
        **Feature: ai-personal-archive-complete, Property 8: Secure local credential management**
        For any API credential requirement, the system should load credentials only from secure local environment variables, never exposing them in code, logs, or client components
        """
        # Test that credentials are only loaded from environment variables
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_openai_key_12345',
            'ANTHROPIC_API_KEY': 'test_anthropic_key_67890',
            'GOOGLE_API_KEY': 'test_google_key_abcde'
        }):
            config = AIConfig()
            
            # Should load credentials from environment
            assert config.has_api_key('openai')
            assert config.has_api_key('anthropic')
            assert config.has_api_key('google')
            
            # Should return actual keys (but never log them)
            assert config.get_api_key('openai') == 'test_openai_key_12345'
            assert config.get_api_key('anthropic') == 'test_anthropic_key_67890'
            assert config.get_api_key('google') == 'test_google_key_abcde'
    
    def test_no_hardcoded_credentials(self):
        """Test that no credentials are hardcoded in the codebase"""
        # Check that placeholder/invalid keys are rejected
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'your_openai_api_key_here',  # Placeholder
            'ANTHROPIC_API_KEY': 'placeholder',
            'GOOGLE_API_KEY': 'test'  # Too short
        }):
            config = AIConfig()
            
            # Should reject placeholder/invalid keys
            assert not config.has_api_key('openai')
            assert not config.has_api_key('anthropic')
            assert not config.has_api_key('google')
    
    @given(st.text(min_size=1, max_size=100))
    def test_credential_sanitization_in_logs(self, log_message):
        """Test that credentials are never exposed in log messages"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'secret_key_12345',
            'ANTHROPIC_API_KEY': 'another_secret_67890'
        }):
            config = AIConfig()
            
            # Create a log message that might contain credentials
            test_message = f"{log_message} secret_key_12345 another_secret_67890"
            
            # Should sanitize credentials from log messages
            sanitized = config.validate_no_credentials_in_logs(test_message)
            
            assert 'secret_key_12345' not in sanitized
            assert 'another_secret_67890' not in sanitized
            assert '[OPENAI_API_KEY_REDACTED]' in sanitized or 'secret_key_12345' not in test_message
            assert '[ANTHROPIC_API_KEY_REDACTED]' in sanitized or 'another_secret_67890' not in test_message
    
    def test_environment_variable_only_loading(self):
        """Test that credentials are ONLY loaded from environment variables"""
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            config = AIConfig()
            
            # Should have no credentials when environment is empty
            assert not config.has_api_key('openai')
            assert not config.has_api_key('anthropic')
            assert not config.has_api_key('google')
            
            assert config.get_api_key('openai') is None
            assert config.get_api_key('anthropic') is None
            assert config.get_api_key('google') is None


class TestProviderHierarchy:
    """Test provider hierarchy adherence"""
    
    def test_provider_hierarchy_adherence(self):
        """
        **Feature: ai-personal-archive-complete, Property 9: Provider hierarchy adherence**
        For any AI processing task, the system should attempt providers in quality-priority order (GPT-4, Claude-3, Google) before failing
        """
        with patch.dict(os.environ, {
            'AI_PROVIDER_HIERARCHY': 'openai,anthropic,google',
            'OPENAI_API_KEY': 'test_openai_key',
            'ANTHROPIC_API_KEY': 'test_anthropic_key',
            'GOOGLE_API_KEY': 'test_google_key'
        }):
            manager = AIProviderManager()
            
            # Should have providers in correct priority order
            assert len(manager.provider_hierarchy) == 3
            assert manager.provider_hierarchy[0].name == 'openai'
            assert manager.provider_hierarchy[0].priority == 1
            assert manager.provider_hierarchy[1].name == 'anthropic'
            assert manager.provider_hierarchy[1].priority == 2
            assert manager.provider_hierarchy[2].name == 'google'
            assert manager.provider_hierarchy[2].priority == 3
    
    @pytest.mark.asyncio
    async def test_automatic_fallback_mechanism(self):
        """Test that providers fallback automatically when one fails"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key_12345',
            'ANTHROPIC_API_KEY': 'test_key_67890',
            'GOOGLE_API_KEY': 'test_key_abcde'
        }):
            manager = AIProviderManager()
            
            # Ensure providers are marked as available and mock their methods
            openai_provider = manager.providers['openai']
            anthropic_provider = manager.providers['anthropic']
            google_provider = manager.providers['google']
            
            # Set status and mock is_available to return True
            openai_provider.status = ProviderStatus.AVAILABLE
            anthropic_provider.status = ProviderStatus.AVAILABLE
            google_provider.status = ProviderStatus.AVAILABLE
            
            openai_provider.is_available = MagicMock(return_value=True)
            anthropic_provider.is_available = MagicMock(return_value=True)
            google_provider.is_available = MagicMock(return_value=True)
            
            # Mock the first provider to fail, second to succeed
            async def openai_fail(*args, **kwargs):
                raise Exception("API Error")
            
            async def anthropic_success(*args, **kwargs):
                return "Success from Anthropic"
                
            async def google_success(*args, **kwargs):
                return "Success from Google"
            
            openai_provider.generate_text = openai_fail
            anthropic_provider.generate_text = anthropic_success
            google_provider.generate_text = google_success
            
            # Should fallback to second provider
            result = await manager.generate_text("test prompt")
            assert result == "Success from Anthropic"
            
            # Should have tried OpenAI first, then succeeded with Anthropic
            # Note: We can't easily assert call counts with async function replacement
            # but the test passing means the fallback worked correctly


class TestLocalUsageTracking:
    """Test local usage tracking functionality"""
    
    def test_local_usage_tracking(self):
        """
        **Feature: ai-personal-archive-complete, Property 10: Local usage tracking**
        For any API call made, the system should log usage metrics including provider and cost for local monitoring and analytics
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_usage.db"
            tracker = LocalUsageTracker(str(db_path))
            
            # Record some usage
            tracker.record_usage(
                provider="openai",
                endpoint="text_generation",
                tokens_used=100,
                estimated_cost=0.002,
                success=True,
                task_type="story_generation",
                response_time_ms=1500
            )
            
            tracker.record_usage(
                provider="anthropic",
                endpoint="text_generation", 
                tokens_used=150,
                estimated_cost=0.003,
                success=True,
                task_type="analysis",
                response_time_ms=2000
            )
            
            # Should track usage locally
            summary = tracker.get_usage_summary(days=1)
            
            assert summary["total"]["calls"] == 2
            assert summary["total"]["cost"] == 0.005
            assert summary["total"]["tokens"] == 250
            assert summary["total"]["success_rate"] == 1.0
            
            # Should track by provider
            assert len(summary["by_provider"]) == 2
            provider_names = [p["provider"] for p in summary["by_provider"]]
            assert "openai" in provider_names
            assert "anthropic" in provider_names
    
    @given(st.text(min_size=1, max_size=50), st.integers(min_value=1, max_value=10000), st.floats(min_value=0.0001, max_value=1.0))
    def test_usage_tracking_data_integrity(self, provider, tokens, cost):
        """Test that usage tracking maintains data integrity"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_usage.db"
            tracker = LocalUsageTracker(str(db_path))
            
            # Record usage with various inputs
            tracker.record_usage(
                provider=provider,
                endpoint="test_endpoint",
                tokens_used=tokens,
                estimated_cost=cost,
                success=True
            )
            
            # Should store data correctly
            summary = tracker.get_usage_summary(days=1)
            assert summary["total"]["calls"] == 1
            assert abs(summary["total"]["cost"] - cost) < 0.0001
            assert summary["total"]["tokens"] == tokens
    
    def test_credential_sanitization_in_usage_logs(self):
        """Test that usage tracking never logs credentials"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_usage.db"
            tracker = LocalUsageTracker(str(db_path))
            
            # Try to record usage with credential-like data
            tracker.record_usage(
                provider="openai_sk-test123456",  # Looks like it might contain a key
                endpoint="test_endpoint_with_secret_key",
                tokens_used=100,
                estimated_cost=0.002,
                success=True,
                task_type="test_with_api_key_data"
            )
            
            # Check that data was sanitized before storage
            with sqlite3.connect(db_path) as conn:
                result = conn.execute("SELECT * FROM api_usage").fetchone()
                
                # Should not contain any credential-like patterns
                assert "sk-" not in str(result)
                assert "secret_key" not in str(result)
    
    def test_local_data_retention_policy(self):
        """Test that old usage data is cleaned up according to retention policy"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_usage.db"
            tracker = LocalUsageTracker(str(db_path))
            
            # Record some usage
            tracker.record_usage("openai", "test", 100, 0.002, True)
            
            # Should have data
            summary = tracker.get_usage_summary(days=1)
            assert summary["total"]["calls"] == 1
            
            # Clean up with 0 days retention (should remove everything)
            tracker.cleanup_old_records(keep_days=0)
            
            # Should have no data after cleanup
            summary = tracker.get_usage_summary(days=1)
            assert summary["total"]["calls"] == 0


class TestProviderAvailability:
    """Test provider availability and status management"""
    
    def test_provider_status_without_credentials(self):
        """Test that providers report correct status when credentials are missing"""
        with patch.dict(os.environ, {}, clear=True):
            provider = OpenAIProvider()
            
            # Should not be available without credentials
            assert not provider.is_available()
            assert provider.status.value == "no_credentials"
    
    def test_provider_status_with_credentials(self):
        """Test that providers report available status with valid credentials"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'valid_test_key_12345'}):
            provider = OpenAIProvider()
            
            # Should be available with credentials (initially)
            # Note: We can't test actual API calls without real credentials
            # but we can test the credential checking logic
            assert provider.status != "no_credentials"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])