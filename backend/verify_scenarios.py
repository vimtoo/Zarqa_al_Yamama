
import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.agents.scenario_modeler import scenario_modeler
from app.graph.state import ForecastState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyScenarios")

async def verify():
    print("🧪 Verifying Scenario Modeler (Phase 5 Fix)...")
    
    # Mock State
    state = ForecastState(
        scenario="Political instability in Country X following election",
        political_risk_score=0.75,
        context_sentiment={"sentiment_score": -0.4},
        agents_executed=[],
        errors=[]
    )
    
    # Run Agent
    result_state = await scenario_modeler.analyze(state)
    
    scenarios = result_state.get("scenario_probabilities", [])
    
    # Checks
    if not scenarios:
        print("❌ FAILED: No scenarios returned")
        exit(1)
        
    print(f"✅ Generated {len(scenarios)} scenarios")
    
    if len(scenarios) < 2:
        print("❌ FAILED: Must have at least 2 competing scenarios")
        exit(1)
        
    for s in scenarios:
        print(f"\nScenario: {s.get('scenario_name', s.get('scenario'))}")
        print(f"  Probability: {s.get('probability')}")
        print(f"  Band: {s.get('likelihood_band')}")
        print(f"  Narrative: {s.get('narrative')}")
        
        # Check output structure
        if "likelihood_band" not in s:
            print("❌ FAILED: Missing 'likelihood_band'")
            exit(1)
            
        # Check for false precision (probability shouldn't be exactly heuristic 0.33 etc if LLM did its job, 
        # but mostly we check that bands are present).
        
    print("\n✅ Verification Passed: ScenarioModeler produces competing narratives with bands.")

if __name__ == "__main__":
    asyncio.run(verify())
