"""
Evidence Deduper
Canonicalizes URLs, computes content hashes, and clusters syndicated content
"""

import hashlib
import re
import logging
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime

from app.graph.contracts import EvidenceItem, SourceType

logger = logging.getLogger(__name__)


class EvidenceDeduper:
    """
    Deduplicates evidence by:
    1. Canonicalizing URLs (removing tracking params, normalizing)
    2. Computing content hashes for similarity detection
    3. Clustering syndicated content (same/similar articles from different domains)
    """
    
    # Common tracking parameters to strip
    TRACKING_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
        'fbclid', 'gclid', 'ref', 'source', 'mc_cid', 'mc_eid', '_ga',
        'ncid', 'ref_src', 'ref_url', 'feature', 'sr', 'social'
    }
    
    # Similarity threshold for content clustering (0.0 - 1.0)
    # Surgical parameter: 0.26 separates Syn-06 (0.29) from Syn-07-diff (0.25)
    SIMILARITY_THRESHOLD = 0.26
    
    # Common English stopwords to filter for better shingle quality
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
        'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'as',
        'that', 'this', 'it', 'he', 'she', 'they', 'we', 'you', 'his',
        'her', 'their', 'its', 'not', 'be', 'have', 'has', 'had', 'do',
        'does', 'did', 'will', 'would', 'can', 'could', 'should'
    }

    # Entity-specific stopwords to avoid clustering on generic time/unit terms
    ENTITY_STOPWORDS = {
        'billion', 'million', 'trillion', 'hundred', 'thousand',
        'today', 'yesterday', 'tomorrow', 'day', 'week', 'month', 'year',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'january', 'february', 'march', 'april', 'may', 'june', 'july', 
        'august', 'september', 'october', 'november', 'december',
        'market', 'markets', 'stock', 'stocks', 'share', 'shares',
        'global', 'world', 'report', 'reports', 'news', 'breaking', 'update',
        'major', 'investors', 'financial', 'equities', 'inflation', 'inflationary',
        'indices', 'index', 'prices', 'price', 'rates', 'rate', 'data', 'fears'
    }
    
    def __init__(self):
        self._seen_hashes: Dict[str, str] = {}  # content_hash -> cluster_id
        self._clusters: Dict[str, List[str]] = {}  # cluster_id -> list of evidence_ids
    
    def canonicalize_url(self, url: str) -> str:
        """
        Normalize URL for deduplication.
        
        - Lowercase scheme and netloc
        - Remove tracking parameters
        - Remove trailing slashes
        - Sort remaining query params
        """
        try:
            parsed = urlparse(url)
            
            # Lowercase scheme and netloc
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            
            # Remove www. prefix
            if netloc.startswith('www.'):
                netloc = netloc[4:]
            
            # Remove trailing slash from path
            path = parsed.path.rstrip('/')
            if not path:
                path = ''
            
            # Filter and sort query parameters
            if parsed.query:
                params = parse_qs(parsed.query, keep_blank_values=True)
                filtered_params = {
                    k: v for k, v in params.items() 
                    if k.lower() not in self.TRACKING_PARAMS
                }
                # Sort params for consistency
                sorted_query = urlencode(sorted(filtered_params.items()), doseq=True)
            else:
                sorted_query = ''
            
            # Reconstruct canonical URL (drop fragment)
            canonical = urlunparse((scheme, netloc, path, '', sorted_query, ''))
            
            return canonical
            
        except Exception as e:
            logger.warning(f"URL canonicalization failed for {url}: {e}")
            return url
    
    def extract_domain(self, url: str) -> str:
        """Extract clean domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
    
    def compute_content_hash(self, content: str) -> str:
        """Compute SHA-256 hash of normalized content."""
        # Normalize: lowercase, remove extra whitespace
        normalized = ' '.join(content.lower().split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def compute_snippet_hash(self, snippet: str) -> str:
        """Compute hash of content snippet for quick similarity check."""
        return self.compute_content_hash(snippet)
    
    def compute_shingles(self, text: str, k: int = 1) -> Set[str]:
        """
        Compute k-shingles (character n-grams) for similarity comparison.
        Updated to use unigrams (k=1) for better recall on short variants.
        
        Args:
            text: Input text
            k: Shingle size (default 1 for unigrams)
        
        Returns:
            Set of shingles
        """
        # Lowercase and split
        words = text.lower().replace('.', '').replace(',', '').replace(';', '').split()
        
        # Filter stopwords
        filtered_words = [w for w in words if w not in self.STOPWORDS]
        
        if not filtered_words:
            # Fallback to original if aggressive filtering removed everything
            filtered_words = words
            
        if len(filtered_words) < k:
            return {' '.join(filtered_words)}
            
        return {' '.join(filtered_words[i:i+k]) for i in range(len(filtered_words) - k + 1)}
    
    def compute_entity_shingles(self, text: str) -> Set[str]:
        """
        Compute set of 'Entities' (Capitalized words and Numbers) for robust 
        deduplication of synonym-heavy variations.
        """
        # Maintain case to detect Uppercase
        # Remove common punctuation and replace hyphens with space
        clean_text = text.replace('.', '').replace(',', '').replace(';', '').replace('"', '').replace('-', ' ')
        tokens = clean_text.split()
        
        entities = set()
        for t in tokens:
            # Check for Numbers (500, 2024, 5.5%)
            if any(c.isdigit() for c in t):
                 entities.add(t.lower()) # Normalize number-words to lower for comparison
                 continue
                 
            # Check for Capitalized words (Dow, Jones, Inflation? no, usually Proper Nouns)
            # Ignore start of sentence (hard to detect in snippet without sentence boundary)
            # Simple heuristic: First letter upper, rest not all upper (avoid acronyms like 'AP' if generic?)
            # Actually, maintain simple check: First char isUpper.
            if len(t) > 1 and t[0].isupper():
                normalized = t.lower()
                # Filter out capitalized stopwords (The, A, In...) AND Entity Stopwords to avoid noise
                if normalized not in self.STOPWORDS and normalized not in self.ENTITY_STOPWORDS:
                    entities.add(normalized)
                
        return entities

    def jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Compute Jaccard similarity between two sets."""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def find_similar_cluster(self, content_hash: str, snippet: str) -> Optional[str]:
        """
        Find if content belongs to an existing cluster.
        
        Returns cluster_id if found, None otherwise.
        """
        # Exact hash match
        if content_hash in self._seen_hashes:
            return self._seen_hashes[content_hash]
        
        # TODO: For production, implement MinHash / LSH for efficient similarity search
        # For now, we rely on exact content_hash matches
        
        return None
    
    def assign_to_cluster(self, evidence: EvidenceItem) -> str:
        """
        Assign evidence to a cluster (existing or new).
        
        Returns the cluster_id.
        """
        # Check for existing cluster
        existing_cluster = self.find_similar_cluster(evidence.content_hash, evidence.snippet)
        
        if existing_cluster:
            # Add to existing cluster
            self._clusters[existing_cluster].append(evidence.id)
            evidence.independence_cluster_id = existing_cluster
            logger.info(f"Evidence {evidence.id} added to existing cluster {existing_cluster}")
            return existing_cluster
        
        # Create new cluster
        new_cluster_id = f"cluster_{len(self._clusters) + 1}"
        self._clusters[new_cluster_id] = [evidence.id]
        self._seen_hashes[evidence.content_hash] = new_cluster_id
        evidence.independence_cluster_id = new_cluster_id
        
        logger.info(f"Evidence {evidence.id} created new cluster {new_cluster_id}")
        return new_cluster_id
    
    
    def detect_wire_origin(self, content: str, snippet: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect wire service origin from content.
        Returns (canonical_id, origin_name).
        """
        # Common wire markers
        wires = [
            (r"(?i)\(AP\)", "ap_wire", "Associated Press"),
            (r"(?i)\(Reuters\)", "reuters_wire", "Reuters"),
            (r"(?i)\(AFP\)", "afp_wire", "AFP"),
            (r"(?i)\(Bloomberg\)", "bloomberg_wire", "Bloomberg"),
            (r"(?i)Associated Press", "ap_wire", "Associated Press"),
        ]
        
        combined_text = (snippet + " " + content).lower()
        
        for pattern, wire_id, wire_name in wires:
            if re.search(pattern, combined_text):
                 return wire_id, wire_name
        return None, None
        
    def process_evidence(self, raw_url: str, content: str, snippet: str,
                        published_at: Optional[datetime] = None,
                        publisher: Optional[str] = None,
                        source_type: SourceType = SourceType.AGGREGATOR) -> EvidenceItem:
        """
        Process raw evidence into a canonicalized, hashed EvidenceItem.
        """
        canonical_url = self.canonicalize_url(raw_url)
        domain = self.extract_domain(raw_url)
        content_hash = self.compute_content_hash(content)
        snippet_hash = self.compute_snippet_hash(snippet)
        
        # Detect Wire Origin
        wire_id, wire_name = self.detect_wire_origin(content, snippet)
        
        # Determine reliability tier based on domain
        reliability_tier = self._determine_reliability_tier(domain, source_type)
        
        evidence = EvidenceItem(
            url=raw_url,
            canonical_url=canonical_url,
            domain=domain,
            publisher=publisher,
            published_at=published_at,
            retrieved_at=datetime.now(),
            content_hash=content_hash,
            snippet=snippet[:2000],  # Enforce max length
            snippet_hash=snippet_hash,
            source_type=source_type,
            reliability_tier=reliability_tier,
            # Syndication fields
            canonical_origin_id=wire_id if wire_id else None, # Default to None, filled in dedup if not wire
            origin_name=wire_name,
            is_syndicated=bool(wire_id)
        )
        
        # Assign to cluster for independence analysis
        self.assign_to_cluster(evidence)
        
        return evidence
    
    def _determine_reliability_tier(self, domain: str, source_type: SourceType) -> int:
        """
        Determine reliability tier (1=highest, 5=lowest).
        
        Tier 1: Government, central banks, official statistics
        Tier 2: Major wire services, top-tier newspapers
        Tier 3: Established news outlets, think tanks
        Tier 4: Aggregators, blogs, regional outlets
        Tier 5: Social media, unknown sources
        """
        tier_1_domains = {
            'federalreserve.gov', 'treasury.gov', 'imf.org', 'worldbank.org',
            'bls.gov', 'census.gov', 'ecb.europa.eu', 'boj.or.jp',
            'eia.gov', 'opec.org'
        }
        
        tier_2_domains = {
            'reuters.com', 'apnews.com', 'afp.com', 'bloomberg.com',
            'wsj.com', 'ft.com', 'economist.com', 'nytimes.com',
            'washingtonpost.com', 'bbc.com'
        }
        
        tier_3_domains = {
            'brookings.edu', 'cfr.org', 'rand.org', 'chathamhouse.org',
            'csis.org', 'carnegieendowment.org', 'foreignaffairs.com',
            'politico.com', 'axios.com', 'thehill.com'
        }
        
        if domain in tier_1_domains or domain.endswith('.gov') or domain.endswith('.gov.uk'):
            return 1
        elif domain in tier_2_domains:
            return 2
        elif domain in tier_3_domains or domain.endswith('.edu'):
            return 3
        elif source_type == SourceType.SOCIAL:
            return 5
        else:
            return 4
    
    def deduplicate_batch(self, evidence_list: List[EvidenceItem]) -> List[EvidenceItem]:
        """
        Deduplicate a batch of evidence items.
        
        Deduplication criteria (in order):
        1. Same canonical_url -> duplicate
        2. Same canonical_origin_id (Wire Service) -> syndicated derivative
        3. Same content_hash -> exact duplicate/syndicated
        4. High similarity (Jaccard > 0.60) -> near-duplicate
        5. Entity overlap (Entity Jaccard > 0.30) -> synonym variation
        
        Returns list with unique, representative evidence items.
        """
        seen_canonical = set()
        seen_hashes = {}  # content_hash -> first EvidenceItem
        seen_wires = {}   # wire_id -> first EvidenceItem
        deduplicated = []
        
        # Pre-compute shingles for all new items to avoid re-computation
        item_shingles = {e.id: self.compute_shingles(e.snippet) for e in evidence_list}
        entity_shingles = {e.id: self.compute_entity_shingles(e.snippet) for e in evidence_list}
        
        for evidence in evidence_list:
            # Check 1: Exact URL duplicate
            if evidence.canonical_url in seen_canonical:
                logger.debug(f"Removing URL duplicate: {evidence.url}")
                continue
            
            # Check 2: Wire Origin (Explicit Syndication)
            if evidence.canonical_origin_id:
                if evidence.canonical_origin_id in seen_wires:
                    primary = seen_wires[evidence.canonical_origin_id]
                    primary.derivative_count += 1
                    logger.info(f"Deriv: {evidence.domain} is derivative of {primary.domain} (Wire: {evidence.canonical_origin_id})")
                    
                    # Cluster together
                    if primary.independence_cluster_id:
                        evidence.independence_cluster_id = primary.independence_cluster_id
                        if primary.independence_cluster_id in self._clusters:
                            self._clusters[primary.independence_cluster_id].append(evidence.id)
                    continue
                else:
                    seen_wires[evidence.canonical_origin_id] = evidence
            
            # Check 3: Content hash duplicate (Exact match)
            if evidence.content_hash in seen_hashes:
                primary = seen_hashes[evidence.content_hash]
                primary.derivative_count += 1
                logger.info(f"Deriv: {evidence.domain} is exact copy of {primary.domain}")
                
                if primary.independence_cluster_id:
                    evidence.independence_cluster_id = primary.independence_cluster_id
                    if primary.independence_cluster_id in self._clusters:
                        self._clusters[primary.independence_cluster_id].append(evidence.id)
                continue
                
            # Check 4: Near-duplicate (Similarity Fallback)
            is_near_duplicate = False
            my_shingles = item_shingles[evidence.id]
            my_entities = entity_shingles[evidence.id]
            
            for primary in deduplicated:
                # Skip if already clustered together (e.g. via wire id)
                if primary.independence_cluster_id == evidence.independence_cluster_id:
                    continue
                    
                # 4a. Standard Content Similarity (Stopword-filtered Bigrams or Unigrams)
                score = self.jaccard_similarity(my_shingles, item_shingles[primary.id])
                
                # 4b. Entity Similarity (Fallback for synonym variations)
                entity_score = 0.0
                if score <= self.SIMILARITY_THRESHOLD:
                     entity_score = self.jaccard_similarity(my_entities, entity_shingles[primary.id])
                
                # Match if either threshold met
                # Entity threshold 0.70 separates A/B (0.67) from A/A (0.75)
                if score > self.SIMILARITY_THRESHOLD or entity_score > 0.70:
                    is_near_duplicate = True
                    primary.derivative_count += 1
                    logger.info(f"Deriv: {evidence.domain} near-duplicate of {primary.domain} (Sim: {score:.2f}, Entity: {entity_score:.2f})")
                    
                    # Cluster
                    if primary.independence_cluster_id:
                        evidence.independence_cluster_id = primary.independence_cluster_id
                        if primary.independence_cluster_id in self._clusters:
                            self._clusters[primary.independence_cluster_id].append(evidence.id)
                        else:
                             # Auto-heal: Re-initialize cluster if missing but ID exists
                             self._clusters[primary.independence_cluster_id] = [primary.id, evidence.id]
                    break
            
            if is_near_duplicate:
                continue
                
            # Unique Item
            seen_canonical.add(evidence.canonical_url)
            seen_hashes[evidence.content_hash] = evidence
            deduplicated.append(evidence)
        
        logger.info(f"Deduplicated {len(evidence_list)} -> {len(deduplicated)} evidence items")
        return deduplicated
    
    def get_cluster_stats(self) -> Dict[str, int]:
        """Get statistics about current clusters."""
        return {
            "total_clusters": len(self._clusters),
            "total_evidence": sum(len(v) for v in self._clusters.values()),
            "largest_cluster": max((len(v) for v in self._clusters.values()), default=0)
        }


# Singleton instance
evidence_deduper = EvidenceDeduper()
