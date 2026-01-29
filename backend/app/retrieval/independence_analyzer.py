"""
Independence Analyzer
Computes independence scores based on source clustering and publisher ownership
"""

import logging
from typing import List, Dict, Set, Optional
from collections import defaultdict

from app.graph.contracts import EvidenceItem, ClaimItem, SourceType

logger = logging.getLogger(__name__)


class IndependenceAnalyzer:
    """
    Analyzes source independence for claims and evidence.
    
    Independence is reduced when:
    1. Multiple sources shared a `canonical_origin_id` (Syndication/Wire).
    2. Multiple sources are from the same publisher/owner.
    3. Sources are all of the same type (e.g., all wire services).
    
    Consensus Definition:
    "Independent Confirmation" = Count of distinct `canonical_origin_id` clusters.
    Derivatives (re-publications) do NOT increment confirmation count.
    
    Independence scoring formula:
    score = (unique_clusters / total_sources) * source_type_diversity * ownership_penalty
    """
    
    # Known publisher ownership groups (domains -> parent company)
    OWNERSHIP_GROUPS = {
        # News Corp
        'wsj.com': 'news_corp',
        'foxnews.com': 'news_corp',
        'nypost.com': 'news_corp',
        'barrons.com': 'news_corp',
        'marketwatch.com': 'news_corp',
        'theaustralian.com.au': 'news_corp',
        'thetimes.co.uk': 'news_corp',
        
        # Bloomberg LP
        'bloomberg.com': 'bloomberg',
        'businessweek.com': 'bloomberg',
        
        # Conde Nast
        'newyorker.com': 'conde_nast',
        'vanityfair.com': 'conde_nast',
        'wired.com': 'conde_nast',
        'vogue.com': 'conde_nast',
        
        # New York Times Company
        'nytimes.com': 'nytimes_co',
        'theatlantic.com': 'nytimes_co',  # Laurene Powell Jobs, not NYT, but grouped for simplicity
        
        # Washington Post / Bezos
        'washingtonpost.com': 'wapo_bezos',
        
        # BBC
        'bbc.com': 'bbc',
        'bbc.co.uk': 'bbc',
        
        # Reuters/Thomson Reuters
        'reuters.com': 'thomson_reuters',
        
        # Wire Services (treat as single group for redundancy detection)
        'apnews.com': 'wire_services',
        'afp.com': 'wire_services',
    }
    
    # Source type weights for diversity calculation
    SOURCE_TYPE_WEIGHTS = {
        SourceType.PRIMARY_DATA: 1.0,
        SourceType.PRIMARY_REPORTING: 0.9,
        SourceType.ANALYSIS: 0.8,
        SourceType.AGGREGATOR: 0.5,
        SourceType.SOCIAL: 0.3,
    }
    
    def __init__(self):
        pass
    
    def get_ownership_group(self, domain: str) -> str:
        """Get the ownership group for a domain, or domain itself if unknown."""
        return self.OWNERSHIP_GROUPS.get(domain, domain)
    
    def compute_source_type_diversity(self, evidence_list: List[EvidenceItem]) -> float:
        """
        Compute diversity score based on source types.
        
        Higher diversity = sources from different types (data, reporting, analysis).
        """
        if not evidence_list:
            return 0.0
        
        type_counts = defaultdict(int)
        for e in evidence_list:
            type_counts[e.source_type] += 1
        
        # More types = higher diversity
        num_types = len(type_counts)
        max_types = len(SourceType)
        
        # Weight by quality of types present
        weighted_sum = sum(
            self.SOURCE_TYPE_WEIGHTS.get(t, 0.5) * count 
            for t, count in type_counts.items()
        )
        avg_weight = weighted_sum / len(evidence_list) if evidence_list else 0
        
        # Diversity score: combination of type variety and quality
        diversity = (num_types / max_types) * 0.5 + avg_weight * 0.5
        
        return min(1.0, diversity)
    
    def compute_ownership_penalty(self, evidence_list: List[EvidenceItem]) -> float:
        """
        Compute penalty for sources from same ownership groups.
        
        Returns multiplier (0.5 - 1.0) where 1.0 = no penalty, 0.5 = high concentration.
        """
        if len(evidence_list) <= 1:
            return 1.0
        
        ownership_counts = defaultdict(int)
        for e in evidence_list:
            group = self.get_ownership_group(e.domain)
            ownership_counts[group] += 1
        
        # Calculate concentration (Herfindahl-like)
        total = len(evidence_list)
        concentration = sum((count / total) ** 2 for count in ownership_counts.values())
        
        # Convert concentration to penalty (higher concentration = lower multiplier)
        # concentration = 1.0 means all from same owner -> penalty = 0.5
        # concentration = 1/n means perfectly distributed -> penalty = 1.0
        min_concentration = 1.0 / len(ownership_counts) if ownership_counts else 1.0
        
        if concentration <= min_concentration:
            return 1.0
        
        # Linear interpolation between min and 1.0 concentration
        penalty = 1.0 - 0.5 * ((concentration - min_concentration) / (1.0 - min_concentration))
        
        return max(0.5, penalty)
    
    def compute_cluster_independence(self, evidence_list: List[EvidenceItem]) -> float:
        """
        Compute independence based on content clusters.
        
        Multiple pieces of evidence from the same cluster (syndicated content)
        count as a single independent source.
        """
        if not evidence_list:
            return 0.0
        
        # Count unique clusters
        clusters = set()
        for e in evidence_list:
            cluster_id = e.independence_cluster_id or e.id  # Fallback to ID if no cluster
            clusters.add(cluster_id)
        
        # Independence = unique clusters / total sources
        independence = len(clusters) / len(evidence_list)
        
        return independence
    
    def compute_independence_score(self, evidence_list: List[EvidenceItem]) -> float:
        """
        Compute overall independence score for a set of evidence.
        
        Formula:
        score = cluster_independence * source_type_diversity * ownership_penalty
        
        Returns:
            Float between 0.0 (no independence) and 1.0 (fully independent)
        """
        if not evidence_list:
            return 0.0
        
        if len(evidence_list) == 1:
            # Single source cannot be independently confirmed
            # But we don't penalize too harshly
            return 0.5
        
        cluster_ind = self.compute_cluster_independence(evidence_list)
        diversity = self.compute_source_type_diversity(evidence_list)
        ownership = self.compute_ownership_penalty(evidence_list)
        
        score = cluster_ind * diversity * ownership
        
        logger.debug(
            f"Independence: cluster={cluster_ind:.2f}, diversity={diversity:.2f}, "
            f"ownership={ownership:.2f}, final={score:.2f}"
        )
        
        return score
    
    def score_claim(self, claim: ClaimItem, evidence_map: Dict[str, EvidenceItem]) -> float:
        """
        Compute independence score for a specific claim based on its evidence.
        
        Args:
            claim: The claim to score
            evidence_map: Dict mapping evidence_id -> EvidenceItem
        
        Returns:
            Independence score for this claim
        """
        # Gather evidence for this claim
        claim_evidence = [
            evidence_map[eid] for eid in claim.evidence_ids 
            if eid in evidence_map
        ]
        
        score = self.compute_independence_score(claim_evidence)
        
        # Update claim's independence_score
        claim.independence_score = score
        
        return score
    
    def analyze_agent_independence(
        self, 
        claims: List[ClaimItem], 
        evidence: List[EvidenceItem]
    ) -> Dict[str, float]:
        """
        Analyze independence for an agent's output.
        
        Returns:
            Dict with 'overall_independence', 'avg_claim_independence', 
            'unique_clusters', 'unique_owners'
        """
        evidence_map = {e.id: e for e in evidence}
        
        # Score each claim
        claim_scores = []
        for claim in claims:
            score = self.score_claim(claim, evidence_map)
            claim_scores.append(score)
        
        # Overall statistics
        overall = self.compute_independence_score(evidence)
        avg_claim = sum(claim_scores) / len(claim_scores) if claim_scores else 0.0
        
        unique_clusters = len(set(e.independence_cluster_id or e.id for e in evidence))
        unique_owners = len(set(self.get_ownership_group(e.domain) for e in evidence))
        
        return {
            'overall_independence': overall,
            'avg_claim_independence': avg_claim,
            'unique_clusters': unique_clusters,
            'unique_owners': unique_owners,
            'total_evidence': len(evidence)
        }


# Singleton instance
independence_analyzer = IndependenceAnalyzer()
