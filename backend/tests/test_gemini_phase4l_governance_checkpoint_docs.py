from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_DOC = ROOT / "docs" / "gemini_phase4l_governance_checkpoint_and_risk_register.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase4l_governance_checkpoint_doc_exists():
    assert CHECKPOINT_DOC.exists()


def test_phase4l_checkpoint_states_core_governance_status():
    doc = _read(CHECKPOINT_DOC)

    assert "`workflow.py` remains unwired" in doc
    assert "Phase 4K remains NOT APPROVED" in doc
    assert "No live Gemini execution or API-key work is approved" in doc
    assert "`1bdf69e test: harden gemini sidecar artifact safety`" in doc


def test_phase4l_checkpoint_includes_all_phase4l_commit_hashes():
    doc = _read(CHECKPOINT_DOC)

    for commit in ("e6870d3", "6d9069a", "291ede9", "1bdf69e"):
        assert commit in doc


def test_phase4l_checkpoint_includes_risk_ids_r1_through_r12():
    doc = _read(CHECKPOINT_DOC)

    for index in range(1, 13):
        assert f"| R{index} |" in doc


def test_phase4l_checkpoint_recommends_next_stage():
    doc = _read(CHECKPOINT_DOC)

    assert "Phase 4L-N — Citation Quality and Unsupported-Claim Review Hardening" in doc


def test_phase4l_checkpoint_go_no_go_recommendations_are_locked():
    doc = _read(CHECKPOINT_DOC)

    assert "GO for further sidecar-only hardening" in doc
    assert "NO-GO for Phase 4K implementation unless Qusai explicitly approves Option A" in doc
    assert "NO-GO for live Gemini unless a separate explicit live-review approval package is completed" in doc


def test_phase4l_checkpoint_prohibits_protected_writes_and_forecast_artifacts():
    doc = _read(CHECKPOINT_DOC)

    assert "no `agent_outputs` write" in doc
    assert "no `ForecastState` production mutation" in doc
    assert "no `Signal`, `HorizonForecast`, or `FusionResult` creation" in doc
