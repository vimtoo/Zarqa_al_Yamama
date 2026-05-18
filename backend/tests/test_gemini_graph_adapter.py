from __future__ import annotations

import copy
from pathlib import Path

import pytest

from app.integrations.gemini_deep_research.assist_config import GeminiAssistConfig
from app.integrations.gemini_deep_research.graph_adapter import (
    PROTECTED_STATE_KEYS,
    GeminiGraphAdapterSafetyError,
    GeminiGraphNoopAdapter,
    gemini_graph_noop_node,
)


class SpyAssistWrapper:
    def __init__(self) -> None:
        self.called = False

    def run(self, *args, **kwargs):
        self.called = True
        return {"unexpected": True}


def _state(**overrides):
    payload = {
        "scenario": "Assess regional escalation risk",
        "domain": "general",
        "metadata": {"domain": "general", "nested": {"value": 1}},
    }
    payload.update(overrides)
    return payload


def _protected_state():
    return _state(
        agent_outputs={"context_interpreter": {"status": "SUPPORTED"}},
        signals=[{"name": "existing"}],
        horizon_forecasts=[{"horizon": "short"}],
        fusion_result={"legacy": True},
        fusion_result_v2={"v2": True},
        final_report="existing report",
        executive_summary="existing summary",
        report_path="data/reports/existing.md",
        governor_result={"status": "approved"},
        critic_result={"status": "passed"},
        quantifier_result={"probability": 0.5},
        deduped_evidence=[{"id": "ev-1"}],
        evidence_clusters=[{"id": "cluster-1"}],
        independence_summary={"score": 0.8},
        qualitative_forecast={"label": "medium"},
        qualitative_forecast_label="medium",
    )


def _config(**overrides):
    payload = {
        "use_gemini_deep_research": True,
        "assist_enabled": True,
        "gemini_mode": "assist",
        "rollback_enabled": False,
        "require_policy_approval": False,
        "blocked_domains": [],
    }
    payload.update(overrides)
    return GeminiAssistConfig(**payload)


def _adapter_with_config(config: GeminiAssistConfig, spy: SpyAssistWrapper | None = None):
    return GeminiGraphNoopAdapter(
        assist_wrapper=spy or SpyAssistWrapper(),
        config_factory=lambda: config,
    )


def _source() -> str:
    return Path("backend/app/integrations/gemini_deep_research/graph_adapter.py").read_text(
        encoding="utf-8"
    )


def test_gemini_graph_noop_node_returns_state_unchanged_by_default(monkeypatch):
    for key in (
        "SEER_USE_GEMINI_DEEP_RESEARCH",
        "SEER_GEMINI_ASSIST_ENABLED",
        "SEER_GEMINI_MODE",
    ):
        monkeypatch.delenv(key, raising=False)
    state = _state()

    result = gemini_graph_noop_node(state)

    assert result is state
    assert result == state


def test_adapter_run_returns_state_unchanged_by_default():
    state = _state()
    adapter = _adapter_with_config(GeminiAssistConfig())

    result = adapter.run(state)

    assert result is state
    assert result == state


def test_default_noop_does_not_call_assist_wrapper_run():
    spy = SpyAssistWrapper()
    adapter = GeminiGraphNoopAdapter(assist_wrapper=spy, config_factory=GeminiAssistConfig)

    result = adapter.run(_state())

    assert result["scenario"] == "Assess regional escalation risk"
    assert spy.called is False


def test_default_noop_does_not_write_review_key():
    state = _state()
    result = _adapter_with_config(GeminiAssistConfig()).run(state)

    assert "gemini_assist_review" not in result


def test_default_noop_does_not_write_agent_outputs():
    state = _state()
    result = _adapter_with_config(GeminiAssistConfig()).run(state)

    assert "agent_outputs" not in result


def test_default_noop_preserves_protected_keys():
    state = _protected_state()
    before = copy.deepcopy(state)

    result = _adapter_with_config(GeminiAssistConfig()).run(state)

    assert result is state
    assert result == before


def test_default_noop_does_not_mutate_original_state():
    state = _state(metadata={"nested": {"value": 1}})
    before = copy.deepcopy(state)

    _adapter_with_config(GeminiAssistConfig()).run(state)

    assert state == before


def test_shadow_mode_causes_noop():
    spy = SpyAssistWrapper()
    state = _state()
    result = _adapter_with_config(_config(gemini_mode="shadow"), spy).run(state)

    assert result is state
    assert spy.called is False


def test_assist_enabled_false_causes_noop():
    spy = SpyAssistWrapper()
    state = _state()
    result = _adapter_with_config(_config(assist_enabled=False), spy).run(state)

    assert result is state
    assert spy.called is False


def test_use_gemini_false_causes_noop():
    spy = SpyAssistWrapper()
    state = _state()
    result = _adapter_with_config(_config(use_gemini_deep_research=False), spy).run(state)

    assert result is state
    assert spy.called is False


def test_rollback_enabled_causes_noop():
    spy = SpyAssistWrapper()
    state = _state()
    result = _adapter_with_config(_config(rollback_enabled=True), spy).run(state)

    assert result is state
    assert spy.called is False


def test_unsafe_insertion_point_causes_noop():
    spy = SpyAssistWrapper()
    state = _state()
    result = _adapter_with_config(_config(insertion_point="before_planner"), spy).run(state)

    assert result is state
    assert spy.called is False


def test_fail_open_true_causes_noop():
    spy = SpyAssistWrapper()
    state = _state()
    result = _adapter_with_config(_config(fail_open=True), spy).run(state)

    assert result is state
    assert spy.called is False


def test_max_claims_nonpositive_causes_noop():
    spy = SpyAssistWrapper()
    state = _state()
    result = _adapter_with_config(_config(max_claims=0), spy).run(state)

    assert result is state
    assert spy.called is False


def test_max_evidence_items_nonpositive_causes_noop():
    spy = SpyAssistWrapper()
    state = _state()
    result = _adapter_with_config(_config(max_evidence_items=0), spy).run(state)

    assert result is state
    assert spy.called is False


def test_protected_state_keys_include_required_keys():
    required = {
        "agent_outputs",
        "signals",
        "horizon_forecasts",
        "fusion_result",
        "fusion_result_v2",
        "final_report",
        "executive_summary",
        "report_path",
        "governor_result",
        "critic_result",
        "quantifier_result",
        "deduped_evidence",
        "evidence_clusters",
        "independence_summary",
        "qualitative_forecast",
        "qualitative_forecast_label",
    }

    assert required.issubset(GeminiGraphNoopAdapter.protected_state_keys())
    assert required.issubset(PROTECTED_STATE_KEYS)


def test_validate_no_protected_mutation_passes_when_unchanged():
    state = _protected_state()
    after = copy.deepcopy(state)

    assert GeminiGraphNoopAdapter().validate_no_protected_mutation(state, after) is True


def test_validate_no_protected_mutation_detects_changed_agent_outputs():
    before = _protected_state()
    after = copy.deepcopy(before)
    after["agent_outputs"] = {"changed": True}

    with pytest.raises(GeminiGraphAdapterSafetyError, match="agent_outputs"):
        GeminiGraphNoopAdapter().validate_no_protected_mutation(before, after)


def test_validate_no_protected_mutation_detects_changed_fusion_result():
    before = _protected_state()
    after = copy.deepcopy(before)
    after["fusion_result"] = {"changed": True}

    with pytest.raises(GeminiGraphAdapterSafetyError, match="fusion_result"):
        GeminiGraphNoopAdapter().validate_no_protected_mutation(before, after)


def test_validate_no_protected_mutation_detects_changed_executive_summary():
    before = _protected_state()
    after = copy.deepcopy(before)
    after["executive_summary"] = "changed"

    with pytest.raises(GeminiGraphAdapterSafetyError, match="executive_summary"):
        GeminiGraphNoopAdapter().validate_no_protected_mutation(before, after)


def test_graph_adapter_does_not_import_workflow_py():
    source = _source()

    assert "workflow.py" not in source
    assert "app.workflow" not in source


def test_graph_adapter_does_not_import_seer_workflow():
    assert "SeerWorkflow" not in _source()


def test_graph_adapter_does_not_import_existing_agents():
    source = _source()

    assert "app.agents" not in source
    assert "backend/app/agents" not in source


def test_graph_adapter_does_not_import_protected_agent_classes():
    source = _source()

    for forbidden in ("QuantifierV2", "CriticV2", "Governor", "SchemaValidator"):
        assert forbidden not in source


def test_graph_adapter_does_not_import_deduper_or_independence_analyzer():
    source = _source()

    assert "EvidenceDeduper" not in source
    assert "IndependenceAnalyzer" not in source


def test_no_forecast_fusion_objects_are_created():
    source = _source()

    for forbidden in ("Signal(", "HorizonForecast", "FusionResult"):
        assert forbidden not in source


def test_malformed_state_input_does_not_crash():
    state = ["not", "a", "dict"]
    adapter = _adapter_with_config(GeminiAssistConfig())

    result = adapter.run(state)

    assert result is state


def test_nested_state_is_not_mutated():
    state = _state(metadata={"nested": {"value": {"inner": 1}}})
    before = copy.deepcopy(state)

    _adapter_with_config(GeminiAssistConfig()).run(state)

    assert state == before


def test_optional_review_only_path_is_future_work_and_remains_noop():
    spy = SpyAssistWrapper()
    state = _protected_state()
    adapter = _adapter_with_config(_config(), spy)

    result = adapter.run(state)

    assert result is state
    assert spy.called is False
    assert "gemini_assist_review" not in result
    assert "Phase 4F review-only graph execution is future work." in adapter.last_noop_reasons


def test_optional_review_only_path_never_changes_protected_keys():
    spy = SpyAssistWrapper()
    state = _protected_state()
    before = copy.deepcopy(state)

    result = _adapter_with_config(_config(), spy).run(state)

    assert result == before
    assert spy.called is False
