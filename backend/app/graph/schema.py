"""
Zarqa al Yamama - Graph Schema
Legacy schemas with backward compatibility for v2 contracts.

NOTE: For new code, prefer importing directly from app.graph.contracts
"""

from typing import List, Optional, Dict, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Import v2 contracts for forward compatibility
from app.graph.contracts import (
    TimeHorizon,
    SourceType,
    ConfidenceLevel,
    EvidenceItem as EvidenceItemV2,
    ClaimItem as ClaimItemV2,
    Signal,
    AgentOutput,
    HorizonForecast,
    FusionResult,
    ForecastRecord,
    CriticResult,
    ExplainFusion,
    ScenarioProbability,
)

# Re-export v2 contracts for convenience
__all__ = [
    # V2 Contracts
    "TimeHorizon", "SourceType", "ConfidenceLevel",
    "EvidenceItemV2", "ClaimItemV2", "Signal", "AgentOutput",
    "HorizonForecast", "FusionResult", "ForecastRecord", "CriticResult",
    "ExplainFusion", "ScenarioProbability",
    # Legacy (Backward Compatible)
    "EvidenceItem", "Claim", "EvidenceGraph", "Scenario", "ForecastResult",
    "EvidencePack", "GovernanceHaltReport",
]


# ============================================================================
# Legacy Schemas (Backward Compatible)
# ============================================================================

class EvidenceItem(BaseModel):
    """
    A single piece of evidence supporting or refuting a claim.
    
    DEPRECATED: Use EvidenceItemV2 from app.graph.contracts for new code.
    """
    source_url: str
    content_snippet: str
    published_date: Optional[str] = None
    confidence_score: float = Field(default=0.0, description="Reliability of source")
    
    # Recursion Upgrade Fields (Optional for backward compatibility)
    id: Optional[str] = None
    analyst_id: Optional[str] = None
    recursion_depth: int = 0
    context_tags: List[str] = []
    source_domain: Optional[str] = None


class GovernanceHaltReport(BaseModel):
    """Observable record of a governance intervention."""
    type: Literal["GOVERNANCE_HALT"] = "GOVERNANCE_HALT"
    analyst_id: str
    depth: int
    timestamp: datetime
    trigger: Dict[str, Any]  # policy_id, detected_terms
    outcome: str = "ABORT_RECURSION"
    downstream_action: str = "CONFIDENCE_ZERO"


class EvidencePack(BaseModel):
    """The output of a Recursive Analyst - The Currency of Truth."""
    scenario: str
    items: List[EvidenceItem]
    missing_information: List[str] = []
    contradictions: List[str] = []
    recursion_stats: Dict[str, Any] = Field(default_factory=dict, description="Stats like depth, queries run")
    governor_halt_report: Optional[GovernanceHaltReport] = None


class Claim(BaseModel):
    """
    A specific factual claim or sub-conclusion.
    
    DEPRECATED: Use ClaimItemV2 from app.graph.contracts for new code.
    """
    text: str
    supports: List[EvidenceItem] = []
    refutes: List[EvidenceItem] = []
    veracity_score: float = Field(default=0.0, description="0.0 to 1.0 likelihood of truth")
    status: Literal["verified", "disputed", "unknown"] = "unknown"


class EvidenceGraph(BaseModel):
    """Graph of all evidence collected for a forecast."""
    claims: List[Claim] = []
    sources_consulted: List[str] = []
    evidence_packs: List[EvidencePack] = []  # Store full packs
    
    # V2 fields (optional for backward compatibility)
    v2_claims: List[ClaimItemV2] = Field(default_factory=list)
    v2_evidence: List[EvidenceItemV2] = Field(default_factory=list)


class Scenario(BaseModel):
    """A plausible future scenario."""
    name: str
    probability: float
    narrative: str
    drivers: List[str] = []


class ForecastResult(BaseModel):
    """
    The final structured output of the forecasting engine.
    
    DEPRECATED: Use FusionResult from app.graph.contracts for new code.
    """
    forecast_id: str
    timestamp: datetime
    scenario_name: str
    
    # Probabilistic Forecast
    probability: float = Field(description="P50 Probability of baseline outcome")
    confidence_interval: List[float] = Field(description="[P10, P90] range")
    horizon: str = "30d"
    
    # Rationale & Logic
    summary: str
    key_drivers: List[str]
    assumptions: List[str]
    invalidation_criteria: List[str] = Field(description="What would change my mind")
    base_rates: Optional[str] = Field(description="Historical frequency of similar events")
    known_unknowns: List[str] = Field(description="Critical missing information")
    
    # Alternative Scenarios
    scenarios: List[Scenario]
    
    # Evidence Graph
    evidence_graph: EvidenceGraph
    
    # Risks
    risks: List[Dict[str, str]] = []
    
    # V2 field (optional for backward compatibility)
    fusion_result: Optional[FusionResult] = None

