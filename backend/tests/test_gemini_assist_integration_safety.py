from __future__ import annotations

import copy
import json
from pathlib import Path

from app.integrations.gemini_deep_research.assist_audit import GeminiAssistAuditBundle
from app.integrations.gemini_deep_research.assist_config import (
    READY_FOR_ASSIST_RECOMMENDATION,
    GeminiAssistApprovalRecord,
    GeminiAssistConfig,
    GeminiAssistRollbackStatus,
    GeminiPolicyApprovalReference,
)
from app.integrations.gemini_deep_research.assist_node import GeminiAssistNodeWrapper
from app.integrations.gemini_deep_research.client import GeminiDeepResearchClient
from app.integrations.gemini_deep_research.models import (
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
)


PROTECTED_STATE_KEYS = {
    "agent" + "_outputs",
    "signals",
    "horizon_forecasts",
    "fusion_result",
    "final_report",
    "executive_summary",
    "report_path",
    "governor_result",
    "critic_result",
    "quantifier_result",
}


class FakeClient:
    def __init__(
        self,
        *,
        report: str | None = None,
        enabled: bool = True,
    ) -> None:
        self.report = report
        self.enabled = enabled
        self.called = False

    def get_default_model(self) -> str:
        return "fake-gemini-model"

    def is_enabled(self) -> bool:
        return self.enabled

    async def run_research(
        self,
        prompt: str,
        model: str | None = None,
        timeout_seconds: int | None = None,
        mock: bool = True,
    ) -> GeminiDeepResearchResult:
        self.called = True
        return GeminiDeepResearchResult(
            run_id="safety-run-1",
            interaction_id="safety-interaction-1",
            model=model or "fake-gemini-model",
            mode="assist",
            prompt=prompt,
            status=GeminiDeepResearchStatus.COMPLETED,
            raw_response={"mock": mock},
            raw_report=self.report or _safe_report(),
        )


def _safe_report() -> str:
    return (
        "Reuters reported current shipping pressure "
        "https://www.reuters.com/world/middle-east/red-sea-shipping-example. "
        "RAND assessed regional deterrence monitoring needs "
        "https://www.rand.org/pubs/research_reports/RRA0000.html."
    )


def _config(tmp_path: Path, **overrides) -> GeminiAssistConfig:
    payload = {
        "use_gemini_deep_research": True,
        "assist_enabled": True,
        "gemini_mode": "assist",
        "audit_dir": str(tmp_path),
    }
    payload.update(overrides)
    return GeminiAssistConfig(**payload)


def _policy() -> GeminiPolicyApprovalReference:
    return GeminiPolicyApprovalReference(
        policy_decision_id="policy-1",
        recommendation=READY_FOR_ASSIST_RECOMMENDATION,
        readiness_level="limited_assist_trial",
        runs_evaluated=5,
    )


def _approval() -> GeminiAssistApprovalRecord:
    return GeminiAssistApprovalRecord(
        approval_id="approval-1",
        reviewer="reviewer",
        domain="general",
        policy_decision_id="policy-1",
        policy_recommendation=READY_FOR_ASSIST_RECOMMENDATION,
        readiness_level="limited_assist_trial",
        allowed_mode="assist",
        allowed_insertion_point="post_v2_join_pre_evidence",
    )


def _run_allowed(tmp_path: Path, *, state: dict | None = None, report: str | None = None):
    return GeminiAssistNodeWrapper(client=FakeClient(report=report)).run(
        state or {"scenario": "Assess Red Sea escalation risk", "domain": "general"},
        config=_config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=GeminiAssistRollbackStatus(),
        mock=True,
    )


def _assist_source() -> str:
    return Path("backend/app/integrations/gemini_deep_research/assist_node.py").read_text(
        encoding="utf-8"
    )


def _assert_candidate_summary_has_no_forecast_artifacts(audit_bundle: GeminiAssistAuditBundle):
    summary = audit_bundle.candidate_agent_output_summary
    payload = json.dumps(summary)

    assert summary["created"] is True
    if "signals_count" in summary:
        assert summary["signals_count"] == 0
    if "horizon_forecasts_count" in summary:
        assert summary["horizon_forecasts_count"] == 0
    assert summary.get("fusion_result") in {None, False}
    assert "HorizonForecast" not in payload
    assert "FusionResult" not in payload
    assert "horizon_forecasts" not in payload
    assert "fusion_result" not in payload

    if summary.get("valid") is False:
        assert summary.get("error_type") or summary.get("error_message")
        assert audit_bundle.inclusion_decision == "quarantined"
        assert audit_bundle.exclusion_reasons or audit_bundle.normalizer_warnings


def test_original_state_dict_is_not_mutated(tmp_path):
    state = {"scenario": "Assess Red Sea escalation risk", "domain": "general"}
    before = dict(state)

    _run_allowed(tmp_path, state=state)

    assert state == before


def test_nested_state_structures_are_not_mutated(tmp_path):
    state = {
        "scenario": "Assess Red Sea escalation risk",
        "domain": "general",
        "metadata": {"domain": "general", "nested": {"value": 1}},
        "planner_output": {"primary_domain": "general"},
    }
    before = copy.deepcopy(state)

    _run_allowed(tmp_path, state=state)

    assert state == before


def test_review_only_mode_does_not_write_agent_outputs(tmp_path):
    state = {"scenario": "Assess Red Sea escalation risk", "domain": "general"}

    _run_allowed(tmp_path, state=state)

    assert ("agent" + "_outputs") not in state


def test_review_only_mode_does_not_write_protected_report_or_probability_keys(tmp_path):
    state = {"scenario": "Assess Red Sea escalation risk", "domain": "general"}

    _run_allowed(tmp_path, state=state)

    for key in PROTECTED_STATE_KEYS:
        assert key not in state


def test_maybe_attach_review_artifact_attaches_only_review_key(tmp_path):
    state = {"scenario": "Assess Red Sea escalation risk", "domain": "general"}
    result = GeminiAssistNodeWrapper(client=FakeClient()).run(
        state,
        config=_config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=GeminiAssistRollbackStatus(),
        mock=True,
        attach_review_artifact=True,
    )

    added_keys = set(result.updated_state) - set(state)
    assert added_keys == {"gemini_assist_review"}


def test_maybe_attach_review_artifact_attaches_to_cloned_state_only(tmp_path):
    state = {"scenario": "Assess Red Sea escalation risk", "domain": "general"}
    result = GeminiAssistNodeWrapper(client=FakeClient()).run(
        state,
        config=_config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=GeminiAssistRollbackStatus(),
        mock=True,
        attach_review_artifact=True,
    )

    assert "gemini_assist_review" in result.updated_state
    assert "gemini_assist_review" not in state


def test_maybe_attach_review_artifact_never_attaches_raw_report_text(tmp_path):
    raw_report = _safe_report()
    result = GeminiAssistNodeWrapper(client=FakeClient(report=raw_report)).run(
        {"scenario": "Assess Red Sea escalation risk", "domain": "general"},
        config=_config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=GeminiAssistRollbackStatus(),
        mock=True,
        attach_review_artifact=True,
    )

    assert raw_report not in json.dumps(result.updated_state)


def test_candidate_agent_output_if_created_has_empty_signals(tmp_path):
    result = _run_allowed(tmp_path)

    _assert_candidate_summary_has_no_forecast_artifacts(result.audit_bundle)


def test_candidate_summary_has_no_forecast_artifact_like_keys(tmp_path):
    result = _run_allowed(tmp_path)
    payload = json.dumps(result.audit_bundle.candidate_agent_output_summary)

    assert "HorizonForecast" not in payload
    assert "FusionResult" not in payload
    assert "horizon_forecasts" not in payload
    assert "fusion_result" not in payload


def test_probability_contamination_warning_prevents_inclusion(tmp_path):
    result = _run_allowed(
        tmp_path,
        report="There is a 70% chance of escalation https://www.reuters.com/world/a.",
    )

    assert result.audit_bundle.probability_content_quarantined is True
    assert result.audit_bundle.inclusion_decision == "quarantined"
    assert result.candidate_agent_output_valid is False


def test_secret_warning_prevents_inclusion(tmp_path):
    secret = "AIzaFakeSecretValueForSafetyTest12345"
    result = _run_allowed(
        tmp_path,
        report=f"API_KEY={secret} https://www.reuters.com/world/a.",
    )

    assert result.audit_bundle.secret_warning_detected is True
    assert result.audit_bundle.inclusion_decision == "quarantined"
    assert secret not in result.audit_bundle.model_dump_json()


def test_audit_bundle_inclusion_decision_is_never_included_by_default():
    bundle = GeminiAssistAuditBundle()

    assert bundle.inclusion_decision in {"review_only", "skipped", "quarantined", "failed"}
    assert bundle.inclusion_decision != "included"


def test_audit_bundle_redacts_sensitive_key_patterns():
    payload = {
        "key": "value-key",
        "token": "value-token",
        "secret": "value-secret",
        "password": "value-password",
        "credential": "value-credential",
        "api": "value-api",
        "safe": "visible",
    }
    bundle = GeminiAssistAuditBundle(
        config_snapshot=payload,
        feature_flag_snapshot=payload,
    )
    serialized = bundle.model_dump_json()

    for value in payload.values():
        if value != "visible":
            assert value not in serialized
    assert "visible" in serialized


def test_assist_node_does_not_import_workflow_py():
    source = _assist_source()

    assert "from app.workflow" not in source
    assert "import workflow" not in source


def test_assist_node_does_not_import_seer_workflow():
    assert "SeerWorkflow" not in _assist_source()


def test_assist_node_does_not_import_or_call_existing_agents():
    source = _assist_source()

    assert "app.agents" not in source
    assert "ContextInterpreter" not in source
    assert "BlackSwanGenerator" not in source


def test_assist_node_does_not_import_or_call_quantifier_v2():
    source = _assist_source()

    assert "QuantifierV2" not in source
    assert "quantifier_v2" not in source


def test_assist_node_does_not_import_or_call_critic_v2():
    source = _assist_source()

    assert "CriticV2" not in source
    assert "critic_v2" not in source


def test_assist_node_does_not_import_or_call_governor():
    source = _assist_source()

    assert "Governor" not in source
    assert "governor" not in source


def test_assist_node_does_not_import_or_call_schema_validator():
    source = _assist_source()

    assert "SchemaValidator" not in source
    assert "schema_validator" not in source


def test_assist_node_does_not_import_or_call_evidence_deduper():
    source = _assist_source()

    assert "EvidenceDeduper" not in source
    assert "evidence_deduper" not in source


def test_assist_node_does_not_import_or_call_independence_analyzer():
    source = _assist_source()

    assert "IndependenceAnalyzer" not in source
    assert "independence_analyzer" not in source


def test_assist_node_does_not_reference_protected_output_keys():
    source = _assist_source()

    for key in PROTECTED_STATE_KEYS:
        assert f'["{key}"] =' not in source
        assert f"['{key}'] =" not in source
        assert f".setdefault(\"{key}\"" not in source
        assert f".setdefault('{key}'" not in source


def test_monkeypatched_client_not_called_when_blocked(monkeypatch, tmp_path):
    called = {"value": False}

    async def fake_run_research(self, *args, **kwargs):  # noqa: ANN001
        called["value"] = True
        raise AssertionError("blocked path should not call run_research")

    monkeypatch.setattr(GeminiDeepResearchClient, "run_research", fake_run_research)
    result = GeminiAssistNodeWrapper(client=GeminiDeepResearchClient(api_key=None)).run(
        {"scenario": "Assess Red Sea escalation risk", "domain": "general"},
        config=GeminiAssistConfig(audit_dir=str(tmp_path)),
        mock=True,
    )

    assert result.status == "disabled"
    assert called["value"] is False


def test_monkeypatched_allowed_mock_path_uses_no_external_network(monkeypatch, tmp_path):
    called = {"value": False, "mock": None}

    async def fake_run_research(self, prompt, model=None, timeout_seconds=None, mock=True):  # noqa: ANN001
        called["value"] = True
        called["mock"] = mock
        return GeminiDeepResearchResult(
            run_id="patched-mock-run",
            interaction_id="patched-mock-interaction",
            model=model or "fake-gemini-model",
            mode="assist",
            prompt=prompt,
            status=GeminiDeepResearchStatus.COMPLETED,
            raw_report=_safe_report(),
            raw_response={"mock": mock},
        )

    monkeypatch.setattr(GeminiDeepResearchClient, "run_research", fake_run_research)
    result = GeminiAssistNodeWrapper(client=GeminiDeepResearchClient(api_key=None)).run(
        {"scenario": "Assess Red Sea escalation risk", "domain": "general"},
        config=_config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=GeminiAssistRollbackStatus(),
        mock=True,
    )

    assert result.status == "completed_review_only"
    assert called == {"value": True, "mock": True}


def test_no_test_requires_gemini_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = _run_allowed(tmp_path)

    assert result.status == "completed_review_only"


def test_artifacts_are_written_only_under_tmp_path(tmp_path):
    result = _run_allowed(tmp_path)

    for value in [
        result.raw_result_path,
        result.evidence_pack_path,
        result.audit_bundle_path,
        result.trial_result_path,
        result.metadata["node_result_path"],
    ]:
        assert value is not None
        assert Path(value).is_relative_to(tmp_path)


def test_no_forecast_artifact_models_are_constructed_in_assist_node_source():
    source = _assist_source()

    for model_name in ("Signal", "Horizon" + "Forecast", "Fusion" + "Result"):
        assert f"{model_name}(" not in source


def test_no_production_forecast_output_path_is_written(tmp_path):
    result = _run_allowed(tmp_path)
    serialized_paths = json.dumps({
        "raw": result.raw_result_path,
        "pack": result.evidence_pack_path,
        "audit": result.audit_bundle_path,
        "trial": result.trial_result_path,
    })

    assert "backend/reports" not in serialized_paths
    assert "forecast_outputs" not in serialized_paths


def test_malformed_state_input_does_not_crash_and_remains_non_mutated(tmp_path):
    state = ["not", "a", "dict"]
    before = list(state)

    result = GeminiAssistNodeWrapper(client=FakeClient()).run(
        state,
        config=_config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=GeminiAssistRollbackStatus(),
        mock=True,
    )

    assert result.query == "UNKNOWN_QUERY"
    assert result.domain == "general"
    assert state == before
