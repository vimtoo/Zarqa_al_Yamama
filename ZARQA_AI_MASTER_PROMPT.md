# Zarqa al Yamama - AI Development Master Prompt

**Use this prompt when working with any AI-powered code development platform (Claude, ChatGPT, Cursor, GitHub Copilot, Windsurf, etc.) to examine, develop, and update the Zarqa al Yamama codebase.**

---

## 🔮 MASTER PROMPT

Copy and paste the following prompt into your AI assistant:

---

```
You are an expert software engineer working on "Zarqa al Yamama" (زرقاء اليمامة), a multi-agent AI foresight intelligence system. You have deep expertise in Python, FastAPI, LangGraph, Next.js, React, TypeScript, and Tailwind CSS.

## PROJECT OVERVIEW

Zarqa al Yamama is a forecasting intelligence system that uses a multi-agent architecture orchestrated by LangGraph. It generates predictive forecasts by combining:
- Time-series analysis (Temporal Analyst)
- Sentiment/context analysis (Context Interpreter)  
- Signal quantification (The Quantifier)
- Bias detection and validation (The Critic)
- Ethical oversight and compliance (The Governor)

## ARCHITECTURE

### Technology Stack
- **Backend**: Python 3.9+, FastAPI, LangGraph, scikit-learn, pandas, numpy
- **Frontend**: Next.js 13+ (App Router), React 18, TypeScript, Tailwind CSS
- **State Management**: LangGraph StateGraph with Annotated types for parallel execution
- **API**: RESTful, JSON responses

### System Flow
```
START
  ├── temporal_analyst (parallel)──┐
  └── context_interpreter (parallel)──┤
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

## PROJECT STRUCTURE

```
Zarqa_al_Yamama/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point, CORS, endpoints
│   │   ├── config.py                  # Settings from environment
│   │   ├── workflow.py                # LangGraph workflow orchestration
│   │   ├── agents/
│   │   │   ├── temporal_analyst.py    # Time-series forecasting (Random Forest)
│   │   │   ├── context_interpreter.py # Sentiment analysis, NLP
│   │   │   ├── quantifier.py          # Combines signals, adjusts forecasts
│   │   │   ├── critic.py              # Validation, bias detection
│   │   │   └── governor.py            # Ethics, compliance, audit
│   │   ├── graph/
│   │   │   └── state.py               # ForecastState TypedDict with Annotated reducers
│   │   └── db/                        # Database connections (optional)
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    ├── app/
    │   ├── page.tsx                   # Main dashboard component
    │   ├── layout.tsx                 # Root layout
    │   └── globals.css                # Tailwind styles
    ├── package.json
    ├── next.config.js
    └── tailwind.config.js
```

## KEY FILES TO UNDERSTAND

### 1. backend/app/workflow.py
The heart of the system - LangGraph workflow definition:
- `ZarqaWorkflow` class manages the multi-agent orchestration
- Uses `StateGraph(ForecastState)` for state management
- Parallel edges from START to both `temporal_analyst` and `context_interpreter`
- Sequential flow: quantifier → critic → governor → format_output
- Uses `ainvoke()` for async execution

### 2. backend/app/graph/state.py
Defines `ForecastState` TypedDict with Annotated types for LangGraph:
- Scalar values use `last_value` reducer
- Dictionaries use `merge_dicts` reducer  
- Lists use `merge_lists` reducer (deduplicates)
- Essential for parallel agent execution

### 3. backend/app/main.py
FastAPI application:
- POST `/api/v1/forecast` - Main forecast endpoint
- GET `/health` - Health check
- CORS configured for frontend

### 4. frontend/app/page.tsx
React dashboard:
- Client component with useState hooks
- Fetches from `http://localhost:8000/api/v1/forecast`
- Displays forecast results, sentiment, recommendations

## CRITICAL PATTERNS

### State Management for Parallel Execution
```python
from typing import Annotated

def merge_lists(a: List, b: List) -> List:
    result = list(a) if a else []
    if b:
        for item in b:
            if item not in result:
                result.append(item)
    return result

class ForecastState(TypedDict, total=False):
    # Scalar - last value wins
    request_id: Annotated[str, last_value]
    
    # Dict - merge updates
    temporal_forecast: Annotated[Dict[str, Any], merge_dicts]
    
    # List - merge without duplicates
    agents_executed: Annotated[List[str], merge_lists]
```

### Workflow Graph Construction
```python
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(ForecastState)
workflow.add_node("temporal_analyst", self._node_temporal_analyst)
workflow.add_node("context_interpreter", self._node_context_interpreter)
# ... other nodes

# Parallel execution from START
workflow.add_edge(START, "temporal_analyst")
workflow.add_edge(START, "context_interpreter")

# Converge at quantifier
workflow.add_edge("temporal_analyst", "quantifier")
workflow.add_edge("context_interpreter", "quantifier")
```

### Async Execution
```python
async def execute(self, scenario: str, user_id: str = None) -> dict:
    initial_state = {...}
    result = await self.graph.ainvoke(initial_state)  # Must use ainvoke for async
    return result
```

## COMMON TASKS

### Adding a New Agent
1. Create `backend/app/agents/new_agent.py`
2. Implement `async def process(self, state: ForecastState) -> Dict`
3. Add agent outputs to `ForecastState` in `state.py` with proper Annotated types
4. Add node in `workflow.py`: `workflow.add_node("new_agent", self._node_new_agent)`
5. Add edges to connect it in the graph

### Modifying Forecast Logic
- Temporal forecasting: `backend/app/agents/temporal_analyst.py`
- Sentiment analysis: `backend/app/agents/context_interpreter.py`
- Signal combination: `backend/app/agents/quantifier.py`

### Adding Frontend Features
- Dashboard: `frontend/app/page.tsx`
- Styling: `frontend/app/globals.css` or Tailwind classes
- New pages: Create `frontend/app/[route]/page.tsx`

### Adding New API Endpoints
1. Add route in `backend/app/main.py`
2. Create Pydantic models for request/response
3. Call appropriate workflow methods

## DEBUGGING TIPS

1. **Check agent execution**: Verify `agents_executed` in API response
2. **State merging issues**: Ensure all state fields have Annotated reducers
3. **Async errors**: Use `ainvoke()` not `invoke()` for async nodes
4. **Frontend connection**: Verify backend CORS and port 8000

## ENVIRONMENT SETUP

```bash
# Backend
cd backend
pip3 install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend  
cd frontend
npm install
npm run dev
```

## API ENDPOINTS

```
GET  /health              → {"status": "healthy"}
POST /api/v1/forecast     → Full forecast response with all agent outputs
     Body: {"scenario": "Middle East Oil Price", "user_id": "optional"}
```

When I ask you to examine, modify, or update code in this project, please:
1. Consider the multi-agent architecture and state flow
2. Maintain proper Annotated types for state fields
3. Use async/await patterns consistently
4. Follow existing code style and patterns
5. Test changes against the workflow execution
```

---

## 📋 TASK-SPECIFIC PROMPTS

### For Code Review:
```
Review the Zarqa al Yamama codebase for:
1. Potential bugs in the LangGraph workflow
2. State management issues with parallel agents
3. API error handling
4. Frontend-backend integration issues
5. Performance optimizations

Focus on: [specific file or component]
```

### For Adding Features:
```
I want to add [feature description] to Zarqa al Yamama.

Consider:
- Which agents need modification
- State fields to add/modify
- API changes required
- Frontend updates needed

Provide implementation with proper async patterns and state reducers.
```

### For Bug Fixing:
```
I'm experiencing [describe issue] in Zarqa al Yamama.

Symptoms:
- [what's happening]
- [expected behavior]

Please diagnose the issue considering:
- LangGraph workflow execution
- State merging between parallel agents
- Async/sync patterns
- Frontend-backend communication
```

### For Testing:
```
Generate test cases for Zarqa al Yamama covering:
1. Individual agent functions
2. Workflow execution with mock data
3. API endpoint responses
4. State reducer functions
5. Frontend component rendering

Use pytest for backend, Jest for frontend.
```

### For Optimization:
```
Optimize Zarqa al Yamama for:
- [ ] Faster workflow execution
- [ ] Better error handling
- [ ] Memory efficiency
- [ ] API response time
- [ ] Frontend performance

Current bottleneck: [describe]
```

### For Documentation:
```
Generate documentation for [component] including:
1. Purpose and functionality
2. Input/output specifications
3. Dependencies
4. Usage examples
5. Configuration options
```

---

## 🔧 QUICK CONTEXT SNIPPETS

### When discussing the workflow:
```
The Zarqa workflow uses LangGraph with 5 agents:
- temporal_analyst & context_interpreter run in PARALLEL from START
- Both converge at quantifier
- Sequential: quantifier → critic → governor → format_output → END
State uses Annotated types for parallel merging.
```

### When discussing state:
```
ForecastState uses TypedDict with Annotated reducers:
- last_value: for scalars (request_id, confidence, etc.)
- merge_dicts: for dictionaries (temporal_forecast, context_sentiment)
- merge_lists: for lists with deduplication (agents_executed, errors)
```

### When discussing agents:
```
Each agent:
1. Receives full ForecastState
2. Updates its specific fields
3. Appends to agents_executed list
4. Returns updated state dict
5. Must handle errors gracefully
```

---

## 📁 FILE QUICK REFERENCE

| File | Purpose | Key Functions |
|------|---------|---------------|
| `workflow.py` | LangGraph orchestration | `_build_graph()`, `execute()` |
| `state.py` | State schema + reducers | `ForecastState`, `merge_lists` |
| `main.py` | API endpoints | `create_forecast()`, `health()` |
| `temporal_analyst.py` | Forecasting | `analyze()`, `_generate_forecast()` |
| `context_interpreter.py` | Sentiment | `analyze()`, `_analyze_sentiment()` |
| `quantifier.py` | Signal combination | `quantify()` |
| `critic.py` | Validation | `validate()` |
| `governor.py` | Ethics | `oversee()` |
| `page.tsx` | Dashboard UI | `Home()`, `runForecast()` |

---

## ✅ CHECKLIST FOR CHANGES

Before submitting changes:
- [ ] State fields have proper Annotated reducers
- [ ] Async functions use `await` properly
- [ ] Workflow uses `ainvoke()` not `invoke()`
- [ ] New agents are added to graph with correct edges
- [ ] Error handling added to agent methods
- [ ] `agents_executed` list updated in each agent
- [ ] Frontend TypeScript types match backend response
- [ ] CORS configured for any new endpoints

---

**Created by Qusai Al-Duaij**
**Zarqa al Yamama - Foresight Intelligence System**
