"""
LangGraph State Schema for Zarqa al Yamama
Defines the central state object for multi-agent workflow
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
from enum import Enum
import operator

from app.graph.schema import EvidenceGraph, ForecastResult

# V2 Contract Imports
from app.graph.contracts import (
    AgentOutput,
    FusionResult,
    HorizonForecast,
    CriticResult,
    CriticResult,
    TimeHorizon,
    EvidenceItem,
    Domain,
    QualitativeForecast,
    ConflictMetrics,
    BiasTriangulation,
    PolicyRippleOutcome,
)


def last_value(a, b):
    """Reducer that returns the last non-empty value"""
    return b if b else a

def last_value_non_null(a, b):
    """Reducer that returns the last value, allowing False/0 as valid"""
    return b if b is not None else a


def merge_dicts(a: Dict, b: Dict) -> Dict:
    """Reducer that merges dictionaries"""
    result = a.copy() if a else {}
    if b:
        result.update(b)
    return result


def merge_lists(a: List, b: List) -> List:
    """Reducer that merges lists without duplicates"""
    result = list(a) if a else []
    if b:
        for item in b:
            if item not in result:
                result.append(item)
    return result


def merge_agent_outputs(a: Dict[str, AgentOutput], b: Dict[str, AgentOutput]) -> Dict[str, AgentOutput]:
    """Reducer that merges agent outputs by agent_id"""
    result = dict(a) if a else {}
    if b:
        result.update(b)
    return result


def merge_horizon_forecasts(a: Dict[TimeHorizon, HorizonForecast], b: Dict[TimeHorizon, HorizonForecast]) -> Dict[TimeHorizon, HorizonForecast]:
    """Reducer that merges horizon forecasts with latest values"""
    result = dict(a) if a else {}
    if b:
        result.update(b)
    return result


class ValidationStatus(str, Enum):
    """Validation status enumeration"""
    APPROVED = "APPROVED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class EthicalStatus(str, Enum):
    """Ethical status enumeration"""
    APPROVED = "APPROVED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class ForecastState(TypedDict, total=False):
    """
    Central state object for Zarqa al Yamama multi-agent workflow.
    This state is passed through all agents in the LangGraph.
    Uses Annotated types with reducers for parallel execution support.
    """

    # ========================================================================
    # REQUEST METADATA (Set once, never changes)
    # ========================================================================
    request_id: Annotated[str, last_value]
    timestamp: Annotated[datetime, last_value]
    user_id: Annotated[Optional[str], last_value]
    scenario: Annotated[str, last_value]
    forecast_horizon_days: Annotated[int, last_value]
    scenario_classification: Annotated[Optional[str], last_value]
    scenario_is_market: Annotated[Optional[bool], last_value_non_null]  # DEPRECATED
    scenario_classification_confidence: Annotated[Optional[float], last_value_non_null]  # DEPRECATED
    
    # Domain Routing (New in v2.1)
    active_domains: Annotated[List["Domain"], last_value]
    primary_domain: Annotated["Domain", last_value]
    domain_confidence: Annotated[float, last_value]

    # Qualitative Forecast (New in v2.1)
    qualitative_forecast: Annotated[Optional["QualitativeForecast"], last_value]

    # Dynamic Analysis (New in v2.1)
    conflict_metrics: Annotated[Optional["ConflictMetrics"], last_value]
    bias_triangulation: Annotated[Optional["BiasTriangulation"], last_value]
    policy_ripples: Annotated[Optional["PolicyRippleOutcome"], last_value]

    # ========================================================================
    # V2 STRUCTURED AGENT OUTPUTS (New in v2)
    # ========================================================================
    agent_outputs: Annotated[Dict[str, AgentOutput], merge_agent_outputs]
    horizon_forecasts: Annotated[Dict[TimeHorizon, HorizonForecast], merge_horizon_forecasts]
    fusion_result_v2: Annotated[Optional[FusionResult], last_value]
    critic_result_v2: Annotated[Optional[CriticResult], last_value]
    critic_round: Annotated[int, last_value]  # Track re-analysis rounds (max 2)
    v2_join_ready: Annotated[bool, last_value_non_null]
    v2_join_complete: Annotated[bool, last_value_non_null]
    deduped_evidence: Annotated[List[EvidenceItem], last_value]
    evidence_clusters: Annotated[Dict[str, Any], last_value]
    independence_summary: Annotated[Dict[str, Any], last_value]

    # ========================================================================
    # EVIDENCE ANALYST OUTPUTS
    # ========================================================================
    evidence_summary: Annotated[Optional[str], last_value]
    evidence_summary_ar: Annotated[Optional[str], last_value]
    evidence_claims: Annotated[List[Dict[str, Any]], last_value]
    evidence_confidence: Annotated[Optional[float], last_value_non_null]
    evidence_contradictions: Annotated[List[str], merge_lists]
    evidence_contradictions_ar: Annotated[List[str], merge_lists]
    evidence_unknowns: Annotated[List[str], merge_lists]
    evidence_unknowns_ar: Annotated[List[str], merge_lists]
    evidence_error: Annotated[Optional[str], last_value]

    # ========================================================================
    # TEMPORAL ANALYST OUTPUTS
    # ========================================================================
    temporal_forecast: Annotated[Dict[str, Any], merge_dicts]
    temporal_confidence: Annotated[float, last_value]
    temporal_model: Annotated[str, last_value]
    temporal_drivers: Annotated[List[str], merge_lists]
    temporal_data_sources: Annotated[List[str], merge_lists]
    temporal_error: Annotated[Optional[str], last_value]

    # ========================================================================
    # CONTEXT INTERPRETER OUTPUTS
    # ========================================================================
    context_sentiment: Annotated[Dict[str, Any], merge_dicts]
    context_themes: Annotated[List[str], merge_lists]
    context_confidence: Annotated[float, last_value]
    context_key_actors: Annotated[List[str], merge_lists]
    context_related_themes: Annotated[List[str], merge_lists]
    context_mentions_24h: Annotated[int, last_value]
    context_data_sources: Annotated[List[str], merge_lists]
    context_error: Annotated[Optional[str], last_value]

    # ========================================================================
    # WALLED GARDEN SEARCH OUTPUTS
    # ========================================================================
    walled_garden_query: Annotated[str, last_value]
    walled_garden_results: Annotated[List[Dict[str, Any]], last_value]
    walled_garden_answer: Annotated[str, last_value]
    walled_garden_sources: Annotated[List[str], merge_lists]
    walled_garden_error: Annotated[Optional[str], last_value]

    # ========================================================================
    # REPORT WRITER OUTPUTS
    # ========================================================================
    report_path: Annotated[Optional[str], last_value]
    report_filename: Annotated[Optional[str], last_value]
    report_format: Annotated[str, last_value]
    report_error: Annotated[Optional[str], last_value]
    report_pdf_filename: Annotated[Optional[str], last_value]

    # ========================================================================
    # THINK TANK ANALYST OUTPUTS
    # ========================================================================
    think_tank_insights: Annotated[Dict[str, Any], merge_dicts]
    think_tank_sources: Annotated[List[str], merge_lists]
    think_tank_topics: Annotated[List[str], merge_lists]
    think_tank_regions: Annotated[List[str], merge_lists]
    think_tank_confidence: Annotated[float, last_value]
    think_tank_error: Annotated[Optional[str], last_value]

    # ========================================================================
    # POLITICAL STUDIES OUTPUTS
    # ========================================================================
    political_insights: Annotated[Dict[str, Any], merge_dicts]
    political_key_actors: Annotated[List[str], merge_lists]
    political_themes: Annotated[List[str], merge_lists]
    political_regions: Annotated[List[str], merge_lists]
    narrative_brief: Annotated[str, last_value]
    political_data_sources: Annotated[List[str], merge_lists]
    political_error: Annotated[Optional[str], last_value]

    # ========================================================================
    # POLITICAL RISK + SCENARIOS + POLICY + ELECTIONS
    # ========================================================================
    political_risk_score: Annotated[float, last_value]
    political_risk_drivers: Annotated[List[str], merge_lists]
    political_risk_confidence: Annotated[float, last_value]
    scenario_probabilities: Annotated[List[Dict[str, Any]], last_value]
    policy_impact_forecast: Annotated[Dict[str, Any], merge_dicts]
    election_outlook: Annotated[Dict[str, Any], merge_dicts]

    # ========================================================================
    # QUANTIFIER OUTPUTS (MIDDLEWARE)
    # ========================================================================
    quantified_forecast: Annotated[Dict[str, Any], merge_dicts]
    quantified_confidence: Annotated[float, last_value]
    adjustment_rationale: Annotated[str, last_value]
    sentiment_adjustment: Annotated[float, last_value]
    risk_weight: Annotated[float, last_value]
    volatility_factor: Annotated[float, last_value]
    
    # Qualitative Forecast (New in v2.1)
    qualitative_forecast: Annotated[Optional["QualitativeForecast"], last_value]

    # ========================================================================
    # CRITIC VALIDATION
    # ========================================================================
    validation_status: Annotated[str, last_value]
    bias_flags: Annotated[List[str], merge_lists]
    data_quality_score: Annotated[float, last_value]
    source_validation_results: Annotated[Dict[str, Any], merge_dicts]
    critic_error: Annotated[Optional[str], last_value]
    critic_audit: Annotated[Dict[str, Any], merge_dicts]  # Full LLM audit result

    # ========================================================================
    # GOVERNOR OVERSIGHT
    # ========================================================================
    ethical_status: Annotated[str, last_value]
    citation_chain: Annotated[List[str], merge_lists]
    audit_log: Annotated[List[str], merge_lists]
    data_protection_status: Annotated[str, last_value]
    governor_error: Annotated[Optional[str], last_value]

    # ========================================================================
    # FINAL OUTPUT
    # ========================================================================
    executive_summary: Annotated[str, last_value]
    strategic_recommendation: Annotated[str, last_value]
    confidence_intervals: Annotated[Dict[str, float], merge_dicts]
    weak_signals: Annotated[List[Dict[str, Any]], merge_lists]

    # ========================================================================
    # ERROR HANDLING & METADATA
    # ========================================================================
    errors: Annotated[List[str], merge_lists]
    warnings: Annotated[List[str], merge_lists]
    processing_time_ms: Annotated[float, last_value]
    agents_executed: Annotated[List[str], merge_lists]
    data_freshness: Annotated[str, last_value]

    # ========================================================================
    # ANTIGRAVITY UPGRADE (Legacy)
    # ========================================================================
    evidence_graph: Annotated[Optional["EvidenceGraph"], last_value]
    final_forecast: Annotated[Optional["ForecastResult"], last_value]

    # ========================================================================
    # DELPHI CONSENSUS PROTOCOL
    # ========================================================================
    delphi_round: Annotated[int, last_value]
    expert_divergence: Annotated[List[str], merge_lists]
    delphi_convergence_score: Annotated[float, last_value]


class TemporalForecastOutput(TypedDict, total=False):
    """Output schema for Temporal Analyst agent"""
    metric: str
    current_value: float
    forecast_30d: float
    forecast_90d: float
    confidence_30d: float
    confidence_90d: float
    drivers: List[str]
    model_type: str
    data_sources: List[str]
    timestamp: datetime


class ContextSentimentOutput(TypedDict, total=False):
    """Output schema for Context Interpreter agent"""
    theme: str
    sentiment_score: float
    narrative_momentum: str
    mentions_24h: int
    key_actors: List[str]
    related_themes: List[str]
    confidence: float
    data_sources: List[str]
    timestamp: datetime


class PoliticalStudiesOutput(TypedDict, total=False):
    """Output schema for Political Studies Analyst"""
    narrative_brief: str
    key_actors: List[str]
    topics: List[str]
    regions: List[str]
    event_counts: Dict[str, int]
    sample_headlines: List[str]
    timestamp: datetime


class RiskScoreOutput(TypedDict, total=False):
    """Output schema for Political Risk Scorer"""
    risk_score: float
    risk_drivers: List[str]
    confidence: float


class ScenarioModelOutput(TypedDict, total=False):
    """Output schema for Scenario Modeler"""
    scenario: str
    probability: float
    drivers: List[str]
    rationale: str


class PolicyImpactOutput(TypedDict, total=False):
    """Output schema for Policy Impact Analyst"""
    summary: str
    impacts: List[Dict[str, Any]]
    confidence: float


class ElectionForecastOutput(TypedDict, total=False):
    """Output schema for Election Forecaster"""
    status: str
    summary: str
    confidence: float
    races: List[Dict[str, Any]]


class QuantifierOutput(TypedDict, total=False):
    """Output schema for The Quantifier middleware"""
    metric: str
    base_forecast: float
    base_confidence: float
    sentiment_adjustment: float
    final_forecast: float
    final_confidence: float
    adjustment_rationale: str
    risk_weight: float
    volatility_factor: float


class CriticValidationOutput(TypedDict, total=False):
    """Output schema for The Critic agent"""
    validation_status: ValidationStatus
    bias_score: float
    issues: List[str]
    recommendation: str
    data_quality_score: float
    source_validation: Dict[str, Any]


class GovernorOutput(TypedDict, total=False):
    """Output schema for The Governor agent"""
    ethical_status: EthicalStatus
    citation_chain: List[str]
    audit_log: List[str]
    data_protection_status: str
    compliance_notes: List[str]


class ForecastResponse(TypedDict, total=False):
    """Final API response schema"""
    request_id: str
    timestamp: datetime
    scenario: str
    status: str
    headers: Dict[str, str]
    data: Dict[str, Any]
    metadata: Dict[str, Any]
