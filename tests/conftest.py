"""
Pytest configuration and shared fixtures
"""
import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_data_dir():
    """Provide a temporary directory for test data"""
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)
    yield test_dir
    
    # Cleanup
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)

@pytest.fixture
def api_base_url():
    """Base URL for API testing"""
    return "http://localhost:8086"

@pytest.fixture
def frontend_url():
    """Frontend URL for testing"""
    return "http://localhost:52692"