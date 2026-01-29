"""
Schema Validator
Validates agent outputs against v2 AgentOutput contract before fusion
"""

import logging
from typing import List, Dict, Tuple, Optional
from pydantic import ValidationError

from app.graph.contracts import (
    AgentOutput,
    ClaimItem,
    EvidenceItem,
    ValidationIssue,
)
from app.graph.state import ForecastState

logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Validates all agent outputs before they reach the Quantifier.
    
    Checks:
    1. Schema compliance (AgentOutput structure)
    2. Evidence linkage (all evidence_ids exist)
    3. Claim completeness (required fields present)
    4. Confidence bounds (0.0 - 1.0)
    """
    
    def __init__(self):
        pass
    
    def validate_agent_output(self, output: Dict) -> Tuple[Optional[AgentOutput], List[ValidationIssue]]:
        """
        Validate a raw agent output dict against AgentOutput schema.
        
        Returns:
            (AgentOutput, []) if valid
            (None, [ValidationIssue, ...]) if invalid
        """
        issues = []
        
        try:
            # Attempt to parse as AgentOutput
            validated = AgentOutput(**output)
            return validated, []
            
        except ValidationError as e:
            # Convert Pydantic errors to ValidationIssue
            for error in e.errors():
                field = ".".join(str(loc) for loc in error['loc'])
                issues.append(ValidationIssue(
                    issue_type="schema_violation",
                    severity="error",
                    description=f"Field '{field}': {error['msg']}",
                    affected_ids=[]
                ))
            return None, issues
    
    def validate_evidence_linkage(self, agent_output: AgentOutput) -> List[ValidationIssue]:
        """
        Ensure all claim evidence_ids refer to existing evidence.
        """
        issues = []
        evidence_ids = {e.id for e in agent_output.evidence}
        
        for claim in agent_output.claims:
            missing = [eid for eid in claim.evidence_ids if eid not in evidence_ids]
            if missing:
                issues.append(ValidationIssue(
                    issue_type="claim_evidence_mismatch",
                    severity="error",
                    description=f"Claim '{claim.id}' references non-existent evidence: {missing}",
                    affected_ids=[claim.id] + missing
                ))
        
        return issues
    
    def validate_confidence_bounds(self, agent_output: AgentOutput) -> List[ValidationIssue]:
        """
        Ensure all confidence values are within [0.0, 1.0].
        """
        issues = []
        
        # Check overall confidence
        if not 0.0 <= agent_output.confidence <= 1.0:
            issues.append(ValidationIssue(
                issue_type="schema_violation",
                severity="error",
                description=f"Agent confidence {agent_output.confidence} out of bounds [0.0, 1.0]",
                affected_ids=[agent_output.agent_id]
            ))
        
        # Check claim confidences
        for claim in agent_output.claims:
            if not 0.0 <= claim.confidence <= 1.0:
                issues.append(ValidationIssue(
                    issue_type="schema_violation",
                    severity="warning",
                    description=f"Claim confidence {claim.confidence} out of bounds",
                    affected_ids=[claim.id]
                ))
        
        return issues
    
    def validate_claims_have_text(self, agent_output: AgentOutput) -> List[ValidationIssue]:
        """
        Ensure all claims have non-empty text.
        """
        issues = []
        
        for claim in agent_output.claims:
            if not claim.text or len(claim.text.strip()) < 10:
                issues.append(ValidationIssue(
                    issue_type="schema_violation",
                    severity="warning",
                    description=f"Claim '{claim.id}' has insufficient text (min 10 chars)",
                    affected_ids=[claim.id]
                ))
        
        return issues
    
    def validate_full(self, agent_output: AgentOutput) -> List[ValidationIssue]:
        """
        Run all validations on an AgentOutput.
        """
        all_issues = []
        all_issues.extend(self.validate_evidence_linkage(agent_output))
        all_issues.extend(self.validate_confidence_bounds(agent_output))
        all_issues.extend(self.validate_claims_have_text(agent_output))
        return all_issues
    
    def validate_state_outputs(self, state: ForecastState) -> Dict[str, List[ValidationIssue]]:
        """
        Validate all agent_outputs in the state.
        
        Returns:
            Dict mapping agent_id -> list of issues
        """
        results = {}
        agent_outputs = state.get('agent_outputs', {})
        
        for agent_id, output in agent_outputs.items():
            if isinstance(output, AgentOutput):
                issues = self.validate_full(output)
            else:
                # Raw dict, need to parse first
                parsed, parse_issues = self.validate_agent_output(output)
                if parsed:
                    issues = self.validate_full(parsed)
                else:
                    issues = parse_issues
            
            if issues:
                results[agent_id] = issues
                logger.warning(f"Validation issues for {agent_id}: {len(issues)} issues")
        
        return results


# Singleton instance
schema_validator = SchemaValidator()
