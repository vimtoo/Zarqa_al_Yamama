from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = ROOT / "docs" / "gemini_phase4k_disabled_output_equivalence_test_plan.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase4k_disabled_output_equivalence_plan_exists():
    assert PLAN_DOC.exists()


def test_phase4k_disabled_output_equivalence_plan_records_remote_state():
    doc = _read(PLAN_DOC)

    assert "5d8ef76" in doc
    assert "ca9a7da" in doc
    assert "f3c48de" in doc
    assert "f3c48debae50b28768e3ec100c18259585cea418" in doc
    assert "rollback/pre-phase4k-minimal-workflow-wiring-2026-05-18" in doc


def test_phase4k_disabled_output_equivalence_plan_records_approved_route():
    doc = _read(PLAN_DOC)

    assert "v2_join_node -> gemini_assist_noop -> schema_validator_node" in doc
    assert "schema_validator_node receives equivalent input" in doc
    assert "`schema_validator_node` remains downstream gate" in doc


def test_phase4k_disabled_output_equivalence_plan_preserves_boundaries():
    doc = _read(PLAN_DOC)

    assert "no `workflow.py` changes" in doc
    assert "No live Gemini/API-key work is approved" in doc
    assert "no live Gemini" in doc
    assert "no API keys" in doc
    assert "no `ForecastState` mutation" in doc
    assert "no `agent_outputs` writes" in doc
    assert "no `Signal`/`HorizonForecast`/`FusionResult` creation" in doc


def test_phase4k_disabled_output_equivalence_plan_defines_equivalence_target():
    doc = _read(PLAN_DOC)

    assert "protected state keys unchanged" in doc
    assert "no Gemini state keys added in disabled execution" in doc
    assert "no Gemini `agent_outputs` entry" in doc
    assert "canonical output remains identical for deterministic fields" in doc
    assert "nondeterministic fields are excluded only through approved canonicalization rules" in doc


def test_phase4k_disabled_output_equivalence_plan_recommends_future_test_file():
    doc = _read(PLAN_DOC)

    assert "backend/tests/test_gemini_phase4k_disabled_output_equivalence.py" in doc
    assert "direct no-op adapter state identity/equality checks" in doc
    assert "workflow-shaped baseline fixture comparison" in doc
    assert "`tmp_path`-only artifacts" in doc


def test_phase4k_disabled_output_equivalence_plan_blocks_topology_and_bypass_changes():
    doc = _read(PLAN_DOC)

    assert "no `evidence_analyst` route" in doc
    assert "no dirty backup topology" in doc
    assert "no `ReportWriter` trusted input changes" in doc
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


def test_phase4k_disabled_output_equivalence_plan_recommends_next_stage():
    doc = _read(PLAN_DOC)

    assert "Phase 4K-EQ-B — Implement Disabled Output Equivalence Tests" in doc
    assert "test-only, offline, mocked" in doc
    assert "must not modify `workflow.py`" in doc
