from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CI_RECORD = ROOT / "docs" / "gemini_phase4k_ci_validation_record.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase4k_ci_validation_record_exists():
    assert CI_RECORD.exists()


def test_phase4k_ci_validation_record_states_route_and_remote_state():
    doc = _read(CI_RECORD)

    assert "v2_join_node -> gemini_assist_noop -> schema_validator_node" in doc
    assert "v2_join_node --proceed--> gemini_assist_noop --> schema_validator_node" in doc
    assert "5d8ef76 feat: add disabled gemini workflow no-op route" in doc
    assert "ca9a7da docs: add phase 4k post-push governance checkpoint" in doc
    assert "ca9a7da6fa5d1fa4a4ce56c64fdbd7b12507c181 refs/heads/main" in doc
    assert "rollback/pre-phase4k-minimal-workflow-wiring-2026-05-18" in doc
    assert "ac6f812e1599e122e6a8debc981f90c9d0cb7d45" in doc


def test_phase4k_ci_validation_record_states_validation_results():
    doc = _read(CI_RECORD)

    assert "`6 passed`" in doc
    assert "`422 passed`" in doc
    assert "OK: no live/client/key imports in workflow.py" in doc
    assert "OK: no evidence_analyst route introduced" in doc


def test_phase4k_ci_validation_record_records_ci_unavailable():
    doc = _read(CI_RECORD)

    assert "gh run list --branch main --limit 5" in doc
    assert "zsh:1: command not found: gh" in doc
    assert "Manual GitHub CI review is required" in doc


def test_phase4k_ci_validation_record_prepares_equivalence_tests():
    doc = _read(CI_RECORD)

    assert "disabled output equivalence tests" in doc
    assert "Phase 4K-EQ — Disabled Workflow Output Equivalence Tests" in doc
    assert "protected state keys are unchanged" in doc
    assert "representative disabled workflow outputs are canonically identical" in doc
    assert "no downstream `schema_validator_node` input mutation is introduced" in doc


def test_phase4k_ci_validation_record_preserves_no_live_or_key_boundary():
    doc = _read(CI_RECORD)

    assert "No live Gemini/API-key work is approved" in doc
    assert "live Gemini execution" in doc
    assert "API-key usage" in doc
    assert "no live Gemini" in doc
    assert "no API keys" in doc


def test_phase4k_ci_validation_record_blocks_state_writes_and_forecast_artifacts():
    doc = _read(CI_RECORD)

    assert "No production state mutation is approved" in doc
    assert "No `agent_outputs` write is approved" in doc
    assert "No `Signal`/`HorizonForecast`/`FusionResult` creation is approved" in doc
    assert "production `ForecastState` mutation" in doc
    assert "`agent_outputs` writes" in doc
    assert "`Signal`, `HorizonForecast`, or `FusionResult` creation" in doc


def test_phase4k_ci_validation_record_blocks_unapproved_topology_and_bypass():
    doc = _read(CI_RECORD)

    assert "No `evidence_analyst` route was introduced" in doc
    assert "`evidence_analyst` insertion" in doc
    assert "dirty backup topology copying" in doc
    assert "`ReportWriter` trusted input changes" in doc

    for component in (
        "QuantifierV2",
        "CriticV2",
        "Governor",
        "SchemaValidator",
        "EvidenceDeduper",
        "IndependenceAnalyzer",
        "Librarian",
        "ArbitrationPolicy",
    ):
        assert component in doc
