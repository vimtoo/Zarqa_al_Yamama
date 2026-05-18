"""Test-only helpers for Gemini sidecar artifact schema and path safety."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


PRODUCTION_LIKE_PATH_MARKERS = (
    "final_report",
    "report_writer",
    "ForecastState",
    "agent_outputs",
    "horizon_forecasts",
    "fusion_result",
    "signals",
)


def read_json_artifact(path: str | Path) -> Any:
    """Load a JSON artifact from a test path."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def assert_artifact_under_root(path: str | Path, root: str | Path) -> None:
    """Assert an artifact path resolves under the expected local test root."""
    resolved_path = Path(path).resolve()
    resolved_root = Path(root).resolve()
    assert resolved_path.is_relative_to(resolved_root)


def assert_no_production_like_path_markers(value: str | Path | Mapping[str, Any]) -> None:
    """Assert paths or path-bearing mappings avoid production output markers."""
    if isinstance(value, Mapping):
        for item in value.values():
            if isinstance(item, (str, Path, Mapping)):
                assert_no_production_like_path_markers(item)
        return

    text = str(value)
    lowered = text.lower()
    for marker in PRODUCTION_LIKE_PATH_MARKERS:
        assert marker.lower() not in lowered


def assert_required_json_keys(payload: Mapping[str, Any], required_keys: Iterable[str]) -> None:
    """Assert stable top-level keys exist in an artifact payload."""
    missing = [key for key in required_keys if key not in payload]
    assert not missing, f"Missing artifact keys: {missing}"
