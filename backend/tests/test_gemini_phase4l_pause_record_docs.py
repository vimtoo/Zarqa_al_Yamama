from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAUSE_RECORD = ROOT / "docs" / "gemini_phase4l_pause_record.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase4l_pause_record_exists():
    assert PAUSE_RECORD.exists()


def test_phase4l_pause_record_states_checkpoint_and_status():
    doc = _read(PAUSE_RECORD)

    assert "checkpoint/gemini-sidecar-phase4l-complete-2026-05-18" in doc
    assert "631e5a7 docs: add final gemini sidecar hardening summary" in doc
    assert "Gemini remains sidecar-only" in doc
    assert "`workflow.py` remains unwired" in doc
    assert "Phase 4K remains NOT APPROVED" in doc
    assert "No live Gemini/API-key work is approved" in doc


def test_phase4l_pause_record_contains_allowed_next_options():
    doc = _read(PAUSE_RECORD)

    assert "Option A" in doc
    assert "Option B" in doc
    assert "Option C" in doc


def test_phase4l_pause_record_contains_only_eligible_phase4k_route():
    doc = _read(PAUSE_RECORD)

    assert "v2_join_node -> gemini_assist_noop -> schema_validator_node" in doc


def test_phase4l_pause_record_blocks_protected_writes_and_forecast_artifacts():
    doc = _read(PAUSE_RECORD)

    assert "`agent_outputs` writes" in doc
    assert "`ForecastState` mutation" in doc
    assert "`Signal`/`HorizonForecast`/`FusionResult` creation" in doc
    assert "`ReportWriter` trusted input changes" in doc
