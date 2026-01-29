import asyncio
import logging
from app.workflow import ZarqaWorkflow
from app.config import settings

# Configure basic logging
logging.basicConfig(level=logging.INFO)

async def run_eval():
    print("Initializing ZarqaWorkflow...")
    workflow = ZarqaWorkflow()
    
    scenario = "Will the US Federal Reserve cut interest rates in Q1 2025?"
    print(f"Running Eval for Scenario: '{scenario}'")
    
    # Enable all relevant agents
    settings.LIBRARIAN_ENABLED = True
    settings.QUANTIFIER_ENABLED = True
    
    result = await workflow.execute(scenario)
    
    # 1. Check ForecastResult
    final_forecast = result.get("final_forecast")
    if final_forecast:
        print("[PASS] ForecastResult present")
        print(f"  Probability: {final_forecast.probability}")
        print(f"  Confidence Interval: {final_forecast.confidence_interval}")
        print(f"  Summary: {final_forecast.summary}")
    else:
        print("[FAIL] ForecastResult MISSING!")
        
    # 2. Check EvidenceGraph
    evidence_graph = result.get("evidence_graph")
    if evidence_graph:
        claims_count = len(evidence_graph.claims)
        sources_count = len(evidence_graph.sources_consulted)
        print(f"[PASS] EvidenceGraph present (Claims: {claims_count}, Sources: {sources_count})")
    else:
        print("[FAIL] EvidenceGraph MISSING!")
    
    # 3. Check Planner
    # We can check if 'walled_garden_query' was set by Planner
    query = result.get("walled_garden_query")
    if query:
        print(f"[PASS] Planner generated query: '{query}'")
    else:
        print("[FAIL] Planner did not set query!")
        
    # 4. Check Librarian Logs (implicitly via success of agents)
    # If we have sources, Librarian worked.
    if evidence_graph and len(evidence_graph.sources_consulted) > 0:
        print("[PASS] Librarian allowed access to sources")

if __name__ == "__main__":
    asyncio.run(run_eval())
