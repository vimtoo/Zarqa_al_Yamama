from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_DOC = ROOT / "docs" / "gemini_phase4k_final_governance_checkpoint.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase4k_final_governance_checkpoint_exists():
    assert CHECKPOINT_DOC.exists()


def test_phase4k_final_governance_checkpoint_records_route_and_remote_state():
    doc = _read(CHECKPOINT_DOC)

    assert "v2_join_node -> gemini_assist_noop -> schema_validator_node" in doc
    assert "v2_join_node --proceed--> gemini_assist_noop --> schema_validator_node" in doc
    assert "8f249b6 test: add disabled gemini output equivalence checks" in doc
    assert "8f249b67dac6ed4ac24e7a7fcf33aed8f1bc5910 refs/heads/main" in doc
    assert "rollback/pre-phase4k-minimal-workflow-wiring-2026-05-18" in doc
    assert "ac6f812e1599e122e6a8debc981f90c9d0cb7d45" in doc


def test_phase4k_final_governance_checkpoint_includes_commit_inventory():
    doc = _read(CHECKPOINT_DOC)

    for commit in (
        "5d8ef76 feat: add disabled gemini workflow no-op route",
        "ca9a7da docs: add phase 4k post-push governance checkpoint",
        "f3c48de docs: add phase 4k ci validation record",
        "702fc74 docs: add disabled gemini output equivalence plan",
        "8f249b6 test: add disabled gemini output equivalence checks",
    ):
        assert commit in doc


def test_phase4k_final_governance_checkpoint_records_validation_results():
    doc = _read(CHECKPOINT_DOC)

    assert "`6 passed`" in doc
    assert "`8 passed`" in doc
    assert "`200 passed`" in doc
    assert "`446 passed`" in doc
    assert "OK: no live/client/key imports in workflow.py" in doc
    assert "OK: no evidence_analyst route introduced" in doc


def test_phase4k_final_governance_checkpoint_records_ci_limitation():
    doc = _read(CHECKPOINT_DOC)

    assert "CI status remains unavailable locally because `gh` is not installed" in doc
    assert "Manual GitHub CI review is required" in doc
    assert "complete manual GitHub CI review for `main`" in doc


def test_phase4k_final_governance_checkpoint_records_equivalence_coverage():
    doc = _read(CHECKPOINT_DOC)

    assert "backend/tests/test_gemini_phase4k_disabled_output_equivalence.py" in doc
    assert "no-op adapter protected-state preservation" in doc
    assert "canonical disabled-state equivalence" in doc
    assert "downstream `schema_validator_node` input equivalence" in doc
    assert "`tmp_path`-only artifact equivalence capture" in doc
    assert "`schema_validator_node` receives equivalent input behind the no-op hop" in doc


def test_phase4k_final_governance_checkpoint_preserves_disabled_no_live_boundary():
    doc = _read(CHECKPOINT_DOC)

    assert "The integration remains disabled/no-op only" in doc
    assert "No live Gemini/API-key work is approved" in doc
    assert "live Gemini execution" in doc
    assert "API-key usage" in doc
    assert "no live Gemini" in doc
    assert "no API keys" in doc


def test_phase4k_final_governance_checkpoint_blocks_state_writes_and_forecast_artifacts():
    doc = _read(CHECKPOINT_DOC)

    assert "No production state mutation is approved" in doc
    assert "No `agent_outputs` write is approved" in doc
    assert "No `Signal`/`HorizonForecast`/`FusionResult` creation is approved" in doc
    assert "production `ForecastState` mutation" in doc
    assert "`agent_outputs` writes" in doc
    assert "`Signal` creation" in doc
    assert "`HorizonForecast` creation" in doc
    assert "`FusionResult` creation" in doc


def test_phase4k_final_governance_checkpoint_blocks_topology_and_bypass_changes():
    doc = _read(CHECKPOINT_DOC)

    assert "No `evidence_analyst` route was introduced" in doc
    assert "No dirty backup topology was copied" in doc
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


def test_phase4k_final_governance_checkpoint_closes_phase_and_recommends_pause():
    doc = _read(CHECKPOINT_DOC)

    assert "This checkpoint closes Phase 4K implementation/equivalence validation" in doc
    assert "Option A - Pause and monitor" in doc
    assert "Pause Phase 4K implementation work and complete manual GitHub CI review" in doc
    assert "Further work should start only as a new bounded phase" in doc
