"""Phase 4B local assist-mode configuration and gatekeeping models."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Mapping, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}
ALLOWED_MODES = {"off", "shadow", "assist"}
ALLOWED_INSERTION_POINTS = {"review_only_appendix", "post_v2_join_pre_evidence"}
SAFE_INSERTION_POINT = "post_v2_join_pre_evidence"
DEFAULT_ALLOWED_DOMAINS = ["general", "technology", "policy"]
DEFAULT_BLOCKED_DOMAINS = ["geopolitics", "security", "finance", "elections"]
SENSITIVE_DOMAINS = set(DEFAULT_BLOCKED_DOMAINS)
READY_FOR_ASSIST_RECOMMENDATION = "Gemini ready for limited assist-mode trial"
ASSIST_AUDIT_DIR = "data/research/gemini_assist_trials"


AssistTrialStatus = Literal[
    "disabled",
    "blocked",
    "review_only",
    "ready_for_trial",
    "failed",
    "skipped",
]


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _parse_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    normalized = _normalize_text(value)
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return default


def _parse_int(
    value: Optional[str],
    default: int,
    field_name: str,
    warnings: List[str],
    *,
    minimum: int = 0,
) -> int:
    if value is None:
        return default
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        warnings.append(f"{field_name}: invalid integer fell back to safe default {default}.")
        return default
    if parsed < minimum:
        warnings.append(f"{field_name}: integer below {minimum} fell back to safe default {default}.")
        return default
    return parsed


def _parse_list(value: Optional[str], default: List[str]) -> List[str]:
    if value is None:
        return list(default)
    parsed = [_normalize_text(item) for item in value.split(",") if _normalize_text(item)]
    return parsed or list(default)


def _normalize_mode(value: Optional[str], warnings: List[str]) -> str:
    normalized = _normalize_text(value) or "shadow"
    if normalized not in ALLOWED_MODES:
        warnings.append("SEER_GEMINI_MODE: unknown mode fell back to shadow.")
        return "shadow"
    return normalized


def _normalize_insertion_point(value: Optional[str], warnings: List[str]) -> str:
    normalized = _normalize_text(value) or SAFE_INSERTION_POINT
    if normalized not in ALLOWED_INSERTION_POINTS:
        warnings.append(
            "SEER_GEMINI_ASSIST_INSERTION_POINT: unknown value fell back to safe insertion point."
        )
        return SAFE_INSERTION_POINT
    return normalized


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class GeminiAssistConfig(BaseModel):
    """Safe defaults and optional environment parsing for future assist trials."""

    use_gemini_deep_research: bool = False
    gemini_mode: str = "shadow"
    assist_enabled: bool = False
    require_policy_approval: bool = True
    allowed_domains: List[str] = Field(default_factory=lambda: list(DEFAULT_ALLOWED_DOMAINS))
    blocked_domains: List[str] = Field(default_factory=lambda: list(DEFAULT_BLOCKED_DOMAINS))
    insertion_point: str = SAFE_INSERTION_POINT
    max_latency_seconds: int = 900
    fail_open: bool = False
    write_audit: bool = True
    rollback_enabled: bool = True
    max_claims: int = 5
    max_evidence_items: int = 10
    require_zero_probability_content: bool = True
    require_zero_secret_warnings: bool = True
    audit_dir: str = ASSIST_AUDIT_DIR
    policy_report_path: Optional[str] = None
    approval_record_path: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "GeminiAssistConfig":
        """Build config from optional process environment values without mutating env files."""
        source = env or os.environ
        warnings: List[str] = []
        return cls(
            use_gemini_deep_research=_parse_bool(
                source.get("SEER_USE_GEMINI_DEEP_RESEARCH"),
                False,
            ),
            gemini_mode=_normalize_mode(source.get("SEER_GEMINI_MODE"), warnings),
            assist_enabled=_parse_bool(source.get("SEER_GEMINI_ASSIST_ENABLED"), False),
            require_policy_approval=_parse_bool(
                source.get("SEER_GEMINI_ASSIST_REQUIRE_POLICY_APPROVAL"),
                True,
            ),
            allowed_domains=_parse_list(
                source.get("SEER_GEMINI_ASSIST_ALLOWED_DOMAINS"),
                DEFAULT_ALLOWED_DOMAINS,
            ),
            blocked_domains=_parse_list(
                source.get("SEER_GEMINI_ASSIST_BLOCKED_DOMAINS"),
                DEFAULT_BLOCKED_DOMAINS,
            ),
            insertion_point=_normalize_insertion_point(
                source.get("SEER_GEMINI_ASSIST_INSERTION_POINT"),
                warnings,
            ),
            max_latency_seconds=_parse_int(
                source.get("SEER_GEMINI_ASSIST_MAX_LATENCY_SECONDS"),
                900,
                "SEER_GEMINI_ASSIST_MAX_LATENCY_SECONDS",
                warnings,
                minimum=1,
            ),
            fail_open=_parse_bool(source.get("SEER_GEMINI_ASSIST_FAIL_OPEN"), False),
            write_audit=_parse_bool(source.get("SEER_GEMINI_ASSIST_WRITE_AUDIT"), True),
            rollback_enabled=_parse_bool(source.get("SEER_GEMINI_ASSIST_ROLLBACK"), True),
            max_claims=_parse_int(
                source.get("SEER_GEMINI_ASSIST_MAX_CLAIMS"),
                5,
                "SEER_GEMINI_ASSIST_MAX_CLAIMS",
                warnings,
                minimum=1,
            ),
            max_evidence_items=_parse_int(
                source.get("SEER_GEMINI_ASSIST_MAX_EVIDENCE_ITEMS"),
                10,
                "SEER_GEMINI_ASSIST_MAX_EVIDENCE_ITEMS",
                warnings,
                minimum=1,
            ),
            require_zero_probability_content=_parse_bool(
                source.get("SEER_GEMINI_ASSIST_REQUIRE_ZERO_PROBABILITY_CONTENT"),
                True,
            ),
            require_zero_secret_warnings=_parse_bool(
                source.get("SEER_GEMINI_ASSIST_REQUIRE_ZERO_SECRET_WARNINGS"),
                True,
            ),
            audit_dir=source.get("SEER_GEMINI_ASSIST_AUDIT_DIR") or ASSIST_AUDIT_DIR,
            policy_report_path=source.get("SEER_GEMINI_ASSIST_POLICY_REPORT_PATH") or None,
            approval_record_path=source.get("SEER_GEMINI_ASSIST_APPROVAL_RECORD_PATH") or None,
            warnings=warnings,
        )


class GeminiPolicyApprovalReference(BaseModel):
    """Reference to a Phase 3C policy decision that may authorize a trial."""

    policy_decision_id: str
    policy_report_path: Optional[str] = None
    recommendation: str
    readiness_level: str
    runs_evaluated: int = 0
    human_review_required: bool = False
    blocking_reasons: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    def is_ready_for_assist(self) -> bool:
        """Return true only for the explicit limited-trial recommendation."""
        return self.recommendation == READY_FOR_ASSIST_RECOMMENDATION


class GeminiAssistApprovalRecord(BaseModel):
    """Human approval record for a limited future assist trial."""

    approval_id: str = Field(default_factory=lambda: str(uuid4()))
    reviewer: Optional[str] = None
    operator_id: Optional[str] = None
    approved_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    domain: str
    query_class: Optional[str] = None
    policy_decision_id: str
    policy_recommendation: str = READY_FOR_ASSIST_RECOMMENDATION
    readiness_level: str = "limited_assist_trial"
    shadow_run_ids: List[str] = Field(default_factory=list)
    allowed_insertion_point: str = SAFE_INSERTION_POINT
    allowed_mode: str = "assist"
    rollback_owner: Optional[str] = None
    notes: Optional[str] = None
    human_review_completed: bool = False
    sensitive_domain_approved: bool = False

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """Return whether this approval has passed its expiry time."""
        if self.expires_at is None:
            return False
        reference_time = _aware(now or utc_now())
        return _aware(self.expires_at) < reference_time

    def is_sensitive_domain(self) -> bool:
        """Return whether the approval domain is sensitive."""
        return _normalize_text(self.domain) in SENSITIVE_DOMAINS

    def is_valid_for_domain(self, domain: str) -> bool:
        """Return whether the approval applies to the requested domain."""
        requested = _normalize_text(domain)
        approved = _normalize_text(self.domain)
        if not requested or requested != approved or self.is_expired():
            return False
        if requested in SENSITIVE_DOMAINS:
            return self.human_review_completed and self.sensitive_domain_approved
        return True

    def is_valid_for_assist(self, config: GeminiAssistConfig) -> bool:
        """Return whether the record satisfies the local assist approval rules."""
        if not self.approval_id:
            return False
        if not (self.reviewer or self.operator_id):
            return False
        if not self.domain or not self.policy_decision_id:
            return False
        if self.allowed_mode != "assist":
            return False
        if self.allowed_insertion_point not in ALLOWED_INSERTION_POINTS:
            return False
        if self.allowed_insertion_point != config.insertion_point:
            return False
        if self.is_expired():
            return False
        if self.is_sensitive_domain() and not (
            self.human_review_completed and self.sensitive_domain_approved
        ):
            return False
        if self.policy_recommendation != READY_FOR_ASSIST_RECOMMENDATION:
            return bool(self.human_review_completed and self.notes)
        return True


class GeminiAssistRollbackStatus(BaseModel):
    """Local kill-switch state for future assist trials."""

    rollback_enabled: bool = True
    rollback_triggered: bool = False
    triggered_at: Optional[datetime] = None
    triggered_by: Optional[str] = None
    reason: Optional[str] = None
    forced_mode: Optional[str] = None

    def is_blocking(self) -> bool:
        """Return whether rollback state blocks assist."""
        if self.forced_mode in {"shadow", "off"}:
            return True
        return bool(self.rollback_enabled and self.rollback_triggered)

    def trigger(self, reason: str, triggered_by: Optional[str] = None) -> "GeminiAssistRollbackStatus":
        """Trigger rollback in place and return this object."""
        self.rollback_triggered = True
        self.triggered_at = utc_now()
        self.triggered_by = triggered_by
        self.reason = reason
        return self

    def clear(self) -> "GeminiAssistRollbackStatus":
        """Clear rollback state in place and return this object."""
        self.rollback_triggered = False
        self.triggered_at = None
        self.triggered_by = None
        self.reason = None
        self.forced_mode = None
        return self


class GeminiAssistTrialResult(BaseModel):
    """Decision summary for whether a future assist attempt would be allowed."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    status: AssistTrialStatus = "skipped"
    allowed: bool = False
    blocked: bool = True
    blocking_reasons: List[str] = Field(default_factory=list)
    audit_bundle_path: Optional[str] = None
    recommendation: Optional[str] = None
    rollback_triggered: bool = False
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GeminiAssistGatekeeper:
    """Evaluate whether local config and approvals would allow a future assist trial."""

    def evaluate(
        self,
        config: GeminiAssistConfig,
        approval_record: Optional[GeminiAssistApprovalRecord] = None,
        policy_reference: Optional[GeminiPolicyApprovalReference] = None,
        rollback_status: Optional[GeminiAssistRollbackStatus] = None,
        domain: Optional[str] = None,
    ) -> GeminiAssistTrialResult:
        """Return a fail-closed trial decision without executing assist behavior."""
        requested_domain = _normalize_text(domain or (approval_record.domain if approval_record else ""))
        reasons: List[str] = []
        warnings = list(config.warnings)

        reasons.extend(self.check_config(config))
        reasons.extend(self.check_rollback(rollback_status))
        reasons.extend(self.check_domain(config, requested_domain, approval_record))
        reasons.extend(self.check_policy(config, policy_reference))
        reasons.extend(self.check_approval(config, approval_record, requested_domain))

        disabled = (
            not config.use_gemini_deep_research
            or not config.assist_enabled
            or config.gemini_mode != "assist"
        )
        status: AssistTrialStatus = "ready_for_trial"
        allowed = not reasons
        if reasons:
            status = "disabled" if disabled else "blocked"
            allowed = False

        return self.build_trial_result(
            status=status,
            allowed=allowed,
            blocking_reasons=reasons,
            policy_reference=policy_reference,
            rollback_status=rollback_status,
            warnings=warnings,
            domain=requested_domain or None,
            config=config,
        )

    def check_config(self, config: GeminiAssistConfig) -> List[str]:
        """Return config-level blocking reasons."""
        reasons: List[str] = []
        if not config.use_gemini_deep_research:
            reasons.append("Gemini Deep Research is disabled.")
        if not config.assist_enabled:
            reasons.append("Assist mode is disabled.")
        if config.gemini_mode != "assist":
            reasons.append("Gemini mode is not assist.")
        if config.insertion_point not in ALLOWED_INSERTION_POINTS:
            reasons.append("Insertion point is not allowed.")
        if config.fail_open:
            reasons.append("fail_open=true is not allowed for assist.")
        if config.max_claims <= 0:
            reasons.append("max_claims must be positive.")
        if config.max_evidence_items <= 0:
            reasons.append("max_evidence_items must be positive.")
        return reasons

    def check_domain(
        self,
        config: GeminiAssistConfig,
        domain: Optional[str],
        approval_record: Optional[GeminiAssistApprovalRecord] = None,
    ) -> List[str]:
        """Return domain-level blocking reasons."""
        requested = _normalize_text(domain)
        if not requested:
            return ["Domain is required for assist trial evaluation."]

        approved = bool(approval_record and approval_record.is_valid_for_domain(requested))
        if requested in {_normalize_text(item) for item in config.blocked_domains} and not approved:
            return [f"Domain '{requested}' is blocked without explicit approval."]
        if requested not in {_normalize_text(item) for item in config.allowed_domains} and not approved:
            return [f"Domain '{requested}' is not in allowed domains."]
        return []

    def check_policy(
        self,
        config: GeminiAssistConfig,
        policy_reference: Optional[GeminiPolicyApprovalReference],
    ) -> List[str]:
        """Return policy-reference blocking reasons."""
        if not config.require_policy_approval:
            return []
        if policy_reference is None:
            return ["Policy approval reference is required."]
        if not policy_reference.is_ready_for_assist():
            return ["Policy reference is not ready for limited assist trial."]
        return []

    def check_approval(
        self,
        config: GeminiAssistConfig,
        approval_record: Optional[GeminiAssistApprovalRecord],
        domain: Optional[str],
    ) -> List[str]:
        """Return human-approval blocking reasons."""
        if not config.require_policy_approval:
            return []
        if approval_record is None:
            return ["Human approval record is required."]
        if approval_record.is_expired():
            return ["Human approval record is expired."]
        if not approval_record.is_valid_for_domain(domain or ""):
            return ["Human approval record is not valid for the requested domain."]
        if not approval_record.is_valid_for_assist(config):
            return ["Human approval record is not sufficient for assist."]
        return []

    def check_rollback(
        self,
        rollback_status: Optional[GeminiAssistRollbackStatus],
    ) -> List[str]:
        """Return rollback blocking reasons."""
        if rollback_status and rollback_status.is_blocking():
            return ["Rollback state blocks assist."]
        return []

    def build_trial_result(
        self,
        *,
        status: AssistTrialStatus,
        allowed: bool,
        blocking_reasons: List[str],
        policy_reference: Optional[GeminiPolicyApprovalReference],
        rollback_status: Optional[GeminiAssistRollbackStatus],
        warnings: List[str],
        domain: Optional[str],
        config: GeminiAssistConfig,
    ) -> GeminiAssistTrialResult:
        """Build a structured gatekeeper result."""
        return GeminiAssistTrialResult(
            status=status,
            allowed=allowed,
            blocked=not allowed,
            blocking_reasons=list(dict.fromkeys(blocking_reasons)),
            recommendation=policy_reference.recommendation if policy_reference else None,
            rollback_triggered=bool(rollback_status and rollback_status.rollback_triggered),
            warnings=list(dict.fromkeys(warnings)),
            metadata={
                "domain": domain,
                "mode": config.gemini_mode,
                "insertion_point": config.insertion_point,
                "require_policy_approval": config.require_policy_approval,
            },
        )
