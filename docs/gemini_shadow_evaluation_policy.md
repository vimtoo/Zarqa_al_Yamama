# Gemini Deep Research Shadow Evaluation Policy

## 1. Purpose of Phase 3C

Phase 3C adds a repeatable local policy engine for evaluating Gemini Deep Research shadow runs. It decides whether Gemini is not useful, useful only in shadow mode, useful as an assistant candidate, ready for a limited assist-mode trial, a future replacement candidate for selected early-stage agents, or requires human review.

This phase does not connect Gemini to TheSeer production workflow.

## 2. Why Policy Is Needed Before Assist Mode

One successful shadow run is not enough to change system behavior. Deep Research can improve source discovery, but TheSeer must preserve deterministic validation, probability fusion, source governance, and safety gates. A repeat-run policy prevents isolated good results from being mistaken for operational readiness.

## 3. Protected Components

The evaluation policy does not modify or bypass:

- `workflow.py`
- `contracts.py`
- `ContextInterpreter`
- `BlackSwanGenerator`
- `QuantifierV2`
- `CriticV2`
- `Governor`
- `SchemaValidator`
- `Librarian`
- `ArbitrationPolicy`
- `EvidenceDeduper`
- `IndependenceAnalyzer`

It does not write production forecast state or agent output directories.

## 4. Shadow-Run Metrics

The policy aggregates:

- total, successful, failed, timeout, disabled, malformed, and incomplete runs
- high, critical, and unknown risk counts
- average useful new evidence
- average source overlap
- average unsupported claims
- average contradictions
- average duplicate evidence
- average latency when available
- failure or timeout ratio
- recommendation distribution
- overall risk distribution
- selected agent-overlap averages
- warnings indicating secret leakage or probability contamination

## 5. Thresholds

Default thresholds are conservative:

| Threshold | Default |
|---|---:|
| minimum shadow-value runs | 3 |
| minimum assist-trial runs | 5 |
| minimum replacement-candidate runs | 10 |
| max high-risk run ratio | 0.2 |
| max critical risk runs | 0 |
| min average useful new evidence | 2 |
| min average source overlap | 0.2 |
| max average unsupported claims | 1 |
| max average contradictions | 2 |
| max average duplicate evidence | 5 |
| max average latency seconds | 900 |
| max failure or timeout ratio | 0.1 |
| require zero secret leakage | true |
| require zero probability contamination for assist | true |
| require human review for replacement | true |

## 6. Domain Profiles

Supported profiles are:

- `geopolitics`
- `security`
- `policy`
- `macroeconomics`
- `finance`
- `technology`
- `elections`
- `general`

Geopolitics, security, elections, and finance require human review before readiness moves beyond shadow mode. Finance applies stricter freshness and source-overlap standards. Elections apply stricter unsupported-claim tolerance. Geopolitics and security apply stricter source-governance and contradiction tolerance.

## 7. Recommendation Labels

The policy may return only:

- `Gemini not useful`
- `Gemini useful as shadow only`
- `Gemini useful as assistant`
- `Gemini ready for limited assist-mode trial`
- `Gemini candidate for future ContextInterpreter replacement`
- `Gemini candidate for future BlackSwanGenerator replacement`
- `Gemini requires human review`

## 8. Human Review Rules

Human review is required when:

- ContextInterpreter or BlackSwanGenerator replacement candidacy is evaluated
- geopolitics, security, elections, or finance moves above shadow readiness
- contradictions exceed threshold
- critical risk appears
- secret leakage appears
- source-governance risk is high
- input data is malformed or incomplete

## 9. Why One Good Run Is Not Enough

Gemini Deep Research is an external research capability. A single run can overperform by chance, miss domain-specific governance requirements, or hide repeated failure modes. The policy requires multiple runs before assist-mode or candidate-replacement language is allowed.

## 10. Replacement Is Only Future Candidate Status

The policy never approves replacement. It can only label Gemini as a future candidate for ContextInterpreter or BlackSwanGenerator after many clean shadow runs. Local TheSeer governance, validation, and protected components remain authoritative.

## 11. How To Run Tests

```bash
pytest backend/tests/test_gemini_evaluation_policy.py -q
```

Full Gemini integration slice:

```bash
pytest backend/tests/test_gemini_deep_research_client.py backend/tests/test_gemini_evidence_normalizer.py backend/tests/test_gemini_shadow_compare.py backend/tests/test_gemini_shadow_runner.py backend/tests/test_gemini_evaluation_policy.py -q
```

## 12. Example Policy Evaluation Usage

```python
from app.integrations.gemini_deep_research.evaluation_policy import GeminiShadowEvaluationPolicy

policy = GeminiShadowEvaluationPolicy()
runs = policy.load_runs_from_dir("data/research/gemini_shadow_runs")
decision = policy.evaluate_runs(runs, domain="geopolitics")
report = policy.render_policy_report(decision)
```

## 13. Phase 4 Recommendation

Phase 4 should remain non-destructive. It should define a limited assist-mode trial plan, review governance thresholds, decide which saved shadow-run domains are ready for more tests, and require explicit operator approval before any workflow integration is considered.
