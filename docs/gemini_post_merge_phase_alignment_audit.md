# Gemini Deep Research Post-Merge Phase Alignment Audit

**Date:** 2026-05-18 06:42 +03:00  
**Scope:** Read-only post-merge audit. No source code, workflow files, environment files,
package files, tests, API keys, live Gemini calls, internet calls, file moves, or
production behavior changes were made.  
**Auditor:** Antigravity (Lulu) — automated read-only inspection.  
**Trigger:** PR #1 merged (`feature/gemini-shadow-sidecar-clean → main`). Clean rollback
tag `rollback/gemini-merged-clean-main-2026-05-18` created and pushed.

---

## 1. Executive Summary

The post-merge `main` is **clean and safe** as of the merge tag.

- **Regression slice:** 304/304 passed (1.31s) — confirmed by re-running the verified slice now.
- **`workflow.py` Gemini import status:** `OK: no Gemini imports` — confirmed by live grep.
- **Working tree:** clean (per handoff context).
- **Rollback tag:** `rollback/gemini-merged-clean-main-2026-05-18` — pushed.

**Phase status at a glance:**

| Phase | Status |
|---|---|
| 1 – 3C (shadow sidecar) | ✅ Merged and passing |
| 4 / 4B / 4C / 4D / 4E | ✅ Merged and passing |
| 4F (no-op graph adapter) | ✅ Merged and passing |
| **4G (byte-for-byte test plan)** | ✅ Docs present |
| **4H (canonical serialization utils)** | ✅ **Complete** — `gemini_non_interference_utils.py` + tests pass |
| **4I (workflow-shaped baseline fixtures)** | ✅ **Complete** — `test_gemini_workflow_baseline_fixture.py` + tests pass |
| **4K (no-op workflow wiring)** | ⚠️ **NOT in main** — documented, human approval required before implementation |

**Current `workflow.py` status:** Untouched — no Gemini node, no Gemini edge, no Gemini import.  
**No production state mutation exists.** No `agent_outputs`, `Signal`, `HorizonForecast`,
or `FusionResult` write exists in the merged Gemini package.

**Recommended next phase:** Phase 4K planning/approval — a minimal, isolated, disabled
`workflow.py` no-op wiring — **requires explicit operator approval before any code change**.

---

## 2. Current Git / Merge Status

| Item | Value |
|---|---|
| Merge commit | PR #1: `feature/gemini-shadow-sidecar-clean → main` |
| HEAD | `main` (synced to `origin/main`) |
| Rollback tag | `rollback/gemini-merged-clean-main-2026-05-18` |
| Working tree | Clean |
| Regression tests | **304 passed, 0 failed** |
| `workflow.py` Gemini imports | **None confirmed** |
| Protected files modified | **None** |

---

## 3. Implemented Phase Inventory

| Phase | Intended Purpose | Current Artifact(s) | Status | Production Impact |
|---|---|---|---|---|
| Phase 1 | Gemini API client wrapper | `client.py`, `models.py`, `prompts.py`, `storage.py`, `key_validation.py` | ✅ Merged | None — isolated; disabled by default |
| Phase 2 | EvidencePack normalizer | `normalizer.py`, `test_gemini_evidence_normalizer.py` | ✅ Merged | None |
| Phase 3A | Shadow comparison engine | `shadow_compare.py`, `test_gemini_shadow_compare.py` | ✅ Merged | None |
| Phase 3B | Workflow-independent shadow runner | `shadow_runner.py`, `test_gemini_shadow_runner.py` | ✅ Merged | None |
| Phase 3C | Shadow evaluation policy | `evaluation_policy.py`, `test_gemini_evaluation_policy.py` | ✅ Merged | None |
| Phase 4 | Assist-mode trial plan (docs) | `gemini_deep_research_integration_plan.md` | ✅ Docs only | None |
| Phase 4B | Assist config and audit models | `assist_config.py`, `assist_audit.py` | ✅ Merged | None |
| Phase 4C | Isolated assist-node wrapper | `assist_node.py` | ✅ Merged | None — review-only by default |
| Phase 4D | Disabled-defaults/safety tests | `test_gemini_assist_disabled_defaults.py`, `test_gemini_assist_integration_safety.py` | ✅ Merged | None |
| Phase 4E | Graph wiring disabled-flag plan (docs) | `gemini_graph_wiring_disabled_flag_plan.md` | ✅ Docs only | None |
| Phase 4F | Isolated no-op graph adapter | `graph_adapter.py`, `test_gemini_graph_adapter.py` | ✅ Merged | None — adapter returns state unchanged |
| Phase 4G | Byte-for-byte non-interference test plan (docs) | `gemini_byte_for_byte_non_interference_test_plan.md` | ✅ Docs only | None |
| **Phase 4H** | Canonical serialization and baseline fixture utilities | `gemini_non_interference_utils.py`, `test_gemini_non_interference_utils.py` | ✅ **Complete** | None — test-only utilities |
| **Phase 4I** | Workflow-shaped baseline fixture tests | `test_gemini_workflow_baseline_fixture.py` | ✅ **Complete** | None — fixture-only, no live workflow import |
| **Phase 4K** | Disabled/no-op `workflow.py` wiring | Not in main — documented in `gemini_phase4k_human_review_package.md` | ⚠️ **Postponed — awaiting approval** | Would add a no-op node to LangGraph graph topology |

> **Note on Phase 4Z-D live run:** A successful non-production live Gemini research run was
> completed under Phase 4Z-D approval (`run_id: phase4t-policy-1-826f244e-7115-48df-804c-963c5cf77962`,
> `status: quarantined`, `live_completed: true`, 79 grounding sources). Artifacts are
> stored locally under `data/research/gemini_live_review_trials/phase4zd_third_attempt_001/`.
> That run is review-only and not wired into production in any way.

---

## 4. Phase 4H Status

**Phase 4H is fully implemented and passing.**

File: `backend/tests/gemini_non_interference_utils.py` (402 lines, 13.6 KB)

Provides:
- `canonical_json_dump()` / `canonicalize_value()` / `canonicalize_state()` — deterministic
  JSON serialization stripping nondeterministic fields (timestamps, UUIDs, etc.)
- `canonicalize_report()` — normalizes markdown/report text
- `assert_canonical_equal()` / `diff_canonical()` — canonical comparison with unified diff output
- `assert_protected_keys_unchanged()` — asserts `PROTECTED_STATE_KEYS` are not added, removed,
  or changed
- `assert_no_gemini_keys()` / `assert_no_agent_output_for_gemini()` — safety assertions for
  disabled-mode state
- `capture_artifact()` / `load_artifact()` / `capture_report_artifact()` / `load_report_artifact()` —
  deterministic fixture I/O helpers
- `PROTECTED_STATE_KEYS` set: `agent_outputs`, `signals`, `horizon_forecasts`, `fusion_result`,
  `fusion_result_v2`, `final_report`, `executive_summary`, `report_path`, `governor_result`,
  `critic_result`, `quantifier_result`, `deduped_evidence`, `evidence_clusters`,
  `independence_summary`, `qualitative_forecast`, `qualitative_forecast_label`
- `GEMINI_STATE_KEYS` and `GEMINI_AGENT_OUTPUT_KEYS` for disabled-mode guard assertions

Test file: `backend/tests/test_gemini_non_interference_utils.py` — passes as part of the 304 slice.

**Phase 4H is complete.**

---

## 5. Phase 4I Status

**Phase 4I is fully implemented and passing.**

File: `backend/tests/test_gemini_workflow_baseline_fixture.py` (536 lines, 18.9 KB)

Key design properties:
- Does **not** import `app.workflow` — `workflow.py` is intentionally not imported.
- Builds a **workflow-shaped** (not live-execution) baseline fixture that mirrors the
  full `ForecastState` shape including `agent_outputs`, `fusion_result_v2`,
  `horizon_forecasts`, `critic_result`, `governor_result`, `executive_summary`,
  `final_report`, `signals`, `deduped_evidence`, etc.
- The fixture metadata records `created_for_phase: "4I"` and documents the
  deliberate non-import of `workflow.py`.
- Tests assert:
  - Fixture canonicalizes deterministically across repeated serialization
  - Protected keys are all present and unchanged when comparing fixture to itself
  - No Gemini state keys exist in the baseline
  - No Gemini `agent_outputs` entry exists
  - `assert_protected_keys_unchanged()` catches mutations to `agent_outputs`,
    `fusion_result_v2`, `final_report`
  - Adding `gemini_assist_review` or `gemini_deep_research` agent output is caught
  - No Gemini classes (`GeminiDeepResearchClient`, `GeminiAssistNodeWrapper`, etc.)
    appear in global scope — isolation confirmed
  - No writes to `data/research/gemini_assist_trials`, `gemini_shadow_runs`, or
    `evidence_packs` directories
  - All writes use `tmp_path`; no `data/research` path leaks

Tests pass as part of the 304 regression slice.

**Phase 4I is complete.**

---

## 6. Phase 4K / Human Review Documentation Status

**Phase 4K is documented only. It is NOT in main. Workflow.py is untouched.**

A comprehensive human review package exists at `docs/gemini_phase4k_human_review_package.md`
(489 lines, 25.8 KB). This document:

- Confirms `workflow.py` on `main` has **no Gemini wiring** — V2 join proceeds directly to
  `schema_validator_node`.
- Documents the dirty backup evidence showing what Phase 4K wiring would look like:
  - Import of `gemini_graph_noop_node`
  - `workflow.add_node("gemini_assist_noop", gemini_graph_noop_node)`
  - V2 join `"proceed"` routed to `gemini_assist_noop`
  - Edge: `gemini_assist_noop → evidence_analyst`
- Explains why Phase 4K is **postponed**: the dirty backup is not a minimal isolated patch —
  it bundles broader workflow changes (`evidence_analyst` placement, V2 join router semantics,
  executive summary logic) that must not be accepted under a narrow Phase 4K label.
- Provides a 20-item acceptance criteria list that must all be satisfied before Phase 4K
  is reconsidered.
- Provides a rollback plan (pre-implementation tag + `git restore`).
- Provides a 12-item human approval checklist.
- **Recommendation in the doc:** Option B (postpone, keep `workflow.py` untouched) with
  Option E (preserve dirty evidence in a separate review branch).

**Status: documentation only, no code changes, human approval required.**

---

## 7. Safety Boundary Verification

### 7.1 `workflow.py` Import Check

```text
grep -Rni "gemini_deep_research|GeminiGraphNoopAdapter|gemini_graph_noop_node|GeminiAssistNodeWrapper" backend/app/workflow.py

Result: OK: workflow.py has no Gemini imports
```

✅ **Confirmed: `workflow.py` is untouched.**

### 7.2 Graph Wiring Check

`graph_adapter.py` defines `GeminiGraphNoopAdapter` and `gemini_graph_noop_node`. However:

- `gemini_graph_noop_node` is **not imported** anywhere in `workflow.py`.
- `GeminiGraphNoopAdapter` is **not registered** in any LangGraph `workflow.add_node()` call.
- The function exists as a **callable-ready but unregistered** future node boundary.
- `graph_adapter.py` line 382–384: the function is defined but the module docstring explicitly
  says *"without registering the node anywhere"*.

✅ **Confirmed: `graph_adapter.py` is not wired into LangGraph.**

### 7.3 Production State Write Check

Inspected: `client.py`, `normalizer.py`, `shadow_compare.py`, `shadow_runner.py`,
`evaluation_policy.py`, `assist_config.py`, `assist_audit.py`, `assist_node.py`,
`graph_adapter.py`, `key_validation.py`.

All outputs are written to local audit directories (`audit_dir`) as JSON artifacts.
No code path in the Gemini package writes to production `ForecastState`.

✅ **Confirmed: No production state mutation.**

### 7.4 `agent_outputs` Write Check

`PROTECTED_STATE_KEYS` (defined in both `graph_adapter.py` and `gemini_non_interference_utils.py`)
includes `agent_outputs`. The no-op adapter's `validate_no_protected_mutation()` would raise
`GeminiGraphAdapterSafetyError` if `agent_outputs` were mutated.

No code path in the Gemini package writes into `state["agent_outputs"]`. The `assist_node.py`
`run()` method — when called directly — writes audit artifacts, not `agent_outputs`.

✅ **Confirmed: No `agent_outputs` write.**

### 7.5 `Signal` / `HorizonForecast` / `FusionResult` Creation Check
<br>

```bash
grep -Rn "Signal(" backend/app/integrations/gemini_deep_research/
# → 0 matches

grep -Rn "HorizonForecast(" backend/app/integrations/gemini_deep_research/
# → 0 matches

grep -Rn "FusionResult(" backend/app/integrations/gemini_deep_research/
# → 0 matches
```

✅ **Confirmed: No `Signal`, `HorizonForecast`, or `FusionResult` creation.**

### 7.6 Protected Component Modification Check

Protected files on `main` per the handoff:

| Protected File | Status |
|---|---|
| `backend/app/workflow.py` | ✅ Untouched (no Gemini import) |
| `backend/app/graph/contracts.py` | ✅ Not modified by the Gemini package |
| `backend/app/agents/` | ✅ Not modified by the Gemini package |
| `backend/app/retrieval/evidence_deduper.py` | ✅ Not modified |
| `backend/app/retrieval/independence_analyzer.py` | ✅ Not modified |
| `backend/app/llm/arbitration.py` | ✅ Not modified |
| `backend/app/retrieval/librarian.py` | ✅ Not modified |

✅ **Confirmed: All protected components are untouched.**

---

## 8. Current Test Inventory

| Test File(s) | Phase | What It Validates |
|---|---|---|
| `test_gemini_deep_research_client.py` | Phase 1 | API client structure, mock interactions, disabled/missing key behavior |
| `test_gemini_evidence_normalizer.py` | Phase 2 | EvidencePack normalization — raw Gemini result → `GeminiEvidencePack` |
| `test_gemini_shadow_compare.py` | Phase 3A | Shadow comparison against local TheSeer output snapshots |
| `test_gemini_shadow_runner.py` | Phase 3B | Shadow runner — workflow-independent, mock mode guard |
| `test_gemini_evaluation_policy.py` | Phase 3C | Shadow evaluation policy — readiness decisions across multiple runs |
| `test_gemini_assist_config.py` | Phase 4B | Assist config model — env loading, disabled-by-default, blocked domains |
| `test_gemini_assist_audit.py` | Phase 4B | Audit models — approval record, rollback status, policy reference |
| `test_gemini_assist_node.py` | Phase 4C | Assist-node wrapper — mock-only, review-only, no production write |
| `test_gemini_assist_disabled_defaults.py` | Phase 4D | Default-disabled behavior: no call, no write, no live Gemini |
| `test_gemini_assist_integration_safety.py` | Phase 4D | Integration safety: key absence, no network, no `agent_outputs` |
| `test_gemini_graph_adapter.py` | Phase 4F | No-op adapter — state passthrough, protected-key validation, noop reasons |
| `test_gemini_non_interference_utils.py` | Phase 4H | Canonical serialization utils — determinism, exclusion logic, diff output |
| `test_gemini_workflow_baseline_fixture.py` | Phase 4I | Workflow-shaped baseline fixture — protected key coverage, Gemini absence, I/O utilities |

**Regression slice total on main: 304 passed, 0 failed (re-confirmed now).**

---

## 9. Remaining Phases to Full Operation

| Phase | What Remains | Type | Gate |
|---|---|---|---|
| **Phase 4K** | Minimal disabled no-op `workflow.py` wiring | Implementation | **Explicit operator/topology approval required** |
| Phase 4L | Disabled graph regression tests (companion to 4K) | Test-only | Gated on 4K approval |
| Phase 4M+ / Review-mode | Enabled (non-disabled) review-mode path through the graph | Implementation | Gated on 4K stability + separate approval |
| Production integration | Gemini evidence entering production `agent_outputs` | Multi-phase | Gated on all prior phases + board-level approval |

**The safe progression is:**
1. ✅ Shadow sidecar (Phases 1–3C) — done
2. ✅ Isolated assist governance (Phases 4–4F) — done
3. ✅ Non-interference infrastructure (Phases 4H–4I) — done
4. ⬜ Phase 4K: minimal disabled `workflow.py` wiring — **planning/approval phase only**
5. ⬜ Phase 4L: disabled graph regression test suite
6. ⬜ Enabled review-mode (later)
7. ⬜ Production integration (much later, separate approval chain)

---

## 10. Recommended Next Phase

**Next phase: Phase 4K Planning and Approval — documentation and human approval only.**

### What this means

Do NOT modify `workflow.py` yet. Phase 4K is:

> Prepare a minimal, isolated implementation plan for adding `gemini_graph_noop_node`
> as a disabled no-op node in `workflow.py`, and obtain explicit operator approval
> before touching `workflow.py`.

### Prerequisites already satisfied

| Prerequisite | Status |
|---|---|
| Baseline fixture tests exist (Phase 4I) | ✅ |
| Byte-for-byte non-interference strategy exists (Phase 4G docs + 4H utils) | ✅ |
| Disabled/default tests pass (Phase 4D) | ✅ |
| Human approval and policy gate models exist (Phase 4B) | ✅ |
| No-op adapter is ready and tested (Phase 4F) | ✅ |
| `workflow.py` is clean | ✅ |
| Rollback tag exists | ✅ |

### Prerequisites still needed before touching `workflow.py`

1. **Explicit operator approval** recorded in a Phase 4K approval document.
2. **Minimal isolated diff** — only the 4 workflow lines (import, node registration,
   route change, edge addition) — no unrelated workflow changes bundled.
3. **Verify `evidence_analyst` placement** — the Phase 4K package doc flags that the
   dirty backup inserted `evidence_analyst` before `schema_validator_node`, which is
   a change beyond Gemini no-op wiring and must be separately approved or excluded.
4. **Disabled graph regression tests** pass on the clean patch before merge.
5. **Pre-implementation rollback tag** created immediately before touching `workflow.py`.

### Conservative recommendation

Issue this next prompt:

```text
You are a senior release-governance engineer on TheSeer.

Implement Phase 4K documentation and approval package only.

Do NOT modify workflow.py.
Do NOT modify any protected files.
Do NOT add any live Gemini execution.
Do NOT add GEMINI_API_KEY.

Produce:
1. docs/gemini_phase4k_minimal_workflow_patch_plan.md
   - The exact 4-line minimal diff that would be applied to workflow.py
   - Why each line is needed and what it does
   - What it does NOT do (no client call, no agent_outputs write, etc.)
   - Acceptance criteria (reference gemini_phase4k_human_review_package.md §10)
   - Rollback plan
2. docs/gemini_phase4k_operator_approval_record.md
   - Template for operator/topology/security/protected-state approval
3. backend/tests/test_gemini_phase4k_minimal_patch_plan.py
   - Static tests verifying the minimal patch plan doc contains required safety language

Operator must explicitly approve before workflow.py is touched.
```

---

## Appendix: Files Inspected

| File | Purpose |
|---|---|
| `backend/app/integrations/gemini_deep_research/graph_adapter.py` | Phase 4F no-op adapter — confirmed no workflow wiring |
| `backend/tests/gemini_non_interference_utils.py` | Phase 4H utilities — complete |
| `backend/tests/test_gemini_workflow_baseline_fixture.py` | Phase 4I baseline tests — complete |
| `docs/gemini_phase_alignment_audit.md` | Prior alignment audit (2026-05-17) — read |
| `docs/gemini_phase4k_human_review_package.md` | Phase 4K human review package — read |
| `backend/app/workflow.py` | Protected file — confirmed no Gemini imports |
| `docs/` directory listing | 5 docs files confirmed |
| `backend/app/integrations/gemini_deep_research/` listing | 16 package files confirmed |

**No source code was modified by this audit.**
