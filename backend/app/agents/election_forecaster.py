"""
Election Forecaster
Produces election outlooks based on polling and fundamentals.
"""

import logging
from typing import Dict, Any

from app.config import settings
from app.graph.state import ForecastState
from app.data_sources.elections_client import ElectionsClient
from app.agents.political_utils import is_election_related

logger = logging.getLogger(__name__)


class ElectionForecaster:
    """Agent to forecast election outcomes."""

    def __init__(self):
        self.enabled = settings.ELECTION_FORECASTER_ENABLED
        self.client = ElectionsClient()

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        if not self.enabled:
            logger.warning("Election Forecaster is disabled")
            return state

        scenario = state.get("scenario", "")
        try:
            snapshot = await self.client.get_election_snapshot(query=scenario)
            status = snapshot.get("status", "modeled") if isinstance(snapshot, dict) else "modeled"

            if status == "not_applicable" and not is_election_related(scenario):
                state["election_outlook"] = {
                    "status": "not_applicable",
                    "summary": "Scenario does not reference an election or vote.",
                    "confidence": 0.2,
                    "races": []
                }
            else:
                races = snapshot.get("races", []) if isinstance(snapshot, dict) else []
                confidence = 0.45 + (0.15 if races else 0.0)
                data_source = "Elections Data Provider" if races else "Modeled"
                state["election_outlook"] = {
                    "status": status,
                    "summary": snapshot.get("summary", "Election outlook generated."),
                    "confidence": confidence,
                    "races": races,
                    "data_sources": [data_source]
                }
                state["political_data_sources"] = state.get("political_data_sources", []) + [data_source]

            state["agents_executed"].append("election_forecaster")
            logger.info("Election Forecaster completed")

        except Exception as exc:
            logger.error("Election Forecaster error: %s", str(exc))
            state["errors"].append(f"Election Forecaster: {str(exc)}")

        return state


election_forecaster = ElectionForecaster()
