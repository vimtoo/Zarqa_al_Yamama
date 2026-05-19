# Phase 4K-EQ-A Disabled Workflow Output Equivalence Test Plan

## 1. Executive Summary

Phase 4K route is already pushed.

The route is:

```text
v2_join_node -> gemini_assist_noop -> schema_validator_node
```

This plan is test-planning only. No new workflow changes are approved. No live Gemini/API-key work is approved.

The next goal is to prove the no-op route preserves canonical output, protected state, and that `schema_validator_node receives equivalent input` behind the disabled no-op hop.

## 2. Current Remote and Rollback State

| Item | Value |
|---|---|
| Workflow implementation commit | `5d8ef76 feat: add disabled gemini workflow no-op route` |
| Post-push governance commit | `ca9a7da docs: add phase 4k post-push governance checkpoint` |
| CI validation record commit | `f3c48de docs: add phase 4k ci validation record` |
| Remote main hash | `f3c48debae50b28768e3ec100c18259585cea418 refs/heads/main` |
| Rollback tag | `rollback/pre-phase4k-minimal-workflow-wiring-2026-05-18` |
| Rollback tag hash | `ac6f812e1599e122e6a8debc981f90c9d0cb7d45` |

CI status remains unavailable locally because `gh` is not installed. Manual GitHub CI review is still required.

## 3. Equivalence Target

Disabled output equivalence means:

- protected state keys unchanged
- no Gemini state keys added in disabled execution
- no Gemini `agent_outputs` entry
- no live Gemini/client/assist wrapper/runner call
- no `Signal`/`HorizonForecast`/`FusionResult` creation
- `schema_validator_node` receives equivalent input behind the no-op hop
- canonical output remains identical for deterministic fields
- nondeterministic fields are excluded only through approved canonicalization rules

Approved canonicalization should use the existing Phase 4H/4I test utilities, including `build_default_exclusions()`, `canonicalize_state()`, `canonical_json_dump()`, `assert_canonical_equal()`, and `assert_protected_keys_unchanged()`.

## 4. Required Test Design

Recommended future test file:

```text
backend/tests/test_gemini_phase4k_disabled_output_equivalence.py
```

The future test file should include:

- static route checks
- direct no-op adapter state identity/equality checks
- protected state comparison using `backend/tests/gemini_non_interference_utils.py`
- workflow-shaped baseline fixture comparison
- no Gemini state keys assertion
- no Gemini `agent_outputs` assertion
- downstream `schema_validator_node` input equivalence fixture
- report/output canonical equivalence fixture
- no calls to Gemini client, assist wrapper, live runner, internet, or API key
- `tmp_path`-only artifacts

Suggested test groups:

| Test Group | Purpose | Required Boundary |
|---|---|---|
| Static route checks | Confirm route remains `v2_join_node -> gemini_assist_noop -> schema_validator_node`. | No additional `workflow.py` wiring. |
| No-op adapter identity/equality | Confirm `gemini_graph_noop_node` returns protected state unchanged. | No Gemini state keys or `agent_outputs` entries. |
| Baseline fixture equivalence | Compare pre/post no-op fixture state using canonical serialization. | Nondeterministic exclusions only from approved helpers. |
| Schema-validator input fixture | Prove `schema_validator_node` receives equivalent input after the no-op hop. | No downstream gate bypass. |
| Report/output canonical fixture | Confirm deterministic report/output fields remain canonically identical. | No `ReportWriter` trusted input changes. |
| Negative guard checks | Assert injected Gemini keys or Gemini `agent_outputs` entries fail the test helpers. | Fail closed if Gemini writes appear. |

## 5. Data and Fixture Strategy

Use:

- workflow-shaped baseline fixture from Phase 4I
- canonical serialization utilities from Phase 4H
- deterministic `tmp_path` artifacts only
- no live workflow if it would require external services
- no internet
- no real API keys
- no production artifact paths

The Phase 4I fixture in `backend/tests/test_gemini_workflow_baseline_fixture.py` is workflow-shaped, not a live workflow execution. That is appropriate for EQ-B because the target is disabled no-op equivalence, not live runtime coverage.

Future EQ-B tests should reuse or extract the existing baseline fixture carefully. If helper extraction is needed, it should stay under `backend/tests/` unless a separate implementation phase explicitly approves production-code changes.

## 6. Non-Negotiable Boundaries

- no `workflow.py` changes
- no additional Gemini wiring
- no live Gemini
- no API keys
- no `ForecastState` mutation
- no `agent_outputs` writes
- no `Signal`/`HorizonForecast`/`FusionResult` creation
- no `evidence_analyst` route
- no dirty backup topology
- no `ReportWriter` trusted input changes
- no bypass of `QuantifierV2`, `CriticV2`, `Governor`, `SchemaValidator`, `EvidenceDeduper`, `IndependenceAnalyzer`, `Librarian`, or `ArbitrationPolicy`

## 7. Acceptance Criteria

Phase 4K-EQ-B may be considered complete only if:

- tests prove `gemini_graph_noop_node` preserves protected state
- tests prove route remains `v2_join_node -> gemini_assist_noop -> schema_validator_node`
- tests prove `schema_validator_node` remains downstream gate
- tests prove no Gemini keys appear in disabled state
- tests prove no Gemini `agent_outputs` appear
- tests prove canonical baseline/output equivalence for deterministic fixtures
- tests prove nondeterministic fields are excluded only through approved canonicalization
- tests prove no live/client/key/import path is used
- all existing Gemini safety tests pass

## 8. Recommended Next Implementation Stage

Recommended next stage:

```text
Phase 4K-EQ-B — Implement Disabled Output Equivalence Tests
```

This next stage must be test-only, offline, mocked, and must not modify `workflow.py`.

It should add only tests and, if needed, test-only helper extraction under `backend/tests/`. It must not add live Gemini execution, API keys, new workflow imports, new workflow nodes, new workflow edges, production state writes, or production artifact writes.
