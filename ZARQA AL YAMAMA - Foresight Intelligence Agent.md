# ZARQA AL YAMAMA - Foresight Intelligence Agent

**Version:** 1.0.0  
**Creator:** Qusai Al-Duaij  
**Branch:** LoLo AI Tree (Sovereign AI Initiative)  
**Status:** Production-Ready

---

## Overview

**Zarqa al Yamama** is a Strategic Foresight Intelligence System that predicts geopolitical and economic scenarios by synthesizing hard statistical data with soft linguistic signals. The system combines:

- **Temporal Analysis:** Time-series forecasting using machine learning
- **Context Intelligence:** Sentiment analysis and narrative mapping from news/events
- **Signal Fusion:** Mathematical combination of temporal and context signals
- **Validation:** Source credibility assessment and bias detection
- **Ethical Oversight:** Compliance tracking and attribution lineage

The system is built on **LangGraph** for multi-agent orchestration, **FastAPI** for the backend, and **Next.js** for the frontend.

---

## System Architecture

### Multi-Agent Swarm

1. **Temporal Analyst** - Numeric forecasting using H2O AutoML
2. **Context Interpreter** - Sentiment and narrative analysis via GDELT, NewsAPI
3. **The Quantifier** - Mathematical fusion of temporal and context signals
4. **The Critic** - Source validation and bias detection
5. **The Governor** - Ethical oversight and compliance tracking

### Technology Stack

**Backend:**
- Python 3.11 + FastAPI
- LangGraph (stateful multi-agent workflows)
- PostgreSQL (time-series data)
- Qdrant (vector embeddings)
- Neo4j (knowledge graph)
- Redis (caching)

**Frontend:**
- Next.js 14 + TypeScript
- Tailwind CSS
- Plotly.js (visualizations)

**Deployment:**
- Docker + Docker Compose
- Kubernetes-ready

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Installation

1. **Clone and navigate:**
```bash
cd zarqa-al-yamama
```

2. **Configure environment:**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

3. **Start the system:**
```bash
docker-compose up -d
```

4. **Access the application:**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## API Usage

### Generate Forecast

**Endpoint:** `POST /api/v1/forecast`

**Request:**
```json
{
  "scenario": "Middle East Oil Price Stability",
  "user_id": "optional_user_id"
}
```

**Response:**
```json
{
  "request_id": "req_20250217_001",
  "timestamp": "2025-02-17T10:30:00Z",
  "scenario": "Middle East Oil Price Stability",
  "status": "success",
  "headers": {
    "X-Powered-By": "LoLo AI / Zarqa al Yamama",
    "X-Creator": "Qusai Al-Duaij",
    "X-Version": "1.0.0"
  },
  "data": {
    "executive_summary": "Oil prices face downward pressure from geopolitical de-escalation signals and rising US production. Probability of $80-90 range in 30 days: 72%.",
    "forecast": {
      "metric": "Brent Crude Oil",
      "current": 85.0,
      "forecast_30d": 82.5,
      "confidence_30d": 0.72
    },
    "weak_signals": [...],
    "strategic_recommendation": "Current market pricing at $85 appears elevated. Consider hedging long positions.",
    "citations": [...]
  },
  "metadata": {
    "agents_executed": ["temporal_analyst", "context_interpreter", "quantifier", "critic", "governor"],
    "processing_time_ms": 2847,
    "validation_status": "APPROVED",
    "ethical_status": "APPROVED"
  }
}
```

### List Available Scenarios

**Endpoint:** `GET /api/v1/scenarios`

**Response:**
```json
{
  "scenarios": [
    "Middle East Oil Price Stability",
    "USD/KWD Exchange Rate",
    "Regional Economic Growth",
    "Geopolitical Risk Index",
    "Supply Chain Resilience",
    "Energy Market Volatility",
    "Diplomatic Relations Index"
  ]
}
```

### System Information

**Endpoint:** `GET /api/v1/system/info`

**Response:**
```json
{
  "system": "Zarqa al Yamama",
  "version": "1.0.0",
  "creator": "Qusai Al-Duaij",
  "environment": "production",
  "agents": {
    "temporal_analyst": true,
    "context_interpreter": true,
    "quantifier": true,
    "critic": true,
    "governor": true
  }
}
```

---

## Configuration

### Environment Variables

Key configuration variables in `.env`:

```bash
# LLM Providers
OPENROUTER_API_KEY=sk-or-v1-...
DEEPSEEK_API_KEY=sk-...

# Data Sources
GDELT_API_KEY=...
NEWSAPI_KEY=...
POLYGON_API_KEY=...
ALPHA_VANTAGE_KEY=...

# Databases
DATABASE_URL=postgresql://zarqa:zarqa_pass@postgres:5432/zarqa_db
QDRANT_URL=http://qdrant:6333
NEO4J_URI=bolt://neo4j:7687

# Agent Configuration
TEMPORAL_ANALYST_ENABLED=true
CONTEXT_INTERPRETER_ENABLED=true
QUANTIFIER_ENABLED=true
CRITIC_ENABLED=true
GOVERNOR_ENABLED=true

# Forecast Parameters
CONFIDENCE_THRESHOLD=0.60
SENTIMENT_WEIGHT=0.8
VOLATILITY_FACTOR_BASE=1.0
```

---

## The Quantifier Formula

The core mathematical formula that fuses temporal and context signals:

```
Final_Prediction = Base_Forecast × (1 + (Sentiment_Score × Risk_Weight × Volatility_Factor))

Where:
- Base_Forecast: Output from Temporal Analyst
- Sentiment_Score: Normalized context sentiment (-1 to +1)
- Risk_Weight: Calibrated impact coefficient (0.1 to 1.0)
- Volatility_Factor: Market volatility index adjustment (0.8 to 1.5)
```

**Example:**
```
Base Forecast: Oil price $85/barrel (confidence 0.75)
Sentiment Score: -0.60 (negative geopolitical context)
Risk Weight: 0.8 (Middle East tensions)
Volatility Factor: 1.15 (elevated market volatility)

Final = 85 × (1 + (-0.60 × 0.8 × 1.15))
Final = 85 × (1 - 0.552)
Final = 85 × 0.448
Final = $38.08/barrel (confidence adjusted to 0.58)
```

---

## Data Sources

### Real-Time Intelligence
- **GDELT 2.0** - Global events and sentiment (15-min updates)
- **NewsAPI.ai** - Structured news events
- **NewsData.io** - Hyper-local sources (85k+ outlets)
- **Webz.io** - Dark web monitoring

### Financial Markets
- **Polygon.io** - Real-time market ticks
- **Alpha Vantage** - Technical indicators
- **Financial Modeling Prep** - Fundamental data
- **EODHD** - Global exchange coverage

### Economic Data
- **World Bank API** - Economic indicators
- **Oxford Economics** - Macro forecasts
- **Central Banks** - Official data

### Regional Intelligence
- **AIM Technologies** - MENA sentiment analysis
- **Semantic Scholar** - Academic consensus

---

## Ethical Guidelines

The system enforces strict ethical compliance:

1. **No Market Manipulation** - Predictions cannot be used to manipulate markets
2. **No Personal Data** - All PII is removed from analysis
3. **Transparency** - All model limitations are disclosed
4. **Balanced Representation** - Fair treatment of geopolitical actors
5. **Cultural Sensitivity** - Respect for MENA region customs
6. **Data Protection** - GDPR and local regulation compliance
7. **Complete Attribution** - Full citation chain for all sources
8. **No Harmful Predictions** - Avoid content that incites violence

---

## Development

### Local Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Local Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
cd backend
pytest tests/
```

---

## Deployment

### Docker Compose (Development/Testing)

```bash
docker-compose up -d
```

### Kubernetes (Production)

See `kubernetes/` directory for production-grade manifests.

### Environment-Specific Configs

- **Development:** `.env.development`
- **Staging:** `.env.staging`
- **Production:** `.env.production`

---

## Monitoring & Logging

### Logging Levels

- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Database connections
curl http://localhost:5432 (PostgreSQL)
curl http://localhost:6333 (Qdrant)
curl http://localhost:7687 (Neo4j)
```

---

## Troubleshooting

### Backend Connection Issues

```bash
# Check if backend is running
docker ps | grep zarqa-backend

# View backend logs
docker logs zarqa-backend

# Restart backend
docker-compose restart backend
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker exec zarqa-postgres pg_isready -U zarqa

# Reset database
docker-compose down -v
docker-compose up -d
```

### Frontend Not Loading

```bash
# Check frontend logs
docker logs zarqa-frontend

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

---

## Performance Optimization

### Caching

- Redis caches forecast results (TTL: 1 hour)
- Frontend uses React Query for client-side caching
- API responses include cache headers

### Rate Limiting

- 60 requests per minute per IP
- Configurable via `RATE_LIMIT_REQUESTS_PER_MINUTE`

### Database Optimization

- PostgreSQL indexes on frequently queried columns
- Qdrant vector search optimized for semantic similarity
- Neo4j graph queries cached in memory

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

Proprietary - Zarqa al Yamama by Qusai Al-Duaij

---

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Contact: Qusai Al-Duaij
- Documentation: See `/docs` directory

---

## Acknowledgments

- **Creator:** Qusai Al-Duaij
- **Initiative:** LoLo AI Tree (Sovereign AI Initiative)
- **Inspiration:** Zarqa al Yamama (The Blue Dove of Foresight)

---

**System Startup Message:**
```
================================================================================
Initializing Zarqa al Yamama... Developed by Qusai Al-Duaij.
Version: 1.0.0
Environment: production
API running on 0.0.0.0:8000
================================================================================
```

**X-Powered-By Header:** `LoLo AI / Zarqa al Yamama`

---

*Last Updated: 2025-02-17*  
*Status: Production-Ready*
