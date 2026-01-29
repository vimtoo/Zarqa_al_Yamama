"""
Political Risk Scorer
Computes a normalized political risk score based on event signals.
"""

import logging
from typing import Dict, Any, List

from app.config import settings
from app.graph.state import ForecastState
from app.agents.political_utils import clamp

logger = logging.getLogger(__name__)


class RiskScorer:
    """Agent to compute political risk scores."""

    def __init__(self):
        self.enabled = settings.RISK_SCORER_ENABLED

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        if not self.enabled:
            logger.warning("Risk Scorer is disabled")
            return state

        try:
            political_insights = state.get("political_insights", {})
            event_counts = political_insights.get("event_counts", {})

            acled_count = event_counts.get("acled", 0)
            gdelt_count = event_counts.get("gdelt", 0)
            news_count = event_counts.get("news", 0)

            event_factor = min(1.0, (acled_count * 1.2 + gdelt_count * 0.4 + news_count * 0.2) / 100)

            sentiment_score = state.get("context_sentiment", {}).get("sentiment_score", 0.0)
            negative_sentiment = max(0.0, -sentiment_score)

            volatility = state.get("volatility_factor", 1.0)
            volatility_factor = clamp((volatility - 1.0) / 0.5, 0.0, 1.0)

            themes = set(state.get("political_themes", []) + state.get("context_themes", []))
            conflict_bias = 0.2 if any(topic in themes for topic in ["security", "geopolitics", "protest"]) else 0.0

            base_score = 0.25 + (0.4 * event_factor) + (0.2 * negative_sentiment) + (0.1 * volatility_factor) + conflict_bias
            risk_score = clamp(base_score, 0.05, 0.95)

            drivers: List[str] = []
            if acled_count > 0:
                drivers.append("Conflict event intensity (ACLED)")
            if gdelt_count > 0:
                drivers.append("Elevated geopolitical coverage (GDELT)")
            if news_count > 0:
                drivers.append("Increased political news volume")
            if negative_sentiment > 0.2:
                drivers.append("Negative sentiment signals")
            if volatility_factor > 0.3:
                drivers.append("Heightened volatility")
            if conflict_bias > 0:
                drivers.append("Security and conflict themes")

            source_coverage = min(1.0, len(state.get("political_data_sources", [])) / 4)
            confidence = clamp(0.35 + (0.5 * source_coverage), 0.3, 0.9)

            state["political_risk_score"] = float(risk_score)
            state["political_risk_drivers"] = drivers
            state["political_risk_confidence"] = float(confidence)
            state["agents_executed"].append("risk_scorer")

            logger.info("Risk Scorer completed. Score: %.2f", risk_score)

        except Exception as exc:
            logger.error("Risk Scorer error: %s", str(exc))
            state["errors"].append(f"Risk Scorer: {str(exc)}")

        return state


risk_scorer = RiskScorer()
