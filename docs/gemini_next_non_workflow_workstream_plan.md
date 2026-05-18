# Gemini Next Non-Workflow Workstream Plan

## 1. Executive Summary

Phase 4K remains blocked.

`workflow.py` remains untouched. The next Gemini Deep Research workstream should avoid LangGraph wiring entirely and should not add imports, nodes, edges, or route changes to the production graph.

The safe next focus is isolated sidecar quality: richer mocked fixtures, deterministic review artifacts, schema validation for saved shadow outputs, audit-log hardening, edge-case normalizer tests, and documentation for review-only operating modes.

## 2. Current Safe State

- Remote `main` contains `ff1b8ff docs: add phase 4k operator decision package`.
- Remote verification recorded `ff1b8ffcb7a58f8828e3cb192cc5c772c6e76f68 refs/heads/main`.
- `workflow.py` has no Gemini workflow wiring.
- Phase 4K remains `NOT APPROVED`.
- Gemini remains sidecar-only.
- No live Gemini execution is approved in this workstream.
- No `GEMINI_API_KEY` is required or added.
- No production behavior change is approved.
- No Gemini output is injected into `ForecastState`.
- No Gemini code writes `agent_outputs`.
- No Gemini code creates `Signal`, `HorizonForecast`, or `FusionResult`.

## 3. Candidate Safe Workstreams

| Candidate | Purpose | Files likely affected | Safety risk | Tests required | Can proceed without Phase 4K approval? |
|---|---|---|---|---|---|
| A. Improve shadow-run report schema validation | Validate saved shadow-run JSON and Markdown reports before human review so malformed artifacts fail closed. | `backend/app/integrations/gemini_deep_research/storage.py`, `backend/app/integrations/gemini_deep_research/models.py`, `backend/tests/test_gemini_shadow_runner.py`, new mocked fixture tests | LOW if local-only and artifact-only | Shadow runner, storage, evaluation policy, mocked malformed artifact tests | Yes |
| B. Add richer mock Gemini fixtures for allowed domains | Broaden deterministic fixtures for geopolitics, security, policy, macroeconomics, finance, technology, elections, and general domains. | `backend/tests/fixtures/` if created, `backend/tests/test_gemini_evidence_normalizer.py`, `backend/tests/test_gemini_evaluation_policy.py` | LOW if fixtures contain no secrets and no live calls | Normalizer, evaluation policy, client mock tests | Yes |
| C. Build offline review dashboard artifacts as static JSON/Markdown only | Produce local review bundles that summarize sidecar output without touching graph state or production report paths. | `backend/app/integrations/gemini_deep_research/storage.py`, `backend/app/integrations/gemini_deep_research/evaluation_policy.py`, docs, mocked tests | LOW to MEDIUM depending on output paths; must avoid `agent_outputs` and production paths | Storage/report rendering tests, path safety tests, no-write-to-production assertions | Yes |
| D. Strengthen secret-scan and audit-log tests | Ensure API keys, authorization headers, and placeholder credentials are rejected or redacted in logs and artifacts. | `backend/app/integrations/gemini_deep_research/key_validation.py`, `backend/app/integrations/gemini_deep_research/client.py`, `backend/tests/test_gemini_deep_research_client.py` | LOW if validation is only tightened and mocked | Client tests, key validation tests, artifact redaction tests | Yes |
| E. Improve evidence-pack normalizer edge-case tests | Exercise malformed citations, missing source metadata, duplicate evidence, unsupported claims, and fail-closed contract conversion. | `backend/app/integrations/gemini_deep_research/normalizer.py`, `backend/tests/test_gemini_evidence_normalizer.py` | LOW if behavior remains fail-closed | Normalizer tests, no `Signal`/`HorizonForecast`/`FusionResult` assertions | Yes |
| F. Add documentation for sidecar operating modes | Clarify shadow-only, review-only, offline evaluation, disabled assist wrapper, and blocked workflow wiring modes. | `docs/`, `backend/app/integrations/gemini_deep_research/README.md` | LOW | Static documentation checks if added | Yes |
| G. Add local-only CLI dry-run examples | Document or test dry-run commands using mocked/local artifacts only, without requiring Gemini credentials. | `docs/`, `backend/tests/test_gemini_shadow_runner.py`, possibly README | LOW if examples remain mocked and local | CLI dry-run mocked tests, no network assertions | Yes |
| H. Add regression fixtures comparing saved TheSeer outputs to `GeminiEvidencePack` | Strengthen shadow-comparison confidence with static TheSeer output fixtures and deterministic Gemini evidence packs. | `backend/tests/fixtures/`, `backend/tests/test_gemini_shadow_compare.py`, `backend/tests/test_gemini_evaluation_policy.py` | LOW to MEDIUM if fixtures mirror protected state; must remain test-only | Shadow compare tests, non-interference utility tests, protected-key assertions | Yes |

## 4. Recommended Next Workstream

Recommended next workstream: **Strengthen sidecar test coverage and offline review artifacts before any workflow approval.**

The best next stage is to harden local-only evidence packs, saved shadow-run artifacts, evaluation reports, and review bundles. This improves operator confidence without changing LangGraph topology or production behavior.

The recommended first slice is:

- add richer mocked `GeminiEvidencePack` and shadow-run fixtures for supported domains
- validate saved review artifacts deterministically
- assert review artifacts never write to `agent_outputs` or production forecast paths
- expand normalizer and evaluation-policy edge-case coverage
- keep all tests mocked and offline

## 5. Workstream Not Allowed Without Separate Approval

The following remain blocked unless a separate approval explicitly authorizes them:

- `workflow.py` wiring
- LangGraph node insertion
- LangGraph edge insertion
- live Gemini execution
- API key addition
- production state mutation
- `agent_outputs` writes
- `Signal` creation
- `HorizonForecast` creation
- `FusionResult` creation
- replacing or bypassing `QuantifierV2`
- replacing or bypassing `CriticV2`
- replacing or bypassing `Governor`
- replacing or bypassing `SchemaValidator`
- replacing or bypassing `EvidenceDeduper`
- replacing or bypassing `IndependenceAnalyzer`
- replacing or bypassing `Librarian`
- replacing or bypassing `ArbitrationPolicy`

## 6. Suggested Next Stage Name

Phase 4L-A — Sidecar Fixtures and Review Artifact Hardening

## 7. Proposed Phase 4L-A Scope

Phase 4L-A should remain sidecar-only and test-backed.

Allowed scope:

- no `workflow.py` changes
- no live Gemini execution
- no API keys
- no package changes unless a later explicit prompt approves them
- improve tests around saved/mock Gemini evidence packs
- improve audit artifact validation
- ensure deterministic offline review outputs
- ensure generated review artifacts use local sidecar paths only
- assert no writes occur to `agent_outputs` or production report paths
- assert no `Signal`, `HorizonForecast`, or `FusionResult` objects are created
- update documentation only as needed

Out of scope:

- any Phase 4K implementation
- `gemini_assist_noop` insertion
- graph adapter registration in LangGraph
- `ForecastState` mutation
- production workflow behavior changes

## 8. Proposed Phase 4L-A Test Commands

Run the sidecar and review-artifact test slice:

```bash
pytest backend/tests/test_gemini_deep_research_client.py \
       backend/tests/test_gemini_evidence_normalizer.py \
       backend/tests/test_gemini_shadow_compare.py \
       backend/tests/test_gemini_shadow_runner.py \
       backend/tests/test_gemini_evaluation_policy.py \
       backend/tests/test_gemini_assist_config.py \
       backend/tests/test_gemini_assist_audit.py \
       backend/tests/test_gemini_assist_node.py \
       backend/tests/test_gemini_assist_disabled_defaults.py \
       backend/tests/test_gemini_assist_integration_safety.py \
       backend/tests/test_gemini_graph_adapter.py \
       backend/tests/test_gemini_non_interference_utils.py \
       backend/tests/test_gemini_workflow_baseline_fixture.py \
       backend/tests/test_gemini_phase4k_planning_docs.py -q
```

Confirm `workflow.py` remains unwired:

```bash
grep -n "gemini_graph_noop_node\|gemini_assist_noop\|gemini_deep_research" backend/app/workflow.py || echo "OK: no Gemini workflow wiring"
```

If Phase 4L-A adds new fixture or artifact-validation tests, run them explicitly before the full sidecar slice:

```bash
pytest backend/tests/test_gemini_evidence_normalizer.py \
       backend/tests/test_gemini_shadow_runner.py \
       backend/tests/test_gemini_evaluation_policy.py -q
```
