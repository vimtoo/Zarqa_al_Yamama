"""
Legislative records client (bills, regulations, decrees).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import httpx

from app.config import settings
from app.agents.political_utils import extract_topics

logger = logging.getLogger(__name__)


class LegislationClient:
    """Client for Congress.gov API."""

    def __init__(self):
        self.api_key = settings.LEGISLATION_API_KEY
        self.base_url = settings.LEGISLATION_BASE_URL

        if not self.api_key:
            logger.warning("Legislation API (Congress.gov) not configured")

    async def get_recent_legislation(
        self,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch recent legislative items relevant to the query."""
        if not self.api_key:
            return self._fallback_legislation(query, limit)

        # Congress.gov API uses /bill endpoint. If query is provided, we might need a different approach
        # or filter. The v3 API is: https://api.congress.gov/v3/bill
        
        # Construct URL: https://api.congress.gov/v3/bill
        url = f"{self.base_url}/bill"
        
        params = {
            "api_key": self.api_key,
            "limit": limit,
            "format": "json"
        }
        
        # Make the request
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                bills = data.get("bills", [])
                
                # Normalize to our internal format
                results = []
                for bill in bills:
                    title = bill.get("title", "No Title")
                    congress = bill.get("congress", "")
                    bill_type = bill.get("type", "")
                    bill_number = bill.get("number", "")
                    
                    results.append({
                        "title": title,
                        "summary": f"Congress {congress}, {bill_type} {bill_number}. Update: {bill.get('updateDate')}",
                        "status": "active", # Simplified
                        "last_updated": bill.get("updateDate", datetime.utcnow().isoformat()),
                        "source": "congress.gov"
                    })
                
                # Simple client-side filtering if query provided (API search is separate/complex)
                if query:
                    q_lower = query.lower()
                    results = [r for r in results if q_lower in r["title"].lower() or q_lower in r["summary"].lower()]
                    
                return results[:limit]

            logger.warning(
                "Congress.gov API error: %s - %s",
                response.status_code,
                response.text
            )
            return self._fallback_legislation(query, limit)

        except Exception as exc:
            logger.warning("Legislation request error: %s", str(exc))
            return self._fallback_legislation(query, limit)

    def _fallback_legislation(
        self,
        query: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback legislative items derived from the scenario."""
        topics = extract_topics(query or "")
        topic = topics[0] if topics else "governance"

        items = [
            {
                "title": f"Fallback: Policy deliberations on {topic}",
                "summary": f"Legislative discussions regarding {topic} and associated reforms.",
                "status": "under_review",
                "last_updated": datetime.utcnow().isoformat(),
                "source": "simulation"
            },
            {
                "title": f"Fallback: Regulatory update affecting {topic}",
                "summary": f"Regulatory bodies propose adjustments impacting {topic} policy objectives.",
                "status": "draft",
                "last_updated": datetime.utcnow().isoformat(),
                "source": "simulation"
            }
        ]

        return items[:limit]
