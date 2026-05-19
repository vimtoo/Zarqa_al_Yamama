from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from app.integrations.gemini_deep_research.graph_adapter import gemini_graph_noop_node
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
    load_artifact,
    load_report_artifact,
)


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / "backend" / "app" / "workflow.py"


def _workflow_source() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _workflow_tree() -> ast.Module:
    return ast.parse(_workflow_source())


def _string_literals(node: ast.AST) -> list[str]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    ]


def _literal_or_name(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ast.unparse(node)


def _workflow_shaped_state() -> dict:
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
        "provenance": "STATIC_FIXTURE",
    }
    tail_evidence = {
        "id": "ev-tail-001",
        "url": "https://example.test/risk/tail-event",
        "canonical_url": "https://example.test/risk/tail-event",
        "domain": "example.test",
        "publisher": "Example Risk Register",
        "published_at": "2026-05-02",
        "content_hash": "sha256-tail-001",
        "snippet": "Tail-risk monitoring should track maritime disruption triggers.",
        "source_type": "analysis",
        "reliability_tier": 3,
        "provenance": "STATIC_FIXTURE",
    }
    context_claim = {
        "id": "claim-context-001",
        "text": "The baseline scenario remains a bounded regional disruption.",
        "evidence_ids": ["ev-context-001"],
        "confidence": 0.68,
        "time_horizon": "SHORT_TERM",
    }
    tail_claim = {
        "id": "claim-tail-001",
        "text": "A low-likelihood escalation path depends on maritime disruption triggers.",
        "evidence_ids": ["ev-tail-001"],
        "confidence": 0.56,
        "time_horizon": "MEDIUM_TERM",
    }
    horizon_forecast = {
        "horizon": "SHORT_TERM",
        "p10": 0.24,
        "p50": 0.38,
        "p90": 0.52,
        "confidence_level": "MEDIUM",
        "scenario_probabilities": [
            {"scenario": "bounded disruption", "probability": 0.61},
            {"scenario": "rapid escalation", "probability": 0.39},
        ],
    }
    final_report = (
        "# Baseline Forecast\n\n"
        "The workflow-shaped baseline keeps production forecast lanes stable.\n\n"
        "## Probability Summary\n"
        "- Short-term p50 forecast: 0.38\n"
    )
    return {
        "scenario": "Assess regional escalation risk over the next 30 days",
        "active_agents": ["context_interpreter", "black_swan_generator"],
        "skipped_agents": ["market_classifier"],
        "agent_outputs": {
            "context_interpreter": {
                "agent_id": "context_interpreter",
                "status": "SUPPORTED",
                "claims": [context_claim],
                "evidence": [context_evidence],
                "signals": [],
                "confidence": 0.68,
                "summary": "Context lane produced one evidence-backed claim.",
            },
            "black_swan_generator": {
                "agent_id": "black_swan_generator",
                "status": "SUPPORTED",
                "claims": [tail_claim],
                "evidence": [tail_evidence],
                "signals": [],
                "confidence": 0.56,
                "summary": "Tail-risk lane produced one evidence-backed scenario claim.",
            },
        },
        "deduped_evidence": [context_evidence, tail_evidence],
        "evidence_clusters": {
            "cluster-context": ["ev-context-001"],
            "cluster-tail-risk": ["ev-tail-001"],
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
            "all_claims": [context_claim, tail_claim],
            "all_evidence": [context_evidence, tail_evidence],
            "horizon_forecasts": {"SHORT_TERM": horizon_forecast},
            "warnings": [],
        },
        "horizon_forecasts": {"SHORT_TERM": horizon_forecast},
        "quantifier_result": {
            "status": "completed",
            "source": "workflow_shaped_fixture",
            "short_term_p50": 0.38,
        },
        "critic_result": {
            "passed": True,
            "requires_reanalysis": False,
            "audit_notes": ["Static critic baseline passed."],
        },
        "governor_result": {
            "approved": True,
            "halt": False,
            "safety_notes": ["No policy bypass in fixture."],
        },
        "executive_summary": "Short-term risk is moderate in this workflow-shaped baseline.",
        "final_report": final_report,
        "report_path": "backend/tests/fixtures/gemini_non_interference/baseline_final_report.md",
        "errors": [],
        "warnings": [],
    }


def _schema_validator_input_fixture(state: dict) -> dict:
    return {
        "scenario": state["scenario"],
        "agent_outputs": copy.deepcopy(state["agent_outputs"]),
        "deduped_evidence": copy.deepcopy(state["deduped_evidence"]),
        "evidence_clusters": copy.deepcopy(state["evidence_clusters"]),
        "errors": list(state["errors"]),
        "warnings": list(state["warnings"]),
    }


def _assert_static_phase4k_route() -> None:
    tree = _workflow_tree()
    conditional_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_conditional_edges"
        and "v2_join_node" in _string_literals(node)
    ]
    assert len(conditional_calls) == 1
    route_map = next(arg for arg in conditional_calls[0].args if isinstance(arg, ast.Dict))
    routes = {
        key.value: _literal_or_name(value)
        for key, value in zip(route_map.keys, route_map.values)
        if isinstance(key, ast.Constant)
    }
    assert routes["proceed"] == "gemini_assist_noop"

    edges = [
        tuple(_string_literals(node)[:2])
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_edge"
        and len(_string_literals(node)) >= 2
    ]
    assert ("gemini_assist_noop", "schema_validator_node") in edges
    assert ("gemini_assist_noop", "evidence_analyst") not in edges


def test_noop_adapter_preserves_protected_state():
    baseline = _workflow_shaped_state()
    after = gemini_graph_noop_node(copy.deepcopy(baseline))

    assert_protected_keys_unchanged(baseline, after)
    assert_no_gemini_keys(after)
    assert_no_agent_output_for_gemini(after)


def test_noop_adapter_returns_canonical_equivalent_state():
    baseline = _workflow_shaped_state()
    before = canonicalize_state(baseline, exclusions=build_default_exclusions())
    after = canonicalize_state(
        gemini_graph_noop_node(copy.deepcopy(baseline)),
        exclusions=build_default_exclusions(),
    )

    assert before == after
    assert canonical_json_dump(before) == canonical_json_dump(after)
    assert_canonical_equal(before, after, label="disabled no-op state")


def test_schema_validator_input_equivalence_fixture():
    baseline = _workflow_shaped_state()
    before_input = _schema_validator_input_fixture(baseline)
    after_state = gemini_graph_noop_node(copy.deepcopy(baseline))
    after_input = _schema_validator_input_fixture(after_state)

    assert_canonical_equal(before_input, after_input, label="schema validator input")
    assert_no_gemini_keys(after_input)
    assert_no_agent_output_for_gemini(after_input)
    _assert_static_phase4k_route()


def test_report_output_canonical_equivalence_fixture():
    baseline = _workflow_shaped_state()
    after = gemini_graph_noop_node(copy.deepcopy(baseline))

    assert canonicalize_report(baseline["final_report"]) == canonicalize_report(after["final_report"])
    assert_canonical_equal(
        {
            "final_report": baseline["final_report"],
            "executive_summary": baseline["executive_summary"],
            "report_path": baseline["report_path"],
        },
        {
            "final_report": after["final_report"],
            "executive_summary": after["executive_summary"],
            "report_path": after["report_path"],
        },
        label="report writer trusted input",
    )


def test_disabled_state_rejects_gemini_key_injection():
    mutated = copy.deepcopy(_workflow_shaped_state())
    mutated["gemini_assist_review"] = {"status": "unexpected"}

    with pytest.raises(AssertionError, match="gemini_assist_review"):
        assert_no_gemini_keys(mutated)


def test_disabled_agent_outputs_reject_gemini_entry():
    mutated = copy.deepcopy(_workflow_shaped_state())
    mutated["agent_outputs"]["gemini_deep_research"] = {"status": "SUPPORTED"}

    with pytest.raises(AssertionError, match="gemini_deep_research"):
        assert_no_agent_output_for_gemini(mutated)


def test_no_live_gemini_or_client_paths_are_present_in_workflow():
    source = _workflow_source()

    assert "GeminiDeepResearchClient" not in source
    assert "GeminiAssistNodeWrapper" not in source
    assert "live_review_runner" not in source
    assert "GEMINI_API_KEY" not in source
    assert "evidence_analyst" not in source
    for line in source.splitlines():
        if any(factory in line for factory in ("Signal(", "HorizonForecast(", "FusionResult(")):
            assert "gemini" not in line.lower()
    _assert_static_phase4k_route()


def test_tmp_path_only_artifact_equivalence_capture(tmp_path):
    baseline = _workflow_shaped_state()
    after = gemini_graph_noop_node(copy.deepcopy(baseline))
    base = tmp_path / "phase4k_eq"
    before_path = base / "before_state.json"
    after_path = base / "after_state.json"
    before_report_path = base / "before_report.md"
    after_report_path = base / "after_report.md"

    capture_artifact(before_path, baseline, exclusions=build_default_exclusions())
    capture_artifact(after_path, after, exclusions=build_default_exclusions())
    capture_report_artifact(before_report_path, baseline["final_report"])
    capture_report_artifact(after_report_path, after["final_report"])

    assert load_artifact(before_path) == load_artifact(after_path)
    assert load_report_artifact(before_report_path) == load_report_artifact(after_report_path)
    for path in (before_path, after_path, before_report_path, after_report_path):
        assert str(path).startswith(str(tmp_path))
        assert "data/research" not in str(path)
        assert "agent_outputs" not in path.parts
