from __future__ import annotations

from datetime import timedelta

from app.integrations.gemini_deep_research.assist_config import (
    READY_FOR_ASSIST_RECOMMENDATION,
    GeminiAssistApprovalRecord,
    GeminiAssistConfig,
    GeminiAssistGatekeeper,
    GeminiAssistRollbackStatus,
    GeminiPolicyApprovalReference,
    utc_now,
)


def _enabled_config(**overrides) -> GeminiAssistConfig:
    payload = {
        "use_gemini_deep_research": True,
        "gemini_mode": "assist",
        "assist_enabled": True,
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
        "human_review_completed": False,
        "sensitive_domain_approved": False,
    }
    payload.update(overrides)
    return GeminiAssistApprovalRecord(**payload)


def test_assist_config_defaults_are_safe_and_disabled():
    config = GeminiAssistConfig()

    assert config.use_gemini_deep_research is False
    assert config.gemini_mode == "shadow"
    assert config.assist_enabled is False
    assert config.fail_open is False
    assert config.require_policy_approval is True
    assert config.allowed_domains == ["general", "technology", "policy"]
    assert config.blocked_domains == ["geopolitics", "security", "finance", "elections"]


def test_assist_config_from_env_parses_true_false_values():
    config = GeminiAssistConfig.from_env({
        "SEER_USE_GEMINI_DEEP_RESEARCH": "yes",
        "SEER_GEMINI_MODE": "assist",
        "SEER_GEMINI_ASSIST_ENABLED": "on",
        "SEER_GEMINI_ASSIST_FAIL_OPEN": "1",
        "SEER_GEMINI_ASSIST_WRITE_AUDIT": "false",
        "SEER_GEMINI_ASSIST_ROLLBACK": "0",
    })

    assert config.use_gemini_deep_research is True
    assert config.gemini_mode == "assist"
    assert config.assist_enabled is True
    assert config.fail_open is True
    assert config.write_audit is False
    assert config.rollback_enabled is False


def test_assist_config_from_env_parses_allowed_and_blocked_domains():
    config = GeminiAssistConfig.from_env({
        "SEER_GEMINI_ASSIST_ALLOWED_DOMAINS": "general, policy , technology",
        "SEER_GEMINI_ASSIST_BLOCKED_DOMAINS": "security, finance",
    })

    assert config.allowed_domains == ["general", "policy", "technology"]
    assert config.blocked_domains == ["security", "finance"]


def test_unknown_mode_falls_back_to_shadow():
    config = GeminiAssistConfig.from_env({"SEER_GEMINI_MODE": "replace_context"})

    assert config.gemini_mode == "shadow"
    assert any("unknown mode" in warning for warning in config.warnings)


def test_unknown_insertion_point_falls_back_to_safe_default():
    config = GeminiAssistConfig.from_env({
        "SEER_GEMINI_ASSIST_INSERTION_POINT": "before_quantifier",
    })

    assert config.insertion_point == "post_v2_join_pre_evidence"
    assert any("unknown value" in warning for warning in config.warnings)


def test_invalid_integers_fall_back_to_safe_defaults_and_warning_is_recorded():
    config = GeminiAssistConfig.from_env({
        "SEER_GEMINI_ASSIST_MAX_LATENCY_SECONDS": "slow",
        "SEER_GEMINI_ASSIST_MAX_CLAIMS": "0",
        "SEER_GEMINI_ASSIST_MAX_EVIDENCE_ITEMS": "-1",
    })

    assert config.max_latency_seconds == 900
    assert config.max_claims == 5
    assert config.max_evidence_items == 10
    assert len(config.warnings) == 3


def test_approval_record_is_expired_when_expires_at_is_past():
    approval = _approval(expires_at=utc_now() - timedelta(minutes=1))

    assert approval.is_expired() is True


def test_sensitive_domains_require_human_review_completed():
    approval = _approval(
        "geopolitics",
        human_review_completed=False,
        sensitive_domain_approved=True,
    )

    assert approval.is_sensitive_domain() is True
    assert approval.is_valid_for_domain("geopolitics") is False


def test_approval_record_validates_for_non_sensitive_domain():
    approval = _approval("general")

    assert approval.is_valid_for_domain("general") is True
    assert approval.is_valid_for_assist(_enabled_config()) is True


def test_policy_reference_ready_only_for_limited_assist_trial_recommendation():
    assert _policy().is_ready_for_assist() is True
    assert _policy(recommendation="Gemini useful as assistant").is_ready_for_assist() is False


def test_replacement_candidate_policy_recommendation_does_not_count_as_assist_approval():
    policy = _policy(
        recommendation="Gemini candidate for future ContextInterpreter replacement",
        readiness_level="replacement_candidate",
    )

    assert policy.is_ready_for_assist() is False


def test_rollback_triggered_blocks_assist():
    rollback = GeminiAssistRollbackStatus()
    rollback.trigger("manual stop", triggered_by="operator")

    assert rollback.is_blocking() is True


def test_gatekeeper_blocks_when_assist_enabled_is_false():
    result = GeminiAssistGatekeeper().evaluate(
        _enabled_config(assist_enabled=False),
        approval_record=_approval(),
        policy_reference=_policy(),
        domain="general",
    )

    assert result.status == "disabled"
    assert result.allowed is False
    assert any("Assist mode is disabled" in reason for reason in result.blocking_reasons)


def test_gatekeeper_blocks_when_mode_is_not_assist():
    result = GeminiAssistGatekeeper().evaluate(
        _enabled_config(gemini_mode="shadow"),
        approval_record=_approval(),
        policy_reference=_policy(),
        domain="general",
    )

    assert result.status == "disabled"
    assert any("Gemini mode is not assist" in reason for reason in result.blocking_reasons)


def test_gatekeeper_blocks_when_policy_approval_is_missing():
    result = GeminiAssistGatekeeper().evaluate(
        _enabled_config(),
        approval_record=_approval(),
        domain="general",
    )

    assert result.status == "blocked"
    assert "Policy approval reference is required." in result.blocking_reasons


def test_gatekeeper_blocks_sensitive_blocked_domain_without_approval():
    result = GeminiAssistGatekeeper().evaluate(
        _enabled_config(),
        policy_reference=_policy(),
        domain="security",
    )

    assert result.status == "blocked"
    assert any("security" in reason for reason in result.blocking_reasons)


def test_gatekeeper_allows_ready_for_trial_only_when_all_checks_pass():
    result = GeminiAssistGatekeeper().evaluate(
        _enabled_config(),
        approval_record=_approval(),
        policy_reference=_policy(),
        rollback_status=GeminiAssistRollbackStatus(),
        domain="general",
    )

    assert result.status == "ready_for_trial"
    assert result.allowed is True
    assert result.blocked is False


def test_gatekeeper_blocks_if_fail_open_is_true():
    result = GeminiAssistGatekeeper().evaluate(
        _enabled_config(fail_open=True),
        approval_record=_approval(),
        policy_reference=_policy(),
        domain="general",
    )

    assert result.status == "blocked"
    assert any("fail_open" in reason for reason in result.blocking_reasons)
