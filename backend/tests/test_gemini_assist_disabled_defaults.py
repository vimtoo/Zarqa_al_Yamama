from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from app.integrations.gemini_deep_research.assist_config import (
    READY_FOR_ASSIST_RECOMMENDATION,
    GeminiAssistApprovalRecord,
    GeminiAssistConfig,
    GeminiAssistGatekeeper,
    GeminiAssistRollbackStatus,
    GeminiPolicyApprovalReference,
    utc_now,
)
from app.integrations.gemini_deep_research.assist_node import GeminiAssistNodeWrapper
from app.integrations.gemini_deep_research.models import (
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
)


class TrackingClient:
    def __init__(self) -> None:
        self.called = False

    def get_default_model(self) -> str:
        return "fake-gemini-model"

    def is_enabled(self) -> bool:
        return True

    async def run_research(self, *args, **kwargs) -> GeminiDeepResearchResult:
        self.called = True
        return GeminiDeepResearchResult(
            run_id="should-not-run",
            interaction_id="should-not-run",
            model="fake-gemini-model",
            mode="assist",
            status=GeminiDeepResearchStatus.COMPLETED,
            raw_report="Reuters reported current risk https://www.reuters.com/world/a",
        )


def _policy() -> GeminiPolicyApprovalReference:
    return GeminiPolicyApprovalReference(
        policy_decision_id="policy-1",
        recommendation=READY_FOR_ASSIST_RECOMMENDATION,
        readiness_level="limited_assist_trial",
        runs_evaluated=5,
    )


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
        "human_review_completed": False,
        "sensitive_domain_approved": False,
    }
    payload.update(overrides)
    return GeminiAssistApprovalRecord(**payload)


def _enabled_config(tmp_path: Path, **overrides) -> GeminiAssistConfig:
    payload = {
        "use_gemini_deep_research": True,
        "assist_enabled": True,
        "gemini_mode": "assist",
        "audit_dir": str(tmp_path),
    }
    payload.update(overrides)
    return GeminiAssistConfig(**payload)


def _run_blocked(
    tmp_path: Path,
    *,
    config: GeminiAssistConfig,
    domain: str = "general",
    policy_reference: GeminiPolicyApprovalReference | None = None,
    approval_record: GeminiAssistApprovalRecord | None = None,
    rollback_status: GeminiAssistRollbackStatus | None = None,
) -> tuple[TrackingClient, object]:
    client = TrackingClient()
    result = GeminiAssistNodeWrapper(client=client).run(
        {"scenario": "Assess regional escalation risk", "domain": domain},
        config=config,
        policy_reference=policy_reference,
        approval_record=approval_record,
        rollback_status=rollback_status,
        mock=True,
    )
    return client, result


def test_default_assist_config_is_disabled():
    config = GeminiAssistConfig()

    assert config.use_gemini_deep_research is False
    assert config.assist_enabled is False
    assert config.gemini_mode == "shadow"
    assert config.fail_open is False
    assert config.rollback_enabled is True
    assert {"geopolitics", "security", "finance", "elections"}.issubset(config.blocked_domains)


def test_from_env_with_no_env_remains_disabled():
    config = GeminiAssistConfig.from_env({})

    assert config.use_gemini_deep_research is False
    assert config.assist_enabled is False
    assert config.gemini_mode == "shadow"


def test_gatekeeper_blocks_with_default_config(tmp_path):
    result = GeminiAssistGatekeeper().evaluate(
        GeminiAssistConfig(audit_dir=str(tmp_path)),
        domain="general",
    )

    assert result.status == "disabled"
    assert result.blocked is True
    assert result.allowed is False


def test_wrapper_with_default_config_returns_disabled_or_blocked(tmp_path):
    client, result = _run_blocked(
        tmp_path,
        config=GeminiAssistConfig(audit_dir=str(tmp_path)),
    )

    assert result.status in {"disabled", "blocked"}
    assert result.allowed is False
    assert client.called is False


def test_wrapper_with_default_config_does_not_call_client_run_research(tmp_path):
    client, result = _run_blocked(
        tmp_path,
        config=GeminiAssistConfig(audit_dir=str(tmp_path)),
        policy_reference=_policy(),
        approval_record=_approval(),
    )

    assert result.status == "disabled"
    assert client.called is False


def test_shadow_mode_blocks_assist_execution(tmp_path):
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path, gemini_mode="shadow"),
        policy_reference=_policy(),
        approval_record=_approval(),
    )

    assert result.status == "disabled"
    assert any("mode is not assist" in reason for reason in result.blocking_reasons)
    assert client.called is False


def test_assist_disabled_blocks_even_when_gemini_master_enabled(tmp_path):
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path, assist_enabled=False),
        policy_reference=_policy(),
        approval_record=_approval(),
    )

    assert result.status == "disabled"
    assert any("Assist mode is disabled" in reason for reason in result.blocking_reasons)
    assert client.called is False


def test_mode_not_assist_blocks_execution(tmp_path):
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path, gemini_mode="off"),
        policy_reference=_policy(),
        approval_record=_approval(),
    )

    assert result.status == "disabled"
    assert client.called is False


def test_rollback_triggered_blocks_before_research(tmp_path):
    rollback = GeminiAssistRollbackStatus().trigger("operator stop")
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path),
        policy_reference=_policy(),
        approval_record=_approval(),
        rollback_status=rollback,
    )

    assert result.status == "blocked"
    assert any("Rollback" in reason for reason in result.blocking_reasons)
    assert client.called is False


def test_missing_policy_reference_blocks_when_required(tmp_path):
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path),
        approval_record=_approval(),
    )

    assert result.status == "blocked"
    assert "Policy approval reference is required." in result.blocking_reasons
    assert client.called is False


def test_missing_human_approval_record_blocks(tmp_path):
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path),
        policy_reference=_policy(),
    )

    assert result.status == "blocked"
    assert "Human approval record is required." in result.blocking_reasons
    assert client.called is False


def test_expired_approval_record_blocks_execution(tmp_path):
    expired = _approval(expires_at=utc_now() - timedelta(minutes=1))
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path),
        policy_reference=_policy(),
        approval_record=expired,
    )

    assert result.status == "blocked"
    assert any("expired" in reason for reason in result.blocking_reasons)
    assert client.called is False


@pytest.mark.parametrize("domain", ["geopolitics", "security", "finance", "elections"])
def test_sensitive_domains_block_without_sensitive_approval(tmp_path, domain):
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path),
        domain=domain,
        policy_reference=_policy(),
        approval_record=_approval(domain),
    )

    assert result.status == "blocked"
    assert result.allowed is False
    assert client.called is False


def test_fail_open_true_blocks_assist(tmp_path):
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path, fail_open=True),
        policy_reference=_policy(),
        approval_record=_approval(),
    )

    assert result.status == "blocked"
    assert any("fail_open" in reason for reason in result.blocking_reasons)
    assert client.called is False


def test_max_claims_less_than_or_equal_zero_blocks_assist(tmp_path):
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path, max_claims=0),
        policy_reference=_policy(),
        approval_record=_approval(),
    )

    assert result.status == "blocked"
    assert any("max_claims" in reason for reason in result.blocking_reasons)
    assert client.called is False


def test_max_evidence_items_less_than_or_equal_zero_blocks_assist(tmp_path):
    client, result = _run_blocked(
        tmp_path,
        config=_enabled_config(tmp_path, max_evidence_items=0),
        policy_reference=_policy(),
        approval_record=_approval(),
    )

    assert result.status == "blocked"
    assert any("max_evidence_items" in reason for reason in result.blocking_reasons)
    assert client.called is False


def test_unknown_insertion_point_falls_back_or_blocks(tmp_path):
    config = GeminiAssistConfig.from_env({
        "SEER_USE_GEMINI_DEEP_RESEARCH": "1",
        "SEER_GEMINI_MODE": "assist",
        "SEER_GEMINI_ASSIST_ENABLED": "1",
        "SEER_GEMINI_ASSIST_INSERTION_POINT": "before_quantifier",
        "SEER_GEMINI_ASSIST_AUDIT_DIR": str(tmp_path),
    })

    assert config.insertion_point == "post_v2_join_pre_evidence"
    assert any("unknown value" in warning for warning in config.warnings)
