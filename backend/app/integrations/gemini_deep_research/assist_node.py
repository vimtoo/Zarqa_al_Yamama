"""Phase 4C isolated Gemini assist-node rehearsal wrapper."""

from __future__ import annotations

import asyncio
import copy
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.integrations.gemini_deep_research.assist_audit import (
    GeminiAssistAuditBundle,
    ensure_assist_audit_dir,
    save_assist_audit_bundle,
    save_assist_trial_result,
)
from app.integrations.gemini_deep_research.assist_config import (
    GeminiAssistApprovalRecord,
    GeminiAssistConfig,
    GeminiAssistGatekeeper,
    GeminiAssistRollbackStatus,
    GeminiAssistTrialResult,
    GeminiPolicyApprovalReference,
)
from app.integrations.gemini_deep_research.client import GeminiDeepResearchClient
from app.integrations.gemini_deep_research.models import (
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
    GeminiEvidencePack,
)
from app.integrations.gemini_deep_research.normalizer import GeminiEvidenceNormalizer
from app.integrations.gemini_deep_research.prompts import build_deep_research_prompt


PROBABILITY_WARNING = "PROBABILITY_CONTENT_QUARANTINED"
SECRET_WARNING = "POSSIBLE_SECRET_LEAK"
REVIEW_KEY = "gemini_assist_review"


class GeminiAssistNodeResult(BaseModel):
    """Structured Phase 4C rehearsal result. It is not graph state."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    status: str = "blocked"
    allowed: bool = False
    blocked: bool = True
    review_only: bool = True
    query: str = "UNKNOWN_QUERY"
    domain: str = "general"
    candidate_agent_output_created: bool = False
    candidate_agent_output_valid: bool = False
    evidence_pack_path: Optional[str] = None
    raw_result_path: Optional[str] = None
    audit_bundle_path: Optional[str] = None
    trial_result_path: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)
    audit_bundle: Optional[GeminiAssistAuditBundle] = None
    trial_result: Optional[GeminiAssistTrialResult] = None
    updated_state: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GeminiAssistNodeWrapper:
    """Standalone assist-node rehearsal harness with fail-closed defaults."""

    def __init__(
        self,
        *,
        client: Optional[GeminiDeepResearchClient] = None,
        normalizer: Optional[GeminiEvidenceNormalizer] = None,
        gatekeeper: Optional[GeminiAssistGatekeeper] = None,
    ) -> None:
        self.client = client or GeminiDeepResearchClient()
        self.normalizer = normalizer or GeminiEvidenceNormalizer()
        self.gatekeeper = gatekeeper or GeminiAssistGatekeeper()
        self._warnings: List[str] = []

    def run(
        self,
        state: Any,
        config: Optional[GeminiAssistConfig] = None,
        policy_reference: Optional[GeminiPolicyApprovalReference] = None,
        approval_record: Optional[GeminiAssistApprovalRecord] = None,
        rollback_status: Optional[GeminiAssistRollbackStatus] = None,
        mock: bool = True,
        review_only: bool = True,
        attach_review_artifact: bool = False,
    ) -> GeminiAssistNodeResult:
        """Run the isolated rehearsal path without mutating the input state."""
        self._warnings = []
        config = config or GeminiAssistConfig.from_env()
        state_copy = self.clone_state(state)
        query = self.extract_query_from_state(state_copy)
        domain = self.extract_domain_from_state(state_copy)
        context = self.build_research_context(state_copy)

        trial_result = self.run_gatekeeper(
            config,
            policy_reference,
            approval_record,
            rollback_status,
            domain,
        )
        trial_result.warnings = list(dict.fromkeys(trial_result.warnings + self._warnings))

        if trial_result.blocked:
            audit_bundle = self.build_audit_bundle(
                run_id=trial_result.run_id,
                query=query,
                domain=domain,
                config=config,
                policy_reference=policy_reference,
                approval_record=approval_record,
                rollback_status=rollback_status,
                trial_result=trial_result,
                inclusion_decision="skipped",
                exclusion_reasons=trial_result.blocking_reasons,
            )
            node_result = GeminiAssistNodeResult(
                run_id=trial_result.run_id,
                status=trial_result.status,
                allowed=False,
                blocked=True,
                review_only=review_only,
                query=query,
                domain=domain,
                warnings=list(dict.fromkeys(self._warnings + trial_result.warnings)),
                blocking_reasons=trial_result.blocking_reasons,
                audit_bundle=audit_bundle,
                trial_result=trial_result,
                metadata={"mock": mock, "saved": False},
            )
            if config.write_audit:
                node_result = self.save_audit_artifacts(node_result, config)
            if attach_review_artifact:
                node_result.updated_state = self.maybe_attach_review_artifact(state_copy, node_result)
            return node_result

        start = time.perf_counter()
        raw_result: Optional[GeminiDeepResearchResult] = None
        pack: Optional[GeminiEvidencePack] = None
        candidate: Any = None
        raw_result_path: Optional[str] = None
        evidence_pack_path: Optional[str] = None

        try:
            raw_result = self.run_gemini_research(query, context, config, mock=mock)
            run_id = raw_result.run_id
            trial_result = trial_result.model_copy(update={"run_id": run_id})

            if raw_result.status == GeminiDeepResearchStatus.DISABLED:
                status = "disabled"
            elif raw_result.status == GeminiDeepResearchStatus.TIMEOUT:
                status = "timeout"
            elif raw_result.status == GeminiDeepResearchStatus.FAILED:
                status = "failed"
            else:
                status = "completed_review_only" if review_only else "ready_for_trial"
            runtime_blocked = status in {"disabled", "failed", "timeout"}

            pack = self.normalize_result(raw_result, query, context)
            pack = self._cap_pack(pack, config)
            warning_codes = self._warning_codes(pack)
            probability_blocked = (
                config.require_zero_probability_content and PROBABILITY_WARNING in warning_codes
            )
            secret_blocked = config.require_zero_secret_warnings and SECRET_WARNING in warning_codes

            candidate = self.build_candidate_agent_output(pack)
            candidate_created = candidate is not None
            candidate_valid = self._candidate_valid(candidate) and not probability_blocked and not secret_blocked
            exclusion_reasons = self._exclusion_reasons(
                probability_blocked=probability_blocked,
                secret_blocked=secret_blocked,
                candidate_valid=candidate_valid,
                raw_result=raw_result,
            )
            inclusion_decision = "quarantined" if exclusion_reasons else "review_only"

            if config.write_audit:
                raw_result_path = str(self._save_raw_result(raw_result, config))
                evidence_pack_path = str(self._save_evidence_pack(pack, config, run_id))

            audit_bundle = self.build_audit_bundle(
                run_id=run_id,
                query=query,
                domain=domain,
                config=config,
                policy_reference=policy_reference,
                approval_record=approval_record,
                rollback_status=rollback_status,
                trial_result=trial_result,
                raw_result_path=raw_result_path,
                evidence_pack_path=evidence_pack_path,
                candidate_agent_output_summary=self._candidate_summary(candidate),
                inclusion_decision=inclusion_decision,
                exclusion_reasons=exclusion_reasons,
                latency_seconds=round(time.perf_counter() - start, 4),
                timeout=raw_result.status == GeminiDeepResearchStatus.TIMEOUT,
                failed=raw_result.status == GeminiDeepResearchStatus.FAILED,
                risk_flags=self._risk_flags(probability_blocked, secret_blocked),
                normalizer_warnings=[
                    f"{warning.code}: {warning.message}" for warning in pack.normalizer_warnings
                ],
                probability_content_quarantined=probability_blocked,
                secret_warning_detected=secret_blocked,
            )

            node_result = GeminiAssistNodeResult(
                run_id=run_id,
                status=status,
                allowed=not runtime_blocked,
                blocked=runtime_blocked,
                review_only=review_only,
                query=query,
                domain=domain,
                candidate_agent_output_created=candidate_created,
                candidate_agent_output_valid=candidate_valid,
                evidence_pack_path=evidence_pack_path,
                raw_result_path=raw_result_path,
                blocking_reasons=exclusion_reasons if runtime_blocked else [],
                warnings=list(dict.fromkeys(self._warnings + [
                    f"{warning.code}: {warning.message}" for warning in pack.normalizer_warnings
                ])),
                audit_bundle=audit_bundle,
                trial_result=trial_result,
                metadata={
                    "mock": mock,
                    "saved": False,
                    "candidate_inclusion_decision": inclusion_decision,
                },
            )
            if config.write_audit:
                node_result = self.save_audit_artifacts(node_result, config)
            if attach_review_artifact:
                node_result.updated_state = self.maybe_attach_review_artifact(state_copy, node_result)
            return node_result
        except Exception as exc:  # noqa: BLE001 - rehearsal wrapper must fail closed
            run_id = getattr(raw_result, "run_id", trial_result.run_id)
            failed_trial = trial_result.model_copy(update={"run_id": run_id, "status": "failed"})
            audit_bundle = self.build_audit_bundle(
                run_id=run_id,
                query=query,
                domain=domain,
                config=config,
                policy_reference=policy_reference,
                approval_record=approval_record,
                rollback_status=rollback_status,
                trial_result=failed_trial,
                inclusion_decision="failed",
                exclusion_reasons=[f"Assist node wrapper failed closed: {exc.__class__.__name__}"],
                failed=True,
            )
            node_result = GeminiAssistNodeResult(
                run_id=run_id,
                status="failed",
                allowed=False,
                blocked=True,
                review_only=review_only,
                query=query,
                domain=domain,
                warnings=list(dict.fromkeys(self._warnings)),
                blocking_reasons=[f"Assist node wrapper failed closed: {exc.__class__.__name__}"],
                audit_bundle=audit_bundle,
                trial_result=failed_trial,
                metadata={"mock": mock, "saved": False},
            )
            if config.write_audit:
                node_result = self.save_audit_artifacts(node_result, config)
            if attach_review_artifact:
                node_result.updated_state = self.maybe_attach_review_artifact(state_copy, node_result)
            return node_result

    def extract_query_from_state(self, state: Any) -> str:
        """Extract a user-facing research query from a ForecastState-like dict."""
        if not isinstance(state, dict):
            self._warnings.append("State input was not a dictionary; using UNKNOWN_QUERY.")
            return "UNKNOWN_QUERY"
        for key in ("scenario", "query", "user_query", "question", "prompt"):
            value = state.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        self._warnings.append("No query-like field found in state; using UNKNOWN_QUERY.")
        return "UNKNOWN_QUERY"

    def extract_domain_from_state(self, state: Any) -> str:
        """Extract a domain from flexible state fields."""
        if not isinstance(state, dict):
            self._warnings.append("State input was not a dictionary; defaulting domain to general.")
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
        self._warnings.append("No domain-like field found in state; defaulting domain to general.")
        return "general"

    def build_research_context(self, state: Any) -> Dict[str, Any]:
        """Build small public-context metadata without copying full local state."""
        if not isinstance(state, dict):
            return {}
        context: Dict[str, Any] = {}
        for key in ("domain", "time_horizon", "forecast_horizon_days"):
            value = state.get(key)
            if isinstance(value, (str, int, float)) and str(value).strip():
                context[key] = value
        planner_output = state.get("planner_output")
        if isinstance(planner_output, dict):
            for key in ("primary_domain", "time_horizon", "research_focus"):
                value = planner_output.get(key)
                if isinstance(value, (str, int, float)) and str(value).strip():
                    context[f"planner_{key}"] = value
        return context

    def run_gatekeeper(
        self,
        config: GeminiAssistConfig,
        policy_reference: Optional[GeminiPolicyApprovalReference],
        approval_record: Optional[GeminiAssistApprovalRecord],
        rollback_status: Optional[GeminiAssistRollbackStatus],
        domain: str,
    ) -> GeminiAssistTrialResult:
        """Run the Phase 4B gatekeeper before research work."""
        return self.gatekeeper.evaluate(
            config,
            approval_record=approval_record,
            policy_reference=policy_reference,
            rollback_status=rollback_status,
            domain=domain,
        )

    def run_gemini_research(
        self,
        query: str,
        context: Dict[str, Any],
        config: GeminiAssistConfig,
        mock: bool = True,
    ) -> GeminiDeepResearchResult:
        """Run mock/live research through the existing client with live guardrails."""
        prompt = build_deep_research_prompt(query, context=context)
        if not mock and not self.client.is_enabled():
            return GeminiDeepResearchResult.from_error(
                error_type="disabled",
                error_message="Live Gemini Deep Research is disabled by environment.",
                status=GeminiDeepResearchStatus.DISABLED,
                model=self.client.get_default_model(),
                mode=config.gemini_mode,
                prompt=prompt,
                retryable=False,
            )
        return asyncio.run(
            self.client.run_research(
                prompt,
                model=self.client.get_default_model(),
                timeout_seconds=config.max_latency_seconds,
                mock=mock,
            )
        )

    def normalize_result(
        self,
        result: GeminiDeepResearchResult,
        query: str,
        context: Dict[str, Any],
    ) -> GeminiEvidencePack:
        """Normalize raw research result into a local evidence pack."""
        return self.normalizer.normalize_result(
            result,
            original_question=query,
            improved_prompt=build_deep_research_prompt(query, context=context),
        )

    def build_candidate_agent_output(self, pack: GeminiEvidencePack) -> Any:
        """Build a review-only candidate output through the existing normalizer."""
        try:
            return self.normalizer.to_agent_output_candidate(pack)
        except Exception as exc:  # noqa: BLE001
            self._warnings.append(f"Candidate output conversion failed: {exc.__class__.__name__}")
            return None

    def build_audit_bundle(
        self,
        *,
        run_id: str,
        query: str,
        domain: str,
        config: GeminiAssistConfig,
        policy_reference: Optional[GeminiPolicyApprovalReference],
        approval_record: Optional[GeminiAssistApprovalRecord],
        rollback_status: Optional[GeminiAssistRollbackStatus],
        trial_result: GeminiAssistTrialResult,
        raw_result_path: Optional[str] = None,
        evidence_pack_path: Optional[str] = None,
        candidate_agent_output_summary: Optional[Dict[str, Any]] = None,
        inclusion_decision: str = "review_only",
        exclusion_reasons: Optional[List[str]] = None,
        latency_seconds: Optional[float] = None,
        timeout: bool = False,
        failed: bool = False,
        risk_flags: Optional[List[str]] = None,
        normalizer_warnings: Optional[List[str]] = None,
        probability_content_quarantined: bool = False,
        secret_warning_detected: bool = False,
    ) -> GeminiAssistAuditBundle:
        """Build a redacted audit bundle for the rehearsal path."""
        return GeminiAssistAuditBundle(
            run_id=run_id,
            query=query,
            domain=domain,
            mode=config.gemini_mode,
            insertion_point=config.insertion_point,
            config_snapshot=config.model_dump(mode="json"),
            approval_record=approval_record,
            policy_reference=policy_reference,
            rollback_status=rollback_status or GeminiAssistRollbackStatus(),
            raw_result_path=raw_result_path,
            evidence_pack_path=evidence_pack_path,
            candidate_agent_output_summary=candidate_agent_output_summary or {},
            inclusion_decision=inclusion_decision,  # type: ignore[arg-type]
            exclusion_reasons=exclusion_reasons or [],
            latency_seconds=latency_seconds,
            timeout=timeout,
            failed=failed,
            risk_flags=risk_flags or [],
            normalizer_warnings=normalizer_warnings or [],
            probability_content_quarantined=probability_content_quarantined,
            secret_warning_detected=secret_warning_detected,
            human_approval_metadata={
                "approval_id": approval_record.approval_id if approval_record else None,
                "reviewer": approval_record.reviewer if approval_record else None,
                "operator_id": approval_record.operator_id if approval_record else None,
                "human_review_completed": approval_record.human_review_completed
                if approval_record
                else False,
            },
            feature_flag_snapshot={
                "SEER_USE_GEMINI_DEEP_RESEARCH": config.use_gemini_deep_research,
                "SEER_GEMINI_MODE": config.gemini_mode,
                "SEER_GEMINI_ASSIST_ENABLED": config.assist_enabled,
                "SEER_GEMINI_ASSIST_INSERTION_POINT": config.insertion_point,
            },
            metadata={
                "trial_status": trial_result.status,
                "trial_allowed": trial_result.allowed,
                "review_only_default": True,
            },
        )

    def maybe_attach_review_artifact(
        self,
        state: Any,
        node_result: GeminiAssistNodeResult,
    ) -> Dict[str, Any]:
        """Return a cloned state with only a non-production review artifact attached."""
        cloned = self.clone_state(state)
        cloned[REVIEW_KEY] = {
            "run_id": node_result.run_id,
            "status": node_result.status,
            "audit_bundle_path": node_result.audit_bundle_path,
            "evidence_pack_path": node_result.evidence_pack_path,
            "recommendation": node_result.trial_result.recommendation
            if node_result.trial_result
            else None,
            "warnings": node_result.warnings,
        }
        return cloned

    def save_audit_artifacts(
        self,
        node_result: GeminiAssistNodeResult,
        config: GeminiAssistConfig,
    ) -> GeminiAssistNodeResult:
        """Save audit, trial, and node-result JSON under the configured audit directory."""
        if node_result.audit_bundle:
            audit_path = save_assist_audit_bundle(node_result.audit_bundle, output_dir=config.audit_dir)
            node_result.audit_bundle_path = str(audit_path)
        if node_result.trial_result:
            trial_path = save_assist_trial_result(node_result.trial_result, output_dir=config.audit_dir)
            node_result.trial_result_path = str(trial_path)
        node_path = self._save_node_result(node_result, config)
        node_result.metadata["node_result_path"] = str(node_path)
        node_result.metadata["saved"] = True
        return node_result

    def clone_state(self, state: Any) -> Dict[str, Any]:
        """Deep-copy dict-like state; malformed input becomes an empty dict."""
        if not isinstance(state, dict):
            return {}
        return copy.deepcopy(state)

    def _save_raw_result(self, result: GeminiDeepResearchResult, config: GeminiAssistConfig) -> Path:
        directory = ensure_assist_audit_dir(config) / result.run_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "raw_result.json"
        payload = self._redact_raw_result_payload(result.model_dump(mode="json"))
        path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        return path

    def _save_evidence_pack(
        self,
        pack: GeminiEvidencePack,
        config: GeminiAssistConfig,
        run_id: str,
    ) -> Path:
        directory = ensure_assist_audit_dir(config) / run_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "evidence_pack.json"
        path.write_text(
            json.dumps(pack.model_dump(mode="json"), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        return path

    def _save_node_result(self, node_result: GeminiAssistNodeResult, config: GeminiAssistConfig) -> Path:
        directory = ensure_assist_audit_dir(config) / node_result.run_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "node_result.json"
        payload = node_result.model_dump(mode="json", exclude={"updated_state"})
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return path

    def _cap_pack(
        self,
        pack: GeminiEvidencePack,
        config: GeminiAssistConfig,
    ) -> GeminiEvidencePack:
        capped_evidence = list(pack.evidence_items[: config.max_evidence_items])
        allowed_evidence_ids = {item.id for item in capped_evidence}
        capped_claims = [
            claim
            for claim in pack.claim_items
            if all(evidence_id in allowed_evidence_ids for evidence_id in claim.evidence_ids)
        ][: config.max_claims]
        if len(capped_evidence) < len(pack.evidence_items):
            self._warnings.append("Gemini evidence candidates were capped by assist config.")
        if len(capped_claims) < len(pack.claim_items):
            self._warnings.append("Gemini claim candidates were capped by assist config.")
        return pack.model_copy(update={
            "evidence_items": capped_evidence,
            "claim_items": capped_claims,
        })

    def _warning_codes(self, pack: GeminiEvidencePack) -> set[str]:
        return {warning.code for warning in pack.normalizer_warnings}

    def _candidate_valid(self, candidate: Any) -> bool:
        if candidate is None:
            return False
        if getattr(candidate, "ok", True) is False:
            return False
        return True

    def _candidate_summary(self, candidate: Any) -> Dict[str, Any]:
        if candidate is None:
            return {"created": False, "valid": False}
        if getattr(candidate, "ok", True) is False:
            return {
                "created": True,
                "valid": False,
                "error_type": getattr(candidate, "error_type", None),
                "error_message": getattr(candidate, "error_message", None),
            }
        return {
            "created": True,
            "valid": True,
            "agent_id": getattr(candidate, "agent_id", None),
            "claims_count": len(getattr(candidate, "claims", []) or []),
            "evidence_count": len(getattr(candidate, "evidence", []) or []),
            "signals_count": len(getattr(candidate, "signals", []) or []),
            "status": str(getattr(candidate, "status", "")),
        }

    def _exclusion_reasons(
        self,
        *,
        probability_blocked: bool,
        secret_blocked: bool,
        candidate_valid: bool,
        raw_result: GeminiDeepResearchResult,
    ) -> List[str]:
        reasons: List[str] = []
        if probability_blocked:
            reasons.append("Probability-like content was quarantined by assist config.")
        if secret_blocked:
            reasons.append("Secret-like content was detected and quarantined by assist config.")
        if not candidate_valid:
            reasons.append("Candidate output is not valid for review.")
        if raw_result.status == GeminiDeepResearchStatus.FAILED:
            reasons.append(raw_result.error_message or "Gemini research failed.")
        if raw_result.status == GeminiDeepResearchStatus.TIMEOUT:
            reasons.append(raw_result.error_message or "Gemini research timed out.")
        return reasons

    def _risk_flags(self, probability_blocked: bool, secret_blocked: bool) -> List[str]:
        flags: List[str] = []
        if probability_blocked:
            flags.append(PROBABILITY_WARNING)
        if secret_blocked:
            flags.append(SECRET_WARNING)
        return flags

    def _redact_raw_result_payload(self, value: Any) -> Any:
        if isinstance(value, dict):
            redacted: Dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key)
                if any(part in key_text.lower() for part in ("key", "token", "secret", "password", "credential", "api")):
                    redacted[key_text] = "[REDACTED]"
                else:
                    redacted[key_text] = self._redact_raw_result_payload(item)
            return redacted
        if isinstance(value, list):
            return [self._redact_raw_result_payload(item) for item in value]
        if isinstance(value, str):
            redact = getattr(self.normalizer, "_redact_secrets", None)
            if callable(redact):
                return redact(value)
        return value
