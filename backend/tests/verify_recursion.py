import asyncio
import logging
import json
from unittest.mock import AsyncMock, MagicMock
from app.agents.walled_garden_analyst import walled_garden_analyst
from app.config import settings
from app.llm.client import llm_manager

# Configure logging
logging.basicConfig(level=logging.INFO)

async def verify_recursion():
    print("Initializing Recursion Verification (With Mocks)...")
    
    # Ensure WG is enabled
    settings.WALLED_GARDEN_ENABLED = True
    
    # MOCK THE LLM CLIENT
    # We need accurate JSON responses for the recursion to work
    async def mock_complete(*args, **kwargs):
        role = kwargs.get("role", "default")
        prompt = args[0]
        
        print(f"  [MockLLM] Invoked with Role: {role}")
        
        if role == "planner":
            return json.dumps({"query": "Kuwait Vision 2035 renewable energy targets"})
        elif role == "extractor":
            # Rule 3: LLM CANNOT assign confidence.
            # We explicitly OMIT confidence_score here to prove the system handles it.
            return json.dumps({
                "items": [
                    {
                        "source_url": "https://kna.kw/vision2035",
                        "content_snippet": "The target is 15% renewable energy by 2030. Published: 2024.",
                        "published_date": "2024-01-01",
                        "source_domain": "kna.kw"
                    }
                ],
                "missing_info": []
            })
        return "{}"

    # Mock the execute_search to return fake results so we don't hit Google
    async def mock_search(*args, **kwargs):
        return [
            {"link": "https://kna.kw/vision2035", "title": "Kuwait Vision 2035", "snippet": "Official document..."}
        ]

    # Apply mocks
    llm_manager.complete = AsyncMock(side_effect=mock_complete)
    # We also need to patch execution_search in the node, but it is imported inside the module.
    # We can patch the function in the simple way:
    import app.agents.walled_garden_analyst as wg_module
    wg_module.execute_search = mock_search

    # Test Scenario
    state = {
        "scenario": "What are the specific KPI targets for renewable energy in Kuwait's Vision 2035?",
        "agents_executed": [],
        "errors": []
    }
    
    print(f"Running WalledGarden Analysis for: '{state['scenario']}'")
    
    # Run the analyst directly
    result_state = await walled_garden_analyst.analyze(state)
    
    # Verify Evidence Graph presence
    if "evidence_graph" in result_state:
        eg = result_state["evidence_graph"]
        if hasattr(eg, "evidence_packs") and len(eg.evidence_packs) > 0:
            pack = eg.evidence_packs[0]
            print(f"[PASS] EvidencePack generated!")
            print(f"  Analyst: Walled Garden")
            print(f"  Recursion Depth: {pack.recursion_stats.get('depth')}")
            print(f"  Items Found: {len(pack.items)}")
            
            # Print sample item
            if pack.items:
                item = pack.items[0]
                print(f"  Sample Item: {item.content_snippet[:100]}")
                if item.recursion_depth is not None:
                     print(f"  Item Recursion Depth: {item.recursion_depth}")
                else: 
                     print(f"[FAIL] Item recursion depth is None")
                     
                # Rule 5 Verification: Confidence MUST be present (computed)
                # Note: The Quantifier computes it LATER in the workflow. 
                # The Analyst usually puts a placeholder or the result of 'Evaluate'.
                # Wait, the v1.1 spec says "LLMs MAY NOT assign confidence".
                # The schema for EvidenceItem HAS a confidence_score field.
                # If the Analyst produces the item, does it set it?
                # The schema sets it to float. 
                # Our new Quantifier overwrites it. 
                # BUT Walled Garden mints the item. It needs a default.
                # Let's check if it exists.
                print(f"  Item Confidence: {item.confidence_score} (Should be 0.0 or None initially, or calculated if WG uses Evaluator)")
        else:
            print("[FAIL] EvidencePack NOT found or empty")
    else:
        print("[FAIL] evidence_graph NOT present in state")

if __name__ == "__main__":
    asyncio.run(verify_recursion())
