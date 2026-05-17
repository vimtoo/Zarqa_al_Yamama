from __future__ import annotations

import logging
import os
import sys
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.integrations.gemini_deep_research.client import GeminiDeepResearchClient
from app.integrations.gemini_deep_research.models import GeminiDeepResearchStatus
from app.integrations.gemini_deep_research.prompts import build_deep_research_prompt
from app.integrations.gemini_deep_research.storage import load_raw_result, save_raw_result


VALID_FAKE_GEMINI_API_KEY = "test_valid_gemini_key_1234567890abcdef"


@pytest.mark.asyncio
async def test_mock_research_completes_successfully(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("SEER_USE_GEMINI_DEEP_RESEARCH", "0")

    client = GeminiDeepResearchClient()
    result = await client.run_research("Research Gulf energy risk.", mock=True)

    assert result.status == GeminiDeepResearchStatus.COMPLETED
    assert result.raw_report
    assert result.metadata["mock"] is True
    assert result.interaction_id.startswith("mock-")


@pytest.mark.asyncio
async def test_client_disabled_by_default_does_not_call_external_api(monkeypatch):
    monkeypatch.delenv("SEER_USE_GEMINI_DEEP_RESEARCH", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", VALID_FAKE_GEMINI_API_KEY)

    client = GeminiDeepResearchClient()
    client._post_interaction = AsyncMock(return_value={"id": "should-not-call"})

    result = await client.run_research("Research something.")

    assert result.status == GeminiDeepResearchStatus.DISABLED
    assert result.error_type == "disabled"
    client._post_interaction.assert_not_called()


@pytest.mark.asyncio
async def test_missing_gemini_api_key_returns_structured_error(monkeypatch):
    monkeypatch.setenv("SEER_USE_GEMINI_DEEP_RESEARCH", "1")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    client = GeminiDeepResearchClient()
    result = await client.run_research("Research something.")

    assert result.status == GeminiDeepResearchStatus.FAILED
    assert result.error_type == "missing_api_key"
    assert result.error is not None
    assert result.error.retryable is False


@pytest.mark.asyncio
async def test_timeout_returns_structured_timeout_result(monkeypatch):
    monkeypatch.setenv("SEER_USE_GEMINI_DEEP_RESEARCH", "1")
    monkeypatch.setenv("GEMINI_API_KEY", VALID_FAKE_GEMINI_API_KEY)

    client = GeminiDeepResearchClient(poll_interval_seconds=0)
    client._get_interaction = AsyncMock(return_value={"id": "abc123", "status": "running"})

    result = await client.poll_interaction("abc123", timeout_seconds=1)

    assert result.status == GeminiDeepResearchStatus.TIMEOUT
    assert result.error_type == "timeout"
    assert result.interaction_id == "abc123"


@pytest.mark.asyncio
async def test_failed_interaction_returns_structured_failed_result(monkeypatch):
    monkeypatch.setenv("SEER_USE_GEMINI_DEEP_RESEARCH", "1")
    monkeypatch.setenv("GEMINI_API_KEY", VALID_FAKE_GEMINI_API_KEY)

    client = GeminiDeepResearchClient(poll_interval_seconds=0)
    client._post_interaction = AsyncMock(return_value={"id": "abc123", "status": "running"})
    client._get_interaction = AsyncMock(return_value={
        "id": "abc123",
        "status": "failed",
        "error": {"message": "research failed safely"},
    })

    result = await client.run_research("Research something.", timeout_seconds=3)

    assert result.status == GeminiDeepResearchStatus.FAILED
    assert result.error_type == "interaction_failed"
    assert "research failed safely" in result.error_message


def test_storage_saves_and_loads_raw_result(tmp_path, monkeypatch):
    monkeypatch.setenv("SEER_GEMINI_EVIDENCE_PACK_DIR", str(tmp_path))

    result = GeminiDeepResearchClient()
    # Use the mock method through the event loop-free model construction path.
    from app.integrations.gemini_deep_research.models import GeminiDeepResearchResult

    raw = GeminiDeepResearchResult(
        interaction_id="mock-storage",
        status=GeminiDeepResearchStatus.COMPLETED,
        raw_report="stored report",
    )
    path = save_raw_result(raw)
    loaded = load_raw_result(raw.run_id)

    assert path.exists()
    assert loaded.run_id == raw.run_id
    assert loaded.raw_report == "stored report"
    assert result is not None


def test_prompt_builder_includes_no_probability_instruction():
    prompt = build_deep_research_prompt("Will tensions escalate?")

    assert "Do not generate final probabilities" in prompt
    assert "forecast probabilities" in prompt
    assert "probability bands" in prompt


def test_prompt_builder_includes_citation_and_source_instructions():
    prompt = build_deep_research_prompt("Research oil markets.")

    assert "cite each source" in prompt
    assert "URLs" in prompt
    assert "Do not fabricate citations" in prompt


@pytest.mark.asyncio
async def test_api_key_not_in_logs_or_serialized_output(monkeypatch, caplog):
    secret = "AIza_secret_test_value"
    monkeypatch.setenv("SEER_USE_GEMINI_DEEP_RESEARCH", "1")
    monkeypatch.setenv("GEMINI_API_KEY", secret)

    client = GeminiDeepResearchClient()
    client._post_interaction = AsyncMock(side_effect=RuntimeError(f"bad key {secret}"))

    with caplog.at_level(logging.ERROR):
        result = await client.run_research("Research something.")

    serialized = result.model_dump_json()
    assert secret not in caplog.text
    assert secret not in serialized
    assert "[REDACTED_API_KEY]" in result.error_message
