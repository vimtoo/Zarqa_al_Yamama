from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODES_DOC = ROOT / "docs" / "gemini_sidecar_operating_modes.md"
README = ROOT / "backend" / "app" / "integrations" / "gemini_deep_research" / "README.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_sidecar_operating_modes_doc_exists():
    assert MODES_DOC.exists()


def test_sidecar_doc_states_core_status_boundaries():
    doc = _read(MODES_DOC)

    assert "Gemini Deep Research is a sidecar." in doc
    assert "it is not a forecasting authority" in doc
    assert "`workflow.py` remains unwired" in doc
    assert "Phase 4K remains NOT APPROVED" in doc
    assert "No Gemini mode may write production `ForecastState` or `agent_outputs`" in doc


def test_sidecar_doc_contains_required_mode_matrix_modes():
    doc = _read(MODES_DOC)

    for mode in (
        "Disabled",
        "Mock Client Test",
        "Evidence Normalization",
        "Shadow Compare",
        "Shadow Runner Offline",
        "Evaluation Policy Offline",
        "Assist Wrapper Review-Only",
        "Graph Adapter No-Op Unwired",
        "Phase 4K Minimal Disabled Wiring",
        "Live Review Trial",
    ):
        assert mode in doc


def test_phase4k_and_live_trial_statuses_are_locked():
    doc = _read(MODES_DOC)

    assert "| Phase 4K Minimal Disabled Wiring |" in doc
    assert "| Phase 4K Minimal Disabled Wiring | Future minimal disabled/no-op workflow route only if explicitly approved. | No | No | No | No | Yes, only after approval | NOT APPROVED |" in doc
    assert "| Live Review Trial |" in doc
    assert "requires separate explicit approval" in doc


def test_sidecar_doc_prohibits_production_state_and_agent_output_writes():
    doc = _read(MODES_DOC)

    assert "production `ForecastState` writes" in doc
    assert "`agent_outputs`" in doc
    assert "Writes ForecastState?" in doc
    assert "Writes agent_outputs?" in doc


def test_sidecar_doc_prohibits_forecast_artifact_creation():
    doc = _read(MODES_DOC)

    assert "no `Signal` creation" in doc
    assert "no `HorizonForecast` creation" in doc
    assert "no `FusionResult` creation" in doc


def test_sidecar_doc_prohibits_bypassing_protected_components():
    doc = _read(MODES_DOC)

    for boundary in (
        "no `QuantifierV2` replacement",
        "no `CriticV2` replacement",
        "no `Governor` bypass",
        "no `SchemaValidator` bypass",
        "no `EvidenceDeduper` bypass",
        "no `IndependenceAnalyzer` bypass",
        "no `Librarian` bypass",
        "no `ArbitrationPolicy` bypass",
    ):
        assert boundary in doc


def test_sidecar_doc_contains_only_eligible_phase4k_route_and_evidence_analyst_warning():
    doc = _read(MODES_DOC)

    assert "v2_join_node -> gemini_assist_noop -> schema_validator_node" in doc
    assert "`evidence_analyst` insertion is out of scope" in doc
    assert "Dirty backup topology must not be copied" in doc


def test_readme_references_sidecar_operating_modes_doc_and_status():
    readme = _read(README)

    assert "docs/gemini_sidecar_operating_modes.md" in readme
    assert "Gemini remains sidecar-only" in readme
    assert "`workflow.py` is unwired" in readme
    assert "Phase 4K remains NOT APPROVED" in readme
    assert "must not write `agent_outputs`" in readme
    assert "must not run live Gemini unless a separate explicit live-review approval package authorizes it" in readme
