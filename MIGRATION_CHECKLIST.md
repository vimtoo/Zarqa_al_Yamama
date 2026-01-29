# ZARQA AL YAMAMA - MIGRATION CHECKLIST (V1 -> V2)

**Status:** ✅ PRODUCTION-READY (with documented debt)
**Version:** 2.0.0-Foundation
**Last Updated:** 2026-01-13 (Antigravity Audit)

---

## 1. V2 Core Architecture
The foundational logic for the multi-agent system.

- [x] **State Management**: `ForecastState` implemented with immutable Pydantic models.
- [x] **Orchestration**: LangGraph workflow successfully routes between 6+ nodes.
- [x] **Agent Specialization**:
  - [x] `Temporal Analyst` (H2O/Stats)
  - [x] `Context Interpreter` (Sentiment/GDELT)
  - [x] `The Quantifier` (Optimization/Fusion)
  - [x] `The Critic` (Bias/Quality)
  - [x] `The Governor` (Ethics/compliance)
- [x] **Data Contracts**: Strict schema enforcement via `backend/app/graph/contracts.py`.

## 2. Fusion & Explainability (Quantifier V2)
The core mathematical engine for signal synthesis.

- [x] **ExplainFusion Schema**: Tables for `independence_trace`, `penalty_rationale`, `horizon_contributions`.
- [x] **Independence Penalty**: Causal logic implemented (Evidence Count vs Cluster Count).
- [x] **Horizon Semantics**: "Short-term only" logic enforced via `inactive_horizons`.
- [x] **Verification**: `test_e2e_toy_scenario_complete` passes with full audit trace assertions.

## 3. Infrastructure & Runtime
Deployment and execution environment.

- [x] **Docker Container**: `backend/Dockerfile` locked to `python:3.11-slim`.
- [x] **Startup Scripts**: `start_zarqa.sh` and `install.sh` operational.
- [x] **Configuration**: `.env` loading and validation via `pydantic-settings`.
- [!] **Local Environment**: **[DEBT]** Scripts default to system Python (often 3.9) instead of enforcing 3.11.

## 4. Prompt Governance
Control over LLM instructions.

- [x] **Central Registry**: `backend/app/llm/antigravity.py` established.
- [x] **Generic Adapters**: `market_adapter_v1`, `json_repair_v1` centralized.
- [!] **Agent Prompts**: **[DEBT]** Individual agents (`qualitative_quantifier`, `domain_router`, etc.) contain hardcoded prompt strings ("Shadow IT").

## 5. Frontend Integration
User interface and visualization.

- [x] **Forecast Dashboard**: Displays probability, confidence intervals, and reasoning.
- [x] **API Integration**: Connects to `/api/v1/forecast` endpoints.
- [x] **Visualizations**: Plotly.js charts for time-series data.

---

## Post-Delivery Debt (Non-Blocking)
Items to be addressed in the next maintenance cycle (V2.1).

1.  **Prompt Refactor**: Move all hardcoded agent prompts to `antigravity.py`.
2.  **Runtime Enforcer**: Update `setup_project.sh` to strictly require Python 3.11+.
3.  **Test Coverage**: Add negative regression tests for low-confidence fail-closed paths.
