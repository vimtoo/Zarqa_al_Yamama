# TheSeer Manifest — 2026-05-13 to 2026-05-17

Date: 2026-05-17  
Purpose: historical progress manifest and handoff record for Gemini Deep Research work since 2026-05-13.  
Scope: documentation-only record reconstructed from local repository files, docs, tests, git status, and local artifact metadata. No source code, tests, environment files, package files, API keys, live Gemini calls, internet calls, file moves, file deletes, or production behavior changes were intentionally made for this manifest.

## 1. Executive Summary

Since 2026-05-13, TheSeer moved from V2 sovereign-source and fail-closed hardening into a large Gemini Deep Research integration effort. The strategic direction was to treat Gemini Deep Research as a controlled research sidecar, shadow runner, and later review-only capability while preserving TheSeer's deterministic V2 forecasting spine.

The repository now contains Gemini phases from Phase 1 through Phase 4Z-D. Phase 1-3C implement the approved shadow-sidecar path: client wrapper, normalizer, comparator, runner, and evaluation policy. Later Phase 4 work adds planning, disabled assist governance, audit models, no-op graph adapter, disabled workflow wiring, mock review mode, live-review harnesses, approval packages, API-key/header validation, and local live-attempt artifacts.

Current conservative state:

- Phase 3C is the cleanest verified policy baseline.
- Phase 2, 3A, 3B, and 3C targeted tests pass.
- Phase 1 exists but its original client test file now has two failures caused by later API-key validation rejecting the old `"fake-key"` test fixture.
- Later Phase 4+ safety and governance suites mostly pass locally, but these files are untracked and require human review before acceptance.
- `workflow.py` contains Phase 4K disabled/no-op Gemini wiring. It is tested as inert, but it is still a production graph topology change.
- Local live-review artifacts show prior live attempts, including one completed but quarantined Phase 4Z-D run.
- Do not add or use `GEMINI_API_KEY` until phase alignment is complete, tests are reconciled, and a new controlled non-production live run is explicitly approved.

## 2. Core Architectural Doctrine

The durable doctrine for Gemini Deep Research inside TheSeer is:

- Gemini may gather, search, summarize, compare, and propose evidence.
- Gemini must not replace deterministic probability fusion.
- Gemini must not bypass `SchemaValidator`.
- Gemini must not bypass `Governor`.
- Gemini must not bypass `QuantifierV2`.
- Gemini must not bypass `CriticV2`.
- Gemini must not bypass `Librarian` or `ArbitrationPolicy`.
- Gemini must not write directly to production forecast state.
- Gemini must not write `agent_outputs` unless a future explicitly approved phase allows it.
- Gemini must remain disabled by default.
- Gemini output must remain review-only, shadow-only, or locally validated until governance approves otherwise.
- Gemini must not be treated as a source of final probabilities.
- Gemini must not create `Signal`, `HorizonForecast`, or `FusionResult`.

## 3. Protected Components

Protected components and why they remain protected:

- `workflow.py`: controls LangGraph topology, execution order, fan-in, graph edges, and final production behavior.
- `contracts.py`: defines authoritative Pydantic evidence, claim, signal, forecast, and fail-closed contracts.
- `state.py`: defines `ForecastState`, protected state keys, reducers, and downstream data shape.
- `QuantifierV2`: deterministic probability fusion engine; Gemini must not replace it or inject final probabilities.
- `CriticV2`: deterministic validation and critique gate; Gemini must remain subject to it.
- `Governor`: ethical, safety, PII, cultural-sensitivity, and attribution authority.
- `SchemaValidator`: validates contract shape and claim-evidence linkage.
- `Librarian`: governs retrieval and source policy.
- `ArbitrationPolicy`: enforces model/provider authority boundaries, including Gemini advisory/forbidden roles.
- `EvidenceDeduper`: canonicalizes, hashes, clusters, and deduplicates evidence.
- `IndependenceAnalyzer`: measures source independence; Gemini cannot self-certify independence.
- `ReportWriter`: writes final production report; shadow/review outputs must not silently enter trusted report content.
- `ForecastState`: production graph state; Gemini must not mutate it outside explicit approved wrappers.
- `agent_outputs`: production agent-output map; Gemini must not write here by default.
- `Signal`: forecast signal contract; Gemini sidecar must not create it.
- `HorizonForecast`: horizon forecast contract; Gemini sidecar must not create it.
- `FusionResult`: fused forecast output; Gemini sidecar must not create it.

## 4. Phase Timeline Since 2026-05-13

| Date | Phase | Purpose | Files Created/Modified | Tests | Status | Notes |
|---|---|---|---|---|---|---|
| 2026-05-13 | V3 fail-closed sovereign lens | Preserve epistemic integrity and avoid synthetic fallback claims | Manifest records `contracts.py`, analysts, validator, quantifier, report writer changes | Reported in prior manifest as fail-closed tests passing | Historical baseline | Pre-Gemini hardening context |
| 2026-05-15 | Gemini integration plan | Define Gemini as controlled sidecar, not replacement | `docs/gemini_deep_research_integration_plan.md` | Docs only | Present | Plan protects V2 spine |
| Unverified exact date | Phase 1 | Isolated Interactions API client wrapper | `client.py`, `models.py`, `prompts.py`, `storage.py`, README | `test_gemini_deep_research_client.py`: 7 passed, 2 failed now | Needs human review | Later key validation broke old fake-key assumptions |
| Unverified exact date | Phase 2 | Normalize raw Gemini results into `GeminiEvidencePack` | `normalizer.py` | 15 passed | Verified | Local only; no workflow integration |
| Unverified exact date | Phase 3A | Compare Gemini evidence packs with TheSeer outputs | `shadow_compare.py` | 20 passed | Verified | Shadow comparison only |
| Unverified exact date | Phase 3B | Workflow-independent shadow runner / CLI | `shadow_runner.py` | 20 passed | Verified | Mock/live sidecar runner outside graph |
| 2026-05-17 verified locally | Phase 3C | Repeat-run shadow evaluation policy | `evaluation_policy.py`, `docs/gemini_shadow_evaluation_policy.md` | 20 passed | Verified | Current cleanest trusted policy baseline |
| Unverified exact date | Phase 4 | Limited assist-mode trial plan | `docs/gemini_limited_assist_mode_trial_plan.md` | Docs only | Present; review required | Planning only |
| Unverified exact date | Phase 4B | Assist config, approval, rollback, audit models | `assist_config.py`, `assist_audit.py` | Included in 59 passed | Verified locally | Untracked; needs acceptance |
| Unverified exact date | Phase 4C | Isolated assist-node wrapper | `assist_node.py` | Included in 59 passed | Verified locally; review required | Outside graph by itself |
| Unverified exact date | Phase 4D | Disabled-defaults and safety tests | `test_gemini_assist_disabled_defaults.py`, `test_gemini_assist_integration_safety.py` | 50 passed | Verified locally | Mocked/no-live safety |
| Unverified exact date | Phase 4E | Graph wiring disabled-flag plan | `docs/gemini_graph_wiring_disabled_flag_plan.md` | Docs only | Present | Plan recommended no workflow modification yet |
| Unverified exact date | Phase 4F | Isolated no-op graph adapter | `graph_adapter.py` | Included in 111 passed | Verified locally | Adapter no-op by default |
| Unverified exact date | Phase 4G | Byte-for-byte non-interference plan | `docs/gemini_byte_for_byte_non_interference_test_plan.md` | Docs only | Present | Planning only |
| Unverified exact date | Phase 4H | Canonical serialization and fixture utilities | `gemini_non_interference_utils.py` | Included in 111 passed | Verified locally | Test-only |
| Unverified exact date | Phase 4I | Workflow-shaped baseline fixture tests | `test_gemini_workflow_baseline_fixture.py` | Included in 111 passed | Verified locally | Fixture-based baseline |
| Unverified exact date | Phase 4J | Disabled graph wiring implementation plan | `docs/gemini_disabled_graph_wiring_implementation_plan.md` | Docs only | Present | Plan says future 4K only by approval |
| Unverified exact date | Phase 4K | Disabled/no-op workflow wiring | `workflow.py`, `graph_adapter.py`, disabled wiring tests | Included in 84 passed | Needs human review | `workflow.py` now has Gemini no-op node |
| Unverified exact date | Phase 4L | Disabled graph regression | disabled graph regression tests | Included in 84 passed | Verified locally; review required | Proves no-op behavior locally |
| Unverified exact date | Phase 4M-4S | Decision plans and live-review planning | `docs/gemini_phase4m_*` through `docs/gemini_phase4s_*` | Mostly docs | Present; review required | Governance path toward live review |
| Unverified exact date | Phase 4T | Non-production live-review harness | `live_review_runner.py` and tests | 73 passed for live-review runner group | Verified locally; review required | Live-capable only with explicit flags/key |
| Unverified exact date | Phase 4U-4W | Operator rehearsal, dry-run artifacts, human review docs | multiple `docs/gemini_phase4u/v/w_*` and tests | 61 passed and 63 passed groups | Verified locally; review required | No automatic live execution |
| Unverified exact date | Phase 4X-4Y | One-run approval and go/no-go packages | approval/command/preflight docs and tests | Included in 63 passed and 39 passed groups | Verified locally; review required | Approval package only |
| 2026-05-16 artifact dates | Phase 4Z / 4Z-A | First live attempt and investigation | local artifacts plus investigation docs | 36 passed group | Needs human review | First attempt live_attempted true, provider disabled |
| 2026-05-16 artifact dates | Phase 4Z-B | Corrected second attempt | docs and local artifacts | 64 passed group | Needs human review | Second attempt live_attempted true, provider failed |
| Unverified exact date | Phase 4Z-C | API-key/header validation | `key_validation.py`, client validation changes, docs/tests | Included in 392 passed group | Verified locally; review required | Explains current Phase 1 test drift |
| 2026-05-16 artifact dates | Phase 4Z-D | Validated third-attempt package and local completed run artifact | docs and `data/research/gemini_live_review_trials/phase4zd_third_attempt_001` | Included in 392 passed group | Needs human review | Third attempt completed but quarantined |

## 5. Files Created Since 2026-05-13

The following lists are reconstructed from local filesystem evidence. Because the Gemini tree is untracked, exact creation dates are not independently verified unless stated in docs or artifact metadata.

### Gemini integration package

- `backend/app/integrations/gemini_deep_research/README.md`
- `backend/app/integrations/gemini_deep_research/__init__.py`
- `backend/app/integrations/gemini_deep_research/client.py`
- `backend/app/integrations/gemini_deep_research/models.py`
- `backend/app/integrations/gemini_deep_research/prompts.py`
- `backend/app/integrations/gemini_deep_research/storage.py`
- `backend/app/integrations/gemini_deep_research/normalizer.py`
- `backend/app/integrations/gemini_deep_research/shadow_compare.py`
- `backend/app/integrations/gemini_deep_research/shadow_runner.py`
- `backend/app/integrations/gemini_deep_research/evaluation_policy.py`
- `backend/app/integrations/gemini_deep_research/assist_config.py`
- `backend/app/integrations/gemini_deep_research/assist_audit.py`
- `backend/app/integrations/gemini_deep_research/assist_node.py`
- `backend/app/integrations/gemini_deep_research/graph_adapter.py`
- `backend/app/integrations/gemini_deep_research/live_review_runner.py`
- `backend/app/integrations/gemini_deep_research/key_validation.py`

### Tests

- `backend/tests/test_gemini_deep_research_client.py`
- `backend/tests/test_gemini_evidence_normalizer.py`
- `backend/tests/test_gemini_shadow_compare.py`
- `backend/tests/test_gemini_shadow_runner.py`
- `backend/tests/test_gemini_evaluation_policy.py`
- `backend/tests/test_gemini_assist_config.py`
- `backend/tests/test_gemini_assist_audit.py`
- `backend/tests/test_gemini_assist_node.py`
- `backend/tests/test_gemini_assist_disabled_defaults.py`
- `backend/tests/test_gemini_assist_integration_safety.py`
- `backend/tests/gemini_non_interference_utils.py`
- `backend/tests/test_gemini_non_interference_utils.py`
- `backend/tests/test_gemini_graph_adapter.py`
- `backend/tests/test_gemini_workflow_baseline_fixture.py`
- `backend/tests/test_gemini_disabled_workflow_wiring.py`
- `backend/tests/test_gemini_disabled_graph_regression.py`
- `backend/tests/test_gemini_disabled_graph_no_call_no_write.py`
- `backend/tests/test_gemini_disabled_graph_barrier_safety.py`
- `backend/tests/test_gemini_live_review_runner_preflight.py`
- `backend/tests/test_gemini_live_review_runner_cli_safety.py`
- `backend/tests/test_gemini_live_review_runner_audit_artifacts.py`
- `backend/tests/test_gemini_live_review_runner_no_production_mutation.py`
- `backend/tests/test_gemini_live_workflow_baseline_capture.py`
- `backend/tests/test_gemini_live_workflow_downstream_snapshots.py`
- `backend/tests/test_gemini_live_workflow_no_call_no_write.py`
- `backend/tests/test_gemini_review_mode_mock_path.py`
- `backend/tests/test_gemini_review_mode_no_live_calls.py`
- `backend/tests/test_gemini_review_mode_multi_domain.py`
- `backend/tests/test_gemini_review_mode_audit_review.py`
- `backend/tests/test_gemini_review_mode_quarantine_matrix.py`
- `backend/tests/test_gemini_review_mode_state_safety.py`
- `backend/tests/test_gemini_phase4u_cli_examples_safety.py`
- `backend/tests/test_gemini_phase4u_live_governance_docs.py`
- `backend/tests/test_gemini_phase4u_operator_runbook_safety.py`
- `backend/tests/test_gemini_phase4v_dry_run_artifact_capture.py`
- `backend/tests/test_gemini_phase4v_evidence_documentation.py`
- `backend/tests/test_gemini_phase4v_no_live_execution.py`
- `backend/tests/test_gemini_phase4w_artifact_review_checklist.py`
- `backend/tests/test_gemini_phase4w_human_review_docs.py`
- `backend/tests/test_gemini_phase4w_no_live_authorization.py`
- `backend/tests/test_gemini_phase4w_review_decision_template_safety.py`
- `backend/tests/test_gemini_phase4x_api_key_rollback_controls.py`
- `backend/tests/test_gemini_phase4x_approval_outcome_safety.py`
- `backend/tests/test_gemini_phase4x_approval_package_docs.py`
- `backend/tests/test_gemini_phase4x_command_packet_safety.py`
- `backend/tests/test_gemini_phase4x_no_live_execution.py`
- `backend/tests/test_gemini_phase4y_decision_outcome_safety.py`
- `backend/tests/test_gemini_phase4y_execution_readiness_packet.py`
- `backend/tests/test_gemini_phase4y_final_preflight_checklist.py`
- `backend/tests/test_gemini_phase4y_go_no_go_docs.py`
- `backend/tests/test_gemini_phase4y_no_live_execution.py`
- `backend/tests/test_gemini_phase4z_command_handoff_safety.py`
- `backend/tests/test_gemini_phase4z_execution_handoff_docs.py`
- `backend/tests/test_gemini_phase4z_incident_stop_plan.py`
- `backend/tests/test_gemini_phase4z_no_automatic_execution.py`
- `backend/tests/test_gemini_phase4z_post_run_review_checklist.py`
- `backend/tests/test_gemini_phase4za_failure_investigation_docs.py`
- `backend/tests/test_gemini_phase4za_live_runner_enablement_contract.py`
- `backend/tests/test_gemini_phase4za_no_live_retry.py`
- `backend/tests/test_gemini_phase4za_provider_enablement_audit.py`
- `backend/tests/test_gemini_phase4zb_corrected_approval_package.py`
- `backend/tests/test_gemini_phase4zb_go_no_go_record.py`
- `backend/tests/test_gemini_phase4zb_mock_enablement_bridge.py`
- `backend/tests/test_gemini_phase4zb_no_live_execution.py`
- `backend/tests/test_gemini_phase4zb_provider_enablement_contract.py`
- `backend/tests/test_gemini_phase4zb_second_attempt_command_packet.py`
- `backend/tests/test_gemini_phase4zc_api_key_header_validation.py`
- `backend/tests/test_gemini_phase4zc_client_key_validation_contract.py`
- `backend/tests/test_gemini_phase4zc_failed_second_attempt_docs.py`
- `backend/tests/test_gemini_phase4zc_key_validation_unit.py`
- `backend/tests/test_gemini_phase4zc_no_live_retry.py`
- `backend/tests/test_gemini_phase4zd_go_no_go_record.py`
- `backend/tests/test_gemini_phase4zd_no_live_execution.py`
- `backend/tests/test_gemini_phase4zd_post_run_review_template.py`
- `backend/tests/test_gemini_phase4zd_third_attempt_command_packet.py`
- `backend/tests/test_gemini_phase4zd_validated_approval_package.py`
- `backend/tests/test_gemini_phase4zd_validation_evidence_record.py`
- `backend/tests/test_gemini_phase4zd_validation_gate_contract.py`

### Documentation

- `docs/gemini_deep_research_integration_plan.md`
- `docs/gemini_shadow_evaluation_policy.md`
- `docs/gemini_limited_assist_mode_trial_plan.md`
- `docs/gemini_graph_wiring_disabled_flag_plan.md`
- `docs/gemini_byte_for_byte_non_interference_test_plan.md`
- `docs/gemini_disabled_graph_wiring_implementation_plan.md`
- `docs/gemini_phase4m_decision_and_live_baseline_plan.md`
- `docs/gemini_phase4o_review_mode_decision_plan.md`
- `docs/gemini_phase4r_human_review_and_governance_decision.md`
- `docs/gemini_phase4s_limited_live_review_experiment_plan.md`
- `docs/gemini_phase4u_live_review_governance_checklist.md`
- `docs/gemini_phase4u_operator_rehearsal_runbook.md`
- `docs/gemini_phase4v_dry_run_rehearsal_evidence.md`
- `docs/gemini_phase4w_artifact_review_checklist.md`
- `docs/gemini_phase4w_human_review_decision_record.md`
- `docs/gemini_phase4x_api_key_and_rollback_controls.md`
- `docs/gemini_phase4x_live_run_command_packet.md`
- `docs/gemini_phase4x_one_run_live_approval_package.md`
- `docs/gemini_phase4y_execution_readiness_packet.md`
- `docs/gemini_phase4y_final_preflight_checklist.md`
- `docs/gemini_phase4y_go_no_go_decision_record.md`
- `docs/gemini_phase4z_execution_incident_stop_plan.md`
- `docs/gemini_phase4z_one_run_execution_handoff.md`
- `docs/gemini_phase4z_post_run_review_checklist.md`
- `docs/gemini_phase4za_live_attempt_failure_investigation.md`
- `docs/gemini_phase4za_next_attempt_requirements.md`
- `docs/gemini_phase4za_provider_enablement_audit.md`
- `docs/gemini_phase4zb_corrected_second_attempt_approval_package.md`
- `docs/gemini_phase4zb_provider_enablement_contract.md`
- `docs/gemini_phase4zb_second_attempt_command_packet.md`
- `docs/gemini_phase4zb_second_attempt_go_no_go_record.md`
- `docs/gemini_phase4zb_second_attempt_post_run_review.md`
- `docs/gemini_phase4zc_api_key_header_validation.md`
- `docs/gemini_phase4zc_failed_second_attempt_investigation.md`
- `docs/gemini_phase4zc_future_attempt_requirements.md`
- `docs/gemini_phase4zd_post_run_review_template.md`
- `docs/gemini_phase4zd_third_attempt_command_packet.md`
- `docs/gemini_phase4zd_third_attempt_go_no_go_record.md`
- `docs/gemini_phase4zd_validated_third_attempt_approval_package.md`
- `docs/gemini_phase4zd_validation_evidence_record.md`
- `docs/gemini_phase_alignment_audit.md`

### Governance / approval / runbook files

- Phase 4U operator rehearsal and governance docs.
- Phase 4W human-review decision docs.
- Phase 4X one-run approval package and command packet.
- Phase 4Y go/no-go and final preflight docs.
- Phase 4Z incident stop, handoff, and post-run checklist docs.
- Phase 4Z-A/B/C/D investigation, validation, approval, command, and post-run docs.
- Local artifact directories under `data/research/gemini_live_review_trials/`.

## 6. Test History

Known test commands and results from this audit:

- `pytest backend/tests/test_gemini_deep_research_client.py -q` -> 7 passed, 2 failed.
- `pytest backend/tests/test_gemini_evidence_normalizer.py -q` -> 15 passed.
- `pytest backend/tests/test_gemini_shadow_compare.py -q` -> 20 passed.
- `pytest backend/tests/test_gemini_shadow_runner.py -q` -> 20 passed.
- `pytest backend/tests/test_gemini_evaluation_policy.py -q` -> 20 passed.
- Assist config/audit/node group -> 59 passed.
- Assist disabled/default and integration-safety group -> 50 passed.
- Graph adapter/non-interference/baseline group -> 111 passed.
- Disabled workflow/graph regression/no-call/barrier group -> 84 passed.
- Live-review runner dry-run/safety group -> 73 passed.
- Review-mode mock/no-live/quarantine/state group -> 133 passed.
- Phase 4U-4V docs/dry-run group -> 61 passed.
- Phase 4W-4X docs/approval/no-live group -> 63 passed.
- Phase 4Y group -> 39 passed.
- Phase 4Z group -> 36 passed.
- Phase 4Z-A/B group -> 64 passed.
- Phase 4Z-C/D group -> 392 passed.
- Live workflow baseline/downstream/no-call group -> 70 passed, 1 warning.

Reported in docs but not independently re-run as exact historical bundles:

- Phase 4Z-C targeted suite: 99 passed.
- Phase 4Z-B + 4Z-A regression suite: 64 passed.
- Phase 4Z-D validation docs report 163 combined validation/regression passes.

Unverified / requires human review:

- Any exact historical command/result not captured in this audit's terminal output.
- Any live Gemini attempt outcome beyond local redacted artifacts and docs.

## 7. Current Verified State

Verified now:

- Phase 2 normalizer tests pass.
- Phase 3A comparator tests pass.
- Phase 3B shadow runner tests pass.
- Phase 3C evaluation policy tests pass.
- Large later-phase mocked/dry-run safety suites pass locally.

Not clean:

- Phase 1 client tests have 2 failures due later key-validation drift.
- Gemini integration package, Gemini tests, and Gemini docs are untracked.
- `workflow.py` is modified and contains Gemini disabled/no-op wiring.
- Protected components are dirty.
- Local live-review artifacts exist.

Production behavior:

- The inspected no-op wiring is tested as inert, but `workflow.py` topology is changed.
- Production behavior cannot be declared unchanged until the workflow diff is accepted or reverted on a clean branch.

Live Gemini:

- Not enabled by this audit.
- No live Gemini call was made by this audit.
- Local artifacts show prior non-production live attempts, including one completed but quarantined run.

API key:

- Do not add now.

## 8. API Key and Live Gemini History

API key became relevant only after moving beyond mock/shadow phases toward non-production live review. Phase 1-3C mock tests do not require `GEMINI_API_KEY`.

Relevant flags and controls:

- `SEER_USE_GEMINI_DEEP_RESEARCH` defaults to disabled.
- `SEER_GEMINI_MODE` defaults to `shadow`.
- `SEER_GEMINI_TIMEOUT_SECONDS` controls timeout behavior.
- `GEMINI_API_KEY` is required only for real live provider calls.
- `--allow-live-gemini` is necessary but not sufficient for the live-review runner.

Key validation exists:

- `key_validation.py` validates missing, placeholder, malformed, whitespace, control-character, too-short, bracketed, and illegal HTTP-header values before live header construction.
- `client.py` calls key validation before `_post_interaction()` and `_get_interaction()` on live paths.
- Errors are sanitized and must not include the raw key.

Local live-attempt evidence:

- Phase 4Z first attempt: `live_attempted: true`, `live_completed: false`, provider status `disabled`, no raw report.
- Phase 4Z-B second attempt: `live_attempted: true`, `live_completed: false`, provider status `failed`, no raw report; docs cite illegal header value.
- Phase 4Z-D third attempt: `live_attempted: true`, `live_completed: true`, provider status `completed`, status `quarantined`; warnings include secret-like content redaction, missing publication dates, unsupported claim skipped, inferred time horizon, and missing cost.

Standing rule:

Do not add or use `GEMINI_API_KEY` until repository phase alignment is complete, tests are verified, protected-component diffs are reviewed, and a controlled non-production live run is explicitly approved.

## 9. Safety Boundaries Preserved

Observed or documented boundaries:

- No production graph integration existed through Phase 4J planning.
- Phase 4K does add graph wiring, but tests characterize it as disabled/no-op.
- No agent replacement is approved.
- No direct forecast-state mutation by Gemini sidecar is approved.
- No production `agent_outputs` write by Gemini is approved.
- No `Signal`, `HorizonForecast`, or `FusionResult` creation by the Gemini sidecar is approved.
- Mocked tests do not call Gemini or the internet.
- Dry-run tests are designed to avoid live external APIs.
- Live mode requires explicit flags and key.
- Local live-review artifacts are stored under `data/research/gemini_live_review_trials/`, not production report paths.
- Live-review artifacts use redacted raw-result files.

## 10. Known Risks and Open Questions

- Later-phase drift: repository contains Phase 4Z-D while the immediate approved implementation task was Phase 3C.
- Dirty/untracked files: Gemini package/docs/tests are untracked, and many protected components are dirty.
- Stale README risk: early README text says no workflow integration, while later sections document Phase 4K no-op wiring.
- Duplicate or overlapping documents: many Phase 4X/Y/Z approval, command, preflight, and post-run docs exist.
- Workflow no-op wiring exists and must be accepted or isolated.
- Live-attempt artifacts exist and include a completed but quarantined Phase 4Z-D result.
- Branch cleanliness is poor; accepting later phases directly from this checkout is risky.
- Source of later phases is unclear from git because they are untracked.
- Human review must decide whether to accept, freeze, roll back, or isolate later phases.
- Phase 1 tests need reconciliation with Phase 4Z-C key validation.
- Some tests may write local artifacts under project `data/research`; future safe test runs should confirm artifact paths before execution.

## 11. Final-Stage Backlog

Deferred until stable and functional code:

- project rename / rebrand
- cleaning old files
- removing duplicate legacy files
- archiving old code
- redesigning or replacing the app interface
- optional CLI/TUI/operator cockpit
- possible future desktop app
- final codebase cleanup after tests and live-safe execution

These are explicitly not current tasks. Do not rename, delete, archive, or redesign now.

## 12. Recommended Next Step

Immediate next step:

- Complete human review of `docs/gemini_phase_alignment_audit.md`.
- Decide Path A, B, or C.
- Recommended decision: Path C - create a clean branch from the last trusted phase and reapply later phases selectively.
- Do not add API key until alignment is complete.
- Do not perform rename or cleanup now.
- Do not run another live Gemini attempt now.
- Do not accept Phase 4K workflow wiring until explicitly approved after graph-diff review.

Path definitions:

- Path A: roll back or ignore later phases and resume cleanly from Phase 3C.
- Path B: accept later phases as valid only after full safe test verification and protected-component review.
- Path C: create a clean branch from last trusted phase and reapply later phases selectively.

Recommended path: Path C.

## 13. Human Review Checklist

- [ ] Review phase-alignment audit.
- [ ] Confirm trusted phase baseline.
- [ ] Decide Path A / B / C.
- [ ] Verify all safe tests.
- [ ] Confirm whether `workflow.py` Gemini wiring exists.
- [ ] Confirm no protected component mutation beyond accepted diffs.
- [ ] Confirm whether API key can be added.
- [ ] Approve or block next live shadow/review run.
- [ ] Defer rename and cleanup to final stage.
