"""
Report Writer Agent
Writes a Markdown report based on research outputs and LLM analysis.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings
from app.graph.state import ForecastState
from app.llm.client import llm_manager

logger = logging.getLogger(__name__)

ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:80] or "scenario"


def _reports_dir() -> Path:
    base_dir = Path(settings.REPORTS_DIR)
    if not base_dir.is_absolute():
        base_dir = Path(__file__).resolve().parents[2] / base_dir
    return base_dir


def _contains_arabic(text: str) -> bool:
    return bool(ARABIC_RE.search(text or ""))


def _shape_arabic_line(line: str) -> str:
    if not _contains_arabic(line):
        return line
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except Exception:
        return line

    reshaped = arabic_reshaper.reshape(line)
    return get_display(reshaped)


def _write_pdf(text: str, path: Path) -> None:
    from fpdf import FPDF

    font_path = Path(settings.REPORT_PDF_FONT_PATH)
    if not font_path.is_absolute():
        font_path = Path(__file__).resolve().parents[2] / font_path

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    if font_path.exists():
        pdf.add_font("NotoArabic", "", str(font_path))
        pdf.set_font("NotoArabic", size=12)
    else:
        pdf.set_font("Helvetica", size=12)

    for line in text.splitlines():
        pdf.multi_cell(0, 6, txt=_shape_arabic_line(line))
    pdf.output(str(path))


def _format_snippets(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    formatted = []
    for idx, item in enumerate(results, start=1):
        formatted.append(
            {
                "id": idx,
                "title": (item.get("title") or "").strip(),
                "snippet": (item.get("snippet") or "").strip(),
                "url": (item.get("link") or "").strip(),
            }
        )

def _build_report_payload(state: ForecastState) -> Dict[str, Any]:
    is_market = state.get("scenario_is_market", True)
    return {
        "scenario": state.get("scenario", ""),
        "scenario_is_market": is_market,
        "executive_summary": state.get("executive_summary", ""),
        "strategic_recommendation": state.get("strategic_recommendation", ""),
        "temporal_forecast": state.get("temporal_forecast", {}) if is_market else {},
        "quantified_forecast": state.get("quantified_forecast", {}) if is_market else {},
        "context_sentiment": state.get("context_sentiment", {}),
        "political_insights": state.get("political_insights", {}),
        "think_tank_insights": state.get("think_tank_insights", {}),
        "policy_impact": state.get("policy_impact_forecast", {}),
        "scenario_probabilities": state.get("scenario_probabilities", []),
        "political_risk_score": state.get("political_risk_score", 0.0),
        "evidence_summary_en": state.get("evidence_summary", ""),
        "evidence_summary_ar": state.get("evidence_summary_ar", ""),
        "evidence_claims": state.get("evidence_claims", []),
        "evidence_confidence": state.get("evidence_confidence", 0.0),
        "evidence_contradictions_en": state.get("evidence_contradictions", []),
        "evidence_contradictions_ar": state.get("evidence_contradictions_ar", []),
        "evidence_unknowns_en": state.get("evidence_unknowns", []),
        "evidence_unknowns_ar": state.get("evidence_unknowns_ar", []),
        "weak_signals": state.get("weak_signals", []),
        "walled_garden_query": state.get("walled_garden_query", ""),
        "walled_garden_answer": state.get("walled_garden_answer", ""),
        "research_snippets": _format_snippets(state.get("walled_garden_results", [])),
        "sources": state.get("walled_garden_sources", []),
    }


def _build_sources_section(state: ForecastState, text_mode: bool = False) -> str:
    lines = ["SOURCES" if text_mode else "## Sources"]
    snippets = _format_snippets(state.get("walled_garden_results", []))
    if snippets:
        for item in snippets:
            title = item.get("title") or "Untitled"
            url = item.get("url") or ""
            lines.append(f"[{item['id']}] {title} - {url}")
    else:
        lines.append("No trusted sources returned for this query.")

    think_tank_sources = state.get("think_tank_sources", [])
    if think_tank_sources:
        lines.append("")
        lines.append("Think tank sources: " + ", ".join(think_tank_sources))

    if text_mode:
        lines.insert(1, "-" * 8)
    return "\n".join(lines)


def _build_evidence_table(state: ForecastState, text_mode: bool = False) -> str:
    heading = "EVIDENCE TABLE" if text_mode else "## Evidence Table"
    arabic_heading = "جدول الأدلة"
    lines = [heading, arabic_heading]
    if text_mode:
        lines.append("-" * 15)

    snippets = _format_snippets(state.get("walled_garden_results", []))
    if not snippets:
        lines.append("No trusted sources returned for this query.")
        lines.append("لا توجد مصادر موثوقة لهذه الاستعلام.")
        return "\n".join(lines)

    for item in snippets:
        title = item.get("title") or "Untitled"
        url = item.get("url") or ""
        snippet = item.get("snippet") or ""
        lines.append(f"[{item['id']}] {title}")
        lines.append(f"URL: {url}")
        if snippet:
            lines.append(f"Snippet: {snippet}")
        lines.append("")

    return "\n".join(lines).strip()


def _build_justification_section(state: ForecastState, text_mode: bool = False) -> str:
    heading = "EVIDENCE ASSESSMENT" if text_mode else "## Evidence Assessment"
    arabic_heading = "تقييم الأدلة"
    lines = [heading, arabic_heading]
    if text_mode:
        lines.append("-" * 19)

    summary_en = state.get("evidence_summary") or "Evidence summary unavailable."
    summary_ar = state.get("evidence_summary_ar") or "ملخص الأدلة غير متوفر."
    lines.append(f"Summary (EN): {summary_en}")
    lines.append(f"Summary (AR): {summary_ar}")

    confidence = state.get("evidence_confidence")
    if confidence is not None:
        lines.append(f"Confidence: {confidence}")

    contradictions_en = state.get("evidence_contradictions", [])
    contradictions_ar = state.get("evidence_contradictions_ar", [])
    if contradictions_en:
        lines.append("Contradictions (EN): " + "; ".join(contradictions_en))
    if contradictions_ar:
        lines.append("Contradictions (AR): " + "; ".join(contradictions_ar))

    unknowns_en = state.get("evidence_unknowns", [])
    unknowns_ar = state.get("evidence_unknowns_ar", [])
    if unknowns_en:
        lines.append("Unknowns (EN): " + "; ".join(unknowns_en))
    if unknowns_ar:
        lines.append("Unknowns (AR): " + "; ".join(unknowns_ar))

    claims = state.get("evidence_claims", [])
    if claims:
        lines.append("")
        lines.append("Key Claims:")
        for claim in claims[:6]:
            claim_en = claim.get("claim_en") or claim.get("claim") or ""
            claim_ar = claim.get("claim_ar") or ""
            support = claim.get("supporting_sources", [])
            contradict = claim.get("contradicting_sources", [])
            line = f"- {claim_en}"
            if support:
                line += f" (support: {support})"
            if contradict:
                line += f" (contradict: {contradict})"
            lines.append(line)
            if claim_ar:
                lines.append(f"  • {claim_ar}")

    return "\n".join(lines)
def _build_indicators_section(state: ForecastState, text_mode: bool = False) -> str:
    heading = "PREDICTION INDICATORS" if text_mode else "## Prediction Indicators"
    arabic_heading = "مؤشرات التنبؤ"
    lines = [heading, arabic_heading]
    if text_mode:
        lines.append("-" * 22)

    temporal = state.get("temporal_forecast", {})
    quantified = state.get("quantified_forecast", {})
    context = state.get("context_sentiment", {})
    risk_score = state.get("political_risk_score", 0.0)
    risk_confidence = state.get("political_risk_confidence", 0.0)
    volatility_factor = state.get("volatility_factor", 1.0)

    def line(label: str, value: Any) -> None:
        lines.append(f"{label}: {value}")

    line("Metric", temporal.get("metric", "N/A"))
    line("Trend direction", temporal.get("trend_direction", "N/A"))
    line("Current value", temporal.get("current_value", "N/A"))
    line("Forecast 30d", temporal.get("forecast_30d", "N/A"))
    line("Forecast 90d", temporal.get("forecast_90d", "N/A"))
    line("Confidence 30d", temporal.get("confidence_30d", "N/A"))
    line("Confidence 90d", temporal.get("confidence_90d", "N/A"))
    line("Model type", temporal.get("model_type", "N/A"))
    line("Data points", temporal.get("data_points", "N/A"))
    line("Volatility", temporal.get("volatility", "N/A"))

    drivers = temporal.get("drivers", [])
    if drivers:
        line("Drivers", "; ".join(drivers))

    line("Final forecast", quantified.get("final_forecast", "N/A"))
    line("Final confidence", quantified.get("final_confidence", "N/A"))
    line("Sentiment adjustment", quantified.get("sentiment_adjustment", "N/A"))
    line("Risk weight", quantified.get("risk_weight", "N/A"))
    line("Volatility factor", volatility_factor)
    line("Adjustment rationale", quantified.get("adjustment_rationale", "N/A"))

    line("Context sentiment", context.get("sentiment_score", "N/A"))
    line("Narrative momentum", context.get("narrative_momentum", "N/A"))
    line("Mentions (24h)", context.get("mentions_24h", "N/A"))

    if risk_score:
        line("Political risk score", risk_score)
        line("Political risk confidence", risk_confidence)

    scenarios = state.get("scenario_probabilities", []) or []
    if scenarios:
        top = max(scenarios, key=lambda s: s.get("probability", 0.0))
        line(
            "Top scenario",
            f"{top.get('scenario', 'baseline')} ({top.get('probability', 0.0):.0%})",
        )

    return "\n".join(lines)


def _fallback_report(state: ForecastState, text_mode: bool = False) -> str:
    scenario = state.get("scenario", "Unknown scenario")
    summary = state.get("executive_summary", "")
    recommendation = state.get("strategic_recommendation", "")
    walled_answer = state.get("walled_garden_answer", "")
    temporal = state.get("temporal_forecast", {})
    quantified = state.get("quantified_forecast", {})

    heading_exec = "EXECUTIVE SUMMARY" if text_mode else "## Executive Summary"
    heading_research = "RESEARCH FINDINGS" if text_mode else "## Research Findings"
    heading_outlook = "FORECAST OUTLOOK" if text_mode else "## Forecast Outlook"
    heading_recommendations = "RECOMMENDATIONS" if text_mode else "## Recommendations"

    arabic_exec = "الملخص التنفيذي"
    arabic_research = "نتائج البحث"
    arabic_outlook = "توقعات السيناريو"
    arabic_recommendations = "التوصيات"

    separators = []
    if text_mode:
        separators = ["-" * 18, "-" * 17, "-" * 15, "-" * 14]

    lines = [
        heading_exec,
        arabic_exec,
        separators[0] if separators else "",
        summary or "No executive summary generated.",
        "لا تتوفر ترجمة عربية تلقائية في وضع الطوارئ.",
        "",
        heading_research,
        arabic_research,
        separators[1] if separators else "",
        walled_answer or "No trusted-source findings available.",
        "لا تتوفر ترجمة عربية تلقائية في وضع الطوارئ.",
        "",
    ]

    if state.get("scenario_is_market") is not False:
        lines.extend(
            [
                heading_outlook,
                arabic_outlook,
                separators[2] if separators else "",
                f"Metric: {temporal.get('metric', 'N/A')}",
                f"Current: {temporal.get('current_value', 'N/A')}",
                f"30-day forecast: {quantified.get('final_forecast', 'N/A')}",
                f"Confidence: {quantified.get('final_confidence', 'N/A')}",
                "لا تتوفر ترجمة عربية تلقائية في وضع الطوارئ.",
                "",
            ]
        )

    lines.extend(
        [
            heading_recommendations,
            arabic_recommendations,
            separators[3] if separators else "",
            recommendation or "No recommendation available.",
            "لا تتوفر ترجمة عربية تلقائية في وضع الطوارئ.",
        ]
    )

    return "\n".join(lines)


class ReportWriter:
    """
    Agent that writes a Markdown report based on search and LLM analysis outputs.
    """

    def __init__(self):
        self.enabled = settings.REPORT_WRITER_ENABLED
        self.format = settings.REPORT_FORMAT
        self.pdf_enabled = settings.REPORT_PDF_ENABLED

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        if not self.enabled:
            logger.warning("Report Writer is disabled")
            return state

        scenario = state.get("scenario", "")
        if not scenario:
            state["report_error"] = "Missing scenario"
            state["warnings"].append("Report Writer: Missing scenario")
            return state

        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            slug = _safe_slug(scenario)
            reports_dir = _reports_dir()
            reports_dir.mkdir(parents=True, exist_ok=True)
            format_value = (self.format or "").lower()
            text_mode = format_value in ("txt", "text", "plain", "plaintext")
            extension = "md" if format_value in ("markdown", "md") else format_value
            extension = extension or ("txt" if text_mode else "md")
            filename = f"{timestamp}_{slug}.{extension}"
            report_path = reports_dir / filename

            payload = _build_report_payload(state)
            is_market = state.get("scenario_is_market", True)
            report_style = "Decision Brief"
            
            # Decision-Grade Structure
            sections = (
                "1. Executive Summary (MUST be first. Bullets only. State decision, probability, confidence.)\n"
                "2. Situation Assessment (Facts vs Interpretation)\n"
                "3. Forecast Analysis (Scenarios, Drivers, Constraints)\n"
                "4. Key Risks & Uncertainties (Known Unknowns, Falsification Criteria)\n"
                "5. Strategic Implications (What to watch next)"
            )

            prompt = (
                f"Write a strategic {report_style} based ONLY on the data below. "
                f"Strictly follow this structure:\n{sections}\n\n"
                "**Requirements:**\n"
                "- **Tone:** Direct, neutral, authoritative (Intelligence Community style). No fluff.\n"
                "- **Executive Summary:** This section is MANDATORY and must be at the very top. Answer the user question directly.\n"
                "- **Fact vs Interpretation:** Clear distinction between confirmed evidence and analytical leaps.\n"
                "- **Citations:** Use inline citations [Source Name, Year] for every factual claim.\n"
                "- **Uncertainty:** Be explicit about what we do NOT know.\n"
                "- **Bilingual Output:** Provide the FULL brief in English, then the FULL brief in Arabic.\n\n"
                f"Data:\n{json.dumps(payload, ensure_ascii=True, indent=2, default=str)}"
            )

            system_prompt = (
                "You are an elite Intelligence Analyst. You produce decision-grade intelligence briefs. "
                "Your priority is correctness, conciseness, and falsifiability. "
                "Never hedge without cause. State probabilities clearly."
            )

            body = await llm_manager.complete(
                prompt,
                system_prompt=system_prompt,
                temperature=0.1, # Lowest temp for precision
                max_tokens=3000,
            )

            if not body:
                body = _fallback_report(state, text_mode=text_mode)

            if text_mode:
                header_lines = [
                    "INTELLIGENCE BRIEF",
                    "==================",
                    f"Subject: {scenario}",
                    f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}",
                    "Classification: UNCLASSIFIED",
                    "",
                ]
            else:
                header_lines = [
                    f"# Intelligence Brief: {scenario}",
                    f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d')} | **Status:** Final",
                    "---",
                    "",
                ]

            header = "\n".join(header_lines)
            
            # For doctoral reports, we might not need separate appended sections if the LLM does it well,
            # but let's keep the raw evidence table as an Appendix.
            
            report_content = [header, body.strip(), "", "## Appendix A: Quantitative Indicators"]
            
            if is_market:
                indicators = _build_indicators_section(state, text_mode=text_mode)
                report_content.extend([indicators, ""])

            report_content.append("## Appendix B: Primary Source Data")
            evidence_table = _build_evidence_table(state, text_mode=text_mode)
            report_content.extend([evidence_table, ""])

            report_text = "\n".join(report_content)
            report_path.write_text(report_text, encoding="utf-8")

            state["report_path"] = str(report_path)
            state["report_filename"] = filename
            state["report_format"] = self.format
            state["report_error"] = None
            state["agents_executed"].append("report_writer")

            logger.info("Report written to %s", report_path)

            pdf_filename = None
            if self.pdf_enabled:
                try:
                    generated_filename = f"{timestamp}_{slug}.pdf"
                    pdf_path = reports_dir / generated_filename
                    _write_pdf(report_text, pdf_path)
                    pdf_filename = generated_filename # Only set if successful
                except Exception as exc:
                    logger.warning("PDF report generation failed: %s", str(exc))
                    state["warnings"].append(f"Report PDF generation failed: {str(exc)}")

            state["report_pdf_filename"] = pdf_filename

        except Exception as exc:
            logger.error("Report Writer error: %s", str(exc))
            state["report_error"] = str(exc)
            state["errors"].append(f"Report Writer: {str(exc)}")

        return state


report_writer = ReportWriter()
