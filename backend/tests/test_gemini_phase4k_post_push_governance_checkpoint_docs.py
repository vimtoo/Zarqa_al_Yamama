from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_DOC = ROOT / "docs" / "gemini_phase4k_post_push_governance_checkpoint.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase4k_post_push_checkpoint_doc_exists():
    assert CHECKPOINT_DOC.exists()


def test_phase4k_post_push_checkpoint_records_remote_state():
    doc = _read(CHECKPOINT_DOC)

    assert "5d8ef76 feat: add disabled gemini workflow no-op route" in doc
    assert "5d8ef76b81b76134768ea967419df89a3f8ae7b9 refs/heads/main" in doc
    assert "rollback/pre-phase4k-minimal-workflow-wiring-2026-05-18" in doc
    assert "ac6f812e1599e122e6a8debc981f90c9d0cb7d45" in doc


def test_phase4k_post_push_checkpoint_records_only_approved_route():
    doc = _read(CHECKPOINT_DOC)

    assert "v2_join_node -> gemini_assist_noop -> schema_validator_node" in doc
    assert "v2_join_node --proceed--> gemini_assist_noop --> schema_validator_node" in doc
    assert 'workflow.add_node("gemini_assist_noop", gemini_graph_noop_node)' in doc
    assert 'workflow.add_edge("gemini_assist_noop", "schema_validator_node")' in doc
    assert "evidence_analyst` route | Not introduced" in doc


def test_phase4k_post_push_checkpoint_records_test_results():
    doc = _read(CHECKPOINT_DOC)

    assert "`6 passed`" in doc
    assert "`207 passed`" in doc
    assert "`414 passed`" in doc


def test_phase4k_post_push_checkpoint_blocks_live_key_and_state_mutation():
    doc = _read(CHECKPOINT_DOC)

    assert "No live Gemini/API-key work is approved" in doc
    assert "No production state mutation is approved" in doc
    assert "No `agent_outputs` write is approved" in doc
    assert "production `ForecastState` mutation" in doc
    assert "`agent_outputs` writes" in doc
    assert "`ReportWriter` trusted input changes" in doc


def test_phase4k_post_push_checkpoint_blocks_forecast_artifact_creation():
    doc = _read(CHECKPOINT_DOC)

    assert "No `Signal`/`HorizonForecast`/`FusionResult` creation is approved" in doc
    assert "`Signal` creation" in doc
    assert "`HorizonForecast` creation" in doc
    assert "`FusionResult` creation" in doc


def test_phase4k_post_push_checkpoint_blocks_protected_component_bypass():
    doc = _read(CHECKPOINT_DOC)

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


def test_phase4k_post_push_checkpoint_preserves_no_live_import_expectations():
    doc = _read(CHECKPOINT_DOC)

    assert "OK: no live/client/key imports in workflow.py" in doc
    assert "OK: no evidence_analyst route introduced" in doc
    assert "Gemini client import in `workflow.py` | Not present" in doc
    assert "`GEMINI_API_KEY` reference in `workflow.py` | Not present" in doc
