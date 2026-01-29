"""
Elections data client (polls, results, and schedules).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import httpx

from app.config import settings
from app.agents.political_utils import is_election_related

logger = logging.getLogger(__name__)


class ElectionsClient:
    """Client for election data providers."""

    def __init__(self):
        self.api_key = settings.ELECTIONS_API_KEY
        self.base_url = settings.ELECTIONS_BASE_URL

        if not self.api_key or not self.base_url:
            logger.warning("Elections API not configured")

    async def get_election_snapshot(
        self,
        query: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Fetch election snapshot for a scenario.

        Returns a dict with a `races` list if data is available.
        """
        if not self.api_key or not self.base_url:
            return self._fallback_snapshot(query)

        params = {
            "api_key": self.api_key,
            "q": query or "election",
            "limit": limit
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(self.base_url, params=params)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return data

            logger.warning(
                "Elections API error: %s - %s",
                response.status_code,
                response.text
            )
            return self._fallback_snapshot(query)

        except Exception as exc:
            logger.warning("Elections request error: %s", str(exc))
            return self._fallback_snapshot(query)

    def _fallback_snapshot(self, query: Optional[str]) -> Dict[str, Any]:
        """Fallback snapshot when no external elections data is available."""
        if query and not is_election_related(query):
            return {
                "status": "not_applicable",
                "races": [],
                "summary": "No election-related signals detected.",
                "last_updated": datetime.utcnow().isoformat()
            }

        return {
            "status": "modeled",
            "races": [
                {
                    "race": "Generic National Election",
                    "candidates": [
                        {"name": "Incumbent", "probability": 0.55},
                        {"name": "Challenger", "probability": 0.45}
                    ],
                    "key_factors": [
                        "Incumbency advantage",
                        "Economic sentiment",
                        "Security conditions"
                    ]
                }
            ],
            "summary": "Fallback election outlook based on generic fundamentals.",
            "last_updated": datetime.utcnow().isoformat()
        }
