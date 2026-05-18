from __future__ import annotations

import logging
import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.integrations.gemini_deep_research.client import GeminiDeepResearchClient
from app.integrations.gemini_deep_research.key_validation import validate_api_key_for_header
from app.integrations.gemini_deep_research.models import (
    GeminiDeepResearchRequest,
    GeminiDeepResearchStatus,
)
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


def test_phase4lg_valid_looking_fake_key_passes_local_header_validation_only():
    result = validate_api_key_for_header(VALID_FAKE_GEMINI_API_KEY)

    assert result.ok is True
    assert result.reason_code == "ok"


@pytest.mark.parametrize(
    ("key", "reason_code"),
    [
        (None, "missing"),
        ("", "empty"),
        ("   ", "whitespace_only"),
        ("test valid key with spaces 1234567890", "contains_space"),
        ("[REDACTED_API_KEY]", "contains_brackets"),
        ("test_valid_key_with_newline_123\n456", "contains_newline"),
        ("test_valid_key_with_control_\x01123456", "contains_control_character"),
        ("placeholder", "placeholder"),
        ("sk-fakeSidecarSecretValueForValidation12345", "unsupported_secret_prefix"),
        ("too-short", "too_short"),
    ],
)
def test_phase4lg_malformed_keys_fail_closed_with_safe_messages(key, reason_code):
    result = validate_api_key_for_header(key)
    serialized = f"{result.reason_code} {result.safe_message}"

    assert result.ok is False
    assert result.reason_code == reason_code
    if key and reason_code != "placeholder":
        assert key not in serialized


@pytest.mark.asyncio
async def test_phase4lg_create_interaction_rejects_malformed_key_before_http(monkeypatch):
    malformed = "sk-fakeSidecarSecretValueForCreate12345"
    monkeypatch.setenv("SEER_USE_GEMINI_DEEP_RESEARCH", "1")
    client = GeminiDeepResearchClient(api_key=malformed)
    client._post_interaction = AsyncMock(return_value={"id": "should-not-call"})
    client._headers = Mock(side_effect=AssertionError("headers must not be constructed"))

    result = await client.create_interaction(
        GeminiDeepResearchRequest(prompt="Research sidecar key handling.")
    )

    assert result.error_type == "INVALID_API_KEY_HEADER_VALUE"
    assert "unsupported_secret_prefix" in result.error_message
    assert malformed not in result.model_dump_json()
    client._post_interaction.assert_not_called()
    client._headers.assert_not_called()


@pytest.mark.asyncio
async def test_phase4lg_poll_interaction_rejects_malformed_key_before_http(monkeypatch):
    malformed = "Authorization: Bearer fakeAuthorizationToken12345"
    monkeypatch.setenv("SEER_USE_GEMINI_DEEP_RESEARCH", "1")
    client = GeminiDeepResearchClient(api_key=malformed)
    client._get_interaction = AsyncMock(return_value={"id": "should-not-call"})
    client._headers = Mock(side_effect=AssertionError("headers must not be constructed"))

    result = await client.poll_interaction("interaction-1", timeout_seconds=1)

    assert result.error_type == "INVALID_API_KEY_HEADER_VALUE"
    assert "contains_space" in result.error_message
    assert malformed not in result.model_dump_json()
    client._get_interaction.assert_not_called()
    client._headers.assert_not_called()


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
