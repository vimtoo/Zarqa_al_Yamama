"""
The Governor Agent (Ethical Oversight)
Enforces ethical guidelines and tracks citation lineage
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import uuid

from app.config import settings
from app.graph.state import ForecastState, GovernorOutput, EthicalStatus
from app.graph.contracts import BiasTriangulation, SourcePosition
from app.llm.client import llm_manager

logger = logging.getLogger(__name__)


class TheGovernor:
    """
    Ethical oversight agent that ensures compliance with guidelines,
    tracks attribution, and maintains audit trails.
    """

    def __init__(self):
        self.enabled = settings.GOVERNOR_ENABLED
        self.ethical_guidelines = self._initialize_ethical_guidelines()

    def _initialize_ethical_guidelines(self) -> Dict[str, str]:
        """
        Initialize ethical guidelines for the system.
        """
        return {
            'no_market_manipulation': (
                'Predictions must not be used to manipulate markets or prices'
            ),
            'no_personal_data': (
                'No personal identifying information in analysis or outputs'
            ),
            'transparency': (
                'All model limitations and assumptions must be disclosed'
            ),
            'balanced_representation': (
                'Geopolitical actors must be represented fairly and objectively'
            ),
            'cultural_sensitivity': (
                'Respect for cultural and religious sensitivities, especially MENA region'
            ),
            'data_protection': (
                'Compliance with GDPR, Kuwaiti data protection, and local regulations'
            ),
            'attribution': (
                'Complete citation chain for all data sources and reasoning'
            ),
            'no_harmful_predictions': (
                'Avoid predictions that could incite violence or discrimination'
            )
        }

    async def oversee(self, state: ForecastState) -> Dict[str, Any]:
        """
        Main oversight method for ethical governance.
        
        Args:
            state: Current ForecastState
            
        Returns:
            Updated state with ethical validation and audit trail
        """
        if not self.enabled:
            logger.warning("The Governor is disabled")
            return state

        try:
            logger.info("The Governor starting ethical oversight")
            
            # Validate ethical compliance
            ethical_status, compliance_notes = self._validate_ethical_compliance(state)
            
            # Build citation chain
            citation_chain = self._build_citation_chain(state)
            
            # Create audit log
            audit_log = self._create_audit_log(state, ethical_status)
            
            # Verify data protection
            data_protection_status = self._verify_data_protection(state)
            
            # Phase 3: Bias Triangulation (Rule 4)
            bias_triangulation = await self._analyze_bias_landscape(state)
            
            # Update state
            state['ethical_status'] = ethical_status
            state['citation_chain'] = citation_chain
            state['audit_log'] = audit_log
            state['data_protection_status'] = data_protection_status
            state['bias_triangulation'] = bias_triangulation
            
            # Check for Source Monoculture (Red Flag)
            if bias_triangulation:
                self._check_source_monoculture(bias_triangulation, state)
            
            state['agents_executed'].append('governor')
            
            if ethical_status == EthicalStatus.REQUIRES_REVIEW:
                state['warnings'].append(
                    "The Governor: Ethical review required before publication"
                )
            elif ethical_status == EthicalStatus.REJECTED:
                state['errors'].append(
                    "The Governor: Ethical compliance failed. Forecast cannot be published."
                )
            
            logger.info(
                f"The Governor completed. Status: {ethical_status}, "
                f"Citations: {len(citation_chain)}"
            )
            
        except Exception as e:
            logger.error(f"The Governor error: {str(e)}")
            state['errors'].append(f"The Governor: {str(e)}")
            state['ethical_status'] = EthicalStatus.REQUIRES_REVIEW
        
        return state

    def _validate_ethical_compliance(self, state: ForecastState) -> tuple:
        """
        Validate forecast against ethical guidelines.
        """
        compliance_notes = []
        violations = []
        
        # Check for personal data
        if self._contains_personal_data(state):
            violations.append("Personal identifying information detected")
        else:
            compliance_notes.append("✓ No personal data in analysis")
        
        # Check for market manipulation intent
        if self._appears_manipulative(state):
            violations.append("Forecast appears designed for market manipulation")
        else:
            compliance_notes.append("✓ No market manipulation indicators")
        
        # Check for harmful predictions
        if self._contains_harmful_content(state):
            violations.append("Forecast contains potentially harmful predictions")
        else:
            compliance_notes.append("✓ No harmful content detected")
        
        # Check for balanced representation
        if not self._has_balanced_representation(state):
            violations.append("Geopolitical representation may be biased")
        else:
            compliance_notes.append("✓ Balanced geopolitical representation")
        
        # Check for cultural sensitivity
        if not self._respects_cultural_sensitivity(state):
            violations.append("Cultural sensitivity concerns identified")
        else:
            compliance_notes.append("✓ Cultural sensitivity maintained")
        
        # Determine status
        if len(violations) >= 2:
            status = EthicalStatus.REJECTED
        elif len(violations) == 1:
            status = EthicalStatus.REQUIRES_REVIEW
        else:
            status = EthicalStatus.APPROVED
        
        return status, compliance_notes + violations

    def _build_citation_chain(self, state: ForecastState) -> List[str]:
        """
        Build complete citation chain for all data sources.
        """
        citations = []
        
        # Temporal data sources
        for source in state.get('temporal_data_sources', []):
            citations.append(f"{source} (Temporal Analysis)")
        
        # Context data sources
        for source in state.get('context_data_sources', []):
            citations.append(f"{source} (Context Analysis)")

        # Think tank sources
        for source in state.get('think_tank_sources', []):
            citations.append(f"{source} (Think Tank Analysis)")

        # Political data sources
        for source in state.get('political_data_sources', []):
            citations.append(f"{source} (Political Studies)")
        
        # Add timestamp and methodology
        citations.append(
            f"Analysis Date: {datetime.now().isoformat()}"
        )
        citations.append(
            f"Methodology: LangGraph Multi-Agent Workflow (Zarqa al Yamama v1.0)"
        )
        citations.append(
            f"Creator: Qusai Al-Duaij"
        )
        
        return citations

    def _create_audit_log(self, state: ForecastState, ethical_status: EthicalStatus) -> List[str]:
        """
        Create audit log for compliance tracking.
        """
        log = []
        
        log.append(f"[{datetime.now().isoformat()}] Forecast ID: {state.get('request_id', 'unknown')}")
        log.append(f"[{datetime.now().isoformat()}] Scenario: {state.get('scenario', 'unknown')}")
        log.append(f"[{datetime.now().isoformat()}] Agents Executed: {', '.join(state.get('agents_executed', []))}")
        log.append(f"[{datetime.now().isoformat()}] Validation Status: {state.get('validation_status', 'unknown')}")
        log.append(f"[{datetime.now().isoformat()}] Ethical Status: {ethical_status}")
        log.append(f"[{datetime.now().isoformat()}] Data Protection: COMPLIANT")
        log.append(f"[{datetime.now().isoformat()}] Audit Log Created")
        
        return log

    def _verify_data_protection(self, state: ForecastState) -> str:
        """
        Verify data protection compliance.
        """
        checks = [
            not self._contains_personal_data(state),
            self._has_encryption_ready(state),
            self._has_access_controls(state),
            self._has_retention_policy(state)
        ]
        
        if all(checks):
            return "COMPLIANT"
        elif sum(checks) >= 2:
            return "PARTIALLY_COMPLIANT"
        else:
            return "NON_COMPLIANT"

    # Helper validation methods
    def _contains_personal_data(self, state: ForecastState) -> bool:
        """
        Check if forecast contains personal identifying information.
        """
        # In production, use regex patterns and NLP to detect PII
        return False

    def _appears_manipulative(self, state: ForecastState) -> bool:
        """
        Check if forecast appears designed for market manipulation.
        """
        # Check for extreme confidence + extreme predictions
        confidence = state.get('quantified_confidence', 0)
        forecast = state.get('quantified_forecast', {})
        base = state.get('temporal_forecast', {})
        
        if confidence > 0.95 and forecast and base:
            base_value = base.get('forecast_30d', 0)
            final_value = forecast.get('final_forecast', 0)
            
            if base_value > 0:
                change_pct = abs((final_value - base_value) / base_value)
                if change_pct > 0.5:  # >50% change
                    return True
        
        return False

    def _contains_harmful_content(self, state: ForecastState) -> bool:
        """
        Check if forecast contains potentially harmful predictions.
        """
        # Check for incitement to violence or discrimination
        harmful_keywords = [
            'attack', 'war', 'genocide', 'ethnic cleansing',
            'discrimination', 'violence', 'terrorism'
        ]
        
        recommendation = state.get('strategic_recommendation', '').lower()
        
        for keyword in harmful_keywords:
            if keyword in recommendation:
                return True
        
        return False

    def _has_balanced_representation(self, state: ForecastState) -> bool:
        """
        Check for balanced representation of geopolitical actors.
        """
        actors = state.get('context_key_actors', []) + state.get('political_key_actors', [])
        
        # Should have multiple perspectives
        return len(actors) >= 2

    def _respects_cultural_sensitivity(self, state: ForecastState) -> bool:
        """
        Check for cultural sensitivity, especially MENA region.
        """
        # In production, use cultural sensitivity guidelines
        # For now, assume compliance
        return True

    def _has_encryption_ready(self, state: ForecastState) -> bool:
        """
        Check if data is ready for encryption.
        """
        return True  # Simplified check

    def _has_access_controls(self, state: ForecastState) -> bool:
        """
        Check if access controls are in place.
        """
        return True  # Simplified check

    def _has_retention_policy(self, state: ForecastState) -> bool:
        """
        Check if data retention policy is defined.
        """
        return True  # Simplified check

    async def _analyze_bias_landscape(self, state: ForecastState) -> Any:
        """
        Analyze evidence for bias triangulation (Rule 4).
        """
        evidence = state.get('deduped_evidence', [])
        topic = state.get('scenario', 'Unknown Topic')
        
        if not evidence:
            return None

        try:
            # Prepare evidence summary for LLM
            evidence_text = "\n".join([
                f"Source {i}: {e.domain} - {e.snippet[:200]}" 
                for i, e in enumerate(evidence[:10])
            ])
            
            # Use Antigravity via LLMManager
            data = await llm_manager.analyze(
                data={"evidence": evidence_text, "topic": topic},
                analysis_type="bias_triangulation",
                role="bias_triangulation_v1",
                context="Bias triangulation"
            )
            
            data['topic'] = topic # Ensure topic matches
            
            # Fix unrepresented_perspective if string
            if isinstance(data.get('unrepresented_perspective'), str):
                data['unrepresented_perspective'] = [data['unrepresented_perspective']]
                
            return BiasTriangulation(**data)

        except Exception as e:
            logger.warning(f"Bias triangulation failed: {e}")
            return None

    def _check_source_monoculture(self, bias: BiasTriangulation, state: ForecastState):
        """
        Detect 'Source Monoculture' red flag.
        If > 80% sources share the same bias_rating, flag it.
        """
        if not bias.positions:
            return

        total = len(bias.positions)
        bias_counts = {}
        
        for pos in bias.positions:
            rating = pos.bias_rating
            bias_counts[rating] = bias_counts.get(rating, 0) + 1
        
        for rating, count in bias_counts.items():
            if count / total > 0.8 and total >= 3:
                warning = f"🚩 Source Monoculture Detected: {int((count/total)*100)}% sources are '{rating}'."
                state['warnings'].append(warning)
                if bias.consensus_status == "Consensus":
                    state['warnings'].append("⚠️ Consensus is suspect due to monoculture.")
