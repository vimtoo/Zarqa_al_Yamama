"""Isolated Gemini Deep Research Interactions API client.

Phase 1 boundaries:
- No workflow integration.
- No production state mutation.
- No writes to agent_outputs.
- No TheSeer EvidenceItem, ClaimItem, Signal, HorizonForecast, or FusionResult.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from app.integrations.gemini_deep_research.models import (
    GeminiDeepResearchRequest,
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
)
from app.integrations.gemini_deep_research.prompts import build_deep_research_prompt
from app.integrations.gemini_deep_research.key_validation import validate_api_key_for_header

logger = logging.getLogger(__name__)


DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
INTERACTIONS_PATH = "/interactions"
API_REVISION = "2026-05-20"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _truthy(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _safe_int(value: Optional[str], default: int) -> int:
    try:
        parsed = int(str(value))
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


class GeminiDeepResearchClient:
    """Small defensive wrapper around the Gemini Interactions API."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        poll_interval_seconds: float = 10.0,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.poll_interval_seconds = poll_interval_seconds

    def is_enabled(self) -> bool:
        """Return whether Deep Research is explicitly enabled."""
        return _truthy(os.getenv("SEER_USE_GEMINI_DEEP_RESEARCH", "0"))

    def get_default_model(self) -> str:
        return os.getenv("SEER_GEMINI_MODEL", "deep-research-preview-04-2026")

    def get_max_model(self) -> str:
        return os.getenv("SEER_GEMINI_MAX_MODEL", "deep-research-max-preview-04-2026")

    def get_mode(self) -> str:
        return os.getenv("SEER_GEMINI_MODE", "shadow")

    def get_default_timeout(self) -> int:
        return _safe_int(os.getenv("SEER_GEMINI_TIMEOUT_SECONDS"), 900)

    def should_write_evidence_packs(self) -> bool:
        return _truthy(os.getenv("SEER_GEMINI_WRITE_EVIDENCE_PACKS", "1"))

    def get_evidence_pack_dir(self) -> str:
        return os.getenv("SEER_GEMINI_EVIDENCE_PACK_DIR", "data/research/evidence_packs")

    def _headers(self) -> Dict[str, str]:
        # Never log this return value. It contains the API key.
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key or "",
            "Api-Revision": API_REVISION,
        }

    def _create_url(self) -> str:
        return f"{self.base_url}{INTERACTIONS_PATH}"

    def _get_url(self, interaction_id: str) -> str:
        return f"{self.base_url}{INTERACTIONS_PATH}/{interaction_id}"

    def _build_create_payload(self, request: GeminiDeepResearchRequest) -> Dict[str, Any]:
        agent_config: Dict[str, Any] = {"type": "deep-research"}
        if request.collaborative_planning:
            agent_config["thinking_summaries"] = "auto"
            agent_config["collaborative_planning"] = True
        if request.visualization:
            agent_config["visualization"] = "auto"

        payload: Dict[str, Any] = {
            "input": request.prompt,
            "agent": request.model,
            "background": True,
        }
        if agent_config != {"type": "deep-research"}:
            payload["agent_config"] = agent_config
        return payload

    async def _post_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - httpx exists in this app
            raise RuntimeError("httpx is required for live Gemini Deep Research calls") from exc

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self._create_url(),
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def _get_interaction(self, interaction_id: str) -> Dict[str, Any]:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - httpx exists in this app
            raise RuntimeError("httpx is required for live Gemini Deep Research calls") from exc

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self._get_url(interaction_id),
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    def _sanitize_error(self, message: Any) -> str:
        safe = str(message or "")
        if self.api_key:
            safe = safe.replace(self.api_key, "[REDACTED_API_KEY]")
        return safe

    def _extract_interaction_id(self, payload: Dict[str, Any]) -> Optional[str]:
        for key in ("id", "name", "interaction_id", "interactionId"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value.rsplit("/", 1)[-1]
        interaction = payload.get("interaction")
        if isinstance(interaction, dict):
            return self._extract_interaction_id(interaction)
        return None

    def _extract_status(self, payload: Dict[str, Any]) -> str:
        status = payload.get("status") or payload.get("state")
        if isinstance(status, dict):
            status = status.get("state") or status.get("name")
        return str(status or "running").lower()

    def _extract_report(self, payload: Dict[str, Any]) -> Optional[str]:
        for key in ("raw_report", "report", "output_text", "text"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value

        steps = payload.get("steps")
        if isinstance(steps, list):
            for step in reversed(steps):
                if not isinstance(step, dict):
                    continue
                content = step.get("content")
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and isinstance(item.get("text"), str):
                            return item["text"]
                if isinstance(content, str):
                    return content
        return None

    def _extract_error_message(self, payload: Dict[str, Any]) -> Optional[str]:
        error = payload.get("error")
        if isinstance(error, dict):
            return self._sanitize_error(
                error.get("message") or error.get("error_message") or error
            )
        if isinstance(error, str):
            return self._sanitize_error(error)
        return None

    def _extract_citations(self, payload: Dict[str, Any]) -> list[Dict[str, Any]]:
        citations = payload.get("citations")
        if isinstance(citations, list):
            return [c for c in citations if isinstance(c, dict)]

        metadata = payload.get("metadata") or {}
        if isinstance(metadata, dict):
            for key in ("citations", "sources"):
                value = metadata.get(key)
                if isinstance(value, list):
                    return [c for c in value if isinstance(c, dict)]
        return []

    def _extract_usage(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for key in ("usage", "usage_metadata", "usageMetadata"):
            value = payload.get(key)
            if isinstance(value, dict):
                return value
        return None

    def _extract_cost(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        value = payload.get("cost") or payload.get("cost_metadata") or payload.get("costMetadata")
        return value if isinstance(value, dict) else None

    async def create_interaction(
        self,
        request: GeminiDeepResearchRequest,
    ) -> GeminiDeepResearchResult:
        """Create a background Deep Research interaction."""
        if not self.is_enabled():
            return GeminiDeepResearchResult.from_error(
                run_id=request.run_id,
                model=request.model,
                mode=request.mode,
                prompt=request.prompt,
                status=GeminiDeepResearchStatus.DISABLED,
                error_type="disabled",
                error_message="Gemini Deep Research is disabled by SEER_USE_GEMINI_DEEP_RESEARCH.",
                timeout_seconds=request.timeout_seconds,
                retryable=False,
            )

        if not self.api_key:
            return GeminiDeepResearchResult.from_error(
                run_id=request.run_id,
                model=request.model,
                mode=request.mode,
                prompt=request.prompt,
                error_type="missing_api_key",
                error_message="GEMINI_API_KEY is not configured.",
                timeout_seconds=request.timeout_seconds,
                retryable=False,
            )

        # Phase 4Z-C: Fail-closed key/header validation before any HTTP call.
        _kv = validate_api_key_for_header(self.api_key)
        if not _kv.ok:
            logger.error(
                "Gemini Deep Research create_interaction blocked: INVALID_API_KEY_HEADER_VALUE "
                "reason_code=%s",
                _kv.reason_code,
            )
            return GeminiDeepResearchResult.from_error(
                run_id=request.run_id,
                model=request.model,
                mode=request.mode,
                prompt=request.prompt,
                error_type="INVALID_API_KEY_HEADER_VALUE",
                error_message=(
                    f"GEMINI_API_KEY_VALIDATION_FAILED: {_kv.safe_message} "
                    f"(reason_code={_kv.reason_code})"
                ),
                timeout_seconds=request.timeout_seconds,
                retryable=False,
            )

        try:
            payload = self._build_create_payload(request)
            raw = await self._post_interaction(payload)
            interaction_id = self._extract_interaction_id(raw)
            if not interaction_id:
                return GeminiDeepResearchResult.from_error(
                    run_id=request.run_id,
                    model=request.model,
                    mode=request.mode,
                    prompt=request.prompt,
                    raw_response=raw,
                    error_type="missing_interaction_id",
                    error_message="Gemini Interactions API response did not include an interaction ID.",
                    timeout_seconds=request.timeout_seconds,
                )

            return GeminiDeepResearchResult(
                run_id=request.run_id,
                interaction_id=interaction_id,
                model=request.model,
                mode=request.mode,
                prompt=request.prompt,
                status=GeminiDeepResearchStatus.RUNNING,
                created_at=request.created_at,
                started_at=_utc_now(),
                timeout_seconds=request.timeout_seconds,
                raw_response=raw,
                metadata={"api_revision": API_REVISION},
            )
        except Exception as exc:  # noqa: BLE001 - API preview failures are returned structurally
            safe_message = self._sanitize_error(exc)
            logger.error("Gemini Deep Research create_interaction failed: %s", safe_message)
            return GeminiDeepResearchResult.from_error(
                run_id=request.run_id,
                model=request.model,
                mode=request.mode,
                prompt=request.prompt,
                error_type=exc.__class__.__name__,
                error_message=safe_message,
                timeout_seconds=request.timeout_seconds,
            )

    async def poll_interaction(
        self,
        interaction_id: str,
        timeout_seconds: Optional[int] = None,
    ) -> GeminiDeepResearchResult:
        """Poll a background interaction until completion, failure, or timeout."""
        timeout = timeout_seconds or self.get_default_timeout()
        deadline = time.monotonic() + timeout
        model = self.get_default_model()
        mode = self.get_mode()
        run_id = str(uuid4())

        if not self.is_enabled():
            return GeminiDeepResearchResult.from_error(
                run_id=run_id,
                interaction_id=interaction_id,
                model=model,
                mode=mode,
                status=GeminiDeepResearchStatus.DISABLED,
                error_type="disabled",
                error_message="Gemini Deep Research is disabled by SEER_USE_GEMINI_DEEP_RESEARCH.",
                timeout_seconds=timeout,
                retryable=False,
            )

        if not self.api_key:
            return GeminiDeepResearchResult.from_error(
                run_id=run_id,
                interaction_id=interaction_id,
                model=model,
                mode=mode,
                error_type="missing_api_key",
                error_message="GEMINI_API_KEY is not configured.",
                timeout_seconds=timeout,
                retryable=False,
            )

        # Phase 4Z-C: Fail-closed key/header validation before any HTTP call.
        _kv = validate_api_key_for_header(self.api_key)
        if not _kv.ok:
            logger.error(
                "Gemini Deep Research poll_interaction blocked: INVALID_API_KEY_HEADER_VALUE "
                "reason_code=%s",
                _kv.reason_code,
            )
            return GeminiDeepResearchResult.from_error(
                run_id=run_id,
                interaction_id=interaction_id,
                model=model,
                mode=mode,
                error_type="INVALID_API_KEY_HEADER_VALUE",
                error_message=(
                    f"GEMINI_API_KEY_VALIDATION_FAILED: {_kv.safe_message} "
                    f"(reason_code={_kv.reason_code})"
                ),
                timeout_seconds=timeout,
                retryable=False,
            )

        last_raw: Optional[Dict[str, Any]] = None
        while time.monotonic() < deadline:
            try:
                raw = await self._get_interaction(interaction_id)
                last_raw = raw
                status = self._extract_status(raw)
                if status == "completed":
                    return GeminiDeepResearchResult(
                        run_id=run_id,
                        interaction_id=interaction_id,
                        model=model,
                        mode=mode,
                        status=GeminiDeepResearchStatus.COMPLETED,
                        completed_at=_utc_now(),
                        timeout_seconds=timeout,
                        raw_response=raw,
                        raw_report=self._extract_report(raw),
                        citations=self._extract_citations(raw),
                        usage=self._extract_usage(raw),
                        cost=self._extract_cost(raw),
                        metadata={"api_revision": API_REVISION},
                    )
                if status == "failed":
                    message = self._extract_error_message(raw) or "Gemini Deep Research interaction failed."
                    return GeminiDeepResearchResult.from_error(
                        run_id=run_id,
                        interaction_id=interaction_id,
                        model=model,
                        mode=mode,
                        status=GeminiDeepResearchStatus.FAILED,
                        raw_response=raw,
                        error_type="interaction_failed",
                        error_message=message,
                        timeout_seconds=timeout,
                    )
            except Exception as exc:  # noqa: BLE001
                safe_message = self._sanitize_error(exc)
                logger.error("Gemini Deep Research poll_interaction failed: %s", safe_message)
                return GeminiDeepResearchResult.from_error(
                    run_id=run_id,
                    interaction_id=interaction_id,
                    model=model,
                    mode=mode,
                    error_type=exc.__class__.__name__,
                    error_message=safe_message,
                    timeout_seconds=timeout,
                    raw_response=last_raw,
                )

            await asyncio.sleep(max(0.0, self.poll_interval_seconds))

        return GeminiDeepResearchResult.from_error(
            run_id=run_id,
            interaction_id=interaction_id,
            model=model,
            mode=mode,
            status=GeminiDeepResearchStatus.TIMEOUT,
            raw_response=last_raw,
            error_type="timeout",
            error_message=f"Gemini Deep Research interaction timed out after {timeout} seconds.",
            timeout_seconds=timeout,
            metadata={"api_revision": API_REVISION},
        )

    async def run_research(
        self,
        prompt: str,
        model: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        mock: bool = False,
    ) -> GeminiDeepResearchResult:
        """Create and poll a Deep Research interaction or return a mock result."""
        if mock:
            return await self.run_research_mock(prompt, model=model)

        selected_model = model or self.get_default_model()
        timeout = timeout_seconds or self.get_default_timeout()
        request = GeminiDeepResearchRequest(
            prompt=prompt,
            model=selected_model,
            mode=self.get_mode(),
            timeout_seconds=timeout,
            collaborative_planning=_truthy(os.getenv("SEER_GEMINI_ENABLE_COLLABORATIVE_PLANNING", "0")),
            visualization=_truthy(os.getenv("SEER_GEMINI_ENABLE_VISUALIZATION", "0")),
        )

        created = await self.create_interaction(request)
        if created.status != GeminiDeepResearchStatus.RUNNING or not created.interaction_id:
            return created

        polled = await self.poll_interaction(created.interaction_id, timeout_seconds=timeout)
        return polled.model_copy(update={
            "run_id": request.run_id,
            "model": selected_model,
            "mode": request.mode,
            "prompt": prompt,
            "started_at": created.started_at,
            "created_at": request.created_at,
        })

    async def run_research_mock(
        self,
        prompt: str,
        model: Optional[str] = None,
    ) -> GeminiDeepResearchResult:
        """Return a deterministic mock result without external API calls."""
        selected_model = model or self.get_default_model()
        safe_prompt = build_deep_research_prompt(prompt)
        run_id = str(uuid4())
        raw_report = (
            "# Mock Gemini Deep Research Report\n\n"
            "## Sources\n"
            "- Mock source: https://example.com/research\n\n"
            "## Evidence-Backed Findings\n"
            "- This is a mocked Phase 1 result for client and storage tests.\n\n"
            "## Contradictions\n"
            "- None identified in mock mode.\n\n"
            "## Uncertainty\n"
            "- Mock mode does not access live sources.\n"
        )
        return GeminiDeepResearchResult(
            run_id=run_id,
            interaction_id=f"mock-{run_id}",
            model=selected_model,
            mode=self.get_mode(),
            prompt=safe_prompt,
            status=GeminiDeepResearchStatus.COMPLETED,
            created_at=_utc_now(),
            started_at=_utc_now(),
            completed_at=_utc_now(),
            timeout_seconds=self.get_default_timeout(),
            raw_response={
                "id": f"mock-{run_id}",
                "status": "completed",
                "mock": True,
            },
            raw_report=raw_report,
            citations=[{
                "title": "Mock source",
                "url": "https://example.com/research",
            }],
            metadata={
                "mock": True,
                "phase": "phase_1_client_wrapper_only",
            },
        )
