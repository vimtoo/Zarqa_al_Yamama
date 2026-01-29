import logging
import time
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse
from datetime import datetime
import hashlib
import re

from app.config import settings


logger = logging.getLogger(__name__)


class Librarian:
    """
    The Librarian: Centralized Retrieval Governance System.
    
    Responsibilities:
    1. Enforce Domain Allowlist (Strict Mode).
    2. Rate Limiting (Token Bucket).
    3. Caching (Simple in-memory for now, extensible to Redis).
    4. Audit Logging of all external access.
    5. V2: Return structured EvidenceItem with full provenance.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Librarian, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.enabled = settings.LIBRARIAN_ENABLED
        self.strict_mode = settings.LIBRARIAN_STRICT_MODE
        # Parse allowlist
        raw_list = settings.SOURCE_ALLOWLIST.split(",")
        self.allowlist = [d.strip().lower() for d in raw_list if d.strip()]
        
        # Simple in-memory cache: {url: {"content": ..., "timestamp": ..., "content_hash": ...}}
        self._cache: Dict[str, Dict] = {}
        self._cache_ttl = settings.LIBRARIAN_CACHE_TTL_HOURS * 3600
        
        # Rate Limiting state
        self._request_timestamps = []
        self._limit_per_minute = settings.LIBRARIAN_RATE_LIMIT_PER_MINUTE
        
        # Lazy import to avoid circular dependency
        self._deduper = None
    
    def _get_deduper(self):
        """Lazy load evidence deduper to avoid circular imports."""
        if self._deduper is None:
            from app.retrieval.evidence_deduper import evidence_deduper
            self._deduper = evidence_deduper
        return self._deduper
    
    def is_allowed(self, url: str) -> bool:
        """Check if URL domain is in the allowlist."""
        if not self.strict_mode:
            return True
            
        try:
            domain = urlparse(url).netloc.lower()
            # Handle subdomains (e.g., api.bloomberg.com -> bloomberg.com)
            for allowed in self.allowlist:
                if domain == allowed or domain.endswith("." + allowed):
                    return True
            return False
        except Exception as e:
            logger.error(f"Librarian: Failed to parse URL {url}: {e}")
            return False

    def check_rate_limit(self) -> bool:
        """Return True if request is allowed, False if limited."""
        now = time.time()
        # Remove timestamps older than 1 minute
        self._request_timestamps = [t for t in self._request_timestamps if now - t < 60]
        
        if len(self._request_timestamps) < self._limit_per_minute:
            self._request_timestamps.append(now)
            return True
        return False

    def get_cached(self, url: str) -> Optional[Dict]:
        """Retrieve cached entry if valid."""
        if url in self._cache:
            entry = self._cache[url]
            age = time.time() - entry['timestamp']
            if age < self._cache_ttl:
                logger.info(f"Librarian: Cache HIT for {url}")
                return entry
            else:
                del self._cache[url]  # Expired
        return None

    def cache_content(self, url: str, content: str, content_hash: str):
        """Store content in cache with hash."""
        self._cache[url] = {
            "content": content,
            "timestamp": time.time(),
            "content_hash": content_hash
        }

    def clean_content(self, content: str) -> str:
        """Strip scripts, styles, and extra whitespace."""
        # Remove script and style tags
        cleaned = re.sub(r'<(script|style).*?</\1>', '', content, flags=re.DOTALL)
        # Remove HTML tags (keep text) - simplistic approach
        cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
        # Normalize whitespace
        cleaned = " ".join(cleaned.split())
        return cleaned

    def hash_content(self, content: str) -> str:
        """Generate SHA-256 hash of content for audit."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    async def fetch(self, url: str, fetch_function, **kwargs) -> Optional[str]:
        """
        Governance Wrapper for fetching content.
        
        Args:
            url: The URL to fetch.
            fetch_function: The async function to call (e.g., httpx.get or browser tool).
            **kwargs: Arguments for the fetch_function.
            
        Returns:
            Content string or None if blocked/failed.
        """
        # 1. Check Allowlist
        if not self.is_allowed(url):
            logger.warning(f"Librarian: BLOCKED access to {url} (Allowlist Policy)")
            return None
            
        # 2. Check Cache
        cached = self.get_cached(url)
        if cached:
            return cached['content']
            
        # 3. Check Rate Limit
        if not self.check_rate_limit():
            logger.warning(f"Librarian: BLOCKED access to {url} (Rate Limit Exceeded)")
            return None
            
        # 4. Execute Fetch
        try:
            logger.info(f"Librarian: Allowing access to {url}")
            content = await fetch_function(url, **kwargs)
            
            if content:
                # Clean and Hash
                content = self.clean_content(content)
                audit_hash = self.hash_content(content)
                logger.info(f"Librarian: Fetched and cleaned {len(content)} chars from {url} (Hash: {audit_hash})")
                
                # 5. Cache Result
                self.cache_content(url, content, audit_hash)
                
            return content
        except Exception as e:
            logger.error(f"Librarian: Fetch error for {url}: {e}")
            return None

    async def fetch_with_evidence(
        self, 
        url: str, 
        fetch_function,
        snippet_extractor=None,
        published_at: Optional[datetime] = None,
        publisher: Optional[str] = None,
        source_type: Optional[str] = None,
        **kwargs
    ) -> Tuple[Optional[str], Optional['EvidenceItem']]:
        """
        Fetch content and return structured EvidenceItem (V2).
        
        Args:
            url: The URL to fetch.
            fetch_function: The async function to call.
            snippet_extractor: Optional function to extract relevant snippet from content.
            published_at: Optional publication timestamp.
            publisher: Optional publisher name.
            source_type: Optional source type string.
            **kwargs: Arguments for the fetch_function.
            
        Returns:
            Tuple of (content, EvidenceItem) or (None, None) if blocked/failed.
        """
        from app.graph.contracts import EvidenceItem, SourceType
        
        # 1. Check Allowlist
        if not self.is_allowed(url):
            logger.warning(f"Librarian: BLOCKED access to {url} (Allowlist Policy)")
            return None, None
        
        # 2. Check Cache
        cached = self.get_cached(url)
        deduper = self._get_deduper()
        
        if cached:
            content = cached['content']
            content_hash = cached['content_hash']
        else:
            # 3. Check Rate Limit
            if not self.check_rate_limit():
                logger.warning(f"Librarian: BLOCKED access to {url} (Rate Limit Exceeded)")
                return None, None
            
            # 4. Execute Fetch
            try:
                logger.info(f"Librarian: Allowing access to {url}")
                raw_content = await fetch_function(url, **kwargs)
                
                if not raw_content:
                    return None, None
                
                # Clean and Hash
                content = self.clean_content(raw_content)
                content_hash = self.hash_content(content)
                logger.info(f"Librarian: Fetched and cleaned {len(content)} chars from {url} (Hash: {content_hash})")
                
                # 5. Cache Result
                self.cache_content(url, content, content_hash)
                
            except Exception as e:
                logger.error(f"Librarian: Fetch error for {url}: {e}")
                return None, None
        
        # 6. Extract snippet
        if snippet_extractor:
            try:
                snippet = snippet_extractor(content)
            except Exception as e:
                logger.warning(f"Snippet extraction failed: {e}")
                snippet = content[:500]
        else:
            snippet = content[:500]
        
        # 7. Determine source type
        if source_type:
            try:
                src_type = SourceType(source_type)
            except ValueError:
                src_type = SourceType.AGGREGATOR
        else:
            src_type = SourceType.AGGREGATOR
        
        # 8. Create EvidenceItem via deduper
        evidence = deduper.process_evidence(
            raw_url=url,
            content=content,
            snippet=snippet,
            published_at=published_at,
            publisher=publisher,
            source_type=src_type
        )
        
        return content, evidence


# Singleton instance
librarian = Librarian()

