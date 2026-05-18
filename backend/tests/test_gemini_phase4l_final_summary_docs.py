from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUMMARY_DOC = ROOT / "docs" / "gemini_phase4l_final_sidecar_hardening_summary.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase4l_final_summary_doc_exists():
    assert SUMMARY_DOC.exists()


def test_phase4l_final_summary_states_current_safe_status():
    doc = _read(SUMMARY_DOC)

    assert "Gemini remains sidecar-only" in doc
    assert "`workflow.py` remains unwired" in doc
    assert "Phase 4K remains NOT APPROVED" in doc
    assert "No live Gemini/API-key work is approved" in doc
    assert "`314243e test: harden gemini citation quality review`" in doc


def test_phase4l_final_summary_includes_all_phase4l_commit_hashes():
    doc = _read(SUMMARY_DOC)

    for commit in ("e6870d3", "6d9069a", "291ede9", "1bdf69e", "36ad93a", "314243e"):
        assert commit in doc


def test_phase4l_final_summary_contains_decision_options():
    doc = _read(SUMMARY_DOC)

    assert "Option A" in doc
    assert "Option B" in doc
    assert "Option C" in doc


def test_phase4l_final_summary_recommends_pause_unless_more_sidecar_work_requested():
    doc = _read(SUMMARY_DOC)

    assert (
        "Recommended decision: **Option A — Pause Sidecar Hardening**, unless Qusai "
        "wants another non-workflow confidence slice."
        in doc
    )
    assert "Phase 4K implementation remains NO-GO unless Qusai explicitly approves the minimal disabled route" in doc


def test_phase4l_final_summary_contains_only_eligible_phase4k_route():
    doc = _read(SUMMARY_DOC)

    assert "v2_join_node -> gemini_assist_noop -> schema_validator_node" in doc


def test_phase4l_final_summary_prohibits_protected_writes_and_forecast_artifacts():
    doc = _read(SUMMARY_DOC)

    assert "no `agent_outputs` writes" in doc
    assert "no `ForecastState` mutation" in doc
    assert "no `Signal`, `HorizonForecast`, or `FusionResult` creation" in doc
    assert "no `ReportWriter` trusted input changes" in doc
