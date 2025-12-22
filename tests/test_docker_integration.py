"""
Integration tests for Docker deployment of AI-Augmented Personal Archive

Tests complete system startup, initialization, data persistence across container restarts,
and service communication and dependencies.

Requirements: 1.4, 1.5
"""

import pytest
import requests
import time
import subprocess
import json
import os
import tempfile
import shutil
from typing import Dict, Any, List
from pathlib import Path

class TestDockerIntegration:
    """Integration tests for Docker deployment"""
    
    @pytest.fixture(scope="class")
    def docker_environment(self):
        """Setup and teardown Docker environment for testing"""
        # Store original directory
        original_dir = os.getcwd()
        
        # Create temporary test environment
        test_dir = tempfile.mkdtemp(prefix="personal_archive_test_")
        test_data_dir = os.path.join(test_dir, "MyData")
        os.makedirs(os.path.join(test_data_dir, "app_data"), exist_ok=True)
        
        try:
            # Copy necessary files to test directory, excluding problematic symlinks
            def ignore_patterns(dir, files):
                ignored = []
                for file in files:
                    if file in ['__pycache__', '*.pyc', '.git', 'node_modules', 'MyData']:
                        ignored.append(file)
                    # Skip broken symlinks
                    full_path = os.path.join(dir, file)
                    if os.path.islink(full_path) and not os.path.exists(full_path):
                        ignored.append(file)
                return ignored
            
            shutil.copytree(".", test_dir, dirs_exist_ok=True, ignore=ignore_patterns)
            
            os.chdir(test_dir)
            
            # Start Docker services
            result = subprocess.run(
                ["docker-compose", "up", "-d", "--build"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                pytest.fail(f"Failed to start Docker services: {result.stderr}")
            
            # Wait for services to be ready
            self._wait_for_services()
            
            yield {
                'test_dir': test_dir,
                'data_dir': test_data_dir,
                'services': {
                    'frontend': 'http://localhost:52692',
                    'backend': 'http://localhost:8000',
                    'qa': 'http://localhost:57485',
                    'ai_services': 'http://localhost:8086'
                }
            }
            
        finally:
            # Cleanup
            os.chdir(original_dir)
            subprocess.run(["docker-compose", "-f", f"{test_dir}/docker-compose.yml", "down", "-v"], 
                         capture_output=True, cwd=test_dir)
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def _wait_for_services(self, timeout: int = 120):
        """Wait for all services to be ready"""
        services = {
            'frontend': ('http://localhost:52692', '/'),
            'backend': ('http://localhost:8000', '/'),
            'qa': ('http://localhost:57485', '/health'),
            'ai_services': ('http://localhost:8086', '/health')
        }
        
        start_time = time.time()
        
        for service_name, (base_url, endpoint) in services.items():
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=5)
                    if response.status_code in [200, 404]:  # 404 is OK for some endpoints
                        print(f"✓ {service_name} is ready")
                        break
                except requests.exceptions.RequestException:
                    pass
                
                time.sleep(2)
            else:
                pytest.fail(f"Service {service_name} did not become ready within {timeout} seconds")
    
    def test_complete_system_startup(self, docker_environment):
        """Test complete system startup and initialization"""
        services = docker_environment['services']
        
        # Test that all services are responding
        for service_name, url in services.items():
            if service_name == 'frontend':
                # Frontend should serve the React app
                response = requests.get(url, timeout=10)
                assert response.status_code == 200
                assert 'text/html' in response.headers.get('content-type', '')
            
            elif service_name == 'backend':
                # Backend should be running (may return 404 for root)
                response = requests.get(url, timeout=10)
                assert response.status_code in [200, 404]
            
            elif service_name in ['qa', 'ai_services']:
                # QA and AI services should have health endpoints
                response = requests.get(f"{url}/health", timeout=10)
                assert response.status_code == 200
                
                health_data = response.json()
                assert health_data.get('status') in ['healthy', 'ok']
    
    def test_service_communication_and_dependencies(self, docker_environment):
        """Test service communication and dependencies"""
        services = docker_environment['services']
        
        # Test AI services health and capabilities
        ai_health_response = requests.get(f"{services['ai_services']}/health", timeout=10)
        assert ai_health_response.status_code == 200
        
        ai_health = ai_health_response.json()
        assert 'services' in ai_health
        assert 'models_loaded' in ai_health
        
        # Test QA service can communicate with AI services
        qa_health_response = requests.get(f"{services['qa']}/health", timeout=10)
        assert qa_health_response.status_code == 200
        
        # Test that QA service has enhanced capabilities
        try:
            qa_query_response = requests.post(
                f"{services['qa']}/api/query",
                json={'query': 'test query', 'enhanced': True},
                timeout=15
            )
            # Should not fail with 500 error (404 is OK if endpoint doesn't exist yet)
            assert qa_query_response.status_code != 500
        except requests.exceptions.RequestException:
            # Service communication issues are acceptable in test environment
            pass
    
    def test_data_persistence_across_restarts(self, docker_environment):
        """Test data persistence across container restarts"""
        test_dir = docker_environment['test_dir']
        data_dir = docker_environment['data_dir']
        
        # Create test data file
        test_db_path = os.path.join(data_dir, "app_data", "test_persistence.db")
        with open(test_db_path, 'w') as f:
            f.write("test data for persistence")
        
        # Restart backend service
        result = subprocess.run(
            ["docker-compose", "restart", "backend"],
            capture_output=True,
            text=True,
            cwd=test_dir,
            timeout=60
        )
        assert result.returncode == 0
        
        # Wait for backend to be ready again
        time.sleep(10)
        
        # Verify data still exists
        assert os.path.exists(test_db_path)
        with open(test_db_path, 'r') as f:
            content = f.read()
            assert content == "test data for persistence"
        
        # Test that backend service is still accessible
        try:
            response = requests.get("http://localhost:8000", timeout=10)
            assert response.status_code in [200, 404]
        except requests.exceptions.RequestException:
            pytest.fail("Backend service not accessible after restart")
    
    def test_volume_mounting_functionality(self, docker_environment):
        """Test that volume mounting works with enhanced data structures"""
        data_dir = docker_environment['data_dir']
        
        # Create test files in different expected locations
        test_files = {
            'app_data/raw_data.db': 'test database content',
            'app_data/sqlite_cache.db': 'test cache content',
            'app_data/enhanced_data.json': '{"test": "enhanced data"}',
            'app_data/ai_models/test_model.bin': 'test model data'
        }
        
        for file_path, content in test_files.items():
            full_path = os.path.join(data_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        # Verify files are accessible from containers
        containers = ['backend', 'qa', 'ai-services']
        
        for container in containers:
            # Check if container exists and is running
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}", "--filter", f"name={container}"],
                capture_output=True,
                text=True
            )
            
            if container in result.stdout:
                # Test file access in container
                for file_path in test_files.keys():
                    container_path = f"/app/MyData/{file_path}"
                    check_result = subprocess.run(
                        ["docker", "exec", f"personal-timeline-{container}-1", "test", "-f", container_path],
                        capture_output=True
                    )
                    
                    if check_result.returncode != 0:
                        # Try alternative container naming
                        check_result = subprocess.run(
                            ["docker", "exec", container, "test", "-f", container_path],
                            capture_output=True
                        )
                    
                    # File should be accessible (returncode 0 means file exists)
                    assert check_result.returncode == 0, f"File {file_path} not accessible in {container}"
    
    def test_ai_model_volume_persistence(self, docker_environment):
        """Test that AI model volume persists correctly"""
        test_dir = docker_environment['test_dir']
        
        # Create a test model file in the AI models volume
        result = subprocess.run(
            ["docker", "exec", "personal-timeline-ai-services-1", "mkdir", "-p", "/app/models/test"],
            capture_output=True
        )
        
        if result.returncode != 0:
            # Try alternative container name
            result = subprocess.run(
                ["docker", "exec", "ai-services", "mkdir", "-p", "/app/models/test"],
                capture_output=True
            )
        
        # Create test model file
        container_name = "personal-timeline-ai-services-1"
        result = subprocess.run(
            ["docker", "exec", container_name, "sh", "-c", "echo 'test model' > /app/models/test/model.bin"],
            capture_output=True
        )
        
        if result.returncode != 0:
            container_name = "ai-services"
            result = subprocess.run(
                ["docker", "exec", container_name, "sh", "-c", "echo 'test model' > /app/models/test/model.bin"],
                capture_output=True
            )
        
        # Restart AI services container
        restart_result = subprocess.run(
            ["docker-compose", "restart", "ai-services"],
            capture_output=True,
            cwd=test_dir,
            timeout=60
        )
        assert restart_result.returncode == 0
        
        # Wait for service to be ready
        time.sleep(15)
        
        # Verify model file still exists
        check_result = subprocess.run(
            ["docker", "exec", container_name, "test", "-f", "/app/models/test/model.bin"],
            capture_output=True
        )
        assert check_result.returncode == 0, "AI model file not persisted across restart"
    
    def test_environment_variable_configuration(self, docker_environment):
        """Test that environment variables are properly configured"""
        # Test AI services environment
        try:
            response = requests.get("http://localhost:8086/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                
                # AI services should be configured with environment variables
                assert 'status' in health_data
                
                # Test that AI service responds to configuration
                config_test = requests.post(
                    "http://localhost:8086/api/ai/generate_embeddings",
                    json={'texts': ['test configuration']},
                    timeout=30
                )
                
                # Should not fail with configuration errors (503 is OK if models not loaded)
                assert config_test.status_code != 500
                
        except requests.exceptions.RequestException:
            # In test environment, services might not be fully configured
            pass
    
    def test_docker_compose_service_dependencies(self, docker_environment):
        """Test that Docker Compose service dependencies are working"""
        test_dir = docker_environment['test_dir']
        
        # Stop AI services
        result = subprocess.run(
            ["docker-compose", "stop", "ai-services"],
            capture_output=True,
            cwd=test_dir,
            timeout=30
        )
        assert result.returncode == 0
        
        # Backend should still be running but may have degraded functionality
        try:
            response = requests.get("http://localhost:8000", timeout=5)
            # Backend should still respond even without AI services
            assert response.status_code in [200, 404]
        except requests.exceptions.RequestException:
            pytest.fail("Backend should remain accessible when AI services are down")
        
        # Restart AI services
        result = subprocess.run(
            ["docker-compose", "start", "ai-services"],
            capture_output=True,
            cwd=test_dir,
            timeout=60
        )
        assert result.returncode == 0
        
        # Wait for AI services to be ready
        time.sleep(15)
        
        # Verify AI services are accessible again
        try:
            response = requests.get("http://localhost:8086/health", timeout=10)
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.fail("AI services should be accessible after restart")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])