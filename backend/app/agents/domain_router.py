"""
Domain Router Agent
Classifies scenarios into multi-domain contexts (Geopolitics, Macroeconomics, Finance, etc.)
Replaces the legacy binary MarketClassifier.
"""

import logging
from typing import Dict, Any, List
from pydantic import ValidationError

from app.config import settings
from app.graph.state import ForecastState
from app.graph.contracts import Domain, DomainClassification
from app.llm.client import llm_manager

logger = logging.getLogger(__name__)


class DomainRouter:
    """
    Router that determines which analysis domains are relevant for a scenario.
    Optimizes for "Lens Neutrality" by allowing multi-domain classification.
    """

    def __init__(self):
        self.enabled = True  # Always enabled in v2.1

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        """
        Analyze scenario to determine active domains.
        """
        scenario = (state.get("scenario") or "").strip()
        if not scenario:
            logger.warning("Domain Router: Missing scenario")
            return {
                "active_domains": [Domain.GEOPOLITICS],
                "primary_domain": Domain.GEOPOLITICS,
                "domain_confidence": 0.0,
                "warnings": ["Domain Router: Missing scenario, defaulted to Geopolitics"]
            }

        try:
            # systematic multi-label classification
            classification = await self._classify_domains(scenario)
            
            # --- INVARIANT ENFORCEMENT (LAZY ROUTER GUARD) ---
            # Forced activation of Temporal Analyst (Macro/Finance) for key economic terms
            # Keywords: oil, gas, sanctions, FX, currency, inflation, interest rate, trade, tariff, OPEC
            invariants = [
                "oil", "gas", "sanctions", "fx", "currency", 
                "inflation", "interest rate", "trade", "tariff", "opec"
            ]
            scenario_lower = scenario.lower()
            invariant_triggered = False
            triggered_keyword = ""
            
            for keyword in invariants:
                if keyword in scenario_lower:
                    invariant_triggered = True
                    triggered_keyword = keyword
                    break
            
            if invariant_triggered:
                # Force MACROECONOMICS if not already present
                # Use string comparison to avoid Enum identity issues if Pydantic casts differently
                current_domains = [d.value for d in classification.domains] if classification.domains else []
                
                if Domain.MACROECONOMICS.value not in current_domains and Domain.FINANCE.value not in current_domains:
                    logger.info(f"Router Invariant: Forced MACROECONOMICS for keyword '{triggered_keyword}'")
                    logger.info(f"Router Divergence: Invariant forced MACRO when LLM chose {classification.primary_domain}")
                    
                    # Add to domain list (prepend to ensure visibility)
                    classification.domains.append(Domain.MACROECONOMICS)
                    if classification.confidence > 0.9:
                        classification.confidence = 0.9 # Cap confidence if we had to intervene
                else:
                    logger.info(f"Router Invariant: Confirmed MACRO/FINANCE for keyword '{triggered_keyword}' (LLM agreed)")

                logger.info("[METRIC] Quantitative Activation Rate: Invariant Triggered")
            
            # Map back to state
            state["active_domains"] = classification.domains
            state["primary_domain"] = classification.primary_domain
            state["domain_confidence"] = classification.confidence
            state["agents_executed"].append("domain_router")
            
            logger.info(
                f"Domain Router: {classification.primary_domain} "
                f"(Active: {[d.value for d in classification.domains]})"
            )

        except Exception as exc:
            logger.error(f"Domain Router error: {exc}")
            # Fallback safe mode
            state["active_domains"] = [Domain.GEOPOLITICS, Domain.MACROECONOMICS]
            state["primary_domain"] = Domain.GEOPOLITICS
            state["domain_confidence"] = 0.1
            state["errors"].append(f"Domain Router: {str(exc)}")

        return state

    async def _classify_domains(self, scenario: str) -> DomainClassification:
        """
        Use LLM to classify the scenario.
        """
        try:
            # Use Antigravity via LLMManager
            classification_data = await llm_manager.analyze(
                data={"scenario": scenario},
                analysis_type="domain_classification",
                role="domain_router_v2",
                context="Domain classification"
            )

            # Normalize casing for Enums
            if 'domains' in classification_data:
                classification_data['domains'] = [d.lower() for d in classification_data['domains']]
            if 'primary_domain' in classification_data:
                classification_data['primary_domain'] = classification_data['primary_domain'].lower()
                
            return DomainClassification(**classification_data)
            
        except Exception as e:
            # Auto-recovery for generic errors
            logger.warning(f"LLM Classification failed, using fallback: {e}")
            return DomainClassification(
                domains=[Domain.GEOPOLITICS],
                primary_domain=Domain.GEOPOLITICS,
                confidence=0.1,
                reasoning="Fallback due to LLM error"
            )

domain_router = DomainRouter()
