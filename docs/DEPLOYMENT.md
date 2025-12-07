# Deployment Guide

This guide covers multiple deployment options for the EstimateX DSR Rate Matching System.

## 🐳 Docker Deployment (Recommended)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Quick Start

1. **Clone and configure**
   ```bash
   git clone <repository-url>
   cd EstimateX
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Build and run**
   ```bash
   docker-compose up -d
   ```

3. **Access the applications**
   - Main Web Interface: http://localhost:8000
   - MCP Web Interface: http://localhost:5001

4. **View logs**
   ```bash
   docker-compose logs -f
   ```

5. **Stop services**
   ```bash
   docker-compose down
   ```

### Docker Commands

```bash
# Build images
docker-compose build

# Start services in background
docker-compose up -d

# View running containers
docker-compose ps

# Restart a service
docker-compose restart web

# View logs for specific service
docker-compose logs -f web

# Execute command in container
docker-compose exec web python -m pytest

# Stop and remove all containers
docker-compose down -v
```

## 🖥️ Local Development

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # .venv\Scripts\activate   # On Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

4. **Run the application**
   ```bash
   # Main web interface
   python -m src.estimatex.web

   # MCP web interface
   python mcp_web_interface.py

   # MCP server (for Claude Desktop)
   python mcp_server.py
   ```

## ☁️ Cloud Deployment

### AWS Elastic Beanstalk

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB**
   ```bash
   eb init -p python-3.11 estimatex-dsr
   ```

3. **Create environment**
   ```bash
   eb create estimatex-prod
   ```

4. **Deploy**
   ```bash
   eb deploy
   ```

### Heroku

1. **Install Heroku CLI**
   ```bash
   brew install heroku/brew/heroku  # macOS
   ```

2. **Create Procfile**
   ```bash
   echo "web: python -m src.estimatex.web" > Procfile
   ```

3. **Deploy**
   ```bash
   heroku create estimatex-dsr
   git push heroku main
   ```

### Google Cloud Run

1. **Build container**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/estimatex
   ```

2. **Deploy**
   ```bash
   gcloud run deploy estimatex \
     --image gcr.io/PROJECT-ID/estimatex \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## 🔐 Production Configuration

### Environment Variables

Required variables for production:

```bash
# Security
SECRET_KEY=<random-256-bit-key>

# Database
DATABASE_PATH=/app/reference_files/civil/DSR_Civil_combined.db

# Performance
WORKERS=4
THREADS=2

# Features
FLASK_ENV=production
FLASK_DEBUG=0
```

### Security Checklist

- [ ] Set strong SECRET_KEY
- [ ] Disable DEBUG mode
- [ ] Configure HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Regular security updates
- [ ] Enable logging and monitoring
- [ ] Backup database regularly

### Performance Optimization

1. **Use production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 "src.estimatex.web:app"
   ```

2. **Enable caching**
   ```python
   # Add to web.py
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   ```

3. **Use reverse proxy**
   ```nginx
   # nginx.conf
   location / {
       proxy_pass http://localhost:8000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

## 📊 Monitoring

### Health Checks

```bash
# Check service health
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-12-03T10:00:00Z"
}
```

### Logging

Configure logging in production:

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
```

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Docker
docker-compose pull
docker-compose up -d

# Kubernetes
kubectl set image deployment/estimatex estimatex=estimatex:v1.1.0
kubectl rollout status deployment/estimatex
```

### Database Migrations

```bash
# Backup database
cp reference_files/civil/DSR_Civil_combined.db reference_files/civil/DSR_Civil_combined.db.backup

# Run migration
python scripts/update_dsr_database.py
```

### Rollback

```bash
# Docker
docker-compose down
docker-compose up -d --force-recreate

# Kubernetes
kubectl rollout undo deployment/estimatex
```

## 🆘 Troubleshooting

### Common Issues

**Port already in use**
```bash
# Find process using port
lsof -i :8000
# Kill process
kill -9 <PID>
```

**Database locked**
```bash
# Check for multiple connections
lsof reference_files/civil/DSR_Civil_combined.db
```

**Out of memory**
```bash
# Increase Docker memory limit
docker update --memory 2g <container-id>
```

### Logs Location

- Docker: `docker-compose logs -f`
- Local: `logs/app.log`
- Heroku: `heroku logs --tail`
- AWS: CloudWatch Logs

## 📞 Support

For deployment issues:
1. Check logs first
2. Verify environment variables
3. Test health endpoint
4. Review security groups/firewall
5. Check resource limits

## 🔗 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Flask Deployment](https://flask.palletsprojects.com/en/latest/deploying/)
- [AWS EB Python](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-apps.html)
- [Heroku Python](https://devcenter.heroku.com/articles/getting-started-with-python)
