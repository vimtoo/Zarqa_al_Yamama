# Phase 4K-G Operator Decision Package

## 1. Executive Summary

This package is for decision only.

No implementation is performed. Phase 4K remains NOT APPROVED unless Qusai explicitly approves.

The only eligible implementation route is:

```text
v2_join_node -> gemini_assist_noop -> schema_validator_node
```

## 2. Current Verified State

- Remote `main` contains commit `c5c0cf5 docs: add phase 4k workflow approval gate`.
- Remote verification recorded `c5c0cf51175d0b32c3ec9e1ce5fbcc3448c5897a refs/heads/main`.
- `workflow.py` has no Gemini wiring.
- Phase 4K approval record says `NOT APPROVED`.
- Current git status should be clean before any implementation begins.
- No live Gemini execution is approved.
- No API key is present or required.
- No production behavior change is approved.

## 3. Decision Options

### Option A — Approve Minimal Phase 4K Implementation

Approves only:

```text
v2_join_node -> gemini_assist_noop -> schema_validator_node
```

Requirements:

- Create a pre-implementation rollback tag.
- Add disabled graph wiring tests.
- Keep the patch limited to the no-op workflow route.
- Require no production behavior change.
- Keep live Gemini disabled.
- Keep API keys absent.

### Option B — Keep Blocked

Keep the documentation bundle only.

No implementation. Continue shadow/review-only Gemini work outside `workflow.py`.

### Option C — Reject Phase 4K Wiring

Do not add Gemini to `workflow.py`.

Preserve Gemini only as an isolated sidecar.

## 4. Recommended Decision

Recommended decision: **Option B — Keep Blocked**, unless Qusai explicitly wants to test disabled topology wiring.

Option A is bounded and may be safe only because the no-op adapter is already tested and the route target is confirmed as `schema_validator_node`. However, Option A still touches `workflow.py`, which controls LangGraph topology and production execution. It therefore requires explicit operator approval before implementation.

## 5. Approval Language If Qusai Chooses Option A

```text
I, Qusai, approve Phase 4K implementation only for the minimal disabled/no-op route:
v2_join_node -> gemini_assist_noop -> schema_validator_node.

I do not approve live Gemini execution, API keys, production state mutation, agent_outputs writes, Gemini-generated probabilities, Signal/HorizonForecast/FusionResult creation, replacement or bypass of QuantifierV2, CriticV2, Governor, SchemaValidator, EvidenceDeduper, IndependenceAnalyzer, Librarian, ArbitrationPolicy, or unrelated workflow topology changes.
```

## 6. Required Pre-Implementation Commands If Approved

```bash
git status --short
git tag rollback/pre-phase4k-minimal-workflow-wiring-2026-05-18
```

## 7. Required Post-Implementation Validation If Approved

Run the Phase 4K wiring test:

```bash
pytest backend/tests/test_gemini_phase4k_disabled_workflow_wiring.py -q
```

Run the full relevant safety regression slice:

```bash
pytest backend/tests/test_gemini_graph_adapter.py \
       backend/tests/test_gemini_non_interference_utils.py \
       backend/tests/test_gemini_workflow_baseline_fixture.py \
       backend/tests/test_gemini_assist_disabled_defaults.py \
       backend/tests/test_gemini_assist_integration_safety.py \
       backend/tests/test_gemini_phase4k_planning_docs.py \
       backend/tests/test_gemini_phase4k_disabled_workflow_wiring.py -q
```

Run grep checks:

```bash
grep -n "gemini_graph_noop_node" backend/app/workflow.py
grep -n "gemini_assist_noop" backend/app/workflow.py
grep -n "GeminiDeepResearchClient\|GeminiAssistNodeWrapper\|live_review_runner" backend/app/workflow.py
```

Expected:

- only no-op graph adapter import appears
- no client/wrapper/live runner imports appear

## 8. Non-Negotiable Boundaries

- no live Gemini call
- no API key
- no `ForecastState` mutation
- no `agent_outputs` write
- no `Signal`/`HorizonForecast`/`FusionResult` creation
- no schema validation bypass
- no dirty backup topology import
- no `evidence_analyst` insertion
- no report path change
- byte-for-byte disabled output must remain identical
