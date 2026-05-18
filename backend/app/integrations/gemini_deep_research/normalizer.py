"""Phase 2 normalizer for Gemini Deep Research raw reports.

The normalizer is intentionally local and deterministic:
- It does not call Gemini.
- It does not fetch URLs.
- It does not mutate workflow state.
- It does not write agent_outputs.
- It does not create Signals, HorizonForecast, or FusionResult.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.integrations.gemini_deep_research.models import (
    GeminiAgentOutputCandidateFailure,
    GeminiClaimCandidate,
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
    GeminiEvidenceCandidate,
    GeminiEvidencePack,
    GeminiIntelligenceGapCandidate,
    GeminiNormalizerWarning,
    GeminiSourceCandidate,
)


URL_RE = re.compile(r"https?://[^\s<>\]\)\"']+", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]{1,240})\]\((https?://[^)\s]+)\)", re.IGNORECASE)
COMMON_TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
}

SECRET_PATTERNS = [
    re.compile(r"\bAuthorization\s*:\s*[^\n\r]+", re.IGNORECASE),
    re.compile(r"\[REDACTED_API_KEY\]", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z_-]{10,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{16,}", re.IGNORECASE),
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.DOTALL,
    ),
    re.compile(
        r"\b(?:API_KEY|SECRET|TOKEN|PASSWORD|DATABASE_URL)\s*=\s*[^\s]+",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:postgresql?|mysql|redis|mongodb)://[^\s]+", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9])"),
]

PROBABILITY_PATTERNS = [
    re.compile(r"\b(?:p10|p50|p90)\b", re.IGNORECASE),
    re.compile(r"\bconfidence interval\b", re.IGNORECASE),
    re.compile(r"\b(?:final|forecast|event)\s+probabilit(?:y|ies)\b", re.IGNORECASE),
    re.compile(r"\bprobability\s+(?:range|band|estimate|forecast)\b", re.IGNORECASE),
    re.compile(r"\b(?:chance|probability|likelihood|odds|risk)\s+(?:of|is|at|:)?\s*\d{1,3}\s*%", re.IGNORECASE),
    re.compile(r"\b\d{1,3}\s*%\s+(?:chance|probability|likelihood|odds|risk)\b", re.IGNORECASE),
]

UNSUPPORTED_CLAIM_HINTS = (
    "will ",
    "could ",
    "may ",
    "is likely",
    "suggests",
    "indicates",
    "shows",
    "reported",
    "found",
)

OFFICIAL_DOMAINS = {
    "imf.org",
    "worldbank.org",
    "federalreserve.gov",
    "treasury.gov",
    "bls.gov",
    "census.gov",
    "eia.gov",
    "opec.org",
    "ecb.europa.eu",
}
THINK_TANK_DOMAINS = {
    "rand.org",
    "brookings.edu",
    "carnegieendowment.org",
    "iiss.org",
    "sipri.org",
    "crisisgroup.org",
    "csis.org",
    "chathamhouse.org",
    "mei.edu",
    "atlanticcouncil.org",
    "cfr.org",
    "warontherocks.com",
    "agsiw.org",
    "arxiv.org",
    "nber.org",
    "ssrn.com",
}
NEWS_DOMAINS = {
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
    "nytimes.com",
    "washingtonpost.com",
    "ft.com",
    "wsj.com",
    "bloomberg.com",
    "cnn.com",
    "edition.cnn.com",
    "aljazeera.com",
    "theguardian.com",
    "politico.com",
    "axios.com",
}
SOCIAL_DOMAINS = {
    "x.com",
    "twitter.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "reddit.com",
    "youtube.com",
    "linkedin.com",
}
AGGREGATOR_DOMAINS = {
    "news.google.com",
    "gdeltproject.org",
    "yahoo.com",
    "msn.com",
}


class GeminiEvidenceNormalizer:
    """Convert raw Gemini Deep Research results into local evidence candidates."""

    def __init__(self) -> None:
        self._warnings: List[GeminiNormalizerWarning] = []
        self._secret_detected = False
        self._probability_detected = False
        self._time_horizon_inferred = False
        self._unsupported_claim_skipped = False

    def normalize_result(
        self,
        result: GeminiDeepResearchResult,
        original_question: Optional[str] = None,
        improved_prompt: Optional[str] = None,
    ) -> GeminiEvidencePack:
        """Normalize a raw Gemini result into a local `GeminiEvidencePack`."""
        self._reset()
        try:
            raw_report = result.raw_report or ""
            redacted_report = self._redact_secrets(raw_report)
            raw_metadata = self._redact_obj(result.raw_response or {})

            pack = GeminiEvidencePack(
                model=result.model,
                interaction_id=result.interaction_id,
                run_id=result.run_id,
                original_question=self._redact_secrets(original_question or result.prompt or ""),
                improved_research_prompt=self._redact_secrets(improved_prompt or result.prompt or ""),
                raw_report=redacted_report,
                raw_interaction_metadata=raw_metadata if isinstance(raw_metadata, dict) else {},
            )

            if self._contains_probability_content(redacted_report):
                self._probability_detected = True
                self._add_warning(
                    "PROBABILITY_CONTENT_QUARANTINED",
                    "Forecast probability-like content was kept out of candidate claims and signals.",
                    "HIGH",
                )
                pack.uncertainty_notes.append(
                    "Gemini report contained probability-like forecast content; it was quarantined from normalized claims."
                )

            if self._secret_detected:
                self._add_warning(
                    "POSSIBLE_SECRET_LEAK",
                    "Secret-like content was detected and redacted from normalized fields.",
                    "CRITICAL",
                )
                pack.intelligence_gaps.append(self.build_intelligence_gap(
                    reason="Secret-like content was detected in the raw Gemini result and redacted.",
                    missing_inputs=["secret-free raw research output"],
                    severity="CRITICAL",
                    retryable=False,
                ))

            if result.status in {GeminiDeepResearchStatus.FAILED, GeminiDeepResearchStatus.TIMEOUT}:
                severity = "HIGH" if result.status == GeminiDeepResearchStatus.FAILED else "MEDIUM"
                code = "GEMINI_RESULT_FAILED" if result.status == GeminiDeepResearchStatus.FAILED else "GEMINI_RESULT_TIMEOUT"
                self._add_warning(code, f"Gemini result status was {result.status.value}.", severity)
                pack.intelligence_gaps.append(self.build_intelligence_gap(
                    reason=f"Gemini Deep Research result status was {result.status.value}.",
                    missing_inputs=["completed Gemini Deep Research report"],
                    attempted_sources=[],
                    severity=severity,
                ))
                pack.normalizer_warnings = list(self._warnings)
                return pack

            if not redacted_report.strip():
                self._add_warning("EMPTY_REPORT", "Gemini result did not contain a raw report.", "HIGH")
                pack.intelligence_gaps.append(self.build_intelligence_gap(
                    reason="Gemini result did not contain a raw report.",
                    missing_inputs=["raw_report"],
                    severity="HIGH",
                ))
                pack.normalizer_warnings = list(self._warnings)
                return pack

            raw_response_for_sources: Dict[str, Any] = dict(result.raw_response or {})
            if result.citations:
                raw_response_for_sources["citations"] = result.citations

            sources = self.extract_sources(redacted_report, raw_response_for_sources)
            pack.sources = sources

            if not sources:
                self._add_warning("NO_VERIFIED_SOURCES", "No valid source URLs or citations were found.", "HIGH")
                pack.intelligence_gaps.append(self.build_intelligence_gap(
                    reason="No valid source URLs or citations were found in the Gemini report.",
                    missing_inputs=["verified source URLs", "citations"],
                    severity="HIGH",
                ))
                pack.normalizer_warnings = list(self._warnings)
                return pack

            if all(source.published_at is None for source in sources):
                self._add_warning(
                    "MISSING_PUBLICATION_DATES",
                    "No source publication dates were available; dates were not fabricated.",
                    "LOW",
                )
                pack.intelligence_gaps.append(self.build_intelligence_gap(
                    reason="Source publication dates were not available in the Gemini report.",
                    missing_inputs=["publication dates"],
                    attempted_sources=[s.url for s in sources],
                    severity="LOW",
                    retryable=False,
                ))

            pack.evidence_items = self.build_evidence_candidates(sources, redacted_report)
            pack.claim_items = self.extract_candidate_claims(redacted_report, sources)

            if sources and not pack.evidence_items:
                self._add_warning(
                    "NO_TRACEABLE_EVIDENCE",
                    "Sources existed, but no traceable snippets could be converted into evidence candidates.",
                    "HIGH",
                )
                pack.intelligence_gaps.append(self.build_intelligence_gap(
                    reason="Sources existed, but no traceable snippets could be converted into evidence candidates.",
                    missing_inputs=["source-backed report snippets"],
                    attempted_sources=[s.url for s in sources],
                    severity="HIGH",
                ))

            if pack.evidence_items and not pack.claim_items:
                self._add_warning(
                    "NO_SUPPORTED_CLAIMS",
                    "No atomic source-backed claims could be extracted.",
                    "MEDIUM",
                )
                pack.intelligence_gaps.append(self.build_intelligence_gap(
                    reason="The report did not contain atomic source-backed claims suitable for candidate conversion.",
                    missing_inputs=["atomic cited claims"],
                    attempted_sources=[s.url for s in sources],
                    severity="MEDIUM",
                    retryable=False,
                ))

            pack.normalizer_warnings = list(self._warnings)
            return pack
        except Exception as exc:  # noqa: BLE001 - malformed reports must fail closed
            self._add_warning(
                "NORMALIZER_EXCEPTION",
                f"Normalizer failed closed: {exc.__class__.__name__}",
                "HIGH",
            )
            return GeminiEvidencePack(
                model=getattr(result, "model", "deep-research-preview-04-2026"),
                interaction_id=getattr(result, "interaction_id", None),
                run_id=getattr(result, "run_id", ""),
                original_question=original_question,
                improved_research_prompt=improved_prompt,
                raw_report=self._redact_secrets(getattr(result, "raw_report", "") or ""),
                raw_interaction_metadata={},
                intelligence_gaps=[self.build_intelligence_gap(
                    reason="Malformed Gemini result could not be normalized safely.",
                    missing_inputs=["well-formed raw report"],
                    severity="HIGH",
                )],
                normalizer_warnings=list(self._warnings),
            )

    def extract_sources(
        self,
        raw_report: str,
        raw_response: Optional[Dict[str, Any]] = None,
    ) -> List[GeminiSourceCandidate]:
        """Extract and deduplicate source candidates from raw report text."""
        candidates: List[Tuple[str, Optional[str], List[str], Optional[str], Optional[str], Optional[datetime]]] = []
        report = raw_report or ""

        for match in MARKDOWN_LINK_RE.finditer(report):
            title = self._clean_text(match.group(1))
            url = self._clean_url(match.group(2))
            candidates.append((url, title, [match.group(0)], None, None, self._extract_date_near(report, match.start())))

        for match in URL_RE.finditer(report):
            url = self._clean_url(match.group(0))
            line = self._line_containing(report, match.start())
            title, publisher, published_at = self._extract_metadata_from_line(line)
            near_title, near_publisher, near_date = self._extract_metadata_near(report, match.start())
            title = title or near_title
            publisher = publisher or near_publisher
            published_at = published_at or near_date
            if published_at is None:
                published_at = self._extract_date_near(report, match.start())
            candidates.append((url, title, [line.strip()], publisher, publisher, published_at))

        for source_payload in self._iter_raw_response_sources(raw_response or {}):
            url = self._clean_url(str(source_payload.get("url") or source_payload.get("uri") or source_payload.get("link") or ""))
            title = source_payload.get("title")
            publisher = source_payload.get("publisher") or source_payload.get("source")
            published_at = self._parse_date(source_payload.get("published_at") or source_payload.get("date"))
            candidates.append((url, self._clean_text(title or ""), ["raw_response"], publisher, publisher, published_at))

        by_canonical: Dict[str, GeminiSourceCandidate] = {}
        for url, title, markers, publisher, _unused, published_at in candidates:
            canonical = canonicalize_url(url)
            if not canonical:
                continue
            domain = extract_domain(canonical)
            if not domain:
                continue

            source_type = infer_source_type(domain, report)
            existing = by_canonical.get(canonical)
            if existing:
                existing.citation_markers.extend([m for m in markers if m not in existing.citation_markers])
                if not existing.title and title:
                    existing.title = self._redact_secrets(title)
                if not existing.publisher and publisher:
                    existing.publisher = self._redact_secrets(str(publisher))
                if not existing.published_at and published_at:
                    existing.published_at = published_at
                continue

            source_id = f"gem-src-{len(by_canonical) + 1:03d}"
            by_canonical[canonical] = GeminiSourceCandidate(
                source_id=source_id,
                title=self._redact_secrets(title or self._title_from_url(canonical)),
                url=url,
                canonical_url=canonical,
                domain=domain,
                publisher=self._redact_secrets(str(publisher)) if publisher else None,
                published_at=published_at,
                source_type_hint=source_type,
                reliability_notes=f"Inferred as {source_type} from domain and report context.",
                citation_markers=markers,
            )

        return list(by_canonical.values())

    def build_evidence_candidates(
        self,
        sources: List[GeminiSourceCandidate],
        raw_report: str,
    ) -> List[GeminiEvidenceCandidate]:
        """Build local evidence candidates from source candidates."""
        evidence: List[GeminiEvidenceCandidate] = []
        for source in sources:
            snippet = self._snippet_for_source(source, raw_report)
            if not source.url or not source.domain or not snippet:
                continue
            snippet = self._redact_secrets(snippet[:2000])
            content_hash = hashlib.sha256(
                f"{source.canonical_url}{snippet}".encode("utf-8")
            ).hexdigest()
            evidence.append(GeminiEvidenceCandidate(
                id=evidence_id_for_source(source),
                source_id=source.source_id,
                url=source.url,
                canonical_url=source.canonical_url,
                domain=source.domain,
                publisher=source.publisher,
                published_at=source.published_at,
                retrieved_at=source.retrieved_at,
                content_hash=content_hash,
                snippet=snippet,
                source_type=source.source_type_hint,
                reliability_tier=reliability_tier_for_source(source.source_type_hint),
                provenance="LIVE_OSINT",
            ))
        return evidence

    def extract_candidate_claims(
        self,
        raw_report: str,
        sources: List[GeminiSourceCandidate],
    ) -> List[GeminiClaimCandidate]:
        """Extract atomic cited claims. Uncited narrative is not converted."""
        source_by_canonical = {source.canonical_url: source for source in sources}
        claims: List[GeminiClaimCandidate] = []
        seen_texts: set[str] = set()

        for segment in self._claim_segments(raw_report):
            canonical_urls = [canonicalize_url(url) for url in URL_RE.findall(segment)]
            canonical_urls = [url for url in canonical_urls if url in source_by_canonical]

            if not canonical_urls:
                if self._looks_like_claim(segment):
                    self._mark_unsupported_claim_skipped()
                continue

            if self._contains_probability_content(segment):
                self._probability_detected = True
                self._add_warning(
                    "PROBABILITY_CONTENT_QUARANTINED",
                    "A cited probability-like forecast sentence was quarantined from candidate claims.",
                    "HIGH",
                )
                continue

            text = self._clean_claim_text(segment)
            if len(text) < 12:
                continue
            text = text[:500]
            text_key = text.lower()
            if text_key in seen_texts:
                continue
            seen_texts.add(text_key)

            evidence_ids = [
                evidence_id_for_source(source_by_canonical[canonical])
                for canonical in canonical_urls
            ]
            horizon = self._infer_time_horizon(text)
            claim_id = "gem-claim-" + hashlib.sha256(
                f"{text}{','.join(evidence_ids)}".encode("utf-8")
            ).hexdigest()[:16]
            claims.append(GeminiClaimCandidate(
                id=claim_id,
                text=self._redact_secrets(text),
                evidence_ids=evidence_ids,
                confidence=0.55,
                confidence_justification=(
                    "Evidence-support confidence from cited Gemini Deep Research source text; "
                    "not a forecast probability."
                ),
                time_horizon=horizon,
                falsifiable=True,
            ))

        return claims

    def build_intelligence_gap(
        self,
        reason: str,
        missing_inputs: Optional[List[str]] = None,
        attempted_sources: Optional[List[str]] = None,
        severity: str = "MEDIUM",
        retryable: bool = True,
    ) -> GeminiIntelligenceGapCandidate:
        """Build a local IntelligenceGap-like record."""
        return GeminiIntelligenceGapCandidate(
            reason=self._redact_secrets(reason),
            missing_inputs=missing_inputs or [],
            attempted_sources=attempted_sources or [],
            retryable=retryable,
            severity=severity,
        )

    def to_agent_output_candidate(self, pack: GeminiEvidencePack) -> Any:
        """Convert a normalized pack to TheSeer AgentOutput if contracts import cleanly."""
        try:
            from app.graph.contracts import (  # noqa: PLC0415
                AgentOutput,
                ClaimItem,
                EvidenceItem,
                IntelligenceGap,
                OutputStatus,
                ProvenanceKind,
                SourceType,
                TimeHorizon,
            )

            is_fault = any(
                w.code in {"GEMINI_RESULT_FAILED", "GEMINI_RESULT_TIMEOUT", "NORMALIZER_EXCEPTION"}
                for w in pack.normalizer_warnings
            )
            has_supported_candidates = bool(pack.evidence_items and pack.claim_items)

            if is_fault:
                status = OutputStatus.SYSTEM_FAULT
            elif has_supported_candidates:
                status = OutputStatus.SUPPORTED
            else:
                status = OutputStatus.INTELLIGENCE_GAP

            gaps = [
                IntelligenceGap(
                    reason=gap.reason,
                    missing_inputs=gap.missing_inputs,
                    attempted_sources=gap.attempted_sources,
                    retryable=gap.retryable,
                    severity=gap.severity,  # type: ignore[arg-type]
                )
                for gap in pack.intelligence_gaps
            ]

            if status != OutputStatus.SUPPORTED and not gaps:
                gaps = [IntelligenceGap(
                    reason="Gemini Deep Research produced no supported candidate claims.",
                    missing_inputs=["supported source-backed claims"],
                    attempted_sources=[s.url for s in pack.sources],
                    retryable=True,
                    severity="MEDIUM",
                )]

            if status == OutputStatus.SUPPORTED:
                evidence = [
                    EvidenceItem(
                        id=item.id,
                        url=item.url,
                        canonical_url=item.canonical_url,
                        domain=item.domain,
                        publisher=item.publisher,
                        published_at=item.published_at,
                        retrieved_at=item.retrieved_at,
                        content_hash=item.content_hash,
                        snippet=item.snippet,
                        source_type=SourceType(item.source_type),
                        reliability_tier=item.reliability_tier,
                    )
                    for item in pack.evidence_items
                ]
                claims = [
                    ClaimItem(
                        id=item.id,
                        text=item.text,
                        evidence_ids=item.evidence_ids,
                        confidence=item.confidence,
                        confidence_justification=item.confidence_justification,
                        time_horizon=TimeHorizon(item.time_horizon),
                        falsifiable=item.falsifiable,
                        resolution_date=item.resolution_date,
                    )
                    for item in pack.claim_items
                ]
                confidence = min(0.7, max((c.confidence for c in pack.claim_items), default=0.55))
                provenance = ProvenanceKind.LIVE_OSINT
            else:
                evidence = []
                claims = []
                confidence = 0.0
                provenance = ProvenanceKind.NONE

            uncertainty_notes = list(pack.uncertainty_notes)
            uncertainty_notes.extend(
                f"{warning.code}: {warning.message}" for warning in pack.normalizer_warnings
            )

            summary = "; ".join(claim.text for claim in pack.claim_items[:3])[:1000] or None

            return AgentOutput(
                agent_id="gemini_deep_research",
                status=status,
                provenance=provenance,
                gaps=gaps,
                claims=claims,
                evidence=evidence,
                signals=[],
                assumptions=[
                    "Gemini Deep Research output was normalized locally from cited raw report text.",
                    "Candidate confidence is evidence extraction confidence only, not an event probability.",
                ],
                uncertainty_notes=uncertainty_notes[:10],
                confidence=confidence,
                confidence_justification=(
                    "Evidence extraction confidence only; this is not a forecast probability "
                    "and must not be used as QuantifierV2 signal input."
                ),
                summary=summary,
            )
        except Exception as exc:  # noqa: BLE001
            warning = GeminiNormalizerWarning(
                code="AGENT_OUTPUT_CONVERSION_FAILED",
                message=f"AgentOutput conversion failed: {exc.__class__.__name__}",
                severity="HIGH",
            )
            pack.normalizer_warnings.append(warning)
            return GeminiAgentOutputCandidateFailure(
                error_type=exc.__class__.__name__,
                error_message=str(exc),
                warnings=list(pack.normalizer_warnings),
            )

    def _reset(self) -> None:
        self._warnings = []
        self._secret_detected = False
        self._probability_detected = False
        self._time_horizon_inferred = False
        self._unsupported_claim_skipped = False

    def _add_warning(self, code: str, message: str, severity: str = "MEDIUM") -> None:
        if any(w.code == code and w.message == message for w in self._warnings):
            return
        self._warnings.append(GeminiNormalizerWarning(
            code=code,
            message=message,
            severity=severity,
        ))

    def _mark_unsupported_claim_skipped(self) -> None:
        if self._unsupported_claim_skipped:
            return
        self._unsupported_claim_skipped = True
        self._add_warning(
            "UNSUPPORTED_CLAIM_SKIPPED",
            "Uncited narrative claim-like text was not converted into a candidate claim.",
            "MEDIUM",
        )

    def _redact_secrets(self, text: Any) -> str:
        value = str(text or "")
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                self._secret_detected = True
                value = pattern.sub("[REDACTED_SECRET]", value)
        return value

    def _redact_obj(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {self._redact_secrets(k): self._redact_obj(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._redact_obj(v) for v in value]
        if isinstance(value, str):
            return self._redact_secrets(value)
        return value

    def _contains_probability_content(self, text: str) -> bool:
        return any(pattern.search(text or "") for pattern in PROBABILITY_PATTERNS)

    def _iter_raw_response_sources(self, raw_response: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        for key in ("citations", "sources"):
            value = raw_response.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
        metadata = raw_response.get("metadata")
        if isinstance(metadata, dict):
            yield from self._iter_raw_response_sources(metadata)

    def _clean_url(self, url: str) -> str:
        return (url or "").strip().rstrip(".,;:!?)\"]}'")

    def _clean_text(self, text: str) -> str:
        return " ".join(self._redact_secrets(text).split())

    def _line_containing(self, text: str, index: int) -> str:
        start = text.rfind("\n", 0, index) + 1
        end = text.find("\n", index)
        if end == -1:
            end = len(text)
        return text[start:end]

    def _extract_metadata_from_line(self, line: str) -> Tuple[Optional[str], Optional[str], Optional[datetime]]:
        cleaned = line.strip("-* 1234567890.").strip()
        published_at = self._parse_date(cleaned)
        publisher = None
        title = None

        title_match = re.search(r"(?:title|source)\s*:\s*([^|]+)", cleaned, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).split("http", 1)[0].strip(" -")

        pub_match = re.search(r"(?:publisher|publication)\s*:\s*([^|,]+)", cleaned, re.IGNORECASE)
        if pub_match:
            publisher = pub_match.group(1).strip()

        if not title:
            prefix = re.split(r"https?://", cleaned, maxsplit=1)[0].strip(" -,:")
            if prefix and len(prefix) <= 180:
                title = prefix

        return title or None, publisher or None, published_at

    def _extract_metadata_near(self, text: str, index: int) -> Tuple[Optional[str], Optional[str], Optional[datetime]]:
        lines = text.splitlines()
        char_count = 0
        target_line = 0
        for idx, line in enumerate(lines):
            next_count = char_count + len(line) + 1
            if char_count <= index < next_count:
                target_line = idx
                break
            char_count = next_count

        title = None
        publisher = None
        published_at = None
        for line in lines[max(0, target_line - 4): min(len(lines), target_line + 5)]:
            stripped = line.strip()
            title_match = re.match(r"[-*]?\s*Title\s*:\s*(.+)$", stripped, re.IGNORECASE)
            if title_match and not title:
                title = title_match.group(1).strip()
            publisher_match = re.match(r"[-*]?\s*Publisher\s*:\s*(.+)$", stripped, re.IGNORECASE)
            if publisher_match and not publisher:
                publisher = publisher_match.group(1).strip()
            date_match = re.match(r"[-*]?\s*(?:Date|Published)\s*:\s*(.+)$", stripped, re.IGNORECASE)
            if date_match and not published_at:
                published_at = self._parse_date(date_match.group(1))
        return title, publisher, published_at

    def _extract_date_near(self, text: str, index: int) -> Optional[datetime]:
        window = text[max(0, index - 220): index + 220]
        return self._parse_date(window)

    def _parse_date(self, value: Any) -> Optional[datetime]:
        text = str(value or "")
        match = re.search(r"\b(20\d{2}|19\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", text)
        if not match:
            return None
        year, month, day = (int(part) for part in match.groups())
        try:
            return datetime(year, month, day, tzinfo=timezone.utc)
        except ValueError:
            return None

    def _title_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        slug = parsed.path.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").replace("_", " ")
        return slug.title() if slug else parsed.netloc

    def _snippet_for_source(self, source: GeminiSourceCandidate, raw_report: str) -> str:
        canonical = source.canonical_url
        for marker in source.citation_markers:
            if marker and marker != "raw_response":
                return self._clean_report_snippet(marker)
        for match in URL_RE.finditer(raw_report):
            if canonicalize_url(match.group(0)) == canonical:
                return self._clean_report_snippet(self._line_containing(raw_report, match.start()))
        if source.title:
            return source.title
        return ""

    def _clean_report_snippet(self, text: str) -> str:
        cleaned = MARKDOWN_LINK_RE.sub(lambda m: m.group(1), text or "")
        cleaned = URL_RE.sub("", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:;")
        return cleaned

    def _claim_segments(self, raw_report: str) -> List[str]:
        segments: List[str] = []
        for line in (raw_report or "").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if URL_RE.search(stripped):
                segments.append(stripped)
                continue
            for sentence in re.split(r"(?<=[.!?])\s+", stripped):
                if sentence.strip():
                    segments.append(sentence.strip())
        return segments

    def _looks_like_claim(self, text: str) -> bool:
        lowered = (text or "").lower()
        return len(lowered) > 25 and any(hint in lowered for hint in UNSUPPORTED_CLAIM_HINTS)

    def _clean_claim_text(self, segment: str) -> str:
        text = MARKDOWN_LINK_RE.sub(lambda m: m.group(1), segment or "")
        text = URL_RE.sub("", text)
        text = re.sub(r"^\s*[-*]\s*", "", text)
        text = re.sub(r"\s+", " ", text).strip(" -:;")
        return text

    def _infer_time_horizon(self, text: str) -> str:
        lowered = (text or "").lower()
        if any(term in lowered for term in ("current", "immediate", "today", "this week", "now", "near-term")):
            return "SHORT_TERM"
        if any(term in lowered for term in ("multi-year", "long-term", "structural", "by 2030", "by 2035")):
            return "LONG_TERM"
        if any(term in lowered for term in ("month", "quarter", "1-12", "next year", "within a year")):
            return "MEDIUM_TERM"
        if not self._time_horizon_inferred:
            self._time_horizon_inferred = True
            self._add_warning(
                "TIME_HORIZON_INFERRED",
                "Time horizon was unclear for at least one claim and defaulted to MEDIUM_TERM.",
                "LOW",
            )
        return "MEDIUM_TERM"


def canonicalize_url(url: str) -> str:
    """Local URL canonicalization without fetching."""
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            return ""
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        query_items = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in COMMON_TRACKING_PARAMS
        ]
        query = urlencode(query_items, doseq=True)
        path = parsed.path or ""
        return urlunparse((scheme, netloc, path, "", query, ""))
    except Exception:
        return ""


def extract_domain(url: str) -> str:
    parsed = urlparse(url or "")
    domain = parsed.netloc.lower()
    return domain[4:] if domain.startswith("www.") else domain


def _domain_matches(domain: str, known_domains: set[str]) -> bool:
    return any(domain == known or domain.endswith("." + known) for known in known_domains)


def infer_source_type(domain: str, context: str = "") -> str:
    """Infer TheSeer-compatible source type string conservatively."""
    normalized = (domain or "").lower()
    if normalized.endswith(".gov") or ".gov." in normalized or _domain_matches(normalized, OFFICIAL_DOMAINS):
        return "primary_data"
    if _domain_matches(normalized, SOCIAL_DOMAINS):
        return "social"
    if _domain_matches(normalized, NEWS_DOMAINS):
        return "primary_reporting"
    if _domain_matches(normalized, THINK_TANK_DOMAINS):
        return "analysis"
    if _domain_matches(normalized, AGGREGATOR_DOMAINS):
        return "aggregator"
    if any(term in (context or "").lower() for term in ("research", "report", "analysis", "study")):
        return "analysis"
    return "aggregator"


def reliability_tier_for_source(source_type: str) -> int:
    if source_type == "primary_data":
        return 1
    if source_type == "primary_reporting":
        return 2
    if source_type == "analysis":
        return 3
    if source_type == "social":
        return 5
    return 4


def evidence_id_for_source(source: GeminiSourceCandidate) -> str:
    digest = hashlib.sha256(f"{source.source_id}:{source.canonical_url}".encode("utf-8")).hexdigest()
    return f"gemdr-{digest[:16]}"
