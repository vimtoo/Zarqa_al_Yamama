# Zarqa al Yamama - Installation Guide

**Version:** 1.0.0  
**Creator:** Qusai Al-Duaij  
**Last Updated:** 2025-02-17

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4GB | 8GB+ |
| Disk | 10GB | 50GB+ |
| Network | 1Mbps | 10Mbps+ |

### Operating System

- **Linux:** Ubuntu 20.04+, CentOS 8+, Debian 11+
- **macOS:** 10.15+ (Intel or Apple Silicon)
- **Windows:** Windows 10/11 with WSL2

---

## Prerequisites

### Required Software

1. **Docker** (20.10+)
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install docker.io docker-compose-plugin
   
   # macOS
   brew install docker
   
   # Verify installation
   docker --version
   ```

2. **Docker Compose** (2.0+)
   ```bash
   # Verify installation
   docker-compose --version
   ```

3. **Git**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install git
   
   # macOS
   brew install git
   
   # Verify installation
   git --version
   ```

### Optional Software (for local development)

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL Client**
- **Neo4j Cypher Shell**

---

## Installation Steps

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/qusai-duaij/zarqa-al-yamama.git

# Navigate to project directory
cd zarqa-al-yamama

# Verify directory structure
ls -la
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit environment file with your API keys
nano backend/.env
# or
vim backend/.env
```

**Required API Keys:**
- `OPENROUTER_API_KEY` - For LLM access
- `DEEPSEEK_API_KEY` - Alternative LLM provider
- `GDELT_API_KEY` - Global events data
- `NEWSAPI_KEY` - News data source
- `POLYGON_API_KEY` - Stock market data
- `ALPHA_VANTAGE_KEY` - Financial indicators

### Step 3: Build Docker Images

```bash
# Build all images
docker-compose build

# Or build specific service
docker-compose build backend
docker-compose build frontend
```

### Step 4: Start Services

```bash
# Start all services in background
docker-compose up -d

# Or start with logs visible
docker-compose up

# Wait for all services to be healthy (2-3 minutes)
docker-compose ps
```

### Step 5: Initialize Databases

```bash
# PostgreSQL is automatically initialized
# Verify PostgreSQL is running
docker exec zarqa-postgres pg_isready -U zarqa

# Neo4j is automatically initialized
# Verify Neo4j is running
curl -u neo4j:neo4j_pass http://localhost:7474/db/neo4j/exec

# Qdrant is automatically initialized
# Verify Qdrant is running
curl http://localhost:6333/health
```

### Step 6: Verify Installation

```bash
# Check all services are running
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# View logs
docker-compose logs
```

---

## Configuration

### Backend Configuration

Edit `backend/.env`:

```bash
# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
APP_NAME=Zarqa al Yamama
APP_VERSION=1.0.0
CREATOR=Qusai Al-Duaij

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Database Connections
DATABASE_URL=postgresql://zarqa:zarqa_pass@postgres:5432/zarqa_db
QDRANT_URL=http://qdrant:6333
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_pass
REDIS_URL=redis://:redis_pass@redis:6379

# LLM Providers
OPENROUTER_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here

# Data Sources
GDELT_API_KEY=your_key_here
NEWSAPI_KEY=your_key_here
POLYGON_API_KEY=your_key_here
ALPHA_VANTAGE_KEY=your_key_here

# Agent Configuration
TEMPORAL_ANALYST_ENABLED=true
CONTEXT_INTERPRETER_ENABLED=true
QUANTIFIER_ENABLED=true
CRITIC_ENABLED=true
GOVERNOR_ENABLED=true

# Forecast Parameters
DEFAULT_FORECAST_HORIZON_DAYS=30
CONFIDENCE_THRESHOLD=0.60
SENTIMENT_WEIGHT=0.8
```

### Frontend Configuration

Edit `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
```

### Docker Compose Customization

Edit `docker-compose.yml` for custom configuration:

```yaml
services:
  backend:
    environment:
      # Add custom environment variables
      CUSTOM_VAR: value
    ports:
      - "8001:8000"  # Change port if needed
    volumes:
      - ./backend:/app  # For hot reload during development

  postgres:
    environment:
      POSTGRES_PASSWORD: your_secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

---

## Verification

### Health Check

```bash
# Backend health
curl -s http://localhost:8000/health | jq .

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-02-17T10:30:00Z",
  "version": "1.0.0",
  "creator": "Qusai Al-Duaij"
}
```

### API Test

```bash
# Generate a forecast
curl -X POST http://localhost:8000/api/v1/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "Middle East Oil Price Stability",
    "user_id": "test_user"
  }' | jq .

# List available scenarios
curl http://localhost:8000/api/v1/scenarios | jq .

# Get system info
curl http://localhost:8000/api/v1/system/info | jq .
```

### Frontend Test

```bash
# Open in browser
open http://localhost:3000
# or
firefox http://localhost:3000
```

### Database Verification

```bash
# PostgreSQL
docker exec zarqa-postgres psql -U zarqa -d zarqa_db -c "SELECT * FROM forecasts LIMIT 1;"

# Neo4j
docker exec zarqa-neo4j cypher-shell -u neo4j -p neo4j_pass "MATCH (n) RETURN count(n);"

# Qdrant
curl http://localhost:6333/collections

# Redis
docker exec zarqa-redis redis-cli PING
```

---

## Troubleshooting

### Docker Issues

**Problem:** Docker daemon not running

```bash
# Start Docker daemon
sudo systemctl start docker

# Or on macOS
open /Applications/Docker.app
```

**Problem:** Permission denied

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker
```

### Port Conflicts

**Problem:** Port already in use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Database Connection Issues

**Problem:** Cannot connect to PostgreSQL

```bash
# Check if service is running
docker-compose ps postgres

# Check logs
docker logs zarqa-postgres

# Restart service
docker-compose restart postgres

# Verify connection
docker exec zarqa-postgres pg_isready -U zarqa
```

**Problem:** Cannot connect to Neo4j

```bash
# Check if service is running
docker-compose ps neo4j

# Check logs
docker logs zarqa-neo4j

# Restart service
docker-compose restart neo4j

# Verify connection
curl -u neo4j:neo4j_pass http://localhost:7474/db/neo4j/exec
```

### Memory Issues

**Problem:** Services crash due to memory

```bash
# Check resource usage
docker stats

# Increase Docker memory limit in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

### API Connection Issues

**Problem:** Frontend cannot connect to backend

```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS configuration
# Edit backend/.env:
CORS_ORIGINS=["http://localhost:3000"]

# Restart backend
docker-compose restart backend
```

### Build Issues

**Problem:** Docker build fails

```bash
# Clean build
docker-compose build --no-cache

# Check Dockerfile
cat backend/Dockerfile

# Check requirements.txt
cat backend/requirements.txt
```

---

## Development Setup

### Local Backend Development

```bash
# Install Python dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run backend locally
python -m uvicorn app.main:app --reload

# Run tests
pytest tests/
```

### Local Frontend Development

```bash
# Install Node dependencies
cd frontend
npm install

# Run frontend locally
npm run dev

# Build for production
npm run build
```

### Database Tools

```bash
# PostgreSQL CLI
docker exec -it zarqa-postgres psql -U zarqa -d zarqa_db

# Neo4j Cypher Shell
docker exec -it zarqa-neo4j cypher-shell -u neo4j -p neo4j_pass

# Redis CLI
docker exec -it zarqa-redis redis-cli

# Qdrant API
curl http://localhost:6333/collections
```

---

## Next Steps

1. **Configure API Keys** - Add your API keys to `.env`
2. **Start Services** - Run `docker-compose up -d`
3. **Access Dashboard** - Open http://localhost:3000
4. **Generate Forecast** - Use the web interface to create forecasts
5. **Review Documentation** - Read README.md and DEPLOYMENT.md

---

## Support

For installation help:
- Check logs: `docker-compose logs [service]`
- Review configuration: `docker-compose config`
- Contact: Qusai Al-Duaij

---

**Installation Status:** Complete  
**Verification:** Recommended  
**Next Phase:** Configuration & Deployment
