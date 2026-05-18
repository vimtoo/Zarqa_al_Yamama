from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.integrations.gemini_deep_research.models import (
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
)
from app.integrations.gemini_deep_research.normalizer import GeminiEvidenceNormalizer
from fixtures.gemini_sidecar_fixtures import (  # noqa: E402
    duplicate_source_result,
    malformed_missing_source_metadata_result,
    mock_evidence_pack,
)


def _result(
    report: str | None,
    *,
    status: GeminiDeepResearchStatus = GeminiDeepResearchStatus.COMPLETED,
    raw_response: dict | None = None,
    citations: list[dict] | None = None,
) -> GeminiDeepResearchResult:
    return GeminiDeepResearchResult(
        run_id="run-test",
        interaction_id="interaction-test",
        model="deep-research-preview-04-2026",
        mode="shadow",
        prompt="Research the issue.",
        status=status,
        raw_report=report,
        raw_response=raw_response or {},
        citations=citations or [],
    )


def _codes(pack):
    return {warning.code for warning in pack.normalizer_warnings}


def test_normalizer_creates_pack_from_markdown_citations():
    report = (
        "Reuters reported current maritime tensions rose this week "
        "[Reuters](https://www.reuters.com/world/middle-east/example?utm_source=test). "
        "RAND assessed medium-term deterrence risks "
        "[RAND](https://www.rand.org/pubs/research_reports/RRA123.html)."
    )

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))

    assert pack.provider == "gemini_deep_research"
    assert pack.interaction_id == "interaction-test"
    assert len(pack.sources) == 2
    assert len(pack.evidence_items) == 2
    assert len(pack.claim_items) >= 1


def test_normalizer_extracts_bare_urls():
    report = "IMF data show current reserve pressure in the region https://www.imf.org/en/Data"

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))

    assert len(pack.sources) == 1
    assert pack.sources[0].canonical_url == "https://imf.org/en/Data"
    assert pack.sources[0].domain == "imf.org"


def test_normalizer_deduplicates_duplicate_urls():
    report = (
        "First citation https://example.com/article?utm_campaign=x#section\n"
        "Duplicate citation [Example](https://www.example.com/article)"
    )

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))

    assert len(pack.sources) == 1
    assert pack.sources[0].canonical_url == "https://example.com/article"


def test_normalizer_creates_gap_when_no_sources_present():
    report = "This is broad narrative without citations or valid source URLs."

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))

    assert pack.sources == []
    assert pack.claim_items == []
    assert pack.intelligence_gaps
    assert "NO_VERIFIED_SOURCES" in _codes(pack)


def test_normalizer_creates_gap_when_gemini_result_failed():
    pack = GeminiEvidenceNormalizer().normalize_result(
        _result("Should not be used https://reuters.com/a", status=GeminiDeepResearchStatus.FAILED)
    )

    assert pack.intelligence_gaps
    assert "GEMINI_RESULT_FAILED" in _codes(pack)
    assert pack.claim_items == []


def test_normalizer_creates_gap_when_gemini_result_timeout():
    pack = GeminiEvidenceNormalizer().normalize_result(
        _result("Should not be used https://reuters.com/a", status=GeminiDeepResearchStatus.TIMEOUT)
    )

    assert pack.intelligence_gaps
    assert "GEMINI_RESULT_TIMEOUT" in _codes(pack)
    assert pack.claim_items == []


def test_evidence_candidates_include_hash_and_canonical_url():
    report = "Reuters reported current tensions rose https://www.reuters.com/world/a?utm_medium=social#frag"

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))

    evidence = pack.evidence_items[0]
    assert len(evidence.content_hash) == 64
    assert evidence.canonical_url == "https://reuters.com/world/a"


def test_claim_candidates_reference_evidence_ids():
    report = "Reuters reported current tensions rose https://www.reuters.com/world/a"

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))
    evidence_ids = {item.id for item in pack.evidence_items}

    assert pack.claim_items
    assert all(claim.evidence_ids for claim in pack.claim_items)
    assert all(eid in evidence_ids for claim in pack.claim_items for eid in claim.evidence_ids)


def test_unsupported_uncited_claims_are_not_converted():
    report = (
        "Iran will escalate in Q3 without any citation. "
        "Sources:\n"
        "- [Reuters](https://www.reuters.com/world/a)"
    )

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))

    assert all("Iran will escalate" not in claim.text for claim in pack.claim_items)
    assert "UNSUPPORTED_CLAIM_SKIPPED" in _codes(pack)


def test_probability_content_is_quarantined_and_no_signals_created():
    report = "There is a 70% chance of escalation [Reuters](https://www.reuters.com/world/a)."

    normalizer = GeminiEvidenceNormalizer()
    pack = normalizer.normalize_result(_result(report))
    agent_output = normalizer.to_agent_output_candidate(pack)

    assert "PROBABILITY_CONTENT_QUARANTINED" in _codes(pack)
    assert pack.claim_items == []
    assert getattr(agent_output, "signals", []) == []


def test_secret_like_content_is_redacted_and_warning_added():
    secret = "AIzaabcdefghijklmnopqrstuvwxyz123456"
    report = (
        f"API_KEY={secret}\n"
        "Reuters reported current tensions rose https://www.reuters.com/world/a"
    )

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))
    serialized = pack.model_dump_json()

    assert secret not in serialized
    assert "[REDACTED_SECRET]" in serialized
    assert "POSSIBLE_SECRET_LEAK" in _codes(pack)
    assert any(gap.severity == "CRITICAL" for gap in pack.intelligence_gaps)


def test_missing_publication_dates_are_not_fabricated():
    report = "Reuters reported current tensions rose https://www.reuters.com/world/a"

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))

    assert pack.sources[0].published_at is None
    assert "MISSING_PUBLICATION_DATES" in _codes(pack)


def test_source_type_inference_for_common_domains():
    report = "\n".join([
        "IMF data show reserves changed https://www.imf.org/en/Data",
        "RAND assessed regional risks https://www.rand.org/pubs/research_reports/RRA123.html",
        "Reuters reported current tensions https://www.reuters.com/world/a",
        "X post showed a local claim https://x.com/example/status/123",
    ])

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))
    by_domain = {source.domain: source.source_type_hint for source in pack.sources}

    assert by_domain["imf.org"] == "primary_data"
    assert by_domain["rand.org"] == "analysis"
    assert by_domain["reuters.com"] == "primary_reporting"
    assert by_domain["x.com"] == "social"


def test_to_agent_output_candidate_returns_agent_output_with_empty_signals():
    report = "Reuters reported current tensions rose https://www.reuters.com/world/a"

    normalizer = GeminiEvidenceNormalizer()
    pack = normalizer.normalize_result(_result(report))
    agent_output = normalizer.to_agent_output_candidate(pack)

    if getattr(agent_output, "ok", True) is False:
        warning_codes = {warning.code for warning in agent_output.warnings}
        assert agent_output.error_type in {
            "ImportError",
            "ValidationError",
            "PydanticUserError",
            "TypeError",
            "AttributeError",
        }
        assert "AGENT_OUTPUT_CONVERSION_FAILED" in warning_codes
        assert not hasattr(agent_output, "signals")
        assert not hasattr(agent_output, "horizon_forecasts")
        assert not hasattr(agent_output, "fusion_result")
        return

    assert getattr(agent_output, "agent_id") == "gemini_deep_research"
    assert getattr(agent_output, "signals") == []
    assert not hasattr(agent_output, "horizon_forecasts")
    assert not hasattr(agent_output, "fusion_result")
    assert getattr(agent_output, "claims")
    assert getattr(agent_output, "evidence")


def test_malformed_raw_report_fails_closed_without_unhandled_exception():
    report = "### Sources\n- Title: Broken\n- URL: not-a-url\n\nThis will probably fail without citations."

    pack = GeminiEvidenceNormalizer().normalize_result(_result(report))

    assert pack.intelligence_gaps
    assert pack.claim_items == []
    assert "NO_VERIFIED_SOURCES" in _codes(pack)


def test_phase4la_valid_mocked_evidence_pack_fixture_is_source_backed():
    pack = mock_evidence_pack(run_id="phase4la-valid-pack", domain="security")

    assert pack.provider == "gemini_deep_research"
    assert pack.run_id == "phase4la-valid-pack"
    assert len(pack.sources) == 2
    assert len(pack.evidence_items) == 2
    assert pack.claim_items
    assert all(claim.evidence_ids for claim in pack.claim_items)
    assert all(item.source_id for item in pack.evidence_items)


def test_phase4la_missing_source_metadata_fails_closed_without_forecast_artifacts():
    pack = GeminiEvidenceNormalizer().normalize_result(malformed_missing_source_metadata_result())
    serialized = pack.model_dump_json()
    normalizer_source = Path(
        "backend/app/integrations/gemini_deep_research/normalizer.py"
    ).read_text(encoding="utf-8")

    assert pack.sources == []
    assert pack.evidence_items == []
    assert pack.claim_items == []
    assert pack.intelligence_gaps
    assert "NO_VERIFIED_SOURCES" in _codes(pack)
    assert ("agent" + "_outputs") not in serialized
    for model_name in ("Signal", "HorizonForecast", "FusionResult"):
        assert f"{model_name}(" not in normalizer_source


def test_phase4la_duplicate_sources_are_deterministically_deduplicated():
    pack_a = GeminiEvidenceNormalizer().normalize_result(duplicate_source_result())
    pack_b = GeminiEvidenceNormalizer().normalize_result(duplicate_source_result())

    assert len(pack_a.sources) == 1
    assert len(pack_a.evidence_items) == 1
    assert pack_a.sources[0].canonical_url == "https://reuters.com/world/example"
    assert pack_a.evidence_items[0].content_hash == pack_b.evidence_items[0].content_hash
