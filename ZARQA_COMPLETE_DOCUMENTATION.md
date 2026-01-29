# Zarqa al Yamama - Complete Documentation

## زرقاء اليمامة • Foresight Intelligence System

A multi-agent AI system for predictive analytics and forecasting, leveraging LangGraph for orchestrated agent workflows.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [System Setup](#system-setup)
4. [Project Structure](#project-structure)
5. [Agent Descriptions](#agent-descriptions)
6. [Workflow Execution](#workflow-execution)
7. [API Reference](#api-reference)
8. [Frontend Components](#frontend-components)
9. [State Management](#state-management)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

**Zarqa al Yamama** (زرقاء اليمامة) is an AI-powered foresight intelligence system that generates predictive forecasts using a multi-agent architecture. Named after the legendary Arabian prophetess known for her far-seeing vision, this system combines:

- **Temporal Analysis**: Time-series forecasting using machine learning
- **Context Interpretation**: Sentiment analysis and narrative understanding
- **Quantification**: Combining multiple signals into unified predictions
- **Critical Validation**: Bias detection and data quality assessment
- **Ethical Governance**: Compliance and audit trail management

### Key Features
- Multi-agent workflow orchestration with LangGraph
- Parallel execution of independent agents
- Real-time forecast generation
- Sentiment-adjusted predictions
- Bias detection and weak signal identification
- Beautiful React-based frontend dashboard

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                    (Next.js + React)                            │
│                   localhost:3000                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│                    (FastAPI + LangGraph)                        │
│                   localhost:8000                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    WORKFLOW GRAPH                        │   │
│  │                                                          │   │
│  │         ┌──────────────────────────────────┐            │   │
│  │         │           START                   │            │   │
│  │         └──────────────────────────────────┘            │   │
│  │                    / \                                   │   │
│  │                   /   \                                  │   │
│  │                  ▼     ▼                                 │   │
│  │   ┌──────────────────┐  ┌──────────────────┐           │   │
│  │   │ Temporal Analyst │  │Context Interpreter│           │   │
│  │   │   (Forecasting)  │  │  (Sentiment)     │           │   │
│  │   └──────────────────┘  └──────────────────┘           │   │
│  │                  \     /                                 │   │
│  │                   \   /                                  │   │
│  │                    ▼ ▼                                   │   │
│  │         ┌──────────────────────────────────┐            │   │
│  │         │        The Quantifier             │            │   │
│  │         │   (Combines & Adjusts)           │            │   │
│  │         └──────────────────────────────────┘            │   │
│  │                      │                                   │   │
│  │                      ▼                                   │   │
│  │         ┌──────────────────────────────────┐            │   │
│  │         │         The Critic                │            │   │
│  │         │   (Validates & Checks Bias)      │            │   │
│  │         └──────────────────────────────────┘            │   │
│  │                      │                                   │   │
│  │                      ▼                                   │   │
│  │         ┌──────────────────────────────────┐            │   │
│  │         │        The Governor               │            │   │
│  │         │   (Ethics & Compliance)          │            │   │
│  │         └──────────────────────────────────┘            │   │
│  │                      │                                   │   │
│  │                      ▼                                   │   │
│  │         ┌──────────────────────────────────┐            │   │
│  │         │       Format Output               │            │   │
│  │         │   (Summary & Recommendations)    │            │   │
│  │         └──────────────────────────────────┘            │   │
│  │                      │                                   │   │
│  │                      ▼                                   │   │
│  │         ┌──────────────────────────────────┐            │   │
│  │         │            END                    │            │   │
│  │         └──────────────────────────────────┘            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## System Setup

### Prerequisites
- Python 3.11+ (Strict Requirement)
- Node.js 18+
- npm or yarn

### Complete Setup Commands

```bash
# 1. Clone/Navigate to project directory
cd /path/to/Zarqa_al_Yamama

# 2. Install Backend Dependencies
cd backend
pip3 install -r requirements.txt

# 3. Create Environment File (if not exists)
cp .env.example .env
# Edit .env with your API keys if needed

# 4. Install Frontend Dependencies
cd ../frontend
npm install

# 5. Start Backend Server (Terminal 1)
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Start Frontend Server (Terminal 2)
cd ../frontend
npm run dev

# 7. Access the Application
# Open browser to: http://localhost:3000
```

### Quick Start (Single Command)
```bash
# Start both servers (requires two terminals)

# Terminal 1 - Backend:
cd backend && pip3 install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend:
cd frontend && npm install && npm run dev
```

### Using Docker (Alternative)
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Verify Installation
```bash
# Test backend health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Test forecast endpoint
curl -X POST http://localhost:8000/api/v1/forecast \
  -H "Content-Type: application/json" \
  -d '{"scenario": "Middle East Oil Price"}'
```

---

## Project Structure

```
Zarqa_al_Yamama/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration settings
│   │   ├── main.py                # FastAPI application entry
│   │   ├── workflow.py            # LangGraph workflow orchestration
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── temporal_analyst.py    # Time-series forecasting agent
│   │   │   ├── context_interpreter.py # Sentiment analysis agent
│   │   │   ├── quantifier.py          # Signal combination agent
│   │   │   ├── critic.py              # Validation agent
│   │   │   └── governor.py            # Ethics/compliance agent
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── init_db.py
│   │   │   ├── neo4j.py           # Graph database (optional)
│   │   │   └── qdrant.py          # Vector database (optional)
│   │   └── graph/
│   │       ├── __init__.py
│   │       └── state.py           # LangGraph state definitions
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile
│   └── .env                       # Environment variables
│
├── frontend/
│   ├── app/
│   │   ├── globals.css            # Global styles
│   │   ├── layout.tsx             # Root layout
│   │   └── page.tsx               # Main dashboard page
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker-compose.yml             # Docker orchestration
└── ZARQA_COMPLETE_DOCUMENTATION.md # This file
```

---

## Agent Descriptions

### 1. Temporal Analyst (`temporal_analyst.py`)
**Purpose:** Generates numeric forecasts using time-series analysis

**How it works:**
- Fetches historical data (simulated or from APIs like Polygon.io, Alpha Vantage)
- Prepares features with lagged values and moving averages
- Trains a Random Forest regression model
- Generates 30-day and 90-day forecasts with confidence scores

**Outputs:**
- `temporal_forecast`: Contains current value, 30d/90d forecasts
- `temporal_confidence`: Model confidence score (0-1)
- `temporal_drivers`: Key factors driving the forecast
- `temporal_data_sources`: Data sources used

### 2. Context Interpreter (`context_interpreter.py`)
**Purpose:** Analyzes qualitative context and sentiment

**How it works:**
- Gathers news and social media mentions (simulated)
- Performs sentiment analysis using NLP
- Identifies key themes and actors
- Determines narrative momentum (accelerating/decelerating)

**Outputs:**
- `context_sentiment`: Sentiment score and narrative momentum
- `context_themes`: Identified topics (e.g., "Geopolitical Risk")
- `context_key_actors`: Important entities mentioned
- `context_mentions_24h`: Volume of recent mentions

### 3. The Quantifier (`quantifier.py`)
**Purpose:** Combines temporal and contextual signals

**How it works:**
- Takes base forecast from Temporal Analyst
- Applies sentiment-based adjustments
- Calculates risk weights and volatility factors
- Produces a final adjusted forecast

**Outputs:**
- `quantified_forecast`: Final forecast values
- `quantified_confidence`: Combined confidence
- `adjustment_rationale`: Explanation of adjustments
- `sentiment_adjustment`: Magnitude of sentiment impact

### 4. The Critic (`critic.py`)
**Purpose:** Validates forecast quality and detects bias

**How it works:**
- Checks data quality scores
- Identifies potential biases in the analysis
- Validates source credibility
- Flags issues for review

**Outputs:**
- `validation_status`: APPROVED, FLAGGED, or REJECTED
- `bias_flags`: List of identified biases
- `data_quality_score`: Overall quality assessment
- `source_validation_results`: Source credibility checks

### 5. The Governor (`governor.py`)
**Purpose:** Ensures ethical compliance and audit trails

**How it works:**
- Applies ethical guidelines
- Maintains citation chains for transparency
- Creates audit logs
- Checks data protection compliance

**Outputs:**
- `ethical_status`: Compliance status
- `citation_chain`: Traceable data sources
- `audit_log`: Decision trail
- `data_protection_status`: Privacy compliance

---

## Workflow Execution

### Execution Flow

1. **Request Received**: User submits a forecast scenario
2. **State Initialization**: Create initial `ForecastState` with scenario details
3. **Parallel Execution**: `temporal_analyst` and `context_interpreter` run simultaneously
4. **Convergence**: Both outputs merge at `quantifier`
5. **Sequential Processing**: `quantifier` → `critic` → `governor` → `format_output`
6. **Response**: Final state returned with all forecasts and metadata

### State Merging (LangGraph)

The system uses annotated types for proper state merging during parallel execution:

```python
# Scalar values: last value wins
request_id: Annotated[str, last_value]

# Dictionaries: merge updates
temporal_forecast: Annotated[Dict[str, Any], merge_dicts]

# Lists: merge without duplicates
agents_executed: Annotated[List[str], merge_lists]
```

---

## API Reference

### Health Check
```http
GET /health
```
**Response:**
```json
{"status": "healthy"}
```

### Create Forecast
```http
POST /api/v1/forecast
Content-Type: application/json

{
    "scenario": "Middle East Oil Price",
    "user_id": "optional_user_id"
}
```

**Response:**
```json
{
    "request_id": "req_20251218_100000_abc123",
    "timestamp": "2025-12-18T10:00:00.000000",
    "scenario": "Middle East Oil Price",
    "temporal_forecast": {
        "metric": "Middle East Oil Price",
        "current_value": 89.62,
        "forecast_30d": 83.21,
        "confidence_30d": 0.92
    },
    "context_sentiment": {
        "sentiment_score": -0.4,
        "narrative_momentum": "accelerating",
        "mentions_24h": 6590
    },
    "quantified_forecast": {
        "final_forecast": 83.21,
        "final_confidence": 0.92,
        "adjustment_rationale": "Sentiment adjustment applied"
    },
    "executive_summary": "Middle East Oil Price forecast shows...",
    "strategic_recommendation": "Consider hedging...",
    "weak_signals": [...],
    "agents_executed": ["temporal_analyst", "context_interpreter", "quantifier", "critic", "governor"],
    "processing_time_ms": 75
}
```

---

## Frontend Components

### Main Dashboard (`page.tsx`)

**Components:**
1. **Header**: System title and online status indicator
2. **Forecast Input**: Text input with quick scenario buttons
3. **Results Panel**: Displays when forecast is available
   - Executive Summary
   - Key Metrics (Current Value, Forecast, Sentiment)
   - Strategic Recommendation
   - Weak Signals
   - Processing Metadata

**State Management:**
- `scenario`: Current forecast scenario text
- `loading`: Loading state during API call
- `result`: Forecast response data
- `error`: Error message if request fails

### Styling
- **Framework**: Tailwind CSS
- **Theme**: Purple/pink gradient with glassmorphism effects
- **Responsive**: Mobile-friendly design

---

## State Management

### ForecastState Schema

The central state object passed through all agents:

| Category | Fields |
|----------|--------|
| **Request Metadata** | `request_id`, `timestamp`, `user_id`, `scenario`, `forecast_horizon_days` |
| **Temporal Outputs** | `temporal_forecast`, `temporal_confidence`, `temporal_model`, `temporal_drivers`, `temporal_data_sources` |
| **Context Outputs** | `context_sentiment`, `context_themes`, `context_confidence`, `context_key_actors`, `context_mentions_24h` |
| **Quantifier Outputs** | `quantified_forecast`, `quantified_confidence`, `adjustment_rationale`, `sentiment_adjustment`, `risk_weight` |
| **Critic Outputs** | `validation_status`, `bias_flags`, `data_quality_score`, `source_validation_results` |
| **Governor Outputs** | `ethical_status`, `citation_chain`, `audit_log`, `data_protection_status` |
| **Final Output** | `executive_summary`, `strategic_recommendation`, `weak_signals` |
| **Metadata** | `errors`, `warnings`, `processing_time_ms`, `agents_executed` |

---

## Troubleshooting

### Common Issues

**1. "Failed to fetch" error on frontend**
- Ensure backend is running on port 8000
- Check CORS settings in backend
- Verify `http://localhost:8000` is accessible

**2. "ModuleNotFoundError: No module named 'X'"**
- Run `pip3 install -r requirements.txt` in backend directory

**3. "$N/A" values in frontend**
- Check backend logs for errors
- Ensure all agents are executing (check `agents_executed` in response)
- Verify state merging is working correctly

**4. "Can receive only one value per step" error**
- This is a LangGraph state merging issue
- Ensure all state fields use `Annotated` types with proper reducers

**5. Frontend not loading**
- Ensure `npm install` completed successfully
- Check Next.js is running on port 3000
- Clear browser cache and `.next` folder

### Debug Commands

```bash
# Check backend logs
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug

# Test API directly
curl -X POST http://localhost:8000/api/v1/forecast \
  -H "Content-Type: application/json" \
  -d '{"scenario": "Test"}' | python3 -m json.tool

# Check Python imports
cd backend && python3 -c "from app.main import app; print('OK')"

# Check frontend build
cd frontend && npm run build
```

---

## Configuration

### Environment Variables (`backend/.env`)

```env
# Application
APP_NAME=Zarqa al Yamama
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# Server
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Agent Settings
TEMPORAL_ANALYST_ENABLED=true
CONTEXT_INTERPRETER_ENABLED=true
CONFIDENCE_THRESHOLD=0.6
DEFAULT_FORECAST_HORIZON_DAYS=30

# Optional: API Keys for real data
POLYGON_API_KEY=your_key_here
ALPHA_VANTAGE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

---

## Credits

**Created by:** Qusai Al-Duaij

**Powered by:**
- LangGraph (Multi-agent orchestration)
- FastAPI (Backend API)
- Next.js + React (Frontend)
- Tailwind CSS (Styling)
- scikit-learn (Machine Learning)

---

*Zarqa al Yamama - Seeing Beyond the Horizon* 🔮
