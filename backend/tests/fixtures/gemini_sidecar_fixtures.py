"""Mock Gemini sidecar fixtures for offline tests.

These helpers are test-only. They do not call Gemini, import workflow.py,
or construct production forecast artifact models.
"""

from __future__ import annotations

from pathlib import Path

from app.integrations.gemini_deep_research.models import (
    AgentOverlapComparison,
    EvidenceComparison,
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
    GeminiShadowRun,
    RiskAssessment,
    SourceComparison,
)
from app.integrations.gemini_deep_research.normalizer import GeminiEvidenceNormalizer


def mock_domain_report(domain: str = "general") -> str:
    """Return a deterministic source-backed mock Gemini report."""
    domain = (domain or "general").lower()
    if domain == "finance":
        return (
            "IMF data show current reserve pressure changed "
            "https://www.imf.org/en/Data\n"
            "Reuters reported current market stress indicators "
            "https://www.reuters.com/markets/example."
        )
    if domain == "elections":
        return (
            "Official election data remain the preferred source "
            "https://www.fec.gov/data/\n"
            "AP reported current election administration litigation "
            "https://www.apnews.com/article/election-example."
        )
    if domain in {"geopolitics", "security"}:
        return (
            "Reuters reported current maritime tensions rose "
            "https://www.reuters.com/world/middle-east/example\n"
            "RAND assessed medium-term deterrence risks "
            "https://www.rand.org/pubs/research_reports/RRA123.html."
        )
    return (
        "Reuters reported current technology supply-chain pressure "
        "https://www.reuters.com/technology/example\n"
        "CSIS assessed medium-term policy risks "
        "https://www.csis.org/analysis/example."
    )


def mock_gemini_result(
    *,
    run_id: str = "fixture-run-1",
    domain: str = "general",
    report: str | None = None,
    status: GeminiDeepResearchStatus = GeminiDeepResearchStatus.COMPLETED,
) -> GeminiDeepResearchResult:
    """Build a deterministic mocked raw Gemini result."""
    return GeminiDeepResearchResult(
        run_id=run_id,
        interaction_id=f"{run_id}-interaction",
        model="deep-research-preview-04-2026",
        mode="shadow",
        prompt=f"Assess {domain} risk.",
        status=status,
        raw_report=report if report is not None else mock_domain_report(domain),
        raw_response={"mock": True, "domain": domain},
        citations=[],
        metadata={"mock": True, "domain": domain},
    )


def mock_evidence_pack(*, run_id: str = "fixture-run-1", domain: str = "general"):
    """Normalize a deterministic mocked raw result into a GeminiEvidencePack."""
    return GeminiEvidenceNormalizer().normalize_result(
        mock_gemini_result(run_id=run_id, domain=domain),
        original_question=f"Assess {domain} risk.",
    )


def malformed_missing_source_metadata_result() -> GeminiDeepResearchResult:
    """Return a result with source-like text but no valid source URL."""
    return mock_gemini_result(
        run_id="fixture-malformed-missing-source",
        report=(
            "Source: Reuters maritime update\n"
            "Publisher: Reuters\n"
            "URL: not-a-url\n"
            "This unsupported claim will escalate without a valid citation."
        ),
    )


def duplicate_source_result() -> GeminiDeepResearchResult:
    """Return a result with duplicated URLs in different source formats."""
    return mock_gemini_result(
        run_id="fixture-duplicate-source",
        report=(
            "Reuters reported current maritime pressure "
            "https://www.reuters.com/world/example?utm_source=test#section. "
            "Duplicate Reuters citation "
            "[Reuters](https://reuters.com/world/example)."
        ),
    )


def fully_cited_claim_result() -> GeminiDeepResearchResult:
    """Return a report where the claim is directly source-backed."""
    return mock_gemini_result(
        run_id="fixture-fully-cited-claim",
        report=(
            "Reuters reported current maritime inspections increased this week "
            "https://www.reuters.com/world/middle-east/cited-example."
        ),
    )


def uncited_claim_with_source_list_result() -> GeminiDeepResearchResult:
    """Return an uncited claim plus a source list that should not support it."""
    return mock_gemini_result(
        run_id="fixture-uncited-claim-source-list",
        report=(
            "A regional escalation will occur next quarter without a direct citation.\n"
            "Sources:\n"
            "- Reuters background source https://www.reuters.com/world/middle-east/background"
        ),
    )


def invalid_url_source_result() -> GeminiDeepResearchResult:
    """Return source-like metadata containing no valid URL."""
    return mock_gemini_result(
        run_id="fixture-invalid-url-source",
        report=(
            "Title: Broken source metadata\n"
            "Publisher: Reuters\n"
            "URL: hxxps://not-a-valid-url\n"
            "Reuters reported current maritime inspections changed."
        ),
    )


def weak_source_only_result() -> GeminiDeepResearchResult:
    """Return a report backed only by weak/social source candidates."""
    return mock_gemini_result(
        run_id="fixture-weak-source-only",
        report=(
            "X post claimed current disruption was spreading "
            "https://x.com/example/status/123456789."
        ),
    )


def probability_like_cited_claim_result() -> GeminiDeepResearchResult:
    """Return a cited probability-like claim that must remain quarantined."""
    return mock_gemini_result(
        run_id="fixture-probability-like-claim",
        report=(
            "There is a 70% chance of escalation this quarter "
            "https://www.reuters.com/world/middle-east/probability-example."
        ),
    )


def mock_seer_outputs() -> dict:
    """Return deterministic, minimal saved TheSeer-like outputs for comparison."""
    return {
        "agents_executed": ["context_interpreter", "black_swan_generator"],
        "sources": [
            {
                "title": "Reuters example",
                "url": "https://reuters.com/world/middle-east/example",
                "canonical_url": "https://reuters.com/world/middle-east/example",
                "domain": "reuters.com",
                "source_type": "primary_reporting",
            }
        ],
        "evidence_items": [
            {
                "id": "seer-ev-1",
                "url": "https://reuters.com/world/middle-east/example",
                "canonical_url": "https://reuters.com/world/middle-east/example",
                "domain": "reuters.com",
                "content_hash": "a" * 64,
                "snippet": "Reuters reported current maritime tensions rose.",
                "source_type": "primary_reporting",
            }
        ],
        "claims": [
            {
                "id": "seer-claim-1",
                "text": "Reuters reported current maritime tensions rose.",
                "evidence_ids": ["seer-ev-1"],
                "confidence": 0.6,
            }
        ],
    }


def mock_shadow_run(
    *,
    run_id: str = "fixture-shadow-run-1",
    domain: str = "general",
    status: str = "completed",
) -> GeminiShadowRun:
    """Build a deterministic GeminiShadowRun for artifact validation tests."""
    return GeminiShadowRun(
        run_id=run_id,
        query=f"Assess {domain} risk.",
        gemini_interaction_id=f"{run_id}-interaction",
        gemini_model="deep-research-preview-04-2026",
        seer_agents_used=["context_interpreter", "black_swan_generator"],
        source_comparison=SourceComparison(
            gemini_source_count=3,
            seer_source_count=2,
            overlapping_sources=["https://reuters.com/world/middle-east/example"],
            unique_gemini_sources=["https://rand.org/pubs/research_reports/RRA123.html"],
            source_overlap_ratio=0.4,
            gemini_domains=["reuters.com", "rand.org"],
            seer_domains=["reuters.com"],
        ),
        evidence_comparison=EvidenceComparison(
            gemini_evidence_count=3,
            seer_evidence_count=2,
            gemini_claim_count=2,
            seer_claim_count=1,
            accepted_gemini_evidence_count=3,
            duplicate_evidence_count=1,
            unsupported_gemini_claims_count=0,
            contradictions_count=0,
        ),
        agent_overlap=AgentOverlapComparison(
            context_interpreter_overlap=0.6,
            black_swan_generator_overlap=0.5,
            useful_new_evidence_count=2,
            seer_unique_evidence_count=1,
        ),
        risk_assessment=RiskAssessment(
            hallucination_risk="low",
            citation_risk="low",
            source_governance_risk="low",
            schema_compliance_risk="low",
            latency_risk="low",
            cost_risk="unknown",
            dependency_risk="low",
            overall_risk="low",
        ),
        recommendation="Gemini useful as shadow only",
        warnings=[],
        metadata={"status": status, "domain": domain, "latency_seconds": 120},
    )


def assert_sidecar_path(path: str | Path, root: Path) -> None:
    """Assert a saved artifact path remains under the supplied sidecar test root."""
    resolved_path = Path(path).resolve()
    resolved_root = root.resolve()
    assert resolved_path.is_relative_to(resolved_root)
    assert "agent_outputs" not in resolved_path.parts
