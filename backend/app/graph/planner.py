from typing import List, Dict, Any
import logging
from pydantic import BaseModel

from app.llm.client import llm_manager
from app.graph.state import ForecastState
from app.graph.schema import Scenario

logger = logging.getLogger(__name__)

class ResearchSubTask(BaseModel):
    tool: str # e.g. "think_tank_analyst", "walled_garden_analyst"
    query: str
    rationale: str

class ResearchPlan(BaseModel):
    original_query: str
    main_objective: str
    sub_tasks: List[ResearchSubTask]
    suggested_scenarios: List[str]
    entities: List[str]
    regions: List[str]
    timeframe: str
    contrarian_angles: List[str]

class Planner:
    """
    The Planner: Decomposes a high-level forecast query into actionable research steps.
    """
    
    async def generate_plan(self, state: ForecastState) -> ForecastState:
        """
        Analyze the scenario and create a structured research plan.
        """
        scenario = state.get("scenario", "")
        logger.info(f"Planner: Generating research plan for '{scenario}'")
        
        system_prompt = (
            "You are a Senior Strategic Research Planner. "
            "Your goal is to break down a forecasting question into specific, researchable sub-tasks."
            "Assign tasks to specific agents:\n"
            "- 'think_tank_analyst': For policy frameworks, academic theory, long-term trends.\n"
            "- 'walled_garden_analyst': For current events, specific data points, news verification.\n"
            "- 'market_classifier': IF the query involves prices, commodities, or economic indicators.\n"
            "Identify key ENTITIES (people, orgs), REGIONS (specific countries/zones), and TIMEFRAME.\n"
            "Also suggest 2-3 Contrarian Angles to challenge the mainstream view."
        )
        
        prompt = (
            f"Forecast Scenario: '{scenario}'\n\n"
            "Create a Research Plan in STRICT JSON format with keys: "
            "main_objective, "
            "sub_tasks (list of {tool, query, rationale}), "
            "suggested_scenarios (list of strings), "
            "entities (list), regions (list), timeframe (string), contrarian_angles (list)."
        )
        
        try:
            plan_data = await llm_manager.analyze(
                data={"scenario": scenario},
                analysis_type="research_plan", # Custom type, might need to handle in client or just use complete
                context=prompt
            )
            
            # Since analyze() returns a dict, we can map it to our state
            # Ideally we validate with Pydantic, but for now we inject into state
            
            sub_tasks = plan_data.get("sub_tasks", [])
            scenarios = plan_data.get("suggested_scenarios", [])
            
            # Store plan in state (we might need a new field or just log it for now)
            # For this MVP, we will use the plan to DIRECTLY set the queries for other agents
            
            # 1. Configure Walled Garden
            wg_tasks = [t for t in sub_tasks if t.get("tool") == "walled_garden_analyst"]
            if wg_tasks:
                # Combine queries
                combined_query = " ".join([t["query"] for t in wg_tasks])
                state["walled_garden_query"] = combined_query
                logger.info(f"Planner: Set Walled Garden query to '{combined_query}'")
                
            # 2. Configure Scenarios
            if scenarios:
                # Initialize scenario probabilities structure
                state["scenario_probabilities"] = [
                    {"scenario": s, "probability": 0.33, "drivers": []} for s in scenarios[:3]
                ]
            
            return state
            
        except Exception as e:
            logger.error(f"Planner error: {e}")
            # Fallback: maintain default state, allowing agents to run with default logic
            return state

planner = Planner()
