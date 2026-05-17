# Gemini Deep Research Phase Alignment Audit

Date: 2026-05-17  
Scope: read-only repository audit plus this documentation artifact. No source code, workflow code, environment files, package files, tests, API keys, live Gemini calls, internet calls, file moves, file deletes, or production behavior changes were intentionally made for this audit.

## 1. Executive Summary

Current verified phase: Phase 3C is functionally verified by its targeted test suite, and Phase 2, Phase 3A, and Phase 3B targeted suites also pass. Phase 1 exists, but its current targeted client test file is not clean: 7 tests pass and 2 fail because later Phase 4Z-C API-key/header validation rejects the old `"fake-key"` fixture before the mocked interaction path.

Later phases found: repository files and docs exist far beyond Phase 3C, through Phase 4Z-D. These include assist config/audit models, an isolated assist wrapper, no-op graph adapter, disabled/no-op workflow wiring, mock review-mode paths, live-review runner, API-key/header validation, approval packages, failed-attempt investigations, and local live-review artifacts.

Later phases are not automatically trusted. Many later safety suites pass locally, but the Gemini integration tree, docs, and tests are untracked in git, `workflow.py` is dirty and contains Gemini no-op wiring, protected components are dirty, and Phase 1 tests have drifted. This requires a branch/freeze decision before accepting later phases as authoritative.

`workflow.py` is modified and contains Gemini wiring. It imports `gemini_graph_noop_node`, registers `gemini_assist_noop`, routes `v2_join_node` `"proceed"` through that no-op node, and then edges to `evidence_analyst`. Local tests classify this as disabled/no-op wiring, but it is still a production graph topology change and must be human-reviewed before being accepted.

No evidence from the inspected Gemini modules or tests showed a direct Gemini write to production `agent_outputs`, `ForecastState`, `Signal`, `HorizonForecast`, or `FusionResult`. However, protected components are dirty and untracked later-phase artifacts exist, so production behavior cannot be declared clean without a dedicated diff review.

API key readiness: **NO: phase alignment incomplete**. Do not add `GEMINI_API_KEY` now. Mock and dry-run tests do not need it. A future non-production live run should require a new explicit approval after this alignment issue is resolved.

Recommended next step: **Path C - create a clean branch from the last trusted baseline and reapply/accept later phases selectively after human review**, using this audit as the routing document.

## 2. Repository Status

Read-only commands inspected:

- `git status --short`
- `git diff --stat`
- `git diff --name-only`
- `git ls-files backend/app/integrations/gemini_deep_research docs backend/tests`

Git status summary:

- The worktree is heavily dirty.
- `git diff --stat` reports 61 tracked files changed with 12002 insertions and 1863 deletions.
- `backend/app/integrations/` is untracked, which means the Gemini integration package is not currently tracked by git in this checkout.
- `docs/` is untracked, which means Gemini phase docs are not currently tracked by git.
- All Gemini-related test files under `backend/tests/test_gemini_*.py` are untracked.
- `data/research/gemini_live_review_trials/` is untracked and contains local live-review artifacts.

Dirty protected-component files:

- `backend/app/workflow.py`
- `backend/app/graph/contracts.py`
- `backend/app/graph/state.py`
- `backend/app/agents/context_interpreter.py`
- `backend/app/agents/critic.py`
- `backend/app/agents/evidence_analyst.py`
- `backend/app/agents/governor.py`
- `backend/app/agents/quantifier_v2.py`
- `backend/app/agents/report_writer.py`
- `backend/app/agents/schema_validator.py`
- `backend/app/agents/think_tank_analyst.py`
- `backend/app/agents/walled_garden_analyst.py`
- `backend/app/llm/client.py`
- `backend/app/llm/antigravity.py`
- `backend/requirements.txt`
- `.env.example`
- `backend/.env.example`
- `.gitignore`

Gemini-relevant untracked areas:

- `backend/app/integrations/gemini_deep_research/`
- `backend/tests/test_gemini_*.py`
- `backend/tests/gemini_non_interference_utils.py`
- `docs/gemini_*.md`
- `data/research/gemini_live_review_trials/`

Tracked file check:

- `git ls-files backend/app/integrations/gemini_deep_research docs backend/tests` returned only pre-existing non-Gemini backend tests and golden-run files. It did not list the Gemini integration package or Gemini docs/tests, confirming they are untracked in this checkout.

## 3. Phase Inventory Table

| Phase | Purpose | Key Files Present | Tests Present | Tests Passed | Workflow Impact | Risk | Status |
|---|---|---:|---:|---|---|---|---|
| Phase 1 | Gemini Deep Research client wrapper | Yes | Yes | 7 passed, 2 failed | None by package; client can call live only when enabled | MEDIUM | Needs human review |
| Phase 2 | EvidencePack normalizer | Yes | Yes | 15 passed | None | LOW | Verified |
| Phase 3A | Shadow comparison engine | Yes | Yes | 20 passed | None | LOW | Verified |
| Phase 3B | Workflow-independent shadow runner / CLI | Yes | Yes | 20 passed | None | LOW | Verified |
| Phase 3C | Shadow evaluation policy | Yes | Yes | 20 passed | None | LOW | Verified |
| Phase 4 | Limited assist-mode trial plan | Yes | Docs only | Not separately run | None | LOW | Present; doc-reviewed |
| Phase 4B | Assist config and audit models | Yes | Yes | Included in 59 passed | None | LOW | Verified locally |
| Phase 4C | Isolated assist-node wrapper | Yes | Yes | Included in 59 passed | None | MEDIUM | Verified locally; needs human review before acceptance |
| Phase 4D | Disabled-defaults and safety tests | Yes | Yes | 50 passed | None | LOW | Verified locally |
| Phase 4E | Graph wiring disabled-flag plan | Yes | Docs only | Not separately run | None | LOW | Present; doc-reviewed |
| Phase 4F | Isolated no-op graph adapter | Yes | Yes | Included in 111 passed | None by adapter | LOW | Verified locally |
| Phase 4G | Byte-for-byte non-interference test plan | Yes | Docs only | Not separately run | None | LOW | Present; doc-reviewed |
| Phase 4H | Canonical serialization/baseline utilities | Yes | Yes | Included in 111 passed | None | LOW | Verified locally |
| Phase 4I | Workflow-shaped baseline fixture tests | Yes | Yes | Included in 111 passed | None | LOW | Verified locally |
| Phase 4J | Disabled graph wiring implementation plan | Yes | Docs only | Not separately run | None | LOW | Present; doc-reviewed |
| Phase 4K | Disabled/no-op workflow wiring | Yes | Yes | Included in 84 passed | Disabled/no-op graph topology change | HIGH | Needs human review |
| Phase 4L | Disabled graph regression | Yes | Yes | Included in 84 passed | Tests no-op wiring | MEDIUM | Verified locally; needs human review |
| Phase 4M+ | Review-mode, live-review, approval, validation, and attempt docs | Yes | Yes | Later suites passed locally | Mixed: review-only/dry-run plus local live artifacts | HIGH | Present but requires review |
| Phase 4Z-D | Validated third-attempt approval and local live artifact history | Yes | Yes | 392 passed for 4Z-C/4Z-D suite group | Non-production live-review artifacts exist | HIGH | Needs human review |

## 4. Detailed Phase Findings

### Phase 1: Gemini Deep Research client wrapper

**Expected files:**  
- `backend/app/integrations/gemini_deep_research/client.py`
- `backend/app/integrations/gemini_deep_research/models.py`
- `backend/app/integrations/gemini_deep_research/prompts.py`
- `backend/app/integrations/gemini_deep_research/storage.py`
- `backend/app/integrations/gemini_deep_research/README.md`
- `backend/tests/test_gemini_deep_research_client.py`

**Files found:**  
All expected files were found under the untracked Gemini integration package and untracked tests.

**Tests found:**  
- `backend/tests/test_gemini_deep_research_client.py`

**Tests run:**  
- `pytest backend/tests/test_gemini_deep_research_client.py -q` -> 7 passed, 2 failed.

**Production impact:**  
The client package itself is isolated. It can call Gemini only when not in mock mode and `SEER_USE_GEMINI_DEEP_RESEARCH` is truthy with a valid key.

**Protected component impact:**  
None from this package file. It does not import `workflow.py` or production graph contracts for state mutation.

**Risk:**  
MEDIUM

**Status:**  
Needs human review.

**Notes:**  
The two failures are alignment drift, not live-call evidence. Later `key_validation.py` rejects `"fake-key"` as `too_short`, so tests expecting timeout/failed interaction behavior never reach their mocked interaction methods.

### Phase 2: EvidencePack normalizer

**Expected files:**  
- `backend/app/integrations/gemini_deep_research/normalizer.py`
- `backend/tests/test_gemini_evidence_normalizer.py`

**Files found:**  
Both expected files were found.

**Tests found:**  
- `backend/tests/test_gemini_evidence_normalizer.py`

**Tests run:**  
- `pytest backend/tests/test_gemini_evidence_normalizer.py -q` -> 15 passed.

**Production impact:**  
None.

**Protected component impact:**  
No production state mutation observed.

**Risk:**  
LOW

**Status:**  
Verified.

**Notes:**  
Normalizer remains local and converts raw results into local Gemini models rather than forecast contracts.

### Phase 3A: Shadow comparison engine

**Expected files:**  
- `backend/app/integrations/gemini_deep_research/shadow_compare.py`
- `backend/tests/test_gemini_shadow_compare.py`

**Files found:**  
Both expected files were found.

**Tests found:**  
- `backend/tests/test_gemini_shadow_compare.py`

**Tests run:**  
- `pytest backend/tests/test_gemini_shadow_compare.py -q` -> 20 passed.

**Production impact:**  
None.

**Protected component impact:**  
None observed.

**Risk:**  
LOW

**Status:**  
Verified.

**Notes:**  
Comparator produces shadow comparison artifacts and recommendations outside production graph state.

### Phase 3B: Workflow-independent shadow runner / CLI

**Expected files:**  
- `backend/app/integrations/gemini_deep_research/shadow_runner.py`
- `backend/tests/test_gemini_shadow_runner.py`

**Files found:**  
Both expected files were found.

**Tests found:**  
- `backend/tests/test_gemini_shadow_runner.py`

**Tests run:**  
- `pytest backend/tests/test_gemini_shadow_runner.py -q` -> 20 passed.

**Production impact:**  
None.

**Protected component impact:**  
None observed.

**Risk:**  
LOW

**Status:**  
Verified.

**Notes:**  
The runner is workflow-independent and supports mock mode. Live mode is guarded by environment flags.

### Phase 3C: Shadow evaluation policy

**Expected files:**  
- `backend/app/integrations/gemini_deep_research/evaluation_policy.py`
- `backend/tests/test_gemini_evaluation_policy.py`
- `docs/gemini_shadow_evaluation_policy.md`

**Files found:**  
All expected files were found.

**Tests found:**  
- `backend/tests/test_gemini_evaluation_policy.py`

**Tests run:**  
- `pytest backend/tests/test_gemini_evaluation_policy.py -q` -> 20 passed.

**Production impact:**  
None.

**Protected component impact:**  
None observed.

**Risk:**  
LOW

**Status:**  
Verified.

**Notes:**  
Phase 3C is the cleanest currently verified decision-policy baseline. It does not authorize production integration or replacement.

### Phase 4: Limited assist-mode trial plan

**Expected files:**  
- `docs/gemini_limited_assist_mode_trial_plan.md`

**Files found:**  
Found.

**Tests found:**  
No direct tests required; planning document.

**Tests run:**  
Not separately run.

**Production impact:**  
None.

**Protected component impact:**  
None.

**Risk:**  
LOW

**Status:**  
Present but unverified as a governance artifact.

**Notes:**  
The plan correctly states that Phase 4 is planning only and requires Phase 3C readiness before assist mode.

### Phase 4B: Assist config and audit models

**Expected files:**  
- `backend/app/integrations/gemini_deep_research/assist_config.py`
- `backend/app/integrations/gemini_deep_research/assist_audit.py`
- `backend/tests/test_gemini_assist_config.py`
- `backend/tests/test_gemini_assist_audit.py`

**Files found:**  
All expected files were found.

**Tests found:**  
Both expected tests were found.

**Tests run:**  
- `pytest backend/tests/test_gemini_assist_config.py backend/tests/test_gemini_assist_audit.py backend/tests/test_gemini_assist_node.py -q` -> 59 passed.

**Production impact:**  
None by these models.

**Protected component impact:**  
None observed.

**Risk:**  
LOW

**Status:**  
Verified locally, but untracked.

**Notes:**  
Disabled-by-default and approval/rollback concepts are present.

### Phase 4C: Isolated assist-node wrapper

**Expected files:**  
- `backend/app/integrations/gemini_deep_research/assist_node.py`
- `backend/tests/test_gemini_assist_node.py`

**Files found:**  
Both expected files were found.

**Tests found:**  
Found.

**Tests run:**  
- Included in the 59-passed assist suite above.

**Production impact:**  
No workflow integration by this wrapper alone.

**Protected component impact:**  
No direct protected mutation observed in the local tests.

**Risk:**  
MEDIUM

**Status:**  
Verified locally; needs human review before acceptance.

**Notes:**  
The wrapper rehearses future behavior and can write audit artifacts when explicitly called. It should remain frozen until accepted.

### Phase 4D: Disabled-defaults and integration-safety tests

**Expected files:**  
- `backend/tests/test_gemini_assist_disabled_defaults.py`
- `backend/tests/test_gemini_assist_integration_safety.py`

**Files found:**  
Both files were found. The expected name `test_gemini_integration_safety.py` appears as `test_gemini_assist_integration_safety.py`.

**Tests found:**  
Found.

**Tests run:**  
- `pytest backend/tests/test_gemini_assist_disabled_defaults.py backend/tests/test_gemini_assist_integration_safety.py -q` -> 50 passed.

**Production impact:**  
None.

**Protected component impact:**  
None observed.

**Risk:**  
LOW

**Status:**  
Verified locally.

**Notes:**  
Tests assert disabled/default behavior and no-live/no-write boundaries.

### Phase 4E: Graph wiring disabled-flag plan

**Expected files:**  
- `docs/gemini_graph_wiring_disabled_flag_plan.md`

**Files found:**  
Found.

**Tests found:**  
Docs only.

**Tests run:**  
Not separately run.

**Production impact:**  
None as a plan.

**Protected component impact:**  
None.

**Risk:**  
LOW

**Status:**  
Present but unverified.

**Notes:**  
The plan said not to modify `workflow.py` yet. Current repository state has moved past this plan.

### Phase 4F: Isolated no-op graph adapter

**Expected files:**  
- `backend/app/integrations/gemini_deep_research/graph_adapter.py`
- `backend/tests/test_gemini_graph_adapter.py`

**Files found:**  
Both expected files were found.

**Tests found:**  
Found.

**Tests run:**  
- `pytest backend/tests/test_gemini_graph_adapter.py backend/tests/test_gemini_non_interference_utils.py backend/tests/test_gemini_workflow_baseline_fixture.py -q` -> 111 passed.

**Production impact:**  
None by adapter alone.

**Protected component impact:**  
The adapter defines protected keys and returns state unchanged by default.

**Risk:**  
LOW

**Status:**  
Verified locally.

**Notes:**  
The no-op adapter itself appears inert by default.

### Phase 4G: Byte-for-byte non-interference test plan

**Expected files:**  
- `docs/gemini_byte_for_byte_non_interference_test_plan.md`

**Files found:**  
Found.

**Tests found:**  
Docs only.

**Tests run:**  
Not separately run.

**Production impact:**  
None.

**Protected component impact:**  
None.

**Risk:**  
LOW

**Status:**  
Present but unverified.

**Notes:**  
Planning artifact only.

### Phase 4H: Canonical serialization and baseline fixture utilities

**Expected files:**  
- `backend/tests/gemini_non_interference_utils.py`

**Files found:**  
Found.

**Tests found:**  
- `backend/tests/test_gemini_non_interference_utils.py`

**Tests run:**  
- Included in the 111-passed graph/baseline suite.

**Production impact:**  
None.

**Protected component impact:**  
None.

**Risk:**  
LOW

**Status:**  
Verified locally.

**Notes:**  
Test-only utilities.

### Phase 4I: Workflow-shaped baseline fixture tests

**Expected files:**  
- `backend/tests/test_gemini_workflow_baseline_fixture.py`

**Files found:**  
Found.

**Tests found:**  
Found.

**Tests run:**  
- Included in the 111-passed graph/baseline suite.

**Production impact:**  
None.

**Protected component impact:**  
None in tests.

**Risk:**  
LOW

**Status:**  
Verified locally.

**Notes:**  
Fixture tests are not equivalent to full production runtime acceptance.

### Phase 4J: Disabled graph wiring implementation plan

**Expected files:**  
- `docs/gemini_disabled_graph_wiring_implementation_plan.md`

**Files found:**  
Found.

**Tests found:**  
Docs only.

**Tests run:**  
Not separately run.

**Production impact:**  
None as a plan.

**Protected component impact:**  
None.

**Risk:**  
LOW

**Status:**  
Present but unverified.

**Notes:**  
The plan describes future Phase 4K. Current repo already contains Phase 4K wiring.

### Phase 4K: Disabled/no-op workflow wiring

**Expected signs:**  
- `workflow.py` contains `gemini_assist_noop` or `GeminiGraphNoopAdapter` wiring.

**Files found:**  
- `backend/app/workflow.py` imports `gemini_graph_noop_node`.
- `workflow.add_node("gemini_assist_noop", gemini_graph_noop_node)` exists.
- V2 join `"proceed"` routes to `"gemini_assist_noop"`.
- `workflow.add_edge("gemini_assist_noop", "evidence_analyst")` exists.

**Tests found:**  
- `backend/tests/test_gemini_disabled_workflow_wiring.py`
- `backend/tests/test_gemini_disabled_graph_regression.py`
- `backend/tests/test_gemini_disabled_graph_no_call_no_write.py`
- `backend/tests/test_gemini_disabled_graph_barrier_safety.py`

**Tests run:**  
- `pytest backend/tests/test_gemini_disabled_workflow_wiring.py backend/tests/test_gemini_disabled_graph_regression.py backend/tests/test_gemini_disabled_graph_no_call_no_write.py backend/tests/test_gemini_disabled_graph_barrier_safety.py -q` -> 84 passed.

**Production impact:**  
Disabled/no-op wiring, but it is still a production graph topology change.

**Protected component impact:**  
`workflow.py` is modified. Tests assert no Gemini barrier-key addition and no Gemini agent output writes.

**Risk:**  
HIGH

**Status:**  
Needs human review.

**Notes:**  
Even no-op graph wiring changes LangGraph topology and must be explicitly accepted or isolated.

### Phase 4L: Disabled graph regression

**Expected files:**  
- `backend/tests/test_gemini_disabled_graph_regression.py`

**Files found:**  
Found.

**Tests found:**  
Found.

**Tests run:**  
- Included in the 84-passed disabled graph suite.

**Production impact:**  
Tests production graph no-op wiring.

**Protected component impact:**  
Indirectly inspects `workflow.py`.

**Risk:**  
MEDIUM

**Status:**  
Verified locally; needs human review because it depends on accepting Phase 4K.

**Notes:**  
Useful, but not a substitute for a clean branch review.

### Phase 4M and beyond: Decision plans, live review, approvals, validation, and attempt docs

**Expected files:**  
- `backend/app/integrations/gemini_deep_research/live_review_runner.py`
- `backend/app/integrations/gemini_deep_research/key_validation.py`
- `backend/tests/test_gemini_live_review_runner_*.py`
- `backend/tests/test_gemini_phase4*.py`
- `docs/gemini_phase4*.md`

**Files found:**  
All categories were found.

**Tests found:**  
Large suite of dry-run/static/mocked tests found.

**Tests run:**  
- `pytest backend/tests/test_gemini_live_review_runner_preflight.py backend/tests/test_gemini_live_review_runner_cli_safety.py backend/tests/test_gemini_live_review_runner_audit_artifacts.py backend/tests/test_gemini_live_review_runner_no_production_mutation.py -q` -> 73 passed.
- `pytest backend/tests/test_gemini_review_mode_mock_path.py backend/tests/test_gemini_review_mode_no_live_calls.py backend/tests/test_gemini_review_mode_multi_domain.py backend/tests/test_gemini_review_mode_audit_review.py backend/tests/test_gemini_review_mode_quarantine_matrix.py backend/tests/test_gemini_review_mode_state_safety.py -q` -> 133 passed.
- `pytest backend/tests/test_gemini_phase4u_cli_examples_safety.py backend/tests/test_gemini_phase4u_live_governance_docs.py backend/tests/test_gemini_phase4u_operator_runbook_safety.py backend/tests/test_gemini_phase4v_dry_run_artifact_capture.py backend/tests/test_gemini_phase4v_evidence_documentation.py backend/tests/test_gemini_phase4v_no_live_execution.py -q` -> 61 passed.
- `pytest backend/tests/test_gemini_phase4w_artifact_review_checklist.py backend/tests/test_gemini_phase4w_human_review_docs.py backend/tests/test_gemini_phase4w_no_live_authorization.py backend/tests/test_gemini_phase4w_review_decision_template_safety.py backend/tests/test_gemini_phase4x_api_key_rollback_controls.py backend/tests/test_gemini_phase4x_approval_outcome_safety.py backend/tests/test_gemini_phase4x_approval_package_docs.py backend/tests/test_gemini_phase4x_command_packet_safety.py backend/tests/test_gemini_phase4x_no_live_execution.py -q` -> 63 passed.
- `pytest backend/tests/test_gemini_phase4y_decision_outcome_safety.py backend/tests/test_gemini_phase4y_execution_readiness_packet.py backend/tests/test_gemini_phase4y_final_preflight_checklist.py backend/tests/test_gemini_phase4y_go_no_go_docs.py backend/tests/test_gemini_phase4y_no_live_execution.py -q` -> 39 passed.
- `pytest backend/tests/test_gemini_phase4z_command_handoff_safety.py backend/tests/test_gemini_phase4z_execution_handoff_docs.py backend/tests/test_gemini_phase4z_incident_stop_plan.py backend/tests/test_gemini_phase4z_no_automatic_execution.py backend/tests/test_gemini_phase4z_post_run_review_checklist.py -q` -> 36 passed.
- `pytest backend/tests/test_gemini_phase4za_failure_investigation_docs.py backend/tests/test_gemini_phase4za_live_runner_enablement_contract.py backend/tests/test_gemini_phase4za_no_live_retry.py backend/tests/test_gemini_phase4za_provider_enablement_audit.py backend/tests/test_gemini_phase4zb_corrected_approval_package.py backend/tests/test_gemini_phase4zb_go_no_go_record.py backend/tests/test_gemini_phase4zb_mock_enablement_bridge.py backend/tests/test_gemini_phase4zb_no_live_execution.py backend/tests/test_gemini_phase4zb_provider_enablement_contract.py backend/tests/test_gemini_phase4zb_second_attempt_command_packet.py -q` -> 64 passed.
- `pytest backend/tests/test_gemini_phase4zc_api_key_header_validation.py backend/tests/test_gemini_phase4zc_client_key_validation_contract.py backend/tests/test_gemini_phase4zc_failed_second_attempt_docs.py backend/tests/test_gemini_phase4zc_key_validation_unit.py backend/tests/test_gemini_phase4zc_no_live_retry.py backend/tests/test_gemini_phase4zd_go_no_go_record.py backend/tests/test_gemini_phase4zd_no_live_execution.py backend/tests/test_gemini_phase4zd_post_run_review_template.py backend/tests/test_gemini_phase4zd_third_attempt_command_packet.py backend/tests/test_gemini_phase4zd_validated_approval_package.py backend/tests/test_gemini_phase4zd_validation_evidence_record.py backend/tests/test_gemini_phase4zd_validation_gate_contract.py -q` -> 392 passed.
- `pytest backend/tests/test_gemini_live_workflow_baseline_capture.py backend/tests/test_gemini_live_workflow_downstream_snapshots.py backend/tests/test_gemini_live_workflow_no_call_no_write.py -q` -> 70 passed, 1 warning.

**Production impact:**  
Mixed. Most code is dry-run/review-only. Local artifacts show prior non-production live attempts. Phase 4K changes `workflow.py` topology in a disabled/no-op way.

**Protected component impact:**  
Requires human review because `workflow.py`, `contracts.py`, `state.py`, and many agents are dirty in the same worktree.

**Risk:**  
HIGH

**Status:**  
Needs human review.

**Notes:**  
Local artifact history shows:

- Phase 4Z first attempt: `live_attempted: true`, `live_completed: false`, provider status `disabled`.
- Phase 4Z-B second attempt: `live_attempted: true`, `live_completed: false`, provider status `failed`; docs cite an illegal-header-value failure.
- Phase 4Z-D third attempt artifact: `live_attempted: true`, `live_completed: true`, provider status `completed`, but run status `quarantined` because secret-like content was detected/redacted, publication dates were missing, unsupported claims were skipped, time horizon was inferred, and cost was not returned.

These local artifacts were inspected only from disk. No live call was made by this audit.

## 5. Workflow and Protected Component Review

`workflow.py` contains Gemini code. The wiring is:

- import: `from app.integrations.gemini_deep_research.graph_adapter import gemini_graph_noop_node`
- node registration: `workflow.add_node("gemini_assist_noop", gemini_graph_noop_node)`
- route: V2 join `"proceed"` now targets `"gemini_assist_noop"`
- edge: `"gemini_assist_noop"` then goes to `"evidence_analyst"`

Classification: disabled/no-op wiring by local tests, but active graph topology modification by file content.

Gemini is wired into LangGraph as a no-op node. It is not absent.

The no-op adapter returns state unchanged by default and local tests assert it does not call the Gemini client, assist wrapper, normalizer, comparator, runner, HTTP clients, live LLM clients, or retrieval clients in disabled/mock paths.

No evidence was found in the inspected Gemini modules that the no-op path writes `agent_outputs`, `ForecastState`, `Signal`, `HorizonForecast`, or `FusionResult`.

Protected components are dirty:

- `contracts.py` changed substantially, but the observed diff excerpts relate to broader contract evolution rather than a Gemini-specific import.
- `state.py` is dirty.
- `QuantifierV2`, `Critic/Governor/SchemaValidator`, and multiple agents are dirty.
- `Librarian`, `ArbitrationPolicy`, `EvidenceDeduper`, and `IndependenceAnalyzer` were inspected for Gemini references. `ArbitrationPolicy` already contains Gemini advisory/forbidden policy concepts. No direct Gemini Deep Research mutation was found there.

Because the worktree is dirty and the Gemini package is untracked, protected-component safety must be treated as not fully accepted until a clean branch or explicit freeze review is completed.

## 6. Test Results Summary

Safe tests run:

| Command | Result |
|---|---|
| `pytest backend/tests/test_gemini_deep_research_client.py -q` | 7 passed, 2 failed |
| `pytest backend/tests/test_gemini_evidence_normalizer.py -q` | 15 passed |
| `pytest backend/tests/test_gemini_shadow_compare.py -q` | 20 passed |
| `pytest backend/tests/test_gemini_shadow_runner.py -q` | 20 passed |
| `pytest backend/tests/test_gemini_evaluation_policy.py -q` | 20 passed |
| `pytest backend/tests/test_gemini_assist_config.py backend/tests/test_gemini_assist_audit.py backend/tests/test_gemini_assist_node.py -q` | 59 passed |
| `pytest backend/tests/test_gemini_assist_disabled_defaults.py backend/tests/test_gemini_assist_integration_safety.py -q` | 50 passed |
| `pytest backend/tests/test_gemini_graph_adapter.py backend/tests/test_gemini_non_interference_utils.py backend/tests/test_gemini_workflow_baseline_fixture.py -q` | 111 passed |
| `pytest backend/tests/test_gemini_disabled_workflow_wiring.py backend/tests/test_gemini_disabled_graph_regression.py backend/tests/test_gemini_disabled_graph_no_call_no_write.py backend/tests/test_gemini_disabled_graph_barrier_safety.py -q` | 84 passed |
| `pytest backend/tests/test_gemini_live_review_runner_preflight.py backend/tests/test_gemini_live_review_runner_cli_safety.py backend/tests/test_gemini_live_review_runner_audit_artifacts.py backend/tests/test_gemini_live_review_runner_no_production_mutation.py -q` | 73 passed |
| `pytest backend/tests/test_gemini_review_mode_mock_path.py backend/tests/test_gemini_review_mode_no_live_calls.py backend/tests/test_gemini_review_mode_multi_domain.py backend/tests/test_gemini_review_mode_audit_review.py backend/tests/test_gemini_review_mode_quarantine_matrix.py backend/tests/test_gemini_review_mode_state_safety.py -q` | 133 passed |
| `pytest backend/tests/test_gemini_phase4u_cli_examples_safety.py backend/tests/test_gemini_phase4u_live_governance_docs.py backend/tests/test_gemini_phase4u_operator_runbook_safety.py backend/tests/test_gemini_phase4v_dry_run_artifact_capture.py backend/tests/test_gemini_phase4v_evidence_documentation.py backend/tests/test_gemini_phase4v_no_live_execution.py -q` | 61 passed |
| `pytest backend/tests/test_gemini_phase4w_artifact_review_checklist.py backend/tests/test_gemini_phase4w_human_review_docs.py backend/tests/test_gemini_phase4w_no_live_authorization.py backend/tests/test_gemini_phase4w_review_decision_template_safety.py backend/tests/test_gemini_phase4x_api_key_rollback_controls.py backend/tests/test_gemini_phase4x_approval_outcome_safety.py backend/tests/test_gemini_phase4x_approval_package_docs.py backend/tests/test_gemini_phase4x_command_packet_safety.py backend/tests/test_gemini_phase4x_no_live_execution.py -q` | 63 passed |
| `pytest backend/tests/test_gemini_phase4y_decision_outcome_safety.py backend/tests/test_gemini_phase4y_execution_readiness_packet.py backend/tests/test_gemini_phase4y_final_preflight_checklist.py backend/tests/test_gemini_phase4y_go_no_go_docs.py backend/tests/test_gemini_phase4y_no_live_execution.py -q` | 39 passed |
| `pytest backend/tests/test_gemini_phase4z_command_handoff_safety.py backend/tests/test_gemini_phase4z_execution_handoff_docs.py backend/tests/test_gemini_phase4z_incident_stop_plan.py backend/tests/test_gemini_phase4z_no_automatic_execution.py backend/tests/test_gemini_phase4z_post_run_review_checklist.py -q` | 36 passed |
| `pytest backend/tests/test_gemini_phase4za_failure_investigation_docs.py backend/tests/test_gemini_phase4za_live_runner_enablement_contract.py backend/tests/test_gemini_phase4za_no_live_retry.py backend/tests/test_gemini_phase4za_provider_enablement_audit.py backend/tests/test_gemini_phase4zb_corrected_approval_package.py backend/tests/test_gemini_phase4zb_go_no_go_record.py backend/tests/test_gemini_phase4zb_mock_enablement_bridge.py backend/tests/test_gemini_phase4zb_no_live_execution.py backend/tests/test_gemini_phase4zb_provider_enablement_contract.py backend/tests/test_gemini_phase4zb_second_attempt_command_packet.py -q` | 64 passed |
| `pytest backend/tests/test_gemini_phase4zc_api_key_header_validation.py backend/tests/test_gemini_phase4zc_client_key_validation_contract.py backend/tests/test_gemini_phase4zc_failed_second_attempt_docs.py backend/tests/test_gemini_phase4zc_key_validation_unit.py backend/tests/test_gemini_phase4zc_no_live_retry.py backend/tests/test_gemini_phase4zd_go_no_go_record.py backend/tests/test_gemini_phase4zd_no_live_execution.py backend/tests/test_gemini_phase4zd_post_run_review_template.py backend/tests/test_gemini_phase4zd_third_attempt_command_packet.py backend/tests/test_gemini_phase4zd_validated_approval_package.py backend/tests/test_gemini_phase4zd_validation_evidence_record.py backend/tests/test_gemini_phase4zd_validation_gate_contract.py -q` | 392 passed |
| `pytest backend/tests/test_gemini_live_workflow_baseline_capture.py backend/tests/test_gemini_live_workflow_downstream_snapshots.py backend/tests/test_gemini_live_workflow_no_call_no_write.py -q` | 70 passed, 1 warning |

Skipped tests:

- No explicit live Gemini execution tests were run.
- No internet or external API tests were run.
- Full repository test suite was not run because this audit was Gemini-focused and the worktree has many unrelated dirty changes.

Unsafe tests not run:

- Any test requiring real credentials, live Gemini, internet, live retrieval, or external APIs was not intentionally run.

Recommended safe command after fixing Phase 1 fixture drift:

```bash
pytest backend/tests/test_gemini_*.py -q
```

Run this only after confirming all `test_gemini_*.py` tests remain mocked/dry-run and after deciding whether project-local artifact writes by some later tests are acceptable.

## 7. API Key Readiness

Should `GEMINI_API_KEY` be added now?

**NO: phase alignment incomplete.**

Reasoning:

- The repository is not clean.
- Gemini package/docs/tests are untracked.
- `workflow.py` contains no-op Gemini wiring that needs explicit human acceptance.
- Phase 1 targeted tests fail due drift with later key validation.
- Local live-attempt artifacts include a completed but quarantined Phase 4Z-D run.
- Later phases are extensive and need freeze/acceptance review before further live activity.

For mock mode:

- No key is needed.

For any future non-production live review run:

- A new explicit approval is required.
- `SEER_USE_GEMINI_DEEP_RESEARCH=1` must be set only for that one run.
- `SEER_GEMINI_MODE=assist` or the approved mode must be set as required by the reviewed command packet.
- `GEMINI_API_KEY` must come from an approved non-production secret source and must not be printed.
- `--allow-live-gemini` remains necessary but not sufficient.
- Stop after exactly one attempt.
- Unset `GEMINI_API_KEY` and `SEER_USE_GEMINI_DEEP_RESEARCH` after the run.

Existing key-safety evidence:

- Missing key returns structured error.
- Disabled provider gate returns before HTTP calls.
- `key_validation.py` rejects missing, empty, placeholder, bracketed, whitespace, newline, carriage-return, tab, control-character, short, and invalid-header keys.
- Client sanitizes errors by replacing the raw key with `[REDACTED_API_KEY]`.
- Local live-review artifacts use `raw_result_redacted.json`.

## 8. Risk Register

| Risk | Severity | Evidence | Mitigation | Owner Decision Needed? |
|---|---|---|---|---|
| Later-phase drift | HIGH | Files exist through Phase 4Z-D while current approved sequence was Phase 3C | Freeze and review later phases before accepting | Yes |
| Dirty/untracked files | HIGH | Gemini integration, docs, tests, data artifacts are untracked; many protected files are dirty | Create clean branch or explicit freeze branch | Yes |
| `workflow.py` Gemini wiring | HIGH | `gemini_assist_noop` registered and routed in V2 graph | Review Phase 4K and no-op tests before accepting | Yes |
| Accidental live Gemini call | HIGH | Live-review runner and live artifacts exist | Keep keys absent; require explicit one-run approval | Yes |
| API key leakage | HIGH | Prior second attempt failed on illegal header; third attempt produced secret-like warning | Keep validation; inspect artifacts; use non-production secret handling | Yes |
| Production state mutation | HIGH | Workflow changed and protected files dirty | Run clean non-interference suite on accepted branch | Yes |
| `agent_outputs` write | HIGH | Tests assert no Gemini writes, but workflow is dirty | Keep disabled/no-op only; human review graph diff | Yes |
| Protected component mutation | HIGH | `contracts.py`, `state.py`, agents, and `workflow.py` are dirty | Dedicated protected component diff review | Yes |
| Unverified tests | MEDIUM | Phase 1 client test file has two failures | Update tests or classify Phase 1 drift before proceeding | Yes |
| Duplicate docs / stale README | MEDIUM | README says no workflow integration in early sections while later sections document Phase 4K | Consolidate docs after freeze | Yes |
| Unclear resume phase | HIGH | Phase 3C requested, repository contains Phase 4Z-D | Choose Path A/B/C before coding | Yes |
| Local live artifacts | HIGH | `data/research/gemini_live_review_trials` includes prior live attempts and one quarantined completed run | Human review, decide retention/isolation | Yes |

## 9. Recommended Path

Recommended: **Path C - Create a clean branch from last trusted phase and reapply later phases selectively.**

Why:

- Path A would ignore a large amount of locally tested governance and safety work, including useful key validation and no-op tests.
- Path B is premature because Phase 1 tests currently fail, the integration tree is untracked, and workflow/protected components are dirty.
- Path C preserves later work while preventing accidental acceptance of untracked or dirty production changes.

Operational recommendation:

1. Freeze this current checkout as an evidence branch or archive.
2. Identify the last trusted baseline, likely Phase 3C plus any prior non-Gemini protected-component work already accepted by the owner.
3. Create a clean branch from that baseline.
4. Reapply phases in order: 4, 4B, 4C, 4D, 4E, 4F, 4G, 4H, 4I, 4J, then decide on 4K separately.
5. Do not accept Phase 4K workflow wiring until the operator explicitly approves the graph topology change.
6. Do not add `GEMINI_API_KEY` until the accepted branch is clean and tests pass.

## 10. Exact Next Prompt Recommendation

Recommended next prompt type: **create clean branch / cleanup plan**.

```text
You are a senior release-governance engineer working in TheSeer.

Use docs/gemini_phase_alignment_audit.md and THESEER_MANIFEST_2026-05-17.md as the authoritative audit inputs.

Do not modify source code yet. Create a clean branch and selective-acceptance plan for Gemini Deep Research.

Your job is to identify the last trusted baseline, propose exactly which Phase 4+ files should be accepted, frozen, isolated, or ignored, and produce a step-by-step branch strategy that preserves evidence while preventing accidental production behavior changes.

Do not add GEMINI_API_KEY.
Do not run live Gemini.
Do not call the internet.
Do not modify workflow.py.
Do not delete or move files.

Output a branch/freeze plan with exact test commands, acceptance criteria, rollback points, and the owner decision required before accepting Phase 4K workflow wiring.
```
