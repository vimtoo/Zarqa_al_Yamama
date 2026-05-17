"""Phase 4F isolated no-op graph-node adapter.

This module defines the future LangGraph node boundary shape without registering
the node anywhere. Its default behavior is intentionally inert: return the input
state unchanged and avoid all production state writes.
"""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional, Set

from app.integrations.gemini_deep_research.assist_config import (
    SAFE_INSERTION_POINT,
    GeminiAssistApprovalRecord,
    GeminiAssistConfig,
    GeminiAssistGatekeeper,
    GeminiAssistRollbackStatus,
    GeminiPolicyApprovalReference,
)
from app.integrations.gemini_deep_research.assist_node import (
    GeminiAssistNodeResult,
    GeminiAssistNodeWrapper,
)


REVIEW_KEY = "gemini_assist_review"

PROTECTED_STATE_KEYS: Set[str] = {
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


class GeminiGraphAdapterSafetyError(RuntimeError):
    """Raised when a graph-adapter rehearsal changes protected state keys."""


class GeminiGraphNoopAdapter:
    """Standalone no-op adapter with the same call shape as a future graph node."""

    def __init__(
        self,
        assist_wrapper: Optional[Any] = None,
        config_factory: Optional[Callable[[], GeminiAssistConfig]] = None,
    ) -> None:
        self.assist_wrapper = assist_wrapper
        self.config_factory = config_factory
        self.last_noop_reasons: List[str] = []
        self.last_review_result: Optional[GeminiAssistNodeResult] = None

    def __call__(self, state: Any) -> Any:
        """Return graph state through the no-op adapter path."""
        return self.run(state)

    async def async_call(self, state: Any) -> Any:
        """Async-compatible wrapper for a future async graph-node signature."""
        return self.run(state)

    def run(self, state: Any) -> Any:
        """Return state unchanged unless a later phase implements review-only wiring."""
        config = self._build_config()
        if self.should_noop(state, config):
            return state

        before_state = self.clone_state(state)
        after_state = self.maybe_run_review_only(state, config)
        self.validate_no_protected_mutation(before_state, after_state)
        return after_state

    def should_noop(self, state: Any, config: GeminiAssistConfig) -> bool:
        """Return whether Phase 4F must remain inert for this state/config."""
        self.last_noop_reasons = self.build_noop_reason(config, state)
        return bool(self.last_noop_reasons)

    def clone_state(self, state: Any) -> Any:
        """Return a defensive deep copy for optional review-only experiments."""
        if not isinstance(state, dict):
            return copy.deepcopy(state)
        return copy.deepcopy(state)

    @staticmethod
    def protected_state_keys() -> Set[str]:
        """Return production state keys that this adapter must not change."""
        return set(PROTECTED_STATE_KEYS)

    def validate_no_protected_mutation(self, before_state: Any, after_state: Any) -> bool:
        """Raise if a protected production state key was added, removed, or changed."""
        if not isinstance(before_state, dict) or not isinstance(after_state, dict):
            if before_state == after_state:
                return True
            raise GeminiGraphAdapterSafetyError("Non-dict state changed during graph adapter run.")

        missing = object()
        changed = [
            key
            for key in sorted(PROTECTED_STATE_KEYS)
            if before_state.get(key, missing) != after_state.get(key, missing)
        ]
        if changed:
            changed_keys = ", ".join(changed)
            raise GeminiGraphAdapterSafetyError(
                f"Protected state key mutation detected: {changed_keys}"
            )
        return True

    def build_noop_reason(self, config: GeminiAssistConfig, state: Any) -> List[str]:
        """Return deterministic reasons that the adapter must return state unchanged."""
        reasons: List[str] = []
        if not isinstance(state, dict):
            reasons.append("State is not a dict-like graph payload.")
        if not config.use_gemini_deep_research:
            reasons.append("Gemini Deep Research is disabled.")
        if not config.assist_enabled:
            reasons.append("Gemini assist is disabled.")
        if config.gemini_mode != "assist":
            reasons.append("Gemini mode is not assist.")
        if config.rollback_enabled:
            reasons.append("Gemini assist rollback flag is enabled for Phase 4F.")
        if config.insertion_point != SAFE_INSERTION_POINT:
            reasons.append("Gemini assist insertion point is not allowed for graph rehearsal.")
        if config.require_policy_approval:
            reasons.append("Policy approval is not provided to the Phase 4F adapter.")
            reasons.append("Human approval is not provided to the Phase 4F adapter.")
        if self._domain_is_blocked(state, config):
            reasons.append("Requested domain is blocked for Gemini assist.")
        if config.fail_open:
            reasons.append("fail_open=true is not allowed.")
        if config.max_claims <= 0:
            reasons.append("max_claims must be positive.")
        if config.max_evidence_items <= 0:
            reasons.append("max_evidence_items must be positive.")
        if config.warnings:
            reasons.extend(f"Unsafe config warning: {warning}" for warning in config.warnings)

        # Phase 4F deliberately does not execute review-only graph behavior.
        reasons.append("Phase 4F review-only graph execution is future work.")
        return list(dict.fromkeys(reasons))

    def maybe_run_review_only(self, state: Any, config: GeminiAssistConfig) -> Any:
        """Placeholder for a later phase; Phase 4F keeps this path inert."""
        _ = config
        return state

    def run_test_review_mode(
        self,
        state: Any,
        *,
        config: GeminiAssistConfig,
        policy_reference: Optional[GeminiPolicyApprovalReference] = None,
        approval_record: Optional[GeminiAssistApprovalRecord] = None,
        rollback_status: Optional[GeminiAssistRollbackStatus] = None,
        mock: bool = True,
        attach_review_artifact: bool = True,
        audit_dir: Optional[str | Path] = None,
        allow_test_review_mode: bool = False,
    ) -> Any:
        """Run the explicit Phase 4P test-only review path.

        This method is deliberately not used by ``run`` or ``gemini_graph_noop_node``.
        It exists so tests can rehearse review-mode safety without enabling
        production behavior.
        """
        self.last_review_result = None
        config = config.model_copy(update={"audit_dir": str(audit_dir)}) if audit_dir else config
        blockers = self._test_review_mode_blockers(
            state=state,
            config=config,
            policy_reference=policy_reference,
            approval_record=approval_record,
            rollback_status=rollback_status,
            mock=mock,
            attach_review_artifact=attach_review_artifact,
            allow_test_review_mode=allow_test_review_mode,
        )
        if blockers:
            self.last_noop_reasons = blockers
            return state

        domain = self._extract_domain(state)
        trial_result = GeminiAssistGatekeeper().evaluate(
            config,
            approval_record=approval_record,
            policy_reference=policy_reference,
            rollback_status=rollback_status,
            domain=domain,
        )
        if trial_result.blocked:
            self.last_noop_reasons = list(trial_result.blocking_reasons)
            return state

        before_state = self.clone_state(state)
        wrapper = self.assist_wrapper or GeminiAssistNodeWrapper()
        node_result = wrapper.run(
            state,
            config=config,
            policy_reference=policy_reference,
            approval_record=approval_record,
            rollback_status=rollback_status,
            mock=True,
            review_only=True,
            attach_review_artifact=False,
        )
        self.last_review_result = node_result

        cloned_state = self.clone_state(state)
        cloned_state[REVIEW_KEY] = self._build_review_artifact(node_result)
        self.validate_no_protected_mutation(before_state, cloned_state)
        return cloned_state

    def _build_config(self) -> GeminiAssistConfig:
        if self.config_factory is None:
            return GeminiAssistConfig.from_env()
        try:
            config = self.config_factory()
        except Exception:  # noqa: BLE001 - adapter must fail closed
            return GeminiAssistConfig()
        if isinstance(config, GeminiAssistConfig):
            return config
        return GeminiAssistConfig()

    def _domain_is_blocked(self, state: Any, config: GeminiAssistConfig) -> bool:
        domain = self._extract_domain(state)
        blocked = {str(item).strip().lower() for item in config.blocked_domains}
        return domain in blocked

    def _test_review_mode_blockers(
        self,
        *,
        state: Any,
        config: GeminiAssistConfig,
        policy_reference: Optional[GeminiPolicyApprovalReference],
        approval_record: Optional[GeminiAssistApprovalRecord],
        rollback_status: Optional[GeminiAssistRollbackStatus],
        mock: bool,
        attach_review_artifact: bool,
        allow_test_review_mode: bool,
    ) -> List[str]:
        reasons: List[str] = []
        if not allow_test_review_mode:
            reasons.append("Test-only review mode requires explicit allow_test_review_mode=True.")
        if not isinstance(state, dict):
            reasons.append("Test-only review mode requires dict-like state.")
        if not mock:
            reasons.append("Test-only review mode requires mock=True.")
        if not attach_review_artifact:
            reasons.append("Test-only review mode requires attach_review_artifact=True.")
        if not config.use_gemini_deep_research:
            reasons.append("Gemini Deep Research must be explicitly enabled for test review mode.")
        if not config.assist_enabled:
            reasons.append("Assist mode must be explicitly enabled for test review mode.")
        if config.gemini_mode != "assist":
            reasons.append("Test review mode requires gemini_mode=assist.")
        if config.rollback_enabled:
            reasons.append("Config rollback flag must be disabled for test review mode.")
        if rollback_status and rollback_status.is_blocking():
            reasons.append("Rollback state blocks test review mode.")
        if config.insertion_point != SAFE_INSERTION_POINT:
            reasons.append("Test review mode requires the safe insertion point.")
        if config.fail_open:
            reasons.append("fail_open=true is not allowed.")
        if config.max_claims <= 0:
            reasons.append("max_claims must be positive.")
        if config.max_evidence_items <= 0:
            reasons.append("max_evidence_items must be positive.")
        if policy_reference is None:
            reasons.append("Policy approval reference is required.")
        elif not policy_reference.is_ready_for_assist():
            reasons.append("Policy reference is not ready for limited assist trial.")
        if approval_record is None:
            reasons.append("Human approval record is required.")
        if not self._is_safe_test_audit_dir(config.audit_dir):
            reasons.append("Test review mode requires a safe caller-provided audit_dir.")
        return list(dict.fromkeys(reasons))

    def _is_safe_test_audit_dir(self, audit_dir: str | Path) -> bool:
        try:
            candidate = Path(audit_dir).expanduser().resolve()
        except Exception:
            return False

        text = candidate.as_posix().lower()
        production_fragments = (
            "/data/research/gemini_assist_trials",
            "/data/research/gemini_shadow_runs",
            "/data/research/evidence_packs",
        )
        if any(fragment in text for fragment in production_fragments):
            return False
        if not candidate.is_absolute():
            return False

        temp_root = Path(tempfile.gettempdir()).resolve().as_posix().lower()
        parts = {part.lower() for part in candidate.parts}
        return (
            text.startswith(temp_root)
            or "pytest" in text
            or "tmp" in parts
            or "temp" in parts
            or "gemini-review-test" in parts
        )

    def _build_review_artifact(self, node_result: GeminiAssistNodeResult) -> dict[str, Any]:
        audit_bundle = node_result.audit_bundle
        exclusion_reasons = list(node_result.blocking_reasons)
        if audit_bundle:
            exclusion_reasons.extend(audit_bundle.exclusion_reasons)
        inclusion_decision = audit_bundle.inclusion_decision if audit_bundle else None
        warning_text = " ".join(node_result.warnings)
        malformed_warning = any(
            code in warning_text
            for code in ("EMPTY_REPORT", "NO_VERIFIED_SOURCES", "NORMALIZER_EXCEPTION")
        )
        if malformed_warning:
            exclusion_reasons.append("Malformed Gemini output was quarantined.")
        if node_result.status in {"failed", "timeout", "disabled"}:
            status = node_result.status
        elif inclusion_decision == "quarantined" or malformed_warning:
            status = "quarantined"
        else:
            status = node_result.status
        return {
            "run_id": node_result.run_id,
            "status": status,
            "review_only": True,
            "audit_bundle_path": node_result.audit_bundle_path,
            "evidence_pack_path": node_result.evidence_pack_path,
            "warnings": list(dict.fromkeys(node_result.warnings)),
            "blocking_reasons": list(dict.fromkeys(exclusion_reasons)),
            "recommendation": node_result.trial_result.recommendation
            if node_result.trial_result
            else None,
            "overall_risk": audit_bundle.risk_flags if audit_bundle else [],
            "metadata": {
                "mock": True,
                "test_only": True,
                "candidate_inclusion_decision": inclusion_decision,
            },
        }

    def _extract_domain(self, state: Any) -> str:
        if not isinstance(state, dict):
            return "general"
        for key in ("domain", "primary_domain", "active_domain"):
            value = state.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower()
        domains = state.get("domains")
        if isinstance(domains, list) and domains:
            first = domains[0]
            if isinstance(first, str) and first.strip():
                return first.strip().lower()
        planner_output = state.get("planner_output")
        if isinstance(planner_output, dict):
            value = planner_output.get("primary_domain")
            if isinstance(value, str) and value.strip():
                return value.strip().lower()
        metadata = state.get("metadata")
        if isinstance(metadata, dict):
            value = metadata.get("domain")
            if isinstance(value, str) and value.strip():
                return value.strip().lower()
        return "general"


def gemini_graph_noop_node(state: Any) -> Any:
    """Future node-compatible function; it is not registered in any graph."""
    return GeminiGraphNoopAdapter().run(state)
