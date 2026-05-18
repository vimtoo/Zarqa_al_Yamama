from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "docs" / "gemini_phase4k_minimal_workflow_patch_plan.md"
APPROVAL_PATH = ROOT / "docs" / "gemini_phase4k_operator_approval_record.md"
TOPOLOGY_RECORD_PATH = ROOT / "docs" / "gemini_phase4k_topology_mapping_record.md"
DECISION_PACKAGE_PATH = ROOT / "docs" / "gemini_phase4k_operator_decision_package.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase4k_planning_docs_exist():
    assert PLAN_PATH.exists()
    assert APPROVAL_PATH.exists()
    assert TOPOLOGY_RECORD_PATH.exists()
    assert DECISION_PACKAGE_PATH.exists()


def test_phase4k_approval_status_is_not_approved():
    approval = _read(APPROVAL_PATH)

    assert "Status: NOT APPROVED" in approval


def test_phase4k_plan_has_required_operator_warnings():
    plan = _read(PLAN_PATH)

    assert "ILLUSTRATIVE ONLY" in plan
    assert "workflow.py must not be modified without approval" in plan
    assert "disabled/no-op by default" in plan
    assert "byte-for-byte identical when disabled" in plan
    assert "evidence_analyst" in plan


def test_phase4k_plan_prohibits_protected_output_writes():
    plan = _read(PLAN_PATH)

    assert "agent_outputs" in plan
    assert "no `agent_outputs` write" in plan
    assert "no `Signal` creation" in plan
    assert "no `HorizonForecast` creation" in plan
    assert "no `FusionResult` creation" in plan


def test_phase4k_plan_prohibits_bypassing_protected_components():
    plan = _read(PLAN_PATH)

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
        assert component in plan

    assert "no `QuantifierV2` replacement" in plan
    assert "no `CriticV2` replacement" in plan
    assert "no `Governor` bypass" in plan
    assert "no `SchemaValidator` bypass" in plan
    assert "no `EvidenceDeduper` bypass" in plan
    assert "no `IndependenceAnalyzer` bypass" in plan
    assert "no `Librarian` bypass" in plan
    assert "no `ArbitrationPolicy` bypass" in plan


def test_phase4k_topology_mapping_record_captures_current_route():
    record = _read(TOPOLOGY_RECORD_PATH)

    assert "`workflow.py` was not modified" in record
    assert "Phase 4K remains `NOT APPROVED`" in record
    assert "v2_join_node --proceed--> schema_validator_node" in record
    assert "gemini_assist_noop --> schema_validator_node" in record
    assert "`evidence_analyst` is not present in current `workflow.py`" in record
    assert "`evidence_analyst` insertion is out of scope for Phase 4K" in record


def test_phase4k_approval_record_keeps_topology_not_approved():
    approval = _read(APPROVAL_PATH)

    assert "Status: NOT APPROVED" in approval
    assert "Current proceed target: `schema_validator_node`" in approval
    assert (
        "Only eligible future route: `v2_join_node -> gemini_assist_noop -> schema_validator_node`"
        in approval
    )
    assert "`evidence_analyst` is out of scope" in approval
    assert "Status remains `NOT APPROVED`" in approval


def test_phase4k_plan_uses_confirmed_schema_validator_target():
    plan = _read(PLAN_PATH)

    assert "<existing_next_node>" not in plan
    assert "gemini_assist_noop -> schema_validator_node" in plan
    assert 'workflow.add_edge("gemini_assist_noop", "schema_validator_node")' in plan
    assert "No `evidence_analyst` route is introduced." in plan
    assert "gemini_assist_noop -> evidence_analyst" not in plan


def test_phase4k_operator_decision_package_preserves_not_approved_status():
    package = _read(DECISION_PACKAGE_PATH)

    assert "Phase 4K remains NOT APPROVED unless Qusai explicitly approves" in package
    assert "v2_join_node -> gemini_assist_noop -> schema_validator_node" in package
    assert "Option A" in package
    assert "Option B" in package
    assert "Option C" in package
    assert (
        "Recommended decision: **Option B — Keep Blocked**, unless Qusai explicitly wants "
        "to test disabled topology wiring."
        in package
    )


def test_phase4k_operator_decision_package_contains_approval_language():
    package = _read(DECISION_PACKAGE_PATH)

    assert (
        "I, Qusai, approve Phase 4K implementation only for the minimal disabled/no-op route"
        in package
    )
    assert "v2_join_node -> gemini_assist_noop -> schema_validator_node" in package


def test_phase4k_operator_decision_package_preserves_boundaries():
    package = _read(DECISION_PACKAGE_PATH)

    assert "no `evidence_analyst` insertion" in package
    assert "no live Gemini call" in package
    assert "no API key" in package
    assert "no `agent_outputs` write" in package
    assert "no `Signal`/`HorizonForecast`/`FusionResult` creation" in package
