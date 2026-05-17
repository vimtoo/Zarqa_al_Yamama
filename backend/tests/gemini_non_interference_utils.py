"""Deterministic fixture utilities for Gemini non-interference tests.

These helpers are test-only. They do not run TheSeer's workflow, do not call
Gemini, and do not import production graph or agent modules.
"""

from __future__ import annotations

import dataclasses
import difflib
import json
import re
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence, Set


REDACTED = "[REDACTED]"

SENSITIVE_KEY_PARTS = (
    "key",
    "token",
    "secret",
    "password",
    "credential",
    "api",
)

DEFAULT_NONDETERMINISTIC_EXCLUSIONS: Set[str] = {
    "request_id",
    "run_id",
    "timestamp",
    "timestamps",
    "created_at",
    "updated_at",
    "retrieved_at",
    "generated_at",
    "completed_at",
    "started_at",
    "processing_time_ms",
    "duration_ms",
    "node_timing_events",
    "wall_clock",
    "elapsed",
    "report_filename",
    "uuid",
}

STRICT_NONDETERMINISTIC_EXCLUSIONS: Set[str] = set()

PROTECTED_STATE_KEYS: Set[str] = {
    "agent_outputs",
    "signals",
    "horizon_forecasts",
    "fusion_result",
    "fusion_result_v2",
    "final_report",
    "executive_summary",
    "report_path",
    "governor_result",
    "critic_result",
    "quantifier_result",
    "deduped_evidence",
    "evidence_clusters",
    "independence_summary",
    "qualitative_forecast",
    "qualitative_forecast_label",
}

GEMINI_STATE_KEYS: Set[str] = {
    "gemini_assist_review",
    "gemini_deep_research",
    "gemini_evidence_pack",
    "gemini_shadow_run",
    "gemini_assist_trial",
    "gemini_raw_result",
}

GEMINI_AGENT_OUTPUT_KEYS: Set[str] = {
    "gemini_deep_research",
    "gemini",
    "gemini_assist",
    "gemini_assist_node",
}


def build_default_exclusions() -> Set[str]:
    """Return default observability-only and nondeterministic exclusions."""
    return set(DEFAULT_NONDETERMINISTIC_EXCLUSIONS)


def build_strict_exclusions() -> Set[str]:
    """Return an empty exclusion set for strict byte-for-byte comparisons."""
    return set(STRICT_NONDETERMINISTIC_EXCLUSIONS)


def canonical_json_dump(value: Any, exclusions: Optional[Iterable[str]] = None) -> str:
    """Return a deterministic JSON string for a value."""
    canonical = canonicalize_value(value, exclusions=exclusions)
    return json.dumps(
        canonical,
        ensure_ascii=True,
        sort_keys=True,
        indent=2,
        separators=(",", ": "),
    )


def canonicalize_value(
    value: Any,
    exclusions: Optional[Iterable[str]] = None,
    path: str = "",
) -> Any:
    """Canonicalize common Python/Pydantic/dataclass values for stable comparison."""
    exclusion_set = _normalize_exclusions(exclusions)

    if is_nondeterministic_path(path, exclusion_set):
        return None

    if hasattr(value, "model_dump") and callable(value.model_dump):
        value = value.model_dump(mode="json")
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        value = dataclasses.asdict(value)
    elif isinstance(value, Enum):
        return value.value
    elif isinstance(value, datetime):
        return normalize_datetime(value)
    elif isinstance(value, date):
        return value.isoformat()
    elif isinstance(value, Path):
        return normalize_path_string(str(value))
    elif isinstance(value, set):
        return sorted(
            [canonicalize_value(item, exclusions=exclusion_set, path=path) for item in value],
            key=_stable_sort_key,
        )
    elif isinstance(value, tuple):
        return [canonicalize_value(item, exclusions=exclusion_set, path=f"{path}[]") for item in value]

    if isinstance(value, Mapping):
        canonical_dict: dict[str, Any] = {}
        for raw_key in sorted(value.keys(), key=lambda item: str(item)):
            key = str(raw_key)
            child_path = _join_path(path, key)
            if is_nondeterministic_path(child_path, exclusion_set):
                continue
            if _is_sensitive_key(key):
                canonical_dict[key] = REDACTED
                continue
            canonical_dict[key] = canonicalize_value(
                value[raw_key],
                exclusions=exclusion_set,
                path=child_path,
            )
        return canonical_dict

    if isinstance(value, list):
        return [
            canonicalize_value(item, exclusions=exclusion_set, path=f"{path}[]")
            for item in value
        ]

    if isinstance(value, str):
        return _normalize_string(value)

    return value


def canonicalize_state(
    state: Mapping[str, Any],
    exclusions: Optional[Iterable[str]] = None,
) -> dict:
    """Canonicalize a ForecastState-like mapping for deterministic comparison."""
    canonical = canonicalize_value(state, exclusions=exclusions)
    if not isinstance(canonical, dict):
        raise TypeError("canonicalize_state expects a mapping-like state.")
    return canonical


def canonicalize_report(text: str) -> str:
    """Normalize markdown/report text without removing substantive content."""
    normalized = str(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def remove_nondeterministic_fields(value: Any, exclusions: Iterable[str]) -> Any:
    """Return value with approved nondeterministic fields removed."""
    return canonicalize_value(value, exclusions=exclusions)


def assert_canonical_equal(
    left: Any,
    right: Any,
    exclusions: Optional[Iterable[str]] = None,
    label: str = "",
) -> None:
    """Assert two values are canonically equal, with a useful diff on failure."""
    left_dump = canonical_json_dump(left, exclusions=exclusions)
    right_dump = canonical_json_dump(right, exclusions=exclusions)
    if left_dump != right_dump:
        raise AssertionError(diff_canonical(left, right, exclusions=exclusions, label=label))


def diff_canonical(
    left: Any,
    right: Any,
    exclusions: Optional[Iterable[str]] = None,
    label: str = "",
) -> str:
    """Return a unified diff of canonical JSON strings."""
    left_dump = canonical_json_dump(left, exclusions=exclusions)
    right_dump = canonical_json_dump(right, exclusions=exclusions)
    heading = f"Canonical diff for {label}" if label else "Canonical diff"
    if left_dump == right_dump:
        return f"{heading}: values match."
    first_path = _first_difference_path(
        json.loads(left_dump),
        json.loads(right_dump),
    )
    diff = "\n".join(
        difflib.unified_diff(
            left_dump.splitlines(),
            right_dump.splitlines(),
            fromfile="left",
            tofile="right",
            lineterm="",
        )
    )
    return f"{heading}: first differing path: {first_path}\n{diff}"


def protected_state_keys() -> Set[str]:
    """Return ForecastState keys that disabled Gemini tests must protect."""
    return set(PROTECTED_STATE_KEYS)


def assert_protected_keys_unchanged(before: Mapping[str, Any], after: Mapping[str, Any]) -> None:
    """Assert protected keys have identical presence and canonical values."""
    missing = object()
    for key in sorted(PROTECTED_STATE_KEYS):
        before_value = before.get(key, missing)
        after_value = after.get(key, missing)
        if before_value is missing and after_value is missing:
            continue
        if before_value is missing:
            raise AssertionError(f"Protected key added: {key}")
        if after_value is missing:
            raise AssertionError(f"Protected key removed: {key}")
        try:
            assert_canonical_equal(before_value, after_value, label=f"protected key {key}")
        except AssertionError as exc:
            raise AssertionError(f"Protected key changed: {key}\n{exc}") from exc


def capture_artifact(path: Path | str, value: Any, exclusions: Optional[Iterable[str]] = None) -> None:
    """Write a deterministic JSON fixture artifact."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonical_json_dump(value, exclusions=exclusions), encoding="utf-8")


def load_artifact(path: Path | str) -> Any:
    """Load a JSON fixture artifact."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def capture_report_artifact(path: Path | str, text: str) -> None:
    """Write a normalized report fixture artifact."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonicalize_report(text), encoding="utf-8")


def load_report_artifact(path: Path | str) -> str:
    """Load and normalize a report fixture artifact."""
    return canonicalize_report(Path(path).read_text(encoding="utf-8"))


def normalize_path_string(value: str) -> str:
    """Normalize local path strings for deterministic fixture comparison."""
    normalized = str(value).replace("\\", "/")
    while "//" in normalized and not normalized.startswith("http://") and not normalized.startswith("https://"):
        normalized = normalized.replace("//", "/")
    return normalized


def normalize_datetime(value: datetime) -> str:
    """Return an ISO-8601 datetime string with stable UTC handling."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def is_nondeterministic_path(path: str, exclusions: Optional[Iterable[str]]) -> bool:
    """Return whether path/key matches an approved nondeterministic exclusion."""
    if not exclusions:
        return False
    normalized_path = str(path or "").strip().lower()
    key = normalized_path.split(".")[-1].replace("[]", "")
    for exclusion in _normalize_exclusions(exclusions):
        if not exclusion:
            continue
        if exclusion == normalized_path or exclusion == key:
            return True
        if exclusion.startswith("*.") and normalized_path.endswith(exclusion[1:]):
            return True
        if exclusion.endswith(".*") and normalized_path.startswith(exclusion[:-2]):
            return True
        if "*" in exclusion:
            prefix, _, suffix = exclusion.partition("*")
            if normalized_path.startswith(prefix) and normalized_path.endswith(suffix):
                return True
    return False


def summarize_state_keys(state: Mapping[str, Any]) -> dict:
    """Return a deterministic summary of state key presence for debugging."""
    return {
        "keys": sorted(str(key) for key in state.keys()),
        "protected_keys_present": sorted(key for key in PROTECTED_STATE_KEYS if key in state),
        "gemini_keys_present": sorted(key for key in GEMINI_STATE_KEYS if key in state),
        "agent_output_count": len(state.get("agent_outputs", {}) or {}),
    }


def assert_no_gemini_keys(state: Mapping[str, Any]) -> None:
    """Assert disabled-mode state has no Gemini-specific top-level keys."""
    present = sorted(key for key in GEMINI_STATE_KEYS if key in state)
    if present:
        raise AssertionError(f"Unexpected Gemini state keys present: {present}")


def assert_no_agent_output_for_gemini(state: Mapping[str, Any]) -> None:
    """Assert disabled-mode state has no Gemini agent output entry."""
    agent_outputs = state.get("agent_outputs", {}) or {}
    if not isinstance(agent_outputs, Mapping):
        return
    present = sorted(
        key
        for key in agent_outputs.keys()
        if str(key).strip().lower() in GEMINI_AGENT_OUTPUT_KEYS
        or str(key).strip().lower().startswith("gemini_")
    )
    if present:
        raise AssertionError(f"Unexpected Gemini agent_outputs entries present: {present}")


def _normalize_exclusions(exclusions: Optional[Iterable[str]]) -> Set[str]:
    return {str(item).strip().lower() for item in exclusions or set() if str(item).strip()}


def _join_path(parent: str, key: str) -> str:
    return key if not parent else f"{parent}.{key}"


def _normalize_string(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    if "\n" in normalized:
        normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    return normalize_path_string(normalized) if "\\" in normalized else normalized


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    tokens = [token for token in re.split(r"[^a-z0-9]+", lowered) if token]
    return any(token in SENSITIVE_KEY_PARTS for token in tokens)


def _stable_sort_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def _first_difference_path(left: Any, right: Any, path: str = "$") -> str:
    if type(left) is not type(right):
        return path
    if isinstance(left, dict):
        left_keys = set(left.keys())
        right_keys = set(right.keys())
        if left_keys != right_keys:
            changed = sorted(left_keys ^ right_keys)
            return f"{path}.{changed[0]}" if changed else path
        for key in sorted(left.keys()):
            child_path = _first_difference_path(left[key], right[key], f"{path}.{key}")
            if child_path:
                return child_path
        return ""
    if isinstance(left, list):
        if len(left) != len(right):
            return f"{path}[length]"
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            child_path = _first_difference_path(left_item, right_item, f"{path}[{index}]")
            if child_path:
                return child_path
        return ""
    if left != right:
        return path
    return ""
