"""
Verification Script for Conflict Metrics (T-3)
Tests extraction of structured conflict data.
"""

import asyncio
import logging
from app.agents.political_studies_analyst import political_studies_analyst
from app.graph.state import ForecastState
from app.graph.contracts import ConflictMetrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify():
    # Test Scenario: Civil Unrest
    scenario = "Escalating civil unrest in Paris regarding pension reforms."
    logger.info(f"\n🧪 Test T-3: {scenario}")
    
    # Mock summary text to avoid API calls
    mock_summary = """
    Protests in Paris have intensified over the last 48 hours. 
    Police deployed tear gas in Place de la Concorde. 
    Arrests have increased by 20% since yesterday. 
    Unions threaten indefinite strikes.
    Lyon and Marseille also report isolated incidents.
    """
    
    # We cheat slightly by only testing extraction, not end-to-end gathering
    # But political_studies_analyst.analyze does gathering.
    # To test extraction specifically, we can call the method directly 
    # OR mock the gathering. Let's test the private extraction method for precision.
    
    metrics = await political_studies_analyst._extract_conflict_metrics(mock_summary, scenario)
    
    if metrics:
        print(f"Velocity: {metrics.velocity}")
        print(f"Intensity: {metrics.intensity_score}")
        print(f"Hotspots: {metrics.hotspots}")
        print(f"Trend: {metrics.trend}")
        
        assert metrics.intensity_score > 0, "Intensity should be positive"
        assert "Paris" in str(metrics.hotspots) or "Place de la Concorde" in str(metrics.hotspots), "Paris extraction failed"
        assert metrics.trend in ["accelerating", "stable", "decelerating"], "Invalid trend enum"
        
        print("\n✅ Verification Passed!")
    else:
        print("\n❌ Verification Failed: No metrics returned.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
