from __future__ import annotations

import copy
import os
from pathlib import Path

import pytest

from gemini_non_interference_utils import (
    assert_canonical_equal,
    assert_no_agent_output_for_gemini,
    assert_no_gemini_keys,
    assert_protected_keys_unchanged,
    build_default_exclusions,
    canonical_json_dump,
    canonicalize_report,
    canonicalize_state,
    capture_artifact,
    capture_report_artifact,
    diff_canonical,
    load_artifact,
    load_report_artifact,
    protected_state_keys,
)


REAL_GEMINI_ARTIFACT_DIRS = (
    Path("data/research/gemini_assist_trials"),
    Path("data/research/gemini_shadow_runs"),
    Path("data/research/evidence_packs"),
)


def _baseline_state() -> dict:
    """Return a workflow-shaped baseline fixture, not a live workflow execution."""
    context_evidence = {
        "id": "ev-context-001",
        "url": "https://example.test/context/regional-risk",
        "canonical_url": "https://example.test/context/regional-risk",
        "domain": "example.test",
        "publisher": "Example Test Archive",
        "published_at": "2026-05-01",
        "content_hash": "sha256-context-001",
        "snippet": "Regional risk indicators remain elevated but bounded.",
        "source_type": "analysis",
        "reliability_tier": 3,
        "provenance": "LIVE_OSINT",
    }
    black_swan_evidence = {
        "id": "ev-black-swan-001",
        "url": "https://example.test/risk/tail-event",
        "canonical_url": "https://example.test/risk/tail-event",
        "domain": "example.test",
        "publisher": "Example Risk Register",
        "published_at": "2026-05-02",
        "content_hash": "sha256-black-swan-001",
        "snippet": "Tail-risk monitoring should track maritime disruption triggers.",
        "source_type": "analysis",
        "reliability_tier": 3,
        "provenance": "LIVE_OSINT",
    }
    context_claim = {
        "id": "claim-context-001",
        "text": "The baseline scenario remains a bounded regional disruption.",
        "evidence_ids": ["ev-context-001"],
        "confidence": 0.68,
        "time_horizon": "SHORT_TERM",
    }
    black_swan_claim = {
        "id": "claim-black-swan-001",
        "text": "A low-likelihood escalation path depends on maritime disruption triggers.",
        "evidence_ids": ["ev-black-swan-001"],
        "confidence": 0.56,
        "time_horizon": "MEDIUM_TERM",
    }
    horizon_forecast = {
        "horizon": "SHORT_TERM",
        "p10": 0.24,
        "p50": 0.38,
        "p90": 0.52,
        "p10_forecast": 0.22,
        "p50_forecast": 0.39,
        "p90_forecast": 0.55,
        "confidence_level": "MEDIUM",
        "scenario_probabilities": [
            {"scenario": "bounded disruption", "probability": 0.61},
            {"scenario": "rapid escalation", "probability": 0.39},
        ],
    }
    final_report = (
        "# Baseline Forecast\n\n"
        "The workflow-shaped baseline keeps the production forecast lanes stable.\n\n"
        "## Probability Summary\n"
        "- Short-term p50 forecast: 0.39\n"
    )
    return {
        "scenario": "Assess regional escalation risk over the next 30 days",
        "active_agents": ["context_adapter", "black_swan_generator"],
        "skipped_agents": ["market_adapter"],
        "swarm_routing_rationale": "Deterministic baseline exercises context and tail-risk lanes.",
        "agent_outputs": {
            "context_interpreter": {
                "agent_id": "context_interpreter",
                "status": "SUPPORTED",
                "provenance": "LIVE_OSINT",
                "claims": [context_claim],
                "evidence": [context_evidence],
                "signals": [],
                "uncertainty_notes": ["Fixture uses stable example.test sources."],
                "confidence": 0.68,
                "summary": "Context lane produced one evidence-backed baseline claim.",
            },
            "black_swan_generator": {
                "agent_id": "black_swan_generator",
                "status": "SUPPORTED",
                "provenance": "INTERNAL_ANALYSIS",
                "claims": [black_swan_claim],
                "evidence": [black_swan_evidence],
                "signals": [],
                "uncertainty_notes": ["Tail-risk claim is scenario-conditional."],
                "confidence": 0.56,
                "summary": "Tail-risk lane produced one evidence-backed scenario claim.",
            },
        },
        "evidence_summary": "Two stable evidence-like records support two claims.",
        "evidence_unknowns": ["Live retrieval is intentionally not used in this fixture."],
        "evidence_contradictions": [],
        "deduped_evidence": [context_evidence, black_swan_evidence],
        "evidence_clusters": {
            "cluster-context": ["ev-context-001"],
            "cluster-tail-risk": ["ev-black-swan-001"],
        },
        "independence_summary": {
            "source_count": 2,
            "independent_domain_count": 1,
            "independence_score": 0.72,
        },
        "qualitative_forecast": {
            "label": "moderate",
            "rationale": "Baseline probability lane remains bounded in the fixture.",
        },
        "qualitative_forecast_label": "moderate",
        "signals": [],
        "fusion_result": None,
        "fusion_result_v2": {
            "confidence_level": "MEDIUM",
            "executive_summary": "Short-term risk remains moderate in the baseline fixture.",
            "all_claims": [context_claim, black_swan_claim],
            "all_evidence": [context_evidence, black_swan_evidence],
            "horizon_forecasts": {"SHORT_TERM": horizon_forecast},
            "warnings": [],
        },
        "horizon_forecasts": {"SHORT_TERM": horizon_forecast},
        "quantifier_result": {
            "status": "completed",
            "source": "workflow_shaped_fixture",
            "short_term_p50": 0.39,
        },
        "critic_result": {
            "passed": True,
            "requires_reanalysis": False,
            "audit_notes": ["Workflow-shaped fixture passed static critic baseline."],
        },
        "critic_result_v2": {
            "passed": True,
            "requires_reanalysis": False,
            "audit_notes": ["Workflow-shaped fixture passed static critic baseline."],
        },
        "governor_result": {
            "approved": True,
            "halt": False,
            "safety_notes": ["No sensitive content or policy bypass in fixture."],
        },
        "executive_summary": "Short-term risk is moderate in this workflow-shaped baseline.",
        "final_report": final_report,
        "report_path": "backend/tests/fixtures/gemini_non_interference/baseline/baseline_final_report.md",
        "errors": [],
        "warnings": [],
    }


def _baseline_metadata(state: dict) -> dict:
    return {
        "fixture_schema_version": "1.0",
        "fixture_type": "workflow_shaped",
        "scenario_id": "phase-4i-workflow-shaped-baseline-001",
        "scenario": state["scenario"],
        "created_for_phase": "4I",
        "approved_nondeterministic_exclusions": sorted(build_default_exclusions()),
        "expected_protected_keys": sorted(protected_state_keys()),
        "expected_absent_gemini_keys": [
            "gemini_assist_review",
            "gemini_deep_research",
            "gemini_evidence_pack",
            "gemini_shadow_run",
            "gemini_assist_trial",
            "gemini_raw_result",
        ],
        "expected_absent_gemini_agent_output": "gemini_deep_research",
        "notes": (
            "Workflow-shaped baseline fixture, not a live workflow execution. "
            "workflow.py is intentionally not imported in Phase 4I."
        ),
    }


def _baseline_bundle() -> tuple[dict, dict]:
    state = _baseline_state()
    return state, _baseline_metadata(state)


def _snapshot_paths(paths=REAL_GEMINI_ARTIFACT_DIRS) -> dict[str, set[str]]:
    snapshot: dict[str, set[str]] = {}
    for path in paths:
        if path.exists():
            snapshot[str(path)] = {
                str(item.relative_to(path))
                for item in path.rglob("*")
                if item.is_file()
            }
        else:
            snapshot[str(path)] = set()
    return snapshot


def test_baseline_fixture_can_be_built():
    state, metadata = _baseline_bundle()

    assert state["scenario"]
    assert metadata["fixture_type"] == "workflow_shaped"


def test_baseline_fixture_canonicalizes_deterministically():
    state = _baseline_state()

    assert canonicalize_state(state) == canonicalize_state(copy.deepcopy(state))


def test_canonical_baseline_json_is_stable_across_repeated_serialization():
    state = _baseline_state()

    assert canonical_json_dump(state) == canonical_json_dump(copy.deepcopy(state))


def test_baseline_report_canonicalizes_deterministically():
    report = _baseline_state()["final_report"] + "  \r\n\n"

    assert canonicalize_report(report) == canonicalize_report(_baseline_state()["final_report"])


def test_baseline_artifact_can_be_written_to_tmp_path(tmp_path):
    state = _baseline_state()
    path = tmp_path / "baseline" / "baseline_state.json"

    capture_artifact(path, state, exclusions=build_default_exclusions())

    assert path.exists()
    assert "agent_outputs" in path.read_text(encoding="utf-8")


def test_baseline_artifact_can_be_loaded_from_tmp_path(tmp_path):
    state = _baseline_state()
    path = tmp_path / "baseline_state.json"

    capture_artifact(path, state, exclusions=build_default_exclusions())
    loaded = load_artifact(path)

    assert loaded["scenario"] == state["scenario"]
    assert loaded["agent_outputs"] == canonicalize_state(
        state,
        exclusions=build_default_exclusions(),
    )["agent_outputs"]


def test_baseline_final_report_artifact_can_be_written_and_loaded(tmp_path):
    report = _baseline_state()["final_report"] + "\n\n"
    path = tmp_path / "baseline_final_report.md"

    capture_report_artifact(path, report)

    assert load_report_artifact(path) == canonicalize_report(report)


def test_baseline_protected_state_keys_are_present():
    state = _baseline_state()

    for key in protected_state_keys():
        assert key in state


def test_protected_keys_unchanged_passes_comparing_baseline_to_itself():
    state = _baseline_state()

    assert_protected_keys_unchanged(state, copy.deepcopy(state))


def test_no_gemini_keys_passes_on_baseline():
    assert_no_gemini_keys(_baseline_state())


def test_no_agent_output_for_gemini_passes_on_baseline():
    assert_no_agent_output_for_gemini(_baseline_state())


def test_baseline_does_not_contain_review_key():
    assert "gemini_assist_review" not in _baseline_state()


def test_baseline_does_not_contain_gemini_agent_output():
    assert "gemini_deep_research" not in _baseline_state()["agent_outputs"]


@pytest.mark.parametrize(
    "field",
    [
        "agent_outputs",
        "fusion_result_v2",
        "horizon_forecasts",
        "critic_result",
        "governor_result",
        "executive_summary",
        "final_report",
    ],
)
def test_baseline_exact_match_fields_are_present(field):
    assert field in _baseline_state()


def test_nondeterministic_exclusions_do_not_remove_substantive_baseline_fields():
    canonical = canonicalize_state(_baseline_state(), exclusions=build_default_exclusions())

    for field in (
        "agent_outputs",
        "fusion_result_v2",
        "horizon_forecasts",
        "critic_result",
        "governor_result",
        "executive_summary",
        "final_report",
        "errors",
        "warnings",
    ):
        assert field in canonical


def test_baseline_comparison_fails_if_agent_outputs_changed():
    baseline = _baseline_state()
    changed = copy.deepcopy(baseline)
    changed["agent_outputs"]["context_interpreter"]["confidence"] = 0.1

    with pytest.raises(AssertionError, match="agent_outputs"):
        assert_protected_keys_unchanged(baseline, changed)


def test_baseline_comparison_fails_if_fusion_result_v2_changed():
    baseline = _baseline_state()
    changed = copy.deepcopy(baseline)
    changed["fusion_result_v2"]["confidence_level"] = "LOW"

    with pytest.raises(AssertionError, match="fusion_result_v2"):
        assert_protected_keys_unchanged(baseline, changed)


def test_baseline_comparison_fails_if_final_report_changed():
    baseline = _baseline_state()
    changed = copy.deepcopy(baseline)
    changed["final_report"] = "# Altered"

    with pytest.raises(AssertionError, match="final_report"):
        assert_protected_keys_unchanged(baseline, changed)


def test_baseline_comparison_fails_if_review_key_added():
    baseline = _baseline_state()
    changed = copy.deepcopy(baseline)
    changed["gemini_assist_review"] = {"run_id": "unexpected"}

    with pytest.raises(AssertionError, match="gemini_assist_review"):
        assert_no_gemini_keys(changed)
    with pytest.raises(AssertionError):
        assert_canonical_equal(baseline, changed, exclusions=build_default_exclusions())


def test_baseline_comparison_fails_if_gemini_agent_output_added():
    baseline = _baseline_state()
    changed = copy.deepcopy(baseline)
    changed["agent_outputs"]["gemini_deep_research"] = {"status": "SUPPORTED"}

    with pytest.raises(AssertionError, match="gemini_deep_research"):
        assert_no_agent_output_for_gemini(changed)
    with pytest.raises(AssertionError):
        assert_canonical_equal(baseline, changed, exclusions=build_default_exclusions())


def test_no_gemini_deep_research_client_call_occurs_by_non_import_fixture_isolation():
    assert "GeminiDeepResearchClient" not in globals()
    assert "GeminiDeepResearchResult" not in globals()


def test_no_gemini_assist_wrapper_or_adapter_call_occurs_by_non_import_fixture_isolation():
    assert "GeminiAssistNodeWrapper" not in globals()
    assert "GeminiGraphNoopAdapter" not in globals()


def test_no_gemini_normalizer_comparator_or_runner_call_occurs_by_non_import_fixture_isolation():
    assert "GeminiEvidenceNormalizer" not in globals()
    assert "GeminiShadowComparator" not in globals()
    assert "GeminiShadowRunner" not in globals()


def test_no_gemini_audit_files_are_written_by_baseline_tests(tmp_path):
    before = _snapshot_paths()
    capture_artifact(tmp_path / "baseline_state.json", _baseline_state())
    capture_report_artifact(tmp_path / "baseline_final_report.md", _baseline_state()["final_report"])
    after = _snapshot_paths()

    assert after == before


@pytest.mark.parametrize("artifact_dir", REAL_GEMINI_ARTIFACT_DIRS)
def test_no_real_gemini_research_artifact_directory_gets_new_files(tmp_path, artifact_dir):
    before = _snapshot_paths([artifact_dir])
    capture_artifact(tmp_path / "baseline_metadata.json", _baseline_metadata(_baseline_state()))
    after = _snapshot_paths([artifact_dir])

    assert after == before


def test_baseline_fixture_metadata_records_fixture_type():
    _, metadata = _baseline_bundle()

    assert metadata["fixture_type"] == "workflow_shaped"
    assert "not a live workflow execution" in metadata["notes"]


def test_baseline_fixture_metadata_records_approved_exclusions():
    _, metadata = _baseline_bundle()

    assert "request_id" in metadata["approved_nondeterministic_exclusions"]
    assert "agent_outputs" not in metadata["approved_nondeterministic_exclusions"]


def test_baseline_fixture_metadata_records_expected_protected_keys():
    _, metadata = _baseline_bundle()

    assert set(metadata["expected_protected_keys"]) == protected_state_keys()


def test_baseline_fixture_metadata_records_expected_absent_gemini_entries():
    _, metadata = _baseline_bundle()

    assert "gemini_assist_review" in metadata["expected_absent_gemini_keys"]
    assert metadata["expected_absent_gemini_agent_output"] == "gemini_deep_research"


def test_workflow_py_is_not_imported_by_phase_4i_baseline_tests():
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden_from_import = "from " + "app.workflow" + " import"
    forbidden_import = "import " + "app.workflow"

    assert forbidden_from_import not in source
    assert forbidden_import not in source
    assert "workflow.py is intentionally not imported" in _baseline_metadata(_baseline_state())["notes"]


def test_tests_do_not_require_gemini_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    state = _baseline_state()

    assert state["scenario"]
    assert os.environ.get("GEMINI_API_KEY") is None


def test_tests_use_tmp_path_for_all_writes(tmp_path):
    state = _baseline_state()
    base = tmp_path / "fixtures" / "gemini_non_interference" / "baseline"

    capture_artifact(base / "baseline_state.json", state)
    capture_artifact(base / "baseline_agent_outputs.json", state["agent_outputs"])
    capture_artifact(base / "baseline_metadata.json", _baseline_metadata(state))
    capture_report_artifact(base / "baseline_final_report.md", state["final_report"])

    for path in base.iterdir():
        assert str(path).startswith(str(tmp_path))
        assert "data/research" not in str(path)


def test_baseline_artifact_bundle_contains_expected_files(tmp_path):
    state, metadata = _baseline_bundle()
    base = tmp_path / "baseline"

    capture_artifact(base / "baseline_state.json", state)
    capture_artifact(base / "baseline_agent_outputs.json", state["agent_outputs"])
    capture_artifact(base / "baseline_metadata.json", metadata)
    capture_report_artifact(base / "baseline_final_report.md", state["final_report"])

    assert sorted(path.name for path in base.iterdir()) == [
        "baseline_agent_outputs.json",
        "baseline_final_report.md",
        "baseline_metadata.json",
        "baseline_state.json",
    ]


def test_loaded_metadata_preserves_required_phase_4i_fields(tmp_path):
    state, metadata = _baseline_bundle()
    path = tmp_path / "baseline_metadata.json"

    capture_artifact(path, metadata)
    loaded = load_artifact(path)

    assert loaded["fixture_schema_version"] == "1.0"
    assert loaded["created_for_phase"] == "4I"
    assert loaded["fixture_type"] == "workflow_shaped"
    assert loaded["scenario"] == state["scenario"]
    assert loaded["expected_protected_keys"] == metadata["expected_protected_keys"]


def test_diff_is_useful_when_baseline_changes():
    baseline = _baseline_state()
    changed = copy.deepcopy(baseline)
    changed["governor_result"]["approved"] = False

    diff = diff_canonical(baseline, changed, exclusions=build_default_exclusions(), label="baseline")

    assert "Canonical diff for baseline" in diff
    assert "$.governor_result.approved" in diff


def test_baseline_report_contains_no_gemini_text():
    report = canonicalize_report(_baseline_state()["final_report"])

    assert "Gemini" not in report
    assert "gemini" not in report
