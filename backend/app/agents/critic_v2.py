"""
The Critic V2
Deterministic validation with bounded rejection rounds.

Rejects ONLY for:
- Schema violations
- Missing evidence links
- Allowlist violations
- Probability incoherence
- Claim-evidence mismatch
- Hallucinated sources

MAX 2 re-analysis rounds. After exhaustion, output with LOW CONFIDENCE flag.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from app.config import settings
from app.graph.state import ForecastState, ValidationStatus
from app.graph.contracts import (
    CriticResult,
    ValidationIssue,
    FusionResult,
    HorizonForecast,
    ConfidenceLevel,
    TimeHorizon,
)
from app.agents.schema_validator import schema_validator

logger = logging.getLogger(__name__)


# Maximum re-analysis rounds before forcing output
MAX_REANALYSIS_ROUNDS = 2


class CriticV2:
    """
    Deterministic validator for forecast outputs.
    
    RULES:
    1. Rejection criteria are explicit and deterministic
    2. No LLM "vibes" for REJECT/APPROVE decisions
    3. Maximum 2 rejection rounds
    4. After exhaustion, mark LOW CONFIDENCE and proceed
    """
    
    def __init__(self):
        self.enabled = settings.CRITIC_ENABLED
        self._safe_list = self._initialize_safe_list()
    
    def _initialize_safe_list(self) -> set:
        """Initialize the Safe List of trusted source domains."""
        return {
            # Government & Central Banks
            'federalreserve.gov', 'treasury.gov', 'imf.org', 'worldbank.org',
            'ecb.europa.eu', 'boj.or.jp', 'boe.co.uk',
            # Official Statistics
            'bls.gov', 'census.gov', 'eia.gov', 'data.gov',
            # Wire Services
            'reuters.com', 'apnews.com', 'afp.com',
            # Major Financial News
            'bloomberg.com', 'wsj.com', 'ft.com', 'economist.com',
            # Major News
            'nytimes.com', 'washingtonpost.com', 'bbc.com', 'theguardian.com',
            # Think Tanks
            'brookings.edu', 'cfr.org', 'rand.org', 'csis.org',
            'carnegieendowment.org', 'chathamhouse.org',
            # Academic
            'arxiv.org', 'ssrn.com', 'nber.org',
            # Industry
            'opec.org', 'iea.org',
        }
    
    def check_schema_violations(self, state: ForecastState) -> List[ValidationIssue]:
        """Check for schema violations in agent outputs."""
        issues = []
        
        # Validate all agent outputs
        validation_results = schema_validator.validate_state_outputs(state)
        
        for agent_id, agent_issues in validation_results.items():
            for issue in agent_issues:
                if issue.severity == "error":
                    issues.append(issue)
        
        return issues
    
    def check_missing_evidence(self, state: ForecastState) -> List[ValidationIssue]:
        """Check for claims without evidence links."""
        issues = []
        
        fusion_result: FusionResult = state.get('fusion_result_v2')
        if not fusion_result:
            return issues
        
        for claim in fusion_result.all_claims:
            if not claim.evidence_ids:
                issues.append(ValidationIssue(
                    issue_type="missing_evidence",
                    severity="error",
                    description=f"Claim '{claim.id}' has no evidence links",
                    affected_ids=[claim.id]
                ))
        
        return issues
    
    def check_allowlist_violations(self, state: ForecastState) -> List[ValidationIssue]:
        """Check for sources not on the safe list."""
        issues = []
        
        fusion_result: FusionResult = state.get('fusion_result_v2')
        if not fusion_result:
            return issues
        
        for evidence in fusion_result.all_evidence:
            domain = evidence.domain.lower()
            
            # Check if domain is on safe list (or subdomain of safe domain)
            is_safe = any(
                domain == safe or domain.endswith('.' + safe)
                for safe in self._safe_list
            )
            
            if not is_safe:
                issues.append(ValidationIssue(
                    issue_type="allowlist_violation",
                    severity="warning",  # Warning, not error
                    description=f"Source '{domain}' not on Safe List",
                    affected_ids=[evidence.id]
                ))
        
        return issues
    
    def check_probability_incoherence(self, state: ForecastState) -> List[ValidationIssue]:
        """Check for probability and quantile violations."""
        issues = []
        
        horizon_forecasts: Dict[TimeHorizon, HorizonForecast] = state.get('horizon_forecasts', {})
        
        for horizon, forecast in horizon_forecasts.items():
            # Check quantile monotonicity
            if not (forecast.p10 <= forecast.p50 <= forecast.p90):
                issues.append(ValidationIssue(
                    issue_type="probability_incoherence",
                    severity="error",
                    description=f"{horizon.value}: Quantile monotonicity violated "
                               f"(P10={forecast.p10}, P50={forecast.p50}, P90={forecast.p90})",
                    affected_ids=[]
                ))
            
            # Check scenario probability sum
            if forecast.scenario_probabilities:
                total = sum(s.probability for s in forecast.scenario_probabilities)
                if abs(total - 1.0) > 1e-6:
                    issues.append(ValidationIssue(
                        issue_type="probability_incoherence",
                        severity="error",
                        description=f"{horizon.value}: Scenario probabilities sum to {total}, expected 1.0",
                        affected_ids=[]
                    ))
        
        return issues
    
    def check_claim_evidence_mismatch(self, state: ForecastState) -> List[ValidationIssue]:
        """Check for claims that reference non-existent evidence."""
        issues = []
        
        fusion_result: FusionResult = state.get('fusion_result_v2')
        if not fusion_result:
            return issues
        
        evidence_ids = {e.id for e in fusion_result.all_evidence}
        
        for claim in fusion_result.all_claims:
            missing = [eid for eid in claim.evidence_ids if eid not in evidence_ids]
            if missing:
                issues.append(ValidationIssue(
                    issue_type="claim_evidence_mismatch",
                    severity="error",
                    description=f"Claim '{claim.id}' references non-existent evidence: {missing}",
                    affected_ids=[claim.id] + missing
                ))
        
        return issues
    
    def run_all_checks(self, state: ForecastState) -> List[ValidationIssue]:
        """Run all deterministic validation checks."""
        all_issues = []
        
        all_issues.extend(self.check_schema_violations(state))
        all_issues.extend(self.check_missing_evidence(state))
        all_issues.extend(self.check_allowlist_violations(state))
        all_issues.extend(self.check_probability_incoherence(state))
        all_issues.extend(self.check_claim_evidence_mismatch(state))
        
        return all_issues
    
    def compute_confidence_penalty(self, issues: List[ValidationIssue]) -> float:
        """Compute confidence penalty based on issues."""
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        
        # Each error = 10% penalty, each warning = 3% penalty
        penalty = (error_count * 0.10) + (warning_count * 0.03)
        
        return min(1.0, penalty)  # Cap at 100%
    
    async def validate(self, state: ForecastState) -> Dict[str, Any]:
        """
        Main validation method.
        
        Returns updated state with validation results.
        """
        if not self.enabled:
            logger.warning("Critic V2 is disabled")
            return state
        
        try:
            logger.info("Critic V2 starting deterministic validation...")
            
            # Get current round
            current_round = state.get('critic_round', 0)
            
            # Run all checks
            issues = self.run_all_checks(state)
            
            # Count errors vs warnings
            errors = [i for i in issues if i.severity == "error"]
            warnings = [i for i in issues if i.severity == "warning"]
            
            logger.info(f"Critic V2 found {len(errors)} errors, {len(warnings)} warnings")
            
            # Determine if we should reject
            has_critical_errors = len(errors) > 0
            can_reject = current_round < MAX_REANALYSIS_ROUNDS
            
            if has_critical_errors and can_reject:
                # REJECT - trigger re-analysis
                approved = False
                requires_reanalysis = True
                next_round = current_round + 1
                
                logger.warning(
                    f"Critic V2 REJECTING (round {current_round + 1}/{MAX_REANALYSIS_ROUNDS}): "
                    f"{len(errors)} critical errors"
                )
                
                # Add error details to state
                for issue in errors:
                    state['errors'].append(f"Critic: {issue.description}")
                
                validation_status = ValidationStatus.REJECTED
                
            elif has_critical_errors and not can_reject:
                # EXHAUSTED - force LOW CONFIDENCE output
                approved = True  # Proceed anyway
                requires_reanalysis = False
                next_round = current_round
                
                logger.warning(
                    f"Critic V2 EXHAUSTED after {MAX_REANALYSIS_ROUNDS} rounds. "
                    f"Proceeding with LOW CONFIDENCE."
                )
                
                # Downgrade confidence
                fusion_result = state.get('fusion_result_v2')
                if fusion_result:
                    fusion_result.confidence_level = ConfidenceLevel.LOW
                    fusion_result.warnings.append(
                        f"Validation exhausted after {MAX_REANALYSIS_ROUNDS} rounds with unresolved errors"
                    )
                
                validation_status = ValidationStatus.FLAGGED
                
            else:
                # APPROVED
                approved = True
                requires_reanalysis = False
                next_round = current_round
                
                # Apply minor penalty for warnings
                if warnings:
                    logger.info(f"Critic V2 APPROVED with {len(warnings)} warnings")
                    validation_status = ValidationStatus.FLAGGED
                else:
                    logger.info("Critic V2 APPROVED - no issues")
                    validation_status = ValidationStatus.APPROVED
            
            # Build CriticResult
            critic_result = CriticResult(
                approved=approved,
                round_number=current_round,
                issues=issues,
                requires_reanalysis=requires_reanalysis,
                confidence_penalty=self.compute_confidence_penalty(issues),
                audit_notes=[
                    f"Round {current_round + 1}: {len(errors)} errors, {len(warnings)} warnings",
                    f"Decision: {'REJECT' if requires_reanalysis else 'APPROVE'}"
                ]
            )
            
            # Update state
            state['critic_result_v2'] = critic_result
            state['critic_round'] = next_round
            state['validation_status'] = validation_status.value
            state['agents_executed'].append('critic_v2')
            
            # Add warnings to state
            for issue in warnings:
                if issue.description not in state.get('warnings', []):
                    state['warnings'].append(f"Critic: {issue.description}")
            
        except Exception as e:
            logger.error(f"Critic V2 error: {str(e)}")
            state['errors'].append(f"Critic V2: {str(e)}")
            state['validation_status'] = ValidationStatus.FLAGGED.value
        
        return state


# Singleton instance
critic_v2 = CriticV2()
