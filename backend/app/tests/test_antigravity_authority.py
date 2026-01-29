
import os
import sys
from unittest.mock import MagicMock

# Mock httpx to avoid ImportError if not installed
sys.modules["httpx"] = MagicMock()

import pytest
from app.llm import client

def test_no_legacy_prompts_in_client():
    """
    Ensure no legacy prompt strings exist in backend/app/llm/client.py
    """
    client_path = os.path.abspath(client.__file__)
    
    with open(client_path, 'r') as f:
        content = f.read()
        
    forbidden_strings = [
        "Analyze the sentiment of",
        "expert financial and geopolitical analyst",
        "Generate a political studies brief",
        "You are Zarqa al Yamama (زرقاء اليمامة)", # The system prompt template
    ]
    
    for s in forbidden_strings:
        assert s not in content, f"Found forbidden legacy string in client.py: '{s}'"

def test_clients_raise_runtime_error_on_analyze():
    """
    Ensure calling analyze() directly on clients raises RuntimeError
    """
    or_client = client.OpenRouterClient()
    ds_client = client.DeepSeekClient()
    
    with pytest.raises(RuntimeError, match="OpenRouterClient.analyze\(\) is disabled"):
        import asyncio
        asyncio.run(or_client.analyze({}, "test"))
        
    with pytest.raises(RuntimeError, match="DeepSeekClient.analyze\(\) is disabled"):
        import asyncio
        asyncio.run(ds_client.analyze({}, "test"))
