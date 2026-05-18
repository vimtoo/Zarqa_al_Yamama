from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.integrations.gemini_deep_research.evaluation_policy import (  # noqa: E402
    GeminiShadowEvaluationPolicy,
    get_domain_profile,
)
from app.integrations.gemini_deep_research.models import (  # noqa: E402
    AgentOverlapComparison,
    EvidenceComparison,
    GeminiShadowRun,
    RiskAssessment,
    SourceComparison,
)
from app.integrations.gemini_deep_research.storage import load_shadow_runs_from_dir  # noqa: E402


def _run(
    idx: int = 1,
    *,
    useful: int = 3,
    source_overlap: float = 0.35,
    unsupported: int = 0,
    contradictions: int = 0,
    duplicates: int = 1,
    risk: str = "low",
    source_governance_risk: str = "low",
    warnings: list[str] | None = None,
    status: str = "completed",
    context_overlap: float = 0.7,
    black_swan_overlap: float = 0.7,
    recommendation: str = "Gemini useful as assistant",
) -> GeminiShadowRun:
    return GeminiShadowRun(
        run_id=f"shadow-{idx}",
        query="Assess regional escalation risk.",
        seer_agents_used=["context_interpreter", "black_swan_generator"],
        source_comparison=SourceComparison(
            gemini_source_count=4,
            seer_source_count=4,
            source_overlap_ratio=source_overlap,
            overlapping_sources=["https://reuters.com/a"],
            unique_gemini_sources=["https://rand.org/a"] * useful,
            unique_seer_sources=[],
            gemini_domains=["reuters.com", "rand.org"],
            seer_domains=["reuters.com"],
        ),
        evidence_comparison=EvidenceComparison(
            gemini_evidence_count=4,
            seer_evidence_count=3,
            gemini_claim_count=3,
            seer_claim_count=3,
            accepted_gemini_evidence_count=4,
            rejected_gemini_evidence_count=0,
            duplicate_evidence_count=duplicates,
            unsupported_gemini_claims_count=unsupported,
            contradictions_count=contradictions,
            intelligence_gap_count=0,
        ),
        agent_overlap=AgentOverlapComparison(
            context_interpreter_overlap=context_overlap,
            black_swan_generator_overlap=black_swan_overlap,
            think_tank_analyst_overlap=0.4,
            walled_garden_analyst_overlap=0.3,
            evidence_analyst_overlap=0.5,
            useful_new_evidence_count=useful,
            seer_unique_evidence_count=1,
        ),
        risk_assessment=RiskAssessment(
            hallucination_risk=risk,
            citation_risk=risk,
            source_governance_risk=source_governance_risk,
            schema_compliance_risk=risk,
            latency_risk="low",
            cost_risk="unknown",
            dependency_risk="low",
            overall_risk=risk,
        ),
        recommendation=recommendation,
        warnings=warnings or [],
        metadata={"status": status, "latency_seconds": 120, "domain": "general"},
    )


def _runs(count: int, **kwargs) -> list[GeminiShadowRun]:
    return [_run(idx=i + 1, **kwargs) for i in range(count)]


def test_evaluate_run_returns_conservative_decision_for_one_good_run():
    decision = GeminiShadowEvaluationPolicy().evaluate_run(_run())

    assert decision.runs_evaluated == 1
    assert decision.recommendation in {"Gemini useful as shadow only", "Gemini requires human review"}
    assert decision.readiness_level in {"shadow", "human_review"}


def test_evaluate_runs_requires_minimum_runs_before_assist_trial():
    decision = GeminiShadowEvaluationPolicy().evaluate_runs(_runs(4))

    assert decision.recommendation != "Gemini ready for limited assist-mode trial"
    assert decision.required_next_runs >= 1


def test_aggregate_runs_computes_average_useful_evidence():
    aggregate = GeminiShadowEvaluationPolicy().aggregate_runs([
        _run(useful=2),
        _run(useful=4),
    ])

    assert aggregate.average_useful_new_evidence_count == 3.0


def test_aggregate_runs_computes_unsupported_claim_average():
    aggregate = GeminiShadowEvaluationPolicy().aggregate_runs([
        _run(unsupported=0),
        _run(unsupported=2),
    ])

    assert aggregate.average_unsupported_claims_count == 1.0


def test_aggregate_runs_computes_failure_timeout_ratio():
    aggregate = GeminiShadowEvaluationPolicy().aggregate_runs([
        _run(status="completed"),
        _run(status="failed"),
        _run(status="timeout"),
        _run(status="completed"),
    ])

    assert aggregate.failed_runs == 1
    assert aggregate.timeout_runs == 1
    assert aggregate.failure_or_timeout_ratio == 0.5


def test_critical_risk_blocks_assist_mode():
    runs = _runs(4) + [_run(risk="critical")]

    decision = GeminiShadowEvaluationPolicy().evaluate_runs(runs)

    assert decision.recommendation == "Gemini requires human review"
    assert decision.blocked is True
    assert any("Critical risk" in reason for reason in decision.blocking_reasons)


def test_secret_leakage_blocks_assist_and_triggers_human_review():
    runs = _runs(4) + [_run(warnings=["POSSIBLE_SECRET_LEAK: redacted secret-like content"])]

    decision = GeminiShadowEvaluationPolicy().evaluate_runs(runs)

    assert decision.human_review_required is True
    assert decision.recommendation == "Gemini requires human review"
    assert any("Secret leakage" in reason for reason in decision.blocking_reasons)


def test_probability_contamination_blocks_assist_when_required():
    runs = _runs(4) + [_run(warnings=["PROBABILITY_CONTENT_QUARANTINED: final forecast probability removed"])]

    decision = GeminiShadowEvaluationPolicy().evaluate_runs(runs)

    assert decision.recommendation != "Gemini ready for limited assist-mode trial"
    assert any("Probability contamination" in reason for reason in decision.blocking_reasons)


def test_too_few_runs_returns_shadow_or_human_review_decision():
    decision = GeminiShadowEvaluationPolicy().evaluate_runs(_runs(2))

    assert decision.readiness_level in {"shadow", "human_review"}


def test_enough_good_runs_can_produce_limited_assist_trial():
    decision = GeminiShadowEvaluationPolicy().evaluate_runs(_runs(5), domain="general")

    assert decision.recommendation == "Gemini ready for limited assist-mode trial"
    assert decision.readiness_level == "limited_assist_trial"


def test_replacement_candidate_is_never_approved_only_candidate():
    decision = GeminiShadowEvaluationPolicy().evaluate_runs(
        _runs(10),
        target_agent="context_interpreter",
    )

    assert "candidate for future ContextInterpreter replacement" in decision.recommendation
    assert "approved" not in decision.recommendation.lower()
    assert decision.human_review_required is True


def test_context_interpreter_replacement_candidate_requires_target_and_enough_runs():
    policy = GeminiShadowEvaluationPolicy()

    without_target = policy.evaluate_runs(_runs(10))
    with_target = policy.evaluate_runs(_runs(10), target_agent="context_interpreter")

    assert without_target.recommendation != "Gemini candidate for future ContextInterpreter replacement"
    assert with_target.recommendation == "Gemini candidate for future ContextInterpreter replacement"


def test_black_swan_replacement_candidate_requires_target_and_enough_runs():
    decision = GeminiShadowEvaluationPolicy().evaluate_runs(
        _runs(10, black_swan_overlap=0.75),
        target_agent="black_swan_generator",
    )

    assert decision.recommendation == "Gemini candidate for future BlackSwanGenerator replacement"
    assert decision.human_review_required is True


def test_sensitive_domains_require_human_review_above_shadow():
    for domain in ("geopolitics", "security", "elections", "finance"):
        decision = GeminiShadowEvaluationPolicy().evaluate_runs(_runs(5), domain=domain)
        assert decision.human_review_required is True
        assert decision.recommendation == "Gemini requires human review"


def test_malformed_incomplete_run_does_not_crash():
    decision = GeminiShadowEvaluationPolicy().evaluate_runs(["not a run"])  # type: ignore[list-item]

    assert decision.recommendation == "Gemini requires human review"
    assert decision.metadata["aggregate"]["malformed_runs"] == 1


def test_unknown_risk_does_not_pass_assist_thresholds():
    decision = GeminiShadowEvaluationPolicy().evaluate_runs(_runs(5, risk="unknown"))

    assert decision.recommendation != "Gemini ready for limited assist-mode trial"
    assert any("Unknown risk" in item for item in decision.failed_criteria)


def test_policy_report_contains_all_required_sections():
    policy = GeminiShadowEvaluationPolicy()
    decision = policy.evaluate_runs(_runs(5))
    report = policy.render_policy_report(decision)

    for section in [
        "# Gemini Deep Research Shadow Evaluation Policy Report",
        "## 1. Decision Summary",
        "## 2. Runs Evaluated",
        "## 3. Metric Summary",
        "## 4. Risk Summary",
        "## 5. Passed Criteria",
        "## 6. Failed Criteria",
        "## 7. Blocking Reasons",
        "## 8. Recommendation",
        "## 9. Required Next Runs",
        "## 10. Next Steps",
    ]:
        assert section in report


def test_domain_profiles_load_correctly():
    finance = get_domain_profile("finance")
    general = get_domain_profile("general")

    assert finance.domain == "finance"
    assert finance.human_review_above_shadow is True
    assert finance.thresholds.max_average_latency_seconds < general.thresholds.max_average_latency_seconds


def test_storage_helper_loads_multiple_shadow_runs_from_directory(tmp_path):
    flat = _run(1)
    nested = _run(2)
    (tmp_path / f"{flat.run_id}.json").write_text(flat.model_dump_json(), encoding="utf-8")
    nested_dir = tmp_path / nested.run_id
    nested_dir.mkdir()
    (nested_dir / "shadow_run.json").write_text(nested.model_dump_json(), encoding="utf-8")
    (nested_dir / "runner_result.json").write_text(json.dumps({"status": "mock_completed"}), encoding="utf-8")

    loaded = load_shadow_runs_from_dir(tmp_path)

    assert {run.run_id for run in loaded} == {flat.run_id, nested.run_id}


def test_no_forecast_artifacts_workflow_or_agent_output_targets_are_referenced():
    source = Path(
        "backend/app/integrations/gemini_deep_research/evaluation_policy.py"
    ).read_text(encoding="utf-8")

    assert "workflow.py" not in source
    assert "from app.workflow" not in source
    assert ("agent" + "_outputs") not in source
    for model_name in ("Signal", "HorizonForecast", "FusionResult"):
        assert f"{model_name}(" not in source
