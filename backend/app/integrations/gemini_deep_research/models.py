"""Models for isolated Gemini Deep Research interaction metadata.

Phase 1 deliberately avoids importing TheSeer's production graph contracts.
These models represent raw interaction lifecycle data only; they are not
EvidenceItem, ClaimItem, Signal, HorizonForecast, or FusionResult objects.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for integration metadata."""
    return datetime.now(timezone.utc)


class GeminiDeepResearchStatus(str, Enum):
    """Lifecycle status for Phase 1 Deep Research wrapper results."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    DISABLED = "disabled"


class GeminiDeepResearchError(BaseModel):
    """Structured, secret-safe error details."""

    error_type: str = Field(..., description="Stable machine-readable error kind")
    error_message: str = Field(..., description="Human-readable error without secrets")
    retryable: bool = Field(default=True)
    raw_error: Optional[Dict[str, Any]] = Field(default=None)


class GeminiInteractionMetadata(BaseModel):
    """Metadata captured from Gemini Interactions API lifecycle events."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    interaction_id: Optional[str] = None
    model: str = "deep-research-preview-04-2026"
    mode: str = "shadow"
    status: GeminiDeepResearchStatus = GeminiDeepResearchStatus.CREATED
    created_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = 900
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Optional[Dict[str, Any]] = None
    cost: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GeminiDeepResearchRequest(BaseModel):
    """Request object for creating a background Deep Research interaction."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    prompt: str
    model: str = "deep-research-preview-04-2026"
    mode: str = "shadow"
    timeout_seconds: int = 900
    collaborative_planning: bool = False
    visualization: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class GeminiDeepResearchResult(BaseModel):
    """Raw Phase 1 result from creating and polling a Gemini interaction."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    interaction_id: Optional[str] = None
    model: str = "deep-research-preview-04-2026"
    mode: str = "shadow"
    prompt: Optional[str] = None
    status: GeminiDeepResearchStatus = GeminiDeepResearchStatus.CREATED
    created_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = 900
    raw_response: Optional[Dict[str, Any]] = None
    raw_report: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    error: Optional[GeminiDeepResearchError] = None
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Optional[Dict[str, Any]] = None
    cost: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_error(
        cls,
        *,
        error_type: str,
        error_message: str,
        run_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        model: str = "deep-research-preview-04-2026",
        mode: str = "shadow",
        prompt: Optional[str] = None,
        status: GeminiDeepResearchStatus = GeminiDeepResearchStatus.FAILED,
        timeout_seconds: int = 900,
        raw_response: Optional[Dict[str, Any]] = None,
        retryable: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "GeminiDeepResearchResult":
        """Build a result carrying structured error fields."""
        err = GeminiDeepResearchError(
            error_type=error_type,
            error_message=error_message,
            retryable=retryable,
        )
        return cls(
            run_id=run_id or str(uuid4()),
            interaction_id=interaction_id,
            model=model,
            mode=mode,
            prompt=prompt,
            status=status,
            completed_at=utc_now(),
            timeout_seconds=timeout_seconds,
            raw_response=raw_response,
            error=err,
            error_type=error_type,
            error_message=error_message,
            metadata=metadata or {},
        )


class GeminiNormalizerWarning(BaseModel):
    """Warning emitted while normalizing raw Gemini research output."""

    code: str
    message: str
    severity: str = "MEDIUM"


class GeminiIntelligenceGapCandidate(BaseModel):
    """Local IntelligenceGap-like candidate for Phase 2 normalization."""

    reason: str
    missing_inputs: List[str] = Field(default_factory=list)
    attempted_sources: List[str] = Field(default_factory=list)
    retryable: bool = True
    severity: str = "MEDIUM"


class GeminiSourceCandidate(BaseModel):
    """Source candidate extracted from a raw Gemini report."""

    source_id: str
    title: Optional[str] = None
    url: str
    canonical_url: str
    domain: str
    publisher: Optional[str] = None
    published_at: Optional[datetime] = None
    retrieved_at: datetime = Field(default_factory=utc_now)
    source_type_hint: str = "aggregator"
    reliability_notes: Optional[str] = None
    citation_markers: List[str] = Field(default_factory=list)


class GeminiEvidenceCandidate(BaseModel):
    """EvidenceItem-like candidate. Not a production EvidenceItem."""

    id: str
    source_id: str
    url: str
    canonical_url: str
    domain: str
    publisher: Optional[str] = None
    published_at: Optional[datetime] = None
    retrieved_at: datetime = Field(default_factory=utc_now)
    content_hash: str
    snippet: str
    source_type: str = "aggregator"
    reliability_tier: int = 3
    provenance: str = "LIVE_OSINT"


class GeminiClaimCandidate(BaseModel):
    """ClaimItem-like candidate. Not a production ClaimItem."""

    id: str
    text: str
    evidence_ids: List[str] = Field(..., min_length=1)
    confidence: float = Field(default=0.55, ge=0.0, le=1.0)
    confidence_justification: str
    time_horizon: str = "MEDIUM_TERM"
    falsifiable: bool = True
    resolution_date: Optional[str] = None


class GeminiEvidencePack(BaseModel):
    """Normalized Phase 2 evidence pack produced from a raw Gemini result."""

    provider: str = "gemini_deep_research"
    model: str = "deep-research-preview-04-2026"
    interaction_id: Optional[str] = None
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    original_question: Optional[str] = None
    improved_research_prompt: Optional[str] = None
    research_plan: List[str] = Field(default_factory=list)
    sources: List[GeminiSourceCandidate] = Field(default_factory=list)
    evidence_items: List[GeminiEvidenceCandidate] = Field(default_factory=list)
    claim_items: List[GeminiClaimCandidate] = Field(default_factory=list)
    uncertainty_notes: List[str] = Field(default_factory=list)
    intelligence_gaps: List[GeminiIntelligenceGapCandidate] = Field(default_factory=list)
    raw_report: Optional[str] = None
    raw_interaction_metadata: Dict[str, Any] = Field(default_factory=dict)
    normalizer_warnings: List[GeminiNormalizerWarning] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class GeminiAgentOutputCandidateFailure(BaseModel):
    """Structured failure returned when AgentOutput conversion is unavailable."""

    ok: bool = False
    error_type: str
    error_message: str
    warnings: List[GeminiNormalizerWarning] = Field(default_factory=list)


RecommendationLabel = Literal[
    "Gemini not useful",
    "Gemini useful as shadow only",
    "Gemini useful as assistant",
    "Gemini ready to replace ContextInterpreter for this domain",
    "Gemini ready to replace BlackSwanGenerator for this domain",
    "Gemini requires human review",
]


class SourceComparison(BaseModel):
    """Local source overlap metrics for Phase 3A shadow comparisons."""

    gemini_source_count: int = 0
    seer_source_count: int = 0
    overlapping_sources: List[str] = Field(default_factory=list)
    unique_gemini_sources: List[str] = Field(default_factory=list)
    unique_seer_sources: List[str] = Field(default_factory=list)
    source_overlap_ratio: float = 0.0
    gemini_domains: List[str] = Field(default_factory=list)
    seer_domains: List[str] = Field(default_factory=list)
    freshness_notes: List[str] = Field(default_factory=list)
    credibility_notes: List[str] = Field(default_factory=list)


class EvidenceComparison(BaseModel):
    """Local evidence and claim comparison metrics for Phase 3A."""

    gemini_evidence_count: int = 0
    seer_evidence_count: int = 0
    gemini_claim_count: int = 0
    seer_claim_count: int = 0
    accepted_gemini_evidence_count: int = 0
    rejected_gemini_evidence_count: int = 0
    duplicate_evidence_count: int = 0
    unsupported_gemini_claims_count: int = 0
    contradictions_count: int = 0
    intelligence_gap_count: int = 0
    evidence_gap_notes: List[str] = Field(default_factory=list)


class AgentOverlapComparison(BaseModel):
    """Simple overlap scores against relevant TheSeer agent lanes."""

    context_interpreter_overlap: Optional[float] = None
    black_swan_generator_overlap: Optional[float] = None
    think_tank_analyst_overlap: Optional[float] = None
    walled_garden_analyst_overlap: Optional[float] = None
    evidence_analyst_overlap: Optional[float] = None
    useful_new_evidence_count: int = 0
    seer_unique_evidence_count: int = 0


class RiskAssessment(BaseModel):
    """Conservative local risk assessment for a Gemini shadow run."""

    hallucination_risk: str = "unknown"
    citation_risk: str = "unknown"
    source_governance_risk: str = "unknown"
    schema_compliance_risk: str = "unknown"
    latency_risk: str = "unknown"
    cost_risk: str = "unknown"
    dependency_risk: str = "medium"
    overall_risk: str = "medium"
    risk_notes: List[str] = Field(default_factory=list)


class GeminiShadowRun(BaseModel):
    """Phase 3A shadow comparison artifact. Not production workflow state."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=utc_now)
    query: Optional[str] = None
    gemini_interaction_id: Optional[str] = None
    gemini_model: Optional[str] = None
    gemini_mode: str = "shadow"
    seer_workflow_version: str = "v2"
    seer_agents_used: List[str] = Field(default_factory=list)
    evidence_pack_summary: Dict[str, Any] = Field(default_factory=dict)
    source_comparison: SourceComparison = Field(default_factory=SourceComparison)
    evidence_comparison: EvidenceComparison = Field(default_factory=EvidenceComparison)
    agent_overlap: AgentOverlapComparison = Field(default_factory=AgentOverlapComparison)
    risk_assessment: RiskAssessment = Field(default_factory=RiskAssessment)
    recommendation: RecommendationLabel = "Gemini useful as shadow only"
    next_steps: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


ShadowRunnerStatus = Literal[
    "completed",
    "failed",
    "timeout",
    "disabled",
    "mock_completed",
]


class GeminiShadowRunnerResult(BaseModel):
    """Phase 3B standalone runner summary. Not production workflow state."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    status: ShadowRunnerStatus
    query: Optional[str] = None
    mock: bool = False
    model: Optional[str] = None
    raw_result_path: Optional[str] = None
    evidence_pack_path: Optional[str] = None
    shadow_run_json_path: Optional[str] = None
    shadow_report_path: Optional[str] = None
    recommendation: Optional[str] = None
    overall_risk: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


EvaluationRecommendation = Literal[
    "Gemini not useful",
    "Gemini useful as shadow only",
    "Gemini useful as assistant",
    "Gemini ready for limited assist-mode trial",
    "Gemini candidate for future ContextInterpreter replacement",
    "Gemini candidate for future BlackSwanGenerator replacement",
    "Gemini requires human review",
]

ReadinessLevel = Literal[
    "none",
    "shadow",
    "assistant_candidate",
    "limited_assist_trial",
    "replacement_candidate",
    "human_review",
]


class EvaluationThresholds(BaseModel):
    """Conservative repeat-run thresholds for Phase 3C readiness decisions."""

    minimum_runs_for_shadow_value: int = 3
    minimum_runs_for_assist_trial: int = 5
    minimum_runs_for_replacement_candidate: int = 10
    max_high_risk_runs_ratio: float = 0.2
    max_critical_risk_runs: int = 0
    min_average_useful_new_evidence: float = 2.0
    min_average_source_overlap: float = 0.2
    max_average_unsupported_claims: float = 1.0
    max_average_contradictions: float = 2.0
    max_average_duplicate_evidence: float = 5.0
    max_average_latency_seconds: float = 900.0
    max_failure_or_timeout_ratio: float = 0.1
    require_zero_secret_leakage: bool = True
    require_zero_probability_contamination_for_assist: bool = True
    require_human_review_for_replacement: bool = True


class DomainEvaluationProfile(BaseModel):
    """Domain-specific policy profile layered over default thresholds."""

    domain: str = "general"
    thresholds: EvaluationThresholds = Field(default_factory=EvaluationThresholds)
    human_review_above_shadow: bool = False
    notes: List[str] = Field(default_factory=list)


class ShadowRunAggregate(BaseModel):
    """Aggregated metrics across one or more saved Gemini shadow runs."""

    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    timeout_runs: int = 0
    disabled_runs: int = 0
    malformed_runs: int = 0
    high_risk_runs: int = 0
    critical_risk_runs: int = 0
    unknown_risk_runs: int = 0
    average_useful_new_evidence_count: float = 0.0
    average_source_overlap_ratio: float = 0.0
    average_unsupported_claims_count: float = 0.0
    average_contradictions_count: float = 0.0
    average_duplicate_evidence_count: float = 0.0
    average_latency_seconds: Optional[float] = None
    failure_or_timeout_ratio: float = 0.0
    recommendation_distribution: Dict[str, int] = Field(default_factory=dict)
    overall_risk_distribution: Dict[str, int] = Field(default_factory=dict)
    agent_overlap_averages: Dict[str, Optional[float]] = Field(default_factory=dict)
    domains_tested: List[str] = Field(default_factory=list)
    warnings_collected: List[str] = Field(default_factory=list)
    secret_leakage_detected: bool = False
    probability_contamination_detected: bool = False
    source_governance_high_runs: int = 0
    incomplete_input_runs: int = 0


class GeminiEvaluationDecision(BaseModel):
    """Phase 3C policy decision. It does not authorize production changes."""

    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=utc_now)
    domain: str = "general"
    target_agent: Optional[str] = None
    runs_evaluated: int = 0
    minimum_runs_required: int = 3
    recommendation: EvaluationRecommendation = "Gemini useful as shadow only"
    readiness_level: ReadinessLevel = "shadow"
    blocked: bool = False
    blocking_reasons: List[str] = Field(default_factory=list)
    passed_criteria: List[str] = Field(default_factory=list)
    failed_criteria: List[str] = Field(default_factory=list)
    risk_summary: Dict[str, Any] = Field(default_factory=dict)
    metric_summary: Dict[str, Any] = Field(default_factory=dict)
    required_next_runs: int = 0
    human_review_required: bool = False
    next_steps: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
