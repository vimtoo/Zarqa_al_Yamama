# ZARQA AL YAMAMA - System Architecture Document

## Executive Overview

**Project Name:** Zarqa al Yamama (ةماميلا ءاقرز) - The Foresight Intelligence Agent  
**Creator:** Qusai Al-Duaij  
**Branch:** LoLo AI Tree (Sovereign AI Initiative)  
**Version:** 1.0.0  
**Status:** Production-Ready Implementation

---

## 1. System Philosophy

Zarqa al Yamama is a **Strategic Foresight Intelligence System** that predicts geopolitical and economic scenarios by synthesizing:

- **Hard Statistical Data:** Market ticks, GDP trends, supply chain metrics
- **Soft Linguistic Signals:** News sentiment, diplomatic discourse, social media trends
- **Weak Signals:** Early warning indicators before events materialize

**Core Principle:** Never predict with certainty. Always express predictions as probabilistic confidence scores derived from multiple data streams.

---

## 2. Technology Stack

### Backend Infrastructure
- **Language:** Python 3.11
- **API Framework:** FastAPI (async-first)
- **Agent Orchestration:** LangGraph (stateful multi-agent workflows)
- **LLM Integration:** OpenRouter API (Hermes 3, DeepSeek), DeepSeek native API

### Data Layer
- **Vector Database:** Qdrant (Docker) - News/Reports embeddings
- **Time-Series Database:** PostgreSQL (Docker) - Economic/market data
- **Knowledge Graph:** Neo4j (Docker) - Context relationships
- **Cache:** Redis (Docker) - Session state, rate limiting

### Frontend
- **Framework:** Next.js 14+ with TypeScript
- **UI Components:** Tailwind CSS, Shadcn/UI
- **State Management:** TanStack Query + Zustand
- **Visualization:** Plotly.js, D3.js for forecasts

### ML/Analytics
- **AutoML:** H2O.ai (Temporal Analyst agent)
- **NLP:** Hugging Face Transformers, spaCy
- **Sentiment Analysis:** AIM Technologies (MENA-specific)
- **Statistical Forecasting:** Prophet, ARIMA, XGBoost

---

## 3. Multi-Agent Architecture (The Swarm)

### 3.1 Temporal Analyst Agent
**Responsibility:** Numeric forecasting using time-series data

**Inputs:**
- Stock prices (Polygon.io, Alpha Vantage)
- Economic indicators (World Bank, Oxford Economics)
- Currency pairs (EODHD, yfinance)

**Process:**
1. Fetch historical data (5+ years)
2. Run H2O AutoML regression models
3. Generate forecast with confidence intervals
4. Output: `forecast_value`, `confidence_score`, `forecast_horizon`

**Output Schema:**
```json
{
  "metric": "USD/KWD Exchange Rate",
  "current_value": 0.307,
  "forecast_30d": 0.309,
  "confidence": 0.78,
  "drivers": ["Oil Price", "Fed Rate", "Geopolitical Risk"],
  "model_type": "XGBoost Ensemble"
}
```

---

### 3.2 Context Interpreter Agent
**Responsibility:** Narrative intelligence and sentiment mapping

**Inputs:**
- News streams (GDELT, NewsAPI.ai, NewsData.io)
- Social media signals (Twitter, regional platforms)
- Diplomatic cables (if available)
- Academic consensus (Semantic Scholar)

**Process:**
1. Scrape and deduplicate events (GDELT 2.0)
2. Map to Neo4j knowledge graph
3. Calculate sentiment trajectories
4. Identify theme co-occurrence patterns
5. Output: `sentiment_impact_score`, `narrative_strength`, `theme_clusters`

**Output Schema:**
```json
{
  "theme": "Middle East Tensions",
  "sentiment_score": -0.65,
  "narrative_momentum": "accelerating",
  "mentions_24h": 2847,
  "key_actors": ["Iran", "Saudi Arabia", "US"],
  "related_themes": ["Oil Price", "Regional Stability"],
  "confidence": 0.82
}
```

---

### 3.3 The Quantifier (Middleware Agent)
**Responsibility:** Mathematically fuse Temporal and Context signals

**Formula:**
```
Final_Prediction = Base_Forecast × (1 + (Sentiment_Score × Risk_Weight × Volatility_Factor))

Where:
- Base_Forecast = Output from Temporal Analyst
- Sentiment_Score = Normalized context sentiment (-1 to +1)
- Risk_Weight = Calibrated impact coefficient (0.1 to 1.0)
- Volatility_Factor = Market volatility index adjustment
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

**Output Schema:**
```json
{
  "metric": "Brent Crude Oil",
  "base_forecast": 85.0,
  "base_confidence": 0.75,
  "sentiment_adjustment": -0.552,
  "final_forecast": 38.08,
  "final_confidence": 0.58,
  "adjustment_rationale": "Negative geopolitical sentiment in MENA region reduces forecast reliability"
}
```

---

### 3.4 The Critic (Red Teamer Agent)
**Responsibility:** Validate sources and identify biases

**Process:**
1. Check all sources against "Safe List" (curated institutional sources)
2. Identify potential propaganda or misinformation
3. Flag data anomalies or outliers
4. Cross-validate across multiple sources
5. Output: `validation_status`, `bias_flags`, `data_quality_score`

**Safe List Categories:**
- **Official:** World Bank, IMF, UN agencies, Central Banks
- **Institutional:** Reuters, AP, AFP, Bloomberg (for factual reporting)
- **Academic:** Peer-reviewed journals, research institutions
- **Regional:** Trusted MENA-specific sources (AIM Technologies, local news agencies)

**Output Schema:**
```json
{
  "claim": "Oil price will reach $150 by Q2 2025",
  "validation_status": "FLAGGED",
  "bias_score": 0.72,
  "issues": [
    "Source is known for bullish oil forecasts",
    "No peer review or institutional backing",
    "Contradicts World Bank baseline"
  ],
  "recommendation": "Use with caution; reduce confidence by 30%"
}
```

---

### 3.5 The Governor (Ethical Oversight Agent)
**Responsibility:** Enforce ethical guidelines and track attribution

**Process:**
1. Validate all predictions against ethical guidelines
2. Track complete citation lineage for every forecast
3. Ensure compliance with data protection regulations
4. Monitor for potential harmful outputs
5. Log all decisions for audit trail

**Ethical Guidelines:**
- No predictions used for market manipulation
- No personal data exposure
- Transparent about model limitations
- Balanced representation of geopolitical actors
- Respect for cultural sensitivities (MENA region)

**Output Schema:**
```json
{
  "prediction_id": "pred_20250217_001",
  "ethical_status": "APPROVED",
  "citation_chain": [
    "GDELT Event #xyz (confidence 0.85)",
    "NewsAPI.ai Article #abc (source: Reuters)",
    "World Bank Data (2024 Q4)",
    "Polygon.io Market Data (real-time)"
  ],
  "data_protection_status": "COMPLIANT",
  "audit_log": "All PII removed; aggregated data only"
}
```

---

## 4. LangGraph State Management

### State Object Schema
```python
from typing import TypedDict, List, Dict, Any
from datetime import datetime

class ForecastState(TypedDict):
    """Central state object for multi-agent workflow"""
    
    # Request metadata
    request_id: str
    timestamp: datetime
    user_id: str
    scenario: str  # e.g., "Middle East Oil Price", "USD/KWD Stability"
    
    # Temporal Analyst outputs
    temporal_forecast: Dict[str, Any]
    temporal_confidence: float
    temporal_model: str
    
    # Context Interpreter outputs
    context_sentiment: Dict[str, Any]
    context_themes: List[str]
    context_confidence: float
    
    # Quantifier outputs
    quantified_forecast: Dict[str, Any]
    quantified_confidence: float
    adjustment_rationale: str
    
    # Critic validation
    validation_status: str  # "APPROVED", "FLAGGED", "REJECTED"
    bias_flags: List[str]
    data_quality_score: float
    
    # Governor oversight
    ethical_status: str  # "APPROVED", "REQUIRES_REVIEW", "REJECTED"
    citation_chain: List[str]
    audit_log: List[str]
    
    # Final output
    executive_summary: str
    strategic_recommendation: str
    confidence_intervals: Dict[str, float]
    
    # Error handling
    errors: List[str]
    warnings: List[str]
```

---

## 5. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER REQUEST                                 │
│              (Scenario: "Middle East Stability")                │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
   ┌─────────────┐          ┌──────────────┐
   │  TEMPORAL   │          │   CONTEXT    │
   │  ANALYST    │          │ INTERPRETER  │
   └────┬────────┘          └──────┬───────┘
        │                         │
        │ Polygon.io             │ GDELT 2.0
        │ Alpha Vantage          │ NewsAPI.ai
        │ World Bank             │ Neo4j Graph
        │ yfinance               │ Sentiment API
        │                         │
        └────────────┬────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  THE QUANTIFIER │
            │   (Middleware)  │
            └────────┬────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌──────────┐
    │ CRITIC │  │GOVERNOR│  │PostgreSQL│
    │(Validation)│(Ethics)│  │ Storage  │
    └────┬───┘  └────┬───┘  └──────────┘
         │           │
         └─────┬─────┘
               │
               ▼
        ┌─────────────────┐
        │  FINAL OUTPUT   │
        │  (Forecast +    │
        │   Confidence +  │
        │   Attribution)  │
        └─────────────────┘
```

---

## 6. API Integration Strategy

### Real-Time Data Feeds
1. **GDELT 2.0 Doc API** → Event detection (15-min updates)
2. **Polygon.io WebSocket** → Market ticks (millisecond latency)
3. **NewsAPI.ai REST** → Structured news events
4. **Alpha Vantage REST** → Technical indicators

### Batch Data Ingestion
1. **World Bank API** → Economic indicators (daily)
2. **Oxford Economics** → Macro forecasts (weekly)
3. **Financial Modeling Prep** → Earnings transcripts (quarterly)
4. **Semantic Scholar** → Academic consensus (weekly)

### Regional Intelligence
1. **AIM Technologies** → MENA sentiment analysis
2. **Webz.io** → Dark web/forum monitoring
3. **NewsData.io** → Hyper-local sources (85k+ outlets)

---

## 7. Project Directory Structure

```
zarqa-al-yamama/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── config.py               # Environment & settings
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── temporal_analyst.py
│   │   │   ├── context_interpreter.py
│   │   │   ├── quantifier.py
│   │   │   ├── critic.py
│   │   │   └── governor.py
│   │   ├── graph/
│   │   │   ├── __init__.py
│   │   │   ├── state.py            # State schema
│   │   │   ├── workflow.py         # LangGraph definition
│   │   │   └── nodes.py            # Agent node implementations
│   │   ├── integrations/
│   │   │   ├── __init__.py
│   │   │   ├── gdelt.py
│   │   │   ├── polygon.py
│   │   │   ├── alpha_vantage.py
│   │   │   ├── newsapi.py
│   │   │   ├── world_bank.py
│   │   │   └── llm.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── postgres.py         # PostgreSQL ORM
│   │   │   ├── qdrant.py           # Vector DB client
│   │   │   ├── neo4j.py            # Knowledge graph
│   │   │   └── models.py           # SQLAlchemy models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py           # REST endpoints
│   │   │   └── schemas.py          # Pydantic schemas
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── validators.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_agents.py
│   │   ├── test_workflow.py
│   │   └── test_integrations.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── forecast/
│   │   │   └── [id]/page.tsx
│   │   └── api/
│   │       └── [...].ts
│   ├── components/
│   │   ├── ForecastChart.tsx
│   │   ├── SentimentGauge.tsx
│   │   ├── ConfidenceIndicator.tsx
│   │   └── CitationPanel.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── utils.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.js
├── docker-compose.yml
├── .env.example
├── README.md
└── ARCHITECTURE.md
```

---

## 8. Docker Infrastructure

### Services
1. **PostgreSQL** - Time-series and transactional data
2. **Qdrant** - Vector embeddings (news/reports)
3. **Neo4j** - Knowledge graph (relationships)
4. **Redis** - Cache and session state
5. **Backend** - FastAPI application
6. **Frontend** - Next.js application

### Environment Variables
```
# API Keys
OPENROUTER_API_KEY=sk-or-v1-...
DEEPSEEK_API_KEY=sk-...
GDELT_API_KEY=...
NEWSAPI_KEY=...
POLYGON_API_KEY=...
ALPHA_VANTAGE_KEY=...
WORLD_BANK_KEY=...

# Database URLs
DATABASE_URL=postgresql://user:pass@postgres:5432/zarqa
QDRANT_URL=http://qdrant:6333
NEO4J_URI=bolt://neo4j:7687
REDIS_URL=redis://redis:6379

# System Configuration
SYSTEM_PROMPT=Initializing Zarqa al Yamama...
CREATOR=Qusai Al-Duaij
ENVIRONMENT=production
```

---

## 9. Output Format Specification

Every API response follows this structure:

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
      "forecast_90d": 80.0,
      "confidence_30d": 0.72,
      "confidence_90d": 0.58
    },
    "weak_signals": [
      {
        "signal": "Reduced diplomatic tensions in Strait of Hormuz",
        "source": "GDELT + Reuters",
        "sentiment_shift": -0.35,
        "impact": "negative_for_prices"
      },
      {
        "signal": "US shale production increase",
        "source": "EIA Weekly Report",
        "magnitude": "+150k barrels/day",
        "impact": "negative_for_prices"
      }
    ],
    "strategic_recommendation": "Current market pricing at $85 appears elevated. Consider hedging long positions. Monitor Strait tensions for upside risk.",
    "confidence_intervals": {
      "lower_bound_30d": 78.0,
      "upper_bound_30d": 87.0,
      "lower_bound_90d": 72.0,
      "upper_bound_90d": 88.0
    },
    "citations": [
      "GDELT Event Database (2025-02-17)",
      "Reuters: Middle East Tensions Index",
      "EIA Weekly Petroleum Status Report",
      "Polygon.io: Brent Crude Futures",
      "World Bank: Commodity Price Index"
    ]
  },
  "metadata": {
    "agents_executed": ["temporal_analyst", "context_interpreter", "quantifier", "critic", "governor"],
    "processing_time_ms": 2847,
    "data_freshness": "real-time"
  }
}
```

---

## 10. Security & Compliance

### Authentication
- JWT tokens for API access
- Role-based access control (RBAC)
- API key rotation every 90 days

### Data Protection
- All PII removed from analysis
- Aggregated data only in outputs
- Encrypted database connections
- Audit logging for all predictions

### Regulatory Compliance
- GDPR-compliant data handling
- Kuwaiti data protection regulations
- No market manipulation safeguards
- Transparent attribution chains

---

## 11. Deployment Strategy

### Development
- Local Docker Compose setup
- Hot-reload for Python/TypeScript
- SQLite for rapid prototyping

### Staging
- Full Docker stack on cloud VM
- Real API integrations
- Load testing and validation

### Production
- Kubernetes orchestration
- Multi-region redundancy
- CDN for frontend assets
- 24/7 monitoring and alerting

---

## 12. Success Metrics

1. **Forecast Accuracy:** RMSE < 5% for 30-day predictions
2. **Latency:** API response < 2 seconds (p95)
3. **Uptime:** 99.9% availability
4. **Source Quality:** 95%+ of citations from Safe List
5. **User Adoption:** 50+ active users in first quarter

---

## 13. Implementation History (V1 Build Log)

> **NOTE:** This section tracks the completed V1 build process. For the future V2 roadmap, refer to `ZARQA AL YAMAMA - SYSTEM OVERVIEW.md`.

1. **Phase 1 [COMPLETED]:** Scaffold monorepo with Next.js + FastAPI
2. **Phase 2 [COMPLETED]:** Configure Docker infrastructure
3. **Phase 3 [COMPLETED]:** Implement LangGraph orchestration
4. **Phase 4 [COMPLETED]:** Build individual agents with API integrations
5. **Phase 5 [COMPLETED]:** Implement The Quantifier mathematical logic
6. **Phase 6 [COMPLETED]:** Create FastAPI endpoints and frontend UI
7. **Phase 7 [COMPLETED]:** Integration testing and validation
8. **Phase 8 [COMPLETED]:** Documentation and delivery

---

**Document Version:** 1.0  
**Last Updated:** 2025-02-17  
**Status:** Ready for Implementation
