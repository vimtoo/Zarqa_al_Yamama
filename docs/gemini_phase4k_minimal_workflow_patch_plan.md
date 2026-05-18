# Phase 4K Minimal Disabled Workflow Patch Plan

Date: 2026-05-18

## 1. Executive Summary

This is a planning document only.

`workflow.py` is not modified in this phase. Gemini remains isolated in `backend/app/integrations/gemini_deep_research/`. The future Phase 4K patch, if explicitly approved later, must be disabled/no-op by default.

Production output must remain byte-for-byte identical when disabled. The intended result of this phase is a bounded, human-reviewable plan and approval gate, not graph wiring.

## 2. Current Verified Safe State

The current verified safe state is:

- `main` is clean after the Gemini selective merge.
- Rollback tag exists: `rollback/gemini-merged-clean-main-2026-05-18`.
- 304 mocked/local Gemini safety tests passed in the post-merge audit.
- Phase 4H is complete: canonical serialization and non-interference utilities exist and pass.
- Phase 4I is complete: workflow-shaped baseline fixture tests exist and pass.
- `workflow.py` has no Gemini imports.
- `graph_adapter.py` is not wired into LangGraph.
- No production state mutation exists from the Gemini package.
- No `agent_outputs` writes exist from Gemini.
- No `Signal`, `HorizonForecast`, or `FusionResult` creation exists in the Gemini package.
- Phase 4K remains documented only and is not approved.

## 3. Proposed Future Minimal Patch Scope

A future Phase 4K implementation may be considered only as exactly four conceptual workflow changes:

1. Import `gemini_graph_noop_node`.
2. Register node: `workflow.add_node("gemini_assist_noop", gemini_graph_noop_node)`.
3. Route the existing V2 join proceed path through `gemini_assist_noop`.
4. Add edge: `gemini_assist_noop -> schema_validator_node`.

Do not apply these changes in Phase 4K-A.

Phase 4K-B topology mapping confirmed that the current existing next node is `schema_validator_node`. Do not infer a different target from the dirty backup.

## 4. Exact Future Diff Sketch

ILLUSTRATIVE ONLY — DO NOT APPLY WITHOUT OPERATOR APPROVAL

This sketch is non-executable and must not be copied blindly. It intentionally avoids exact line numbers because the current `workflow.py` must be inspected immediately before implementation.

```diff
diff --git a/backend/app/workflow.py b/backend/app/workflow.py
--- a/backend/app/workflow.py
+++ b/backend/app/workflow.py
@@
+from app.integrations.gemini_deep_research.graph_adapter import gemini_graph_noop_node

@@
 # Existing graph node registrations
+workflow.add_node("gemini_assist_noop", gemini_graph_noop_node)

@@
 workflow.add_conditional_edges(
     "v2_join_node",
    self._join_router_v2,
    {
-        "proceed": "schema_validator_node",
+        "proceed": "gemini_assist_noop",
         "wait": END,
     },
 )

+workflow.add_edge("gemini_assist_noop", "schema_validator_node")
```

Approval requirement: `workflow.py must not be modified without approval`.

## 5. Evidence Analyst Placement Warning

The previous dirty backup reportedly inserted or moved `evidence_analyst` before `schema_validator_node`.

That is out of scope for Phase 4K unless separately approved.

Phase 4K must not introduce unrelated workflow topology changes. If the future no-op node needs to connect to `evidence_analyst`, first confirm that `evidence_analyst` is already the existing route after `v2_join_node`. If it is not already the existing route, stop and produce a separate topology review.

Do not bundle `evidence_analyst` placement, V2 join barrier changes, router semantics changes, report generation changes, or any existing-agent changes into a minimal Gemini no-op workflow patch.

## 6. What Phase 4K Must NOT Do

Phase 4K must not do any of the following:

- no Gemini client call
- no live API request
- no `ForecastState` mutation
- no `agent_outputs` write
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
- no `ReportWriter` trusted input change
- no environment variable or API key requirement
- no package or dependency change
- no live Gemini execution

## 7. Acceptance Criteria

Phase 4K may be implemented only if every criterion is satisfied:

- Operator approval is recorded before implementation.
- Workflow/topology reviewer approval is recorded before implementation.
- Security reviewer approval is recorded before implementation.
- Protected-state reviewer approval is recorded before implementation.
- Rollback tag is created before implementation.
- `workflow.py` diff is minimal and isolated.
- `workflow.py` diff contains only the approved no-op import, node registration, route target, and edge.
- The future node is disabled/no-op by default.
- Production output remains byte-for-byte identical when disabled.
- Protected keys are unchanged.
- No Gemini keys are added to disabled state.
- No Gemini `agent_outputs` entry appears.
- No live network call occurs.
- No environment key is required.
- `GEMINI_API_KEY` remains absent.
- Live Gemini remains disabled.
- No `Signal`, `HorizonForecast`, or `FusionResult` is created.
- `v2_join_node` barrier behavior is unchanged.
- The existing downstream node receives equivalent inputs.
- Full relevant Gemini safety regression slice passes.
- Full disabled graph wiring tests pass if created later.

## 8. Test Plan for Future Implementation

Before any future implementation, run the current safety regression slice:

```bash
pytest backend/tests/test_gemini_graph_adapter.py \
       backend/tests/test_gemini_non_interference_utils.py \
       backend/tests/test_gemini_workflow_baseline_fixture.py \
       backend/tests/test_gemini_assist_disabled_defaults.py \
       backend/tests/test_gemini_assist_integration_safety.py -q
```

Future implementation should add a test file:

```text
backend/tests/test_gemini_phase4k_disabled_workflow_wiring.py
```

That future test should verify:

- `workflow.py` imports the no-op node only after approval.
- Disabled route preserves protected state.
- No Gemini state keys are added.
- No Gemini `agent_outputs` entry appears.
- No live Gemini client is instantiated.
- Graph topology change is limited to the approved no-op node.
- The existing next node after `v2_join_node`, `schema_validator_node`, is preserved behind the no-op hop.
- No `evidence_analyst` route is introduced.
- `v2_join_node` barrier keys do not include Gemini.

Do not create implementation wiring tests until the operator approval record is approved. Phase 4K-A includes only static documentation validation.

## 9. Rollback Plan

Future operator commands only. Do not run these in Phase 4K-A.

Create a pre-implementation tag before touching `workflow.py`:

```bash
# FUTURE OPERATOR COMMAND ONLY
git status --short
git tag rollback/pre-phase4k-minimal-workflow-wiring-2026-05-18
```

If rollback is needed:

```bash
# FUTURE OPERATOR COMMAND ONLY
git restore --source rollback/pre-phase4k-minimal-workflow-wiring-2026-05-18 -- backend/app/workflow.py
```

Rerun the regression slice:

```bash
# FUTURE OPERATOR COMMAND ONLY
pytest backend/tests/test_gemini_graph_adapter.py \
       backend/tests/test_gemini_non_interference_utils.py \
       backend/tests/test_gemini_workflow_baseline_fixture.py \
       backend/tests/test_gemini_assist_disabled_defaults.py \
       backend/tests/test_gemini_assist_integration_safety.py -q
```

Confirm `workflow.py` no longer imports Gemini after rollback:

```bash
# FUTURE OPERATOR COMMAND ONLY
grep -n "gemini_graph_noop_node\|gemini_assist_noop\|gemini_deep_research" backend/app/workflow.py
```

Expected rollback confirmation: no matches.

## 10. Operator Approval Gate

Implementation cannot begin until Qusai explicitly approves in chat or in a signed approval record.

Until approval is recorded:

- Phase 4K status is `NOT APPROVED`.
- `workflow.py` must remain untouched.
- Gemini must remain isolated.
- No Gemini node or edge may be added to LangGraph.
- No API key may be added.
- No live Gemini execution may occur.
