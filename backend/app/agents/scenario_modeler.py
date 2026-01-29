"""
Scenario Modeler
Produces scenario probabilities for political futures.
"""

import logging
from typing import Dict, Any, List

from app.config import settings
from app.graph.state import ForecastState
from app.agents.political_utils import clamp, normalize_probabilities, scenario_templates
from app.llm.client import llm_manager
from app.db.neo4j import get_neo4j_graph

logger = logging.getLogger(__name__)


class ScenarioModeler:
    """Agent to generate scenario probabilities."""

    def __init__(self):
        self.enabled = settings.SCENARIO_MODELER_ENABLED

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        if not self.enabled:
            logger.warning("Scenario Modeler is disabled")
            return state

        try:
            scenario = state.get("scenario", "")
            risk_score = state.get("political_risk_score", 0.5)
            sentiment = state.get("context_sentiment", {}).get("sentiment_score", 0.0)
            
            # Phase 5 Fix: Use LLM for competing scenarios instead of deterministic math
            scenarios = await self._generate_scenarios(state, scenario, risk_score, sentiment)
            
            # Enforce minimum 2 scenarios (Compromise/Status Quo fallback if LLM fails uniquely)
            # Enforce minimum 2 scenarios (Compromise/Status Quo fallback if LLM fails uniquely)
            if len(scenarios) < 2:
                logger.warning("LLM returned fewer than 2 scenarios. Injecting fallback.")
                scenarios.append({
                    "scenario_name": "Status Quo",
                    "probability": 0.5,
                    "likelihood_band": "Medium", 
                    "narrative": "Continuity of current trends.",
                    "drivers": ["Inertia"],
                    "confidence_check": "Fallback injection"
                })

            state["scenario_probabilities"] = scenarios
            state["agents_executed"].append("scenario_modeler")

            # Phase H: Write Hypothesis Graph
            await self._write_to_graph(state, scenarios)

            logger.info("Scenario Modeler completed with %d scenarios", len(scenarios))

        except Exception as exc:
            logger.error("Scenario Modeler error: %s", str(exc))
            state["errors"].append(f"Scenario Modeler: {str(exc)}")

        return state

    async def _write_to_graph(self, state: ForecastState, scenarios: List[Dict[str, Any]]):
        """Write competing hypotheses to Neo4j graph (Phase H)"""
        try:
            graph = get_neo4j_graph()
            if not await graph.health_check():
                logger.warning("Neo4j not connected, skipping hypothesis graph write")
                return

            event_id = state.get("request_id", "unknown_event")
            # Collect evidence clusters
            evidence_clusters = []
            if "deduped_evidence" in state and state["deduped_evidence"]:
                # specific to object structure
                # We assume EvidenceItem objects or dicts
                for item in state["deduped_evidence"]:
                    # check if dict or object
                    cid = getattr(item, "independence_cluster_id", None) 
                    if not cid and isinstance(item, dict):
                        cid = item.get("independence_cluster_id")
                    
                    if cid and cid not in evidence_clusters:
                        evidence_clusters.append(cid)
            
            import uuid
            
            for index, scen in enumerate(scenarios):
                # Generate unique scenario_id for this hypothesis branch
                # We use a hash or uuid. Let's use uuid.
                scenario_branch_id = str(uuid.uuid4())
                
                await graph.create_hypothesis_edge(
                    event_id=event_id,
                    outcome_name=scen.get("scenario_name", "Unknown Scenario"),
                    scenario_id=scenario_branch_id,
                    confidence=scen.get("likelihood_band", "Medium"),
                    evidence_cluster_ids=evidence_clusters,
                    provenance=f"ScenarioModeler generated based on {len(evidence_clusters)} evidence clusters.",
                    weight=scen.get("probability", 0.0)
                )

        except Exception as e:
            logger.error(f"Failed to write hypothesis graph: {e}")

    async def _generate_scenarios(self, state: ForecastState, scenario: str, risk_score: float, sentiment: float) -> List[Dict[str, Any]]:
        """
        Generate competing scenarios using LLM to avoid false precision.
        """
        try:
            prompt = (
                f"Generate 2-4 competing future scenarios for: {scenario}\n"
                f"Context: Risk Score {risk_score:.2f}, Sentiment {sentiment:.2f}\n"
                f"Task: Return a JSON list of objects matching ScenarioProbability schema.\n"
                f"Schema Requirements:\n"
                f"- scenario_name: str\n"
                f"- probability: float (0.0-1.0, must sum to approx 1.0)\n"
                f"- likelihood_band: 'Low'|'Medium'|'High'|'Critical'\n"
                f"- narrative: str (brief description)\n"
                f"- triggers: List[str] (preconditions)\n"
                f"- indicators: List[str] (early warning signals)\n"
                f"- confidence_check: str (why this band?)\n"
            )

            raw_json = await llm_manager.complete(
                prompt,
                system_prompt="You are a Strategic Forecaster. You MUST provide alternative futures. DO NOT be deterministic.",
                temperature=0.4
            )
            
            import json
            import re
            
            cleaned = raw_json.strip()
            if "```" in cleaned:
                cleaned = re.sub(r"```(?:json)?(.*?)```", r"\1", cleaned, flags=re.DOTALL).strip()
            
            data = json.loads(cleaned)
            if isinstance(data, dict) and "scenarios" in data:
                data = data["scenarios"]
            
            if not isinstance(data, list):
                logger.warning("Scenario output is not a list")
                return []
                
            return data
            
        except Exception as e:
            logger.error(f"Scenario generation failed: {e}")
            return []

        return state


scenario_modeler = ScenarioModeler()
