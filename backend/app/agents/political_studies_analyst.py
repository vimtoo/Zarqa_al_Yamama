"""
Political Studies Analyst
Aggregates political event data and produces narrative briefs.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from app.config import settings
from app.graph.state import ForecastState
from app.graph.contracts import ConflictMetrics
from app.llm.client import llm_manager
from app.agents.context_interpreter import NewsDataClient, GDELTClient
from app.agents.political_utils import extract_topics, extract_regions
from app.data_sources.acled_client import ACLEDClient
from app.data_sources.legislation_client import LegislationClient

logger = logging.getLogger(__name__)


class PoliticalStudiesAnalyst:
    """
    Agent responsible for political studies: narrative briefs, actors, themes,
    and event summaries from multiple political data sources.
    """

    def __init__(self):
        self.enabled = settings.POLITICAL_STUDIES_ANALYST_ENABLED
        self.newsdata_enabled = settings.NEWSDATA_ENABLED
        self.gdelt_enabled = settings.GDELT_ENABLED
        self.acled_enabled = settings.ACLED_ENABLED
        self.legislation_enabled = settings.LEGISLATION_ENABLED

        self.newsdata = NewsDataClient() if self.newsdata_enabled else None
        self.gdelt = GDELTClient() if self.gdelt_enabled else None
        self.acled = ACLEDClient() if self.acled_enabled else None
        self.legislation = LegislationClient() if self.legislation_enabled else None

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        """Run political studies analysis."""
        if not self.enabled:
            logger.warning("Political Studies Analyst is disabled")
            return state

        scenario = state.get("scenario", "")
        logger.info("Political Studies Analyst starting for scenario: %s", scenario)

        try:
            query = scenario or "geopolitical risk"

            tasks = []
            task_keys = []

            if self.newsdata_enabled and self.newsdata:
                tasks.append(self.newsdata.get_world_news(query))
                task_keys.append("news")
            if self.gdelt_enabled and self.gdelt:
                tasks.append(self.gdelt.search_docs(query=query, max_records=25, timespan="7d"))
                task_keys.append("gdelt")
            if self.acled_enabled and self.acled:
                tasks.append(self.acled.get_recent_events(query=query, days=30, limit=50))
                task_keys.append("acled")
            if self.legislation_enabled and self.legislation:
                tasks.append(self.legislation.get_recent_legislation(query=query, limit=15))
                task_keys.append("legislation")

            results = await asyncio.gather(*tasks, return_exceptions=True) if tasks else []
            news_items, gdelt_items, acled_events, legislation_items = [], [], [], []

            for key, result in zip(task_keys, results):
                if isinstance(result, Exception):
                    continue
                if key == "news":
                    news_items = result or []
                elif key == "gdelt":
                    gdelt_items = result or []
                elif key == "acled":
                    acled_events = result or []
                elif key == "legislation":
                    legislation_items = result or []

            summary_text = self._build_summary_text(
                scenario,
                news_items,
                gdelt_items,
                acled_events,
                legislation_items
            )

            topics = extract_topics(summary_text) or extract_topics(scenario)
            regions = extract_regions(summary_text) or extract_regions(scenario)

            data_sources = []
            if news_items:
                data_sources.append("NewsData.io")
            if gdelt_items:
                data_sources.append("GDELT")
            if acled_events:
                data_sources.append("ACLED")
            if legislation_items:
                data_sources.append("Legislative Records")

            llm_analysis = await self._llm_brief(summary_text, scenario)
            narrative_brief = llm_analysis.get("narrative_brief") if llm_analysis else None
            key_actors = llm_analysis.get("key_actors") if llm_analysis else None

            if isinstance(key_actors, str):
                key_actors = [key_actors]
            if key_actors and not isinstance(key_actors, list):
                key_actors = None

            if llm_analysis and llm_analysis.get("themes") and isinstance(llm_analysis["themes"], list):
                topics = llm_analysis["themes"]

            if not narrative_brief:
                narrative_brief = (
                    f"Scenario '{scenario}' shows {len(news_items)} news items, "
                    f"{len(gdelt_items)} GDELT articles, {len(acled_events)} ACLED events, "
                    f"and {len(legislation_items)} legislative updates. "
                    f"Dominant topics: {', '.join(topics[:3]) if topics else 'mixed signals'}."
                )

            if not key_actors:
                key_actors = state.get("context_key_actors", [])

            political_insights = {
                "narrative_brief": narrative_brief,
                "key_actors": key_actors,
                "topics": topics,
                "regions": regions,
                "event_counts": {
                    "news": len(news_items),
                    "gdelt": len(gdelt_items),
                    "acled": len(acled_events),
                    "legislation": len(legislation_items)
                },
                "sample_headlines": [
                    item.get("title") for item in (news_items[:3] if news_items else [])
                ],
                "timestamp": datetime.utcnow().isoformat()
            }

            state["political_insights"] = political_insights
            state["narrative_brief"] = narrative_brief
            state["political_key_actors"] = key_actors
            state["political_themes"] = topics
            state["political_regions"] = regions
            state["political_data_sources"] = data_sources
            state["political_error"] = None

            # Phase 3: Conflict Metrics Extraction
            if scenario:
                state["conflict_metrics"] = await self._extract_conflict_metrics(summary_text, scenario)

            state["agents_executed"].append("political_studies_analyst")

            logger.info(
                "Political Studies Analyst completed with %d sources",
                len(data_sources)
            )

        except Exception as exc:
            logger.error("Political Studies Analyst error: %s", str(exc))
            state["political_error"] = str(exc)
            state["errors"].append(f"Political Studies Analyst: {str(exc)}")

        return state

    def _build_summary_text(
        self,
        scenario: str,
        news_items: List[Dict[str, Any]],
        gdelt_items: List[Dict[str, Any]],
        acled_events: List[Dict[str, Any]],
        legislation_items: List[Dict[str, Any]]
    ) -> str:
        """Build a summary text for LLM analysis and keyword extraction."""
        parts = [scenario]

        for item in news_items[:5]:
            title = item.get("title") or ""
            description = item.get("description") or ""
            parts.append(f"{title}. {description}")

        for item in gdelt_items[:5]:
            title = item.get("title") or ""
            source = item.get("sourceCountry") or ""
            parts.append(f"{title} ({source})")

        for event in acled_events[:5]:
            event_type = event.get("event_type") or "event"
            notes = event.get("notes") or ""
            parts.append(f"{event_type}: {notes}")

        for item in legislation_items[:5]:
            title = item.get("title") or "legislation"
            summary = item.get("summary") or ""
            parts.append(f"{title}: {summary}")

        return " ".join(part for part in parts if part)

    async def _llm_brief(self, summary_text: str, scenario: str) -> Dict[str, Any]:
        """Get structured political brief from LLM."""
        try:
            analysis = await llm_manager.analyze(
                data={
                    "scenario": scenario,
                    "summary": summary_text[:2000]
                },
                analysis_type="political_studies",
                context=f"Political studies brief for: {scenario}"
            )
            return analysis if isinstance(analysis, dict) else {}
        except Exception as exc:
            logger.warning("LLM political brief failed: %s", str(exc))
            return {}

    async def _extract_conflict_metrics(self, summary_text: str, scenario: str) -> Optional[ConflictMetrics]:
        """Extract structured conflict metrics using LLM."""
        try:
            # Use Antigravity via LLMManager
            data = await llm_manager.analyze(
                data={"summary_text": summary_text[:3000], "context": scenario},
                analysis_type="conflict_metrics",
                role="conflict_metrics_v1",
                context="Conflict metrics extraction"
            )
            
            return ConflictMetrics(**data)
            
        except Exception as e:
            logger.warning(f"Conflict metrics extraction failed: {e}")
            return None

political_studies_analyst = PoliticalStudiesAnalyst()
