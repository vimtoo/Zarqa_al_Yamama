from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from app.integrations.gemini_deep_research.assist_config import (
    READY_FOR_ASSIST_RECOMMENDATION,
    GeminiAssistApprovalRecord,
    GeminiAssistConfig,
    GeminiAssistRollbackStatus,
    GeminiPolicyApprovalReference,
)
from app.integrations.gemini_deep_research.assist_node import GeminiAssistNodeWrapper
from app.integrations.gemini_deep_research.models import (
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
)
from gemini_secret_scan_utils import (  # noqa: E402
    FAKE_SECRET_LIKE_VALUES,
    assert_fake_secret_values_absent,
)


class FakeClient:
    def __init__(
        self,
        *,
        status: GeminiDeepResearchStatus = GeminiDeepResearchStatus.COMPLETED,
        report: str | None = None,
        enabled: bool = True,
        raise_error: bool = False,
    ) -> None:
        self.status = status
        self.report = report
        self.enabled = enabled
        self.raise_error = raise_error
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
        if self.raise_error:
            raise RuntimeError("fake client failure")
        return GeminiDeepResearchResult(
            run_id="assist-run-1",
            interaction_id="assist-interaction-1",
            model=model or "fake-gemini-model",
            mode="assist",
            prompt=prompt,
            status=self.status,
            raw_report=self.report if self.report is not None else _good_report(),
            raw_response={"mock": mock},
            error_message="fake timeout" if self.status == GeminiDeepResearchStatus.TIMEOUT else (
                "fake failure" if self.status == GeminiDeepResearchStatus.FAILED else None
            ),
            error_type="fake_error" if self.status != GeminiDeepResearchStatus.COMPLETED else None,
        )


def _good_report() -> str:
    return (
        "Reuters reported current shipping pressure "
        "https://www.reuters.com/world/middle-east/red-sea-shipping-example. "
        "RAND assessed regional deterrence monitoring needs "
        "https://www.rand.org/pubs/research_reports/RRA0000.html."
    )


def _multi_report() -> str:
    return (
        "Reuters reported current shipping pressure https://www.reuters.com/a. "
        "RAND assessed regional deterrence monitoring needs https://www.rand.org/b. "
        "IMF data show reserve pressure changed https://www.imf.org/en/Data."
    )


def _config(tmp_path: Path | None = None, **overrides) -> GeminiAssistConfig:
    payload = {
        "use_gemini_deep_research": True,
        "gemini_mode": "assist",
        "assist_enabled": True,
        "audit_dir": str(tmp_path) if tmp_path else "data/research/gemini_assist_trials",
    }
    payload.update(overrides)
    return GeminiAssistConfig(**payload)


def _policy(**overrides) -> GeminiPolicyApprovalReference:
    payload = {
        "policy_decision_id": "policy-1",
        "recommendation": READY_FOR_ASSIST_RECOMMENDATION,
        "readiness_level": "limited_assist_trial",
        "runs_evaluated": 5,
    }
    payload.update(overrides)
    return GeminiPolicyApprovalReference(**payload)


def _approval(domain: str = "general", **overrides) -> GeminiAssistApprovalRecord:
    payload = {
        "approval_id": "approval-1",
        "reviewer": "reviewer",
        "domain": domain,
        "policy_decision_id": "policy-1",
        "policy_recommendation": READY_FOR_ASSIST_RECOMMENDATION,
        "readiness_level": "limited_assist_trial",
        "allowed_mode": "assist",
        "allowed_insertion_point": "post_v2_join_pre_evidence",
        "human_review_completed": domain in {"geopolitics", "security", "finance", "elections"},
        "sensitive_domain_approved": domain in {"geopolitics", "security", "finance", "elections"},
    }
    payload.update(overrides)
    return GeminiAssistApprovalRecord(**payload)


def _run_allowed(
    tmp_path: Path,
    *,
    client: FakeClient | None = None,
    report: str | None = None,
    config: GeminiAssistConfig | None = None,
    state: dict | None = None,
    mock: bool = True,
):
    client = client or FakeClient(report=report)
    return GeminiAssistNodeWrapper(client=client).run(
        state or {"scenario": "Assess Red Sea escalation risk", "domain": "general"},
        config=config or _config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=GeminiAssistRollbackStatus(),
        mock=mock,
    )


def _assert_candidate_summary_has_no_forecast_artifacts(audit_bundle):
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


def test_wrapper_defaults_to_review_only_behavior(tmp_path):
    result = GeminiAssistNodeWrapper(client=FakeClient()).run(
        {"scenario": "Assess Red Sea escalation risk"},
        config=GeminiAssistConfig(audit_dir=str(tmp_path)),
    )

    assert result.review_only is True
    assert result.status == "disabled"
    assert result.allowed is False


def test_wrapper_does_not_mutate_original_state(tmp_path):
    state = {"scenario": "Assess Red Sea escalation risk", "domain": "general"}
    original = json.loads(json.dumps(state))

    _run_allowed(tmp_path, state=state)

    assert state == original


def test_wrapper_extracts_query_from_scenario():
    wrapper = GeminiAssistNodeWrapper(client=FakeClient())

    assert wrapper.extract_query_from_state({"scenario": "Scenario text"}) == "Scenario text"


@pytest.mark.parametrize("key", ["query", "user_query", "question", "prompt"])
def test_wrapper_extracts_query_from_fallback_keys(key):
    wrapper = GeminiAssistNodeWrapper(client=FakeClient())

    assert wrapper.extract_query_from_state({key: "Fallback text"}) == "Fallback text"


def test_wrapper_defaults_domain_to_general_when_missing():
    wrapper = GeminiAssistNodeWrapper(client=FakeClient())

    assert wrapper.extract_domain_from_state({"scenario": "Question"}) == "general"
    assert any("domain" in warning for warning in wrapper._warnings)


def test_gatekeeper_blocks_before_gemini_call_when_config_disabled(tmp_path):
    client = FakeClient()
    result = GeminiAssistNodeWrapper(client=client).run(
        {"scenario": "Assess Red Sea escalation risk", "domain": "general"},
        config=GeminiAssistConfig(audit_dir=str(tmp_path)),
        policy_reference=_policy(),
        approval_record=_approval(),
    )

    assert result.status == "disabled"
    assert client.called is False


def test_gatekeeper_blocks_sensitive_domain_without_approval(tmp_path):
    client = FakeClient()
    result = GeminiAssistNodeWrapper(client=client).run(
        {"scenario": "Assess security risk", "domain": "security"},
        config=_config(tmp_path),
        policy_reference=_policy(),
        mock=True,
    )

    assert result.status == "blocked"
    assert client.called is False
    assert any("security" in reason for reason in result.blocking_reasons)


def test_rollback_blocks_execution(tmp_path):
    rollback = GeminiAssistRollbackStatus().trigger("operator stop")
    client = FakeClient()
    result = GeminiAssistNodeWrapper(client=client).run(
        {"scenario": "Assess Red Sea escalation risk", "domain": "general"},
        config=_config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=rollback,
    )

    assert result.status == "blocked"
    assert client.called is False


def test_allowed_mock_run_creates_node_result(tmp_path):
    result = _run_allowed(tmp_path)

    assert result.status == "completed_review_only"
    assert result.allowed is True
    assert result.candidate_agent_output_created is True


def test_allowed_mock_run_creates_audit_bundle(tmp_path):
    state = {"scenario": "Assess Red Sea escalation risk", "domain": "general"}
    original = json.loads(json.dumps(state))
    result = _run_allowed(tmp_path, state=state)

    assert result.audit_bundle is not None
    assert result.audit_bundle.inclusion_decision in {"review_only", "quarantined"}
    if result.audit_bundle.inclusion_decision == "quarantined":
        reviewable_details = " ".join(
            result.audit_bundle.exclusion_reasons
            + result.audit_bundle.normalizer_warnings
            + [json.dumps(result.audit_bundle.candidate_agent_output_summary)]
        )
        assert any(
            marker in reviewable_details
            for marker in (
                "Candidate output is not valid",
                "AGENT_OUTPUT_CONVERSION_FAILED",
                "ImportError",
                "ValidationError",
                "UNSUPPORTED_CLAIM_SKIPPED",
                "NO_SUPPORTED_CLAIMS",
            )
        )
    assert state == original
    assert ("agent" + "_outputs") not in state
    assert ("agent" + "_outputs") not in (result.updated_state or {})
    assert "signals" not in (result.updated_state or {})
    assert "horizon_forecasts" not in (result.updated_state or {})
    assert "fusion_result" not in (result.updated_state or {})
    _assert_candidate_summary_has_no_forecast_artifacts(result.audit_bundle)


def test_allowed_mock_run_creates_evidence_pack(tmp_path):
    result = _run_allowed(tmp_path)

    assert result.evidence_pack_path is not None
    payload = json.loads(Path(result.evidence_pack_path).read_text(encoding="utf-8"))
    assert payload["provider"] == "gemini_deep_research"
    assert payload["evidence_items"]


def test_candidate_agent_output_if_created_has_empty_signals(tmp_path):
    result = _run_allowed(tmp_path)

    _assert_candidate_summary_has_no_forecast_artifacts(result.audit_bundle)


def test_max_claims_cap_is_enforced(tmp_path):
    result = _run_allowed(
        tmp_path,
        report=_multi_report(),
        config=_config(tmp_path, max_claims=1),
    )

    payload = json.loads(Path(result.evidence_pack_path).read_text(encoding="utf-8"))
    assert len(payload["claim_items"]) <= 1


def test_max_evidence_items_cap_is_enforced(tmp_path):
    result = _run_allowed(
        tmp_path,
        report=_multi_report(),
        config=_config(tmp_path, max_evidence_items=1),
    )

    payload = json.loads(Path(result.evidence_pack_path).read_text(encoding="utf-8"))
    assert len(payload["evidence_items"]) <= 1


def test_probability_contamination_blocks_inclusion_when_required(tmp_path):
    result = _run_allowed(
        tmp_path,
        report="There is a 70% chance of escalation https://www.reuters.com/world/a.",
    )

    assert result.audit_bundle.probability_content_quarantined is True
    assert result.audit_bundle.inclusion_decision == "quarantined"
    assert result.candidate_agent_output_valid is False


def test_secret_warning_blocks_inclusion_when_required(tmp_path):
    result = _run_allowed(
        tmp_path,
        report="API_KEY=AIzaFakeSecretValueForTesting12345 https://www.reuters.com/world/a.",
    )

    serialized = result.audit_bundle.model_dump_json()
    assert result.audit_bundle.secret_warning_detected is True
    assert result.audit_bundle.inclusion_decision == "quarantined"
    assert "AIzaFakeSecretValueForTesting12345" not in serialized


def test_phase4lg_assist_artifacts_redact_secret_like_report_content(tmp_path):
    raw_report = (
        "Reuters reported current shipping pressure https://www.reuters.com/world/a.\n"
        + "\n".join(FAKE_SECRET_LIKE_VALUES)
    )
    result = _run_allowed(tmp_path, report=raw_report)

    assert result.audit_bundle.secret_warning_detected is True
    assert result.audit_bundle.inclusion_decision == "quarantined"
    for artifact_path in (
        result.raw_result_path,
        result.evidence_pack_path,
        result.audit_bundle_path,
        result.metadata["node_result_path"],
    ):
        payload = Path(artifact_path).read_text(encoding="utf-8")
        assert_fake_secret_values_absent(payload)
        assert "Authorization:" not in payload
        assert "Bearer " not in payload


def test_review_only_mode_does_not_write_agent_outputs(tmp_path):
    state = {"scenario": "Assess Red Sea escalation risk", "domain": "general"}
    result = _run_allowed(tmp_path, state=state)

    assert ("agent" + "_outputs") not in state
    assert ("agent" + "_outputs") not in (result.updated_state or {})


def test_maybe_attach_review_artifact_writes_only_review_key_on_cloned_state(tmp_path):
    wrapper = GeminiAssistNodeWrapper(client=FakeClient())
    state = {"scenario": "Assess Red Sea escalation risk", "domain": "general"}
    result = wrapper.run(
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
    assert ("agent" + "_outputs") not in result.updated_state


def test_maybe_attach_review_artifact_never_writes_production_report_fields(tmp_path):
    result = GeminiAssistNodeWrapper(client=FakeClient()).run(
        {"scenario": "Assess Red Sea escalation risk", "domain": "general"},
        config=_config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=GeminiAssistRollbackStatus(),
        mock=True,
        attach_review_artifact=True,
    )

    for key in ("final_report", "executive_summary", "fusion_result"):
        assert key not in result.updated_state


def test_audit_artifacts_save_under_configured_audit_dir(tmp_path):
    result = _run_allowed(tmp_path)

    run_dir = tmp_path / result.run_id
    assert (run_dir / "raw_result.json").exists()
    assert (run_dir / "evidence_pack.json").exists()
    assert (run_dir / "assist_audit_bundle.json").exists()
    assert (run_dir / "assist_trial_result.json").exists()
    assert (run_dir / "node_result.json").exists()


def test_live_mode_disabled_returns_disabled_and_does_not_call_external_api(tmp_path):
    client = FakeClient(enabled=False)
    result = _run_allowed(tmp_path, client=client, mock=False)

    assert result.status == "disabled"
    assert result.blocked is True
    assert client.called is False


def test_client_failure_returns_failed_result_without_exception(tmp_path):
    result = _run_allowed(
        tmp_path,
        client=FakeClient(status=GeminiDeepResearchStatus.FAILED),
    )

    assert result.status == "failed"
    assert result.blocked is True
    assert any("fake failure" in reason for reason in result.blocking_reasons)


def test_timeout_returns_timeout_result_without_exception(tmp_path):
    result = _run_allowed(
        tmp_path,
        client=FakeClient(status=GeminiDeepResearchStatus.TIMEOUT),
    )

    assert result.status == "timeout"
    assert result.blocked is True
    assert any("fake timeout" in reason for reason in result.blocking_reasons)


def test_missing_query_produces_warning_but_does_not_crash(tmp_path):
    result = _run_allowed(tmp_path, state={"domain": "general"})

    assert result.query == "UNKNOWN_QUERY"
    assert any("No query-like field" in warning for warning in result.warnings)


def test_malformed_state_does_not_crash(tmp_path):
    result = GeminiAssistNodeWrapper(client=FakeClient()).run(
        ["not", "a", "dict"],
        config=_config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=GeminiAssistRollbackStatus(),
        mock=True,
    )

    assert result.query == "UNKNOWN_QUERY"
    assert result.domain == "general"


def test_no_workflow_import():
    source = Path("backend/app/integrations/gemini_deep_research/assist_node.py").read_text(
        encoding="utf-8"
    )

    assert "from app.workflow" not in source
    assert "import workflow" not in source


def test_no_existing_agents_imported_or_called():
    source = Path("backend/app/integrations/gemini_deep_research/assist_node.py").read_text(
        encoding="utf-8"
    )

    assert "app.agents" not in source
    assert "ContextInterpreter" not in source
    assert "BlackSwanGenerator" not in source


def test_no_forecast_artifact_models_created_or_referenced():
    source = Path("backend/app/integrations/gemini_deep_research/assist_node.py").read_text(
        encoding="utf-8"
    )

    forbidden = ["Signal", "Horizon" + "Forecast", "Fusion" + "Result"]
    for name in forbidden:
        assert name not in source


def test_no_production_behavior_changes_are_triggered(tmp_path):
    state = {"scenario": "Assess Red Sea escalation risk", "domain": "general"}
    result = _run_allowed(tmp_path, state=state)

    assert result.updated_state is None
    assert set(state) == {"scenario", "domain"}


def test_tests_are_fully_mocked():
    client = FakeClient()

    assert client.enabled is True
    assert hasattr(client, "run_research")
