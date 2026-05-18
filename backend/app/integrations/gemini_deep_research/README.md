# Gemini Deep Research Integration - Phase 1, 2, 3A, 3B, 3C, 4, 4B, 4C, 4D, 4E, 4F, 4G, 4H, 4I, 4J, 4K, 4L, 4M, 4N, 4O, 4P, 4Q, 4R, 4S, 4T, 4U, 4V, 4W, 4X, 4Y, 4Z, 4Z-A, 4Z-B, 4Z-C, and 4Z-D

This package is an isolated wrapper for Gemini Deep Research through the Gemini Interactions API.

It does not connect to `workflow.py`, does not modify forecast state, does not write `agent_outputs`, and does not replace any TheSeer agent. It also does not create `EvidenceItem`, `ClaimItem`, `Signal`, `HorizonForecast`, or `FusionResult`.

## Sidecar Operating Modes

The canonical operating-mode reference is `docs/gemini_sidecar_operating_modes.md`.

Gemini remains sidecar-only. `workflow.py` is unwired, Phase 4K remains NOT APPROVED, and no production state mutation is approved. The package must not write `agent_outputs`, must not create `Signal`, `HorizonForecast`, or `FusionResult` objects, and must not run live Gemini unless a separate explicit live-review approval package authorizes it.

## What Exists

- `client.py`: creates and polls background Deep Research interactions.
- `models.py`: stores raw request/result/error/metadata models.
- `prompts.py`: builds safe research-only prompts.
- `storage.py`: saves and loads raw interaction results under `data/research/evidence_packs/` or the configured directory.
- `normalizer.py`: converts raw Gemini results into a local `GeminiEvidencePack`.
- `shadow_compare.py`: compares `GeminiEvidencePack` outputs against local TheSeer outputs.
- `shadow_runner.py`: runs the client, normalizer, comparator, and artifact saving as a workflow-independent command.
- `evaluation_policy.py`: aggregates shadow runs and produces conservative readiness decisions.
- `assist_config.py`: defines disabled-by-default assist configuration, approval, rollback, and gatekeeper models.
- `assist_audit.py`: defines local assist audit bundles and non-production audit storage helpers.
- `assist_node.py`: rehearses a future assist node outside LangGraph in review-only mode.
- `live_review_runner.py`: provides a manually invoked, non-production live-review harness that is blocked by default and tested only through dry-run/mocked paths.

## Mock Mode

Use mock mode for tests or local verification without external calls:

```python
from app.integrations.gemini_deep_research import GeminiDeepResearchClient

client = GeminiDeepResearchClient()
result = await client.run_research("Research the question", mock=True)
```

## Environment Variables Read

- `SEER_USE_GEMINI_DEEP_RESEARCH` default `0`
- `SEER_GEMINI_MODE` default `shadow`
- `SEER_GEMINI_MODEL` default `deep-research-preview-04-2026`
- `SEER_GEMINI_MAX_MODEL` default `deep-research-max-preview-04-2026`
- `SEER_GEMINI_TIMEOUT_SECONDS` default `900`
- `SEER_GEMINI_ENABLE_COLLABORATIVE_PLANNING` default `0`
- `SEER_GEMINI_ENABLE_VISUALIZATION` default `0`
- `SEER_GEMINI_WRITE_EVIDENCE_PACKS` default `1`
- `SEER_GEMINI_EVIDENCE_PACK_DIR` default `data/research/evidence_packs`
- `GEMINI_API_KEY`

If `SEER_USE_GEMINI_DEEP_RESEARCH` is not enabled, live API calls are skipped. If `GEMINI_API_KEY` is missing while live mode is enabled, the client returns a structured error result.

## Known Limitations

- The Interactions API is preview and may change.
- Tests are mocked and never call Gemini.
- No workflow integration exists in Phase 1.
- Collaborative planning and visualization are only passed through as optional request flags.

## Phase 2 Normalizer

`normalizer.py` converts a raw `GeminiDeepResearchResult` into `GeminiEvidencePack`.

The normalizer may create:

- source candidates extracted from citations and URLs
- evidence candidates with canonical URLs and content hashes
- claim candidates only when they are source-backed
- IntelligenceGap-like records when sources are missing, weak, uncited, invalid, failed, or timed out
- warnings for quarantined probability-like content and possible secret leakage

Phase 2 boundaries:

- It does not call Gemini.
- It does not call external web APIs.
- It does not fetch URLs.
- It does not connect to `workflow.py`.
- It does not write `agent_outputs`.
- It does not create signals or probabilities.
- It does not create `HorizonForecast` or `FusionResult`.
- It does not replace any agents.

`to_agent_output_candidate(pack)` can attempt a local contract conversion for validation only. The converted object is not inserted into workflow state by this package.

## Phase 3A Shadow Comparison

`shadow_compare.py` compares a normalized `GeminiEvidencePack` against already available local TheSeer outputs.

The comparator produces:

- `GeminiShadowRun` JSON artifacts
- human-readable markdown reports
- source, evidence, agent-overlap, risk, and recommendation metrics

Phase 3A boundaries:

- It does not call Gemini.
- It does not call the internet.
- It does not fetch URLs.
- It does not connect to `workflow.py`.
- It does not write `agent_outputs`.
- It does not create signals or probabilities.
- It does not create `HorizonForecast` or `FusionResult`.
- It does not replace any agents.

Shadow comparison artifacts are stored under `data/research/gemini_shadow_runs/` by default. This is separate from production forecast result paths.

## Phase 3B Shadow Runner

`shadow_runner.py` is a standalone diagnostic runner. It can run Gemini mock or live outside the production graph, normalize the result, compare it against an optional saved TheSeer output JSON, and save artifacts under:

`data/research/gemini_shadow_runs/{run_id}/`

Each saved run folder contains:

- `raw_result.json`
- `evidence_pack.json`
- `shadow_run.json`
- `shadow_report.md`
- `runner_result.json`

Phase 3B boundaries:

- It does not connect to `workflow.py`.
- It does not call existing agents.
- It does not write `agent_outputs`.
- It does not modify production forecast behavior.
- It does not create signals or probabilities.
- It does not create `HorizonForecast` or `FusionResult`.
- Tests use mocked inputs and do not call Gemini or the internet.

Mock command:

```bash
python -m app.integrations.gemini_deep_research.shadow_runner \
  --query "Assess the risk of escalation in the Red Sea" \
  --mock \
  --print-report
```

With saved TheSeer output:

```bash
python -m app.integrations.gemini_deep_research.shadow_runner \
  --query "Assess the risk of escalation in the Red Sea" \
  --seer-output data/sample_forecast_output.json \
  --mock
```

Live mode is allowed only when explicitly enabled:

```bash
SEER_USE_GEMINI_DEEP_RESEARCH=1 GEMINI_API_KEY=... \
python -m app.integrations.gemini_deep_research.shadow_runner \
  --query "Assess the risk of escalation in the Red Sea"
```

## Phase 3C Evaluation Policy

`evaluation_policy.py` evaluates one or more saved `GeminiShadowRun` artifacts and produces a conservative `GeminiEvaluationDecision`.

The policy can classify Gemini as:

- not useful
- useful as shadow only
- useful as assistant
- ready for limited assist-mode trial
- candidate for future ContextInterpreter replacement
- candidate for future BlackSwanGenerator replacement
- requiring human review

Phase 3C boundaries:

- It does not call Gemini.
- It does not call the internet.
- It does not fetch URLs.
- It does not connect to `workflow.py`.
- It does not write `agent_outputs`.
- It does not modify production forecast behavior.
- It does not create signals or probabilities.
- It does not create `HorizonForecast` or `FusionResult`.
- It never approves replacement; it can only mark future candidate status.

Policy documentation is available at `docs/gemini_shadow_evaluation_policy.md`.

Example usage:

```python
from app.integrations.gemini_deep_research.evaluation_policy import GeminiShadowEvaluationPolicy

policy = GeminiShadowEvaluationPolicy()
runs = policy.load_runs_from_dir("data/research/gemini_shadow_runs")
decision = policy.evaluate_runs(runs, domain="general")
print(policy.render_policy_report(decision))
```

## Phase 4 Limited Assist-Mode Trial Plan

Phase 4 is planning only. The limited assist-mode plan is documented at `docs/gemini_limited_assist_mode_trial_plan.md`.

No workflow integration exists, no production behavior changed, and no agents are replaced. The next implementation step, if approved later, should be Phase 4B: assist-mode config and audit models only, with no workflow connection.

## Phase 4B Assist Config and Audit Models

`assist_config.py` and `assist_audit.py` define the local safety box for a future limited assist-mode trial.

They provide:

- disabled-by-default assist configuration parsing
- human approval records
- policy approval references
- rollback status
- gatekeeper checks that only decide whether a future trial would be allowed
- assist audit bundles and trial-result artifacts under `data/research/gemini_assist_trials/{run_id}/`

Phase 4B boundaries:

- It does not run Gemini.
- It does not connect to `workflow.py`.
- It does not write `agent_outputs`.
- It does not modify production forecast behavior.
- It does not replace any agents.
- The gatekeeper returns `ready_for_trial` only when config, policy, approval, rollback, and domain checks all pass.

Phase 4B remains configuration and audit modeling only.

## Phase 4C Isolated Assist-Node Wrapper

`assist_node.py` provides `GeminiAssistNodeWrapper`, a standalone rehearsal harness for a future assist node.

Phase 4C behavior:

- It is not wired into LangGraph.
- It does not modify `workflow.py`.
- It does not call existing agents.
- It does not write `agent_outputs`.
- It does not mutate the original input state.
- It defaults to `review_only=True`.
- It runs `GeminiAssistGatekeeper` before any research path.
- It can produce assist audit artifacts, raw-result JSON, evidence-pack JSON, trial-result JSON, and node-result JSON under `data/research/gemini_assist_trials/{run_id}/`.
- It can build a candidate `AgentOutput` for validation/review only.
- It may attach a non-production `gemini_assist_review` artifact only to a cloned state and only when explicitly requested.

Phase 4C remains isolated wrapper work only.

## Phase 4D Disabled Defaults and Integration-Safety Tests

Phase 4D adds regression tests proving the assist stack remains disabled, inert, and safe by default.

The Phase 4D tests verify:

- default config disables Gemini assist behavior
- shadow mode and disabled assist flags block execution
- rollback, missing policy approval, missing human approval, expired approval, and sensitive domains block execution
- review-only mode does not mutate production state or write `agent_outputs`
- review artifacts stay under `gemini_assist_review` on cloned state only
- audit artifacts use test-controlled directories in tests
- tests remain mocked and do not call Gemini or the internet

Phase 4D adds no graph wiring and no production behavior.

## Phase 4E Graph Wiring Disabled-Flag Plan

Phase 4E is planning only. The graph wiring plan is documented at `docs/gemini_graph_wiring_disabled_flag_plan.md`.

Phase 4E boundaries:

- It does not modify `workflow.py`.
- It does not wire anything into LangGraph.
- It does not change production behavior.
- It documents disabled-by-default flags, permitted and forbidden state keys, byte-for-byte non-interference requirements, rollback rules, audit requirements, and future graph-wiring tests.

The next recommended step is Phase 4F: an isolated no-op graph adapter function, still with no `workflow.py` modification.

## Phase 4F Isolated No-Op Graph Adapter

`graph_adapter.py` adds `GeminiGraphNoopAdapter` and `gemini_graph_noop_node`.

Phase 4F behavior:

- It is an isolated no-op graph adapter.
- It is not wired into LangGraph.
- It does not modify `workflow.py`.
- It returns state unchanged by default.
- It does not call Gemini or the assist wrapper on the default path.
- It does not write `agent_outputs`.
- It protects production state keys such as forecast outputs, report outputs, and protected component results.
- It exists only to rehearse the future graph-node boundary.

The optional review-only graph execution path remains future work. The next recommended step is Phase 4G: stronger no-op adapter regression tests or byte-for-byte workflow fixture planning, still with no `workflow.py` modification.

## Phase 4G Byte-for-Byte Non-Interference Test Plan

Phase 4G is planning only. The byte-for-byte non-interference test plan is documented at `docs/gemini_byte_for_byte_non_interference_test_plan.md`.

Phase 4G boundaries:

- It does not modify `workflow.py`.
- It does not wire anything into LangGraph.
- It does not change production behavior.
- It defines how future disabled Gemini graph wiring must prove identical output against a baseline workflow run.
- It documents exact-match fields, approved nondeterministic exclusions, downstream input snapshots, no-call guarantees, no-write guarantees, and future test files.

The next recommended step is Phase 4H: canonical serialization and baseline fixture utilities, still with no `workflow.py` modification.

## Phase 4H Canonical Serialization and Baseline Fixture Utilities

Phase 4H adds test-only canonical serialization and fixture helpers in `backend/tests/gemini_non_interference_utils.py`.

Phase 4H behavior:

- It does not run the workflow.
- It does not modify `workflow.py`.
- It does not wire Gemini into LangGraph.
- It provides deterministic JSON, state, and report canonicalization helpers.
- It provides protected-state-key checks for future disabled-wiring tests.
- It provides artifact read/write helpers for future baseline and disabled-wiring fixtures.
- It provides Gemini-key safety assertions for future non-interference tests.

The next recommended step is Phase 4I: baseline fixture tests against the current workflow, still with no Gemini graph wiring.

## Phase 4I Workflow-Shaped Baseline Fixture Tests

Phase 4I adds baseline fixture tests against the current workflow shape in `backend/tests/test_gemini_workflow_baseline_fixture.py`.

Phase 4I behavior:

- It does not modify `workflow.py`.
- It does not wire Gemini into LangGraph.
- It does not call Gemini or the internet.
- It uses a workflow-shaped baseline fixture rather than running the live workflow.
- It validates baseline state, report, agent outputs, metadata, protected-state keys, no-Gemini-key assertions, and tmp_path-only artifact writes.
- It prepares future byte-for-byte disabled-wiring comparison without changing production behavior.

The next recommended step is Phase 4J planning or disabled graph wiring only after baseline tests remain stable.

## Phase 4J Disabled Graph Wiring Implementation Plan

Phase 4J is planning only. The disabled graph wiring implementation plan is documented at `docs/gemini_disabled_graph_wiring_implementation_plan.md`.

Phase 4J boundaries:

- It does not modify `workflow.py`.
- It does not wire anything into LangGraph.
- It does not change production behavior.
- It documents the exact future insertion point, route-target change, no-op node, no-call/no-write requirements, rollback plan, blockers, and operator approval checklist.
- It preserves the current V2 spine and keeps Gemini out of `v2_join_node` barrier logic.

The next possible step is Phase 4K: first disabled/no-op `workflow.py` wiring only if explicitly approved.

## Phase 4K Disabled/No-Op Workflow Wiring

Phase 4K adds the first disabled/no-op `workflow.py` wiring.

Phase 4K behavior:

- It inserts `gemini_assist_noop` after `v2_join_node` and before `evidence_analyst`.
- The node callable is `gemini_graph_noop_node`.
- The node is not enabled for Gemini.
- The node returns state unchanged by default.
- It does not call Gemini.
- It does not write `agent_outputs`.
- It does not create `Signal`, `HorizonForecast`, or `FusionResult`.
- It does not alter `v2_join_node` barrier logic.
- It does not add Gemini to `BARRIER_NODE_TO_KEY`.
- It does not add Gemini to `active_agents` or `skipped_agents`.

The next phase should be Phase 4L: disabled graph regression and byte-for-byte comparison.

## Phase 4L Disabled Graph Regression

Phase 4L adds disabled graph regression and byte-for-byte comparison tests.

Phase 4L behavior:

- It does not enable Gemini.
- It does not add review-only execution.
- It proves the Phase 4K no-op wiring is inert.
- It checks no-call/no-write behavior for Gemini research, assist wrapper, normalizer, comparator, runner, and audit helpers.
- It checks protected state keys and no-Gemini state/agent-output guarantees against the workflow-shaped baseline.
- It checks route and barrier safety around `v2_join_node`, `gemini_assist_noop`, and the protected V2 spine.

The next phase should be Phase 4M planning for rollback, live workflow-derived baseline capture, or review-only test mode depending on regression results.

## Phase 4M Decision and Live Workflow-Derived Baseline Plan

Phase 4M is planning only. The decision and live workflow-derived baseline plan is documented at `docs/gemini_phase4m_decision_and_live_baseline_plan.md`.

Phase 4M behavior:

- It adds no Python/source-code changes.
- It does not modify `workflow.py`.
- It does not enable Gemini.
- It does not add review-only execution.
- It recommends keeping the disabled/no-op wiring frozen while Phase 4N captures a live workflow-derived deterministic baseline.

The recommended next phase is Phase 4N: live workflow-derived baseline capture tests with deterministic mocks, still with no Gemini enablement.

## Phase 4N Live Workflow-Derived Baseline Capture Tests

Phase 4N adds live workflow-derived baseline capture tests with deterministic mocks.

Phase 4N behavior:

- It does not enable Gemini.
- It does not add review-only execution.
- It does not modify `workflow.py`.
- It runs the compiled/current workflow under deterministic test node wrappers with the disabled/no-op Gemini node present.
- It captures live workflow-derived baseline state, report, agent outputs, metadata, and downstream input snapshots under `tmp_path` in tests.
- It verifies no Gemini client, assist wrapper, normalizer, comparator, runner, audit helper, internet, live LLM, live retrieval, or live API path is called.
- It verifies no Gemini artifact files are written by default.
- It records route/barrier metadata for `v2_join_node -> gemini_assist_noop -> evidence_analyst`.

The next phase should be Phase 4O planning: decide whether to roll back, strengthen live baseline capture, or design a test-only review-mode experiment.

## Phase 4O Review-Mode Decision Plan

Phase 4O is planning only. The review-mode decision plan is documented at `docs/gemini_phase4o_review_mode_decision_plan.md`.

Phase 4O behavior:

- It adds no Python/source-code changes.
- It does not modify `workflow.py`.
- It does not add graph wiring.
- It does not enable Gemini.
- It does not add review-only execution.
- It recommends keeping the disabled/no-op wiring frozen while deciding whether to proceed to a test-only mock review-mode experiment.

The recommended next phase is Phase 4P only if approved: test-only, mock-only review-mode implementation.

## Phase 4P Test-Only Mock Review Mode

Phase 4P adds a test-only, mock-only review-mode path.

Phase 4P behavior:

- It remains disabled by default.
- `gemini_graph_noop_node` still no-ops by default.
- Review mode requires explicit test invocation.
- Review mode requires `mock=True`.
- Review mode requires policy approval, human approval, rollback off, and a safe `tmp_path` audit directory.
- Review mode may attach only `gemini_assist_review` to a cloned state.
- It does not write `agent_outputs`.
- It does not alter protected production keys.
- It does not enable live Gemini.
- It does not call the internet.
- It redacts secret-like raw-result audit artifacts and quarantines secret/probability/malformed output conditions.

The next phase should be Phase 4Q: multi-domain mock review-mode regression tests and audit review, still no live Gemini.

## Phase 4Q Multi-Domain Mock Review Regression

Phase 4Q adds multi-domain mock review-mode regression tests and audit review.

Phase 4Q behavior:

- It remains mock-only and test-only.
- It does not enable live Gemini.
- It does not modify `workflow.py`.
- It verifies safe-domain behavior for `general`, `technology`, and `policy`.
- It verifies sensitive-domain blocking for `geopolitics`, `security`, `finance`, and `elections` without explicit sensitive approval.
- It verifies sensitive-domain mock review mode can run only with explicit sensitive approval.
- It verifies audit artifact structure, JSON validity, redaction, and `tmp_path`-only writes.
- It verifies quarantine behavior for secret warnings, probability contamination, malformed output, timeouts, failures, unsupported claims, uncited claims, and invalid URLs.
- It verifies no-live-call/no-write guarantees and protected-key stability.

The next phase should be Phase 4R: human review of audit artifacts and a decision on whether to continue, rollback, or keep review mode mock-only.

## Phase 4R Human Review and Governance Decision

Phase 4R is documentation/governance only. The human review and governance decision is documented at `docs/gemini_phase4r_human_review_and_governance_decision.md`.

Phase 4R behavior:

- It adds no Python/source-code changes.
- It does not modify `workflow.py`.
- It does not enable live Gemini.
- It does not add production review mode.
- It reviews Phase 4Q mock-only audit and regression evidence.
- It recommends keeping disabled/no-op wiring and test-only mock review mode while blocking live Gemini.

The recommended next phase is Phase 4S planning only if approved: a limited non-production live Gemini review-only experiment plan.

## Phase 4S Limited Non-Production Live Review Experiment Plan

Phase 4S is planning only. The limited non-production live review experiment plan is documented at `docs/gemini_phase4s_limited_live_review_experiment_plan.md`.

Phase 4S behavior:

- It adds no Python/source-code changes.
- It does not modify `workflow.py`.
- It does not execute live Gemini.
- It does not add production review mode.
- It defines non-production-only boundaries, allowed and forbidden domains, run limits, cost/latency limits, API key handling, audit artifacts, human review, citation validation, stop rules, and rollback.

The recommended next phase is Phase 4T only if approved: a limited non-production live review-only harness.

## Phase 4T Limited Non-Production Live Review Harness

Phase 4T adds `live_review_runner.py`, a limited non-production live review-only harness. It is blocked by default and is manually invoked only.

Phase 4T behavior:

- It does not modify `workflow.py`.
- It does not add graph wiring or production review mode.
- It does not write `agent_outputs`.
- It does not mutate protected production keys.
- It requires explicit non-production flags, manual approval, an allowed domain, a safe audit directory, cost/latency limits, and an API key only for real live execution.
- It generates redacted dry-run/preflight artifacts, human review templates, citation review templates, and latency/cost metadata.
- Tests are dry-run/mocked and do not call live Gemini, the internet, or live external APIs.

The recommended next phase is Phase 4U: dry-run operator rehearsal and documentation, or Phase 4T-live only by manual operator command outside tests.

## Phase 4U Operator Rehearsal and Live Governance Documentation

Phase 4U adds operator rehearsal and governance documentation:

- `docs/gemini_phase4u_operator_rehearsal_runbook.md`
- `docs/gemini_phase4u_live_review_governance_checklist.md`

Phase 4U behavior:

- It does not enable live Gemini.
- It does not execute live Gemini.
- It does not modify `workflow.py`.
- It does not add graph wiring.
- It does not change production behavior.
- It keeps dry-run/mock-only rehearsal as the safe operator path.
- It documents expected dry-run artifacts, operator inspection steps, stop rules, and evidence to record.
- It states that future live use still requires separate explicit approval.

The recommended next phase is Phase 4V: dry-run operator rehearsal artifact capture, still with no live Gemini.

## Phase 4V Dry-Run Rehearsal Artifact Capture

Phase 4V captures dry-run rehearsal evidence for the Phase 4T non-production live-review harness. The evidence record is documented at `docs/gemini_phase4v_dry_run_rehearsal_evidence.md`.

Phase 4V behavior:

- It does not enable live Gemini.
- It does not execute live Gemini.
- It does not use or require API keys.
- It does not modify `workflow.py`.
- It does not add graph wiring.
- It does not change production behavior.
- It verifies expected dry-run artifacts and safety checks.
- It proves dry-run artifact capture can occur under `tmp_path` in tests without live Gemini, internet, or live API calls.
- It states that future live use still requires separate explicit approval.

The recommended next phase is Phase 4W: human review of captured dry-run artifacts and an approval decision, still with no automatic live execution.

## Phase 4W Human Review of Dry-Run Artifacts

Phase 4W creates the human-review process and decision templates for Phase 4V dry-run artifacts:

- `docs/gemini_phase4w_human_review_decision_record.md`
- `docs/gemini_phase4w_artifact_review_checklist.md`

Phase 4W behavior:

- It does not authorize live Gemini.
- It does not execute live Gemini.
- It does not use or require API keys.
- It does not modify `workflow.py`.
- It does not add graph wiring.
- It does not change production behavior.
- It reviews dry-run artifacts only.
- It limits decisions to requesting one future live-run approval prompt, repeating dry-run only, deferring pending fixes, or rejecting.
- It states that future live use still requires separate explicit approval.

The recommended next phase is Phase 4X: a separate approval prompt for exactly one limited, manually invoked, non-production live review-run request. Phase 4X should still be an approval gate, not automatic live execution.

## Phase 4X One-Run Live Approval Package

Phase 4X creates the approval package for exactly one limited, manually invoked, non-production live review-run request:

- `docs/gemini_phase4x_one_run_live_approval_package.md`
- `docs/gemini_phase4x_live_run_command_packet.md`
- `docs/gemini_phase4x_api_key_and_rollback_controls.md`

Phase 4X behavior:

- It does not execute live Gemini.
- It does not call the internet or live external APIs.
- It does not use or require API keys in tests.
- It does not modify `workflow.py`.
- It does not add graph wiring.
- It does not change production behavior.
- It does not authorize automatic live execution.
- It prepares one-run approval materials, a future-only command packet, API-key controls, and rollback/stop controls.

The recommended next phase is Phase 4Y: manual approval review of the one-run package and explicit go/no-go decision. Phase 4Y should still not execute live Gemini unless the user separately requests the approved command execution after approval.

## Phase 4Y Go/No-Go Decision Process

Phase 4Y creates the manual approval review and go/no-go decision process for exactly one limited, manually invoked, non-production live Gemini review run:

- `docs/gemini_phase4y_go_no_go_decision_record.md`
- `docs/gemini_phase4y_final_preflight_checklist.md`
- `docs/gemini_phase4y_execution_readiness_packet.md`

Phase 4Y behavior:

- It does not execute live Gemini.
- It does not call the internet or live external APIs.
- It does not use or require API keys.
- It does not modify `workflow.py`.
- It does not add graph wiring.
- It does not change production behavior.
- It records a human go/no-go decision only.
- It limits any GO outcome to exactly one future manual run request.
- It does not authorize retries, batch execution, scheduling, background execution, production graph integration, production forecast influence, or additional live runs.
- It still requires a separate user/operator request before any approved one-run command can be executed.

The recommended next step is no automatic execution. If the Phase 4Y decision is GO and all final preflight checks pass, the operator may make a separate request for the single approved command; otherwise repeat dry-run review or fix the blocking issue.

## Phase 4Z One-Run Execution Handoff

Phase 4Z creates the approved one-run execution handoff for exactly one manually invoked, non-production, review-only Gemini live run:

- `docs/gemini_phase4z_one_run_execution_handoff.md`
- `docs/gemini_phase4z_post_run_review_checklist.md`
- `docs/gemini_phase4z_execution_incident_stop_plan.md`

Phase 4Z behavior:

- It does not automatically execute live Gemini.
- It does not enable production Gemini.
- It does not call the internet or live external APIs in tests.
- It does not use or require API keys in tests.
- It does not modify `workflow.py`.
- It does not add graph wiring.
- It does not change production behavior.
- It requires Phase 4Y GO, final preflight PASS, and a separate explicit execution request before any live command.
- The future live run is exactly one manually invoked, non-production, review-only run.
- All output remains review-only and outside production state.
- Post-run review is required.
- Additional live runs require a new approval package.

The recommended next step is not automatic execution. If Phase 4Y GO, final preflight PASS, and a separate explicit execution request are complete, the operator may execute exactly one approved non-production live review command using the Phase 4Z handoff. If any condition is missing, complete Phase 4Y records or repeat dry-run/governance review.

## Phase 4Z-A Live Attempt Failure Investigation

Phase 4Z-A investigates and documents the failed/blocked Phase 4Z one-run live attempt:

- `docs/gemini_phase4za_live_attempt_failure_investigation.md`
- `docs/gemini_phase4za_provider_enablement_audit.md`
- `docs/gemini_phase4za_next_attempt_requirements.md`

Phase 4Z-A behavior:

- It does not retry live Gemini.
- It does not authorize another live run.
- It does not call the internet or live external APIs in tests.
- It does not use or require a real Gemini API key.
- It does not modify `workflow.py`.
- It does not add graph wiring.
- It does not change production behavior.
- It records that the previous Phase 4Z command counts as one attempted live run.
- It rejects the output because `provider_status: disabled`, `live_completed: false`, raw report was empty, citations were empty, and cost was not returned.
- It documents that `--allow-live-gemini` is necessary but not sufficient: the underlying client also requires `SEER_USE_GEMINI_DEEP_RESEARCH=1`.
- It recommends `SEER_GEMINI_MODE=assist` for governance-consistent future review mode.
- It states that any further live attempt requires a new approval package.

The recommended next step is no retry under the consumed Phase 4Y/4Z approval. Prepare a new approval package only after the provider enablement chain is explicitly reviewed and approved.

## Phase 4Z-B Corrected Second-Attempt Approval Package

Phase 4Z-B creates the corrected approval package and provider-enablement contract for a future second one-run, manually invoked, non-production, review-only Gemini live attempt:

- `docs/gemini_phase4zb_corrected_second_attempt_approval_package.md`
- `docs/gemini_phase4zb_provider_enablement_contract.md`
- `docs/gemini_phase4zb_second_attempt_command_packet.md`
- `docs/gemini_phase4zb_second_attempt_go_no_go_record.md`

Phase 4Z-B behavior:

- It does not execute live Gemini.
- It does not retry the previous Phase 4Z attempt.
- It does not call the internet or live external APIs in tests.
- It does not use or require a real Gemini API key in tests.
- It does not modify `workflow.py`.
- It does not add graph wiring.
- It does not change production behavior.
- It records that the previous approval was consumed and the previous output was rejected.
- It documents that `--allow-live-gemini` is necessary but not sufficient.
- It adds the corrected lower-level provider prerequisite: `SEER_USE_GEMINI_DEEP_RESEARCH=1`.
- It recommends `SEER_GEMINI_MODE=assist` for governance consistency.
- It requires a new approval record, new GO decision, new final preflight PASS, new operator confirmation, and a separate explicit execution request before any future second attempt.
- It keeps the second attempt exactly one manually invoked, non-production, review-only run.

The recommended next step is no automatic execution. If the corrected Phase 4Z-B approval package is signed and a new GO/PASS/handoff is completed, the operator may separately request exactly one corrected second-attempt execution. If any uncertainty remains, repeat dry-run only.

## Phase 4Z-C: Failed Second Attempt Investigation and API Key Validation

Phase 4Z-C investigates the failed corrected Phase 4Z-B second attempt and adds fail-closed API-key/header validation.

**Investigation summary:**

- The corrected Phase 4Z-B second attempt was executed exactly once and consumed.
- The output is rejected: `live_completed: false`, `status: failed`, `provider_status: failed`.
- Terminal failure: `Gemini Deep Research create_interaction failed: Illegal header value b'[REDACTED_API_KEY]'`
- No usable Gemini report, citations, cost, or usage metadata were returned.
- No API key leakage was observed in artifacts.
- No production mutation was observed.
- Investigation documents: `docs/gemini_phase4zc_failed_second_attempt_investigation.md`

**API-key/header validation added:**

- `key_validation.py`: adds `validate_api_key_for_header(key)` — a fail-closed validator that rejects missing, empty, placeholder, bracket-containing, control-character-containing, space-containing, and too-short keys before any HTTP header is constructed.
- `client.py`: wired to call `validate_api_key_for_header` in `create_interaction()` and `poll_interaction()` **before** `_post_interaction()` or `_get_interaction()` are invoked.
- Validation contract: `docs/gemini_phase4zc_api_key_header_validation.md`
- Future attempt requirements: `docs/gemini_phase4zc_future_attempt_requirements.md`

**Phase 4Z-C absolute boundaries:**

- It does not retry live Gemini.
- It does not authorize another live attempt.
- It does not use or require a real API key.
- It does not call the internet.
- It does not modify `workflow.py`, `contracts.py`, graph state, or existing agents.
- It does not write `agent_outputs`, `Signal`, `HorizonForecast`, `FusionResult`, `final_report`, or `executive_summary`.

**No new live attempt is approved.** Any future live attempt requires a new approval package after validation passes. No new live execution is approved by this README entry. No active retry command exists.

Recommended next phase: Phase 4Z-D — Validated Third-Attempt Approval Package (preparation only, no live execution).

## Phase 4Z-D: Validated Third-Attempt Approval Package

Phase 4Z-D prepares the validated approval package, validation evidence record, corrected command packet, go/no-go record, and post-run review template for a possible future third attempt.

**Context:**

- First attempt (Phase 4Z): consumed and rejected — `provider_status: disabled` because `SEER_USE_GEMINI_DEEP_RESEARCH` was not truthy.
- Second attempt (Phase 4Z-B): consumed and rejected — `Illegal header value b'[REDACTED_API_KEY]'` because the API key was a malformed or placeholder value that could not be placed in an HTTP header.
- Phase 4Z-C: investigated the second failure and implemented fail-closed API-key/header validation in `key_validation.py`, wired into `client.py` before `_post_interaction()` and `_get_interaction()`. All 163 tests (99 Phase 4Z-C + 64 Phase 4Z-B/4Z-A regression) passed.

**Phase 4Z-D documents:**

- `docs/gemini_phase4zd_validated_third_attempt_approval_package.md`
- `docs/gemini_phase4zd_validation_evidence_record.md`
- `docs/gemini_phase4zd_third_attempt_command_packet.md`
- `docs/gemini_phase4zd_third_attempt_go_no_go_record.md`
- `docs/gemini_phase4zd_post_run_review_template.md`

**Phase 4Z-D absolute boundaries:**

- It does not execute live Gemini.
- It does not retry either prior attempt.
- It does not authorize automatic execution.
- It does not use or require a real API key.
- It does not call the internet.
- It does not modify `workflow.py`, `contracts.py`, graph state, or existing agents.
- It does not write `agent_outputs`, `Signal`, `HorizonForecast`, `FusionResult`, `final_report`, or `executive_summary`.

**No new live attempt is approved by Phase 4Z-D.** Any future third attempt requires the Phase 4Z-D approval package to be signed, a new GO decision to be reached, a new final preflight PASS to be confirmed, and a separate explicit execution request to be received. No active retry command exists.

Recommended next step: complete and sign the Phase 4Z-D approval package, GO/PASS record, and operator confirmation — then issue a separate execution request for exactly one validated third attempt.
