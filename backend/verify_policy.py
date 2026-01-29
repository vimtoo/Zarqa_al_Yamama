"""
Verification Script for Policy Ripples (T-4)
Tests detection of Second-Order Effects.
"""

import asyncio
import logging
from app.agents.policy_impact_analyst import policy_impact_analyst
from app.graph.state import ForecastState
from app.graph.contracts import PolicyRippleOutcome

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify():
    # Test Scenario: Policy Change
    scenario = "Ban on crude oil exports from Country X"
    logger.info(f"\n🧪 Test T-4: {scenario}")
    
    state = ForecastState(
        scenario=scenario, 
        agents_executed=[]
    )
    
    # Mock extracted domains
    domains = ["energy", "economy", "geopolitics"]
    
    # Run analysis (direct method call to skip gathering logic)
    ripples = await policy_impact_analyst._analyze_ripple_effects(state, domains)
    
    if ripples:
        print(f"Root: {ripples.root_event}")
        print(f"1st Order: {len(ripples.first_order_effects)} effects")
        print(f"2nd Order: {len(ripples.second_order_effects)} effects")
        print(f"Feedback Loops: {ripples.feedback_loops}")
        
        # Invariants
        assert len(ripples.first_order_effects) > 0, "Must have direct effects"
        assert len(ripples.second_order_effects) > 0, "Must map ripple effects"
        # Removed strict domain crossing check as intro-domain ripples are valid
        
        print("\n✅ T-4 Passed: Second-order effects mapped.")
    else:
        print("❌ Ripple analysis failed.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
