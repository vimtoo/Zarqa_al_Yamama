# Gemini Phase 4K Human Review Package

## 1. Executive Summary

Current clean branch: `feature/gemini-shadow-sidecar-clean`.

Current checkpoint tag: `rollback/gemini-clean-sidecar-plus-isolated-assist-2026-05-17`.

Current clean branch tests pass: `304 passed in 1.36s` for the approved mocked/local Gemini Phase 1-4F/4I test bundle.

Current `workflow.py` status: no Gemini workflow wiring is present in the clean branch. The current V2 continuation routes `v2_join_node` `"proceed"` directly to `schema_validator_node`.

Dirty backup status: the dirty evidence backup contains Phase 4K-style wiring. It imports `gemini_graph_noop_node`, registers `gemini_assist_noop`, routes `v2_join_node` `"proceed"` to `gemini_assist_noop`, and adds `gemini_assist_noop -> evidence_analyst`. The backup also contains broader workflow changes unrelated to a minimal no-op Gemini insertion, including additional workflow topology changes and an `evidence_analyst` node in the V2 gate path.

Recommended decision: **postpone Phase 4K** and keep the dirty wiring only as review-branch evidence until a smaller, isolated Phase 4K patch is prepared and reviewed.

Phase 4K should not be accepted now. Even if the adapter itself is no-op by default, inserting a node into LangGraph changes production graph topology. The dirty backup patch is not cleanly limited to Gemini no-op wiring.

API key status: do not add `GEMINI_API_KEY`. It is not needed for this review and remains unsafe to add for production or live use.

## 2. Evidence Reviewed

Current branch files inspected:

- `backend/app/workflow.py`
- `backend/app/graph/contracts.py`
- `backend/app/graph/state.py`
- `backend/app/integrations/gemini_deep_research/graph_adapter.py`
- `backend/app/integrations/gemini_deep_research/assist_node.py`
- `backend/app/integrations/gemini_deep_research/assist_config.py`
- `backend/app/integrations/gemini_deep_research/assist_audit.py`
- `backend/tests/test_gemini_graph_adapter.py`
- `backend/tests/test_gemini_non_interference_utils.py`
- `backend/tests/test_gemini_workflow_baseline_fixture.py`
- `backend/tests/test_gemini_assist_integration_safety.py`

Dirty backup files inspected:

- `../TheSeer-gemini-dirty-evidence-2026-05-17/backend/app/workflow.py`
- `../TheSeer-gemini-dirty-evidence-2026-05-17/backend/tests/test_gemini_disabled_workflow_wiring.py`
- `../TheSeer-gemini-dirty-evidence-2026-05-17/backend/tests/test_gemini_disabled_graph_regression.py`
- `../TheSeer-gemini-dirty-evidence-2026-05-17/backend/tests/test_gemini_disabled_graph_no_call_no_write.py`
- `../TheSeer-gemini-dirty-evidence-2026-05-17/backend/tests/test_gemini_disabled_graph_barrier_safety.py`
- `../TheSeer-gemini-dirty-evidence-2026-05-17/docs/gemini_disabled_graph_wiring_implementation_plan.md`
- `../TheSeer-gemini-dirty-evidence-2026-05-17/docs/gemini_graph_wiring_disabled_flag_plan.md`

Governance docs inspected:

- `docs/gemini_phase_alignment_audit.md`
- `docs/gemini_clean_branch_freeze_plan.md`
- `THESEER_MANIFEST_2026-05-17.md`

Commands run:

- `git status --short`
- `git log --oneline --decorate --graph --max-count=8`
- `test -d ../TheSeer-gemini-dirty-evidence-2026-05-17`
- `rg -n "gemini_assist_noop|gemini_graph_noop_node|GeminiGraphNoopAdapter|gemini_deep_research" ...`
- `diff -u backend/app/workflow.py ../TheSeer-gemini-dirty-evidence-2026-05-17/backend/app/workflow.py | rg -n "..."`
- `python3 -m py_compile backend/app/integrations/gemini_deep_research/graph_adapter.py`
- `PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider ... -q`

No dirty-backup tests were run. They were inspected as evidence only.

## 3. Current Clean Branch State

Accepted phases:

- Phase 1-3C Gemini Deep Research shadow sidecar.
- `key_validation.py` required by the client.
- Isolated assist governance/config/audit/wrapper.
- No-op graph adapter.
- Non-interference utilities and tests.

Current graph status:

- `workflow.py` is not modified by Gemini in the clean branch.
- No `gemini_assist_noop` node is registered in the production graph.
- No Gemini edge exists in the clean graph.
- Current V2 continuation is:

```text
v2_join_node --proceed--> schema_validator_node
schema_validator_node --> evidence_deduper_node
```

Current no-op graph adapter status:

- `GeminiGraphNoopAdapter.run()` returns the original state unchanged when disabled/default blockers exist.
- `gemini_graph_noop_node(state)` calls `GeminiGraphNoopAdapter().run(state)`.
- The adapter has explicit protected-state keys and validation helpers.
- The explicit test-review path is separate from `run()` and is not used by `gemini_graph_noop_node`.

Current API/live status:

- Gemini remains disabled by default.
- No API key is present or needed.
- No live Gemini call was made.
- No production state mutation is accepted.

## 4. Phase 4K Dirty Backup Diff Summary

Concise workflow diff findings:

| Change | Dirty Backup Evidence | Classification | Review Finding |
|---|---|---|---|
| Import `gemini_graph_noop_node` | `workflow.py` line 51 | no-op adapter import | Direct Gemini integration import into protected workflow file. |
| Register `gemini_assist_noop` | `workflow.py` line 457 | topology change | Adds a production graph node, even if node is no-op. |
| Route `v2_join_node` proceed to Gemini node | `workflow.py` lines 637-644 | routing change | Replaces downstream route target for the V2 join proceed path. |
| Add `gemini_assist_noop -> evidence_analyst` edge | `workflow.py` line 646 | downstream-order change | Inserts Gemini no-op before `evidence_analyst`. |
| Add/use `evidence_analyst` in V2 gate path | `workflow.py` lines 46, 460, 647 | downstream-order change | Clean branch currently routes join to `schema_validator_node`, not `evidence_analyst`; this is broader than Gemini no-op wiring. |
| V2 join router semantics changed | dirty lines 685-704 and 1295-1415 | unclear / topology-adjacent | The backup contains idempotent BSP changes and `v2_join_complete_routed`; this is not Phase 4K-only. |
| Broader workflow topology additions | dirty diff includes new profiled nodes and agent paths | unclear / high risk | The dirty backup is not a minimal isolated Gemini patch. |
| Final report / executive summary changes | diff shows `executive_summary` logic changes | unclear | Not part of a no-op Gemini insertion and should not be bundled. |

No evidence showed the `gemini_assist_noop` adapter itself writing `agent_outputs`, creating `Signal`, creating `HorizonForecast`, creating `FusionResult`, or calling Gemini. The risk is the production topology change plus the non-minimal dirty workflow patch.

## 5. Workflow Topology Analysis

Original clean path around the join:

```text
v2_join_node
  proceed -> schema_validator_node
  wait    -> END

schema_validator_node
  -> evidence_deduper_node
  -> independence_analyzer_node
  -> qualitative_quantifier
  -> quantifier_v2
  -> critic_v2
  -> governor
  -> format_output
```

Dirty Phase 4K-style path:

```text
v2_join_node
  proceed -> gemini_assist_noop
  wait    -> END

gemini_assist_noop
  -> evidence_analyst
  -> schema_validator_node
```

Topology conclusion:

- The path changes graph topology even if state is unchanged.
- The no-op node is state-neutral in the isolated adapter tests, but insertion into LangGraph still changes execution ordering, node scheduling, observability, possible timing, and failure surface.
- The dirty backup also introduces `evidence_analyst` before `schema_validator_node`, which is not present in the clean branch's V2 continuation. That is a separate workflow behavior change and should not be accepted under a narrow Phase 4K label.
- Topology change alone is operationally meaningful because LangGraph node registration and routing can affect execution traces, routing semantics, profiling, barriers, and downstream inputs.

Answers to required review questions:

1. Phase 4K changes import, node registration, V2 proceed route, and a new edge from Gemini no-op to `evidence_analyst`.
2. Dirty backup lines: import at 51, node at 457, route at 641, edge at 646.
3. `gemini_assist_noop` would sit after `v2_join_node` and before `evidence_analyst`.
4. The isolated adapter is no-op by default in `run()` because default config blockers return the original state.
5. `gemini_graph_noop_node` returns `GeminiGraphNoopAdapter().run(state)`, and disabled/default adapter tests show state identity and protected-key preservation.
6. The no-op wiring does not call Gemini by itself.
7. The no-op wiring does not call `assist_node.py` through `GeminiAssistNodeWrapper.run()` by default.
8. The no-op wiring does not call `client.py` by default.
9. The no-op wiring does not call `live_review_runner.py`.
10. The no-op adapter does not write `agent_outputs` by default.
11. The no-op adapter is designed not to mutate protected `ForecastState` keys.
12. The no-op adapter source does not instantiate `Signal`, `HorizonForecast`, or `FusionResult`.
13. Dirty backup tests assert Gemini is not added to the `v2_join_node` barrier-key map, but the dirty workflow also changes join/router behavior outside Gemini.
14. Dirty backup changes downstream path by placing `evidence_analyst` after Gemini no-op and before schema validation; this can affect inputs relative to the clean branch.
15. Yes, it affects graph topology and downstream order.
16. Yes, topology changes production behavior surface even if the state object is returned unchanged.
17. Dirty backup tests provide static and adapter-level proof for no-call/no-write/no-mutation behavior.
18. Missing: full clean-branch production workflow equivalence, live graph execution equivalence, reducer side-effect proof, and isolated minimal patch proof.
19. Rollback requires a pre-implementation tag and a single-file `workflow.py` restore if rejected.
20. Required approvals: workflow/topology, security, protected-state, and test-evidence approval.
21. Phase 4K should not be accepted now.

## 6. Safety Matrix

| Safety Question | Evidence | Current Answer | Risk | Required Mitigation |
|---|---|---|---|---|
| No live Gemini call | Adapter `run()` no-ops by default; dirty tests monkeypatch client calls | Likely yes for no-op adapter | LOW for adapter, MEDIUM in graph | Run disabled graph no-call tests from a minimal clean patch. |
| No assist_node execution | `run()` returns before review path; dirty no-call test monkeypatches wrapper | Likely yes by default | LOW | Keep `run_test_review_mode()` separate from graph node. |
| No client execution | `gemini_graph_noop_node` does not instantiate client path | Likely yes | LOW | Add clean-branch graph test that fails on `GeminiDeepResearchClient.run_research`. |
| No live_review_runner execution | No import in workflow or adapter | Yes | LOW | Keep `live_review_runner.py` out of Phase 4K. |
| No agent_outputs write | Adapter protected keys include `agent_outputs`; tests assert no Gemini agent output | Likely yes | LOW/MEDIUM | Verify in full disabled graph run, not only adapter call. |
| No ForecastState protected-key mutation | Adapter validates protected keys in optional paths | Likely yes for adapter | MEDIUM | Canonical full-state comparison before/after graph node. |
| No Signal creation | Adapter source checks show no `Signal(` | Yes for adapter | LOW | Static test plus runtime object-creation guard if feasible. |
| No HorizonForecast creation | Adapter source checks show no `HorizonForecast(` | Yes for adapter | LOW | Static test plus runtime guard if feasible. |
| No FusionResult creation | Adapter source checks show no `FusionResult(` | Yes for adapter | LOW | Static test plus runtime guard if feasible. |
| No raw Gemini report in state | No-op path does not create review artifact | Likely yes | LOW | Assert no `gemini_assist_review` and no raw report string in disabled graph output. |
| No final_report modification | Disabled graph regression tests compare fixture report | Partially proven | MEDIUM | Need full workflow-derived comparison, not only fixture. |
| No executive_summary modification | Disabled graph regression tests compare fixture summary | Partially proven | MEDIUM | Need full workflow-derived comparison. |
| No evidence_analyst input mutation | Dirty backup inserts node before `evidence_analyst` | Not proven | HIGH | Compare inputs to downstream node in a minimal clean patch. |
| No v2_join_node barrier-key mutation | Dirty tests assert no Gemini in barrier map | Partially proven | MEDIUM | Review actual clean patch; dirty backup has broader join changes. |
| No state reducer incompatibility | No full graph execution evidence in backup tests | Not proven | HIGH | Add reducer/graph execution regression if Phase 4K proceeds. |
| No schema/contract drift | Clean branch did not copy dirty contracts/state | Yes for current branch | MEDIUM for future wiring | Keep contracts/state untouched. |
| No latency impact | No-op node adds a graph hop | Not proven | MEDIUM | Benchmark or assert negligible node runtime in disabled path. |
| No dependency impact | Workflow import uses existing graph adapter | Likely yes | LOW | Do not add package files. |
| No test-only proof gap | Dirty tests are mostly static/fixture/adapter checks | Gap exists | HIGH | Add full clean disabled graph regression before acceptance. |
| Easy rollback | Single intended file is `workflow.py`, but dirty backup has broader changes | Only if minimal patch | MEDIUM/HIGH | Require pre-implementation rollback tag and isolated diff. |

## 7. Test Evidence Review

### `test_gemini_disabled_workflow_wiring.py`

What it checks:

- Static workflow source contains the Gemini no-op import, node registration, proceed route, and edge.
- Barrier-key logic does not include Gemini.
- `gemini_graph_noop_node` returns state unchanged.
- No Gemini keys, no `agent_outputs` write, no forecast contract object creation, and no artifact writes by the adapter.
- The test explicitly says its structural tests do not import workflow.

What it proves:

- The intended static wiring shape exists in the dirty backup.
- The isolated adapter remains no-op for direct calls.
- The adapter does not call the Gemini client or assist wrapper in direct tests.

What it does not prove:

- It does not prove the full LangGraph runtime output is identical.
- It does not prove reducer behavior or scheduling is unchanged.
- It does not prove `evidence_analyst` receives equivalent inputs.
- It does not isolate Gemini wiring from the other dirty workflow changes.

Should it be copied later:

- Yes, but only after editing it against a minimal clean Phase 4K patch.

Should it be modified later:

- Yes. It should compare against the clean branch's actual current path and avoid assuming unrelated dirty workflow changes.

### `test_gemini_disabled_graph_regression.py`

What it checks:

- `gemini_graph_noop_node` preserves a workflow-shaped baseline fixture.
- Protected fields such as `agent_outputs`, `fusion_result_v2`, `horizon_forecasts`, `critic_result`, `governor_result`, `executive_summary`, and `final_report` remain canonically identical.
- Negative tests prove the comparison catches Gemini keys, Gemini agent output, and protected-field mutation.

What it proves:

- Direct adapter calls preserve a representative fixture.
- Canonical comparison utilities catch obvious protected-state changes.

What it does not prove:

- It is not a full production workflow execution.
- It does not prove LangGraph topology insertion is harmless.
- It does not prove timing, reducers, or downstream node inputs are unchanged.

Should it be copied later:

- Yes, as part of a disabled graph regression package.

Should it be modified later:

- Yes. It should be paired with a real graph construction or execution test if feasible.

### `test_gemini_disabled_graph_no_call_no_write.py`

What it checks:

- Direct no-op adapter call does not call client, assist wrapper, normalizer, comparator, or shadow runner.
- No artifacts are written to Gemini artifact directories.
- No obvious HTTP calls are made.
- No audit storage helpers are called.
- No raw result, evidence pack, shadow run, or assist trial files are created.

What it proves:

- The direct adapter path is inert.
- The no-op function does not accidentally execute the Gemini research stack.

What it does not prove:

- It does not prove the workflow graph never calls those components after a real route.
- It does not prove production E2E equivalence.
- HTTP monkeypatching is best-effort and not a formal network sandbox.

Should it be copied later:

- Yes, with clean-branch paths and no dirty backup dependencies.

Should it be modified later:

- Yes. Add graph-level invocation coverage if Phase 4K is implemented.

### `test_gemini_disabled_graph_barrier_safety.py`

What it checks:

- Exactly one Gemini no-op node, one proceed-route target, and one edge.
- No Gemini entry in barrier-key maps, active-agent logic, skipped-agent logic, or expected output keys.
- Downstream ordering around `evidence_analyst`, schema validation, deduplication, independence analysis, quantifier, critic, governor, and report writer.
- Workflow imports only `gemini_graph_noop_node`, not client/wrapper/normalizer/comparator/runner.

What it proves:

- Static barrier and route invariants are represented in the dirty backup.
- Gemini is not added as a parallel branch before the join.

What it does not prove:

- It does not prove runtime equivalence.
- It does not prove state reducers behave identically.
- It assumes the dirty backup workflow structure, which differs from the clean branch.

Should it be copied later:

- Yes, but only after reworking it for the minimal clean Phase 4K patch.

Should it be modified later:

- Yes. It must not accidentally accept the broader dirty workflow rewrite.

## 8. Decision Options

| Option | Benefit | Risk | Required Tests | Required Approvals | Rollback Complexity | Recommendation |
|---|---|---|---|---|---|---|
| A: Accept Phase 4K now | Moves wiring forward quickly | High: modifies protected workflow, dirty patch not isolated, topology changes production graph | All current 304 plus disabled workflow tests plus full graph equivalence | Workflow, security, protected-state | Medium/high because dirty diff is broad | Not recommended |
| B: Postpone Phase 4K and keep graph untouched | Preserves clean branch and production graph | Delays graph rehearsal | Current 304 remains sufficient | None beyond recording decision | Low | Recommended |
| C: Reject Phase 4K entirely | Keeps Gemini workflow-independent only | May defer useful future review-only path | Current shadow/assist wrapper tests | Governance approval | Low | Acceptable but premature |
| D: Rework into runtime-disabled feature flag not inserted until explicitly enabled | Safer future design | Requires new design and tests | Adapter, config, graph construction, disabled equivalence | Workflow, security, protected-state | Medium | Good future alternative |
| E: Keep Phase 4K only in a separate review branch | Preserves evidence without production impact | Requires branch discipline | Disabled graph tests in review branch | Workflow review owner | Low/medium | Recommended with B |

Preferred decision: **Option B now, with Option E for evidence preservation.**

## 9. Recommendation

Recommendation: **postpone Phase 4K**.

Do not accept Phase 4K into the clean branch now.

Reason:

- The current clean branch already has the isolated no-op graph adapter and 304 local/mocked tests passing.
- The current clean branch deliberately keeps `workflow.py` untouched.
- The dirty backup proves a possible shape but is not a minimal Phase 4K-only diff.
- The dirty backup introduces broader workflow topology changes, including `evidence_analyst` placement and V2 join/router changes.
- Static and fixture tests are useful but do not prove full production graph equivalence.

Recommended handling:

- Keep Phase 4K in a separate review branch or frozen evidence package.
- If Phase 4K is reconsidered, implement a minimal clean-branch patch only after approval.
- The minimal patch must not include unrelated workflow, agent, state, contract, package, or live-run changes.

## 10. Acceptance Criteria For Future Phase 4K

Phase 4K may be considered only if all are true:

1. Current clean branch tests pass.
2. Dirty workflow diff is reviewed and approved.
3. The future implementation is a minimal isolated diff, not the broad dirty backup workflow.
4. The no-op adapter is proven to return byte-for-byte or canonically identical protected state.
5. No Gemini client call occurs.
6. No `assist_node.py` call occurs.
7. No `live_review_runner.py` call occurs.
8. No network call occurs.
9. No `agent_outputs` write occurs.
10. No protected `ForecastState` keys are added or modified.
11. No `Signal`, `HorizonForecast`, or `FusionResult` is created.
12. `evidence_analyst` receives equivalent inputs, or any intentional insertion before it is separately approved.
13. `v2_join_node` barrier behavior is unchanged.
14. Full disabled graph regression tests pass.
15. Rollback tag exists before implementation.
16. Human workflow/topology approval is recorded.
17. Human security approval is recorded.
18. Human protected-state approval is recorded.
19. API key remains absent.
20. Live Gemini remains disabled.

## 11. Rollback Plan If Implemented Later

Future operator commands only. Do not run these as part of this review package.

Create rollback tag before implementation:

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this review
git status --short
git tag rollback/pre-phase4k-workflow-wiring-2026-05-17
```

Expected implementation file list if minimal:

```text
backend/app/workflow.py
backend/tests/test_gemini_disabled_workflow_wiring.py
backend/tests/test_gemini_disabled_graph_regression.py
backend/tests/test_gemini_disabled_graph_no_call_no_write.py
backend/tests/test_gemini_disabled_graph_barrier_safety.py
```

Tests to run before implementation:

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this review
PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider \
  backend/tests/test_gemini_deep_research_client.py \
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
  backend/tests/test_gemini_workflow_baseline_fixture.py -q
```

Tests to run after implementation:

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this review
PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider \
  backend/tests/test_gemini_deep_research_client.py \
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
  backend/tests/test_gemini_disabled_workflow_wiring.py \
  backend/tests/test_gemini_disabled_graph_regression.py \
  backend/tests/test_gemini_disabled_graph_no_call_no_write.py \
  backend/tests/test_gemini_disabled_graph_barrier_safety.py -q
```

Restore previous `workflow.py` if rejected:

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this review
git restore --source rollback/pre-phase4k-workflow-wiring-2026-05-17 -- backend/app/workflow.py
```

Remove graph-wiring tests if implementation is rejected:

```bash
# FUTURE OPERATOR COMMAND ONLY - do not run in this review
git rm backend/tests/test_gemini_disabled_workflow_wiring.py
git rm backend/tests/test_gemini_disabled_graph_regression.py
git rm backend/tests/test_gemini_disabled_graph_no_call_no_write.py
git rm backend/tests/test_gemini_disabled_graph_barrier_safety.py
```

No data migration should be needed if Phase 4K remains truly state-neutral and writes no artifacts by default.

## 12. Human Approval Checklist

- [ ] Workflow/topology owner approval
- [ ] Security owner approval
- [ ] Protected-state owner approval
- [ ] Test evidence reviewed
- [ ] Rollback tag created
- [ ] API key confirmed absent
- [ ] Live Gemini confirmed disabled
- [ ] No `agent_outputs` write confirmed
- [ ] No `ForecastState` protected-key mutation confirmed
- [ ] No `Signal`/`HorizonForecast`/`FusionResult` creation confirmed
- [ ] Decision recorded

## 13. Exact Next Prompt Recommendation

Because the recommendation is postpone, use this next prompt:

```text
You are a senior release-governance engineer working on TheSeer.

Create a Phase 4K review-branch/freeze package only. Do not modify the clean selective branch production workflow. Preserve the dirty Phase 4K evidence in a separate review branch or documentation package, isolate the minimal intended workflow diff from unrelated dirty workflow changes, and prepare a future approval checklist.

Do not modify workflow.py on the clean branch. Do not add GEMINI_API_KEY. Do not enable Gemini. Do not run live Gemini. Do not add Phase 4K graph wiring unless a human workflow/topology owner explicitly approves a separate implementation prompt.
```
