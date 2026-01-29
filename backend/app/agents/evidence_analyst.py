"""
Evidence Analyst Agent
Builds deeper evidence-based justifications from trusted snippets.
"""

import json
import logging
from typing import Any, Dict, List

from app.config import settings
from app.graph.state import ForecastState
from app.llm.client import llm_manager

logger = logging.getLogger(__name__)

MAX_SNIPPETS = 10


def _clean_response(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0]
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0]
    return cleaned.strip()


def _format_snippets(results: List[Dict[str, Any]]) -> str:
    lines = []
    for idx, item in enumerate(results[:MAX_SNIPPETS], start=1):
        title = item.get("title", "") or "Untitled"
        url = item.get("link", "") or ""
        snippet = item.get("snippet", "") or ""
        lines.append(f"[{idx}] {title}\nURL: {url}\nSnippet: {snippet}")
    return "\n\n".join(lines)


def _fallback_evidence(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(results)
    confidence = 0.3 if count < 2 else 0.5
    return {
        "summary_en": "Evidence is limited; conclusions are tentative.",
        "summary_ar": "الأدلة محدودة؛ الاستنتاجات أولية.",
        "confidence": confidence,
        "claims": [],
        "contradictions_en": [],
        "contradictions_ar": [],
        "unknowns_en": ["More trusted sources are needed to confirm the claims."],
        "unknowns_ar": ["هناك حاجة إلى مصادر موثوقة إضافية لتأكيد الادعاءات."],
    }


class EvidenceAnalyst:
    """
    Deepens research by extracting claims, contradictions, and justifications.
    """

    def __init__(self):
        self.enabled = settings.EVIDENCE_ANALYST_ENABLED

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        if not self.enabled:
            logger.warning("Evidence Analyst is disabled")
            return state

        results = state.get("walled_garden_results", []) or []
        scenario = state.get("scenario", "")

        if not results:
            state["evidence_summary"] = "No trusted evidence available."
            state["evidence_claims"] = []
            state["evidence_confidence"] = 0.0
            state["evidence_contradictions"] = []
            state["evidence_unknowns"] = ["No trusted sources returned for this query."]
            state["evidence_error"] = "No trusted evidence available"
            return state

        try:
            snippets = _format_snippets(results)
            prompt = (
                "Synthesize the search results into a JSON object containing:\n"
                "* `evidence_summary`: English summary.\n"
                "* `evidence_summary_ar`: Arabic 'transcreation' (not literal translation).\n"
                "* `claims`: List of specific assertions.\n"
                "* `contradictions`: List where Source A disagrees with Source B.\n"
                "* `unknowns`: Explicit list of what data is MISSING.\n"
                "* `confidence_score`: 0.0 to 1.0 based on source density.\n\n"
                "Use ONLY the provided snippets."
                f"\n\nScenario: {scenario}\n\nSnippets:\n{snippets}"
            )

            response_text = await llm_manager.complete(
                prompt,
                system_prompt="You are a precise evidence analyst. Output valid JSON only.",
                temperature=0.2,
                max_tokens=900,
            )

            cleaned = _clean_response(response_text)
            data = json.loads(cleaned) if cleaned else {}

            summary_en = data.get("evidence_summary") or "Evidence summary unavailable."
            summary_ar = data.get("evidence_summary_ar") or "ملخص الأدلة غير متوفر."
            confidence = float(data.get("confidence_score", 0.5))
            claims = data.get("claims", []) # List of strings or objects

            state["evidence_summary"] = summary_en
            state["evidence_summary_ar"] = summary_ar
            state["evidence_claims"] = claims
            state["evidence_confidence"] = confidence
            state["evidence_contradictions"] = data.get("contradictions", []) or []
            # Note: User didn't ask for contradictions_ar in prompt, but state has it. 
            # I will map contradictions to both or leave AR empty if not generated.
            # The prompt requested "contradictions": List.
            state["evidence_contradictions_ar"] = [] 
            state["evidence_unknowns"] = data.get("unknowns", []) or []
            # Same for unknowns_ar
            state["evidence_unknowns_ar"] = []
            state["evidence_error"] = None
            state["agents_executed"].append("evidence_analyst")

        except Exception as exc:
            logger.error("Evidence Analyst error: %s", str(exc))
            fallback = _fallback_evidence(results)
            state["evidence_summary"] = fallback["summary_en"]
            state["evidence_summary_ar"] = fallback["summary_ar"]
            state["evidence_claims"] = fallback["claims"]
            state["evidence_confidence"] = fallback["confidence"]
            state["evidence_contradictions"] = fallback["contradictions_en"]
            state["evidence_contradictions_ar"] = fallback["contradictions_ar"]
            state["evidence_unknowns"] = fallback["unknowns_en"]
            state["evidence_unknowns_ar"] = fallback["unknowns_ar"]
            state["evidence_error"] = str(exc)
            state["warnings"].append(f"Evidence Analyst: {str(exc)}")

        return state


evidence_analyst = EvidenceAnalyst()
