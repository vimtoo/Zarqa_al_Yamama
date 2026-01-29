
import sys
import os
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from app.graph.contracts import EvidenceItem, SourceType
from app.retrieval.evidence_deduper import evidence_deduper
from app.retrieval.independence_analyzer import independence_analyzer

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("verify_syndication_hard")

def run_hard_syndication_test():
    print("\n--- Hard Syndication Test (Synonym Variations) ---")
    
    # 1. Base Story (No explicit wire markers)
    # Variations using synonyms but same core facts
    variations = [
        "Global markets plunged today as inflation fears gripped investors. The Dow Jones fell 500 points.",
        "World stock markets tumbled on Monday amid rising panic over inflation. The Dow Jones Industrial Average dropped by 500 points.",
        "Equities worldwide slumped significantly as inflationary pressures scared traders. A 500-point drop was seen in the Dow.",
        "Inflation scare causes global market sell-off. The Dow Jones index lost 500 points in heavy trading.",
        "Major indices fell sharply today. Investors are worried about inflation, causing the Dow to slide 500 points.",
        "Financial markets faced a downturn due to inflation concerns. The Dow Jones shed 500 points by the close.",
        "Stocks took a hit globally as inflation data spooked the street. The Dow declined by 500 points.",
        "A 500-point drop in the Dow Jones marked a day of global market losses driven by inflation anxiety.",
        "Global equities traded lower as inflation fears persisted. The Dow Jones fell 500 points in a rough session.",
        "Markets around the world sank today on inflation news. The Dow Jones Industrial Average was down 500 points."
    ]
    
    ev_list = []
    print(f"Injecting {len(variations)} variations of the same story (no wire markers)...")
    
    for i, content in enumerate(variations):
        # Create Evidence Item via process_evidence to strip markers (none here) and hash
        ev = evidence_deduper.process_evidence(
            raw_url=f"http://outlet-{i}.com/market-report",
            content=content, 
            snippet=content, # Use same for snippet
            published_at=datetime.now(),
            source_type=SourceType.PRIMARY_REPORTING
        )
        ev_list.append(ev)
        print(f" [{i}] {content[:60]}...")

    # 2. Run Batch Deduplication
    print("\nRunning Deduplication...")
    deduped = evidence_deduper.deduplicate_batch(ev_list)
    
    # 3. Analyze Independence
    print("\nAnalyzing Independence Clusters...")
    stats = independence_analyzer.analyze_agent_independence([], ev_list)
    unique_clusters = stats.get("unique_clusters", 0)
    
    print(f"Total Items: {len(ev_list)}")
    print(f"Deduplicated Representative Items: {len(deduped)}")
    print(f"Unique Clusters Found: {unique_clusters}")
    
    if unique_clusters == 1:
        print("\n✅ SUCCESS: All variations passed as 1 single cluster.")
        sys.exit(0)
    else:
        print(f"\n❌ FAILURE: Expected 1 cluster, found {unique_clusters}.")
        print("System failed to detect these as the same story.")
        sys.exit(1)

if __name__ == "__main__":
    run_hard_syndication_test()
