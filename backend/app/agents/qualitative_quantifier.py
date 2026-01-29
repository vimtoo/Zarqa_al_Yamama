"""
Qualitative Quantifier Agent
Synthesizes non-numeric event forecasts with explicit uncertainty handling.
Enforces Hard Rule #2: Uncertainty Preservation.
"""

import logging
import json
from typing import Dict, Any, List

from app.config import settings
from app.graph.state import ForecastState
from app.graph.contracts import QualitativeForecast, EvidenceItem
from app.llm.client import llm_manager

logger = logging.getLogger(__name__)

class QualitativeQuantifier:
    """
    The Outcome Estimator.
    Instead of calculating a price target, it estimates the likelihood of complex event outcomes.
    """

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        """
        Synthesize qualitative forecast from available evidence.
        """
        scenario = state.get("scenario", "")
        if not scenario:
            return state

        # Gather context from previous agents
        evidence_pool = state.get("deduped_evidence", [])
        narrative_brief = state.get("narrative_brief", "")
        
        # If no dedicated evidence, fallback to raw agent outputs
        if not evidence_pool:
             # Try to fish out evidence from agent outputs
             for output in state.get("agent_outputs", {}).values():
                 if hasattr(output, "evidence"):
                     evidence_pool.extend(output.evidence)

        logger.info(f"Qualitative Quantifier Analysis: {len(evidence_pool)} evidence items available.")

        prompt = (
            f"Analyze the scenario: '{scenario}'\n"
            f"Background Context: {narrative_brief}\n"
            f"Evidence Count: {len(evidence_pool)}\n\n"
            f"Task: Generate a Qualitative Forecast.\n"
            f"STRICT RULES:\n"
            f"1. NO numeric probabilities (Use: Almost Certain, Likely, Toss-up, Unlikely, Remote).\n"
            f"2. You MUST identify what you DON'T know (Unknown Factors).\n"
            f"3. You MUST identify preconditions and blockers.\n\n"
            f"Output JSON matching exactly:\n"
            f"{{"
            f"  'outcome_label': 'Short summary of outcome',\n"
            f"  'likelihood_category': 'Likely',\n"
            f"  'time_horizon_label': '6 months',\n"
            f"  'preconditions': ['List of things that must happen first'],\n"
            f"  'blockers': ['List of things that prevent this'],\n"
            f"  'confidence_score': 0.7,\n"
            f"  'unknown_factors': ['List of critical missing info'],\n"
            f"  'evidence_chain': ['List of evidence UUIDs that support this']\n"
            f"}}"
        )
        
        # Attach evidence snippets to context (limited to avoid overflow)
        context_str = "\n".join([f"- [{e.id}] {e.snippet[:150]}..." for e in evidence_pool[:10]])
        full_prompt = f"{prompt}\n\nEvidence:\n{context_str}"

        try:
            raw_json = await llm_manager.complete(
                full_prompt,
                system_prompt="You are the Zarqa Outcome Estimator. You DO NOT collapse uncertainty. You preserve it.",
                temperature=0.2 # Low temp for schema adherence
            )
            
            # Robust Parsing
            data = self._clean_json(raw_json)
            
            # Ensure valid enum value for likelihood
            valid_cats = ["Almost Certain", "Likely", "Toss-up", "Unlikely", "Remote"]
            if data.get("likelihood_category") not in valid_cats:
                # Fuzzy match or default
                logger.warning(f"Invalid likelihood '{data.get('likelihood_category')}', defaulting to 'Toss-up'")
                data["likelihood_category"] = "Toss-up"

            # Validate against evidence IDs (Hallucination check)
            valid_ids = {e.id for e in evidence_pool}
            filtered_chain = [eid for eid in data.get("evidence_chain", []) if eid in valid_ids]
            data["evidence_chain"] = filtered_chain
            
            # Force compliance with unknown_factors invariant
            if not data.get("unknown_factors"):
                data["unknown_factors"] = ["Specific timing of events", "Internal decision making process"]
            
            forecast = QualitativeForecast(**data)
            
            state["qualitative_forecast"] = forecast
            state["agents_executed"].append("qualitative_quantifier")
            
            logger.info(f"Qualitative Forecast: {forecast.outcome_label} ({forecast.likelihood_category})")

        except Exception as e:
            logger.error(f"Qualitative Quantifier Failed: {e}")
            state["errors"].append(f"Qualitative Quantifier: {str(e)}")

        return state

    def _clean_json(self, raw: str) -> Dict:
        import re
        import json
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        return json.loads(cleaned)

qualitative_quantifier = QualitativeQuantifier()
