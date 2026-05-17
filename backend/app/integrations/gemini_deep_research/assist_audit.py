"""Phase 4B local audit models and storage helpers for future assist trials."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.integrations.gemini_deep_research.assist_config import (
    ASSIST_AUDIT_DIR,
    GeminiAssistApprovalRecord,
    GeminiAssistConfig,
    GeminiAssistRollbackStatus,
    GeminiAssistTrialResult,
    GeminiPolicyApprovalReference,
    utc_now,
)


InclusionDecision = Literal[
    "included",
    "excluded",
    "quarantined",
    "review_only",
    "failed",
    "skipped",
]

SENSITIVE_KEY_PARTS = ("key", "token", "secret", "password", "credential", "api")


def _project_root() -> Path:
    # assist_audit.py -> gemini_deep_research -> integrations -> app -> backend -> root
    return Path(__file__).resolve().parents[4]


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return _project_root() / candidate


def _base_dir(config_or_path: GeminiAssistConfig | str | Path | None = None) -> Path:
    if isinstance(config_or_path, GeminiAssistConfig):
        return _resolve_path(config_or_path.audit_dir)
    if config_or_path is not None:
        return _resolve_path(config_or_path)
    return _resolve_path(ASSIST_AUDIT_DIR)


def _redact_sensitive(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _redact_sensitive(value.model_dump(mode="json"))
    if isinstance(value, Mapping):
        redacted: Dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if any(part in key_text.lower() for part in SENSITIVE_KEY_PARTS):
                redacted[key_text] = "[REDACTED]"
            else:
                redacted[key_text] = _redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    return value


class GeminiAssistAuditBundle(BaseModel):
    """Complete audit snapshot for a future assist-trial decision point."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=utc_now)
    query: Optional[str] = None
    domain: Optional[str] = None
    mode: str = "shadow"
    insertion_point: str = "review_only_appendix"
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)
    approval_record: Optional[GeminiAssistApprovalRecord] = None
    policy_reference: Optional[GeminiPolicyApprovalReference] = None
    rollback_status: GeminiAssistRollbackStatus = Field(default_factory=GeminiAssistRollbackStatus)
    raw_result_path: Optional[str] = None
    evidence_pack_path: Optional[str] = None
    candidate_agent_output_summary: Dict[str, Any] = Field(default_factory=dict)
    schema_validation_result: Dict[str, Any] = Field(default_factory=dict)
    deduplication_result: Dict[str, Any] = Field(default_factory=dict)
    independence_analysis_result: Dict[str, Any] = Field(default_factory=dict)
    inclusion_decision: InclusionDecision = "review_only"
    exclusion_reasons: List[str] = Field(default_factory=list)
    latency_seconds: Optional[float] = None
    timeout: bool = False
    failed: bool = False
    risk_flags: List[str] = Field(default_factory=list)
    normalizer_warnings: List[str] = Field(default_factory=list)
    source_governance_notes: List[str] = Field(default_factory=list)
    probability_content_quarantined: bool = False
    secret_warning_detected: bool = False
    human_approval_metadata: Dict[str, Any] = Field(default_factory=dict)
    feature_flag_snapshot: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def redact_snapshots(self) -> "GeminiAssistAuditBundle":
        """Redact sensitive snapshot fields before serialization."""
        self.config_snapshot = _redact_sensitive(self.config_snapshot)
        self.feature_flag_snapshot = _redact_sensitive(self.feature_flag_snapshot)
        self.human_approval_metadata = _redact_sensitive(self.human_approval_metadata)
        self.metadata = _redact_sensitive(self.metadata)
        return self


def ensure_assist_audit_dir(
    config_or_path: GeminiAssistConfig | str | Path | None = None,
) -> Path:
    """Create and return the base directory for assist-trial audit artifacts."""
    path = _base_dir(config_or_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_assist_audit_bundle(
    bundle: GeminiAssistAuditBundle,
    output_dir: str | Path | None = None,
) -> Path:
    """Save an assist audit bundle under a run-specific non-production folder."""
    directory = ensure_assist_audit_dir(output_dir) / bundle.run_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "assist_audit_bundle.json"
    path.write_text(
        json.dumps(bundle.model_dump(mode="json"), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return path


def load_assist_audit_bundle(path: str | Path) -> GeminiAssistAuditBundle:
    """Load a saved assist audit bundle."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return GeminiAssistAuditBundle.model_validate(payload)


def save_assist_trial_result(
    result: GeminiAssistTrialResult,
    output_dir: str | Path | None = None,
) -> Path:
    """Save a gatekeeper result under a run-specific non-production folder."""
    directory = ensure_assist_audit_dir(output_dir) / result.run_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "assist_trial_result.json"
    path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return path


def load_assist_trial_result(path: str | Path) -> GeminiAssistTrialResult:
    """Load a saved assist gatekeeper result."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return GeminiAssistTrialResult.model_validate(payload)
