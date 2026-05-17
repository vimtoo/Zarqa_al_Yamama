# Gemini Deep Research Integration Plan for TheSeer

Date: 2026-05-15  
Scope: Planning and documentation only. No source code, environment, package, or workflow behavior changes are included in this document.  
External target: [Gemini Deep Research via Gemini Interactions API](https://ai.google.dev/gemini-api/docs/interactions/deep-research), not the normal `generateContent` endpoint.

## 1. Executive Summary

Gemini Deep Research should enter TheSeer as an optional, reversible research sidecar that gathers source-backed context, citations, evidence candidates, contradictions, uncertainty notes, and tail-risk hypotheses. It must not replace TheSeer's deterministic V2 spine.

The recommended first architecture is:

```text
User Query
  -> Existing Planner
  -> Existing TheSeer agents
  -> Gemini Deep Research shadow/optional node
  -> Evidence Pack Normalizer
  -> EvidenceAnalyst
  -> SchemaValidator
  -> EvidenceDeduper
  -> IndependenceAnalyzer
  -> QuantifierV2
  -> CriticV2
  -> Governor
  -> ReportWriter
```

The core rule is strict:

```text
Gemini may gather, search, summarize, compare, and propose evidence.
Gemini must not replace probability fusion, schema validation, ethical review,
source governance, deduplication, independence scoring, or final safety gates.
```

The first safe targets are `ContextInterpreter` and `BlackSwanGenerator`. Gemini can support them because both are evidence/context generation lanes. The protected components are `QuantifierV2`, `CriticV2`, `Governor`, `SchemaValidator`, `contracts.py`, `Librarian`, `ArbitrationPolicy`, `EvidenceDeduper`, and `IndependenceAnalyzer`.

All listed project files were present. No required file was missing.

## 2. Current TheSeer V2 Pipeline Summary

The local codebase currently has a LangGraph V2 workflow assembled in `backend/app/workflow.py`. In V2 mode, `SEER_USE_V2=1` activates an import-time tripwire requiring `quantifier_v2`, `critic_v2`, `schema_validator`, `evidence_deduper`, and `independence_analyzer`.

Current V2 flow:

```text
START
  -> planner
  -> parallel V2/NSC/DIIS agents
  -> v2_join_node
  -> evidence_analyst
  -> schema_validator_node
  -> evidence_deduper_node
  -> independence_analyzer_node
  -> qualitative_quantifier
  -> quantifier_v2
  -> critic_v2
  -> governor
  -> format_output
  -> report_writer
  -> END
```

Important observed behavior:

| Area | Current Behavior | Gemini Integration Impact |
|---|---|---|
| V2 join barrier | Waits for expected `agent_outputs` keys before downstream gates. | Shadow mode must not add required join keys. Assist mode must add only normalized `AgentOutput` after a deliberate design change. |
| Schema contracts | `AgentOutput` enforces claim-evidence linkage and fail-closed gap semantics. | Gemini output must be normalized into these contracts or quarantined. |
| Deduplication | `EvidenceDeduper` canonicalizes URLs, hashes content, detects wire/syndicated copies, and clusters evidence. | Gemini citations must pass through it. |
| Independence | `IndependenceAnalyzer` scores source diversity, ownership concentration, and clusters. | Gemini cannot self-declare independence. |
| Quantification | `QuantifierV2` performs deterministic signal fusion, log-odds extremization, and Monte Carlo intervals. | Gemini must not generate final probabilities or fused signals. |
| Critique | `CriticV2` checks schema, evidence linkage, allowlists, probability coherence, and claim-evidence mismatch. | Gemini evidence must remain subject to these checks. |
| Governor | `TheGovernor` handles ethical review, PII checks, harmful-content checks, cultural sensitivity, attribution, and audit logs. | Gemini must not bypass it. |
| Reporting | `ReportWriter` writes final reports and renders Intelligence Gaps in Appendix C. | Shadow comparisons should be separate from production reports. |

## 3. Protected Components

These components must remain authoritative and must not be bypassed or overwritten by Gemini Deep Research.

| Component | File | Protection Rule |
|---|---|---|
| `contracts.py` | `backend/app/graph/contracts.py` | Source of truth for Pydantic evidence, claim, signal, forecast, and fail-closed contracts. Do not loosen for Gemini. |
| `SchemaValidator` | `backend/app/agents/schema_validator.py` | Must reject malformed Gemini-derived outputs before any downstream use. |
| `EvidenceDeduper` | `backend/app/retrieval/evidence_deduper.py` | Must canonicalize, hash, cluster, and deduplicate Gemini citations. |
| `IndependenceAnalyzer` | `backend/app/retrieval/independence_analyzer.py` | Must compute independence; Gemini cannot self-certify independent confirmation. |
| `QuantifierV2` | `backend/app/agents/quantifier_v2.py` | Must remain the only deterministic probability fusion engine. |
| `CriticV2` | `backend/app/agents/critic_v2.py` | Must remain the deterministic final validation loop. |
| `Governor` | `backend/app/agents/governor.py` | Must remain the ethical, safety, PII, cultural sensitivity, and attribution authority. |
| `Librarian` | `backend/app/retrieval/librarian.py` | Must preserve source allowlist, strict mode, rate limit, cache, and audit governance. |
| `ArbitrationPolicy` | `backend/app/llm/arbitration.py` | Must preserve Gemini advisory-only provider authority rules. |

## 4. Proposed Gemini Deep Research Integration Architecture

### 4.1 External API Target

Gemini Deep Research should be integrated through the Gemini Interactions API. Google's Deep Research documentation describes it as a preview agent that performs web research, creates a research plan, gathers sources, and produces a cited report. The examples use long-running background interactions and polling or streaming through Interactions API methods. The normal TheSeer `GeminiClient.complete()` currently calls `models/{model}:generateContent`; it is not the correct integration surface for Deep Research.

Required adapter boundary:

```text
GeminiDeepResearchClient
  -> create background interaction
  -> poll or stream until completed, failed, or timed out
  -> persist raw interaction metadata and raw report
  -> pass raw report to local normalizer
```

The adapter must not directly write `EvidenceItem`, `ClaimItem`, `Signal`, or final forecast objects into production state.

### 4.2 Recommended Architecture: Post-Planner Optional/Shadow Node

Recommended first design:

```text
User Query
  -> Existing Planner
  -> Existing TheSeer V2 agents
  -> Gemini Deep Research sidecar
       -> raw interaction metadata
       -> raw cited report
       -> GeminiEvidencePack JSON
       -> shadow comparison report
  -> Existing V2 gates unchanged
```

In shadow mode:

```text
Gemini output is stored outside production forecast state.
Gemini output does not enter `agent_outputs`.
Gemini output does not affect `v2_join_node`.
Gemini output does not affect `QuantifierV2`, `CriticV2`, `Governor`, or `ReportWriter`.
```

In later assist mode:

```text
Gemini raw report
  -> Evidence Pack Normalizer
  -> contract-valid AgentOutput(agent_id="gemini_deep_research")
  -> SchemaValidator
  -> EvidenceDeduper
  -> IndependenceAnalyzer
  -> QuantifierV2 only through existing weights and gates
```

This is safer than replacing an existing node immediately because it allows source-quality, latency, cost, hallucination, schema, and overlap comparisons without changing forecast behavior.

### 4.3 Alternative Architecture: Pre-Research Before Planner

Alternative:

```text
User Query
  -> Gemini Deep Research pre-research adapter
  -> Existing Planner
  -> Existing TheSeer workflow
```

Pros:

| Advantage | Detail |
|---|---|
| Better query expansion | Gemini may produce clearer research framing before TheSeer's planner. |
| Better entity discovery | It may identify actors, locations, institutions, and source clusters early. |
| Useful for vague user prompts | It can turn broad questions into specific research dimensions. |

Cons:

| Risk | Detail |
|---|---|
| Planner contamination | Gemini framing could bias TheSeer's routing before local agents run. |
| Higher latency | Deep Research is long-running and may delay every forecast. |
| Governance risk | Pre-planner output may shape source selection before `Librarian` and `ArbitrationPolicy` are applied. |
| Harder comparison | It becomes difficult to distinguish TheSeer value from Gemini-seeded context. |
| More dangerous failure mode | A failed Gemini call could block or degrade the entry path unless carefully isolated. |

Recommendation: do not use pre-research by default. Reserve it for a later `assist` experiment after shadow evaluation proves that Gemini improves evidence quality without increasing hallucination or source-governance risk.

### 4.4 Where Gemini Should Enter

Gemini should enter after the existing Planner has interpreted the user query and after TheSeer's normal agents have started or completed. The safest initial implementation is a sidecar runner that receives:

| Input | Source |
|---|---|
| Original user query | `state["scenario"]` |
| Forecast horizon | `state["forecast_horizon_days"]` and planner output |
| Domain routing | `active_domains`, `primary_domain`, planner metadata |
| Existing agent outputs for comparison only | `agent_outputs`, `walled_garden_results`, `think_tank_sources`, `context_data_sources` |
| Security mode | `rag_mode`, `session_id`, but no user documents unless explicitly configured |

### 4.5 Existing Outputs Gemini Should Supplement

| Existing Output | Gemini Supplement |
|---|---|
| `context_sentiment`, `context_themes`, `context_key_actors` | Current background, source summaries, actors, narrative momentum, and missing perspectives. |
| `agent_outputs["context_interpreter"]` | Later, normalized evidence-backed context claims. |
| `agent_outputs["black_swan_generator"]` | Later, evidence-backed tail-risk scenarios separated from speculative hypotheses. |
| `think_tank_insights`, `think_tank_sources` | Shadow comparison and later curated summaries, but only under allowlist governance. |
| `walled_garden_results` | Shadow comparison and candidate source suggestions, not direct replacement of trusted-source logic. |
| `evidence_summary`, `evidence_unknowns`, `evidence_contradictions` | Candidate uncertainty notes and contradictions after normalizer validation. |

### 4.6 Agents Gemini May Replace Later

Only after shadow runs show sustained value and low risk:

| Later Replacement Candidate | Condition |
|---|---|
| `ContextInterpreter` | Gemini consistently finds fresher, more diverse, source-backed context and normalized claims pass SchemaValidator. |
| `BlackSwanGenerator` | Gemini produces better evidence-backed tail risks while separating speculative scenarios from cited facts. |

Do not recommend immediate replacement. The first replacement mode should retain fallback to the existing agent on timeout, malformed output, missing sources, or failed schema validation.

### 4.7 Agents That Must Remain Untouched

The following must not be replaced by Gemini Deep Research:

```text
QuantifierV2
CriticV2
Governor
SchemaValidator
contracts.py
Librarian
ArbitrationPolicy
EvidenceDeduper
IndependenceAnalyzer
```

### 4.8 Storage Design

Store Gemini output separately from production forecast state:

| Artifact | Path |
|---|---|
| Raw/normalized evidence packs | `data/research/evidence_packs/{run_id}.json` |
| Raw Gemini reports | `data/research/evidence_packs/{run_id}.raw.md` or embedded `raw_report` in JSON |
| Shadow run metadata | `data/research/gemini_shadow_runs/{run_id}.json` |
| Human-readable comparison reports | `data/research/gemini_shadow_runs/{run_id}.md` |
| Optional aggregate doc | `docs/gemini_shadow_comparison.md` |

Shadow artifacts must not be read by `QuantifierV2`, `CriticV2`, `Governor`, or `ReportWriter`.

### 4.9 Downstream Flow Rules

| Downstream Component | Gemini Flow Rule |
|---|---|
| `EvidenceAnalyst` | May receive normalized candidate evidence in assist mode. Must not trust raw Gemini prose as evidence. |
| `SchemaValidator` | Must validate every Gemini-derived `AgentOutput`. Malformed data is rejected or quarantined. |
| `EvidenceDeduper` | Must canonicalize URLs, compute hashes, detect duplicate/syndicated citations, and assign clusters. |
| `IndependenceAnalyzer` | Must compute source independence. Gemini source count alone is not independent confirmation. |
| `QuantifierV2` | Receives only existing contract-valid signals from authorized agents. Gemini must not inject final probabilities. |
| `CriticV2` | Must validate Gemini-derived evidence like any other agent output. |
| `Governor` | Must review final output regardless of Gemini involvement. |
| `ReportWriter` | Production report must not include shadow Gemini output. In assist mode, it may cite validated evidence only after V2 gates. |

### 4.10 New Modules to Create Later

| Module | Responsibility |
|---|---|
| `backend/app/integrations/gemini_deep_research/client.py` | Interactions API client for create, poll, stream, timeout, and error handling. |
| `backend/app/integrations/gemini_deep_research/models.py` | Local Pydantic models for raw interaction metadata and `GeminiEvidencePack`. |
| `backend/app/integrations/gemini_deep_research/normalizer.py` | Converts Gemini reports into `EvidenceItem`, `ClaimItem`, `IntelligenceGap`, and `AgentOutput`. |
| `backend/app/integrations/gemini_deep_research/prompts.py` | Research prompt templates with strict security and no-probability instructions. |
| `backend/app/integrations/gemini_deep_research/storage.py` | Writes evidence packs and shadow run artifacts. |
| `backend/app/integrations/gemini_deep_research/shadow_compare.py` | Compares Gemini output against TheSeer agents. |
| `backend/app/integrations/gemini_deep_research/workflow_nodes.py` | Optional LangGraph node wrappers for shadow/assist/replace modes. |
| `backend/app/integrations/gemini_deep_research/security.py` | Query redaction, secret scanning, and allowed-context checks. |

### 4.11 New Config Flags to Create Later

See Section 7 for full flag definitions. These flags should be added only during implementation phases, not during Phase 0 documentation.

### 4.12 Tests Needed Later

| Test Area | Purpose |
|---|---|
| Client timeout and polling | Deep Research cannot hang the workflow. |
| Normalizer contract tests | Every Gemini pack either becomes valid `AgentOutput` or `IntelligenceGap`. |
| Schema fail-closed tests | Malformed Gemini claims fail before fusion. |
| No-probability tests | Gemini event probabilities are stripped or ignored. |
| Shadow non-interference tests | Shadow mode does not change forecast outputs byte-for-byte. |
| Replacement fallback tests | `replace_context` and `replace_black_swan` fall back to existing agents on failure. |
| Source governance tests | Gemini citations respect `Librarian` and allowlist rules. |
| Dedup/independence tests | Gemini duplicate sources are clustered and not over-weighted. |

## 5. Evidence Contract Mapping

### 5.1 Relevant TheSeer Contract Concepts

From `backend/app/graph/contracts.py`:

| Contract | Meaning |
|---|---|
| `EvidenceItem` | Source-backed evidence with URL, canonical URL, domain, timestamps, content hash, snippet, source type, reliability tier, and syndication metadata. |
| `ClaimItem` | Atomic, falsifiable claim with at least one valid `evidence_id`, confidence, time horizon, independence score, and optional resolution date. |
| `AgentOutput` | Structured agent output containing status, provenance, gaps, claims, evidence, signals, assumptions, uncertainty notes, confidence, and summary. |
| `IntelligenceGap` | Fail-closed representation of missing or unverifiable evidence. |
| `OutputStatus` | `SUPPORTED`, `INTELLIGENCE_GAP`, `RECUSED`, or `SYSTEM_FAULT`. |
| `ProvenanceKind` | `LIVE_OSINT`, `BYOD`, `CURATED_CACHE`, `SIMULATION`, `INTERNAL_ANALYSIS`, or `NONE`. |
| `SourceType` | `primary`, `syndicated`, `primary_data`, `primary_reporting`, `analysis`, `aggregator`, or `social`. |
| `Signal` | Probabilistic Monte Carlo triad used by fusion. Gemini must not emit these in first phases. |
| `TimeHorizon` | `SHORT_TERM`, `MEDIUM_TERM`, or `LONG_TERM`. |
| `ConfidenceLevel` | Final output confidence level. Gemini must not set this directly. |

### 5.2 Gemini to TheSeer Mapping

| Gemini Deep Research Output | TheSeer Object | Mapping Rule |
|---|---|---|
| Interaction ID | `GeminiEvidencePack.interaction_id` | Preserve exactly for traceability. |
| Research plan | `GeminiEvidencePack.research_plan` | Store as metadata. Do not convert to evidence. |
| Source/citation URL | `EvidenceItem.url` and `canonical_url` | Normalize URL; strip tracking params later through `EvidenceDeduper`. |
| Source title/publisher | `EvidenceItem.publisher` and source metadata | Use only if Gemini provides it or local fetch confirms it. |
| Publication date | `EvidenceItem.published_at` | Use parsed date only if provided or locally verified. Otherwise `null`. |
| Retrieved timestamp | `EvidenceItem.retrieved_at` | Local timestamp when adapter processed the Gemini report. |
| Cited source excerpt | `EvidenceItem.snippet` | Must be traceable to a cited source. Max 2000 chars. |
| Source body/hash | `EvidenceItem.content_hash` | SHA-256 of normalized source snippet or fetched content. |
| Citation domain | `EvidenceItem.domain` | Extract locally from URL. |
| Source category | `EvidenceItem.source_type` | Map by domain/source kind; do not accept Gemini category blindly. |
| Narrative conclusion | `ClaimItem` | Split into atomic falsifiable claims and link to evidence IDs. |
| Broad synthesis | `AgentOutput.summary` | Keep as summary only after claims are separately extracted. |
| Uncertainty statements | `AgentOutput.uncertainty_notes` | Preserve as notes. |
| Missing source categories | `IntelligenceGap` | Use when sources are missing, unverified, stale, or insufficient. |
| Gemini confidence wording | `ClaimItem.confidence_justification` or uncertainty notes | Do not convert to final probability. |
| Gemini event probabilities | Quarantined note | Do not create `Signal` or `FusionResult` from them. |

### 5.3 Provenance and Source Type Rules

| Condition | ProvenanceKind | SourceType |
|---|---|---|
| Gemini cites public web source and URL is present | `LIVE_OSINT` | Based on domain: `primary_reporting`, `analysis`, `primary_data`, `aggregator`, or `social`. |
| Gemini cites source previously cached by TheSeer | `CURATED_CACHE` | Preserve original source type from cached item. |
| Gemini makes an analytical synthesis over cited evidence | `INTERNAL_ANALYSIS` for summary only | Do not convert synthesis-only prose into standalone evidence. |
| Gemini uses uploaded/private documents | Not allowed by default | Only allow later under explicit BYOD policy; otherwise do not send. |
| Gemini returns no verified citations | `NONE` | Produce `OutputStatus.INTELLIGENCE_GAP`. |

### 5.4 Mandatory Normalization Rules

1. Gemini must not invent `EvidenceItem.id` values without traceable provenance. IDs should be deterministic from `interaction_id`, canonical URL, snippet hash, and source index.
2. Every `ClaimItem` must reference at least one valid `EvidenceItem.id`.
3. If Gemini provides no verified sources, the adapter must produce an `IntelligenceGap` instead of synthetic evidence.
4. If Gemini provides citations but no publication dates, set `published_at` to `null`; do not fabricate dates.
5. If Gemini produces broad narrative, the normalizer must split it into atomic falsifiable claims.
6. If Gemini output is not contract-compliant, `SchemaValidator` must reject it.
7. Gemini output may be treated as `LIVE_OSINT`, `CURATED_CACHE`, or `INTERNAL_ANALYSIS` only when justified by source metadata and local context.
8. Gemini must not generate final probability values for `QuantifierV2`.
9. Gemini must not emit `Signal` objects in shadow mode or early assist mode.
10. Gemini citations must preserve contradictions. Conflicting claims should be represented as separate claims or uncertainty notes, not averaged away.

### 5.5 Proposed `GeminiEvidencePack` JSON Shape

```json
{
  "provider": "gemini_deep_research",
  "model": "deep-research-preview-04-2026",
  "interaction_id": "...",
  "run_id": "...",
  "original_question": "...",
  "improved_research_prompt": "...",
  "research_plan": [],
  "sources": [
    {
      "source_id": "gem-src-001",
      "title": "...",
      "url": "...",
      "canonical_url": "...",
      "domain": "...",
      "publisher": "...",
      "published_at": null,
      "retrieved_at": "...",
      "source_type_hint": "analysis",
      "reliability_notes": "...",
      "citation_markers": []
    }
  ],
  "evidence_items": [
    {
      "id": "gemdr-<interaction>-<hash>",
      "source_id": "gem-src-001",
      "url": "...",
      "canonical_url": "...",
      "domain": "...",
      "publisher": "...",
      "published_at": null,
      "retrieved_at": "...",
      "content_hash": "...",
      "snippet": "...",
      "source_type": "analysis",
      "reliability_tier": 3,
      "provenance": "LIVE_OSINT"
    }
  ],
  "claim_items": [
    {
      "id": "gem-claim-001",
      "text": "...",
      "evidence_ids": ["gemdr-<interaction>-<hash>"],
      "confidence": 0.55,
      "confidence_justification": "Supported by cited source; not a forecast probability.",
      "time_horizon": "MEDIUM_TERM",
      "falsifiable": true,
      "resolution_date": null
    }
  ],
  "uncertainty_notes": [],
  "intelligence_gaps": [
    {
      "reason": "...",
      "missing_inputs": [],
      "attempted_sources": [],
      "retryable": true,
      "severity": "MEDIUM"
    }
  ],
  "raw_report": "...",
  "raw_interaction_metadata": {},
  "normalizer_warnings": [],
  "created_at": "..."
}
```

### 5.6 Adapter Output Contract

For assist mode, the normalized output should become:

```text
AgentOutput(
  agent_id="gemini_deep_research",
  status=SUPPORTED or INTELLIGENCE_GAP or SYSTEM_FAULT,
  provenance=LIVE_OSINT or CURATED_CACHE or INTERNAL_ANALYSIS or NONE,
  gaps=[...],
  claims=[...],
  evidence=[...],
  signals=[],
  assumptions=[...],
  uncertainty_notes=[...],
  confidence=<evidence confidence only>,
  confidence_justification="Derived from cited Gemini Deep Research sources; not a forecast probability.",
  summary=<short synthesis>
)
```

## 6. Safe Replacement Target Analysis

| Component | Current Role | Gemini Role | Replacement Level | Risk | Recommendation |
|---|---|---|---|---|---|
| `ContextInterpreter` | Fetches NewsAPI/GNews/GDELT, sentiment, themes, actors, and typed context evidence. | Broad current-events research, source gathering, source comparison, background synthesis. | Safe first-stage target. High replacement potential later. | Medium | Start with shadow comparison, then assist. Replacement only after normalized claims pass V2 gates and output quality beats current context. |
| `BlackSwanGenerator` | Generates low-probability, high-impact tail-risk scenarios from local context and LLM output. | Evidence-backed tail-risk discovery, scenario mechanisms, blind spots. | Safe first-stage target. High replacement potential later. | Medium | Strong candidate after ContextInterpreter. Must separate cited risks from speculative hypotheses. |
| `ThinkTankAnalyst` | Recursive think-tank RSS/live retrieval over RAND, IISS, SIPRI, Carnegie, Brookings, Chatham House, AGSIW, etc. | Retrieve and summarize think tank content. | Partial support only. | Medium-high | Preserve sovereign source lists, `Librarian`, grounding checks, and fail-closed gap behavior. |
| `WalledGardenAnalyst` | Trusted-source OSINT recursive search with allowlisted domains, BYOD strict/hybrid modes, and V3 gap output. | Supplement search queries and suggest sources. | Partial support only. | High | Do not bypass allowlists, strict BYOD boundary, or trusted-domain extraction. |
| `EvidenceAnalyst` | Converts trusted snippets and skipped-node conditions into evidence summaries, claims, contradictions, and gaps. | Help synthesize and compare evidence. | Partial support only. | High | Gemini can propose synthesis; local contract enforcement stays in TheSeer. |
| `PoliticalStudiesAnalyst` | Aggregates news, GDELT, ACLED, and legislation into narrative political briefs and conflict metrics. | Background narrative and source discovery. | Partial support only; unknown for event counts. | Medium-high | Do not replace ACLED counting, legislation retrieval, or conflict metric contract logic. |
| `QuantifierV2` | Deterministic probability fusion with calibrated weights, independence penalties, log-odds extremization, and Monte Carlo intervals. | None. | Protected non-replacement target. | Critical | Never replace. Gemini probabilities are forbidden. |
| `CriticV2` | Deterministic validation of schema, evidence links, allowlists, probability coherence, and claim-evidence mismatch. | None, except possible sandboxed human-review note generation. | Protected non-replacement target. | Critical | Never replace final validation loop. |
| `Governor` | Ethical oversight, PII checks, harmful content checks, cultural sensitivity, bias triangulation, audit, citation chain. | None. | Protected non-replacement target. | Critical | Never replace. Gemini cannot become ethical authority. |
| `SchemaValidator` | Validates all `AgentOutput` objects and fail-closed gap semantics before fusion. | None. | Protected non-replacement target. | Critical | Never replace or loosen. |
| `Librarian` | Source allowlist, strict mode, rate limit, cache, audit, `EvidenceItem` creation. | None. | Protected; no replacement without human review. | Critical | Preserve authority. Gemini source suggestions must be checked against it. |
| `ArbitrationPolicy` | Enforces Gemini advisory-only doctrine and forbidden decision lanes. | None. | Protected non-replacement target. | Critical | Extend carefully if needed, but do not bypass. |
| `EvidenceDeduper` | URL canonicalization, hash computation, wire/syndication detection, clustering. | None. | Protected non-replacement target. | High | Gemini citations must flow through it. |
| `IndependenceAnalyzer` | Scores cluster independence, source-type diversity, ownership concentration, and claim independence. | None. | Protected non-replacement target. | High | Gemini source counts must not substitute for this score. |
| `ReportWriter` | Final Markdown/text/PDF report generation, evidence table, source appendix, intelligence gaps. | Separate shadow comparison report writer only. | Unknown/human review for production replacement. | Medium-high | Do not replace production report writer in this plan. Use separate comparison reports for Gemini shadow output. |

Classification summary:

| Class | Components |
|---|---|
| A. Safe first-stage targets | `ContextInterpreter`, `BlackSwanGenerator` |
| B. Partial support targets | `ThinkTankAnalyst`, `WalledGardenAnalyst`, `EvidenceAnalyst`, `PoliticalStudiesAnalyst`, `ReportWriter` for comparison reporting only |
| C. Protected non-replacement targets | `QuantifierV2`, `CriticV2`, `Governor`, `SchemaValidator`, `contracts.py`, `Librarian`, `ArbitrationPolicy`, `EvidenceDeduper`, `IndependenceAnalyzer` |
| D. Unknown / needs human review | Production `ReportWriter` replacement, any BYOD/private-document research mode, any source-governance changes |

## 7. Feature Flag Design

Default must be disabled and safe:

```bash
SEER_USE_GEMINI_DEEP_RESEARCH=0
SEER_GEMINI_MODE=shadow
```

Proposed flags:

| Variable | Default | Meaning |
|---|---:|---|
| `SEER_USE_GEMINI_DEEP_RESEARCH` | `0` | Master kill switch. `0` means no Deep Research calls, regardless of mode. |
| `SEER_GEMINI_MODE` | `shadow` | Operating mode: `off`, `shadow`, `assist`, `replace_context`, `replace_black_swan`, or `replace_selected`. |
| `SEER_GEMINI_MODEL` | `deep-research-preview-04-2026` | Default Deep Research model. |
| `SEER_GEMINI_MAX_MODEL` | `deep-research-max-preview-04-2026` | Higher-capability model for explicit manual tests only. |
| `SEER_GEMINI_TIMEOUT_SECONDS` | `900` | Max wait for a Deep Research interaction. Timeout saves metadata and continues. |
| `SEER_GEMINI_ENABLE_COLLABORATIVE_PLANNING` | `0` | Allows multi-turn planning with Gemini only when explicitly enabled. Off by default to avoid planner contamination. |
| `SEER_GEMINI_ENABLE_VISUALIZATION` | `0` | Allows visualization features if exposed by the Interactions API. Off by default. |
| `SEER_GEMINI_ALLOWED_TARGETS` | `context_interpreter,black_swan_generator` | Comma-separated replacement targets allowed in replacement modes. |
| `SEER_GEMINI_WRITE_EVIDENCE_PACKS` | `1` | Persist raw and normalized evidence packs for audit and comparison. |
| `SEER_GEMINI_EVIDENCE_PACK_DIR` | `data/research/evidence_packs` | Directory for normalized evidence packs. |
| `SEER_GEMINI_FAIL_OPEN` | `0` | Whether malformed or failed Gemini output may be ignored in assist/replacement modes. Default `0` means Gemini output is quarantined and existing agents remain authoritative. |

Mode definitions:

| Mode | Behavior |
|---|---|
| `off` | No Gemini calls, no evidence packs, no comparison reports. Equivalent to master switch disabled. |
| `shadow` | Gemini runs outside production forecast logic and writes separate artifacts only. No forecast output changes. |
| `assist` | Gemini normalized `AgentOutput` may be added as supplementary evidence after normalizer and before V2 gates. Existing agents still run. |
| `replace_context` | Gemini may replace `ContextInterpreter` output only when allowed and contract-compliant. Existing `ContextInterpreter` is fallback. |
| `replace_black_swan` | Gemini may replace `BlackSwanGenerator` output only when allowed and contract-compliant. Existing generator is fallback. |
| `replace_selected` | Only explicitly listed `SEER_GEMINI_ALLOWED_TARGETS` may be replaced. All protected components remain untouched. |

Safety requirements:

1. Default is safe and disabled.
2. Gemini must be disabled by default.
3. Gemini must be testable without changing forecast outputs.
4. No core pipeline behavior should change until manually enabled.
5. If Gemini fails, TheSeer continues using existing agents.
6. Gemini output must be stored separately for comparison in shadow mode.
7. Gemini must never be a required `v2_join_node` dependency in shadow mode.

## 8. Shadow Mode Design

Shadow mode is the required first implementation mode.

### 8.1 Shadow Mode Rules

```text
Existing TheSeer workflow runs normally.
Gemini Deep Research runs in parallel or after the primary research stage.
Gemini output is saved separately.
Gemini output does not affect final forecasts.
Gemini output is compared against existing agents.
No production forecast logic is changed.
```

Hard rule:

```text
Shadow mode must never influence QuantifierV2, CriticV2, Governor, or ReportWriter output.
```

### 8.2 Safe Shadow Execution Pattern

Recommended implementation pattern:

```text
1. Planner runs normally.
2. Existing TheSeer V2 agents run normally.
3. Shadow runner starts Gemini with a sanitized research prompt.
4. TheSeer forecast completes normally.
5. Shadow runner writes GeminiEvidencePack.
6. Shadow comparator compares Gemini output against TheSeer evidence.
7. Comparator writes JSON and Markdown reports under data/research/gemini_shadow_runs/.
```

The shadow runner should not write to:

```text
state["agent_outputs"]
state["deduped_evidence"]
state["evidence_clusters"]
state["independence_summary"]
state["fusion_result_v2"]
state["horizon_forecasts"]
state["executive_summary"]
state["report_path"]
```

### 8.3 Shadow Comparison Outputs

Each shadow run should produce either:

```text
docs/gemini_shadow_comparison.md
```

or per-run outputs:

```text
data/research/gemini_shadow_runs/{run_id}.json
data/research/gemini_shadow_runs/{run_id}.md
```

Per-run files are preferred because Deep Research is long-running and comparisons should be auditable by run ID.

### 8.4 Comparison Metrics

The comparison must evaluate:

| Metric | Description |
|---|---|
| Source quality | Reliability tier, primary vs secondary, trusted domain status. |
| Source freshness | Publication dates and retrieved timestamps. Unknown dates must remain unknown. |
| Source diversity | Distinct domains, source types, ownership groups, and clusters. |
| Source credibility | Allowlist status, publisher reputation, source type. |
| Useful evidence count | Gemini claims that could become valid `EvidenceItem` plus `ClaimItem`. |
| Duplicate findings | Overlap with existing TheSeer evidence or syndicated repeats. |
| Unsupported claims | Claims without citations or with non-resolving citations. |
| Contradictions | Claims that conflict with TheSeer trusted sources. |
| Missing source types | Official data, primary reporting, think tank analysis, local/regional sources, etc. |
| Latency | Interaction start to final report. |
| Token cost | If available from API metadata. |
| API cost | If available from billing metadata or configured estimator. |
| Context overlap | Overlap with `ContextInterpreter`. |
| Black swan overlap | Overlap with `BlackSwanGenerator`. |
| Think tank overlap | Overlap with `ThinkTankAnalyst`. |
| Walled garden overlap | Overlap with `WalledGardenAnalyst`. |
| Gemini unique value | Useful evidence Gemini found that TheSeer missed. |
| TheSeer unique value | Useful evidence TheSeer found that Gemini missed. |

### 8.5 Proposed `GeminiShadowRun` JSON Structure

```json
{
  "run_id": "...",
  "timestamp": "...",
  "query": "...",
  "seer_agents_used": [],
  "gemini_interaction_id": "...",
  "gemini_model": "deep-research-preview-04-2026",
  "gemini_mode": "shadow",
  "seer_workflow_version": "v2",
  "evidence_pack_path": "data/research/evidence_packs/....json",
  "comparison": {
    "source_overlap": 0.0,
    "unique_gemini_sources": [],
    "unique_seer_sources": [],
    "useful_new_evidence_count": 0,
    "unsupported_claims_count": 0,
    "duplicate_findings_count": 0,
    "contradictions_count": 0,
    "latency_seconds": 0,
    "token_cost": null,
    "api_cost": null,
    "overlap_by_agent": {
      "context_interpreter": 0.0,
      "black_swan_generator": 0.0,
      "think_tank_analyst": 0.0,
      "walled_garden_analyst": 0.0
    },
    "recommendation": "Gemini useful as shadow only"
  }
}
```

## 9. Comparison Report Design

Every Gemini shadow run should create a human-readable comparison report suitable for upload to ChatGPT/Lulu for further review.

Template:

```markdown
# Gemini Deep Research Shadow Comparison

## 1. Run Metadata
- run_id:
- timestamp:
- user query:
- Gemini model:
- Gemini mode:
- interaction_id:
- TheSeer workflow version:
- agents executed:

## 2. Source Comparison
- sources found by TheSeer:
- sources found by Gemini:
- overlapping sources:
- unique Gemini sources:
- unique TheSeer sources:
- source freshness:
- source credibility:

## 3. Evidence Comparison
- EvidenceItems produced by TheSeer:
- EvidenceItems proposed by Gemini:
- accepted Gemini evidence:
- rejected Gemini evidence:
- duplicate evidence:
- unsupported Gemini claims:
- evidence gaps:

## 4. Agent Replacement Assessment
- ContextInterpreter comparison:
- BlackSwanGenerator comparison:
- ThinkTankAnalyst comparison:
- WalledGardenAnalyst comparison:
- EvidenceAnalyst comparison:

## 5. Risk Assessment
- hallucination risk:
- citation risk:
- source-governance risk:
- schema-compliance risk:
- latency risk:
- cost risk:
- dependency risk:

## 6. Recommendation
One of:
- Gemini not useful
- Gemini useful as shadow only
- Gemini useful as assistant
- Gemini ready to replace ContextInterpreter for this domain
- Gemini ready to replace BlackSwanGenerator for this domain
- Gemini requires human review

## 7. Next Steps
- what to test next:
- which agent to compare next:
- which prompt to improve:
- whether to run another shadow test:
```

Recommendation labels must be conservative. A single good run is not enough to mark Gemini ready to replace anything.

## 10. Failure Handling

| Failure | Required Behavior |
|---|---|
| Gemini API fails | TheSeer continues normally. Save failure metadata if shadow artifacts are enabled. |
| Gemini interaction times out | Save partial metadata, mark `SYSTEM_FAULT` in the pack, and continue. |
| Gemini returns malformed data | Quarantine raw output. If in assist/replacement mode, `SchemaValidator` must reject it. |
| Gemini returns no sources | Produce `IntelligenceGap`; do not synthesize evidence. |
| Gemini cites weak sources | Mark lower reliability tier and source-governance warnings. |
| Gemini cites unknown publication dates | Set `published_at` to `null`; do not fabricate. |
| Gemini output conflicts with trusted TheSeer sources | Preserve contradiction for comparison or later Critic/Governor review. Do not suppress it. |
| Gemini produces unsupported claims | Reject or quarantine them. They must not become `ClaimItem`. |
| Gemini generates event probabilities | Strip from evidence path or store only as raw note. Do not create `Signal`. |
| Gemini response is partially valid | Accept only locally normalized, source-backed, contract-compliant parts; quarantine the rest. |
| Gemini suggests disallowed/private source use | Block, log governance warning, and create gap if required. |

Default mode rule:

```text
Gemini must never block the existing workflow in default mode.
```

## 11. Security and Governance Notes

Mandatory security rules:

1. Do not send secrets, `.env` files, private keys, credentials, API keys, tokens, database URLs, or local secret documents to Gemini.
2. Do not send sensitive local documents unless a future explicit BYOD Gemini mode is designed and manually enabled.
3. Do not send `session_id` document contents by default. Shadow mode should use only the user query and non-sensitive planner context.
4. Respect source governance and allowlists.
5. Preserve `Librarian` authority for allowlist, strict mode, cache, rate limit, and audit.
6. Preserve `ArbitrationPolicy` authority for Gemini advisory-only lanes.
7. Preserve `Governor` authority for ethical review and final safety status.
8. Preserve fail-closed contracts in `contracts.py`.
9. Store Gemini outputs with provenance, interaction ID, model, prompt, timestamps, and normalization warnings.
10. Mark all Gemini-generated evidence as externally generated until validated locally.

Recommended redaction before Gemini calls:

| Input Category | Action |
|---|---|
| `.env`, credentials, tokens | Never send. |
| User documents | Never send in Phase 1-8. Human-review design required. |
| Internal system prompts | Do not send. |
| Full ForecastState | Do not send. Build a minimal prompt. |
| Agent outputs | In shadow comparison, use only non-sensitive summaries and public citation metadata. |
| Local file paths | Strip unless explicitly relevant and non-sensitive. |

## 12. Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Hallucinated citations | High | Require URL/citation extraction, local normalization, and SchemaValidator rejection if no valid evidence exists. |
| Source-governance bypass | Critical | Keep `Librarian` and allowlist checks authoritative. Gemini can suggest sources, not approve them. |
| Probability contamination | Critical | Strip Gemini probabilities; do not allow Gemini to emit `Signal` or `FusionResult`. |
| Planner bias | Medium-high | Do not run Gemini before Planner by default. Use shadow post-planner architecture first. |
| Long-running latency | Medium | Background interactions, timeouts, no required join dependency in shadow mode. |
| Cost growth | Medium | Persist cost metadata, cap shadow runs, require manual enablement for max model. |
| Schema drift | High | Normalizer tests plus fail-closed SchemaValidator. |
| Duplicate source inflation | High | Force all Gemini citations through `EvidenceDeduper` and `IndependenceAnalyzer`. |
| Weak-source over-weighting | High | Reliability tiers and Critic/Governor warnings. |
| Private data leakage | Critical | Minimal prompt, redaction, no BYOD Deep Research by default. |
| Dependency on preview API | Medium | Feature flags, graceful fallback, no default production dependency. |

## 13. Recommended Implementation Phases

| Phase | Scope | Exit Criteria |
|---|---|---|
| Phase 0 | Documentation and design only. | This plan exists. No code or behavior changed. |
| Phase 1 | Create Gemini client wrapper, no workflow integration. | Can create/poll a background Deep Research interaction in isolated smoke tests. |
| Phase 2 | Create EvidencePack normalizer. | Raw reports become valid `GeminiEvidencePack` or fail-closed `IntelligenceGap`. |
| Phase 3 | Run Gemini in shadow mode. | Forecast outputs remain unchanged; separate artifacts are written. |
| Phase 4 | Compare Gemini against `ContextInterpreter`. | Multiple shadow runs show source freshness, quality, and useful unique evidence. |
| Phase 5 | Compare Gemini against `BlackSwanGenerator`. | Tail-risk outputs are evidence-backed and speculation is clearly separated. |
| Phase 6 | Enable assist mode only if shadow mode shows value. | Gemini supplementary `AgentOutput` passes V2 gates without forecast regressions. |
| Phase 7 | Consider selective replacement of `ContextInterpreter`. | Replacement mode has fallback, test coverage, and better evidence metrics across domains. |
| Phase 8 | Consider selective replacement of `BlackSwanGenerator`. | Tail-risk evidence quality improves without speculative contamination. |
| Phase 9 | Consider partial support for `ThinkTankAnalyst` or `WalledGardenAnalyst`. | Human review confirms source governance and allowlist behavior remain intact. |

Never replace:

```text
QuantifierV2
CriticV2
Governor
SchemaValidator
contracts.py
Librarian
ArbitrationPolicy
EvidenceDeduper
IndependenceAnalyzer
```

## 14. Files That Would Need to Be Created Later

| File | Purpose |
|---|---|
| `backend/app/integrations/gemini_deep_research/__init__.py` | Integration package marker. |
| `backend/app/integrations/gemini_deep_research/client.py` | Interactions API wrapper. |
| `backend/app/integrations/gemini_deep_research/models.py` | Pydantic models for raw and normalized packs. |
| `backend/app/integrations/gemini_deep_research/normalizer.py` | Contract mapping and fail-closed conversion. |
| `backend/app/integrations/gemini_deep_research/prompts.py` | Safe Deep Research prompt templates. |
| `backend/app/integrations/gemini_deep_research/storage.py` | Evidence pack and shadow run persistence. |
| `backend/app/integrations/gemini_deep_research/shadow_compare.py` | Comparison engine. |
| `backend/app/integrations/gemini_deep_research/workflow_nodes.py` | Optional shadow/assist LangGraph nodes. |
| `backend/app/integrations/gemini_deep_research/security.py` | Redaction and prompt safety helpers. |
| `docs/gemini_shadow_comparison.md` | Optional aggregate shadow comparison document. |
| `data/research/evidence_packs/.gitkeep` | Optional artifact directory marker if tracking empty dirs. |
| `data/research/gemini_shadow_runs/.gitkeep` | Optional artifact directory marker if tracking empty dirs. |

## 15. Files That Would Need to Be Modified Later

No modifications are required for Phase 0.

Later implementation would likely modify:

| File | Future Change |
|---|---|
| `backend/app/config.py` | Add `SEER_GEMINI_*` Deep Research flags without changing existing `GEMINI_*` generateContent settings. |
| `backend/app/workflow.py` | Add optional shadow/assist nodes only after client and normalizer tests pass. |
| `backend/app/graph/state.py` | Add optional non-production shadow metadata fields if needed. Avoid fields consumed by V2 gates in shadow mode. |
| `backend/app/llm/arbitration.py` | Possibly add explicit Deep Research advisory lanes. Do not loosen forbidden decision lanes. |
| `backend/app/agents/context_interpreter.py` | Later replacement hook only after Phase 7 approval. |
| `backend/app/agents/black_swan_generator.py` | Later replacement hook only after Phase 8 approval. |
| `backend/app/agents/evidence_analyst.py` | Later assist-mode ingestion of normalized Gemini evidence candidates. |
| `backend/app/agents/report_writer.py` | Only if validated Gemini evidence should be displayed in production reports. Shadow reports should be separate. |
| `backend/tests/test_config.py` | Add config validation tests for new flags. |
| `backend/tests/test_arbitration.py` | Add Deep Research lane enforcement tests. |

## 16. Tests That Would Need to Be Added Later

| Test File | Coverage |
|---|---|
| `backend/tests/test_gemini_deep_research_client.py` | Create/poll/timeout/fail API wrapper behavior with mocked Interactions API. |
| `backend/tests/test_gemini_evidence_normalizer.py` | Raw report to `GeminiEvidencePack` mapping, no-source gaps, date handling, atomic claims. |
| `backend/tests/test_gemini_contracts.py` | Normalized `AgentOutput` passes Pydantic and `SchemaValidator`; malformed output fails. |
| `backend/tests/test_gemini_shadow_mode.py` | Shadow artifacts are written and forecast outputs are unchanged. |
| `backend/tests/test_gemini_no_probability_injection.py` | Gemini event probabilities do not create `Signal`, `HorizonForecast`, or `FusionResult`. |
| `backend/tests/test_gemini_source_governance.py` | Weak or disallowed sources are marked, rejected, or quarantined. |
| `backend/tests/test_gemini_dedup_independence.py` | Gemini duplicate citations are clustered and independence-scored locally. |
| `backend/tests/test_gemini_replace_context_fallback.py` | Replacement falls back to `ContextInterpreter` on timeout/malformed/no-source output. |
| `backend/tests/test_gemini_replace_black_swan_fallback.py` | Replacement falls back to local `BlackSwanGenerator` on failure. |
| `backend/tests/v2_integration/test_gemini_shadow_non_interference.py` | End-to-end V2 forecast is unchanged in shadow mode. |

## 17. Files Analyzed

All required files were present and analyzed:

| File | Status | Notes |
|---|---|---|
| `docs/agents_function.md` | Present | Audit inventory and replaceability notes. |
| `docs/agents_function_summary.md` | Present | Summary of critical, replaceable, and protected agents. |
| `backend/app/workflow.py` | Present | V2 LangGraph topology, join barrier, V2 gates, Quantifier tripwires. |
| `backend/app/graph/contracts.py` | Present | Evidence, claim, agent output, signal, forecast, critic, and fail-closed contracts. |
| `backend/app/agents/context_interpreter.py` | Present | Current news/GDELT/MCP context and AgentOutput builder. |
| `backend/app/agents/black_swan_generator.py` | Present | Tail-risk generator and V2 AgentOutput behavior. |
| `backend/app/agents/think_tank_analyst.py` | Present | Recursive think-tank retrieval, RSS sources, grounding checks, V3 gap output. |
| `backend/app/agents/walled_garden_analyst.py` | Present | Trusted sources, allowlist-style search, BYOD strict/hybrid handling, V3 gap output. |
| `backend/app/agents/evidence_analyst.py` | Present | Evidence summary bridge and skipped-agent IntelligenceGap injection. |
| `backend/app/agents/schema_validator.py` | Present | Contract validation and gap integrity checks. |
| `backend/app/agents/quantifier_v2.py` | Present | Deterministic fusion, signal extraction, log-odds extremization, Monte Carlo CI. |
| `backend/app/agents/critic_v2.py` | Present | Deterministic validation and bounded reanalysis. |
| `backend/app/agents/governor.py` | Present | Ethics, citation chain, data protection, PII, harmful content, bias checks. |
| `backend/app/llm/arbitration.py` | Present | Gemini advisory-only and forbidden-lane policy. |
| `backend/app/retrieval/librarian.py` | Present | Allowlist, cache, rate limit, audit, `fetch_with_evidence`. |

Additional relevant files analyzed:

| File | Why |
|---|---|
| `backend/app/graph/state.py` | State keys and reducers relevant to shadow non-interference. |
| `backend/app/retrieval/evidence_deduper.py` | Deduplication and clustering rules for Gemini citations. |
| `backend/app/retrieval/independence_analyzer.py` | Source independence scoring rules. |
| `backend/app/agents/political_studies_analyst.py` | Partial support target with ACLED/GDELT/legislation event logic. |
| `backend/app/agents/report_writer.py` | Final production report behavior and Intelligence Gaps appendix. |
| `backend/app/llm/client.py` | Existing normal Gemini `generateContent` client, distinct from Deep Research Interactions API. |
| `backend/GEMINI_SETUP.md` | Existing Gemini key setup for normal Gemini usage. |
| `backend/verify_gemini.py` | Existing normal Gemini smoke test. |

Missing required files:

```text
None.
```

## 18. Final Recommendation

Proceed only with Phase 0 complete and then Phase 1 in isolation. Do not wire Gemini Deep Research into the production workflow until:

1. A separate Interactions API client exists.
2. A local normalizer can convert Deep Research reports into contract-valid evidence packs.
3. Shadow mode proves non-interference with forecast outputs.
4. Comparison reports show Gemini improves source quality, source freshness, useful evidence count, or tail-risk coverage.
5. Protected components remain untouched and authoritative.

The safest next implementation prompt is:

```text
Implement Phase 1 only: create a Gemini Deep Research Interactions API client wrapper under backend/app/integrations/gemini_deep_research/ with mocked tests. Do not modify workflow.py, agents, contracts.py, environment files, package files, or production behavior. The client must support create, poll, timeout, failure metadata, and dry-run/mocked operation.
```

