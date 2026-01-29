"""
Unified News Client handling multiple providers (NewsAPI, GNews).
"""

import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)

class NewsClient:
    """Aggregates news from enabled providers (NewsAPI, GNews)."""
    
    def __init__(self):
        self.newsapi_key = settings.NEWSAPI_KEY
        self.newsapi_base = settings.NEWSAPI_BASE_URL
        
        self.gnews_key = settings.GNEWS_API_KEY
        self.gnews_base = settings.GNEWS_BASE_URL
        
        if not self.newsapi_key:
            logger.warning("NewsAPI not configured")
        if not self.gnews_key:
            logger.warning("GNews not configured")

    async def get_news(
        self, 
        query: str, 
        limit: int = 10,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Fetch news from all available sources and merge."""
        
        results = []
        
        # 1. Fetch from NewsAPI
        if self.newsapi_key:
            try:
                newsapi_results = await self._fetch_newsapi(query, limit, days_back)
                results.extend(newsapi_results)
            except Exception as e:
                logger.error(f"NewsAPI error: {str(e)}")
                
        # 2. Fetch from GNews
        if self.gnews_key:
            try:
                # Adjust limit to balance sources if needed, or fetch full limit
                gnews_results = await self._fetch_gnews(query, limit, days_back)
                results.extend(gnews_results)
            except Exception as e:
                logger.error(f"GNews error: {str(e)}")
        
        # Deduplicate by title
        seen_titles = set()
        unique_results = []
        for r in results:
            if r["title"] not in seen_titles:
                seen_titles.add(r["title"])
                unique_results.append(r)
                
        # Sort by date (newest first)
        unique_results.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        return unique_results[:limit]

    async def _fetch_newsapi(self, query: str, limit: int, days_back: int) -> List[Dict[str, Any]]:
        """Fetch from NewsAPI.org"""
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        params = {
            "apiKey": self.newsapi_key,
            "q": query,
            "from": from_date,
            "sortBy": "relevancy",
            "language": "en",
            "pageSize": limit
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.newsapi_base}/everything", params=params)
            
        if resp.status_code != 200:
            logger.error(f"NewsAPI request failed: {resp.text}")
            return []
            
        data = resp.json()
        articles = data.get("articles", [])
        
        normalized = []
        for a in articles:
            normalized.append({
                "title": a.get("title"),
                "description": a.get("description"),
                "url": a.get("url"),
                "source": f"NewsAPI/{a.get('source', {}).get('name')}",
                "published_at": a.get("publishedAt")
            })
        return normalized

    async def _fetch_gnews(self, query: str, limit: int, days_back: int) -> List[Dict[str, Any]]:
        """Fetch from GNews.io"""
        # GNews uses 'from' in simplified format or just checks recent
        
        params = {
            "apikey": self.gnews_key,
            "q": query,
            "lang": "en",
            "max": limit,
            "sortby": "relevance"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.gnews_base}/search", params=params)
            
        if resp.status_code != 200:
            logger.error(f"GNews request failed: {resp.text}")
            return []
            
        data = resp.json()
        articles = data.get("articles", [])
        
        normalized = []
        for a in articles:
            normalized.append({
                "title": a.get("title"),
                "description": a.get("description"),
                "url": a.get("url"),
                "source": f"GNews/{a.get('source', {}).get('name')}",
                "published_at": a.get("publishedAt")
            })
        return normalized
