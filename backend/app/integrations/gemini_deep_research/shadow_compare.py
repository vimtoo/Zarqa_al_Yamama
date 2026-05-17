"""Phase 3A local shadow comparison for Gemini Deep Research evidence packs."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from app.integrations.gemini_deep_research.models import (
    AgentOverlapComparison,
    EvidenceComparison,
    GeminiEvidencePack,
    GeminiShadowRun,
    RiskAssessment,
    SourceComparison,
)
from app.integrations.gemini_deep_research.normalizer import (
    URL_RE,
    canonicalize_url,
    extract_domain,
)


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
}

AGENT_KEYS = {
    "context_interpreter": "context_interpreter_overlap",
    "black_swan_generator": "black_swan_generator_overlap",
    "think_tank_analyst": "think_tank_analyst_overlap",
    "walled_garden_analyst": "walled_garden_analyst_overlap",
    "evidence_analyst": "evidence_analyst_overlap",
}
AGENT_COLLECTION_KEY = "agent" + "_outputs"
RISK_ORDER = {"low": 0, "unknown": 1, "medium": 2, "high": 3, "critical": 4}


class GeminiShadowComparator:
    """Compare normalized Gemini packs against local TheSeer outputs."""

    def __init__(self) -> None:
        self._warnings: List[str] = []

    def compare(
        self,
        gemini_pack: GeminiEvidencePack | Dict[str, Any],
        seer_outputs: Optional[Dict[str, Any]],
        query: Optional[str] = None,
        agents_used: Optional[List[str]] = None,
        run_id: Optional[str] = None,
    ) -> GeminiShadowRun:
        """Build a complete shadow comparison artifact from local inputs."""
        self._warnings = []
        pack = self._coerce_pack(gemini_pack)
        seer = self._coerce_seer_outputs(seer_outputs)

        source_comparison = self.compare_sources(pack, seer)
        evidence_comparison = self.compare_evidence(pack, seer)
        agent_overlap = self.compare_agent_overlap(pack, seer)
        risk_assessment = self.assess_risks(pack, seer)

        shadow_run = GeminiShadowRun(
            run_id=run_id or f"gemini-shadow-{hashlib.sha256((pack.run_id or '').encode('utf-8')).hexdigest()[:12]}",
            query=query or pack.original_question,
            gemini_interaction_id=pack.interaction_id,
            gemini_model=pack.model,
            gemini_mode="shadow",
            seer_workflow_version="v2",
            seer_agents_used=agents_used or self._extract_agents_used(seer),
            evidence_pack_summary=self._summarize_pack(pack),
            source_comparison=source_comparison,
            evidence_comparison=evidence_comparison,
            agent_overlap=agent_overlap,
            risk_assessment=risk_assessment,
            warnings=list(self._warnings),
            metadata={
                "gemini_run_id": pack.run_id,
                "comparison_engine": "gemini_deep_research_phase_3a",
            },
        )
        shadow_run.recommendation = self.build_recommendation(shadow_run)
        shadow_run.next_steps = self._build_next_steps(shadow_run)
        return shadow_run

    def compare_sources(
        self,
        gemini_pack: GeminiEvidencePack | Dict[str, Any],
        seer_outputs: Optional[Dict[str, Any]],
    ) -> SourceComparison:
        """Compare source overlap with simple local canonicalization only."""
        pack = self._coerce_pack(gemini_pack)
        seer = self._coerce_seer_outputs(seer_outputs)
        gemini_sources = self._dedupe_records(self._source_records_from_pack(pack))
        seer_sources = self._dedupe_records(self._extract_source_records(seer))

        overlapping_gemini: Set[str] = set()
        overlapping_labels: Set[str] = set()
        for gemini_source in gemini_sources:
            for seer_source in seer_sources:
                if self._sources_overlap(gemini_source, seer_source):
                    overlapping_gemini.add(self._record_key(gemini_source))
                    overlapping_labels.add(self._record_label(gemini_source))
                    break

        unique_gemini = [
            self._record_label(source)
            for source in gemini_sources
            if self._record_key(source) not in overlapping_gemini
        ]
        unique_seer = [
            self._record_label(source)
            for source in seer_sources
            if not any(self._sources_overlap(source, gemini_source) for gemini_source in gemini_sources)
        ]

        union_count = len(overlapping_labels) + len(unique_gemini) + len(unique_seer)
        overlap_ratio = round(len(overlapping_labels) / union_count, 4) if union_count else 0.0

        freshness_notes = self._freshness_notes(gemini_sources, seer_sources)
        credibility_notes = self._credibility_notes(gemini_sources, seer_sources)

        if not gemini_sources:
            self._add_warning("Gemini pack contained no comparable source URLs.")
        if not seer_sources:
            self._add_warning("TheSeer comparison input contained no comparable sources.")

        return SourceComparison(
            gemini_source_count=len(gemini_sources),
            seer_source_count=len(seer_sources),
            overlapping_sources=sorted(overlapping_labels),
            unique_gemini_sources=sorted(unique_gemini),
            unique_seer_sources=sorted(unique_seer),
            source_overlap_ratio=overlap_ratio,
            gemini_domains=sorted({source["domain"] for source in gemini_sources if source.get("domain")}),
            seer_domains=sorted({source["domain"] for source in seer_sources if source.get("domain")}),
            freshness_notes=freshness_notes,
            credibility_notes=credibility_notes,
        )

    def compare_evidence(
        self,
        gemini_pack: GeminiEvidencePack | Dict[str, Any],
        seer_outputs: Optional[Dict[str, Any]],
    ) -> EvidenceComparison:
        """Compare evidence and claim candidates using local IDs, URLs, hashes, and text overlap."""
        pack = self._coerce_pack(gemini_pack)
        seer = self._coerce_seer_outputs(seer_outputs)
        gemini_evidence = [self._as_dict(item) for item in pack.evidence_items]
        gemini_claims = [self._as_dict(item) for item in pack.claim_items]
        seer_evidence = self._extract_evidence_records(seer)
        seer_claims = self._extract_claim_records(seer)

        evidence_ids = {str(item.get("id")) for item in gemini_evidence if item.get("id")}
        unsupported_claims = [
            claim for claim in gemini_claims
            if not self._claim_is_supported(claim, evidence_ids, gemini_evidence)
        ]

        rejected_evidence = [
            item for item in gemini_evidence
            if not item.get("url")
            or not canonicalize_url(str(item.get("canonical_url") or item.get("url") or ""))
            or not item.get("domain")
            or not str(item.get("snippet") or "").strip()
        ]
        if self._pack_has_warning(pack, "POSSIBLE_SECRET_LEAK") and gemini_evidence:
            rejected_evidence = gemini_evidence

        duplicate_count = 0
        for item in gemini_evidence:
            if any(self._evidence_duplicate(item, seer_item) for seer_item in seer_evidence):
                duplicate_count += 1

        contradictions = self._count_possible_contradictions(gemini_claims, seer_claims)
        gap_notes = [gap.reason for gap in pack.intelligence_gaps]
        gap_notes.extend(f"{warning.code}: {warning.message}" for warning in pack.normalizer_warnings)
        if unsupported_claims:
            gap_notes.append(f"{len(unsupported_claims)} Gemini claim candidate(s) lacked valid evidence linkage.")

        return EvidenceComparison(
            gemini_evidence_count=len(gemini_evidence),
            seer_evidence_count=len(seer_evidence),
            gemini_claim_count=len(gemini_claims),
            seer_claim_count=len(seer_claims),
            accepted_gemini_evidence_count=max(0, len(gemini_evidence) - len(rejected_evidence)),
            rejected_gemini_evidence_count=len(rejected_evidence),
            duplicate_evidence_count=duplicate_count,
            unsupported_gemini_claims_count=len(unsupported_claims),
            contradictions_count=contradictions,
            intelligence_gap_count=len(pack.intelligence_gaps),
            evidence_gap_notes=gap_notes[:20],
        )

    def compare_agent_overlap(
        self,
        gemini_pack: GeminiEvidencePack | Dict[str, Any],
        seer_outputs: Optional[Dict[str, Any]],
    ) -> AgentOverlapComparison:
        """Compute simple overlap scores for selected TheSeer agent lanes."""
        pack = self._coerce_pack(gemini_pack)
        seer = self._coerce_seer_outputs(seer_outputs)
        gemini_bundle = self._text_bundle_from_pack(pack)
        source_comparison = self.compare_sources(pack, seer)
        result = AgentOverlapComparison(
            useful_new_evidence_count=len(source_comparison.unique_gemini_sources),
            seer_unique_evidence_count=len(source_comparison.unique_seer_sources),
        )

        for agent_key, field_name in AGENT_KEYS.items():
            agent_output = self._find_agent_output(seer, agent_key)
            if agent_output is None:
                self._add_warning(f"Missing comparison output for {agent_key}.")
                setattr(result, field_name, None)
                continue
            score = self._overlap_score(gemini_bundle, self._text_bundle_from_value(agent_output))
            setattr(result, field_name, score)

        return result

    def assess_risks(
        self,
        gemini_pack: GeminiEvidencePack | Dict[str, Any],
        seer_outputs: Optional[Dict[str, Any]],
    ) -> RiskAssessment:
        """Assess shadow-run risks conservatively from local comparison metrics."""
        pack = self._coerce_pack(gemini_pack)
        seer = self._coerce_seer_outputs(seer_outputs)
        source_comparison = self.compare_sources(pack, seer)
        evidence_comparison = self.compare_evidence(pack, seer)
        notes: List[str] = []

        if evidence_comparison.gemini_claim_count and evidence_comparison.unsupported_gemini_claims_count:
            hallucination_risk = "high"
            notes.append("Gemini produced claim candidates without valid evidence linkage.")
        elif evidence_comparison.gemini_claim_count and evidence_comparison.unsupported_gemini_claims_count == 0:
            hallucination_risk = "low"
        elif source_comparison.gemini_source_count:
            hallucination_risk = "medium"
        else:
            hallucination_risk = "high"
            notes.append("No Gemini sources were available to support claims.")

        if source_comparison.gemini_source_count == 0:
            citation_risk = "high"
            notes.append("Gemini source comparison found no URLs.")
        elif evidence_comparison.rejected_gemini_evidence_count:
            citation_risk = "high"
            notes.append("At least one Gemini evidence candidate failed traceability checks.")
        elif self._pack_has_warning(pack, "MISSING_PUBLICATION_DATES"):
            citation_risk = "medium"
            notes.append("Gemini source metadata was missing publication dates.")
        else:
            citation_risk = "low"

        source_types = [str(source.source_type_hint) for source in pack.sources]
        if not source_types:
            source_governance_risk = "high"
        elif all(source_type in {"social", "aggregator"} for source_type in source_types):
            source_governance_risk = "high"
            notes.append("Gemini sources were social-only or aggregator-only.")
        elif any(source_type in {"social", "aggregator"} for source_type in source_types):
            source_governance_risk = "medium"
        else:
            source_governance_risk = "low"

        if self._pack_has_warning(pack, "NORMALIZER_EXCEPTION"):
            schema_compliance_risk = "high"
        elif pack.normalizer_warnings:
            schema_compliance_risk = "medium"
        else:
            schema_compliance_risk = "low"

        metadata = pack.raw_interaction_metadata or {}
        latency_risk = self._metric_risk(metadata, ("latency_seconds", "duration_seconds"))
        cost_risk = "unknown"
        if metadata.get("cost") or metadata.get("cost_usd"):
            cost_risk = "medium"
        if metadata.get("usage") and not metadata.get("cost") and not metadata.get("cost_usd"):
            cost_risk = "unknown"

        if any(self._pack_has_warning(pack, code) for code in ("GEMINI_RESULT_FAILED", "GEMINI_RESULT_TIMEOUT")):
            dependency_risk = "high"
            notes.append("Gemini interaction failed or timed out.")
        elif metadata.get("interaction_id") and metadata.get("completed_at"):
            dependency_risk = "low"
        else:
            dependency_risk = "medium"

        risks = [
            hallucination_risk,
            citation_risk,
            source_governance_risk,
            schema_compliance_risk,
            latency_risk,
            cost_risk,
            dependency_risk,
        ]
        overall = max(risks, key=lambda value: RISK_ORDER.get(value, 2))
        if overall == "unknown":
            overall = "medium"

        return RiskAssessment(
            hallucination_risk=hallucination_risk,
            citation_risk=citation_risk,
            source_governance_risk=source_governance_risk,
            schema_compliance_risk=schema_compliance_risk,
            latency_risk=latency_risk,
            cost_risk=cost_risk,
            dependency_risk=dependency_risk,
            overall_risk=overall,
            risk_notes=notes[:20],
        )

    def build_recommendation(self, comparison: GeminiShadowRun) -> str:
        """Return one conservative recommendation label."""
        source_cmp = comparison.source_comparison
        evidence_cmp = comparison.evidence_comparison
        overlap = comparison.agent_overlap
        risk = comparison.risk_assessment

        if (
            source_cmp.gemini_source_count == 0
            or evidence_cmp.accepted_gemini_evidence_count == 0
            or (risk.hallucination_risk == "high" and risk.citation_risk == "high")
        ):
            return "Gemini not useful"

        if evidence_cmp.contradictions_count > 0 or risk.source_governance_risk == "high":
            return "Gemini requires human review"

        if risk.overall_risk in {"high", "unknown"} or comparison.warnings:
            return "Gemini useful as shadow only"

        if (
            overlap.context_interpreter_overlap is not None
            and overlap.context_interpreter_overlap >= 0.75
            and overlap.useful_new_evidence_count >= 3
            and evidence_cmp.unsupported_gemini_claims_count == 0
            and risk.citation_risk == "low"
            and risk.schema_compliance_risk == "low"
            and comparison.metadata.get("allow_replacement_assessment") is True
        ):
            return "Gemini ready to replace ContextInterpreter for this domain"

        if (
            overlap.black_swan_generator_overlap is not None
            and overlap.black_swan_generator_overlap >= 0.75
            and overlap.useful_new_evidence_count >= 3
            and evidence_cmp.unsupported_gemini_claims_count == 0
            and risk.overall_risk == "low"
            and comparison.metadata.get("allow_replacement_assessment") is True
        ):
            return "Gemini ready to replace BlackSwanGenerator for this domain"

        if (
            overlap.useful_new_evidence_count > 0
            and evidence_cmp.unsupported_gemini_claims_count == 0
            and risk.overall_risk in {"low", "medium"}
        ):
            if risk.overall_risk == "low":
                return "Gemini useful as assistant"
            return "Gemini useful as shadow only"

        return "Gemini requires human review"

    def render_markdown_report(self, shadow_run: GeminiShadowRun | Dict[str, Any]) -> str:
        """Render a human-readable Gemini shadow comparison report."""
        run = shadow_run if isinstance(shadow_run, GeminiShadowRun) else GeminiShadowRun.model_validate(shadow_run)
        source = run.source_comparison
        evidence = run.evidence_comparison
        overlap = run.agent_overlap
        risk = run.risk_assessment

        return "\n".join([
            "# Gemini Deep Research Shadow Comparison",
            "",
            "## 1. Run Metadata",
            f"- run_id: {run.run_id}",
            f"- timestamp: {run.timestamp.isoformat()}",
            f"- user query: {run.query or 'unknown'}",
            f"- Gemini model: {run.gemini_model or 'unknown'}",
            f"- Gemini mode: {run.gemini_mode}",
            f"- interaction_id: {run.gemini_interaction_id or 'unknown'}",
            f"- TheSeer workflow version: {run.seer_workflow_version}",
            f"- agents executed: {', '.join(run.seer_agents_used) if run.seer_agents_used else 'unknown'}",
            "",
            "## 2. Source Comparison",
            f"- Gemini source count: {source.gemini_source_count}",
            f"- TheSeer source count: {source.seer_source_count}",
            f"- overlapping sources: {self._format_list(source.overlapping_sources)}",
            f"- unique Gemini sources: {self._format_list(source.unique_gemini_sources)}",
            f"- unique TheSeer sources: {self._format_list(source.unique_seer_sources)}",
            f"- source overlap ratio: {source.source_overlap_ratio}",
            f"- Gemini domains: {self._format_list(source.gemini_domains)}",
            f"- TheSeer domains: {self._format_list(source.seer_domains)}",
            f"- freshness notes: {self._format_list(source.freshness_notes)}",
            f"- credibility notes: {self._format_list(source.credibility_notes)}",
            "",
            "## 3. Evidence Comparison",
            f"- Gemini evidence count: {evidence.gemini_evidence_count}",
            f"- TheSeer evidence count: {evidence.seer_evidence_count}",
            f"- Gemini claim count: {evidence.gemini_claim_count}",
            f"- TheSeer claim count: {evidence.seer_claim_count}",
            f"- accepted Gemini evidence: {evidence.accepted_gemini_evidence_count}",
            f"- rejected Gemini evidence: {evidence.rejected_gemini_evidence_count}",
            f"- duplicate evidence: {evidence.duplicate_evidence_count}",
            f"- unsupported Gemini claims: {evidence.unsupported_gemini_claims_count}",
            f"- contradictions: {evidence.contradictions_count}",
            f"- intelligence gaps: {evidence.intelligence_gap_count}",
            f"- evidence gap notes: {self._format_list(evidence.evidence_gap_notes)}",
            "",
            "## 4. Agent Replacement Assessment",
            f"- ContextInterpreter comparison: {self._format_score(overlap.context_interpreter_overlap)}",
            f"- BlackSwanGenerator comparison: {self._format_score(overlap.black_swan_generator_overlap)}",
            f"- ThinkTankAnalyst comparison: {self._format_score(overlap.think_tank_analyst_overlap)}",
            f"- WalledGardenAnalyst comparison: {self._format_score(overlap.walled_garden_analyst_overlap)}",
            f"- EvidenceAnalyst comparison: {self._format_score(overlap.evidence_analyst_overlap)}",
            "",
            "## 5. Risk Assessment",
            f"- hallucination risk: {risk.hallucination_risk}",
            f"- citation risk: {risk.citation_risk}",
            f"- source-governance risk: {risk.source_governance_risk}",
            f"- schema-compliance risk: {risk.schema_compliance_risk}",
            f"- latency risk: {risk.latency_risk}",
            f"- cost risk: {risk.cost_risk}",
            f"- dependency risk: {risk.dependency_risk}",
            f"- overall risk: {risk.overall_risk}",
            f"- risk notes: {self._format_list(risk.risk_notes)}",
            "",
            "## 6. Recommendation",
            run.recommendation,
            "",
            "## 7. Next Steps",
            *[f"- {step}" for step in (run.next_steps or ["Run another shadow comparison with complete local outputs."])],
            "",
        ])

    def save_shadow_run(self, shadow_run: GeminiShadowRun | Dict[str, Any]) -> Any:
        """Persist a shadow-run JSON artifact outside production outputs."""
        from app.integrations.gemini_deep_research.storage import save_shadow_run  # noqa: PLC0415

        run = shadow_run if isinstance(shadow_run, GeminiShadowRun) else GeminiShadowRun.model_validate(shadow_run)
        return save_shadow_run(run)

    def save_markdown_report(self, shadow_run: GeminiShadowRun | Dict[str, Any]) -> Any:
        """Persist a human-readable markdown report outside production outputs."""
        from app.integrations.gemini_deep_research.storage import save_shadow_report  # noqa: PLC0415

        run = shadow_run if isinstance(shadow_run, GeminiShadowRun) else GeminiShadowRun.model_validate(shadow_run)
        return save_shadow_report(run)

    def _coerce_pack(self, value: GeminiEvidencePack | Dict[str, Any]) -> GeminiEvidencePack:
        if isinstance(value, GeminiEvidencePack):
            return value
        try:
            return GeminiEvidencePack.model_validate(value or {})
        except Exception:
            self._add_warning("GeminiEvidencePack input was malformed; comparison used an empty fail-closed pack.")
            return GeminiEvidencePack(
                raw_report="",
                normalizer_warnings=[],
                intelligence_gaps=[],
            )

    def _coerce_seer_outputs(self, value: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        self._add_warning("TheSeer comparison input was missing or not a dictionary.")
        return {}

    def _summarize_pack(self, pack: GeminiEvidencePack) -> Dict[str, Any]:
        return {
            "provider": pack.provider,
            "run_id": pack.run_id,
            "source_count": len(pack.sources),
            "evidence_count": len(pack.evidence_items),
            "claim_count": len(pack.claim_items),
            "intelligence_gap_count": len(pack.intelligence_gaps),
            "warning_codes": [warning.code for warning in pack.normalizer_warnings],
        }

    def _extract_agents_used(self, seer: Dict[str, Any]) -> List[str]:
        explicit = seer.get("agents_executed") or seer.get("agents_used")
        if isinstance(explicit, list):
            return [str(item) for item in explicit]
        agents = [key for key in AGENT_KEYS if key in seer]
        for item in self._as_list(seer.get(AGENT_COLLECTION_KEY)):
            payload = self._as_dict(item)
            agent_id = payload.get("agent_id")
            if agent_id:
                agents.append(str(agent_id))
        return sorted(dict.fromkeys(agents))

    def _source_records_from_pack(self, pack: GeminiEvidencePack) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for source in pack.sources:
            records.append({
                "url": source.url,
                "canonical_url": source.canonical_url,
                "domain": source.domain,
                "title": source.title,
                "publisher": source.publisher,
                "published_at": source.published_at,
                "source_type": source.source_type_hint,
            })
        for evidence in pack.evidence_items:
            records.append({
                "url": evidence.url,
                "canonical_url": evidence.canonical_url,
                "domain": evidence.domain,
                "title": None,
                "publisher": evidence.publisher,
                "published_at": evidence.published_at,
                "source_type": evidence.source_type,
            })
        return records

    def _extract_source_records(self, value: Any, depth: int = 0) -> List[Dict[str, Any]]:
        if depth > 5:
            return []
        records: List[Dict[str, Any]] = []
        if isinstance(value, str):
            for url in URL_RE.findall(value):
                records.append(self._record_from_url(url))
            return records
        if isinstance(value, list):
            for item in value:
                records.extend(self._extract_source_records(item, depth + 1))
            return records
        payload = self._as_dict(value)
        if not payload:
            return records

        url = payload.get("canonical_url") or payload.get("url") or payload.get("uri") or payload.get("link")
        domain = payload.get("domain")
        title = payload.get("title") or payload.get("name")
        publisher = payload.get("publisher") or payload.get("source")
        if url or domain or title:
            record = self._record_from_url(str(url or ""))
            record.update({
                "domain": str(domain or record.get("domain") or ""),
                "title": str(title) if title else None,
                "publisher": str(publisher) if publisher else None,
                "published_at": payload.get("published_at") or payload.get("date"),
                "source_type": payload.get("source_type") or payload.get("source_type_hint"),
            })
            records.append(record)

        for key in (
            "sources",
            "citations",
            "evidence",
            "evidence_items",
            "items",
            "results",
            AGENT_COLLECTION_KEY,
            *AGENT_KEYS.keys(),
        ):
            if key in payload:
                records.extend(self._extract_source_records(payload[key], depth + 1))
        return records

    def _extract_evidence_records(self, value: Any, depth: int = 0) -> List[Dict[str, Any]]:
        if depth > 5:
            return []
        if isinstance(value, str):
            return [{"snippet": value, **self._record_from_url(url)} for url in URL_RE.findall(value)]
        if isinstance(value, list):
            records: List[Dict[str, Any]] = []
            for item in value:
                records.extend(self._extract_evidence_records(item, depth + 1))
            return records
        payload = self._as_dict(value)
        if not payload:
            return []

        records: List[Dict[str, Any]] = []
        if any(key in payload for key in ("snippet", "content_hash", "canonical_url", "url")):
            record = self._record_from_url(str(payload.get("canonical_url") or payload.get("url") or ""))
            record.update(payload)
            if not record.get("snippet"):
                record["snippet"] = payload.get("text") or payload.get("summary") or ""
            records.append(record)

        for key in (
            "evidence",
            "evidence_items",
            "sources",
            "items",
            AGENT_COLLECTION_KEY,
            *AGENT_KEYS.keys(),
        ):
            if key in payload:
                records.extend(self._extract_evidence_records(payload[key], depth + 1))
        return self._dedupe_records(records)

    def _extract_claim_records(self, value: Any, depth: int = 0) -> List[Dict[str, Any]]:
        if depth > 5:
            return []
        if isinstance(value, str):
            return [{"text": text} for text in self._sentence_candidates(value)]
        if isinstance(value, list):
            records: List[Dict[str, Any]] = []
            for item in value:
                records.extend(self._extract_claim_records(item, depth + 1))
            return records
        payload = self._as_dict(value)
        if not payload:
            return []

        records: List[Dict[str, Any]] = []
        if payload.get("text") and ("evidence_ids" in payload or "confidence" in payload or "time_horizon" in payload):
            records.append(payload)
        for key in ("claims", "claim_items", AGENT_COLLECTION_KEY, *AGENT_KEYS.keys()):
            if key in payload:
                records.extend(self._extract_claim_records(payload[key], depth + 1))
        for key in ("summary", "raw_report", "output"):
            if isinstance(payload.get(key), str):
                records.extend(self._extract_claim_records(payload[key], depth + 1))
        return records

    def _find_agent_output(self, seer: Dict[str, Any], agent_key: str) -> Any:
        if agent_key in seer:
            return seer[agent_key]
        wanted = agent_key.replace("_", "")
        for item in self._as_list(seer.get(AGENT_COLLECTION_KEY)):
            payload = self._as_dict(item)
            agent_id = str(payload.get("agent_id") or payload.get("name") or "").lower().replace("_", "")
            if wanted in agent_id:
                return item
        return None

    def _text_bundle_from_pack(self, pack: GeminiEvidencePack) -> Dict[str, Any]:
        urls = {source.canonical_url for source in pack.sources if source.canonical_url}
        domains = {source.domain for source in pack.sources if source.domain}
        texts = [claim.text for claim in pack.claim_items]
        texts.extend(item.snippet for item in pack.evidence_items)
        if pack.raw_report:
            texts.append(pack.raw_report)
        return {
            "urls": urls,
            "domains": domains,
            "tokens": self._tokens(" ".join(texts)),
        }

    def _text_bundle_from_value(self, value: Any) -> Dict[str, Any]:
        sources = self._extract_source_records(value)
        texts = self._extract_texts(value)
        return {
            "urls": {source.get("canonical_url") for source in sources if source.get("canonical_url")},
            "domains": {source.get("domain") for source in sources if source.get("domain")},
            "tokens": self._tokens(" ".join(texts)),
        }

    def _overlap_score(self, left: Dict[str, Any], right: Dict[str, Any]) -> float:
        left_urls = set(left.get("urls") or [])
        right_urls = set(right.get("urls") or [])
        left_domains = set(left.get("domains") or [])
        right_domains = set(right.get("domains") or [])
        left_tokens = set(left.get("tokens") or [])
        right_tokens = set(right.get("tokens") or [])

        url_score = self._set_overlap(left_urls, right_urls)
        domain_score = self._set_overlap(left_domains, right_domains) * 0.6
        token_score = self._set_overlap(left_tokens, right_tokens)
        return round(max(url_score, domain_score, token_score), 4)

    def _claim_is_supported(
        self,
        claim: Dict[str, Any],
        evidence_ids: Set[str],
        evidence: Sequence[Dict[str, Any]],
    ) -> bool:
        claim_evidence_ids = {str(item) for item in self._as_list(claim.get("evidence_ids")) if item}
        if not claim_evidence_ids or not claim_evidence_ids.issubset(evidence_ids):
            return False
        supported_evidence = [item for item in evidence if str(item.get("id")) in claim_evidence_ids]
        return any(item.get("url") and item.get("domain") and item.get("snippet") for item in supported_evidence)

    def _evidence_duplicate(self, left: Dict[str, Any], right: Dict[str, Any]) -> bool:
        left_url = canonicalize_url(str(left.get("canonical_url") or left.get("url") or ""))
        right_url = canonicalize_url(str(right.get("canonical_url") or right.get("url") or ""))
        if left_url and right_url and left_url == right_url:
            return True
        if left.get("content_hash") and right.get("content_hash") and left.get("content_hash") == right.get("content_hash"):
            return True
        return self._jaccard(str(left.get("snippet") or ""), str(right.get("snippet") or "")) >= 0.82

    def _count_possible_contradictions(
        self,
        gemini_claims: Sequence[Dict[str, Any]],
        seer_claims: Sequence[Dict[str, Any]],
    ) -> int:
        count = 0
        for gemini_claim in gemini_claims:
            left = str(gemini_claim.get("text") or "")
            for seer_claim in seer_claims:
                right = str(seer_claim.get("text") or "")
                if self._looks_contradictory(left, right):
                    count += 1
                    break
        return count

    def _looks_contradictory(self, left: str, right: str) -> bool:
        left_tokens = self._tokens(left)
        right_tokens = self._tokens(right)
        if self._set_overlap(left_tokens, right_tokens) < 0.45:
            return False
        left_neg = bool(re.search(r"\b(no|not|unlikely|decrease|decline|reduce|lower)\b", left, re.IGNORECASE))
        right_neg = bool(re.search(r"\b(no|not|unlikely|decrease|decline|reduce|lower)\b", right, re.IGNORECASE))
        left_pos = bool(re.search(r"\b(likely|increase|rise|expand|higher|escalate)\b", left, re.IGNORECASE))
        right_pos = bool(re.search(r"\b(likely|increase|rise|expand|higher|escalate)\b", right, re.IGNORECASE))
        return (left_neg and right_pos) or (right_neg and left_pos)

    def _freshness_notes(
        self,
        gemini_sources: Sequence[Dict[str, Any]],
        seer_sources: Sequence[Dict[str, Any]],
    ) -> List[str]:
        notes: List[str] = []
        if gemini_sources and not any(source.get("published_at") for source in gemini_sources):
            notes.append("Gemini sources do not include publication dates.")
        if seer_sources and not any(source.get("published_at") for source in seer_sources):
            notes.append("TheSeer comparison sources do not include publication dates.")
        return notes or ["No freshness concerns detected from available metadata."]

    def _credibility_notes(
        self,
        gemini_sources: Sequence[Dict[str, Any]],
        seer_sources: Sequence[Dict[str, Any]],
    ) -> List[str]:
        notes: List[str] = []
        weak_types = {"social", "aggregator", None, ""}
        gemini_types = {source.get("source_type") for source in gemini_sources}
        seer_types = {source.get("source_type") for source in seer_sources}
        if gemini_sources and gemini_types.issubset(weak_types):
            notes.append("Gemini source mix is social, aggregator, or unclassified.")
        if seer_sources and seer_types.issubset(weak_types):
            notes.append("TheSeer source mix is social, aggregator, or unclassified.")
        return notes or ["Source credibility requires local governance review before promotion."]

    def _metric_risk(self, metadata: Dict[str, Any], keys: Tuple[str, ...]) -> str:
        for key in keys:
            value = metadata.get(key)
            if isinstance(value, (int, float)):
                if value > 900:
                    return "high"
                if value > 300:
                    return "medium"
                return "low"
        return "unknown"

    def _build_next_steps(self, run: GeminiShadowRun) -> List[str]:
        steps = [
            "Run another shadow comparison with complete local TheSeer outputs.",
            "Review unique Gemini sources against Librarian and source-governance rules.",
        ]
        if run.evidence_comparison.unsupported_gemini_claims_count:
            steps.append("Tighten normalization rules for unsupported Gemini claim candidates.")
        if run.risk_assessment.citation_risk in {"medium", "high"}:
            steps.append("Improve citation metadata capture before any assist-mode trial.")
        if run.agent_overlap.context_interpreter_overlap is not None:
            steps.append("Continue ContextInterpreter shadow comparisons across multiple domains.")
        return steps

    def _record_from_url(self, url: str) -> Dict[str, Any]:
        canonical = canonicalize_url(url)
        return {
            "url": url,
            "canonical_url": canonical,
            "domain": extract_domain(canonical) if canonical else "",
            "title": None,
            "publisher": None,
            "published_at": None,
            "source_type": None,
        }

    def _dedupe_records(self, records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        by_key: Dict[str, Dict[str, Any]] = {}
        for record in records:
            normalized = dict(record)
            if normalized.get("url") and not normalized.get("canonical_url"):
                normalized["canonical_url"] = canonicalize_url(str(normalized["url"]))
            if normalized.get("canonical_url") and not normalized.get("domain"):
                normalized["domain"] = extract_domain(str(normalized["canonical_url"]))
            key = self._record_key(normalized)
            if not key:
                continue
            existing = by_key.get(key)
            if existing:
                for field in ("title", "publisher", "published_at", "source_type", "snippet", "content_hash"):
                    if not existing.get(field) and normalized.get(field):
                        existing[field] = normalized[field]
                continue
            by_key[key] = normalized
        return list(by_key.values())

    def _record_key(self, record: Dict[str, Any]) -> str:
        canonical = canonicalize_url(str(record.get("canonical_url") or record.get("url") or ""))
        if canonical:
            return f"url:{canonical}"
        domain = str(record.get("domain") or "").strip().lower()
        title = self._normalize_label(record.get("title"))
        publisher = self._normalize_label(record.get("publisher"))
        if domain and title:
            return f"domain-title:{domain}:{title}"
        if domain and publisher:
            return f"domain-publisher:{domain}:{publisher}"
        if domain:
            return f"domain:{domain}"
        if title:
            return f"title:{title}"
        return ""

    def _record_label(self, record: Dict[str, Any]) -> str:
        canonical = canonicalize_url(str(record.get("canonical_url") or record.get("url") or ""))
        if canonical:
            return canonical
        if record.get("domain"):
            return str(record["domain"])
        if record.get("title"):
            return str(record["title"])
        return "unknown-source"

    def _sources_overlap(self, left: Dict[str, Any], right: Dict[str, Any]) -> bool:
        left_url = canonicalize_url(str(left.get("canonical_url") or left.get("url") or ""))
        right_url = canonicalize_url(str(right.get("canonical_url") or right.get("url") or ""))
        if left_url and right_url and left_url == right_url:
            return True
        left_domain = str(left.get("domain") or "").lower()
        right_domain = str(right.get("domain") or "").lower()
        if left_domain and right_domain and left_domain == right_domain:
            return True
        left_publisher = self._normalize_label(left.get("publisher"))
        right_publisher = self._normalize_label(right.get("publisher"))
        if left_publisher and right_publisher and left_publisher == right_publisher:
            return True
        return self._jaccard(str(left.get("title") or ""), str(right.get("title") or "")) >= 0.75

    def _extract_texts(self, value: Any, depth: int = 0) -> List[str]:
        if depth > 5:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            texts: List[str] = []
            for item in value:
                texts.extend(self._extract_texts(item, depth + 1))
            return texts
        payload = self._as_dict(value)
        if not payload:
            return []
        texts = [
            str(payload[key])
            for key in ("text", "summary", "snippet", "raw_report", "output", "content")
            if isinstance(payload.get(key), str)
        ]
        for key in ("claims", "claim_items", "evidence", "evidence_items", "sources", AGENT_COLLECTION_KEY, *AGENT_KEYS.keys()):
            if key in payload:
                texts.extend(self._extract_texts(payload[key], depth + 1))
        return texts

    def _sentence_candidates(self, text: str) -> List[str]:
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text or "")
            if len(sentence.strip()) > 20
        ]

    def _tokens(self, text: str) -> Set[str]:
        stop = {"the", "and", "for", "with", "that", "this", "from", "into", "will", "would", "could", "have", "has"}
        return {
            token
            for token in re.findall(r"[a-z0-9]{3,}", (text or "").lower())
            if token not in stop
        }

    def _set_overlap(self, left: Set[str], right: Set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)

    def _jaccard(self, left: str, right: str) -> float:
        return self._set_overlap(self._tokens(left), self._tokens(right))

    def _normalize_label(self, value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip().lower())

    def _pack_has_warning(self, pack: GeminiEvidencePack, code: str) -> bool:
        return any(warning.code == code for warning in pack.normalizer_warnings)

    def _as_dict(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if hasattr(value, "dict"):
            return value.dict()
        return {}

    def _as_list(self, value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _format_list(self, values: Sequence[Any]) -> str:
        return ", ".join(str(value) for value in values) if values else "none"

    def _format_score(self, value: Optional[float]) -> str:
        return "not available" if value is None else f"{value:.4f}"

    def _add_warning(self, warning: str) -> None:
        if warning not in self._warnings:
            self._warnings.append(warning)
