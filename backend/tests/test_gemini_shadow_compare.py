from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.integrations.gemini_deep_research.models import (  # noqa: E402
    GeminiClaimCandidate,
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
    GeminiEvidencePack,
    GeminiIntelligenceGapCandidate,
)
from app.integrations.gemini_deep_research.normalizer import GeminiEvidenceNormalizer  # noqa: E402
from app.integrations.gemini_deep_research.shadow_compare import GeminiShadowComparator  # noqa: E402
from app.integrations.gemini_deep_research.storage import (  # noqa: E402
    load_shadow_run,
    save_shadow_report,
    save_shadow_run,
)


def _result(report: str) -> GeminiDeepResearchResult:
    return GeminiDeepResearchResult(
        run_id="gemini-run-1",
        interaction_id="gemini-interaction-1",
        model="deep-research-preview-04-2026",
        mode="shadow",
        prompt="Research the question.",
        status=GeminiDeepResearchStatus.COMPLETED,
        raw_report=report,
        raw_response={},
    )


def _pack() -> GeminiEvidencePack:
    report = (
        "Reuters reported current maritime tensions rose this week "
        "[Reuters](https://www.reuters.com/world/middle-east/example?utm_source=test). "
        "RAND assessed medium-term deterrence risks "
        "[RAND](https://www.rand.org/pubs/research_reports/RRA123.html)."
    )
    return GeminiEvidenceNormalizer().normalize_result(
        _result(report),
        original_question="Assess regional maritime risk.",
    )


def _seer_outputs() -> dict:
    return {
        "agents_executed": [
            "context_interpreter",
            "black_swan_generator",
            "think_tank_analyst",
            "walled_garden_analyst",
            "evidence_analyst",
        ],
        "sources": [
            {
                "title": "Reuters maritime update",
                "url": "https://reuters.com/world/middle-east/example",
                "domain": "reuters.com",
                "publisher": "Reuters",
                "source_type": "primary_reporting",
            },
            {
                "title": "AP regional update",
                "url": "https://apnews.com/article/unique-seer",
                "domain": "apnews.com",
                "publisher": "Associated Press",
                "source_type": "primary_reporting",
            },
        ],
        "evidence_items": [
            {
                "id": "seer-ev-1",
                "url": "https://reuters.com/world/middle-east/example",
                "canonical_url": "https://reuters.com/world/middle-east/example",
                "domain": "reuters.com",
                "content_hash": "a" * 64,
                "snippet": "Reuters reported current maritime tensions rose this week.",
                "source_type": "primary_reporting",
            }
        ],
        "claims": [
            {
                "id": "seer-claim-1",
                "text": "Reuters reported current maritime tensions rose this week.",
                "evidence_ids": ["seer-ev-1"],
                "confidence": 0.7,
                "time_horizon": "SHORT_TERM",
            }
        ],
        "context_interpreter": {
            "summary": "Reuters reported current maritime tensions rose this week https://reuters.com/world/middle-east/example",
            "claims": [
                {"text": "Reuters reported current maritime tensions rose this week."}
            ],
        },
        "black_swan_generator": "Tail risks remain plausible but are not dominant.",
        "think_tank_analyst": "A think tank lane noted medium-term deterrence risks without a retained citation.",
        "walled_garden_analyst": {"summary": "No protected-source override was available."},
        "evidence_analyst": {
            "evidence": [
                {
                    "url": "https://reuters.com/world/middle-east/example",
                    "snippet": "Reuters reported current maritime tensions rose this week.",
                }
            ]
        },
    }


def test_comparator_creates_shadow_run_from_pack_and_seer_outputs():
    run = GeminiShadowComparator().compare(_pack(), _seer_outputs(), query="Assess risk", run_id="shadow-1")

    assert run.run_id == "shadow-1"
    assert run.query == "Assess risk"
    assert run.gemini_interaction_id == "gemini-interaction-1"
    assert run.gemini_mode == "shadow"


def test_source_comparison_counts_gemini_and_seer_sources():
    comparison = GeminiShadowComparator().compare_sources(_pack(), _seer_outputs())

    assert comparison.gemini_source_count == 2
    assert comparison.seer_source_count >= 2


def test_source_comparison_detects_overlapping_canonical_urls():
    comparison = GeminiShadowComparator().compare_sources(_pack(), _seer_outputs())

    assert "https://reuters.com/world/middle-east/example" in comparison.overlapping_sources
    assert comparison.source_overlap_ratio > 0


def test_source_comparison_detects_unique_gemini_sources():
    comparison = GeminiShadowComparator().compare_sources(_pack(), _seer_outputs())

    assert "https://rand.org/pubs/research_reports/RRA123.html" in comparison.unique_gemini_sources


def test_source_comparison_detects_unique_seer_sources():
    comparison = GeminiShadowComparator().compare_sources(_pack(), _seer_outputs())

    assert "https://apnews.com/article/unique-seer" in comparison.unique_seer_sources


def test_evidence_comparison_counts_evidence_and_claims():
    comparison = GeminiShadowComparator().compare_evidence(_pack(), _seer_outputs())

    assert comparison.gemini_evidence_count == 2
    assert comparison.seer_evidence_count >= 1
    assert comparison.gemini_claim_count >= 1
    assert comparison.seer_claim_count >= 1


def test_evidence_comparison_detects_unsupported_gemini_claims():
    pack = _pack()
    pack.claim_items.append(
        GeminiClaimCandidate(
            id="bad-claim",
            text="This unsupported claim has no matching evidence candidate.",
            evidence_ids=["missing-evidence"],
            confidence=0.5,
            confidence_justification="Evidence-support confidence only; not a forecast probability.",
            time_horizon="MEDIUM_TERM",
        )
    )

    comparison = GeminiShadowComparator().compare_evidence(pack, _seer_outputs())

    assert comparison.unsupported_gemini_claims_count == 1


def test_evidence_comparison_detects_duplicate_evidence_by_url_or_text_similarity():
    comparison = GeminiShadowComparator().compare_evidence(_pack(), _seer_outputs())

    assert comparison.duplicate_evidence_count >= 1


def test_agent_overlap_handles_missing_agent_output_without_crashing():
    overlap = GeminiShadowComparator().compare_agent_overlap(_pack(), {"sources": []})

    assert overlap.context_interpreter_overlap is None
    assert overlap.black_swan_generator_overlap is None


def test_agent_overlap_computes_nonzero_overlap_when_urls_or_claim_text_overlap():
    overlap = GeminiShadowComparator().compare_agent_overlap(_pack(), _seer_outputs())

    assert overlap.context_interpreter_overlap is not None
    assert overlap.context_interpreter_overlap > 0


def test_risk_assessment_marks_high_citation_risk_when_gemini_has_no_urls():
    pack = GeminiEvidencePack(
        run_id="empty-pack",
        original_question="Question",
        intelligence_gaps=[
            GeminiIntelligenceGapCandidate(reason="No URLs found.", severity="HIGH")
        ],
    )

    risk = GeminiShadowComparator().assess_risks(pack, _seer_outputs())

    assert risk.citation_risk == "high"


def test_risk_assessment_marks_high_hallucination_risk_when_claims_are_unsupported():
    pack = _pack()
    pack.claim_items.append(
        GeminiClaimCandidate(
            id="bad-claim",
            text="Unsupported claim.",
            evidence_ids=["missing-evidence"],
            confidence=0.5,
            confidence_justification="Evidence-support confidence only; not a forecast probability.",
            time_horizon="MEDIUM_TERM",
        )
    )

    risk = GeminiShadowComparator().assess_risks(pack, _seer_outputs())

    assert risk.hallucination_risk == "high"


def test_recommendation_is_conservative_and_does_not_recommend_replacement_from_weak_evidence():
    run = GeminiShadowComparator().compare(_pack(), _seer_outputs())

    assert not run.recommendation.startswith("Gemini ready to replace")


def test_recommendation_can_classify_useful_shadow_output_as_shadow_only():
    run = GeminiShadowComparator().compare(_pack(), _seer_outputs())

    assert run.recommendation == "Gemini useful as shadow only"


def test_markdown_report_contains_all_required_sections():
    comparator = GeminiShadowComparator()
    report = comparator.render_markdown_report(comparator.compare(_pack(), _seer_outputs()))

    for section in [
        "# Gemini Deep Research Shadow Comparison",
        "## 1. Run Metadata",
        "## 2. Source Comparison",
        "## 3. Evidence Comparison",
        "## 4. Agent Replacement Assessment",
        "## 5. Risk Assessment",
        "## 6. Recommendation",
        "## 7. Next Steps",
    ]:
        assert section in report


def test_storage_saves_and_loads_shadow_run_json(tmp_path, monkeypatch):
    monkeypatch.setenv("SEER_GEMINI_SHADOW_RUN_DIR", str(tmp_path))
    run = GeminiShadowComparator().compare(_pack(), _seer_outputs(), run_id="shadow-storage")

    path = save_shadow_run(run)
    loaded = load_shadow_run("shadow-storage")

    assert path == tmp_path / "shadow-storage.json"
    assert loaded.run_id == run.run_id
    assert loaded.source_comparison.gemini_source_count == run.source_comparison.gemini_source_count


def test_storage_saves_markdown_report(tmp_path, monkeypatch):
    monkeypatch.setenv("SEER_GEMINI_SHADOW_RUN_DIR", str(tmp_path))
    run = GeminiShadowComparator().compare(_pack(), _seer_outputs(), run_id="shadow-report")

    path = save_shadow_report(run)

    assert path == tmp_path / "shadow-report.md"
    assert path.read_text(encoding="utf-8").startswith("# Gemini Deep Research Shadow Comparison")


def test_comparator_tolerates_dict_inputs_as_well_as_pydantic_model_inputs():
    pack_dict = _pack().model_dump(mode="json")

    run = GeminiShadowComparator().compare(pack_dict, _seer_outputs())

    assert run.source_comparison.gemini_source_count == 2


def test_no_forecast_artifacts_or_output_write_targets_are_created_or_referenced():
    run = GeminiShadowComparator().compare(_pack(), _seer_outputs())
    serialized = run.model_dump_json()
    source = Path(
        "backend/app/integrations/gemini_deep_research/shadow_compare.py"
    ).read_text(encoding="utf-8")

    assert ("agent" + "_outputs") not in serialized
    for model_name in ("Signal", "HorizonForecast", "FusionResult"):
        assert f"{model_name}(" not in source


def test_malformed_or_incomplete_input_does_not_throw_unhandled_exception():
    run = GeminiShadowComparator().compare(
        {"sources": "not-a-valid-source-list", "claim_items": [{"evidence_ids": []}]},
        None,
    )

    assert run.evidence_comparison.gemini_evidence_count == 0
    assert run.warnings
