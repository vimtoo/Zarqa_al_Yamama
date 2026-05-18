# Gemini Sidecar Operating Modes

## 1. Executive Summary

Gemini Deep Research is a sidecar.

It may help gather, normalize, compare, evaluate, and review evidence, but it is not a forecasting authority. It does not own TheSeer's probabilities, final forecast state, or production report path.

`workflow.py` remains unwired. Phase 4K remains NOT APPROVED. No Gemini mode may write production `ForecastState` or `agent_outputs` unless separately approved in a future governance phase.

## 2. Mode Matrix

| Mode | Purpose | Live Gemini? | API Key Required? | Writes ForecastState? | Writes agent_outputs? | Touches workflow.py? | Status |
|---|---|---|---|---|---|---|---|
| Disabled | Keep Gemini integration inert by default. | No | No | No | No | No | allowed |
| Mock Client Test | Exercise client paths with mocked responses only. | No | No | No | No | No | allowed |
| Evidence Normalization | Convert raw or mocked Gemini research results into local `GeminiEvidencePack` objects. | No | No | No | No | No | allowed |
| Shadow Compare | Compare `GeminiEvidencePack` artifacts against already saved TheSeer outputs. | No | No | No | No | No | allowed |
| Shadow Runner Offline | Run the workflow-independent runner in mock/offline mode and save sidecar review artifacts. | No | No | No | No | No | allowed |
| Evaluation Policy Offline | Aggregate saved shadow runs and render conservative readiness decisions. | No | No | No | No | No | allowed |
| Assist Wrapper Review-Only | Rehearse assist behavior outside LangGraph and emit review/audit artifacts only. | Mocked or separately gated | No for mock/review-only tests | No | No | No | allowed, review-only |
| Graph Adapter No-Op Unwired | Keep a tested no-op adapter available but not registered in LangGraph. | No | No | No | No | No | allowed, unwired |
| Phase 4K Minimal Disabled Wiring | Future minimal disabled/no-op workflow route only if explicitly approved. | No | No | No | No | Yes, only after approval | NOT APPROVED |
| Live Review Trial | Manually invoked non-production review run under a separate live-trial approval package. | Yes, only when approved | Yes, only when approved | No | No | No | requires separate explicit approval |

## 3. Non-Negotiable Boundaries

- no Gemini-generated probabilities
- no `Signal` creation
- no `HorizonForecast` creation
- no `FusionResult` creation
- no `QuantifierV2` replacement
- no `CriticV2` replacement
- no `Governor` bypass
- no `SchemaValidator` bypass
- no `EvidenceDeduper` bypass
- no `IndependenceAnalyzer` bypass
- no `Librarian` bypass
- no `ArbitrationPolicy` bypass
- no `ReportWriter` trusted-input change
- no `workflow.py` change without explicit approval
- no API key unless live trial explicitly approved

## 4. Approved Local Paths

Allowed local sidecar paths:

- `data/research/gemini_shadow_runs/`
- `data/research/gemini_assist_trials/`
- `data/research/gemini_live_review_trials/` only for separately approved live trials
- pytest-controlled `tmp_path` directories

Prohibited paths and targets:

- production report paths
- production `ForecastState` writes
- `agent_outputs`
- `backend/app/workflow.py` unless Phase 4K is explicitly approved

## 5. Review Artifact Rules

- artifacts must be deterministic where possible
- secrets must be absent or redacted
- sidecar artifacts and audit logs must not persist raw `AIza`, `sk-`, `Bearer `, `api_key=`, `password=`, `token=`, `secret=`, `Authorization`, or `[REDACTED_API_KEY]` values
- unsupported claims must fail closed or be skipped
- malformed evidence packs and malformed shadow-run artifacts must not crash review tooling
- review artifacts are not trusted production inputs
- review artifacts must not modify graph state
- review artifacts must not become `Signal`, `HorizonForecast`, or `FusionResult` objects
- review artifacts must not bypass TheSeer's validation, deduplication, independence, quantification, criticism, governance, librarian, arbitration, or report-writing boundaries

## 6. Phase 4K Gate Reminder

Phase 4K remains NOT APPROVED.

The only eligible future route is:

```text
v2_join_node -> gemini_assist_noop -> schema_validator_node
```

`evidence_analyst` insertion is out of scope. Dirty backup topology must not be copied.
