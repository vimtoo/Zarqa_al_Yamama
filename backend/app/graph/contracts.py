"""
Zarqa al Yamama v2 - Data Contracts
Pydantic v2 models for structured agent outputs, evidence tracking, and forecast fusion.

These contracts enforce:
1. Structured claims with evidence_ids linking
2. Time-horizon stratification (SHORT_TERM, MEDIUM_TERM, LONG_TERM)
3. Independence scoring for source deduplication
4. Probability coherence validation
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from enum import Enum
import uuid


# ============================================================================
# Enums
# ============================================================================

class TimeHorizon(str, Enum):
    """Time horizon classification for claims and forecasts."""
    SHORT_TERM = "SHORT_TERM"    # 0-30 days
    MEDIUM_TERM = "MEDIUM_TERM"  # 1-12 months
    LONG_TERM = "LONG_TERM"      # 1-5 years


class SourceType(str, Enum):
    """Classification of evidence source types."""
    PRIMARY = "primary"                   # General primary source
    SYNDICATED = "syndicated"             # Syndicated content from wire services
    PRIMARY_DATA = "primary_data"         # Market data, official statistics
    PRIMARY_REPORTING = "primary_reporting"  # Original journalism
    ANALYSIS = "analysis"                 # Think tank reports, research
    AGGREGATOR = "aggregator"             # News aggregators, wire services
    SOCIAL = "social"                     # Social media, forums



class Domain(str, Enum):
    """Domain classification for routing analysis."""
    GEOPOLITICS = "geopolitics"
    MACROECONOMICS = "macroeconomics"
    FINANCE = "finance"
    TECHNOLOGY = "technology"
    SECURITY = "security"
    POLICY = "policy"


class ConfidenceLevel(str, Enum):
    """Discrete confidence levels for final output."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================================
# Evolution Plan - New Schemas
# ============================================================================

class ConflictMetrics(BaseModel):
    """Metrics for conflict dynamics (velocity, intensity, hotspots)."""
    velocity: float = Field(..., description="Rate of change in conflict events")
    intensity_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Normalized intensity 0-100")
    anchor_id: Optional[str] = Field(None, description="ID of the matching anchor event")
    band: Optional[Literal["A", "B", "C", "D", "E"]] = Field(None, description="Ordinal intensity band")
    delta_required: bool = Field(default=True, description="Warning: Score must not be interpreted as absolute")
    unknown_reason: Optional[str] = Field(None, description="Required if score is missing")
    hotspots: List[str] = Field(default_factory=list, description="Geographic conflict clusters")
    trend: Literal["accelerating", "stable", "decelerating"] = "stable"

    @model_validator(mode='after')
    def validate_anchoring(self) -> 'ConflictMetrics':
        """Enforce anchoring rules: Score requires Anchor ID and Band."""
        if self.intensity_score is not None:
            if not self.anchor_id or not self.band:
                 raise ValueError("Unanchored Metric violation: intensity_score requires anchor_id and band")
        else:
             if not self.unknown_reason:
                  raise ValueError("Missing Metric violation: Null intensity_score requires unknown_reason")
        return self


class QualitativeForecast(BaseModel):
    """
    Non-numeric forecast for event outcomes.
    Enforces Rule 2: Uncertainty Preservation & Rule 3: Human/System Balance.
    """
    outcome_label: str = Field(..., description="The predicted qualitative outcome")
    likelihood_category: Literal["Almost Certain", "Likely", "Toss-up", "Unlikely", "Remote"] = Field(..., description="Categorical likelihood")
    time_horizon_label: str = Field(..., description="e.g. '6-12 Months'")
    
    # Support
    evidence_chain: List[str] = Field(default_factory=list, description="UUIDs of EvidenceItems")
    preconditions: List[str] = Field(default_factory=list, description="Conditions required for this outcome")
    blockers: List[str] = Field(default_factory=list, description="Factors that would prevent this outcome")
    
    # Uncertainty
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Epistemic confidence in the analysis")
    unknown_factors: List[str] = Field(..., min_length=1, description="Known unknowns (Must not be empty)")

    @model_validator(mode='after')
    def validate_invariants(self) -> 'QualitativeForecast':
        if not self.unknown_factors:
             raise ValueError("Invariant Failed: unknown_factors cannot be empty (Omniscience prohibited)")
        # If evidence chain is empty, confidence must be low
        if not self.evidence_chain and self.confidence_score > 0.2:
             raise ValueError("Invariant Failed: High confidence requires evidence chain")
        return self


class DomainClassification(BaseModel):
    """Result of domain routing."""
    domains: List[Domain] = Field(..., min_length=1)
    primary_domain: Domain
    confidence: float
    reasoning: str


# ============================================================================
# Evolution Plan - Phase 3 Schemas
# ============================================================================

class EffectNode(BaseModel):
    description: str
    domain: Domain
    likelihood: str
    impact_severity: str = Field(..., pattern="^(HIGH|MEDIUM|LOW)$")

class PolicyRippleOutcome(BaseModel):
    """Schema for second-order policy effects."""
    root_event: str
    first_order_effects: List[EffectNode]
    second_order_effects: List[EffectNode]
    feedback_loops: List[str]

class SourcePosition(BaseModel):
    source_id: str
    stance: Literal["Supports", "Refutes", "Neutral"]
    bias_rating: str

class BiasTriangulation(BaseModel):
    """
    Explicitly measures and reports source disagreement.
    Enforces Rule 4: Dialectical Rigor.
    """
    topic: str
    consensus_status: Literal["Consensus", "Divided", "Polarized", "Chaos"]
    positions: List[SourcePosition]
    divergence_point: str = Field(..., description="Crux of the disagreement")
    unrepresented_perspective: List[str] = Field(..., min_length=1, description="Missing voices")

# ============================================================================
# Evidence Contracts
# ============================================================================

class EvidenceItem(BaseModel):
    """
    A single piece of evidence with full provenance tracking.
    
    Requirements:
    - Every evidence item MUST have a unique ID
    - canonical_url enables deduplication
    - content_hash enables syndication detection
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str = Field(..., description="Original URL as fetched")
    canonical_url: str = Field(..., description="Normalized URL for deduplication")
    domain: str = Field(..., description="Extracted domain (e.g., 'reuters.com')")
    publisher: Optional[str] = Field(None, description="Publisher name if known")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp if available")
    retrieved_at: datetime = Field(default_factory=datetime.now)
    content_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$", description="SHA-256 of content")
    snippet: str = Field(..., max_length=2000, description="Relevant excerpt")
    snippet_hash: Optional[str] = Field(None, pattern=r"^[a-f0-9]{64}$")
    source_type: SourceType = Field(default=SourceType.AGGREGATOR)
    independence_cluster_id: Optional[str] = Field(None, description="ID of syndication cluster")
    
    # Metadata for confidence computation
    reliability_tier: int = Field(default=3, ge=1, le=5, description="1=highest, 5=lowest")
    
    # Syndication Tracking (Syndication Loophole Fix)
    canonical_origin_id: Optional[str] = Field(None, description="ID of the original wire/source")
    origin_name: Optional[str] = Field(None, description="Name of origin (e.g. 'Associated Press')")
    is_syndicated: bool = Field(default=False)
    derivative_count: int = Field(default=0, description="Number of detected copies/derivatives")


# ============================================================================
# Claim Contracts
# ============================================================================

class ClaimItem(BaseModel):
    """
    An atomic, falsifiable claim with evidence linkage.
    
    Requirements:
    - MUST reference at least one evidence_id
    - MUST be tagged with time_horizon
    - Confidence MUST be justified
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(..., max_length=500, description="Atomic, falsifiable statement")
    evidence_ids: List[str] = Field(..., min_length=1, description="UUIDs of supporting evidence")
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_justification: str = Field(..., description="Why this confidence level?")
    time_horizon: TimeHorizon = Field(...)
    independence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="1.0 = fully independent sources")
    falsifiable: bool = Field(default=True)
    resolution_date: Optional[str] = Field(None, description="When can this claim be verified? (YYYY-MM-DD)")


# ============================================================================
# Signal Contracts
# ============================================================================

class Signal(BaseModel):
    """A numeric or categorical indicator with horizon tagging."""
    name: str = Field(..., description="Signal name (e.g., 'oil_price_30d')")
    value: float = Field(...)
    unit: Optional[str] = Field(None, description="Unit of measurement")
    time_horizon: TimeHorizon = Field(...)
    source_agent: Optional[str] = Field(None, description="Which agent produced this signal")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


# ============================================================================
# Agent Output Contract
# ============================================================================

class AgentOutput(BaseModel):
    """
    Structured output contract for ALL agents.
    
    Requirements:
    - Every claim MUST reference evidence via evidence_ids
    - Unstructured prose is forbidden beyond summaries
    - Assumptions and uncertainty_notes MUST be explicit
    """
    agent_id: str = Field(..., description="Agent identifier (e.g., 'temporal_analyst')")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Core structured outputs
    claims: List[ClaimItem] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    signals: List[Signal] = Field(default_factory=list)
    
    # Explicit assumptions and uncertainty
    assumptions: List[str] = Field(default_factory=list, description="Dependency conditions")
    uncertainty_notes: List[str] = Field(default_factory=list, description="Known blind spots")
    
    # Overall confidence
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_justification: str = Field(default="")
    
    # Optional summary (the ONLY place for prose)
    summary: Optional[str] = Field(None, max_length=1000)
    
    @field_validator('claims')
    @classmethod
    def validate_claims_have_evidence(cls, claims: List[ClaimItem], info) -> List[ClaimItem]:
        """Ensure all claims reference valid evidence IDs."""
        # Note: Full validation against evidence list happens at model level
        return claims
    
    @model_validator(mode='after')
    def validate_evidence_linkage(self) -> 'AgentOutput':
        """Ensure all claim evidence_ids exist in evidence list."""
        evidence_ids = {e.id for e in self.evidence}
        for claim in self.claims:
            for eid in claim.evidence_ids:
                if eid not in evidence_ids:
                    raise ValueError(f"Claim '{claim.id}' references non-existent evidence '{eid}'")
        return self


# ============================================================================
# Horizon Forecast Contracts
# ============================================================================

class ScenarioProbability(BaseModel):
    """A scenario with its probability."""
    scenario_name: str
    probability: float = Field(..., ge=0.0, le=1.0)
    likelihood_band: Literal["Low", "Medium", "High", "Critical"] = Field(..., description="Categorical likelihood to prevent false precision")
    narrative: Optional[str] = None
    drivers: List[str] = Field(default_factory=list)
    triggers: List[str] = Field(default_factory=list, description="Preconditions/Events that trigger this scenario")
    indicators: List[str] = Field(default_factory=list, description="Observable signals to watch")
    first_order_effects: List[str] = Field(default_factory=list)
    second_order_effects: List[str] = Field(default_factory=list)
    confidence_check: str = Field(default="", description="Why this probability band?")


class HorizonForecast(BaseModel):
    """
    Forecast for a specific time horizon.
    
    Requirements:
    - Quantiles MUST be monotonic: P10 ≤ P50 ≤ P90
    - Scenario probabilities MUST sum to 1.0
    """
    horizon: TimeHorizon
    p10: float = Field(..., description="10th percentile")
    p50: float = Field(..., description="50th percentile (median)")
    p90: float = Field(..., description="90th percentile")
    scenario_probabilities: List[ScenarioProbability] = Field(default_factory=list)
    key_drivers: List[str] = Field(default_factory=list)
    agent_weights: Dict[str, float] = Field(default_factory=dict, description="Agent contribution weights")
    
    @model_validator(mode='after')
    def validate_quantile_monotonicity(self) -> 'HorizonForecast':
        """Ensure P10 ≤ P50 ≤ P90."""
        if not (self.p10 <= self.p50 <= self.p90):
            raise ValueError(f"Quantile monotonicity violated: P10={self.p10}, P50={self.p50}, P90={self.p90}")
        return self
    
    @model_validator(mode='after')
    def validate_probability_sum(self) -> 'HorizonForecast':
        """Ensure scenario probabilities sum to 1.0."""
        if self.scenario_probabilities:
            total = sum(sp.probability for sp in self.scenario_probabilities)
            if abs(total - 1.0) > 1e-6:
                raise ValueError(f"Scenario probabilities sum to {total}, expected 1.0")
        return self


# ============================================================================
# Fusion Result Contracts
# ============================================================================

class ConflictResolution(BaseModel):
    """Record of how a signal conflict was resolved."""
    conflict_description: str
    agents_involved: List[str]
    resolution_method: str
    final_value: float
    horizon: TimeHorizon


class ExplainFusion(BaseModel):
    """
    Full breakdown of fusion weights, conflicts, and resolutions.
    
    BOUNDARY: This schema MUST NOT contain content claims or new evidence.
    It is strictly for explaining the mathematical derivation of the forecast.
    """
    agent_contributions: Dict[str, float] = Field(default_factory=dict)
    
    # Truth Window Fields
    agent_contributions_raw: Dict[str, float] = Field(default_factory=dict, description="Pre-penalty raw weights")
    agent_contributions_final: Dict[str, float] = Field(default_factory=dict, description="Post-penalty final weights")
    independence_trace: Dict[str, Any] = Field(default_factory=dict, description="Cluster count and duplicate groups")
    penalty_rationale: Dict[str, str] = Field(default_factory=dict, description="Reason for applied penalty")
    horizon_contributions: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Final weights per horizon")
    inactive_horizons: List[str] = Field(default_factory=list, description="Horizons with no signal contributions")
    
    independence_penalties: Dict[str, float] = Field(default_factory=dict)
    conflicts_detected: List[str] = Field(default_factory=list)
    conflict_resolutions: List[ConflictResolution] = Field(default_factory=list)
    normalization_factors: Dict[str, float] = Field(default_factory=dict)


class FusionResult(BaseModel):
    """
    The final structured output of the forecasting engine.
    
    Requirements:
    - Separate forecasts per horizon
    - Full explain_fusion breakdown
    - Audit trail for compliance
    """
    forecast_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    scenario_name: str
    
    # Horizon-stratified forecasts
    horizon_forecasts: Dict[TimeHorizon, HorizonForecast] = Field(default_factory=dict)
    
    # Narrative outputs
    executive_summary: str = Field(default="")
    strategic_recommendation: Optional[str] = None
    
    # Transparency
    explain_fusion: ExplainFusion = Field(default_factory=ExplainFusion)
    
    # Confidence
    confidence_level: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    
    # Evidence linkage
    all_claims: List[ClaimItem] = Field(default_factory=list)
    all_evidence: List[EvidenceItem] = Field(default_factory=list)
    sources_consulted: List[str] = Field(default_factory=list)
    
    # Audit
    audit_trail: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Invalidation criteria
    assumptions: List[str] = Field(default_factory=list)
    known_unknowns: List[str] = Field(default_factory=list)
    invalidation_criteria: List[str] = Field(default_factory=list)


# ============================================================================
# Forecast Registry Contracts (for Calibration)
# ============================================================================

class EvaluationMetrics(BaseModel):
    """Calibration metrics for resolved forecasts."""
    resolved: bool = False
    resolution_date: Optional[datetime] = None
    actual_outcome: Optional[str] = None
    brier_score: Optional[float] = None
    pinball_loss: Optional[float] = None
    crps: Optional[float] = None  # Continuous Ranked Probability Score


class ModelVersions(BaseModel):
    """Version tracking for reproducibility."""
    quantifier: str = "1.0.0"
    agents: Dict[str, str] = Field(default_factory=dict)
    contracts: str = "2.0.0"


class ForecastRecord(BaseModel):
    """
    Complete forecast record for calibration registry.
    
    Stores predictions with full context for Brier/CRPS scoring.
    """
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    forecast_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    scenario: str
    horizons: List[TimeHorizon] = Field(default_factory=list)
    
    # Complete output snapshot
    outputs: Optional[FusionResult] = None
    
    # Evidence snapshot for audit
    evidence_graph_snapshot: Dict[str, Any] = Field(default_factory=dict)
    
    # Versioning
    model_versions: ModelVersions = Field(default_factory=ModelVersions)
    
    # Evaluation (populated when forecast resolves)
    evaluation: EvaluationMetrics = Field(default_factory=EvaluationMetrics)


# ============================================================================
# Validation Response Contract
# ============================================================================

class ValidationIssue(BaseModel):
    """A specific validation issue found by the Critic."""
    issue_type: Literal["schema_violation", "missing_evidence", "allowlist_violation", 
                        "probability_incoherence", "claim_evidence_mismatch", "hallucinated_source"]
    severity: Literal["error", "warning"]
    description: str
    affected_ids: List[str] = Field(default_factory=list)


class CriticResult(BaseModel):
    """Structured output from The Critic."""
    approved: bool
    round_number: int = Field(ge=0, le=2)
    issues: List[ValidationIssue] = Field(default_factory=list)
    requires_reanalysis: bool = False
    confidence_penalty: float = Field(default=0.0, ge=0.0, le=1.0)
    audit_notes: List[str] = Field(default_factory=list)
