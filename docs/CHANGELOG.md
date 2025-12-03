# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-03

### Added
- **Docker Support**: Multi-stage Dockerfile for production deployment
- **Docker Compose**: Full stack deployment with web and MCP services
- **CI/CD Pipeline**: GitHub Actions workflows for testing, building, and deployment
  - Automated testing on Python 3.9, 3.10, 3.11, 3.12
  - Code quality checks (black, pylint, mypy)
  - Security scanning (bandit, safety)
  - Docker image building and pushing
  - Integration tests with docker-compose
- **Release Workflow**: Automated releases with version tagging
- **Environment Configuration**: `.env.example` for easy configuration
- **Deployment Guide**: Comprehensive DEPLOYMENT.md covering multiple platforms
- **Contributing Guide**: CONTRIBUTING.md with development workflow
- **Health Check Endpoint**: `/health` for monitoring and load balancers
- **Project Configuration**: `pyproject.toml` for modern Python packaging
- **Code Quality Tools**: Pre-commit hooks and linting configuration

### Enhanced
- **MCP Integration**: Web interface for testing MCP tools
- **Test Suite**: 44+ passing tests with >80% coverage
- **Documentation**: Updated README with deployment information

### Infrastructure
- `.dockerignore` for optimized builds
- `.github/workflows/` for CI/CD automation
- Docker multi-stage builds for smaller images
- Health checks in Docker Compose

## [0.9.0] - 2025-11-30

### Added
- **MCP Server**: Model Context Protocol integration for AI assistants
- **MCP Web Interface**: Browser-based testing for MCP tools
- 6 MCP tools: search_code, search_description, calculate_cost, get_chapter, convert_pdf, list_categories
- MCP resources for DSR databases

### Enhanced
- SQLite backend performance (50-100x faster)
- Multi-volume DSR support
- Generic CLI scripts with command-line arguments

## [0.8.0] - 2025-11-15

### Added
- Comprehensive test suite (44 tests)
- Test documentation (TESTING.md)
- Coverage reporting

### Fixed
- Test failures due to API changes
- Database operation test issues
- Web interface test reliability

## [0.7.0] - 2025-11-01

### Added
- SQLite database backend for DSR matching
- Multi-category support
- Database versioning and migration tools

### Changed
- Migrated from JSON to SQLite for 50-100x performance improvement
- Updated matching scripts to use SQLite

### Deprecated
- JSON-based matching (use SQLite instead)

## [0.6.0] - 2025-10-15

### Added
- Web interface for PDF conversion
- Cost estimation through web UI
- File browser for organized viewing

### Enhanced
- PDF to JSON conversion with table extraction
- Report generation in multiple formats

## [0.5.0] - 2025-09-30

### Added
- DSR rate matching system
- Text similarity algorithms
- Cost calculation engine

### Features
- Fuzzy matching with configurable thresholds
- Multiple DSR volume support
- JSON, CSV, and Markdown report generation

## [0.4.0] - 2025-09-15

### Added
- CLI interface for PDF conversion
- Structured JSON output format
- Metadata extraction

## [0.3.0] - 2025-09-01

### Added
- PDF to JSON conversion using PyMuPDF
- Basic text extraction
- Page-by-page processing

## [0.2.0] - 2025-08-15

### Added
- Project structure
- Initial Flask web application
- Basic file upload functionality

## [0.1.0] - 2025-08-01

### Added
- Initial project setup
- README and basic documentation
- Requirements file

---

## Release Notes Template

```markdown
## [Version] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements
```

---

## Upgrade Guide

### From 0.9.0 to 1.0.0

1. **Docker Migration** (Optional but recommended)
   ```bash
   # Pull latest code
   git pull origin main
   
   # Build and run with Docker
   docker-compose up -d
   ```

2. **Environment Variables**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit with your configuration
   vim .env
   ```

3. **CI/CD Setup** (For maintainers)
   - Add Docker Hub credentials to GitHub secrets
   - Configure `DOCKER_USERNAME` and `DOCKER_PASSWORD`
   - Push to trigger automated builds

4. **No Breaking Changes**
   - All existing APIs remain compatible
   - Database schema unchanged
   - CLI commands unchanged

### From 0.8.0 to 0.9.0

1. **Install MCP dependencies**
   ```bash
   pip install mcp>=0.9.0
   ```

2. **Configure Claude Desktop** (Optional)
   - See MCP_INTEGRATION.md for setup

3. **Test MCP Web Interface**
   ```bash
   python mcp_web_interface.py
   ```

### From 0.7.0 to 0.8.0

1. **Run existing tests**
   ```bash
   pytest tests/ -v
   ```

2. **Update test dependencies**
   ```bash
   pip install pytest pytest-cov
   ```

---

## Future Roadmap

### Planned for 1.1.0
- [ ] Authentication and authorization
- [ ] API documentation with Swagger
- [ ] Database management UI
- [ ] Advanced analytics dashboard
- [ ] Batch processing with queue system

### Planned for 1.2.0
- [ ] Machine learning enhancements
- [ ] Elasticsearch integration
- [ ] Rate comparison engine
- [ ] Export to Excel templates

### Planned for 2.0.0
- [ ] Mobile app/PWA
- [ ] Real-time collaboration
- [ ] Multi-language support
- [ ] Plugin system
