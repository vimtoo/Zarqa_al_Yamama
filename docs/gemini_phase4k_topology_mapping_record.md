# Phase 4K-C Topology Mapping Record

## 1. Executive Summary

This is documentation only.

`workflow.py` was not modified. Phase 4K remains `NOT APPROVED`.

The current `v2_join_node` `"proceed"` target is `schema_validator_node`. The only topology-preserving future insertion eligible for operator approval is:

```text
v2_join_node -> gemini_assist_noop -> schema_validator_node
```

No Gemini workflow wiring exists in the current `workflow.py`.

## 2. Current Git Status

Command: `git status --short`

```text
?? backend/tests/test_gemini_phase4k_planning_docs.py
?? docs/gemini_phase4k_minimal_workflow_patch_plan.md
?? docs/gemini_phase4k_operator_approval_record.md
?? docs/gemini_post_merge_phase_alignment_audit.md
```

Command: `git diff --name-only`

```text

```

Result: there are untracked Phase 4K-A/post-merge documentation artifacts, but no tracked file diffs.

## 3. Current V2 Join Route

Exact current route:

```text
v2_join_node --proceed--> schema_validator_node
```

Current `add_conditional_edges` block from `backend/app/workflow.py`:

```python
workflow.add_conditional_edges(
    "v2_join_node",
    self._join_router_v2,
    {
        "proceed": "schema_validator_node",
        "wait": END
    }
)
```

The current router returns `"proceed"` when `state.get("v2_join_ready")` is true and `"wait"` otherwise.

## 4. Current Downstream Route

Current downstream route:

```text
v2_join_node --proceed--> schema_validator_node
schema_validator_node --> evidence_deduper_node
evidence_deduper_node --> independence_analyzer_node
independence_analyzer_node --> qualitative_quantifier
qualitative_quantifier --> quantifier_v2
quantifier_v2 --> critic_v2
critic_v2 --proceed--> governor
governor --> format_output
format_output --> report_writer or END
```

This route preserves the existing mandatory V2 gate chain. Any future Phase 4K no-op insertion must preserve the same downstream target behind the no-op hop.

## 5. Evidence Analyst Finding

`evidence_analyst` is not present in current `workflow.py`.

Any future route to `evidence_analyst` would be a new topology change. `evidence_analyst` insertion is out of scope for Phase 4K.

Dirty backup topology must not be copied. The dirty backup reportedly routed `gemini_assist_noop` to `evidence_analyst`, but that is not topology-preserving against the current clean workflow because the current route goes directly to `schema_validator_node`.

## 6. Approved Future Patch Shape for Consideration

The only future Phase 4K patch eligible for operator approval is:

```text
v2_join_node --proceed--> gemini_assist_noop
gemini_assist_noop --> schema_validator_node
```

Do not implement this patch in Phase 4K-C.

This shape preserves the existing proceed target by placing the no-op node between `v2_join_node` and `schema_validator_node`.

## 7. Topology Risk Assessment

- Barrier semantics should remain unchanged only if `gemini_assist_noop` is not added to barrier keys, active-agent logic, skipped-agent logic, or expected `agent_outputs`.
- State shape should remain unchanged only if `gemini_graph_noop_node` returns state unchanged.
- Protected keys must remain unchanged.
- Schema validation must not be bypassed; `schema_validator_node` must remain the immediate downstream production gate after the no-op hop.
- Report generation path must remain unchanged: `governor -> format_output -> report_writer or END`.
- Any deviation from `v2_join_node -> gemini_assist_noop -> schema_validator_node` requires separate topology review.
- Any introduction of `evidence_analyst` requires separate topology review.
- Any dirty-backup workflow/router/barrier change outside the minimal no-op insertion is out of scope.

## 8. Approval Readiness

Phase 4K may proceed to operator approval only for:

```text
v2_join_node -> gemini_assist_noop -> schema_validator_node
```

Phase 4K is still `NOT APPROVED`.

Implementation remains blocked until Qusai explicitly approves in chat or in a signed approval record.

## 9. Required Future Implementation Tests

Future implementation test file:

```text
backend/tests/test_gemini_phase4k_disabled_workflow_wiring.py
```

It must verify:

- `workflow.py` imports only `gemini_graph_noop_node` from `graph_adapter`.
- `workflow.add_node` registers only `gemini_assist_noop` as the new Gemini node.
- `v2_join_node` `"proceed"` routes to `gemini_assist_noop`.
- `gemini_assist_noop` routes to `schema_validator_node`.
- No `evidence_analyst` route is introduced.
- No Gemini client is imported.
- No `GeminiAssistNodeWrapper` is imported.
- No live runner is imported.
- No `agent_outputs` write appears.
- No protected state mutation appears.
- No Gemini state keys appear in disabled execution.
- Byte-for-byte disabled output remains identical.
