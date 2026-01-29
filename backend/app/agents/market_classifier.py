"""
Market Classifier Agent
Uses the LLM to determine whether a scenario is market-related.
"""

import json
import logging
import re
from typing import Dict, Any, Tuple

from app.config import settings
from app.graph.state import ForecastState
from app.llm.client import llm_manager

logger = logging.getLogger(__name__)


def _parse_label(response: str) -> str:
    if not response:
        return ""
    text = response.strip().lower()

    if text.startswith("{"):
        try:
            data = json.loads(text)
            for key in ("label", "classification", "scenario_type"):
                value = str(data.get(key, "")).lower().strip()
                if value in ("market", "non-market", "nonmarket"):
                    return "non-market" if value in ("non-market", "nonmarket") else "market"
        except Exception:
            pass

    first = re.split(r"[\s,.:;]+", text, maxsplit=1)[0]
    if first in ("market", "non-market", "nonmarket"):
        return "non-market" if first in ("non-market", "nonmarket") else "market"

    if re.search(r"\bnon[- ]?market\b", text) or re.search(r"\bnot\s+market\b", text):
        return "non-market"
    if re.search(r"\bnot\b.*\bmarket\b", text):
        return "non-market"
    if re.search(r"\bmarket\b", text):
        return "market"
    return ""


def _keyword_flags(scenario: str) -> Tuple[bool, bool]:
    keywords = [
        "price", "prices", "market", "stock", "equity", "index", "bond", "yield",
        "currency", "forex", "fx", "inflation", "gdp", "interest rate", "oil",
        "gold", "commodity", "commodities", "bitcoin", "crypto", "earnings",
        "trade", "tariff"
    ]
    non_market_keywords = [
        "election", "elections", "president", "prime minister", "parliament",
        "government", "policy", "law", "legal", "court", "constitution",
        "conflict", "war", "security", "military", "protest", "diplomacy",
        "sanction", "treaty", "terrorism", "coup"
    ]
    scenario_lower = scenario.lower()
    has_market = any(keyword in scenario_lower for keyword in keywords)
    has_non_market = any(keyword in scenario_lower for keyword in non_market_keywords)
    return has_market, has_non_market


def _heuristic_label(scenario: str) -> str:
    has_market, has_non_market = _keyword_flags(scenario)
    if has_market and not has_non_market:
        return "market"
    if has_non_market and not has_market:
        return "non-market"
    if has_market and has_non_market:
        return "market"
    return "non-market"


class MarketClassifier:
    """
    Classifies scenarios as market vs non-market using the LLM.
    """

    def __init__(self):
        self.enabled = settings.MARKET_CLASSIFIER_ENABLED

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        if not self.enabled:
            logger.warning("Market Classifier is disabled")
            return state

        scenario = (state.get("scenario") or "").strip()
        if not scenario:
            state["scenario_classification"] = "non-market"
            state["scenario_is_market"] = False
            state["scenario_classification_confidence"] = 0.0
            state["warnings"].append("Market Classifier: Missing scenario")
            return state

        try:
            system_prompt = (
                "You are the Market Classifier Agent. Your goal is to detect Second-Order Economic Effects. "
                "Analyze the causal chain of the scenario. Does this event trigger volatility in:\n"
                "1. Commodities (Oil, Gas, Gold)?\n"
                "2. Currency Pegs (KWD basket)?\n"
                "3. Sovereign Wealth Funds (KIA)?\n"
                "If YES to any, classify as MARKET.\n"
                "Example: A political resignation is NON-MARKET, but if it stalls a major fiscal budget vote, it becomes MARKET.\n"
                "Reply with strict JSON: {\"classification\": \"market\" | \"non-market\", \"reasoning\": \"your analysis\"}"
            )
            prompt = f"Scenario: {scenario}\nAnalyze causal chain and classify:"
            response = await llm_manager.complete(
                prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=100,  # Increased for reasoning
            )

            label = _parse_label(response)
            confidence = 0.7 if label else 0.3

            has_market, has_non_market = _keyword_flags(scenario)
            if label == "market" and has_non_market and not has_market:
                label = "non-market"
                confidence = 0.6
                state["warnings"].append("Market Classifier: keyword override to non-market")

            if not label:
                label = _heuristic_label(scenario)
                state["warnings"].append("Market Classifier: LLM fallback heuristic used")

            state["scenario_classification"] = label
            state["scenario_is_market"] = label == "market"
            state["scenario_classification_confidence"] = confidence
            state["agents_executed"].append("market_classifier")

            logger.info(
                "Market Classifier: %s (confidence %.2f) for scenario: %s",
                label,
                confidence,
                scenario,
            )

        except Exception as exc:
            logger.error("Market Classifier error: %s", str(exc))
            label = _heuristic_label(scenario)
            state["scenario_classification"] = label
            state["scenario_is_market"] = label == "market"
            state["scenario_classification_confidence"] = 0.2
            state["warnings"].append(f"Market Classifier: {str(exc)}")

        return state


market_classifier = MarketClassifier()
