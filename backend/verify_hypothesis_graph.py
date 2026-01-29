
import asyncio
import logging
import sys
import os
import uuid

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from app.db.neo4j import get_neo4j_graph

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("verify_hypothesis_graph")

async def run_test():
    print("\n--- Phase H: Hypothesis Graph Verification ---")
    
    graph = get_neo4j_graph()
    if not await graph.health_check():
        print("❌ SKIPPING: Neo4j not available.")
        sys.exit(0) # Exit cleanly if no DB
    
    event_id = f"test-event-{uuid.uuid4()}"
    print(f"Creating Test Event: {event_id}")
    
    # 1. Create Base Event
    await graph.add_event(event_id, "Hypothesis Test Event", "2025-01-01")
    
    # 2. Create Competing Hypotheses
    s1_id = str(uuid.uuid4())
    s2_id = str(uuid.uuid4())
    
    print(f"Injecting Hypothesis 1 (Scenario: {s1_id})")
    await graph.create_hypothesis_edge(
        event_id=event_id,
        outcome_name="Outcome A: Peace",
        scenario_id=s1_id,
        confidence="High",
        evidence_cluster_ids=["c1", "c2"],
        provenance="Test provenance 1",
        weight=0.8
    )
    
    print(f"Injecting Hypothesis 2 (Scenario: {s2_id})")
    await graph.create_hypothesis_edge(
        event_id=event_id,
        outcome_name="Outcome B: Conflict",
        scenario_id=s2_id,
        confidence="Low",
        evidence_cluster_ids=["c3"],
        provenance="Test provenance 2",
        weight=0.2
    )
    
    # 3. Verify Graph State
    print("Verifying Graph State...")
    async with graph.driver.session(database=graph.database) as session:
        result = await session.run(
            """
            MATCH (e:Event {id: $event_id})-[r:HYPOTHESIZED_CAUSES]->(o)
            RETURN r.scenario_id as sid, r.confidence as conf, o.name as outcome
            """,
            event_id=event_id
        )
        
        records = [record async for record in result]
        
    print(f"Found {len(records)} hypothesis edges.")
    
    s1_found = False
    s2_found = False
    
    for r in records:
        print(f" - Edge: Scenario={r['sid']}, Outcome={r['outcome']}, Conf={r['conf']}")
        if r['sid'] == s1_id and r['outcome'] == "Outcome A: Peace":
            s1_found = True
        if r['sid'] == s2_id and r['outcome'] == "Outcome B: Conflict":
            s2_found = True
            
    if s1_found and s2_found:
        print("✅ PASS: Competing hypotheses coexist correctly.")
    else:
        print("❌ FAIL: Missing hypothesis edges.")
        sys.exit(1)
        
    await graph.close()

if __name__ == "__main__":
    asyncio.run(run_test())
