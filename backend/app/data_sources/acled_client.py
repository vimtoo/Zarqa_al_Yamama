"""
ACLED API client (conflict and event data).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ACLEDClient:
    """Client for ACLED event data."""

    def __init__(self):
        self.api_key = settings.ACLED_API_KEY
        self.email = settings.ACLED_EMAIL
        self.base_url = settings.ACLED_BASE_URL

        if not self.api_key or not self.email:
            logger.warning("ACLED API key/email not configured")

    async def get_events(
        self,
        query: Optional[str] = None,
        country: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch ACLED events.

        Args:
            query: Free-text query terms.
            country: Country filter (if supported by API).
            start_date: Start date YYYY-MM-DD.
            end_date: End date YYYY-MM-DD.
            limit: Maximum number of records.
        """
        if not self.api_key or not self.email or not self.base_url:
            return []

        params: Dict[str, Any] = {
            "key": self.api_key,
            "email": self.email,
            "limit": limit
        }

        if query:
            params["terms"] = query
        if country:
            params["country"] = country

        if start_date and end_date:
            params["event_date"] = f"{start_date}|{end_date}"

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(self.base_url, params=params)

            if response.status_code == 200:
                data = response.json()
                return data.get("data", data.get("events", []))

            logger.warning(
                "ACLED API error: %s - %s",
                response.status_code,
                response.text
            )
            return []

        except Exception as exc:
            logger.warning("ACLED request error: %s", str(exc))
            return []

    async def get_recent_events(
        self,
        query: Optional[str] = None,
        country: Optional[str] = None,
        days: int = 30,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch recent ACLED events with a rolling window."""
        end = datetime.utcnow().date()
        start = end - timedelta(days=days)
        return await self.get_events(
            query=query,
            country=country,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            limit=limit
        )
