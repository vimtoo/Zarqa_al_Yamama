
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Ensure backend in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.graph.contracts import Domain, DomainClassification
from app.agents.domain_router import DomainRouter

async def test_router_invariant():
    print("\n--- Testing Domain Router Invariant Enforcement ---")
    
    router = DomainRouter()
    
    # Mock _classify_domains to simulate LLM returning ONLY Policy (Lazy Router Defect)
    # This simulates the LLM missing the economic implication of "oil sanctions"
    # Use AsyncMock because _classify_domains is awaited
    with patch.object(router, '_classify_domains', new_callable=AsyncMock) as mock_classify:

        # Setup - simulate a lazy LLM that always returns POLICY
        mock_classify.return_value = DomainClassification(
            domains=[Domain.POLICY], 
            primary_domain=Domain.POLICY, 
            confidence=0.8, 
            reasoning="Lazy classification ignoring economic keywords."
        )
        
        test_cases = [
            ("oil", "Crude oil prices spike due to supply chain disruption."),
            ("FX", "The FX markets are volatile this morning."),
            ("sanctions", "New sanctions imposed on central bank assets.")
        ]

        for keyword, scenario_text in test_cases:
            print(f"\n--- Test Case: '{keyword}' Invariant ---")
            print(f"Scenario: {scenario_text}")
            
            state = {
                "scenario": scenario_text,
                "agents_executed": [],
                "errors": []
            }
            
            result_state = await router.analyze(state)
            
            active = [d.value for d in result_state.get("active_domains", [])]
            
            print(f"Input: '{scenario_text}'")
            print(f"LLM said: POLICY")
            print(f"Router Result: {active}")
            
            if Domain.MACROECONOMICS.value in active or Domain.FINANCE.value in active:
                 print(f"✅ PASS: Invariant triggered for '{keyword}'. TemporalAnalyst WILL run.")
            else:
                 print(f"❌ FAIL: Invariant missed '{keyword}'.")
                 sys.exit(1)

    print("\n✅ All routing invariants verified.")

if __name__ == "__main__":
    asyncio.run(test_router_invariant())
