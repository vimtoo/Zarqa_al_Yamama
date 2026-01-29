
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.llm.arbitration import ArbitrationPolicy, ArbitrationLane, TaskType, Sensitivity
from app.llm.client import LLMManager

logger = logging.getLogger("test_arbitration")

@pytest.mark.asyncio
async def test_forbidden_lane_blocks_gemini():
    """
    Prove that a FORBIDDEN agent (TemporalAnalyst) cannot use Gemini 
    even if enabled, and defaults to primary.
    """
    # Setup
    with patch("app.llm.client.Settings") as mock_settings:
        mock_settings.return_value.GEMINI_ENABLED = True
        mock_settings.return_value.GEMINI_API_KEY = "fake_key"
        mock_settings.return_value.DEFAULT_LLM_PROVIDER = "openrouter"
        mock_settings.return_value.OPENROUTER_API_KEY = "fake_key"
        
        # Initialize Forbidden Agent
        manager = LLMManager(agent_name="TemporalAnalyst")
        
        # Verify Clients Initialized
        assert "gemini" in manager.clients
        assert "openrouter" in manager.clients
        
        # Mock Client Completes
        manager.clients["openrouter"].complete = AsyncMock(return_value="primary_response")
        manager.clients["gemini"].complete = AsyncMock(return_value="gemini_response")
        
        # Execute
        result = await manager.complete(
            prompt="test prompt",
            messages=[{"role": "user", "content": "predict probability"}],
            task_type=TaskType.DECISION,
            sensitivity=Sensitivity.HIGH
        )
        
        # Assertions
        assert result == "primary_response"
        manager.clients["openrouter"].complete.assert_called_once()
        manager.clients["gemini"].complete.assert_not_called()
        
        # Check Lane Resolution logic directly
        lane = ArbitrationPolicy.get_lane("TemporalAnalyst", TaskType.DECISION)
        assert lane == ArbitrationLane.FORBIDDEN
        
        res = ArbitrationPolicy.resolve_model(lane, gemini_enabled=True, primary_model="openrouter")
        assert res["model_used"] == "openrouter"
        assert res["reason"] == "lane_forbidden"

@pytest.mark.asyncio
async def test_advisory_lane_allows_gemini():
    """
    Prove that an ADVISORY agent (ReportWriter) CAN use Gemini 
    when enabled for synthesis tasks.
    """
    # Setup
    with patch("app.llm.client.Settings") as mock_settings:
        mock_settings.return_value.GEMINI_ENABLED = True
        mock_settings.return_value.GEMINI_API_KEY = "fake_key"
        mock_settings.return_value.DEFAULT_LLM_PROVIDER = "openrouter"
        mock_settings.return_value.OPENROUTER_API_KEY = "fake_key"
        
        # Initialize Advisory Agent
        manager = LLMManager(agent_name="ReportWriter")
        
        # Mock Clients
        manager.clients["gemini"] = MagicMock()
        manager.clients["gemini"].complete = AsyncMock(return_value="gemini_synthesis")
        manager.clients["openrouter"] = MagicMock()
        
        # Execute
        result = await manager.complete(
            prompt="test prompt",
            messages=[{"role": "user", "content": "write report"}],
            task_type=TaskType.SYNTHESIS
        )
        
        # Assertions
        assert result == "gemini_synthesis"
        manager.clients["gemini"].complete.assert_called_once()
        
        # Check Lane Logic
        lane = ArbitrationPolicy.get_lane("ReportWriter", TaskType.SYNTHESIS)
        assert lane == ArbitrationLane.ADVISORY

@pytest.mark.asyncio
async def test_gemini_disabled_fallback():
    """
    Prove that even allowed agents fallback to primary if Gemini is disabled.
    """
    with patch("app.llm.client.Settings") as mock_settings:
        mock_settings.return_value.GEMINI_ENABLED = False
        mock_settings.return_value.DEFAULT_LLM_PROVIDER = "openrouter"
        mock_settings.return_value.OPENROUTER_API_KEY = "fake_key"
        
        manager = LLMManager(agent_name="ReportWriter")
        
        # Verify Gemini client NOT initialized or not used
        # Note: In implementation, we init client only if enabled key presence.
        # But here enabled=False.
        
        manager.clients["openrouter"] = MagicMock()
        manager.clients["openrouter"].complete = AsyncMock(return_value="primary_fallback")
        
        result = await manager.complete(
            prompt="test prompt",
            messages=[{"role": "user", "content": "write report"}],
            task_type=TaskType.SYNTHESIS
        )
        
        assert result == "primary_fallback"
        
@pytest.mark.asyncio
async def test_crosscheck_trigger():
    """
    Prove high sensitivity triggers crosscheck lane (audit only for now).
    """
    lane = ArbitrationPolicy.get_lane("GenericAgent", TaskType.DECISION, Sensitivity.HIGH)
    assert lane == ArbitrationLane.CROSSCHECK
    
    # Current implementation falls back to primary but logs reasoning
    res = ArbitrationPolicy.resolve_model(lane, gemini_enabled=True, primary_model="openrouter")
    assert res["model_used"] == "openrouter"
    assert res["reason"] == "crosscheck_primary"
