"""
Verification Script for Bias Triangulation (T-5)
Tests:
1. Identifying Disagreement (Consensus Status)
2. Detecting Source Monoculture (Red Flag)
"""

import asyncio
import logging
from app.agents.governor import TheGovernor
from app.graph.state import ForecastState
from app.graph.contracts import EvidenceItem, SourceType, BiasTriangulation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify():
    governor = TheGovernor()
    
    # Test Scenario: Contested Responsibility
    scenario = "Who is responsible for the pipeline explosion?"
    logger.info(f"\n🧪 Test T-5: {scenario}")
    
    # Mock Evidence: Polarized
    evidence = [
        EvidenceItem(
            id="src_1",
            url="http://state-media.com",
            canonical_url="http://state-media.com",
            domain="state-media.com",
            content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            snippet="The government claims foreign saboteurs caused the blast.",
            source_type=SourceType.PRIMARY
        ),
        EvidenceItem(
            id="src_2",
            url="http://rebel-news.org",
            canonical_url="http://rebel-news.org",
            domain="rebel-news.org",
            content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            snippet="Rebels claim the explosion was due to poor maintenance by the state.",
            source_type=SourceType.PRIMARY
        )
    ]
    
    state = ForecastState(
        scenario=scenario, 
        deduped_evidence=evidence,
        agents_executed=[],
        warnings=[]
    )
    
    # Run analysis
    bias = await governor._analyze_bias_landscape(state)
    
    if bias:
        print(f"Consensus: {bias.consensus_status}")
        print(f"Divergence: {bias.divergence_point}")
        print(f"Missing: {bias.unrepresented_perspective}")
        
        assert bias.consensus_status in ["Divided", "Polarized", "Chaos"], "Should identify conflict"
        assert len(bias.positions) == 2, "Should have 2 positions"
    else:
        print("❌ Bias analysis failed to run.")
        exit(1)

    print("\n✅ T-5 Passed: Polarized landscape detected.")
    
    # Test Red Flag: Monoculture
    logger.info("\n🚩 Testing Red Flag: Source Monoculture")
    
    # Create monoculture
    bias.positions.append(bias.positions[0])
    bias.positions.append(bias.positions[0])
    # Now 3/4 are same (75%? No, make it >80%)
    # Let's mock a pure monoculture result object manually for the check function
    from app.graph.contracts import SourcePosition
    
    monoculture_bias = BiasTriangulation(
        topic=scenario,
        consensus_status="Consensus",
        positions=[
            SourcePosition(source_id="1", stance="Supports", bias_rating="State Media"),
            SourcePosition(source_id="2", stance="Supports", bias_rating="State Media"),
            SourcePosition(source_id="3", stance="Supports", bias_rating="State Media"),
            SourcePosition(source_id="4", stance="Supports", bias_rating="State Media")
        ],
        divergence_point="None",
        unrepresented_perspective=["Opposition"]
    )
    
    state['warnings'] = []
    governor._check_source_monoculture(monoculture_bias, state)
    
    print(f"Warnings: {state['warnings']}")
    assert any("Source Monoculture Detected" in w for w in state['warnings']), "Failed to flag monoculture"
    print("✅ Red Flag Logic Verified.")

if __name__ == "__main__":
    asyncio.run(verify())
