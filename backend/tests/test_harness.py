
import pytest
import json
import os
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import sys

# Add backend to path to import verify_regression
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from verify_regression import CalibrationRunner

@pytest.mark.asyncio
async def test_calibration_runner_success():
    """Test that runner passes on valid output."""
    runner = CalibrationRunner()
    
    # Mock Workflow
    mock_workflow = MagicMock()
    mock_workflow.graph.ainvoke = AsyncMock(return_value={
        "agents_executed": ["political_studies_analyst"],
        "conflict_metrics": MagicMock(intensity_score=50),
        "narrative_brief": "There is significant unrest and violent protests."
    })
    runner.workflow = mock_workflow
    
    # Create temp scenario
    scenario = {
        "scenario_id": "TEST-001",
        "name": "Test Success",
        "input_text": "input",
        "expected_behavior": {
            "routing": {
                "must_activate_agents": ["political_studies_analyst"],
                "forbidden_agents": ["report_writer"]
            },
            "metrics": {
                "conflict_intensity_band": "BAND_III" # 41-60
            },
            "uncertainty": {},
            "narrative_invariants": {
                "must_contain_keywords": ["unrest"],
                "must_not_contain": ["peaceful"]
            }
        }
    }
    
    # Write to tmp file
    with open("test_scenario_pass.json", "w") as f:
        json.dump(scenario, f)
        
    await runner.run_scenario(Path("test_scenario_pass.json"))
    
    assert len(runner.failures) == 0
    os.remove("test_scenario_pass.json")

@pytest.mark.asyncio
async def test_calibration_runner_routing_failure():
    """Test detection of missing agents."""
    runner = CalibrationRunner()
    
    # Mock Workflow - Missing Agent
    mock_workflow = MagicMock()
    mock_workflow.graph.ainvoke = AsyncMock(return_value={
        "agents_executed": [], # Empty execution
        "conflict_metrics": MagicMock(intensity_score=50),
        "narrative_brief": "unrest"
    })
    runner.workflow = mock_workflow
    
    scenario = {
        "scenario_id": "TEST-002",
        "name": "Test Routing Fail",
        "input_text": "input",
        "expected_behavior": {
            "routing": {
                "must_activate_agents": ["political_studies_analyst"],
                "forbidden_agents": []
            },
            "metrics": {},
            "uncertainty": {},
            "narrative_invariants": { "must_contain_keywords": [], "must_not_contain": []}
        }
    }
    
    with open("test_scenario_fail_route.json", "w") as f:
        json.dump(scenario, f)
        
    await runner.run_scenario(Path("test_scenario_fail_route.json"))
    
    assert len(runner.failures) == 1
    assert "Routing Lobotomy" in runner.failures[0]["violations"][0]
    os.remove("test_scenario_fail_route.json")

@pytest.mark.asyncio
async def test_calibration_runner_metric_drift():
    """Test detection of metric drift."""
    runner = CalibrationRunner()
    
    # Mock Workflow - Score too high (drift to Band IV)
    mock_workflow = MagicMock()
    mock_workflow.graph.ainvoke = AsyncMock(return_value={
        "agents_executed": ["political_studies_analyst"],
        "conflict_metrics": MagicMock(intensity_score=70), # Band IV
        "narrative_brief": "unrest"
    })
    runner.workflow = mock_workflow
    
    scenario = {
        "scenario_id": "TEST-003",
        "name": "Test Metric Drift",
        "input_text": "input",
        "expected_behavior": {
            "routing": { "must_activate_agents": [], "forbidden_agents": []},
            "metrics": {
                "conflict_intensity_band": "BAND_III" # Expect 41-60
            },
            "uncertainty": {},
            "narrative_invariants": { "must_contain_keywords": [], "must_not_contain": []}
        }
    }
    
    with open("test_scenario_fail_metric.json", "w") as f:
        json.dump(scenario, f)
        
    await runner.run_scenario(Path("test_scenario_fail_metric.json"))
    
    assert len(runner.failures) == 1
    assert "Metric Drift" in runner.failures[0]["violations"][0]
    os.remove("test_scenario_fail_metric.json")
