"""Phase 3C repeatable local evaluation policy for Gemini shadow runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from app.integrations.gemini_deep_research.models import (
    DomainEvaluationProfile,
    EvaluationThresholds,
    GeminiEvaluationDecision,
    GeminiShadowRun,
    ShadowRunAggregate,
)


RISK_RANK = {"low": 0, "unknown": 1, "medium": 2, "high": 3, "critical": 4}
SENSITIVE_DOMAINS = {"geopolitics", "security", "elections", "finance"}
TARGET_CONTEXT = "context_interpreter"
TARGET_BLACK_SWAN = "black_swan_generator"


def get_domain_profile(domain: Optional[str]) -> DomainEvaluationProfile:
    """Return a conservative domain-specific evaluation profile."""
    normalized = (domain or "general").strip().lower() or "general"
    thresholds = EvaluationThresholds()
    notes: List[str] = []
    human_review_above_shadow = False

    if normalized in {"geopolitics", "security"}:
        thresholds = thresholds.model_copy(update={
            "minimum_runs_for_replacement_candidate": 15,
            "max_high_risk_runs_ratio": 0.1,
            "max_average_unsupported_claims": 0.5,
            "max_average_contradictions": 1.0,
        })
        human_review_above_shadow = True
        notes.append("Geopolitics and security require stricter source governance and review.")
    elif normalized == "finance":
        thresholds = thresholds.model_copy(update={
            "max_average_latency_seconds": 600.0,
            "min_average_source_overlap": 0.3,
            "max_average_unsupported_claims": 0.5,
        })
        human_review_above_shadow = True
        notes.append("Finance requires stricter freshness, source quality, and probability separation.")
    elif normalized == "elections":
        thresholds = thresholds.model_copy(update={
            "minimum_runs_for_replacement_candidate": 15,
            "min_average_source_overlap": 0.3,
            "max_average_unsupported_claims": 0.0,
            "max_average_contradictions": 1.0,
        })
        human_review_above_shadow = True
        notes.append("Elections require official or primary reporting preference and human review.")
    elif normalized in {"policy", "macroeconomics", "technology", "general"}:
        notes.append("Default conservative thresholds apply.")
    else:
        normalized = "general"
        notes.append("Unknown domain fell back to general thresholds.")

    return DomainEvaluationProfile(
        domain=normalized,
        thresholds=thresholds,
        human_review_above_shadow=human_review_above_shadow,
        notes=notes,
    )


class GeminiShadowEvaluationPolicy:
    """Evaluate one or more local Gemini shadow runs for readiness progression."""

    def __init__(self, thresholds: Optional[EvaluationThresholds] = None) -> None:
        self.default_thresholds = thresholds or EvaluationThresholds()

    def evaluate_run(
        self,
        shadow_run: GeminiShadowRun | Dict[str, Any],
        domain: Optional[str] = None,
        target_agent: Optional[str] = None,
    ) -> GeminiEvaluationDecision:
        """Evaluate a single shadow run conservatively."""
        return self.evaluate_runs([shadow_run], domain=domain, target_agent=target_agent)

    def evaluate_runs(
        self,
        shadow_runs: Sequence[GeminiShadowRun | Dict[str, Any]],
        domain: Optional[str] = None,
        target_agent: Optional[str] = None,
    ) -> GeminiEvaluationDecision:
        """Aggregate and decide readiness for multiple shadow runs."""
        aggregate = self.aggregate_runs(shadow_runs)
        return self.decide_readiness(aggregate, domain=domain, target_agent=target_agent)

    def aggregate_runs(
        self,
        shadow_runs: Sequence[GeminiShadowRun | Dict[str, Any]],
    ) -> ShadowRunAggregate:
        """Compute repeatable metrics from flexible local shadow-run inputs."""
        total = len(shadow_runs or [])
        values = {
            "useful": [],
            "source_overlap": [],
            "unsupported": [],
            "contradictions": [],
            "duplicates": [],
            "latency": [],
        }
        recommendation_distribution: Dict[str, int] = {}
        risk_distribution: Dict[str, int] = {}
        agent_scores: Dict[str, List[float]] = {
            "context_interpreter": [],
            "black_swan_generator": [],
            "think_tank_analyst": [],
            "walled_garden_analyst": [],
            "evidence_analyst": [],
        }
        warnings: List[str] = []
        domains: List[str] = []
        counts = {
            "successful": 0,
            "failed": 0,
            "timeout": 0,
            "disabled": 0,
            "malformed": 0,
            "high": 0,
            "critical": 0,
            "unknown": 0,
            "source_governance_high": 0,
            "incomplete": 0,
        }
        secret_leakage = False
        probability_contamination = False

        for raw_run in shadow_runs or []:
            run, status, malformed, extra_warnings = self._coerce_run(raw_run)
            warnings.extend(extra_warnings)
            if malformed or run is None:
                counts["malformed"] += 1
                counts["incomplete"] += 1
                counts["failed"] += 1
                risk_distribution["unknown"] = risk_distribution.get("unknown", 0) + 1
                counts["unknown"] += 1
                continue

            status = status or self._infer_status(run)
            if status in {"failed", "failure"}:
                counts["failed"] += 1
            elif status == "timeout":
                counts["timeout"] += 1
            elif status == "disabled":
                counts["disabled"] += 1
            else:
                counts["successful"] += 1

            risk = self._risk_label(run)
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
            if risk == "critical":
                counts["critical"] += 1
            if risk == "high":
                counts["high"] += 1
            if risk == "unknown":
                counts["unknown"] += 1
            if run.risk_assessment.source_governance_risk == "high":
                counts["source_governance_high"] += 1

            recommendation_distribution[run.recommendation] = recommendation_distribution.get(run.recommendation, 0) + 1
            values["useful"].append(float(run.agent_overlap.useful_new_evidence_count))
            values["source_overlap"].append(float(run.source_comparison.source_overlap_ratio))
            values["unsupported"].append(float(run.evidence_comparison.unsupported_gemini_claims_count))
            values["contradictions"].append(float(run.evidence_comparison.contradictions_count))
            values["duplicates"].append(float(run.evidence_comparison.duplicate_evidence_count))

            latency = self._extract_latency(run)
            if latency is not None:
                values["latency"].append(latency)

            for key in agent_scores:
                field = f"{key}_overlap"
                score = getattr(run.agent_overlap, field, None)
                if isinstance(score, (int, float)):
                    agent_scores[key].append(float(score))

            if run.query:
                domain_guess = self._metadata_string(run.metadata, "domain")
                if domain_guess:
                    domains.append(domain_guess)
            run_warnings = list(run.warnings)
            run_warnings.extend(run.evidence_comparison.evidence_gap_notes)
            warnings.extend(run_warnings)
            if self._contains_secret_warning(run_warnings):
                secret_leakage = True
            if self._contains_probability_warning(run_warnings):
                probability_contamination = True
            if self._run_incomplete(run):
                counts["incomplete"] += 1

        failure_or_timeout = counts["failed"] + counts["timeout"]
        return ShadowRunAggregate(
            total_runs=total,
            successful_runs=counts["successful"],
            failed_runs=counts["failed"],
            timeout_runs=counts["timeout"],
            disabled_runs=counts["disabled"],
            malformed_runs=counts["malformed"],
            high_risk_runs=counts["high"],
            critical_risk_runs=counts["critical"],
            unknown_risk_runs=counts["unknown"],
            average_useful_new_evidence_count=self._avg(values["useful"]),
            average_source_overlap_ratio=self._avg(values["source_overlap"]),
            average_unsupported_claims_count=self._avg(values["unsupported"]),
            average_contradictions_count=self._avg(values["contradictions"]),
            average_duplicate_evidence_count=self._avg(values["duplicates"]),
            average_latency_seconds=self._avg_or_none(values["latency"]),
            failure_or_timeout_ratio=round(failure_or_timeout / total, 4) if total else 1.0,
            recommendation_distribution=recommendation_distribution,
            overall_risk_distribution=risk_distribution,
            agent_overlap_averages={
                key: self._avg_or_none(scores)
                for key, scores in agent_scores.items()
            },
            domains_tested=sorted(set(domains)),
            warnings_collected=list(dict.fromkeys(warnings))[:100],
            secret_leakage_detected=secret_leakage,
            probability_contamination_detected=probability_contamination,
            source_governance_high_runs=counts["source_governance_high"],
            incomplete_input_runs=counts["incomplete"],
        )

    def load_runs_from_dir(self, path: str | Path) -> List[GeminiShadowRun]:
        """Load local shadow runs from a directory of Phase 3A/3B JSON artifacts."""
        from app.integrations.gemini_deep_research.storage import load_shadow_runs_from_dir  # noqa: PLC0415

        return load_shadow_runs_from_dir(path)

    def decide_readiness(
        self,
        aggregate: ShadowRunAggregate,
        domain: Optional[str] = None,
        target_agent: Optional[str] = None,
    ) -> GeminiEvaluationDecision:
        """Produce a conservative readiness decision from aggregate metrics."""
        profile = get_domain_profile(domain)
        thresholds = self._thresholds_for_profile(profile)
        normalized_target = (target_agent or "").strip().lower() or None
        minimum_required = self._minimum_required(thresholds, normalized_target)
        passed: List[str] = []
        failed: List[str] = []
        blocking: List[str] = []
        human_review_required = False

        self._criterion(
            aggregate.total_runs >= thresholds.minimum_runs_for_shadow_value,
            f"At least {thresholds.minimum_runs_for_shadow_value} runs exist for shadow-value assessment.",
            "Too few runs for repeatable shadow-value assessment.",
            passed,
            failed,
        )
        self._criterion(
            aggregate.average_useful_new_evidence_count >= thresholds.min_average_useful_new_evidence,
            "Average useful new evidence meets threshold.",
            "Average useful new evidence is below threshold.",
            passed,
            failed,
        )
        self._criterion(
            aggregate.average_source_overlap_ratio >= thresholds.min_average_source_overlap,
            "Average source overlap meets threshold.",
            "Average source overlap is below threshold.",
            passed,
            failed,
        )
        self._criterion(
            aggregate.average_unsupported_claims_count <= thresholds.max_average_unsupported_claims,
            "Unsupported claim average is acceptable.",
            "Unsupported claim average exceeds threshold.",
            passed,
            failed,
        )
        self._criterion(
            aggregate.average_contradictions_count <= thresholds.max_average_contradictions,
            "Contradiction average is acceptable.",
            "Contradiction average exceeds threshold.",
            passed,
            failed,
        )
        self._criterion(
            aggregate.failure_or_timeout_ratio <= thresholds.max_failure_or_timeout_ratio,
            "Failure and timeout ratio is acceptable.",
            "Failure or timeout ratio exceeds threshold.",
            passed,
            failed,
        )

        high_risk_ratio = aggregate.high_risk_runs / aggregate.total_runs if aggregate.total_runs else 1.0
        if high_risk_ratio > thresholds.max_high_risk_runs_ratio:
            blocking.append("High-risk run ratio exceeds policy threshold.")
        if aggregate.critical_risk_runs > thresholds.max_critical_risk_runs:
            blocking.append("Critical risk was observed.")
            human_review_required = True
        if aggregate.secret_leakage_detected and thresholds.require_zero_secret_leakage:
            blocking.append("Secret leakage warning was observed.")
            human_review_required = True
        if aggregate.probability_contamination_detected and thresholds.require_zero_probability_contamination_for_assist:
            blocking.append("Probability contamination warning blocks assist-mode progression.")
        if aggregate.source_governance_high_runs:
            blocking.append("Source-governance risk was high in at least one run.")
            human_review_required = True
        if aggregate.incomplete_input_runs or aggregate.malformed_runs:
            blocking.append("Input data was incomplete or malformed.")
            human_review_required = True
        if aggregate.unknown_risk_runs:
            failed.append("Unknown risk labels prevent assist or replacement readiness.")

        recommendation, readiness = self._base_recommendation(
            aggregate,
            thresholds,
            normalized_target,
            high_risk_ratio,
            blocking,
        )

        if normalized_target and recommendation not in {
            "Gemini candidate for future ContextInterpreter replacement",
            "Gemini candidate for future BlackSwanGenerator replacement",
        }:
            human_review_required = True
            if aggregate.total_runs < thresholds.minimum_runs_for_replacement_candidate:
                blocking.append("Replacement-candidate evaluation was requested with too few runs.")

        if profile.human_review_above_shadow and readiness in {
            "assistant_candidate",
            "limited_assist_trial",
            "replacement_candidate",
        }:
            human_review_required = True
            if readiness != "replacement_candidate":
                recommendation = "Gemini requires human review"
                readiness = "human_review"
                blocking.append(f"{profile.domain} domain requires human review before readiness above shadow.")

        if readiness == "replacement_candidate" and thresholds.require_human_review_for_replacement:
            human_review_required = True

        if aggregate.critical_risk_runs or aggregate.secret_leakage_detected:
            recommendation = "Gemini requires human review"
            readiness = "human_review"
        elif aggregate.incomplete_input_runs or aggregate.malformed_runs:
            recommendation = "Gemini requires human review"
            readiness = "human_review"
        elif recommendation == "Gemini ready for limited assist-mode trial" and blocking:
            recommendation = "Gemini requires human review" if human_review_required else "Gemini useful as shadow only"
            readiness = "human_review" if human_review_required else "shadow"

        blocked = bool(blocking)
        if recommendation == "Gemini requires human review":
            human_review_required = True
            blocked = True

        required_next_runs = max(0, minimum_required - aggregate.total_runs)
        decision = GeminiEvaluationDecision(
            domain=profile.domain,
            target_agent=normalized_target,
            runs_evaluated=aggregate.total_runs,
            minimum_runs_required=minimum_required,
            recommendation=recommendation,  # type: ignore[arg-type]
            readiness_level=readiness,  # type: ignore[arg-type]
            blocked=blocked,
            blocking_reasons=list(dict.fromkeys(blocking)),
            passed_criteria=passed,
            failed_criteria=failed,
            risk_summary=self._risk_summary(aggregate),
            metric_summary=self._metric_summary(aggregate),
            required_next_runs=required_next_runs,
            human_review_required=human_review_required,
            next_steps=self._next_steps(recommendation, required_next_runs, normalized_target, profile.domain),
            metadata={
                "thresholds": thresholds.model_dump(),
                "domain_profile_notes": profile.notes,
                "aggregate": aggregate.model_dump(),
            },
        )
        return decision

    def render_policy_report(self, decision: GeminiEvaluationDecision | Dict[str, Any]) -> str:
        """Render a human-readable policy report for review."""
        item = decision if isinstance(decision, GeminiEvaluationDecision) else GeminiEvaluationDecision.model_validate(decision)
        metrics = item.metric_summary
        risk = item.risk_summary
        return "\n".join([
            "# Gemini Deep Research Shadow Evaluation Policy Report",
            "",
            "## 1. Decision Summary",
            f"- decision_id: {item.decision_id}",
            f"- timestamp: {item.timestamp.isoformat()}",
            f"- domain: {item.domain}",
            f"- target_agent: {item.target_agent or 'none'}",
            f"- recommendation: {item.recommendation}",
            f"- readiness_level: {item.readiness_level}",
            f"- blocked: {item.blocked}",
            f"- human_review_required: {item.human_review_required}",
            "",
            "## 2. Runs Evaluated",
            f"- runs evaluated: {item.runs_evaluated}",
            f"- minimum runs required: {item.minimum_runs_required}",
            f"- successful runs: {metrics.get('successful_runs', 0)}",
            f"- failed runs: {metrics.get('failed_runs', 0)}",
            f"- timeout runs: {metrics.get('timeout_runs', 0)}",
            f"- disabled runs: {metrics.get('disabled_runs', 0)}",
            "",
            "## 3. Metric Summary",
            f"- average useful new evidence: {metrics.get('average_useful_new_evidence_count', 0.0)}",
            f"- average source overlap: {metrics.get('average_source_overlap_ratio', 0.0)}",
            f"- average unsupported claims: {metrics.get('average_unsupported_claims_count', 0.0)}",
            f"- average contradictions: {metrics.get('average_contradictions_count', 0.0)}",
            f"- average duplicate evidence: {metrics.get('average_duplicate_evidence_count', 0.0)}",
            f"- average latency seconds: {metrics.get('average_latency_seconds')}",
            f"- failure/timeout ratio: {metrics.get('failure_or_timeout_ratio', 1.0)}",
            "",
            "## 4. Risk Summary",
            f"- high risk runs: {risk.get('high_risk_runs', 0)}",
            f"- critical risk runs: {risk.get('critical_risk_runs', 0)}",
            f"- risk distribution: {risk.get('overall_risk_distribution', {})}",
            f"- secret leakage detected: {risk.get('secret_leakage_detected', False)}",
            f"- probability contamination detected: {risk.get('probability_contamination_detected', False)}",
            "",
            "## 5. Passed Criteria",
            *self._markdown_list(item.passed_criteria),
            "",
            "## 6. Failed Criteria",
            *self._markdown_list(item.failed_criteria),
            "",
            "## 7. Blocking Reasons",
            *self._markdown_list(item.blocking_reasons),
            "",
            "## 8. Recommendation",
            self._recommendation_explanation(item),
            "",
            "## 9. Required Next Runs",
            f"{item.required_next_runs} additional run(s) are required for {item.target_agent or 'general'} in {item.domain}.",
            "",
            "## 10. Next Steps",
            *self._markdown_list(item.next_steps),
            "",
        ])

    def save_policy_report(
        self,
        decision: GeminiEvaluationDecision,
        output_path: str | Path | None = None,
    ) -> Path:
        """Save a policy report under docs by default."""
        from app.integrations.gemini_deep_research.storage import save_policy_report  # noqa: PLC0415

        return save_policy_report(decision, output_path=output_path)

    def _thresholds_for_profile(self, profile: DomainEvaluationProfile) -> EvaluationThresholds:
        if self.default_thresholds == EvaluationThresholds():
            return profile.thresholds
        return self.default_thresholds

    def _minimum_required(self, thresholds: EvaluationThresholds, target_agent: Optional[str]) -> int:
        if target_agent in {TARGET_CONTEXT, TARGET_BLACK_SWAN}:
            return thresholds.minimum_runs_for_replacement_candidate
        return thresholds.minimum_runs_for_assist_trial

    def _base_recommendation(
        self,
        aggregate: ShadowRunAggregate,
        thresholds: EvaluationThresholds,
        target_agent: Optional[str],
        high_risk_ratio: float,
        blocking: List[str],
    ) -> tuple[str, str]:
        if aggregate.total_runs == 0:
            return "Gemini requires human review", "human_review"

        if target_agent == TARGET_CONTEXT:
            return self._replacement_recommendation(
                aggregate,
                thresholds,
                "Gemini candidate for future ContextInterpreter replacement",
                "context_interpreter",
            )
        if target_agent == TARGET_BLACK_SWAN:
            return self._replacement_recommendation(
                aggregate,
                thresholds,
                "Gemini candidate for future BlackSwanGenerator replacement",
                "black_swan_generator",
            )

        if (
            aggregate.total_runs >= thresholds.minimum_runs_for_shadow_value
            and aggregate.average_useful_new_evidence_count < thresholds.min_average_useful_new_evidence
            and (
                aggregate.average_unsupported_claims_count > thresholds.max_average_unsupported_claims
                or aggregate.failure_or_timeout_ratio > thresholds.max_failure_or_timeout_ratio
                or high_risk_ratio > thresholds.max_high_risk_runs_ratio
            )
        ):
            return "Gemini not useful", "none"

        if aggregate.total_runs < thresholds.minimum_runs_for_shadow_value:
            return "Gemini useful as shadow only", "shadow"

        value_ok = aggregate.average_useful_new_evidence_count >= thresholds.min_average_useful_new_evidence
        claims_ok = aggregate.average_unsupported_claims_count <= thresholds.max_average_unsupported_claims
        contradictions_ok = aggregate.average_contradictions_count <= thresholds.max_average_contradictions
        overlap_ok = aggregate.average_source_overlap_ratio >= thresholds.min_average_source_overlap
        failure_ok = aggregate.failure_or_timeout_ratio <= thresholds.max_failure_or_timeout_ratio
        risk_ok = (
            high_risk_ratio <= thresholds.max_high_risk_runs_ratio
            and aggregate.critical_risk_runs == 0
            and aggregate.unknown_risk_runs == 0
        )
        contamination_ok = not aggregate.secret_leakage_detected and not aggregate.probability_contamination_detected

        if (
            aggregate.total_runs >= thresholds.minimum_runs_for_assist_trial
            and value_ok
            and claims_ok
            and contradictions_ok
            and overlap_ok
            and failure_ok
            and risk_ok
            and contamination_ok
            and not blocking
        ):
            return "Gemini ready for limited assist-mode trial", "limited_assist_trial"

        if value_ok and claims_ok and contradictions_ok and aggregate.critical_risk_runs == 0:
            return "Gemini useful as assistant", "assistant_candidate"

        return "Gemini useful as shadow only", "shadow"

    def _replacement_recommendation(
        self,
        aggregate: ShadowRunAggregate,
        thresholds: EvaluationThresholds,
        label: str,
        agent_key: str,
    ) -> tuple[str, str]:
        overlap = aggregate.agent_overlap_averages.get(agent_key)
        if (
            aggregate.total_runs >= thresholds.minimum_runs_for_replacement_candidate
            and aggregate.average_useful_new_evidence_count >= thresholds.min_average_useful_new_evidence
            and aggregate.average_unsupported_claims_count <= min(0.25, thresholds.max_average_unsupported_claims)
            and aggregate.average_contradictions_count <= thresholds.max_average_contradictions
            and aggregate.failure_or_timeout_ratio <= thresholds.max_failure_or_timeout_ratio
            and aggregate.critical_risk_runs == 0
            and aggregate.high_risk_runs == 0
            and aggregate.unknown_risk_runs == 0
            and not aggregate.secret_leakage_detected
            and not aggregate.probability_contamination_detected
            and overlap is not None
            and overlap >= max(0.5, thresholds.min_average_source_overlap)
        ):
            return label, "replacement_candidate"
        return "Gemini requires human review", "human_review"

    def _coerce_run(
        self,
        raw_run: GeminiShadowRun | Dict[str, Any],
    ) -> tuple[Optional[GeminiShadowRun], Optional[str], bool, List[str]]:
        warnings: List[str] = []
        status: Optional[str] = None
        if isinstance(raw_run, GeminiShadowRun):
            status = self._metadata_string(raw_run.metadata, "status")
            return raw_run, status, False, warnings
        if not isinstance(raw_run, dict):
            warnings.append("Malformed shadow run input was not a dictionary or GeminiShadowRun.")
            return None, None, True, warnings

        status = str(raw_run.get("status") or raw_run.get("runner_status") or "").lower() or None
        candidate = raw_run.get("shadow_run") if isinstance(raw_run.get("shadow_run"), dict) else raw_run
        if "shadow_run_json" in raw_run and isinstance(raw_run["shadow_run_json"], dict):
            candidate = raw_run["shadow_run_json"]
        try:
            run = GeminiShadowRun.model_validate(candidate)
            if status:
                run.metadata["status"] = status
            return run, status or self._metadata_string(run.metadata, "status"), False, warnings
        except Exception:
            warnings.append("Malformed or incomplete shadow run input could not be validated.")
            return None, status, True, warnings

    def _infer_status(self, run: GeminiShadowRun) -> str:
        status = self._metadata_string(run.metadata, "status")
        if status:
            return status
        joined_warnings = " ".join(run.warnings + run.evidence_comparison.evidence_gap_notes).lower()
        if "timeout" in joined_warnings:
            return "timeout"
        if "disabled" in joined_warnings:
            return "disabled"
        if "failed" in joined_warnings or "system fault" in joined_warnings:
            return "failed"
        return "completed"

    def _risk_label(self, run: GeminiShadowRun) -> str:
        risk = str(run.risk_assessment.overall_risk or "unknown").lower()
        return risk if risk in RISK_RANK else "unknown"

    def _extract_latency(self, run: GeminiShadowRun) -> Optional[float]:
        for key in ("latency_seconds", "duration_seconds"):
            value = run.metadata.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        nested = run.metadata.get("usage") or run.metadata.get("cost") or {}
        if isinstance(nested, dict):
            value = nested.get("latency_seconds")
            if isinstance(value, (int, float)):
                return float(value)
        return None

    def _run_incomplete(self, run: GeminiShadowRun) -> bool:
        return not run.source_comparison or not run.evidence_comparison or not run.risk_assessment

    def _metadata_string(self, metadata: Dict[str, Any], key: str) -> Optional[str]:
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
        return None

    def _contains_secret_warning(self, warnings: Iterable[str]) -> bool:
        joined = " ".join(warnings).lower()
        return "possible_secret_leak" in joined or "secret leakage" in joined or "secret-like" in joined

    def _contains_probability_warning(self, warnings: Iterable[str]) -> bool:
        joined = " ".join(warnings).lower()
        return "probability_content_quarantined" in joined or "probability contamination" in joined

    def _criterion(
        self,
        condition: bool,
        passed_text: str,
        failed_text: str,
        passed: List[str],
        failed: List[str],
    ) -> None:
        if condition:
            passed.append(passed_text)
        else:
            failed.append(failed_text)

    def _risk_summary(self, aggregate: ShadowRunAggregate) -> Dict[str, Any]:
        return {
            "high_risk_runs": aggregate.high_risk_runs,
            "critical_risk_runs": aggregate.critical_risk_runs,
            "unknown_risk_runs": aggregate.unknown_risk_runs,
            "overall_risk_distribution": aggregate.overall_risk_distribution,
            "secret_leakage_detected": aggregate.secret_leakage_detected,
            "probability_contamination_detected": aggregate.probability_contamination_detected,
            "source_governance_high_runs": aggregate.source_governance_high_runs,
        }

    def _metric_summary(self, aggregate: ShadowRunAggregate) -> Dict[str, Any]:
        return {
            "total_runs": aggregate.total_runs,
            "successful_runs": aggregate.successful_runs,
            "failed_runs": aggregate.failed_runs,
            "timeout_runs": aggregate.timeout_runs,
            "disabled_runs": aggregate.disabled_runs,
            "average_useful_new_evidence_count": aggregate.average_useful_new_evidence_count,
            "average_source_overlap_ratio": aggregate.average_source_overlap_ratio,
            "average_unsupported_claims_count": aggregate.average_unsupported_claims_count,
            "average_contradictions_count": aggregate.average_contradictions_count,
            "average_duplicate_evidence_count": aggregate.average_duplicate_evidence_count,
            "average_latency_seconds": aggregate.average_latency_seconds,
            "failure_or_timeout_ratio": aggregate.failure_or_timeout_ratio,
            "recommendation_distribution": aggregate.recommendation_distribution,
            "agent_overlap_averages": aggregate.agent_overlap_averages,
            "malformed_runs": aggregate.malformed_runs,
            "incomplete_input_runs": aggregate.incomplete_input_runs,
        }

    def _next_steps(
        self,
        recommendation: str,
        required_next_runs: int,
        target_agent: Optional[str],
        domain: str,
    ) -> List[str]:
        steps = []
        if required_next_runs:
            steps.append(f"Run {required_next_runs} additional shadow comparison(s) for {domain}.")
        if target_agent:
            steps.append(f"Keep {target_agent} in shadow comparison only; do not replace the local agent.")
        if recommendation == "Gemini requires human review":
            steps.append("Perform human review of source governance, contradictions, and risk notes.")
        if recommendation == "Gemini ready for limited assist-mode trial":
            steps.append("Design a separate assist-mode trial plan with explicit rollback and no production default changes.")
        if "replacement" in recommendation.lower():
            steps.append("Treat this as future-candidate status only; approval would require a separate governance review.")
        if not steps:
            steps.append("Continue collecting shadow runs before changing any operational mode.")
        return steps

    def _recommendation_explanation(self, decision: GeminiEvaluationDecision) -> str:
        if decision.recommendation == "Gemini ready for limited assist-mode trial":
            return "Gemini met repeat-run thresholds for a limited, reversible assist-mode trial outside default production behavior."
        if "candidate for future" in decision.recommendation:
            return "Gemini met candidate thresholds, but this is not approval to replace an agent; human review remains required."
        if decision.recommendation == "Gemini requires human review":
            return "The aggregate contains risk, governance, completeness, or target-agent concerns that require human review."
        return "The recommendation preserves shadow-first evaluation until repeatable evidence supports a higher readiness level."

    def _markdown_list(self, values: Sequence[str]) -> List[str]:
        return [f"- {value}" for value in values] if values else ["- none"]

    def _avg(self, values: Sequence[float]) -> float:
        return round(sum(values) / len(values), 4) if values else 0.0

    def _avg_or_none(self, values: Sequence[float]) -> Optional[float]:
        return round(sum(values) / len(values), 4) if values else None
