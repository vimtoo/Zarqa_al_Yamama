
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
logger = logging.getLogger("verify_syndication_precision")

def run_precision_test():
    print("\n--- Syndication Precision Guard (Zero Scope Creep) ---")
    
    # TEST 1: Negative Control (Shared Entities, Distinct Events)
    # Event A: Oracle acquires Cerner
    # Event B: Oracle invests in Cloud
    # Overlap: Oracle, $28 Billion (hypothetical same number to trick it)
    print("\n[Test 1] Negative Control: Entity Overlap but Distinct Events")
    
    # Use fresh instance to avoid singleton state issues
    from app.retrieval.evidence_deduper import EvidenceDeduper
    deduper = EvidenceDeduper()
    
    event_a_vars = [
        "Oracle to acquire Cerner for $28 billion in all-cash deal.",
        "Breaking: Oracle buys medical data giant Cerner for $28 billion.",
        "Cerner agreed to be acquired by Oracle Corporation for $28bn.",
        "Major tech acquisition: Oracle takes over Cerner for $28 billion.",
        "Oracle's $28 billion bet on Cerner aims to revolutionize healthcare."
    ]
    
    event_b_vars = [
        "Oracle invests $28 billion to expand cloud infrastructure globally.",
        "Oracle announces $28 billion capital expenditure for cloud data centers.",
        "New Oracle Cloud strategy involves $28 billion investment.",
        "Oracle commits $28 billion to fight AWS and Azure in cloud wars.",
        "Tech giant Oracle pours $28 billion into server infrastructure."
    ]
    
    ev_list = []
    
    # Inject Event A
    for i, content in enumerate(event_a_vars):
        ev = deduper.process_evidence(
            raw_url=f"http://outlet-a-{i}.com/news",
            content=content, snippet=content,
            published_at=datetime.now(),
            source_type=SourceType.PRIMARY_REPORTING
        )
        ev_list.append(ev)
        
    # Inject Event B
    for i, content in enumerate(event_b_vars):
        ev = deduper.process_evidence(
            raw_url=f"http://outlet-b-{i}.com/news",
            content=content, snippet=content,
            published_at=datetime.now(),
            source_type=SourceType.PRIMARY_REPORTING
        )
        ev_list.append(ev)

    print(f"Injecting {len(ev_list)} items (5 Event A, 5 Event B)...")
    
    # We want to test DEDUPLICATION from scratch.
    # process_evidence() already assigned them to clusters sequentially.
    # We rely on deduplicate_batch() to merge them.
    # Crucially, we MUST NOT clear deduper._clusters because items refer to these keys.
    
    deduped = deduper.deduplicate_batch(ev_list)
    
    deduped = deduper.deduplicate_batch(ev_list)
    stats = independence_analyzer.analyze_agent_independence([], ev_list)
    clusters = stats.get("unique_clusters", 0)
    
    print(f"Total Items: {len(ev_list)}")
    print(f"Unique Clusters Found: {clusters}")
    
    if clusters >= 2:
        print("✅ PASS: Correctly separated distinct events.")
    else:
        print("❌ FAIL: Over-collapsed distinct events into single cluster.")

    # TEST 2: Time Boundary (Same Entity/Action, Different Date)
    print("\n[Test 2] Time Boundary: Same Event Type, Different Date")
    
    # Event X: Monday
    event_x_vars = [
        "The Dow Jones Industrial Average fell 500 points on Monday.",
        "Monday saw the Dow Jones drop by 500 points amid trading fears.",
        "Stocks down: Dow loses 500 points in Monday session."
    ]
    
    # Event Y: Friday
    event_y_vars = [
        "The Dow Jones Industrial Average fell 500 points on Friday.",
        "Friday trading ended with the Dow Jones dropping 500 points.",
        "Stocks down: Dow loses 500 points in closing Friday session."
    ]
    
    ev_list_2 = []
    for i, content in enumerate(event_x_vars):
        ev = evidence_deduper.process_evidence(
            raw_url=f"http://outlet-x-{i}.com/news",
            content=content, snippet=content,
            published_at=datetime.now(),
            source_type=SourceType.PRIMARY_REPORTING
        )
        ev_list_2.append(ev)
        
    for i, content in enumerate(event_y_vars):
        ev = evidence_deduper.process_evidence(
            raw_url=f"http://outlet-y-{i}.com/news",
            content=content, snippet=content,
            published_at=datetime.now(),
            source_type=SourceType.PRIMARY_REPORTING
        )
        ev_list_2.append(ev)
        
    print(f"Injecting {len(ev_list_2)} items (3 Monday, 3 Friday)...")
    
    # For Test 2, we should use a NEW deduper instance to start fresh
    deduper2 = EvidenceDeduper()
    
    ev_list_2_fresh = []
    # Re-process using new deduper to get clean state
    for i, content in enumerate(event_x_vars):
        ev = deduper2.process_evidence(raw_url=f"http://outlet-x-{i}.com/news", content=content, snippet=content, published_at=datetime.now())
        ev_list_2_fresh.append(ev)
    for i, content in enumerate(event_y_vars):
        ev = deduper2.process_evidence(raw_url=f"http://outlet-y-{i}.com/news", content=content, snippet=content, published_at=datetime.now())
        ev_list_2_fresh.append(ev)
        
    deduped_2 = deduper2.deduplicate_batch(ev_list_2_fresh)
    stats_2 = independence_analyzer.analyze_agent_independence([], ev_list_2_fresh)
    clusters_2 = stats_2.get("unique_clusters", 0)
    
    print(f"Total Items: {len(ev_list_2)}")
    print(f"Unique Clusters Found: {clusters_2}")
    
    if clusters_2 >= 2:
        print("✅ PASS: Correctly separated Monday vs Friday.")
    else:
        print("❌ FAIL: Over-collapsed different dates.")
        
    if clusters >= 2 and clusters_2 >= 2:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_precision_test()
