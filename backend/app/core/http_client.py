"""
Global HTTP Client Management
Provides a shared httpx.AsyncClient to avoid connection churn.
"""

import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

class GlobalHTTPClient:
    """Singleton wrapper for the global HTTP client"""
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """Get the shared client instance. Creates one if it doesn't exist (lazy load fallback)."""
        if cls._client is None or cls._client.is_closed:
            logger.warning("GlobalHTTPClient accessed before explicit initialization or was closed. creating new instance.")
            # Default configuration for lazy initialization
            cls._client = httpx.AsyncClient(
                timeout=300.0,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return cls._client

    @classmethod
    async def start(cls):
        """Initialize the global client on startup"""
        if cls._client is None or cls._client.is_closed:
            logger.info("Initializing Global HTTP Client")
            cls._client = httpx.AsyncClient(
                timeout=300.0,
                limits=httpx.Limits(max_keepalive_connections=50, max_connections=200),
                follow_redirects=True
            )

    @classmethod
    async def stop(cls):
        """Close the global client on shutdown"""
        if cls._client:
            logger.info("Closing Global HTTP Client")
            await cls._client.aclose()
            cls._client = None
