"""
Unit tests for AI provider functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.ai_services.providers import AIProviderManager, OpenAIProvider, ProviderStatus
from src.ai_services.config import config

class TestAIProviders:
    
    def test_provider_initialization(self):
        """Test that providers initialize correctly"""
        manager = AIProviderManager()
        assert len(manager.providers) == 3
        assert 'openai' in manager.providers
        assert 'anthropic' in manager.providers
        assert 'google' in manager.providers
    
    def test_provider_availability_without_credentials(self):
        """Test provider availability when no API keys are configured"""
        with patch.object(config, 'has_api_key', return_value=False):
            provider = OpenAIProvider()
            assert not provider.is_available()
            assert provider.status == ProviderStatus.NO_CREDENTIALS
    
    def test_provider_availability_with_credentials(self):
        """Test provider availability when API keys are configured"""
        with patch.object(config, 'has_api_key', return_value=True):
            provider = OpenAIProvider()
            assert provider.is_available()
            assert provider.status == ProviderStatus.AVAILABLE
    
    @pytest.mark.asyncio
    async def test_text_generation_success(self):
        """Test successful text generation"""
        with patch.object(config, 'has_api_key', return_value=True), \
             patch('aiohttp.ClientSession') as mock_session:
            
            # Mock successful API response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'choices': [{'message': {'content': 'Generated text'}}]
            })
            mock_response.raise_for_status = Mock()
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            provider = OpenAIProvider()
            result = await provider.generate_text("Test prompt")
            
            assert result == "Generated text"
            assert provider.status == ProviderStatus.AVAILABLE
    
    @pytest.mark.asyncio
    async def test_text_generation_rate_limit(self):
        """Test handling of rate limit errors"""
        with patch.object(config, 'has_api_key', return_value=True), \
             patch('aiohttp.ClientSession') as mock_session:
            
            # Mock rate limit response
            mock_response = AsyncMock()
            mock_response.status = 429
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            provider = OpenAIProvider()
            
            with pytest.raises(Exception, match="Rate limit exceeded"):
                await provider.generate_text("Test prompt")
            
            assert provider.status == ProviderStatus.RATE_LIMITED
    
    def test_usage_stats_tracking(self):
        """Test that usage statistics are tracked correctly"""
        manager = AIProviderManager()
        
        # Initially no usage
        stats = manager.get_usage_stats(days=1)
        assert stats['total']['calls'] == 0
        assert stats['total']['cost'] == 0
        
        # Add some mock usage
        from src.ai_services.providers import APIUsage
        import time
        
        usage = APIUsage(
            provider="openai",
            endpoint="text_generation",
            tokens_used=100,
            cost=0.002,
            timestamp=time.time(),
            success=True
        )
        manager.usage_stats.append(usage)
        
        stats = manager.get_usage_stats(days=1)
        assert stats['total']['calls'] == 1
        assert stats['total']['cost'] == 0.002
        assert len(stats['by_provider']) == 1
        assert stats['by_provider'][0]['provider'] == 'openai'