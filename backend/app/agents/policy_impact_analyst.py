"""
Policy Impact Analyst
Estimates policy impacts across key domains.
"""

import logging
from typing import Dict, Any, List

from app.config import settings
from app.graph.state import ForecastState
from app.graph.contracts import PolicyRippleOutcome
from app.llm.client import llm_manager
from app.agents.political_utils import clamp

logger = logging.getLogger(__name__)


class PolicyImpactAnalyst:
    """Agent to estimate policy impacts based on political signals."""

    def __init__(self):
        self.enabled = settings.POLICY_IMPACT_ANALYST_ENABLED

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        if not self.enabled:
            logger.warning("Policy Impact Analyst is disabled")
            return state

        try:
            risk_score = state.get("political_risk_score", 0.5)
            sentiment = state.get("context_sentiment", {}).get("sentiment_score", 0.0)
            themes = state.get("political_themes", []) or state.get("context_themes", [])
            think_tank_topics = state.get("think_tank_topics", [])

            domain_map = {
                "energy": "energy",
                "economics": "economy",
                "finance": "finance",
                "security": "security",
                "geopolitics": "security",
                "technology": "technology",
                "governance": "governance",
                "climate": "environment"
            }

            domains: List[str] = []
            for topic in themes + think_tank_topics:
                domain = domain_map.get(topic)
                if domain and domain not in domains:
                    domains.append(domain)

            if not domains:
                domains = ["governance", "security", "economy"]

            summary_direction = "neutral"
            if sentiment < -0.2 or risk_score > 0.65:
                summary_direction = "negative"
            elif sentiment > 0.2 and risk_score < 0.45:
                summary_direction = "positive"

            summary_magnitude = "low"
            if risk_score > 0.75 or abs(sentiment) > 0.6:
                summary_magnitude = "high"
            elif risk_score > 0.55 or abs(sentiment) > 0.3:
                summary_magnitude = "medium"

            impacts = []
            for domain in domains[:5]:
                direction = summary_direction
                magnitude = summary_magnitude

                impacts.append({
                    "domain": domain,
                    "direction": direction,
                    "magnitude": magnitude,
                    "rationale": f"Risk score {risk_score:.2f} and sentiment {sentiment:+.2f} drive impact."
                })

            confidence = clamp(0.4 + (state.get("political_risk_confidence", 0.4) * 0.4), 0.3, 0.85)

            policy_summary = (
                f"Policy impacts show {summary_direction} pressure across {', '.join(domains[:3])}. "
                f"Risk score at {risk_score:.2f} implies {summary_magnitude} volatility."
            )

            state["policy_impact_forecast"] = {
                "summary": policy_summary,
                "impacts": impacts,
                "confidence": float(confidence)
            }
            
            # Phase 3: Policy Ripple Analysis (Rule 4)
            policy_ripples = await self._analyze_ripple_effects(state, domains)
            state["policy_ripples"] = policy_ripples
            
            state["agents_executed"].append("policy_impact_analyst")

            logger.info("Policy Impact Analyst completed")

        except Exception as exc:
            logger.error("Policy Impact Analyst error: %s", str(exc))
            state["errors"].append(f"Policy Impact Analyst: {str(exc)}")

        return state


    async def _analyze_ripple_effects(self, state: ForecastState, domains: List[str]) -> Any:
        """
        Analyze second-order policy ripple effects.
        """
        scenario = state.get("scenario", "")
        if not scenario:
            return None
            
        try:
            prompt = (
                f"Analyze the policy ripple effects for: {scenario}\n"
                f"Impacted Domains: {', '.join(domains)}\n\n"
                f"Task: Generate a Policy Ripple Outcome (JSON).\n"
                f"Valid Domains: geopolitics, macroeconomics, finance, technology, security, policy\n"
                f"Requirements:\n"
                f"1. root_event: The central policy change\n"
                f"2. first_order_effects: Direct consequences [description, domain(MUST be valid), likelihood, impact_severity(HIGH/MEDIUM/LOW)]\n"
                f"3. second_order_effects: Indirect consequences (Ripples) [same schema]\n"
                f"4. feedback_loops: List of reinforcing cycles\n"
            )
            
            raw_json = await llm_manager.complete(
                prompt,
                system_prompt="You are a Systems Thinker. You map causal chains. Output strictly valid JSON.",
                temperature=0.0
            )
            
            import json
            import re
            
            # Robust JSON cleaning
            cleaned = raw_json.strip()
            # Remove Markdown code blocks
            if "```" in cleaned:
                cleaned = re.sub(r"```(?:json)?(.*?)```", r"\1", cleaned, flags=re.DOTALL).strip()
            
            # Find JSON object
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]
            
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError:
                # Try correcting trailing commas
                cleaned = re.sub(r",\s*}", "}", cleaned)
                cleaned = re.sub(r",\s*]", "]", cleaned)
                data = json.loads(cleaned)
            
            # Map invalid domains
            valid_domains = ["geopolitics", "macroeconomics", "finance", "technology", "security", "policy"]
            domain_map = {
                "energy": "macroeconomics",
                "economy": "macroeconomics",
                "trade": "finance",
                "governance": "policy",
                "environment": "geopolitics"
            }
            
            def fix_domain(effects):
                for eff in effects:
                    d = eff.get('domain', '').lower()
                    if d not in valid_domains:
                        eff['domain'] = domain_map.get(d, "geopolitics") # Default fallback
            
            if 'first_order_effects' in data:
                fix_domain(data['first_order_effects'])
            if 'second_order_effects' in data:
                fix_domain(data['second_order_effects'])
                
            return PolicyRippleOutcome(**data)
            
        except Exception as e:
            logger.warning(f"Policy ripple analysis failed: {e}")
            if 'raw_json' in locals():
                logger.debug(f"Raw output: {raw_json}")
            return None


policy_impact_analyst = PolicyImpactAnalyst()
