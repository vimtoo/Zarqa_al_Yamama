
import sys
import os
import logging
from datetime import datetime

# Ensure backend in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.graph.contracts import EvidenceItem, SourceType
from app.retrieval.evidence_deduper import evidence_deduper
from app.retrieval.independence_analyzer import independence_analyzer

# Configure logging to see Deduper output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_syndication")

def run_syndication_test():
    print("\n--- Testing Syndication Loophole Fix ---")
    
    # Base Content (AP Wire Pattern)
    base_snippet = "WASHINGTON (AP) — The Federal Reserve signaled widely expected interest rate cuts today. Chair Powell stated inflation is cooling."
    base_content = "WASHINGTON (AP) — The Federal Reserve signaled widely expected interest rate cuts today. Chair Powell stated inflation is cooling."
    
    evidence_list = []
    
    # Simulate 10 variations (Syndicated) across different domains
    print("Generating 10 syndicated variations...")
    for i in range(10):
        # Add slight variation to ensure hash diff (testing similarity/regex, not hash match)
        variation = f"{base_snippet} (Updated: {i} mins ago)"
        
        # Add "noise" shingle to test similarity threshold (needs to be > 0.85 similarity)
        # Adding a short unique string is fine, snippet is dominant
        
        ev = evidence_deduper.process_evidence(
            raw_url=f"https://source-{i}.com/news/article-{i}",
            content=base_content + f" variation {i}", # Change content slightly
            snippet=variation,
            published_at=datetime.now(),
            source_type=SourceType.PRIMARY_REPORTING
        )
        evidence_list.append(ev)

    print(f"Created {len(evidence_list)} raw evidence items.")
    
    # Run Deduplication Batch
    print("\nRunning Deduplication Batch...")
    deduplicated = evidence_deduper.deduplicate_batch(evidence_list)
    
    print(f"Deduplicated count: {len(deduplicated)} (Expected ~10, but clustered)")
    # Note: deduplicate_batch removes strictly redundant items from the *returned list* 
    # BUT we want to see if `derivative_count` and clustering worked.
    # Actually, my deduplicate_batch implementation *removes* them from the list if they are duplicates.
    # Wait, the requirement says "Deduplication by snippet_hash/URL allows syndicated wire stories to appear as multi-source consensus."
    # So we *want* them to be removed/clustered so they don't appear as independent sources.
    
    # If they are clustered, they might still be in the list?
    # My code:
    # "if evidence.canonical_origin_id in seen_wires: ... continue"
    # So they are removed from the 'deduplicated' list.
    
    print(f"Resulting unique items: {len(deduplicated)}")
    
    if len(deduplicated) != 1:
        print(f"❌ FAILED: Expected 1 unique item, got {len(deduplicated)}")
        # If similarity/regex failed, we might get 10.
        for item in deduplicated:
            print(f"  - {item.domain} (Wire: {item.canonical_origin_id})")
        sys.exit(1)
        
    primary = deduplicated[0]
    print(f"Primary Item: {primary.domain}")
    print(f"Wire ID: {primary.canonical_origin_id}")
    print(f"Derivative Count: {primary.derivative_count}")
    
    # Check Logic
    if primary.canonical_origin_id != "ap_wire":
        print("❌ FAILED: Did not detect AP Wire origin.")
        sys.exit(1)
        
    if primary.derivative_count != 9:
        print(f"❌ FAILED: Expected derivative_count 9, got {primary.derivative_count}")
        sys.exit(1)

    print("✅ SUCCESS: 10 items collapsed to 1 primary.")
    
    # Check Independence Analysis
    # We pass the *original* list to independence analyzer to see how it handles the cluster?
    # Or typically the Deduper output is what gets passed to the next stage?
    # The deduplicated list has only 1 item.
    # If I pass the original list (assuming the system kept them but clustered them), 
    # Independence Analyzer should verify unique clusters.
    
    # IndependenceAnalyzer usually takes the *deduplicated* items if that's what the pipeline does.
    # But let's verify that even if all 10 were passed (e.g. if deduper didn't filter them but just clustered them),
    # the unique_cluster count is 1.
    
    print("\nVerifying Independence Analyzer (Cluster Count)...")
    stats = independence_analyzer.analyze_agent_independence([], evidence_list) # Pass all 10
    unique_clusters = stats['unique_clusters']
    
    print(f"Unique Clusters: {unique_clusters}")
    
    if unique_clusters != 1:
        print(f"❌ FAILED: Expected 1 unique cluster, got {unique_clusters}")
        sys.exit(1)
        
    print("✅ SUCCESS: Independence Analyzer sees 1 unique cluster.")

if __name__ == "__main__":
    run_syndication_test()
