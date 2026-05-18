# Gemini Deep Research Clean Branch and Selective Acceptance Plan

Date: 2026-05-17

Scope: planning and documentation only. This plan is based on the local phase-alignment audit and TheSeer manifest:

- `docs/gemini_phase_alignment_audit.md`
- `THESEER_MANIFEST_2026-05-17.md`

No source code, tests, workflow files, agent files, contracts, state definitions, environment files, package files, branches, API keys, live Gemini calls, internet calls, or production behavior were intentionally changed to create this plan.

## 1. Executive Decision

Recommended path: **Path C - create a clean branch from the last trusted baseline and reapply/accept later phases selectively.**

The current checkout is too dirty and too far ahead of the verified Phase 3C sequence to accept wholesale. The repository contains useful Phase 4+ work, including tests and governance documents, but it also contains dirty protected components, untracked Gemini files, live-review artifacts, and disabled/no-op workflow wiring in `workflow.py`.

Phase 4K workflow wiring should **not** be accepted now. It must be postponed and classified as `BLOCK_UNTIL_HUMAN_REVIEW` because it changes production LangGraph topology even if the node is currently no-op and disabled.

`GEMINI_API_KEY` should **not** be added now. API-key use should wait until the clean selective branch is green, protected diffs are reviewed, live governance is re-approved, and a single non-production live run is explicitly authorized.

## 2. Last Trusted Baseline

Logical trusted baseline:

- Phase 2 normalizer: verified by targeted tests.
- Phase 3A shadow comparator: verified by targeted tests.
- Phase 3B workflow-independent shadow runner: verified by targeted tests.
- Phase 3C shadow evaluation policy: verified by targeted tests and is the cleanest policy baseline.

Conditional baseline item:

- Phase 1 client wrapper exists and is architecturally part of the shadow sidecar, but its current targeted client tests are not clean. The audit recorded 7 passing tests and 2 failures caused by later Phase 4Z-C API-key validation rejecting the older `"fake-key"` fixture. Phase 1 should be accepted only after reconciling that test drift.

Git baseline:

- A precise trusted git commit cannot be inferred from this checkout because the Gemini package, Gemini docs, and Gemini tests are untracked, while many protected tracked files are dirty.
- The operator must identify the last clean trusted commit or branch before creating the new baseline branch.

Recommended baseline statement:

> Treat Phase 3C shadow-sidecar behavior as the last trusted logical baseline, but create the clean branch from an operator-confirmed clean git commit and then reapply Phase 1-3C selectively with Phase 1 tests reconciled.

## 3. Repository Classification

| Category | Classification | Evidence | Proposed Handling |
|---|---|---|---|
| Trusted baseline | Phase 2, 3A, 3B, 3C shadow-sidecar work | Targeted tests passed in audit | `TRUSTED_ACCEPT` after clean branch replay |
| Conditional trusted work | Phase 1 client wrapper | Present, but 2 tests fail after key-validation drift | `ACCEPT_AFTER_TESTS` |
| Useful later-phase work | Phase 4B, 4D, 4F, 4G-H-I tests/utilities | Later mocked/dry-run suites passed locally | `ACCEPT_AFTER_TESTS` in batches |
| Workflow-topology changes | Phase 4K disabled/no-op workflow wiring | `workflow.py` imports/registers/routes through Gemini no-op node | `BLOCK_UNTIL_HUMAN_REVIEW` |
| Live-review/API-key work | Phase 4M through 4Z-D docs, runner, key validation, artifacts | Live-capable code and local live-attempt artifacts exist | `ISOLATE_OUT_OF_PRODUCTION` unless separately approved |
| Dirty protected-component work | `workflow.py`, contracts, state, agents, LLM files, env/package files | `git status --short` and diff inspection | `BLOCK_UNTIL_HUMAN_REVIEW` |
| Final-stage backlog | rename, cleanup, archive, app redesign, operator cockpit | Manifest marks these deferred | `DEFER_FINAL_STAGE` |

## 4. Acceptance Categories

Use these exact categories during selective acceptance:

- `TRUSTED_ACCEPT`: accept into the clean branch after confirming the relevant targeted tests pass from a clean checkout.
- `ACCEPT_AFTER_TESTS`: useful work, but it must pass targeted tests and be reviewed for protected-surface isolation before acceptance.
- `FREEZE_FOR_REVIEW`: preserve the files for human review, but do not merge into the production branch yet.
- `ISOLATE_OUT_OF_PRODUCTION`: keep in a quarantine/review branch or artifact archive, not in the clean production branch.
- `IGNORE_FOR_NOW`: leave out of the clean branch unless a later decision needs it.
- `BLOCK_UNTIL_HUMAN_REVIEW`: do not accept without explicit owner approval.
- `DEFER_FINAL_STAGE`: postpone until TheSeer is stable, tested, and operationally clean.

## 5. Phase Acceptance Matrix

| Phase | Current Status | Risk | Proposed Action | Required Tests | Required Human Approval | Notes |
|---|---|---|---|---|---|---|
| Phase 1 | Present; 7 passed, 2 failed | MEDIUM | `ACCEPT_AFTER_TESTS` | `pytest backend/tests/test_gemini_deep_research_client.py -q` after reconciling fake-key/key-validation drift | Yes, to approve validation behavior | Do not weaken key validation just to restore old fixtures. Update tests or phase boundary deliberately. |
| Phase 2 | Verified locally | LOW | `TRUSTED_ACCEPT` | `pytest backend/tests/test_gemini_evidence_normalizer.py -q` | No, beyond normal review | Local normalizer only; no workflow integration. |
| Phase 3A | Verified locally | LOW | `TRUSTED_ACCEPT` | `pytest backend/tests/test_gemini_shadow_compare.py -q` | No, beyond normal review | Shadow comparison only. |
| Phase 3B | Verified locally | LOW | `TRUSTED_ACCEPT` | `pytest backend/tests/test_gemini_shadow_runner.py -q` | No, beyond normal review | Workflow-independent runner; keep live mode disabled by default. |
| Phase 3C | Verified locally | LOW | `TRUSTED_ACCEPT` | `pytest backend/tests/test_gemini_evaluation_policy.py -q` | No, beyond normal review | Cleanest verified policy baseline. |
| Phase 4 | Present as documentation | LOW | `FREEZE_FOR_REVIEW` or `ACCEPT_AFTER_TESTS` as docs-only | Documentation review; no runtime tests required | Yes, governance approval | Keep as a plan only; it does not authorize assist mode. |
| Phase 4B | Verified locally; untracked | LOW | `ACCEPT_AFTER_TESTS` | `pytest backend/tests/test_gemini_assist_config.py backend/tests/test_gemini_assist_audit.py -q` | Yes, for config/audit semantics | Accept only with no production connection. |
| Phase 4C | Verified locally; untracked | MEDIUM | `FREEZE_FOR_REVIEW` | `pytest backend/tests/test_gemini_assist_node.py -q` | Yes | Rehearses future assist behavior; do not connect to graph. |
| Phase 4D | Verified locally | LOW | `ACCEPT_AFTER_TESTS` | `pytest backend/tests/test_gemini_assist_disabled_defaults.py backend/tests/test_gemini_assist_integration_safety.py -q` | No, beyond normal review | Useful safety tests for disabled defaults. |
| Phase 4E | Present as documentation | LOW | `FREEZE_FOR_REVIEW` | Documentation review | Yes | The plan predates current workflow wiring; review against actual 4K diff. |
| Phase 4F | Verified locally | LOW unless wired | `ACCEPT_AFTER_TESTS` only if not wired to `workflow.py` | `pytest backend/tests/test_gemini_graph_adapter.py -q` | Yes if accepted near graph work | Adapter alone can be accepted; workflow connection remains blocked. |
| Phase 4G | Present as documentation | LOW | `ACCEPT_AFTER_TESTS` or `FREEZE_FOR_REVIEW` | Documentation review | Optional | Non-interference plan is useful as acceptance criteria. |
| Phase 4H | Verified locally | LOW | `ACCEPT_AFTER_TESTS` | `pytest backend/tests/test_gemini_non_interference_utils.py -q` | No, beyond normal review | Test utility only. |
| Phase 4I | Verified locally | LOW | `ACCEPT_AFTER_TESTS` | `pytest backend/tests/test_gemini_workflow_baseline_fixture.py -q` | No, beyond normal review | Fixture tests are useful but not production proof. |
| Phase 4J | Present as documentation | LOW | `FREEZE_FOR_REVIEW` | Documentation review | Yes | Keep as future wiring proposal. |
| Phase 4K | Present in dirty `workflow.py` | HIGH | `BLOCK_UNTIL_HUMAN_REVIEW` | Only after approval: disabled workflow/no-call/regression tests | Required: workflow/topology owner | Postpone. No-op graph topology still changes production workflow. |
| Phase 4L | Present; depends on 4K | MEDIUM | `FREEZE_FOR_REVIEW` | `pytest backend/tests/test_gemini_disabled_graph_regression.py backend/tests/test_gemini_disabled_graph_no_call_no_write.py backend/tests/test_gemini_disabled_graph_barrier_safety.py -q` | Yes if 4K is accepted | Keep with 4K review package, not with clean 3C branch. |
| Phase 4M | Present as decision/live baseline docs | MEDIUM | `ISOLATE_OUT_OF_PRODUCTION` or `FREEZE_FOR_REVIEW` | Documentation review and no-live safety tests | Yes | Do not mix with production branch. |
| Phase 4O | Present as review-mode plan | MEDIUM | `FREEZE_FOR_REVIEW` | Review-mode mock/no-live tests if code accepted | Yes | Planning can be preserved; implementation requires separate gate. |
| Phase 4R | Present as governance decision docs | MEDIUM | `FREEZE_FOR_REVIEW` | Documentation review | Yes | Human-review policy material. |
| Phase 4S | Present as limited live-review experiment plan | HIGH | `ISOLATE_OUT_OF_PRODUCTION` | No-live governance tests only | Required | Live-review planning, not production-ready. |
| Phase 4T | Live-review runner exists | HIGH | `ISOLATE_OUT_OF_PRODUCTION` | Dry-run/preflight/no-production-mutation tests only | Required | Live-capable. Must stay out until explicit live approval. |
| Phase 4U | Operator rehearsal/runbooks present | MEDIUM | `FREEZE_FOR_REVIEW` | Doc safety tests | Yes | Useful operational docs, but not baseline code. |
| Phase 4V | Dry-run evidence docs/tests present | MEDIUM | `FREEZE_FOR_REVIEW` | Dry-run artifact tests only | Yes | Ensure test artifact paths do not pollute production. |
| Phase 4W | Human review and artifact checklist docs present | MEDIUM | `FREEZE_FOR_REVIEW` | Doc safety tests | Yes | Preserve for governance review. |
| Phase 4X | One-run approval and command packet docs present | HIGH | `ISOLATE_OUT_OF_PRODUCTION` | No-live approval/command safety tests only | Required | Contains live-run preparation material; do not accept into production branch yet. |
| Phase 4Y | Execution readiness and go/no-go docs present | HIGH | `ISOLATE_OUT_OF_PRODUCTION` | No-live readiness tests only | Required | Live execution readiness material. |
| Phase 4Z | First attempt docs/artifacts present | HIGH | `ISOLATE_OUT_OF_PRODUCTION` | No-automatic-execution and incident docs tests | Required | Live-attempt evidence; quarantine. |
| Phase 4Z-A | Failure investigation/provider audit present | HIGH | `ISOLATE_OUT_OF_PRODUCTION` | No-live-retry/provider audit tests | Required | Treat as incident record. |
| Phase 4Z-B | Corrected second attempt package present | HIGH | `ISOLATE_OUT_OF_PRODUCTION` | Corrected package/go-no-go/no-live tests | Required | Preserve but quarantine. |
| Phase 4Z-C | API-key/header validation present | MEDIUM/HIGH | `ISOLATE_OUT_OF_PRODUCTION`; consider later selective `ACCEPT_AFTER_TESTS` | Key-validation unit and client validation contract tests | Required security approval | Useful, but it changed Phase 1 test behavior. Accept only after phase-boundary decision. |
| Phase 4Z-D | Validated third-attempt package and artifacts present | HIGH | `ISOLATE_OUT_OF_PRODUCTION` | No-live-execution, validation-gate, approval-package tests | Required | Completed quarantined run evidence; do not merge into production branch. |

## 6. Phase 4+ File Routing

### Accept After Tests

Accept these only in a clean branch, in small commits, with targeted mocked/dry-run tests:

- `backend/app/integrations/gemini_deep_research/assist_config.py`
- `backend/app/integrations/gemini_deep_research/assist_audit.py`
- `backend/tests/test_gemini_assist_config.py`
- `backend/tests/test_gemini_assist_audit.py`
- `backend/tests/test_gemini_assist_disabled_defaults.py`
- `backend/tests/test_gemini_assist_integration_safety.py`
- `backend/app/integrations/gemini_deep_research/graph_adapter.py`, but only if not wired to `workflow.py`
- `backend/tests/gemini_non_interference_utils.py`
- `backend/tests/test_gemini_non_interference_utils.py`
- `backend/tests/test_gemini_graph_adapter.py`
- `backend/tests/test_gemini_workflow_baseline_fixture.py`

### Freeze For Review

Freeze these for human review before acceptance:

- `docs/gemini_limited_assist_mode_trial_plan.md`
- `backend/app/integrations/gemini_deep_research/assist_node.py`
- `backend/tests/test_gemini_assist_node.py`
- `docs/gemini_graph_wiring_disabled_flag_plan.md`
- `docs/gemini_byte_for_byte_non_interference_test_plan.md`
- `docs/gemini_disabled_graph_wiring_implementation_plan.md`
- Phase 4L disabled graph regression tests, unless Phase 4K is explicitly accepted.
- Phase 4U through Phase 4W governance/runbook/checklist docs.

### Isolate Out Of Production

Keep these on a quarantine or review branch until separately approved:

- `backend/app/integrations/gemini_deep_research/live_review_runner.py`
- `backend/app/integrations/gemini_deep_research/key_validation.py`, until the Phase 1 test drift is deliberately resolved.
- Phase 4M through Phase 4Z-D live-review, command-packet, approval, failure-investigation, and post-run documents.
- `backend/tests/test_gemini_live_review_runner_*.py`
- `backend/tests/test_gemini_phase4x_*.py`
- `backend/tests/test_gemini_phase4y_*.py`
- `backend/tests/test_gemini_phase4z*.py`
- `data/research/gemini_live_review_trials/`

### Block Until Human Review

Do not accept automatically:

- `backend/app/workflow.py` Gemini no-op wiring.
- Any protected-component diff that touches forecast contracts, graph state, quantification, validation, report generation, agent outputs, or graph topology.
- Any code path that can call Gemini live.
- Any env/package change needed only for live Gemini.

### Ignore For Now

Leave out of clean branches:

- `__pycache__/` files.
- `.DS_Store`.
- Any generated local artifacts not needed for mocked tests.
- Local live-run raw or redacted artifacts unless placed in a quarantine branch.

### Defer Final Stage

Do not mix with Gemini acceptance:

- project rename or rebrand
- broad cleanup or archival
- duplicate-file removal
- UI redesign
- CLI/TUI/operator cockpit
- desktop app exploration

## 7. Protected Component Review Plan

Do not accept dirty protected-component changes blindly. Do not accept `workflow.py` Gemini wiring automatically. Do not accept `contracts.py` changes without schema review. Do not accept agent changes without confirming they are unrelated to Gemini or intentionally part of accepted work.

| File | Dirty? | Gemini-Related? | Risk | Required Review | Proposed Action |
|---|---:|---:|---|---|---|
| `backend/app/workflow.py` | Yes | Yes | HIGH | Workflow topology, graph edges, no-op node placement, production non-interference | `BLOCK_UNTIL_HUMAN_REVIEW`; postpone Phase 4K |
| `backend/app/graph/contracts.py` | Yes | No direct Gemini evidence from diff scan | HIGH | Schema owner review for `Signal`, `HorizonForecast`, `FusionResult`, bounds, validators | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/app/graph/state.py` | Yes | No direct Gemini evidence from diff scan | HIGH | ForecastState/reducer/state-key compatibility review | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/app/agents/context_interpreter.py` | Yes | No direct Gemini evidence from diff scan | HIGH | Confirm no Gemini replacement, no direct sidecar injection, no unsafe state writes | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/app/agents/evidence_analyst.py` | Yes | No direct Gemini evidence from diff scan | MEDIUM/HIGH | Confirm unrelated to Gemini or intentionally accepted | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/app/agents/governor.py` | Yes | No direct Gemini evidence from diff scan | HIGH | Safety/governance behavior review | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/app/agents/quantifier_v2.py` | Yes | No direct Gemini evidence from diff scan | HIGH | Probability-fusion and signal-handling review | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/app/agents/report_writer.py` | Yes | No direct Gemini evidence from diff scan | MEDIUM/HIGH | Confirm report output cannot include unapproved Gemini material | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/app/agents/schema_validator.py` | Yes | No direct Gemini evidence from diff scan | HIGH | Contract-validation review | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/app/agents/think_tank_analyst.py` | Yes | No direct Gemini evidence from diff scan | MEDIUM/HIGH | Confirm no unapproved agent-output behavior | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/app/agents/walled_garden_analyst.py` | Yes | No direct Gemini evidence from diff scan | MEDIUM/HIGH | Confirm retrieval isolation remains intact | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/app/llm/client.py` | Yes | Yes, includes Gemini/client/provider changes | HIGH | Provider routing, key handling, live-call gates, logging/redaction | `ISOLATE_OUT_OF_PRODUCTION` until reviewed |
| `backend/app/llm/antigravity.py` | Yes | No direct Gemini evidence from diff scan | MEDIUM | Confirm unrelated runtime behavior | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/requirements.txt` | Yes | Yes, includes `google-generativeai` | MEDIUM/HIGH | Dependency and live-provider surface review | Do not accept until needed and approved |
| root `requirements.txt` | Not observed in diff output | Unknown | UNKNOWN | Confirm presence/status before branch acceptance | `IGNORE_FOR_NOW` unless dirty |
| `package.json` | Dirty in broader status/diff context if present | No direct Gemini evidence from diff scan | MEDIUM | Confirm frontend/package changes unrelated to Gemini | `BLOCK_UNTIL_HUMAN_REVIEW` if dirty |
| `.env.example` | Yes | Indirect provider/key surface | HIGH | Secret hygiene and placeholder review | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `backend/.env.example` | Yes | Potential key/flag surface | HIGH | Secret hygiene and flag-default review | `BLOCK_UNTIL_HUMAN_REVIEW` |
| `.gitignore` | Yes | Potential artifact/secret exclusion surface | MEDIUM/HIGH | Ensure keys/artifacts/cache are ignored; no production artifacts masked accidentally | `BLOCK_UNTIL_HUMAN_REVIEW` |

Protected-diff review requirements:

- Review `workflow.py` as a topology change, not as a normal helper import.
- Review `contracts.py` and `state.py` as schema/compatibility changes, even if not Gemini-related.
- Review agent changes independently from Gemini work; they may be valuable, but they should not be bundled into the Gemini clean branch.
- Review `llm/client.py`, env examples, and requirements as live-provider enablement surfaces.

## 8. Phase 4K Decision

Decision: **postpone Phase 4K.**

Reasoning:

- Phase 4K modifies `workflow.py`, a protected production component.
- It imports `gemini_graph_noop_node`.
- It registers `gemini_assist_noop`.
- It routes the V2 join proceed path through the no-op node before `evidence_analyst`.
- Existing tests characterize this as disabled/no-op, but the graph topology is still changed.

Acceptance conditions for any future Phase 4K review:

- Explicit workflow/topology owner approval.
- Byte-for-byte or canonical non-interference proof from a clean branch.
- Disabled defaults confirmed.
- No Gemini live calls.
- No Gemini writes to `agent_outputs`.
- No mutation of protected `ForecastState` fields.
- No `Signal`, `HorizonForecast`, or `FusionResult` creation by Gemini sidecar.
- Rollback branch/tag created immediately before applying the wiring.

Until those conditions are met, Phase 4K remains `BLOCK_UNTIL_HUMAN_REVIEW`.

## 9. Branch Strategy

Do not run these commands during this audit. They are future operator commands only.

### 9.1 Preserve Current Dirty Checkout

Purpose: preserve the current dirty/untracked state as evidence before any cleanup, reset, branch switch, or selective replay.

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
git status --short
git branch archive/gemini-dirty-evidence-2026-05-17
```

If the operator wants a complete file-level archive outside git, create it explicitly and keep it out of production branches:

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
mkdir -p ../TheSeer-gemini-dirty-evidence-2026-05-17
rsync -a --exclude .git ./ ../TheSeer-gemini-dirty-evidence-2026-05-17/
```

### 9.2 Identify Clean Trusted Baseline

Purpose: locate the clean commit before unreviewed Phase 4+ drift and protected dirty diffs.

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
git log --oneline --decorate --graph --all --max-count=80
git status --short
```

The owner must choose `<TRUSTED_BASELINE_COMMIT>`. If no commit contains Phase 3C cleanly, use the last stable TheSeer commit and replay Phase 1-3C as a controlled patch set.

### 9.3 Create Baseline Branch

Purpose: create an explicit baseline branch from the owner-selected commit.

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
git switch --detach <TRUSTED_BASELINE_COMMIT>
git switch -c baseline/theseer-phase3c-trusted
```

Optional rollback tag:

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
git tag rollback/pre-gemini-selective-acceptance-2026-05-17
```

### 9.4 Create Selective Acceptance Branch

Purpose: replay only approved Phase 1-3C and selected safe Phase 4 test/governance files.

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
git switch -c feature/gemini-shadow-sidecar-clean
```

Replay order:

1. Phase 1 client/models/prompts/storage/README and tests.
2. Reconcile Phase 1 tests with key-validation boundary.
3. Phase 2 normalizer and tests.
4. Phase 3A comparator and tests.
5. Phase 3B runner and tests.
6. Phase 3C evaluation policy, tests, and docs.
7. Optional Phase 4B/4D/4F/4G-H-I acceptance batches after tests.

Do not replay:

- `workflow.py` Phase 4K wiring.
- Live-review runner or key-validation changes unless separately approved.
- Local live artifacts.
- Dirty protected-component changes unrelated to the accepted Gemini phase.

### 9.5 Create Phase 4+ Freeze Review Branch

Purpose: preserve useful but unaccepted Phase 4+ code/docs/tests for review without merging them into the clean sidecar branch.

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
git switch -c review/gemini-phase4-plus-freeze
```

This branch may contain Phase 4 planning docs, assist config/audit/node material, graph adapter work, non-interference tests, and disabled graph tests for review. It should still avoid live secrets and should not be used as production.

### 9.6 Create Live Artifact Quarantine Branch

Purpose: preserve Phase 4Z live-attempt docs/artifacts separately from production and selective acceptance.

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
git switch -c quarantine/gemini-live-artifacts-2026-05-17
```

Quarantine branch rules:

- No API keys.
- No `.env` secrets.
- Redacted artifacts only.
- No production workflow acceptance.
- No live rerun authorization implied.

## 10. Rollback Points

Required rollback points:

| Rollback Point | When To Create | Purpose |
|---|---|---|
| `rollback/pre-gemini-selective-acceptance-2026-05-17` | Before replaying Gemini into the clean branch | Return to clean trusted baseline |
| `rollback/gemini-phase1-3c-clean-2026-05-17` | After Phase 1-3C pass targeted tests | Stable shadow-sidecar checkpoint |
| `rollback/pre-phase4b-acceptance-2026-05-17` | Before accepting Phase 4B | Undo assist config/audit if review fails |
| `rollback/pre-phase4f-graph-adapter-2026-05-17` | Before accepting graph adapter/non-interference utilities | Undo graph-adjacent test work |
| `rollback/pre-phase4k-workflow-wiring-2026-05-17` | Only if Phase 4K is later approved | Undo workflow topology change |
| `rollback/pre-live-review-enable-2026-05-17` | Only before any future live-review branch | Undo live-capable surfaces |

No rollback point authorizes deletion or reset during this planning task. These are future operator actions.

## 11. Required Test Gates

### Clean Phase 1-3C Gate

Required before calling the clean branch trusted:

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
pytest backend/tests/test_gemini_deep_research_client.py -q
pytest backend/tests/test_gemini_evidence_normalizer.py -q
pytest backend/tests/test_gemini_shadow_compare.py -q
pytest backend/tests/test_gemini_shadow_runner.py -q
pytest backend/tests/test_gemini_evaluation_policy.py -q
```

Expected condition:

- All mocked/local tests pass.
- No Gemini live call.
- No internet call.
- No `agent_outputs` write by Gemini.
- No `ForecastState` injection by Gemini.
- No `Signal`, `HorizonForecast`, or `FusionResult` creation by Gemini sidecar.

### Optional Phase 4B/4D Acceptance Gate

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
pytest backend/tests/test_gemini_assist_config.py backend/tests/test_gemini_assist_audit.py -q
pytest backend/tests/test_gemini_assist_disabled_defaults.py backend/tests/test_gemini_assist_integration_safety.py -q
```

### Optional Phase 4F/4G-H-I Acceptance Gate

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
pytest backend/tests/test_gemini_graph_adapter.py -q
pytest backend/tests/test_gemini_non_interference_utils.py -q
pytest backend/tests/test_gemini_workflow_baseline_fixture.py -q
```

### Phase 4K Gate, Only If Later Approved

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this audit
pytest backend/tests/test_gemini_disabled_workflow_wiring.py backend/tests/test_gemini_disabled_graph_regression.py backend/tests/test_gemini_disabled_graph_no_call_no_write.py backend/tests/test_gemini_disabled_graph_barrier_safety.py -q
```

This gate is not sufficient by itself. It must be paired with human workflow-topology approval.

## 12. Owner Approvals Required

| Approval | Required For | Owner Decision |
|---|---|---|
| Baseline approval | Selecting `<TRUSTED_BASELINE_COMMIT>` | Confirm last clean trusted point |
| Phase 1 drift approval | Reconciling fake-key/key-validation test behavior | Decide whether validation belongs in Phase 1 or later |
| Protected schema approval | `contracts.py`, `state.py` | Confirm no unsafe schema/state mutation |
| Workflow topology approval | Phase 4K | Accept, postpone, or reject no-op Gemini graph wiring |
| Agent owner approval | Dirty agent files | Confirm unrelated changes are not bundled into Gemini branch |
| Security approval | API-key validation, env examples, dependencies | Confirm secret hygiene and live-provider gates |
| Live-review approval | Any future Gemini live run | Explicitly authorize one non-production run |
| Artifact retention approval | Phase 4Z live artifacts | Decide quarantine, archive, or discard policy |

## 13. API Key Policy

Current answer: **NO: phase alignment incomplete.**

Do not add `GEMINI_API_KEY` now.

API key may be considered only when all conditions are true:

- Clean selective branch exists.
- Phase 1-3C tests pass.
- Protected-component diffs are reviewed.
- Phase 4K is either absent/postponed or explicitly approved.
- Live-review code is isolated from production.
- Security owner approves key-validation and redaction behavior.
- A single non-production live run is explicitly approved.
- `SEER_USE_GEMINI_DEEP_RESEARCH=1` is intentionally set only in the operator's live-run shell.
- `--allow-live-gemini` is supplied only for the approved live command.
- The key is never written to code, docs, tests, `.env`, logs, artifacts, prompts, shell history, or command text.

Mock tests and dry-run tests do not require `GEMINI_API_KEY`.

## 14. Safest Next Implementation Step

After this plan is reviewed, the safest next implementation step is:

1. Preserve the current dirty checkout as evidence.
2. Select the clean trusted baseline commit.
3. Create a clean selective branch.
4. Reapply Phase 1-3C only.
5. Reconcile Phase 1 client tests with the later key-validation boundary.
6. Run the Phase 1-3C mocked/local test gate.
7. Stop for review before accepting Phase 4+ files.

Do not start with Phase 4K. Do not add a key. Do not run live Gemini. Do not bundle unrelated protected-component changes into the Gemini branch.

## 15. Exact Next Prompt Recommendation

Recommended next IDE prompt:

```text
You are a senior release-governance engineer and Python backend engineer working on TheSeer.

Implement the clean selective Gemini branch preparation only after the operator has created the requested branch. Accept Phase 1-3C first, reconcile the Phase 1 key-validation test drift without weakening secret hygiene, and run only mocked/local Phase 1-3C tests.

Do not modify workflow.py. Do not accept Phase 4K. Do not add GEMINI_API_KEY. Do not run live Gemini. Do not modify protected agents, contracts.py, state.py, env files, or package files unless the operator explicitly approves that file in this branch.
```

## 16. Summary

Path C remains the safest route. The clean production path should accept the shadow-sidecar work through Phase 3C first, then review Phase 4+ in separate batches. Phase 4K workflow wiring, live-review code, API-key validation, and live-attempt artifacts should be frozen or quarantined until explicit human approval.
