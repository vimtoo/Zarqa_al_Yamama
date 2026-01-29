
import os
import sys
from unittest.mock import MagicMock

# Mock httpx
sys.modules["httpx"] = MagicMock()

import pytest
from unittest.mock import AsyncMock, patch
from app.llm import client


import asyncio

def test_analyze_fail_closed_structure():
    """
    Test that LLMManager.analyze returns a valid LOW_CONFIDENCE object
    when provider calls fail to return valid JSON.
    """
    async def _run():
        # Setup Manager
        manager = client.LLMManager()
        
        # Mock get_client to return a client that always returns garbage
        mock_client = AsyncMock()
        mock_client.complete.return_value = "This is not JSON"
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            # Trigger analyze
            result = await manager.analyze(
                data={"test": 1},
                analysis_type="market_adapter_v1"
            )
            
            # ASSERTIONS based on Low Confidence Contract
            assert isinstance(result, dict), "Result must be a dict"
            
            # 1. Status
            assert result.get("status") == "LOW_CONFIDENCE"
            assert result.get("agent") == "market_adapter_v1"
            
            # 2. Confidence/Claims
            assert result.get("confidence") == 0.0
            assert result.get("claims") == []
            assert result.get("evidence") == []
            
            # 3. Uncertainty Notes (Crucial fix)
            notes = result.get("uncertainty_notes")
            assert isinstance(notes, list)
            assert len(notes) > 0, "uncertainty_notes must contain the reason"
            assert "Failed to generate/parse" in notes[0]
            
            # 4. Raw response capture
            assert result.get("raw_response") == "This is not JSON"
    
    asyncio.run(_run())

def test_analyze_success_structure():
    """
    Test that successful calls also include uncertainty_notes if missing
    """
    async def _run():
        manager = client.LLMManager()
        mock_client = AsyncMock()
        # Return valid JSON but missing uncertainty_notes
        mock_client.complete.return_value = '{"claims": ["foo"]}'
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            result = await manager.analyze({}, "test")
            
            assert result.get("claims") == ["foo"]
            # Should be injected by the manager
            assert isinstance(result.get("uncertainty_notes"), list)
            assert len(result.get("uncertainty_notes")) == 0
            
    asyncio.run(_run())
