from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from app.integrations.gemini_deep_research.assist_audit import (
    GeminiAssistAuditBundle,
    load_assist_audit_bundle,
    load_assist_trial_result,
    save_assist_audit_bundle,
    save_assist_trial_result,
)
from app.integrations.gemini_deep_research.assist_config import (
    GeminiAssistTrialResult,
)
from gemini_artifact_safety_utils import (  # noqa: E402
    assert_artifact_under_root,
    assert_no_production_like_path_markers,
    assert_required_json_keys,
    read_json_artifact,
)
from gemini_secret_scan_utils import (  # noqa: E402
    FAKE_SECRET_LIKE_VALUES,
    assert_fake_secret_values_absent,
)


ASSIST_MODULES = [
    Path("backend/app/integrations/gemini_deep_research/assist_config.py"),
    Path("backend/app/integrations/gemini_deep_research/assist_audit.py"),
]


def _assist_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in ASSIST_MODULES)


def test_audit_bundle_redacts_secrets_in_config_and_feature_flag_snapshots():
    api_value = "AIzaSyFakeSecretValueForTest"
    token_value = "bearer-token-value"
    bundle = GeminiAssistAuditBundle(
        config_snapshot={
            "GEMINI_API_KEY": api_value,
            "nested": {"bearer_token": token_value, "safe_value": "visible"},
        },
        feature_flag_snapshot={"password_value": "hidden", "safe_flag": "visible"},
        human_approval_metadata={"credential_note": "hidden"},
        metadata={"notes": "visible"},
    )

    payload = bundle.model_dump_json()

    assert api_value not in payload
    assert token_value not in payload
    assert "hidden" not in payload
    assert "[REDACTED]" in payload
    assert "visible" in payload


def test_audit_bundle_default_inclusion_decision_is_not_included():
    bundle = GeminiAssistAuditBundle()

    assert bundle.inclusion_decision in {"review_only", "skipped"}
    assert bundle.inclusion_decision != "included"


def test_assist_trial_result_serializes_and_loads(tmp_path):
    result = GeminiAssistTrialResult(
        run_id="trial-1",
        status="blocked",
        allowed=False,
        blocked=True,
        blocking_reasons=["policy missing"],
    )

    path = save_assist_trial_result(result, output_dir=tmp_path)
    loaded = load_assist_trial_result(path)

    assert path == tmp_path / "trial-1" / "assist_trial_result.json"
    assert loaded.run_id == "trial-1"
    assert loaded.status == "blocked"
    assert loaded.blocking_reasons == ["policy missing"]


def test_assist_audit_bundle_saves_and_loads(tmp_path):
    bundle = GeminiAssistAuditBundle(
        run_id="audit-1",
        query="Assess supply-chain risk.",
        domain="technology",
        probability_content_quarantined=False,
        secret_warning_detected=False,
        feature_flag_snapshot={"SEER_GEMINI_ASSIST_ENABLED": "1"},
    )

    path = save_assist_audit_bundle(bundle, output_dir=tmp_path)
    loaded = load_assist_audit_bundle(path)

    assert path == tmp_path / "audit-1" / "assist_audit_bundle.json"
    assert loaded.run_id == "audit-1"
    assert loaded.query == "Assess supply-chain risk."
    assert loaded.inclusion_decision == "review_only"


def test_saved_assist_artifacts_are_json_without_raw_secret_values(tmp_path):
    bundle = GeminiAssistAuditBundle(
        run_id="audit-secret",
        config_snapshot={"api_key": "secret-value"},
    )

    path = save_assist_audit_bundle(bundle, output_dir=tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["config_snapshot"]["api_key"] == "[REDACTED]"
    assert "secret-value" not in path.read_text(encoding="utf-8")


def test_phase4lg_audit_bundle_redacts_secret_like_string_values():
    bundle = GeminiAssistAuditBundle(
        run_id="audit-secret-like-values",
        config_snapshot={"safe_note": list(FAKE_SECRET_LIKE_VALUES)},
        feature_flag_snapshot={"safe_flag_note": " ".join(FAKE_SECRET_LIKE_VALUES)},
        human_approval_metadata={"operator_note": "Authorization: Bearer fakeAuthorizationToken12345"},
        metadata={"review_note": "sk-fakeSidecarSecretValueForRedaction12345"},
    )

    payload = bundle.model_dump_json()

    assert_fake_secret_values_absent(payload)
    assert "[REDACTED]" in payload


def test_phase4lg_saved_audit_bundle_does_not_persist_authorization_header(tmp_path):
    bundle = GeminiAssistAuditBundle(
        run_id="audit-authorization-redaction",
        metadata={
            "safe_review_text": "Authorization: Bearer fakeAuthorizationToken12345",
            "nested": {"safe_note": "api_key=fake_sidecar_api_key_value"},
        },
    )

    path = save_assist_audit_bundle(bundle, output_dir=tmp_path)
    payload = path.read_text(encoding="utf-8")

    assert_fake_secret_values_absent(payload)
    assert "Authorization:" not in payload
    assert "Bearer " not in payload


def test_assist_modules_do_not_import_workflow_module():
    source = _assist_source()

    assert "import workflow" not in source
    assert "from app.workflow" not in source


def test_assist_modules_do_not_write_agent_outputs():
    source = _assist_source()

    assert ("agent" + "_outputs") not in source


def test_assist_modules_do_not_create_forecast_artifact_models():
    source = _assist_source()

    for model_name in ("Signal", "HorizonForecast", "FusionResult"):
        assert f"{model_name}(" not in source


def test_phase4lj_saved_assist_audit_artifact_has_stable_schema_and_safe_path(tmp_path):
    bundle = GeminiAssistAuditBundle(
        run_id="audit-schema-path-safe",
        query="Assess review-only risk.",
        metadata={"review_note": "sidecar artifact only"},
    )

    path = save_assist_audit_bundle(bundle, output_dir=tmp_path)
    payload = read_json_artifact(path)

    assert_artifact_under_root(path, tmp_path)
    assert_no_production_like_path_markers(path)
    assert_required_json_keys(
        payload,
        (
            "run_id",
            "created_at",
            "mode",
            "insertion_point",
            "inclusion_decision",
            "risk_flags",
            "metadata",
        ),
    )
    assert ("agent" + "_outputs") not in path.read_text(encoding="utf-8")
    assert "ForecastState" not in path.read_text(encoding="utf-8")


def test_phase4lj_saved_assist_trial_result_has_stable_schema_and_safe_path(tmp_path):
    result = GeminiAssistTrialResult(
        run_id="trial-schema-path-safe",
        status="blocked",
        allowed=False,
        blocked=True,
        blocking_reasons=["Phase 4K remains NOT APPROVED"],
    )

    path = save_assist_trial_result(result, output_dir=tmp_path)
    payload = read_json_artifact(path)

    assert_artifact_under_root(path, tmp_path)
    assert_no_production_like_path_markers(path)
    assert_required_json_keys(payload, ("run_id", "status", "allowed", "blocked", "blocking_reasons"))


@pytest.mark.parametrize(
    "unsafe_output_dir",
    [
        "../gemini_assist_trials",
        "agent_outputs",
        "final_report",
        "report_writer",
        "ForecastState",
        "horizon_forecasts",
        "fusion_result",
        "signals",
    ],
)
def test_phase4lj_assist_audit_rejects_traversal_and_production_like_output_dirs(unsafe_output_dir):
    bundle = GeminiAssistAuditBundle(run_id="audit-reject-unsafe-path")

    with pytest.raises(ValueError):
        save_assist_audit_bundle(bundle, output_dir=unsafe_output_dir)
