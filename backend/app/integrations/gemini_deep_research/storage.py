"""Raw result storage for Phase 1 Gemini Deep Research artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.integrations.gemini_deep_research.models import (
    GeminiDeepResearchResult,
    GeminiEvidencePack,
    GeminiEvaluationDecision,
    GeminiShadowRun,
    GeminiShadowRunnerResult,
)


DEFAULT_EVIDENCE_PACK_DIR = "data/research/evidence_packs"
DEFAULT_SHADOW_RUN_DIR = "data/research/gemini_shadow_runs"
DEFAULT_POLICY_REPORT_PATH = "docs/gemini_shadow_evaluation_policy_report.md"
PROHIBITED_ARTIFACT_PATH_PARTS = {
    "agent_outputs",
    "final_report",
    "forecaststate",
    "fusion_result",
    "horizon_forecasts",
    "report_writer",
    "signals",
}


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _project_root() -> Path:
    # storage.py -> gemini_deep_research -> integrations -> app -> backend -> root
    return Path(__file__).resolve().parents[4]


def _configured_dir() -> Path:
    raw = os.getenv("SEER_GEMINI_EVIDENCE_PACK_DIR", DEFAULT_EVIDENCE_PACK_DIR)
    path = Path(raw)
    if path.is_absolute():
        return _validate_sidecar_artifact_path(path)
    return _validate_sidecar_artifact_path(_project_root() / path)


def _configured_shadow_dir() -> Path:
    raw = os.getenv("SEER_GEMINI_SHADOW_RUN_DIR", DEFAULT_SHADOW_RUN_DIR)
    path = Path(raw)
    if path.is_absolute():
        return _validate_sidecar_artifact_path(path)
    return _validate_sidecar_artifact_path(_project_root() / path)


def _shadow_base_dir(output_dir: str | Path | None = None) -> Path:
    if output_dir is None:
        return _configured_shadow_dir()
    path = Path(output_dir)
    if path.is_absolute():
        return _validate_sidecar_artifact_path(path)
    return _validate_sidecar_artifact_path(_project_root() / path)


def _validate_sidecar_artifact_path(path: Path) -> Path:
    """Fail closed on traversal or production-like sidecar artifact paths."""
    raw_parts = [str(part) for part in path.parts]
    if any(part == ".." for part in raw_parts):
        raise ValueError("Gemini sidecar artifact paths must not contain traversal segments.")
    lowered_parts = [part.lower() for part in raw_parts]
    blocked = sorted(
        {
            marker
            for marker in PROHIBITED_ARTIFACT_PATH_PARTS
            for part in lowered_parts
            if marker in part
        }
    )
    if blocked:
        raise ValueError(f"Gemini sidecar artifacts cannot be written under production-like path parts: {blocked}")
    return path


def ensure_evidence_pack_dir() -> Path:
    """Create and return the raw Gemini evidence pack directory."""
    path = _configured_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def evidence_pack_writes_enabled() -> bool:
    """Return whether raw Phase 1 result writes are enabled."""
    return _truthy(os.getenv("SEER_GEMINI_WRITE_EVIDENCE_PACKS", "1"))


def save_raw_result(result: GeminiDeepResearchResult) -> Path:
    """Save raw interaction result JSON outside production forecast outputs."""
    directory = ensure_evidence_pack_dir()
    path = directory / f"{result.run_id}.json"
    if not evidence_pack_writes_enabled():
        return path
    path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return path


def load_raw_result(run_id: str) -> GeminiDeepResearchResult:
    """Load a raw Phase 1 result by run ID."""
    path = ensure_evidence_pack_dir() / f"{run_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return GeminiDeepResearchResult.model_validate(payload)


def ensure_shadow_run_dir() -> Path:
    """Create and return the Phase 3A shadow comparison directory."""
    path = _configured_shadow_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_shadow_run(shadow_run: GeminiShadowRun) -> Path:
    """Save a Gemini shadow comparison JSON artifact outside forecast outputs."""
    directory = ensure_shadow_run_dir()
    path = directory / f"{shadow_run.run_id}.json"
    path.write_text(
        json.dumps(shadow_run.model_dump(mode="json"), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return path


def load_shadow_run(run_id: str) -> GeminiShadowRun:
    """Load a saved Gemini shadow comparison JSON artifact."""
    path = ensure_shadow_run_dir() / f"{run_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return GeminiShadowRun.model_validate(payload)


def save_shadow_report(shadow_run: GeminiShadowRun) -> Path:
    """Save the human-readable Gemini shadow markdown report."""
    from app.integrations.gemini_deep_research.shadow_compare import (  # noqa: PLC0415
        GeminiShadowComparator,
    )

    directory = ensure_shadow_run_dir()
    path = directory / f"{shadow_run.run_id}.md"
    report = GeminiShadowComparator().render_markdown_report(shadow_run)
    path.write_text(report, encoding="utf-8")
    return path


def ensure_shadow_run_artifact_dir(
    run_id: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Create and return the folder for a standalone Phase 3B shadow run."""
    path = _shadow_base_dir(output_dir) / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_raw_result_artifact(
    result: GeminiDeepResearchResult,
    run_id: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Save a Phase 3B raw result artifact in a run-specific folder."""
    path = ensure_shadow_run_artifact_dir(run_id, output_dir) / "raw_result.json"
    path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return path


def save_evidence_pack_artifact(
    pack: GeminiEvidencePack,
    run_id: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Save a Phase 3B normalized evidence pack artifact."""
    path = ensure_shadow_run_artifact_dir(run_id, output_dir) / "evidence_pack.json"
    path.write_text(
        json.dumps(pack.model_dump(mode="json"), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return path


def save_shadow_run_artifact(
    shadow_run: GeminiShadowRun,
    output_dir: str | Path | None = None,
) -> Path:
    """Save a Phase 3B shadow run JSON artifact in a run-specific folder."""
    path = ensure_shadow_run_artifact_dir(shadow_run.run_id, output_dir) / "shadow_run.json"
    path.write_text(
        json.dumps(shadow_run.model_dump(mode="json"), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return path


def save_shadow_report_artifact(
    shadow_run: GeminiShadowRun,
    output_dir: str | Path | None = None,
) -> Path:
    """Save a Phase 3B shadow markdown report in a run-specific folder."""
    from app.integrations.gemini_deep_research.shadow_compare import (  # noqa: PLC0415
        GeminiShadowComparator,
    )

    path = ensure_shadow_run_artifact_dir(shadow_run.run_id, output_dir) / "shadow_report.md"
    path.write_text(
        GeminiShadowComparator().render_markdown_report(shadow_run),
        encoding="utf-8",
    )
    return path


def save_runner_result_artifact(
    result: GeminiShadowRunnerResult,
    run_id: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Save a Phase 3B runner summary in a run-specific folder."""
    path = ensure_shadow_run_artifact_dir(run_id, output_dir) / "runner_result.json"
    path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return path


def load_shadow_runs_from_dir(path: str | Path) -> list[GeminiShadowRun]:
    """Load all valid shadow-run JSON artifacts from a local directory."""
    root = Path(path)
    if not root.exists():
        return []
    candidates = list(root.glob("*.json")) + list(root.glob("*/shadow_run.json"))
    runs: list[GeminiShadowRun] = []
    for candidate in sorted(set(candidates)):
        if candidate.name in {"runner_result.json", "raw_result.json", "evidence_pack.json"}:
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
            runs.append(GeminiShadowRun.model_validate(payload))
        except Exception:
            continue
    return runs


def save_policy_report(
    decision: GeminiEvaluationDecision,
    output_path: str | Path | None = None,
) -> Path:
    """Save a Phase 3C policy report under docs by default."""
    from app.integrations.gemini_deep_research.evaluation_policy import (  # noqa: PLC0415
        GeminiShadowEvaluationPolicy,
    )

    path = Path(output_path) if output_path else _project_root() / DEFAULT_POLICY_REPORT_PATH
    if not path.is_absolute():
        path = _project_root() / path
    path = _validate_sidecar_artifact_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        GeminiShadowEvaluationPolicy().render_policy_report(decision),
        encoding="utf-8",
    )
    return path
