# Zarqa al Yamama - Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2025-02-17

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Compose Deployment](#docker-compose-deployment)
3. [Environment Configuration](#environment-configuration)
4. [Database Initialization](#database-initialization)
5. [Health Checks](#health-checks)
6. [Troubleshooting](#troubleshooting)
7. [Production Deployment](#production-deployment)

---

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### Start the System

```bash
# Navigate to project root
cd zarqa-al-yamama

# Configure environment
cp backend/.env.example backend/.env

# Start all services
docker-compose up -d

# Verify all services are running
docker-compose ps

# View logs
docker-compose logs -f
```

### Access the Application

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web UI |
| API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Health Check | http://localhost:8000/health | System health |
| Neo4j Browser | http://localhost:7474 | Graph DB UI |
| Qdrant Dashboard | http://localhost:6333/dashboard | Vector DB UI |

---

## Docker Compose Deployment

### Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│                   Port: 3000                             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Backend (FastAPI)                       │
│                   Port: 8000                             │
├──────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ PostgreSQL   │  │   Qdrant     │  │    Neo4j     │   │
│  │  Port: 5432  │  │ Port: 6333   │  │ Port: 7687   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                          │
│  ┌──────────────┐                                        │
│  │    Redis     │                                        │
│  │  Port: 6379  │                                        │
│  └──────────────┘                                        │
└──────────────────────────────────────────────────────────┘
```

### Docker Compose Commands

```bash
# Start services in background
docker-compose up -d

# Start with logs
docker-compose up

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View logs
docker-compose logs -f [service_name]

# Restart service
docker-compose restart [service_name]

# Rebuild images
docker-compose build --no-cache

# Scale service
docker-compose up -d --scale backend=3
```

---

## Environment Configuration

### Backend Configuration (.env)

```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
APP_NAME=Zarqa al Yamama
APP_VERSION=1.0.0
CREATOR=Qusai Al-Duaij

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Database URLs
DATABASE_URL=postgresql://zarqa:zarqa_pass@postgres:5432/zarqa_db
QDRANT_URL=http://qdrant:6333
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_pass
REDIS_URL=redis://:redis_pass@redis:6379

# LLM Providers
OPENROUTER_API_KEY=sk-or-v1-...
DEEPSEEK_API_KEY=sk-...

# Data Sources
GDELT_API_KEY=...
NEWSAPI_KEY=...
POLYGON_API_KEY=...
ALPHA_VANTAGE_KEY=...
NEWSDATA_API_KEY=...
WEBZ_API_KEY=...

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
VOLATILITY_FACTOR_BASE=1.0
RISK_WEIGHT_BASE=0.5

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Data Retention
DATA_RETENTION_DAYS=90
CACHE_TTL_SECONDS=3600
```

### Frontend Configuration

```bash
# In docker-compose.yml or .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=production
```

---

## Database Initialization

### PostgreSQL Setup

```bash
# Connect to PostgreSQL
docker exec -it zarqa-postgres psql -U zarqa -d zarqa_db

# Verify tables
\dt

# View table structure
\d forecasts

# Exit
\q
```

### Neo4j Setup

```bash
# Access Neo4j Browser
# Navigate to http://localhost:7474
# Username: neo4j
# Password: neo4j_pass

# Create initial data
MATCH (n) DETACH DELETE n;

CREATE (kuwait:Actor {name: 'Kuwait', country: 'Kuwait', type: 'Country'})
CREATE (saudi:Actor {name: 'Saudi Arabia', country: 'Saudi Arabia', type: 'Country'})
CREATE (iran:Actor {name: 'Iran', country: 'Iran', type: 'Country'})
CREATE (oil:Theme {name: 'Oil Prices', category: 'Energy'})
CREATE (geopolitics:Theme {name: 'Geopolitical Tensions', category: 'Politics'})

CREATE (kuwait)-[:EXPORTS_TO]->(oil)
CREATE (saudi)-[:EXPORTS_TO]->(oil)
CREATE (iran)-[:INFLUENCES]->(geopolitics)
```

### Qdrant Setup

```bash
# Check collection status
curl http://localhost:6333/collections

# Get collection info
curl http://localhost:6333/collections/news_embeddings

# View collection stats
curl http://localhost:6333/collections/news_embeddings/points
```

---

## Health Checks

### System Health Verification

```bash
# Backend health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-02-17T10:30:00Z",
#   "version": "1.0.0",
#   "creator": "Qusai Al-Duaij"
# }

# Frontend health
curl http://localhost:3000

# PostgreSQL health
docker exec zarqa-postgres pg_isready -U zarqa

# Neo4j health
curl -u neo4j:neo4j_pass http://localhost:7474/db/neo4j/exec

# Qdrant health
curl http://localhost:6333/health

# Redis health
docker exec zarqa-redis redis-cli ping
```

### Docker Compose Health Status

```bash
# Check all services
docker-compose ps

# Expected output:
# NAME                 COMMAND                  SERVICE      STATUS
# zarqa-backend        "uvicorn app.main:app"   backend      Up (healthy)
# zarqa-frontend       "node server.js"         frontend     Up (healthy)
# zarqa-postgres       "postgres"               postgres     Up (healthy)
# zarqa-qdrant         "qdrant"                 qdrant       Up (healthy)
# zarqa-neo4j          "tini -g -- /startup.sh" neo4j        Up (healthy)
# zarqa-redis          "redis-server"           redis        Up (healthy)
```

---

## Troubleshooting

### Backend Connection Issues

**Problem:** Backend fails to start

```bash
# Check logs
docker logs zarqa-backend

# Common issues:
# - Port 8000 already in use
# - Database connection failed
# - Missing environment variables

# Solution: Restart with clean state
docker-compose down -v
docker-compose up -d
```

### Database Connection Issues

**Problem:** "Connection refused" error

```bash
# Check if PostgreSQL is running
docker exec zarqa-postgres pg_isready -U zarqa

# If not running, restart
docker-compose restart postgres

# Check connection string
echo $DATABASE_URL
```

### Frontend Not Loading

**Problem:** Frontend shows blank page

```bash
# Check frontend logs
docker logs zarqa-frontend

# Verify API URL configuration
docker exec zarqa-frontend env | grep NEXT_PUBLIC_API_URL

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Memory Issues

**Problem:** Services crash due to memory

```bash
# Check resource usage
docker stats

# Increase Docker memory limit
# Edit Docker Desktop settings or docker-compose.yml:

services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### Port Conflicts

**Problem:** "Port already in use" error

```bash
# Find process using port
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

---

## Production Deployment

### Pre-Production Checklist

- [ ] All environment variables configured
- [ ] SSL/TLS certificates obtained
- [ ] Database backups configured
- [ ] Monitoring and logging set up
- [ ] Rate limiting configured
- [ ] CORS origins restricted
- [ ] API keys rotated
- [ ] Security audit completed

### Production Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: zarqa-backend:1.0.0
    environment:
      ENVIRONMENT: production
      LOG_LEVEL: WARNING
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_backup:/var/lib/postgresql/backup
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U zarqa"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ... other services
```

### Deployment Commands

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# View production logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale backend service
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Monitoring

```bash
# Set up Prometheus monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana dashboard
# http://localhost:3001
# Username: admin
# Password: admin
```

### Backup and Recovery

```bash
# Backup PostgreSQL
docker exec zarqa-postgres pg_dump -U zarqa zarqa_db > backup.sql

# Restore PostgreSQL
docker exec -i zarqa-postgres psql -U zarqa zarqa_db < backup.sql

# Backup Qdrant
docker exec zarqa-qdrant qdrant-cli backup

# Backup Neo4j
docker exec zarqa-neo4j neo4j-admin dump --to-path=/backup
```

---

## Performance Tuning

### PostgreSQL Optimization

```sql
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '256MB';

-- Increase work memory
ALTER SYSTEM SET work_mem = '4MB';

-- Enable parallel queries
ALTER SYSTEM SET max_parallel_workers = 4;

-- Reload configuration
SELECT pg_reload_conf();
```

### Redis Optimization

```bash
# Increase max memory
docker exec zarqa-redis redis-cli CONFIG SET maxmemory 2gb

# Set eviction policy
docker exec zarqa-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Neo4j Optimization

```bash
# Increase heap size
export NEO4J_HEAP_MEMORY=2G
export NEO4J_PAGECACHE_MEMORY=1G
```

---

## Security Hardening

### Network Security

```yaml
# Restrict network access
networks:
  zarqa-network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-zarqa

services:
  backend:
    networks:
      - zarqa-network
    # Don't expose to host network
```

### Secrets Management

```bash
# Use Docker Secrets (Swarm mode)
echo "super_secret_password" | docker secret create db_password -

# Or use environment file
docker-compose --env-file .env.prod up -d
```

### SSL/TLS Configuration

```yaml
services:
  backend:
    environment:
      SSL_CERT_FILE: /etc/ssl/certs/cert.pem
      SSL_KEY_FILE: /etc/ssl/private/key.pem
    volumes:
      - /etc/ssl/certs:/etc/ssl/certs:ro
      - /etc/ssl/private:/etc/ssl/private:ro
```

---

## Kubernetes Deployment

See `kubernetes/` directory for production-grade Kubernetes manifests.

```bash
# Deploy to Kubernetes
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/postgres.yaml
kubectl apply -f kubernetes/qdrant.yaml
kubectl apply -f kubernetes/neo4j.yaml
kubectl apply -f kubernetes/backend.yaml
kubectl apply -f kubernetes/frontend.yaml

# Verify deployment
kubectl get pods -n zarqa
kubectl get services -n zarqa
```

---

## Support

For deployment issues:
- Check logs: `docker-compose logs [service]`
- Review configuration: `docker-compose config`
- Test connectivity: `docker-compose exec [service] ping [other_service]`
- Contact: Qusai Al-Duaij

---

**System Status:** Production-Ready  
**Last Verified:** 2025-02-17
