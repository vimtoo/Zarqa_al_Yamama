
import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Configure Logging to show the specific lines we need
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def verify_halt_enforcement():
    print(">>> INITIALIZING GOVERNANCE HALT PROOF <<<\n")
    
    # 1. Mock dependencies to avoid real API calls
    with patch('app.llm.client.llm_manager.complete', new_callable=AsyncMock) as mock_complete, \
         patch('app.agents.walled_garden_analyst.execute_search', new_callable=AsyncMock) as mock_search, \
         patch('app.graph.evaluator.evaluator.evaluate') as mock_evaluate:
        
        # Setup Mocks
        mock_complete.return_value = '{"query": "mock", "items": [{"content_snippet": "fact", "source_url": "url"}]}'
        mock_search.return_value = [{'link': 'http://test.com', 'title': 'Test', 'snippet': 'Test Content'}]
        
        # CRITICAL: Mock the Evaluator to trigger TERMINATE_GOVERNOR_HALT at Depth 1
        # This simulates a Governor Halt occurring after the first iteration
        def side_effect_evaluate(pack):
            depth = pack.recursion_stats.get('depth', 0)
            if depth >= 1:
                # SIMULATE GOVERNOR HALT TRIGGER
                print(f"[MOCK EVALUATOR] >> SIMULATING GOVERNANCE HALT AT DEPTH {depth} <<")
                return "TERMINATE_GOVERNOR_HALT"
            else:
                 print(f"[MOCK EVALUATOR] Depth {depth}: FAIL_CONTINUE")
                 return "FAIL_CONTINUE"
                 
        mock_evaluate.side_effect = side_effect_evaluate

        # Import Analyst (Triggering the graph build with mocked deps)
        from app.agents.walled_garden_analyst import walled_garden_analyst
        
        # Setup State
        state = {
            "scenario": "Restricted Topic Scenario",
            "agents_executed": [],
            "errors": []
        }
        
        print(f"Running Analysis on: '{state['scenario']}'")
        print("Expected Behavior: Loop should run once (Depth 0), then HALT at Depth 1 (Before Max Depth 3).\n")
        
        # Execute
        result = await walled_garden_analyst.analyze(state)
        
        # Validation
        if "evidence_graph" in result:
            pack = result["evidence_graph"].evidence_packs[0]
            final_depth = pack.recursion_stats['depth']
            halt_report = pack.governor_halt_report
            
            print(f"\n>>> RESULT <<<")
            print(f"Final Recursion Depth: {final_depth}")
            
            if halt_report:
                print(f"[SUCCESS] GovernanceHaltReport Detected!")
                print(f"  Reason: {halt_report.trigger}")
                print(f"  Outcome: {halt_report.outcome}")
            else:
                print(f"[FAIL] NO GovernanceHaltReport found in final pack.")
                
            if final_depth < 3 and halt_report:
                print("[SUCCESS] Recursion aborted EARLY (before max depth 3) AND Report Generated.")
            else:
                print("[FAIL] Recursion check failed.")
        else:
            print("[FAIL] No evidence pack generated.")

if __name__ == "__main__":
    asyncio.run(verify_halt_enforcement())
