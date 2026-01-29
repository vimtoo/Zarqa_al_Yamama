"""
Verification Script for Qualitative Quantifier
Tests strict adherence to Frozen Contract #2.
"""

import asyncio
import logging
from app.agents.qualitative_quantifier import qualitative_quantifier
from app.graph.state import ForecastState
from app.graph.contracts import EvidenceItem, SourceType, QualitativeForecast

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify():
    # Mock Evidence
    mock_evidence = [
        EvidenceItem(
            id="ev_1",
            url="http://news.com",
            canonical_url="http://news.com",
            domain="news.com",
            content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            snippet="The ruling party is consolidating power ahead of elections.",
            source_type=SourceType.PRIMARY
        ),
        EvidenceItem(
            id="ev_2",
            url="http://report.org",
            canonical_url="http://report.org",
            domain="report.org",
            content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            snippet="Opposition leaders claim suppression tactics are intensifying.",
            source_type=SourceType.PRIMARY
        )
    ]

    # Test Case 1: Standard Political Scenario
    scenario = "Will the upcoming election result in a regime change?"
    logger.info(f"\n🧪 Test 1: {scenario}")
    
    state = ForecastState(
        scenario=scenario, 
        deduped_evidence=mock_evidence,
        agents_executed=[],
        errors=[]
    )
    
    result = await qualitative_quantifier.analyze(state)
    forecast: QualitativeForecast = result.get("qualitative_forecast")
    
    assert forecast is not None, "Forecast returned None"
    
    # Contract Verification (Rule 2 checks)
    print(f"Outcome: {forecast.outcome_label}")
    print(f"Likelihood: {forecast.likelihood_category}")
    print(f"Unknowns: {len(forecast.unknown_factors)}")
    print(f"Evidence Chain: {forecast.evidence_chain}")
    
    # Invariant Checks
    assert hasattr(forecast, 'unknown_factors') and len(forecast.unknown_factors) > 0, "Invariant: Omniscience detected (no unknowns)"
    assert hasattr(forecast, 'likelihood_category') and isinstance(forecast.likelihood_category, str), "Invariant: Numeric probability used?"
    
    # Check Evidence linking
    # Note: LLM might hallucinate IDs unless forced. The agent logic filters invalid IDs.
    # If the LLM returns no valid IDs, the evidence_chain will be empty.
    # If confidence > 0.2, evidence_chain MUST NOT be empty.
    if forecast.confidence_score > 0.2:
        assert len(forecast.evidence_chain) > 0, "Invariant: High confidence without evidence citation"

    print("\n✅ Verification Passed!")

if __name__ == "__main__":
    asyncio.run(verify())
