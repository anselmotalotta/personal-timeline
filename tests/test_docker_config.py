"""
Docker configuration tests for AI-Augmented Personal Archive

Tests Docker configuration files and setup without requiring full container deployment.
This provides faster feedback on configuration correctness.

Requirements: 1.4, 1.5
"""

import pytest
import os
import json
from pathlib import Path

class TestDockerConfiguration:
    """Test Docker configuration files and setup"""
    
    def test_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists and has required services"""
        assert os.path.exists("docker-compose.yml"), "docker-compose.yml file not found"
        
        with open("docker-compose.yml", 'r') as f:
            compose_content = f.read()
        
        # Check that all required services are defined
        required_services = ['frontend:', 'backend:', 'qa:', 'ai-services:']
        for service in required_services:
            assert service in compose_content, f"Service {service.rstrip(':')} not defined"
    
    def test_ai_services_configuration(self):
        """Test AI services configuration in docker-compose.yml"""
        with open("docker-compose.yml", 'r') as f:
            compose_content = f.read()
        
        # Check AI services configuration
        assert 'ai-services:' in compose_content, "AI services not defined"
        assert 'Dockerfile.ai-services' in compose_content, "AI services Dockerfile not specified"
        assert '8086:8086' in compose_content, "AI services port not mapped"
        assert 'AI_MODEL_DIR' in compose_content, "AI model directory not configured"
        assert 'ai-models:/app/models' in compose_content, "AI models volume not mounted"
    
    def test_service_dependencies(self):
        """Test that service dependencies are properly configured"""
        with open("docker-compose.yml", 'r') as f:
            compose_content = f.read()
        
        # Check dependencies using text search
        assert 'depends_on:' in compose_content, "No service dependencies configured"
        
        # Frontend should depend on backend, qa, and ai-services
        frontend_section = self._extract_service_section(compose_content, 'frontend')
        assert 'backend' in frontend_section, "Frontend missing backend dependency"
        assert 'qa' in frontend_section, "Frontend missing QA dependency"
        assert 'ai-services' in frontend_section, "Frontend missing AI services dependency"
        
        # QA should depend on backend and ai-services
        qa_section = self._extract_service_section(compose_content, 'qa')
        assert 'backend' in qa_section, "QA missing backend dependency"
        assert 'ai-services' in qa_section, "QA missing AI services dependency"
        
        # Backend should depend on ai-services
        backend_section = self._extract_service_section(compose_content, 'backend')
        assert 'ai-services' in backend_section, "Backend missing AI services dependency"
    
    def _extract_service_section(self, content: str, service_name: str) -> str:
        """Extract a service section from docker-compose content"""
        lines = content.split('\n')
        service_lines = []
        in_service = False
        
        for line in lines:
            if line.strip() == f'{service_name}:':
                in_service = True
                continue
            elif in_service and line.startswith('  ') and ':' in line and not line.startswith('    '):
                # Next service started
                break
            elif in_service:
                service_lines.append(line)
        
        return '\n'.join(service_lines)
    
    def test_dockerfile_ai_services_exists(self):
        """Test that Dockerfile.ai-services exists and has correct content"""
        assert os.path.exists("Dockerfile.ai-services"), "Dockerfile.ai-services not found"
        
        with open("Dockerfile.ai-services", 'r') as f:
            dockerfile_content = f.read()
        
        # Check for required components
        assert 'FROM python:3.10-slim' in dockerfile_content, "Base image not specified correctly"
        assert 'EXPOSE 8086' in dockerfile_content, "Port 8086 not exposed"
        assert '/app/models' in dockerfile_content, "AI models directory not configured"
        assert 'HEALTHCHECK' in dockerfile_content, "Health check not configured"
        assert 'ai_service_manager' in dockerfile_content, "AI service manager not specified as entry point"
    
    def test_environment_configuration_template(self):
        """Test that environment configuration template exists"""
        assert os.path.exists(".env.example"), ".env.example file not found"
        
        with open(".env.example", 'r') as f:
            env_content = f.read()
        
        # Check for required environment variables
        required_vars = [
            'LOCAL_LLM_MODEL', 'EMBEDDING_MODEL', 'TTS_MODEL', 'MULTIMODAL_MODEL',
            'AI_PROCESSING_BATCH_SIZE', 'AI_MAX_MEMORY_GB', 'ENABLE_GPU',
            'ENABLE_AI_ENHANCEMENT', 'ENHANCED_QA_ENABLED'
        ]
        
        for var in required_vars:
            assert var in env_content, f"Environment variable {var} not documented in .env.example"
    
    def test_ai_service_manager_exists(self):
        """Test that AI service manager module exists"""
        ai_service_path = "src/common/services/ai_service_manager.py"
        assert os.path.exists(ai_service_path), "AI service manager not found"
        
        with open(ai_service_path, 'r') as f:
            content = f.read()
        
        # Check for required classes and functions
        assert 'class AIServiceManager' in content, "AIServiceManager class not found"
        assert 'def run(' in content, "Run method not found"
        assert '/health' in content, "Health endpoint not configured"
        assert '/api/ai/' in content, "AI API endpoints not configured"
    
    def test_enhanced_startup_script(self):
        """Test that enhanced startup script exists and has AI integration"""
        startup_script = "src/ingest/ingestion_startup.sh"
        assert os.path.exists(startup_script), "Enhanced startup script not found"
        
        with open(startup_script, 'r') as f:
            content = f.read()
        
        # Check for AI enhancement integration
        assert 'ENABLE_AI_ENHANCEMENT' in content, "AI enhancement toggle not found"
        assert 'AI_SERVICES_URL' in content, "AI services URL not configured"
        assert 'ai_enhancement_pipeline' in content, "AI enhancement pipeline not integrated"
        assert 'curl -f' in content, "Health check for AI services not found"
    
    def test_volume_configuration(self):
        """Test that Docker volumes are properly configured"""
        with open("docker-compose.yml", 'r') as f:
            compose_content = f.read()
        
        # Check that ai-models volume is defined
        assert 'volumes:' in compose_content, "No volumes section in docker-compose.yml"
        assert 'ai-models:' in compose_content, "ai-models volume not defined"
        assert 'driver: local' in compose_content, "ai-models volume not using local driver"
    
    def test_enhanced_qa_server_integration(self):
        """Test that QA service is configured to use enhanced server"""
        with open("docker-compose.yml", 'r') as f:
            compose_content = f.read()
        
        # Check that QA service uses enhanced server
        qa_section = self._extract_service_section(compose_content, 'qa')
        assert 'enhanced_qa_server' in qa_section, "QA service not using enhanced server"
        assert 'AI_SERVICES_URL' in qa_section, "QA service missing AI services URL"
        assert 'ENHANCED_QA_ENABLED' in qa_section, "QA service missing enhanced QA toggle"
    
    def test_verification_script_exists(self):
        """Test that enhanced verification script exists"""
        script_path = "scripts/verify_enhanced_docker_setup.sh"
        assert os.path.exists(script_path), "Enhanced verification script not found"
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check that script tests all services
        assert 'AI Services' in content, "AI services check not found"
        assert '8086' in content, "AI services port check not found"
        assert '/health' in content, "Health endpoint check not found"
        assert 'ai-models' in content, "AI models volume check not found"
    
    def test_ai_enhancement_pipeline_exists(self):
        """Test that AI enhancement pipeline module exists"""
        pipeline_path = "src/common/services/ai_enhancement_pipeline.py"
        assert os.path.exists(pipeline_path), "AI enhancement pipeline not found"
        
        with open(pipeline_path, 'r') as f:
            content = f.read()
        
        # Check for required functionality
        assert 'class AIEnhancementPipeline' in content, "AIEnhancementPipeline class not found"
        assert 'run_enhancement' in content, "run_enhancement method not found"
        assert 'AI_SERVICES_URL' in content, "AI services integration not found"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])