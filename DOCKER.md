# Docker Deployment Guide

## Overview

EstimateX is containerized using Docker for easy deployment and scaling. The application uses a multi-stage build process to minimize image size and includes multiple services.

## Quick Start

### Prerequisites

- Docker 20.10 or later
- Docker Compose 1.29 or later

### Validate Configuration

Before building, validate your Docker setup:

```bash
./validate_docker.sh
```

### Build and Run

**Option 1: Build and run the web service only**

```bash
docker build -t estimatex:latest .
docker run -p 8000:8000 estimatex:latest
```

**Option 2: Run all services with Docker Compose**

```bash
docker-compose up -d
```

**Option 3: Run specific services**

```bash
# Web service only
docker-compose up -d web

# Web + MCP web interface
docker-compose up -d web mcp-web
```

## Services

The `docker-compose.yml` defines four services:

### 1. Web Service (`web`)
- **Port**: 8000
- **Container**: `estimatex-web`
- **Purpose**: Main Flask web application
- **Health Check**: `/health` endpoint
- **Volumes**:
  - `./reference_files:/app/reference_files`
  - `./uploads:/app/uploads`
  - `./examples:/app/examples`

### 2. MCP Web Interface (`mcp-web`)
- **Port**: 5001
- **Container**: `estimatex-mcp-web`
- **Purpose**: Model Context Protocol web interface
- **Command**: `python mcp_web_interface.py`

### 3. MCP Server (`mcp-server`)
- **Container**: `estimatex-mcp-server`
- **Purpose**: MCP server for Claude Desktop integration
- **Mode**: stdio (stdin/stdout)
- **Command**: `python mcp_server.py`

### 4. Database Manager (`db-manager`)
- **Port**: 5002
- **Container**: `estimatex-db-manager`
- **Purpose**: Database management interface
- **Command**: `python database_manager.py`

## Dockerfile Details

### Multi-Stage Build

The Dockerfile uses a two-stage build process:

**Stage 1: Builder**
- Base: `python:3.11-slim`
- Installs build dependencies (gcc, g++, libffi-dev, libssl-dev)
- Installs Python packages from `requirements.txt`

**Stage 2: Runtime**
- Base: `python:3.11-slim`
- Copies only Python packages from builder stage
- Installs minimal runtime dependencies (libgomp1)
- Copies application code
- Sets up environment variables

### Environment Variables

- `PYTHONPATH=/app` - Python module search path
- `PATH=/root/.local/bin:$PATH` - Include user-installed packages
- `FLASK_APP=estimatex.web` - Flask application entry point
- `FLASK_ENV=production` - Production mode settings

### Exposed Ports

- **8000**: Main web application
- **5001**: MCP web interface

### Health Check

The container includes a health check that:
- Runs every 30 seconds
- Checks the `/health` endpoint
- Times out after 10 seconds
- Retries 3 times before marking as unhealthy

## Networking

All services are connected to the `estimatex-network` bridge network, allowing inter-service communication.

## Volumes

### Named Volumes

- `reference_files`: DSR database and reference data
- `uploads`: User-uploaded files
- `examples`: Example files and outputs

### Volume Mounting

To persist data across container restarts, mount local directories:

```bash
docker run -p 8000:8000 \
  -v $(pwd)/reference_files:/app/reference_files \
  -v $(pwd)/uploads:/app/uploads \
  estimatex:latest
```

## Management Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop specific service
docker-compose stop web
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart web
```

### Check Service Status

```bash
docker-compose ps
```

### Execute Commands in Container

```bash
# Run bash shell
docker-compose exec web bash

# Run Python command
docker-compose exec web python -c "from estimatex import __version__; print(__version__)"

# Run tests
docker-compose exec web pytest
```

## Production Deployment

### Security Considerations

1. **Change Secret Keys**: Update Flask secret key in production
   ```bash
   docker run -e FLASK_SECRET_KEY="your-secure-random-key" ...
   ```

2. **Use HTTPS**: Place behind a reverse proxy (nginx, Traefik)
   
3. **Limit Resources**: Set memory and CPU limits
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 1G
   ```

4. **Non-Root User**: Consider running as non-root user

### Optimization

1. **Build with BuildKit**: 
   ```bash
   DOCKER_BUILDKIT=1 docker build -t estimatex:latest .
   ```

2. **Use .dockerignore**: Already configured to exclude unnecessary files

3. **Layer Caching**: Dependencies are installed before copying app code

### Monitoring

1. **Health Endpoint**: `http://localhost:8000/health`
2. **Container Stats**: `docker stats estimatex-web`
3. **Logs**: `docker logs -f estimatex-web`

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs web

# Check container status
docker-compose ps

# Inspect container
docker inspect estimatex-web
```

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8080:8000"  # Map to different host port
```

### Permission Issues

```bash
# Fix volume permissions
sudo chown -R $(id -u):$(id -g) uploads/ reference_files/
```

### Out of Memory

```bash
# Increase Docker memory limit in Docker Desktop
# Or set limits in docker-compose.yml
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Docker Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t estimatex:${{ github.sha }} .
      - name: Run tests
        run: docker run estimatex:${{ github.sha }} pytest
```

### Build Arguments

```bash
# Custom Python version
docker build --build-arg PYTHON_VERSION=3.12 -t estimatex:latest .
```

## Development with Docker

### Hot Reload

For development with auto-reload:

```yaml
services:
  web:
    build: .
    volumes:
      - .:/app
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
```

### Debug Mode

```bash
docker-compose up web
# Container runs with debug output
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices for Writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

## Support

For issues or questions about Docker deployment, please open an issue on GitHub.
