# Zarqa al Yamama - Think Tank Intelligence Integration

## 🏛️ Overview

This document provides comprehensive instructions for running the Think Tank Intelligence integration in Zarqa al Yamama. The Think Tank Analyst module aggregates policy intelligence from global think tanks to enhance forecasting capabilities with expert policy analysis.

## 📚 Integrated Think Tank Sources

| Source | URL | Purpose | Refresh Rate |
|--------|-----|---------|--------------|
| **EU Council Library (Eureka)** | [consilium.europa.eu](https://www.consilium.europa.eu/en/documents-publications/library/) | EU policy documents & analysis | 24 hours |
| **Harvard Kennedy School** | [guides.library.harvard.edu](https://guides.library.harvard.edu/hks/think_tank_search) | US & Non-US think tank search | Weekly |
| **UPenn TTCSP** | [guides.library.upenn.edu](https://guides.library.upenn.edu/c.php?g=1035991&p=7509972) | Global think tank rankings | Monthly |
| **NC State Global Think Tanks** | [lib.ncsu.edu](https://www.lib.ncsu.edu/databases/global-think-tanks) | Searchable database | 24 hours |
| **RAND Corporation** | [rand.org](https://www.rand.org/news/rss.html) | Defense & security analysis | 6 hours |
| **Carnegie Endowment** | [carnegieendowment.org](https://carnegieendowment.org) | International peace & policy | 6 hours |
| **Chatham House** | [chathamhouse.org](https://www.chathamhouse.org/rss-feeds) | UK/European perspective | 6 hours |
| **Brookings Institution** | [brookings.edu](https://www.brookings.edu) | US domestic & foreign policy | 6 hours |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (Strict Requirement)
- Node.js 18+
- pip (Python package manager)
- npm (Node package manager)

### Installation Steps

#### 1. Clone and Navigate to Project

```bash
cd /Users/qusaial-duaij/Zarqa_al_Yamama
```

#### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install the new dependencies for think tank scraping:
- `beautifulsoup4>=4.12.2` - HTML parsing
- `lxml>=4.9.3` - XML/HTML processing
- `feedparser>=6.0.10` - RSS feed parsing

#### 3. Configure Environment Variables

Edit `backend/.env` to configure think tank settings (optional - defaults are provided):

```bash
# Think Tank Analyst (enabled by default)
THINK_TANK_ANALYST_ENABLED=true

# Optional: Override default URLs if needed
# EU_COUNCIL_LIBRARY_URL=https://www.consilium.europa.eu/en/documents-publications/library/
# HARVARD_KSG_BASE_URL=https://guides.library.harvard.edu/hks/think_tank_search
```

#### 4. Start the Backend Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. Start the Frontend (optional, in a new terminal)

```bash
cd frontend
npm install
npm run dev
```

## 📖 Detailed Usage

### Running a Forecast with Think Tank Intelligence

#### Via API (curl)

```bash
curl -X POST "http://localhost:8000/api/v1/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "Middle East Oil Price Impact on European Energy Security",
    "user_id": "analyst_001"
  }'
```

#### Via Python

```python
import asyncio
from app.workflow import ZarqaWorkflow

async def run_forecast():
    workflow = ZarqaWorkflow()
    result = await workflow.execute(
        scenario="Middle East Oil Price Impact on European Energy Security",
        user_id="analyst_001"
    )
    
    # Access think tank insights
    think_tank_data = result.get('think_tank_insights', {})
    print(f"Policy Insights: {len(think_tank_data.get('policy_insights', []))}")
    print(f"Sources Used: {result.get('think_tank_sources', [])}")
    print(f"Topics Identified: {result.get('think_tank_topics', [])}")
    print(f"Regions Covered: {result.get('think_tank_regions', [])}")
    
    return result

# Run
result = asyncio.run(run_forecast())
```

### API Response Structure

The forecast response now includes think tank intelligence:

```json
{
  "request_id": "req_20251220_121500_abc12345",
  "scenario": "Middle East Oil Price Impact on European Energy Security",
  "think_tank_insights": {
    "policy_insights": [
      {
        "source": "EU Council Library",
        "title": "Energy Security Policy Framework 2025",
        "summary": "Analysis of EU energy diversification strategies...",
        "url": "https://...",
        "relevance_score": 0.85,
        "topics": ["energy", "geopolitics", "security"],
        "regions": ["Europe", "Middle East"]
      }
    ],
    "policy_summary": "Analysis of 12 think tank reports from 4 sources...",
    "average_relevance": 0.72,
    "total_reports_analyzed": 45,
    "relevant_reports_count": 12
  },
  "think_tank_sources": ["EU Council Library", "Harvard Kennedy School", "RAND Corporation"],
  "think_tank_topics": ["energy", "geopolitics", "economics"],
  "think_tank_regions": ["Europe", "Middle East", "Global"],
  "think_tank_confidence": 0.82,
  "weak_signals": [
    {
      "signal": "Policy intelligence from 12 think tank reports",
      "source": "Think Tank Analyst",
      "top_sources": ["EU Council Library", "RAND Corporation"],
      "topics": ["energy", "security"],
      "impact": "enhanced_context"
    }
  ]
}
```

## 🏗️ Architecture

### Workflow Integration

```
START
  ├── temporal_analyst (parallel)─────────────┐
  ├── context_interpreter (parallel)──────────┤
  └── think_tank_analyst (parallel)───────────┤
                                              ▼
                                       quantifier
                                              │
                                              ▼
                                          critic
                                              │
                                              ▼
                                         governor
                                              │
                                              ▼
                                      format_output
                                              │
                                              ▼
                                            END
```

### New Files Created

| File | Purpose |
|------|---------|
| [`backend/app/agents/think_tank_analyst.py`](backend/app/agents/think_tank_analyst.py) | Main think tank scraping and analysis agent |

### Modified Files

| File | Changes |
|------|---------|
| [`backend/app/config.py`](backend/app/config.py) | Added think tank configuration settings |
| [`backend/app/requirements.txt`](backend/requirements.txt) | Added web scraping dependencies |
| [`backend/app/graph/state.py`](backend/app/graph/state.py) | Added think tank state fields |
| [`backend/app/workflow.py`](backend/app/workflow.py) | Integrated think tank analyst into graph |

## ⚙️ Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `THINK_TANK_ANALYST_ENABLED` | `true` | Enable/disable think tank analysis |
| `EU_COUNCIL_LIBRARY_URL` | `https://www.consilium.europa.eu/en/documents-publications/library/` | EU Council Library URL |
| `HARVARD_KSG_BASE_URL` | `https://guides.library.harvard.edu/hks/think_tank_search` | Harvard KSG URL |
| `UPENN_TTCSP_URL` | `https://guides.library.upenn.edu/c.php?g=1035991&p=7509972` | UPenn TTCSP URL |
| `NCSTATE_GLOBAL_URL` | `https://www.lib.ncsu.edu/databases/global-think-tanks` | NC State URL |
| `THINK_TANK_REQUEST_TIMEOUT` | `30` | HTTP request timeout (seconds) |
| `THINK_TANK_MAX_REPORTS_PER_SOURCE` | `20` | Max reports to fetch per source |
| `THINK_TANK_MIN_RELEVANCE_SCORE` | `0.15` | Minimum relevance score threshold |
| `THINK_TANK_MAX_RELEVANT_REPORTS` | `15` | Max relevant reports to return |

### Disabling Think Tank Analysis

To disable the think tank analyst (for faster execution or debugging):

```bash
# In backend/.env
THINK_TANK_ANALYST_ENABLED=false
```

Or programmatically:

```python
from app.config import settings
settings.THINK_TANK_ANALYST_ENABLED = False
```

## 🔧 Commands Reference

### Backend Commands

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Run server (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run server (production)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Run tests
pytest

# Run specific test file
pytest test_integrations.py -v

# Check health
curl http://localhost:8000/health
```

### Frontend Commands

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Docker Commands (if using Docker)

```bash
# Build and start all services
docker-compose up --build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## 🧪 Testing the Integration

### Test API Endpoint

```bash
# Health check
curl http://localhost:8000/health

# Test forecast with think tank scenario
curl -X POST "http://localhost:8000/api/v1/forecast" \
  -H "Content-Type: application/json" \
  -d '{"scenario": "European energy policy shifts affecting oil markets"}'
```

### Test Think Tank Analyst Directly

```python
import asyncio
from app.agents.think_tank_analyst import ThinkTankAnalyst

async def test_think_tank():
    analyst = ThinkTankAnalyst()
    
    # Fetch all sources
    reports = await analyst.fetch_all_sources()
    print(f"Total reports fetched: {len(reports)}")
    
    # Filter for a scenario
    relevant = analyst.filter_relevant_reports(
        reports, 
        "Middle East Oil Price",
        min_relevance=0.2,
        max_reports=10
    )
    
    print(f"Relevant reports: {len(relevant)}")
    for report in relevant[:3]:
        print(f"  - {report.title} ({report.source}) - Score: {report.relevance_score:.2f}")
    
    await analyst.close()

asyncio.run(test_think_tank())
```

## 📊 Topic & Region Keywords

### Topics Detected

| Topic | Keywords |
|-------|----------|
| Energy | oil, gas, energy, renewable, petroleum, OPEC, fuel |
| Geopolitics | conflict, war, diplomacy, sanctions, alliance, treaty |
| Economics | trade, tariff, GDP, inflation, recession, market |
| Technology | AI, cyber, technology, digital, semiconductor, tech |
| Security | defense, military, security, terrorism, nuclear |
| Climate | climate, carbon, emissions, sustainability, environment |
| Governance | democracy, election, policy, governance, regulation |
| Finance | banking, finance, investment, currency, debt |

### Regions Detected

| Region | Keywords |
|--------|----------|
| Middle East | Middle East, Gulf, Saudi, Iran, Iraq, Syria, Lebanon, UAE, Qatar, Kuwait, MENA, GCC |
| Europe | EU, Europe, European, NATO, UK, Britain, Germany, France |
| Asia Pacific | China, Japan, Korea, ASEAN, India, Pacific, Asia, Taiwan |
| Americas | US, USA, America, Canada, Mexico, Brazil, Latin America |
| Africa | Africa, African, Sub-Saharan, North Africa |
| Russia/Eurasia | Russia, Russian, Eurasia, Central Asia, Kazakhstan, Belarus |

## 🚨 Troubleshooting

### Common Issues

#### 1. HTTP Connection Errors

```
Error fetching https://www.consilium.europa.eu/...: Connection timeout
```

**Solution**: Check internet connection, increase timeout in config:
```python
THINK_TANK_REQUEST_TIMEOUT=60
```

#### 2. No Reports Found

```
No relevant think tank reports found for 'scenario'.
```

**Solution**: Try a more specific scenario or lower the relevance threshold:
```python
THINK_TANK_MIN_RELEVANCE_SCORE=0.1
```

#### 3. BeautifulSoup Import Error

```
ModuleNotFoundError: No module named 'bs4'
```

**Solution**: Install missing dependency:
```bash
pip install beautifulsoup4
```

#### 4. Think Tank Analyst Not Running

Check if enabled in config:
```bash
grep THINK_TANK_ANALYST_ENABLED backend/.env
```

### Logs

View detailed logs for debugging:

```bash
# Start with debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📈 Performance Considerations

- **Caching**: Reports are cached per source with configurable refresh intervals
- **Parallel Execution**: Think Tank Analyst runs in parallel with other analysts
- **Async HTTP**: All web requests are asynchronous to prevent blocking
- **Rate Limiting**: Built-in delays to respect source web servers

## 📝 License

This integration is part of the Zarqa al Yamama project. All think tank content remains property of their respective sources - this module only aggregates metadata and summaries for research purposes.

---

**Created by Qusai Al-Duaij**  
**Zarqa al Yamama - Foresight Intelligence System**
