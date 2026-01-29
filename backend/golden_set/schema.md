# Calibration Dataset Schema

**Version:** 1.0 (Fixed)
**Location:** `backend/golden_set/*.json`

Each JSON file in this directory represents a canonical historical or synthetic scenario used to detect epistemic drift.

## Schema Definition

```json
{
  "scenario_id": "GS-001",
  "name": "Historical Event Name",
  "input_text": "The raw user query or context snippet used to trigger the system.",
  "expected_behavior": {
    "routing": {
      "must_include_domains": ["GEOPOLITICS", "MACROECONOMICS"],
      "must_activate_agents": ["PoliticalStudiesAnalyst", "TemporalAnalyst"],
      "forbidden_agents": ["ReportWriter"]
    },
    "metrics": {
      "conflict_intensity_band": "BAND_III", // BAND_I (0-20), BAND_II (21-40), BAND_III (41-60), BAND_IV (61-80), BAND_V (81-100)
      "conflict_anchor_ref": "Anchor_C",
      "economic_impact_severity": "HIGH"
    },
    "uncertainty": {
      "minimum_unknown_factors": 3,
      "forbidden_confidence": "HIGH" // If the event was historically uncertain
    },
    "narrative_invariants": {
      "must_contain_keywords": ["supply chain", "inflation", "protest"],
      "must_not_contain": ["peaceful assembly", "minor disruption"]
    }
  }
}
```

## Bands Reference

*   **BAND_I (0-20):** Latent/Political (No physical violence)
*   **BAND_II (21-40):** Sporadic Unrest (Isolated incidents)
*   **BAND_III (41-60):** Sustained Confrontation (Organized, non-lethal)
*   **BAND_IV (61-80):** Insurgency (Lethal, territory denial)
*   **BAND_V (81-100):** Total Conflict (Heavy weaponry, collapse)
