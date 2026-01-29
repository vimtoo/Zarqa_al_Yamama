"""
The Quantifier V2
Deterministic fusion of agent signals with independence weighting and horizon stratification.

NO "LLM VIBES" - all computations are traceable and reproducible.

BOUNDARY STATEMENT:
The Quantifier is FORBIDDEN from generating original claims or narratives.
It describes the HOW (math), not the WHAT (evidence).
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np

from app.config import settings
from app.graph.state import ForecastState
from app.graph.contracts import (
    AgentOutput,
    FusionResult,
    HorizonForecast,
    TimeHorizon,
    ExplainFusion,
    ConflictResolution,
    ScenarioProbability,
    ClaimItem,
    EvidenceItem,
    ConfidenceLevel,
)
from app.retrieval.independence_analyzer import independence_analyzer

logger = logging.getLogger(__name__)


class QuantifierV2:
    """
    Deterministic fusion engine for multi-agent forecasting.
    
    Core Formula:
    forecast[h] = Σ(agent_signal[h] * weight[agent, h] * independence[agent]) / normalization
    
    Where:
    - h = time horizon (SHORT_TERM, MEDIUM_TERM, LONG_TERM)
    - weight[agent, h] = agent reliability * horizon-specific factor
    - independence[agent] = penalty for low source independence
    """
    
    # Agent reliability weights (0.0 - 1.0)
    # These should be calibrated over time based on Brier/CRPS scores
    AGENT_RELIABILITY = {
        'temporal_analyst': 0.85,
        'context_interpreter': 0.70,
        'think_tank_analyst': 0.75,
        'political_studies_analyst': 0.70,
        'election_forecaster': 0.65,
        'market_classifier': 0.80,
        'walled_garden_analyst': 0.60,
        'risk_scorer': 0.70,
        'scenario_modeler': 0.65,
        'policy_impact_analyst': 0.65,
    }
    
    # Horizon-specific agent weights
    # Which agents dominate for each time horizon
    HORIZON_WEIGHTS = {
        TimeHorizon.SHORT_TERM: {
            'temporal_analyst': 1.0,
            'market_classifier': 0.9,
            'context_interpreter': 0.6,
            'think_tank_analyst': 0.3,
            'political_studies_analyst': 0.3,
            'election_forecaster': 0.2,
            'risk_scorer': 0.5,
            'scenario_modeler': 0.4,
            'policy_impact_analyst': 0.3,
            'walled_garden_analyst': 0.4,
        },
        TimeHorizon.MEDIUM_TERM: {
            'temporal_analyst': 0.6,
            'market_classifier': 0.6,
            'context_interpreter': 0.7,
            'think_tank_analyst': 0.8,
            'political_studies_analyst': 0.8,
            'election_forecaster': 0.9,
            'risk_scorer': 0.7,
            'scenario_modeler': 0.8,
            'policy_impact_analyst': 0.8,
            'walled_garden_analyst': 0.5,
        },
        TimeHorizon.LONG_TERM: {
            'temporal_analyst': 0.3,
            'market_classifier': 0.4,
            'context_interpreter': 0.5,
            'think_tank_analyst': 1.0,
            'political_studies_analyst': 0.9,
            'election_forecaster': 0.5,
            'risk_scorer': 0.6,
            'scenario_modeler': 1.0,
            'policy_impact_analyst': 0.9,
            'walled_garden_analyst': 0.6,
        },
    }
    
    def __init__(self):
        self.enabled = settings.QUANTIFIER_ENABLED
    
    def get_agent_weight(self, agent_id: str, horizon: TimeHorizon) -> float:
        """Get combined weight for an agent at a specific horizon."""
        reliability = self.AGENT_RELIABILITY.get(agent_id, 0.5)
        horizon_factor = self.HORIZON_WEIGHTS.get(horizon, {}).get(agent_id, 0.5)
        return reliability * horizon_factor
    
    def compute_independence_penalty(self, agent_output: AgentOutput) -> Tuple[float, Dict[str, Any]]:
        """
        Compute independence penalty (0.5 - 1.0) for an agent.
        
        Low independence = high penalty = lower weight.
        """
        if not agent_output.evidence:
            return 0.7, {}  # Default penalty for no evidence
        
        stats = independence_analyzer.analyze_agent_independence(
            agent_output.claims, 
            agent_output.evidence
        )
        
        # Convert independence score to penalty multiplier
        # independence=1.0 -> penalty=1.0 (no penalty)
        # independence=0.0 -> penalty=0.5 (50% weight reduction)
        independence = stats.get('overall_independence', 0.5)
        penalty = 0.5 + (independence * 0.5)
        
        return penalty, stats
    
    def extract_signals_by_horizon(
        self, 
        agent_outputs: Dict[str, AgentOutput]
    ) -> Dict[TimeHorizon, Dict[str, List[float]]]:
        """
        Extract and group signals by time horizon.
        
        Returns:
            {horizon: {agent_id: [signal_values]}}
        """
        grouped = {h: {} for h in TimeHorizon}
        
        for agent_id, output in agent_outputs.items():
            for signal in output.signals:
                horizon = signal.time_horizon
                if agent_id not in grouped[horizon]:
                    grouped[horizon][agent_id] = []
                grouped[horizon][agent_id].append(signal.value)
        
        return grouped
    
    def detect_conflicts(
        self, 
        signals_by_horizon: Dict[TimeHorizon, Dict[str, List[float]]]
    ) -> List[str]:
        """
        Detect significant conflicts between agent signals.
        
        Returns list of conflict descriptions.
        """
        conflicts = []
        
        for horizon, agents in signals_by_horizon.items():
            if len(agents) < 2:
                continue
            
            # Get average signal per agent
            agent_means = {a: np.mean(v) for a, v in agents.items() if v}
            
            if not agent_means:
                continue
            
            # Check for large disagreements (>2 std dev from mean)
            all_means = list(agent_means.values())
            overall_mean = np.mean(all_means)
            overall_std = np.std(all_means) if len(all_means) > 1 else 0
            
            for agent, mean_val in agent_means.items():
                if overall_std > 0 and abs(mean_val - overall_mean) > 2 * overall_std:
                    conflicts.append(
                        f"{horizon.value}: {agent} signal ({mean_val:.2f}) diverges significantly "
                        f"from consensus ({overall_mean:.2f} ± {overall_std:.2f})"
                    )
        
        return conflicts
    
    def fuse_signals(
        self,
        agent_outputs: Dict[str, AgentOutput],
        horizon: TimeHorizon
    ) -> Tuple[float, float, float, Dict[str, float], Dict[str, float]]:
        """
        Fuse signals for a specific horizon.
        
        Returns:
            (p10, p50, p90, agent_contributions, agent_contributions_raw)
        """
        weighted_values = []
        weights = []
        contributions = {}
        contributions_raw = {}
        
        for agent_id, output in agent_outputs.items():
            # Get signals for this horizon
            horizon_signals = [s for s in output.signals if s.time_horizon == horizon]
            if not horizon_signals:
                continue
            
            # Average signal value for this agent
            avg_value = np.mean([s.value for s in horizon_signals])
            
            # Compute weight
            base_weight = self.get_agent_weight(agent_id, horizon)
            independence_penalty, _ = self.compute_independence_penalty(output)
            final_weight = base_weight * independence_penalty * output.confidence
            
            weighted_values.append(avg_value * final_weight)
            weights.append(final_weight)
            contributions[agent_id] = final_weight
            contributions_raw[agent_id] = base_weight * output.confidence
        
        if not weighted_values:
            # No signals for this horizon
            return 0.0, 0.0, 0.0, {}, {}
        
        # Weighted average for P50
        total_weight = sum(weights)
        p50 = sum(weighted_values) / total_weight if total_weight > 0 else 0.0
        
        # Estimate uncertainty (P10, P90) based on signal variance and confidence
        if len(weighted_values) > 1:
            values = [wv / w for wv, w in zip(weighted_values, weights) if w > 0]
            std = np.std(values) if values else abs(p50) * 0.15
        else:
            std = abs(p50) * 0.15  # Default 15% uncertainty
        
        # 80% confidence interval (P10 to P90)
        z_score = 1.28  # ~80% CI
        p10 = p50 - z_score * std
        p90 = p50 + z_score * std
        
        return p10, p50, p90, contributions, contributions_raw
        
    def normalize_scenario_probabilities(
        self, 
        scenarios: List[ScenarioProbability]
    ) -> List[ScenarioProbability]:
        """
        Ensure scenario probabilities sum to 1.0.
        """
        if not scenarios:
            return scenarios
        
        total = sum(s.probability for s in scenarios)
        if abs(total - 1.0) < 1e-6:
            return scenarios
        
        if total == 0:
            # Equal distribution
            equal_prob = 1.0 / len(scenarios)
            return [
                ScenarioProbability(
                    scenario_name=s.scenario_name,
                    probability=equal_prob,
                    narrative=s.narrative,
                    drivers=s.drivers
                )
                for s in scenarios
            ]
        
        # Normalize
        return [
            ScenarioProbability(
                scenario_name=s.scenario_name,
                probability=s.probability / total,
                narrative=s.narrative,
                drivers=s.drivers
            )
            for s in scenarios
        ]
    
    def validate_quantile_coherence(self, p10: float, p50: float, p90: float) -> Tuple[float, float, float]:
        """
        Ensure quantiles are monotonic: P10 ≤ P50 ≤ P90.
        If violated, correct by averaging.
        """
        if p10 <= p50 <= p90:
            return p10, p50, p90
        
        logger.warning(f"Quantile monotonicity violated: P10={p10}, P50={p50}, P90={p90}. Correcting...")
        
        # Sort and reassign
        sorted_vals = sorted([p10, p50, p90])
        return sorted_vals[0], sorted_vals[1], sorted_vals[2]
    
    def determine_confidence_level(
        self, 
        agent_outputs: Dict[str, AgentOutput],
        conflicts: List[str]
    ) -> ConfidenceLevel:
        """
        Determine overall confidence level.
        """
        if not agent_outputs:
            return ConfidenceLevel.LOW
        
        # Average agent confidence
        avg_confidence = np.mean([o.confidence for o in agent_outputs.values()])
        
        # Penalty for conflicts
        conflict_penalty = len(conflicts) * 0.1
        adjusted_confidence = avg_confidence - conflict_penalty
        
        if adjusted_confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif adjusted_confidence >= 0.4:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def aggregate_claims_and_evidence(
        self, 
        agent_outputs: Dict[str, AgentOutput]
    ) -> Tuple[List[ClaimItem], List[EvidenceItem]]:
        """
        Aggregate all claims and evidence from agents.
        """
        all_claims = []
        all_evidence = []
        evidence_ids_seen = set()
        
        for output in agent_outputs.values():
            all_claims.extend(output.claims)
            for e in output.evidence:
                if e.id not in evidence_ids_seen:
                    all_evidence.append(e)
                    evidence_ids_seen.add(e.id)
        
        return all_claims, all_evidence
    
    async def quantify(self, state: ForecastState) -> Dict[str, Any]:
        """
        Main quantification method.
        
        Produces horizon-stratified FusionResult with full explain_fusion.
        """
        if not self.enabled:
            return state
        
        try:
            logger.info("Quantifier V2 starting deterministic fusion...")
            
            agent_outputs: Dict[str, AgentOutput] = state.get('agent_outputs', {})
            
            if not agent_outputs:
                logger.warning("No structured agent outputs available. Using legacy path.")
                # Fallback to legacy quantifier behavior would go here
                state['warnings'].append("Quantifier: No v2 agent outputs, using legacy fusion")
                return state
            
            # 1. Extract signals by horizon
            signals_by_horizon = self.extract_signals_by_horizon(agent_outputs)
            
            # 2. Detect conflicts
            conflicts = self.detect_conflicts(signals_by_horizon)
            
            # 3. Fuse signals per horizon
            horizon_forecasts = {}
            all_contributions = {}
            all_contributions_raw = {}
            all_independence_penalties = {}
            all_independence_stats = {}
            conflict_resolutions = []
            
            for horizon in TimeHorizon:
                p10, p50, p90, contributions, contributions_raw = self.fuse_signals(agent_outputs, horizon)
                p10, p50, p90 = self.validate_quantile_coherence(p10, p50, p90)
                
                # Get scenario probabilities from state (if available)
                raw_scenarios = state.get('scenario_probabilities', [])
                scenarios = [
                    ScenarioProbability(
                        scenario_name=s.get('scenario', 'Unknown'),
                        probability=s.get('probability', 0.0),
                        narrative=s.get('rationale', ''),
                        drivers=s.get('drivers', [])
                    )
                    for s in raw_scenarios
                ]
                scenarios = self.normalize_scenario_probabilities(scenarios)
                
                # Extract key drivers
                key_drivers = []
                for output in agent_outputs.values():
                    for claim in output.claims:
                        if claim.time_horizon == horizon and claim.confidence > 0.6:
                            key_drivers.append(claim.text[:100])
                key_drivers = key_drivers[:5]  # Top 5
                
                horizon_forecasts[horizon] = HorizonForecast(
                    horizon=horizon,
                    p10=p10,
                    p50=p50,
                    p90=p90,
                    scenario_probabilities=scenarios,
                    key_drivers=key_drivers,
                    agent_weights=contributions
                )
                
                all_contributions[horizon.value] = contributions
                all_contributions_raw[horizon.value] = contributions_raw
                
                # Record independence penalties & stats
                for agent_id, output in agent_outputs.items():
                    if agent_id not in all_independence_penalties:
                        pen, st = self.compute_independence_penalty(output)
                        all_independence_penalties[agent_id] = pen
                        all_independence_stats[agent_id] = st
            
            # 4. Build explain_fusion
            # Flatten contributions: aggregate across horizons per agent
            flattened_contributions = {}
            flattened_contributions_raw = {}
            
            for horizon_name, contrib_dict in all_contributions.items():
                for agent_id, weight in contrib_dict.items():
                    if agent_id not in flattened_contributions:
                        flattened_contributions[agent_id] = 0.0
                    flattened_contributions[agent_id] += weight
            
            for horizon_name, contrib_dict in all_contributions_raw.items():
                for agent_id, weight in contrib_dict.items():
                    if agent_id not in flattened_contributions_raw:
                        flattened_contributions_raw[agent_id] = 0.0
                    flattened_contributions_raw[agent_id] += weight

            # Build rationale
            penalty_rationale = {}
            for agent_id, stats in all_independence_stats.items():
                output = agent_outputs.get(agent_id)
                evidence_count = stats.get('evidence_count') or stats.get('total_evidence') or (len(output.evidence) if output else 0)
                cluster_count_agent = stats.get('cluster_count') or stats.get('unique_clusters') or 0
                unique_clusters = stats.get('unique_clusters', [])
                
                # Causal logic
                if evidence_count <= 1:
                    penalty_rationale[agent_id] = "Low evidence count penalty floor"
                elif cluster_count_agent < evidence_count:
                    penalty_rationale[agent_id] = f"Duplicate clusters detected ({cluster_count_agent}/{evidence_count})"
                elif stats.get('overall_independence', 1.0) < 0.8:
                     penalty_rationale[agent_id] = f"Low owner diversity"
                else:
                    penalty_rationale[agent_id] = "Full weight applied (Independent source)"

            # Task A: Consistent cluster_count
            # cluster_count = sum(unique_clusters across agents)
            total_cluster_count = sum((s.get('cluster_count') or s.get('unique_clusters') or 0) for s in all_independence_stats.values())
            
            independence_trace = state.get("independence_summary", {}).copy()
            independence_trace['cluster_count'] = total_cluster_count
            
            # Task B: Horizon Semantics
            # Task B: Horizon Semantics
            active = {h for h, c in all_contributions.items() if c}
            inactive_horizons = [th.value for th in TimeHorizon if th.value not in active]
            filtered_normalization = {h: 1.0 for h in active}

            explain_fusion = ExplainFusion(
                agent_contributions=flattened_contributions,
                agent_contributions_raw=flattened_contributions_raw,
                agent_contributions_final=flattened_contributions,
                independence_trace=independence_trace,
                penalty_rationale=penalty_rationale,
                horizon_contributions=all_contributions,
                inactive_horizons=inactive_horizons,
                independence_penalties=all_independence_penalties,
                conflicts_detected=conflicts,
                conflict_resolutions=conflict_resolutions,
                normalization_factors=filtered_normalization
            )
            
            
            # 5. Aggregate claims and evidence
            all_claims, all_evidence = self.aggregate_claims_and_evidence(agent_outputs)
            
            # 6. Determine confidence level
            confidence_level = self.determine_confidence_level(agent_outputs, conflicts)
            
            # 7. Generate executive summary
            short_term = horizon_forecasts.get(TimeHorizon.SHORT_TERM)
            executive_summary = (
                f"Forecast for '{state.get('scenario', 'Unknown')}': "
                f"Short-term P50={short_term.p50:.2f} (range: {short_term.p10:.2f}-{short_term.p90:.2f}) "
                f"based on {len(agent_outputs)} agents with {confidence_level.value} confidence."
                if short_term else "Insufficient data for forecast."
            )
            
            # 8. Build FusionResult
            fusion_result = FusionResult(
                forecast_id=state.get('request_id', str(uuid.uuid4())),
                timestamp=datetime.now(),
                scenario_name=state.get('scenario', ''),
                horizon_forecasts=horizon_forecasts,
                executive_summary=executive_summary,
                explain_fusion=explain_fusion,
                confidence_level=confidence_level,
                all_claims=all_claims,
                all_evidence=all_evidence,
                sources_consulted=[e.url for e in all_evidence],
                audit_trail=[
                    f"Quantifier V2 processed {len(agent_outputs)} agents",
                    f"Detected {len(conflicts)} signal conflicts",
                    f"Overall confidence: {confidence_level.value}"
                ],
                warnings=conflicts if conflicts else [],
                assumptions=[a for o in agent_outputs.values() for a in o.assumptions],
                known_unknowns=[u for o in agent_outputs.values() for u in o.uncertainty_notes],
                invalidation_criteria=[]
            )
            
            # 9. Update state
            state['fusion_result_v2'] = fusion_result
            state['horizon_forecasts'] = horizon_forecasts
            
            # Legacy compatibility
            short_term_p50 = horizon_forecasts.get(TimeHorizon.SHORT_TERM, HorizonForecast(
                horizon=TimeHorizon.SHORT_TERM, p10=0, p50=0, p90=0
            )).p50
            state['quantified_forecast'] = {
                'final_forecast': short_term_p50,
                'final_confidence': 0.7 if confidence_level == ConfidenceLevel.HIGH else 0.5,
            }
            state['quantified_confidence'] = 0.7 if confidence_level == ConfidenceLevel.HIGH else 0.5
            state['agents_executed'].append('quantifier_v2')
            
            logger.info(f"Quantifier V2 completed. Confidence: {confidence_level.value}")
            
        except Exception as e:
            logger.error(f"Quantifier V2 error: {str(e)}")
            state['errors'].append(f"Quantifier V2: {str(e)}")
        
        return state


# Singleton instance
quantifier_v2 = QuantifierV2()
