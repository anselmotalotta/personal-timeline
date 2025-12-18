# Task 1.1.1: Development Environment Setup

**Epic**: 1.1 Development Environment & DevOps  
**Phase**: 1 - Foundation & Core Infrastructure  
**Duration**: 3 days  
**Assignee**: DevOps Engineer + Backend Developer  
**Priority**: Critical  
**Dependencies**: None  

---

## Task Overview

Set up a complete local development environment that allows developers to run the entire Personal Timeline application stack locally with minimal setup. This includes containerization, database setup, service orchestration, and development tooling.

---

## User Stories Covered

**US-DEV-001: Development Environment Setup**
- As a developer, I want to set up the complete application locally so that I can develop and test features efficiently
- As a new team member, I want to get the development environment running quickly so that I can start contributing immediately
- As a developer, I want hot reloading and fast feedback loops so that I can iterate quickly during development

---

## Detailed Requirements

### Functional Requirements

**REQ-DEV-001: Docker-based Development Stack**
- Complete application stack must run with single command (`docker-compose up`)
- All services must be containerized (backend API, frontend, database, cache, queue)
- Development containers must support hot reloading for code changes
- Container networking must allow service-to-service communication
- Persistent volumes must preserve data between container restarts

**REQ-DEV-002: Database Development Setup**
- PostgreSQL database with development schema and sample data
- Database migrations must run automatically on startup
- Database seeding with realistic test data for development
- Database admin interface (pgAdmin or similar) for debugging
- Backup and restore capabilities for development data

**REQ-DEV-003: Development Tooling Integration**
- Code formatting and linting tools integrated
- Pre-commit hooks for code quality enforcement
- Environment variable management for different configurations
- Log aggregation and viewing for all services
- Health check endpoints for all services

**REQ-DEV-004: Frontend Development Setup**
- React development server with hot module replacement
- TypeScript compilation with watch mode
- CSS/SCSS processing with live reload
- Asset optimization for development builds
- Source map generation for debugging

**REQ-DEV-005: Backend Development Setup**
- FastAPI development server with auto-reload
- Python virtual environment management
- Database connection pooling for development
- API documentation auto-generation and serving
- Background task processing with Celery

### Non-Functional Requirements

**REQ-DEV-NFR-001: Performance**
- Initial setup time under 10 minutes on modern hardware
- Hot reload response time under 2 seconds for code changes
- Container startup time under 30 seconds for full stack
- Memory usage under 4GB for complete development stack
- CPU usage under 50% during normal development activities

**REQ-DEV-NFR-002: Reliability**
- Development environment must be reproducible across different machines
- Container orchestration must handle service failures gracefully
- Data persistence must survive container restarts and updates
- Network connectivity must be stable between services
- Error messages must be clear and actionable for troubleshooting

**REQ-DEV-NFR-003: Usability**
- Single command setup for new developers
- Clear documentation for common development tasks
- Intuitive service discovery and debugging
- Consistent development experience across team members
- Easy switching between different development configurations

---

## Technical Specifications

### Docker Compose Architecture

**Service Definitions**:
```yaml
# Core application services
- personal-timeline-api: FastAPI backend service
- personal-timeline-web: React frontend service
- personal-timeline-worker: Celery background worker
- personal-timeline-scheduler: Celery beat scheduler

# Infrastructure services
- postgres: PostgreSQL database
- redis: Redis cache and message broker
- pgadmin: Database administration interface
- mailhog: Email testing service (development)

# Development tools
- nginx: Reverse proxy for service routing
- elasticsearch: Search engine (optional for development)
- kibana: Log visualization (optional for development)
```

**Network Configuration**:
- Custom bridge network for service communication
- Port mapping for external access to key services
- Service discovery via Docker DNS
- Load balancing for multiple service instances

**Volume Management**:
- Named volumes for database persistence
- Bind mounts for source code hot reloading
- Shared volumes for file uploads and media
- Backup volumes for data protection

### Development Scripts and Automation

**Setup Scripts**:
- `scripts/dev-setup.sh`: Initial development environment setup
- `scripts/dev-start.sh`: Start development services
- `scripts/dev-stop.sh`: Stop development services
- `scripts/dev-reset.sh`: Reset development environment
- `scripts/dev-logs.sh`: View aggregated service logs

**Database Management**:
- `scripts/db-migrate.sh`: Run database migrations
- `scripts/db-seed.sh`: Seed database with test data
- `scripts/db-backup.sh`: Backup development database
- `scripts/db-restore.sh`: Restore database from backup
- `scripts/db-reset.sh`: Reset database to clean state

**Code Quality Tools**:
- `scripts/lint.sh`: Run linting on all code
- `scripts/format.sh`: Format code according to standards
- `scripts/test.sh`: Run all tests in development environment
- `scripts/type-check.sh`: Run TypeScript type checking
- `scripts/security-scan.sh`: Run security vulnerability scans

### Environment Configuration

**Environment Variables**:
```bash
# Application Configuration
APP_ENV=development
DEBUG=true
LOG_LEVEL=debug

# Database Configuration
DATABASE_URL=postgresql://dev_user:dev_pass@postgres:5432/personal_timeline_dev
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
FAST_REFRESH=true

# External Services (Development)
OPENAI_API_KEY=sk-dev-key-placeholder
AWS_ACCESS_KEY_ID=dev-access-key
AWS_SECRET_ACCESS_KEY=dev-secret-key
AWS_S3_BUCKET=personal-timeline-dev

# Email Configuration (Development)
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USER=dev
SMTP_PASSWORD=dev
```

**Configuration Management**:
- `.env.development`: Development-specific environment variables
- `.env.local`: Local developer overrides (gitignored)
- `docker-compose.override.yml`: Local Docker Compose overrides
- `config/development.py`: Python configuration for development
- `config/development.json`: Frontend configuration for development

---

## Implementation Tasks

### Task 1.1.1.1: Docker Infrastructure Setup
**Duration**: 1 day  
**Assignee**: DevOps Engineer

**Subtasks**:
1. Create base Docker Compose configuration
   - Define all required services with proper networking
   - Configure volume mounts for code and data persistence
   - Set up environment variable management
   - Configure service dependencies and startup order

2. Create Dockerfiles for each service
   - Multi-stage Dockerfile for backend API (development + production stages)
   - Dockerfile for frontend development server
   - Dockerfile for Celery worker with development tools
   - Optimize Docker layers for fast rebuilds

3. Set up development networking
   - Configure custom bridge network for services
   - Set up port mapping for external access
   - Configure service discovery and DNS resolution
   - Set up reverse proxy for unified access

4. Implement health checks
   - Health check endpoints for all services
   - Docker health check configuration
   - Service dependency health verification
   - Automated service restart on health failures

**Acceptance Criteria**:
- [ ] All services start successfully with `docker-compose up`
- [ ] Services can communicate with each other via service names
- [ ] Health checks pass for all services
- [ ] Logs are accessible via `docker-compose logs`
- [ ] Services restart automatically on failure
- [ ] Port mapping allows external access to key services

### Task 1.1.1.2: Database Development Setup
**Duration**: 1 day  
**Assignee**: Backend Developer

**Subtasks**:
1. PostgreSQL container configuration
   - Configure PostgreSQL with development settings
   - Set up database user and permissions
   - Configure connection pooling and performance settings
   - Set up database backup and restore procedures

2. Database schema and migrations
   - Create initial database schema
   - Set up Alembic for database migrations
   - Create migration scripts for development data
   - Implement automatic migration on container startup

3. Development data seeding
   - Create realistic test data for all entities
   - Implement data seeding scripts
   - Set up data fixtures for different scenarios
   - Create data reset and cleanup procedures

4. Database administration tools
   - Set up pgAdmin container for database management
   - Configure database monitoring and logging
   - Set up query performance analysis tools
   - Create database backup and restore scripts

**Acceptance Criteria**:
- [ ] PostgreSQL container starts with correct configuration
- [ ] Database schema is created automatically
- [ ] Sample data is seeded on first startup
- [ ] pgAdmin is accessible and configured
- [ ] Database migrations run automatically
- [ ] Backup and restore procedures work correctly

### Task 1.1.1.3: Development Tooling Integration
**Duration**: 1 day  
**Assignee**: DevOps Engineer + Backend Developer

**Subtasks**:
1. Code quality tools setup
   - Configure ESLint and Prettier for frontend
   - Set up Black, isort, and flake8 for backend
   - Create pre-commit hooks for code quality
   - Set up automated code formatting on save

2. Development scripts creation
   - Create setup and management scripts
   - Implement log aggregation and viewing
   - Set up environment variable management
   - Create debugging and troubleshooting tools

3. Hot reloading configuration
   - Configure React hot module replacement
   - Set up FastAPI auto-reload for backend
   - Configure file watching for automatic restarts
   - Optimize rebuild times for development

4. Documentation and onboarding
   - Create comprehensive README for setup
   - Document common development workflows
   - Create troubleshooting guide
   - Set up developer onboarding checklist

**Acceptance Criteria**:
- [ ] Code quality tools run automatically on commit
- [ ] Hot reloading works for both frontend and backend
- [ ] Development scripts are functional and documented
- [ ] New developers can set up environment in under 10 minutes
- [ ] All development workflows are documented
- [ ] Troubleshooting guide covers common issues

---

## Testing Requirements

### Unit Testing Setup
- Jest configuration for frontend unit tests
- pytest configuration for backend unit tests
- Test database setup with fixtures
- Mock configuration for external services
- Code coverage reporting setup

### Integration Testing Setup
- Test containers for integration tests
- API testing framework setup
- Database integration test configuration
- Service-to-service communication testing
- End-to-end test environment preparation

### Performance Testing Setup
- Development performance monitoring
- Resource usage tracking
- Build time optimization
- Hot reload performance measurement
- Container startup time optimization

---

## Quality Assurance

### Code Quality Standards
- ESLint configuration with TypeScript rules
- Prettier configuration for consistent formatting
- Python code quality with Black, isort, flake8
- Pre-commit hooks for automated quality checks
- Code review checklist for development setup

### Documentation Standards
- README with clear setup instructions
- Inline code documentation for complex configurations
- Architecture decision records for setup choices
- Troubleshooting guide with common issues
- Developer onboarding documentation

### Security Considerations
- Development secrets management
- Container security best practices
- Network security for development environment
- Data protection in development
- Secure defaults for all configurations

---

## Deliverables

### Configuration Files
- [ ] `docker-compose.yml`: Main Docker Compose configuration
- [ ] `docker-compose.override.yml`: Development overrides
- [ ] `.env.development`: Development environment variables
- [ ] `Dockerfile.api`: Backend API container
- [ ] `Dockerfile.web`: Frontend container
- [ ] `Dockerfile.worker`: Celery worker container

### Scripts and Automation
- [ ] `scripts/dev-setup.sh`: Environment setup script
- [ ] `scripts/dev-start.sh`: Start development services
- [ ] `scripts/dev-stop.sh`: Stop development services
- [ ] `scripts/dev-reset.sh`: Reset development environment
- [ ] `scripts/db-migrate.sh`: Database migration script
- [ ] `scripts/db-seed.sh`: Database seeding script

### Documentation
- [ ] `README.md`: Comprehensive setup guide
- [ ] `docs/DEVELOPMENT.md`: Development workflow guide
- [ ] `docs/TROUBLESHOOTING.md`: Common issues and solutions
- [ ] `docs/ARCHITECTURE.md`: Development environment architecture
- [ ] `docs/ONBOARDING.md`: New developer onboarding guide

### Quality Assurance
- [ ] `.pre-commit-config.yaml`: Pre-commit hooks configuration
- [ ] `.eslintrc.js`: ESLint configuration
- [ ] `.prettierrc`: Prettier configuration
- [ ] `pyproject.toml`: Python project configuration
- [ ] `pytest.ini`: pytest configuration

---

## Success Metrics

### Performance Metrics
- **Setup Time**: < 10 minutes for new developer setup
- **Hot Reload Time**: < 2 seconds for code changes
- **Container Startup**: < 30 seconds for full stack
- **Memory Usage**: < 4GB for complete development stack
- **Build Time**: < 5 minutes for full application build

### Quality Metrics
- **Documentation Coverage**: 100% of setup procedures documented
- **Script Reliability**: 100% success rate for setup scripts
- **Developer Satisfaction**: > 90% positive feedback on setup experience
- **Issue Resolution**: < 1 hour average time to resolve setup issues
- **Onboarding Success**: 100% of new developers successfully set up environment

### Reliability Metrics
- **Environment Consistency**: 100% reproducible across different machines
- **Service Uptime**: > 99% uptime for development services
- **Data Persistence**: 100% data retention across container restarts
- **Error Recovery**: < 5 minutes to recover from service failures
- **Backup Success**: 100% success rate for backup and restore operations

---

## Risk Assessment

### Technical Risks
- **Docker Performance**: Slow performance on some development machines
- **Port Conflicts**: Conflicts with existing services on developer machines
- **Resource Usage**: High memory/CPU usage affecting other applications
- **Network Issues**: Service communication problems in Docker network
- **Data Loss**: Accidental data loss during development

### Mitigation Strategies
- **Performance Optimization**: Optimize Docker configuration for speed
- **Port Management**: Use configurable ports with sensible defaults
- **Resource Monitoring**: Monitor and optimize resource usage
- **Network Debugging**: Provide network troubleshooting tools
- **Data Protection**: Implement robust backup and restore procedures

---

## Dependencies

### External Dependencies
- Docker Desktop or Docker Engine (latest stable version)
- Docker Compose v2.0+
- Git for version control
- Modern web browser for development
- Sufficient system resources (8GB RAM, 20GB disk space)

### Internal Dependencies
- None (this is the foundation task)

### Blocking Dependencies
- None (this task must be completed before other development can begin)

---

**Task Owner**: DevOps Engineer  
**Reviewers**: Technical Lead, Backend Developer, Frontend Developer  
**Stakeholders**: Development Team, Project Manager  

---

**Change Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-18 | OpenHands | Initial task specification |