# Golden Run Report
**Date**: 2025-12-25T19:37:38.308159

## Scenario 1: Answerable (True)
* **Type**: Deterministic Golden (mocked retrieval)
* **Outcome**: PASS (Mocked)
* **Artifacts**: [View Bundle](scenario_01_answerable_true/)

## Scenario 2: Governance Halt
* **Type**: Deterministic Golden (policy-triggered / mocked)
* **Outcome**: HALTED
* **Artifacts**: [View Bundle](scenario_02_unknown_or_halt/)

## Scenario 1 (Answerable Live)
* **Type**: Live Golden (real retrieval; may PASS or end Unknown)
* **Goal**: Execute production pipeline against allowlist.
* **Input**: "What is the specific target for renewable energy in Kuwait's Vision 2035 and cite the source date?"
* **Outcome**: TERMINATE_MAX_DEPTH (Search Limited)
* **Details**: 
    1. **LLM Connectivity**: ✅ SUCCESS. DeepSeek API accepted keys and generated plans ("Kuwait Vision 2035...").
    2. **Retrieval**: ⚠️ EMPTY. Search returned 0 results (scraper/allowlist restriction). 
    3. **Safety**: ✅ SUCCESS. System failed safely to Max Depth without hallucination.
* **Artifacts**: [View Bundle](scenario_01_answerable_live/)

## Scenario 1 (Depth Capped): Archived diagnostic
* **Type**: Archived diagnostic
* **Artifacts**: [View Bundle](scenario_01_depth_capped/)
