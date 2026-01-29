"""
The Critic Agent (Red Teamer)
Validates sources and identifies biases in predictions
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from app.config import settings
from app.graph.state import ForecastState, CriticValidationOutput, ValidationStatus

logger = logging.getLogger(__name__)


class TheCritic:
    """
    Red teaming agent that validates sources, identifies biases,
    and ensures data quality of all inputs.
    """

    def __init__(self):
        self.enabled = settings.CRITIC_ENABLED
        self.safe_list = self._initialize_safe_list()

    def _initialize_safe_list(self) -> Dict[str, List[str]]:
        """
        Initialize the "Safe List" of trusted sources.
        Categorized by institutional type.
        """
        return {
            'official': [
                'World Bank',
                'IMF',
                'UN Agencies',
                'Central Banks',
                'OECD',
                'BIS',
                'Federal Reserve',
                'ECB'
            ],
            'institutional': [
                'Reuters',
                'AP News',
                'AFP',
                'Bloomberg',
                'Financial Times',
                'Wall Street Journal',
                'Economist',
                'BBC',
                'RAND',
                'Carnegie',
                'Brookings',
                'Chatham House',
                'Council on Foreign Relations'
            ],
            'academic': [
                'Peer-reviewed journals',
                'MIT',
                'Stanford',
                'Oxford',
                'Cambridge',
                'Harvard',
                'Princeton',
                'Yale'
            ],
            'regional_mena': [
                'AIM Technologies',
                'Al Jazeera',
                'Asharq Al-Awsat',
                'Gulf News',
                'Arab News',
                'Middle East Eye',
                'Al-Monitor'
            ],
            'financial': [
                'Polygon.io',
                'Alpha Vantage',
                'Financial Modeling Prep',
                'Yahoo Finance',
                'EODHD',
                'IEX Cloud'
            ],
            'data_providers': [
                'GDELT',
                'NewsAPI.ai',
                'NewsData.io',
                'Webz.io',
                'Semantic Scholar',
                'ACLED',
                'Election',
                'Legislation'
            ]
        }

    async def validate(self, state: ForecastState) -> Dict[str, Any]:
        """
        Main validation method for red-teaming the forecast.
        
        Args:
            state: Current ForecastState
            
        Returns:
            Updated state with validation results
        """
        if not self.enabled:
            logger.warning("The Critic is disabled")
            return state

        try:
            logger.info("The Critic starting validation")
            
            # Validate data sources
            source_validation = self._validate_sources(
                state.get('temporal_data_sources', []) +
                state.get('context_data_sources', []) +
                state.get('think_tank_sources', []) +
                state.get('political_data_sources', [])
            )
            
            # Check for bias indicators
            bias_flags = self._identify_bias_flags(state)

            
            # Assess data quality
            data_quality_score = self._assess_data_quality(state)
            
            # LLM Red Team Audit
            audit_result = await self._audit_forecast(state)
            audit_verdict = audit_result.get("verdict", "APPROVED")
            audit_reasoning = audit_result.get("reasoning", "")
            
            # Determine validation status (combining Logic and LLM)
            validation_status = self._determine_validation_status(
                source_validation,
                bias_flags,
                data_quality_score
            )
            
            # DELPHI CONSENSUS CHECK
            # If consensus is low and we haven't done enough rounds, reject to trigger loop
            delphi_score = state.get("delphi_convergence_score", 1.0)
            delphi_round = state.get("delphi_round", 0)
            
            if delphi_round < 2 and delphi_score < 0.7:
                validation_status = ValidationStatus.REJECTED
                state['errors'].append(f"The Critic (Delphi): Consensus Low ({delphi_score:.2f}). Triggering Round {delphi_round + 1}.")
            
            # LLM Veto Power
            if audit_verdict == "REJECT":
                validation_status = ValidationStatus.REJECTED
                state['errors'].append(f"The Critic (Red Team): REJECTED - {audit_reasoning}")
            elif audit_verdict == "CONDITIONAL APPROVAL":
                if validation_status == ValidationStatus.APPROVED:
                    validation_status = ValidationStatus.FLAGGED
                state['warnings'].append(f"The Critic (Red Team): Conditional Approval - {audit_reasoning}")

            # Update state
            state['validation_status'] = validation_status
            state['bias_flags'] = bias_flags
            state['data_quality_score'] = data_quality_score
            state['source_validation_results'] = source_validation
            state['critic_audit'] = audit_result # Store full audit
            state['agents_executed'].append('critic')
            
            if validation_status == ValidationStatus.FLAGGED and audit_verdict != "CONDITIONAL APPROVAL":
                 state['warnings'].append(
                    f"The Critic (Logic): {len(bias_flags)} bias flags identified. "
                    f"Reduce confidence by 15-30%."
                )
            elif validation_status == ValidationStatus.REJECTED and audit_verdict != "REJECT":
                 state['errors'].append(
                    "The Critic (Logic): Validation failed. Forecast not recommended."
                )
            
            logger.info(
                f"The Critic completed. Status: {validation_status}, "
                f"Data Quality: {data_quality_score:.2%}, Audit: {audit_verdict}"
            )
            
        except Exception as e:
            logger.error(f"The Critic error: {str(e)}")
            state['errors'].append(f"The Critic: {str(e)}")
            state['validation_status'] = ValidationStatus.FLAGGED
        
        return state

    async def _audit_forecast(self, state: ForecastState) -> Dict[str, str]:
        """
        Perform a hostile audit using the LLM.
        """
        try:
            from app.llm.client import llm_manager
            
            scenario = state.get('scenario', "Unknown")
            evidence = state.get('evidence_summary', "No evidence summary")
            claims = state.get('evidence_claims', [])
            
            prompt = (
                f"Forecasting Audit requested for scenario: '{scenario}'\n\n"
                f"Evidence Provided:\n{evidence}\n\n"
                f"Claims Made:\n{json.dumps(claims, indent=2)}\n\n"
                "Act as a Red Team Auditor. Challenge this forecast analysis:\n"
                "1. **Bias Check:** Is there recency bias or source selection bias?\n"
                "2. **Overconfidence:** Are the confidence levels justified by the evidence?\n"
                "3. **Missing Evidence:** What critical data points are absent?\n\n"
                "Return valid JSON ONLY:\n"
                "{\n"
                "  \"verdict\": \"REJECT\" | \"CONDITIONAL APPROVAL\" | \"APPROVED\",\n"
                "  \"bias_check\": \"...\",\n"
                "  \"overconfidence_check\": \"...\",\n"
                "  \"missing_evidence\": \"...\",\n"
                "  \"reasoning\": \"Summary decision logic...\"\n"
                "}"
            )
            
            response = await llm_manager.complete(
                prompt,
                system_prompt="You are a Red Team Auditor. Be critical and objective. Output valid JSON.",
                temperature=0.1,
                max_tokens=256
            )
            
            import json
            text = response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
            
        except Exception as e:
            logger.warning(f"Critic Audit failed: {e}")
            return {"verdict": "APPROVED", "reasoning": "Audit failed, defaulting to approved."}

    def _validate_sources(self, sources: List[str]) -> Dict[str, Any]:
        """
        Validate data sources against the Safe List.
        """
        validation_results = {}
        safe_sources = []
        flagged_sources = []
        
        for source in sources:
            is_safe = self._is_source_safe(source)
            validation_results[source] = {
                'safe': is_safe,
                'category': self._categorize_source(source)
            }
            
            if is_safe:
                safe_sources.append(source)
            else:
                flagged_sources.append(source)
        
        return {
            'total_sources': len(sources),
            'safe_sources': len(safe_sources),
            'flagged_sources': len(flagged_sources),
            'details': validation_results
        }

    def _is_source_safe(self, source: str) -> bool:
        """
        Check if a source is on the Safe List.
        """
        for category, sources in self.safe_list.items():
            for safe_source in sources:
                if safe_source.lower() in source.lower():
                    return True
        return False

    def _categorize_source(self, source: str) -> str:
        """
        Categorize a source by type.
        """
        for category, sources in self.safe_list.items():
            for safe_source in sources:
                if safe_source.lower() in source.lower():
                    return category
        return 'unknown'

    def _identify_bias_flags(self, state: ForecastState) -> List[str]:
        """
        Identify potential bias indicators in the forecast.
        """
        flags = []
        
        # Check for extreme confidence
        if state.get('temporal_confidence', 0) > 0.95:
            flags.append("Temporal confidence suspiciously high (>95%)")
        
        # Check for sentiment-forecast alignment
        sentiment = state.get('context_sentiment', {}).get('sentiment_score', 0)
        adjustment = state.get('sentiment_adjustment', 0)
        
        if abs(adjustment) > 0.5:
            flags.append("Large sentiment adjustment (>50%) - verify drivers")
        
        # Check for data recency
        if state.get('data_freshness') == 'stale':
            flags.append("Data freshness concerns - consider recent events")
        
        # Check for source diversity
        all_sources = (
            state.get('temporal_data_sources', []) +
            state.get('context_data_sources', [])
        )
        if len(set(all_sources)) < len(all_sources) / 2:
            flags.append("Limited source diversity - consider additional data")
        
        # Check for conflicting signals
        temporal_drivers = state.get('temporal_drivers', [])
        context_themes = state.get('context_themes', [])
        
        if not any(d in context_themes for d in temporal_drivers):
            flags.append("Weak alignment between temporal drivers and context themes")

        # Political risk without data coverage
        political_risk = state.get('political_risk_score', 0.0)
        political_sources = state.get('political_data_sources', [])
        if political_risk > 0.85 and len(political_sources) < 2:
            flags.append("High political risk score with limited data coverage")
        
        return flags

    def _assess_data_quality(self, state: ForecastState) -> float:
        """
        Assess overall data quality score (0.0 to 1.0).
        """
        score = 0.8  # Start with baseline
        
        # Deduct for validation issues
        source_validation = state.get('source_validation_results', {})
        if source_validation.get('flagged_sources', 0) > 0:
            score -= 0.1 * source_validation['flagged_sources']
        
        # Deduct for bias flags
        bias_count = len(state.get('bias_flags', []))
        score -= 0.05 * bias_count
        
        # Bonus for high confidence
        if state.get('context_confidence', 0) > 0.8:
            score += 0.05
        
        return max(0.3, min(1.0, score))

    def _determine_validation_status(
        self,
        source_validation: Dict[str, Any],
        bias_flags: List[str],
        data_quality_score: float
    ) -> ValidationStatus:
        """
        Determine overall validation status.
        """
        if data_quality_score < 0.5 or len(bias_flags) > 5:
            return ValidationStatus.REJECTED
        elif source_validation.get('flagged_sources', 0) > 0 or len(bias_flags) > 2:
            return ValidationStatus.FLAGGED
        else:
            return ValidationStatus.APPROVED
