import json
import os

SCENARIOS_DIR = "backend/golden_set"

scenarios = [
    # --- ECONOMIC SHOCKS (Must trigger TemporalAnalyst) ---
    {
        "scenario_id": "GS-001",
        "name": "Suez Canal Blockage (2021)",
        "input_text": "Analysis of Ever Given container ship blocking Suez Canal causing trade disruption.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["logistics", "macroeconomics"],
                "must_activate_agents": ["temporal_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" },
            "uncertainty": { "minimum_unknown_factors": 1, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["supply chain"], "must_not_contain": [] }
        }
    },
    {
        "scenario_id": "GS-002",
        "name": "Oil Price Spike (2022)",
        "input_text": "Impact of crude oil prices hitting $120/barrel due to sanctions speculation.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["finance", "energy"],
                "must_activate_agents": ["temporal_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_II" },
            "uncertainty": { "minimum_unknown_factors": 2, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["inflation"], "must_not_contain": [] }
        }
    },
    {
        "scenario_id": "GS-003",
        "name": "Chip Shortage (2021)",
        "input_text": "Global semiconductor shortage affecting automotive manufacturing.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["technology", "macroeconomics"],
                "must_activate_agents": ["temporal_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" },
            "uncertainty": { "minimum_unknown_factors": 1, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["automotive"], "must_not_contain": [] }
        }
    },
    {
        "scenario_id": "GS-004",
        "name": "Grain Deal Collapse",
        "input_text": "Suspension of Black Sea Grain Initiative affecting wheat futures.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["macroeconomics", "geopolitics"],
                "must_activate_agents": ["temporal_analyst", "political_studies_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_III" },
            "uncertainty": { "minimum_unknown_factors": 2, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["food security"], "must_not_contain": [] }
        }
    },
    {
        "scenario_id": "GS-005",
        "name": "Currency Devaluation (Lira)",
        "input_text": "Rapid devaluation of Turkish Lira causing import inflation.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["finance", "macroeconomics"],
                "must_activate_agents": ["temporal_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_II" },
            "uncertainty": { "minimum_unknown_factors": 1, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["hyperinflation"], "must_not_contain": [] }
        }
    },

    # --- POLITICAL UNREST (Must obey Anchors) ---
    {
        "scenario_id": "GS-006",
        "name": "Paris Pension Protests",
        "input_text": "Violent protests across France following pension reform enactment. Trash fires.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["politics", "security"],
                "must_activate_agents": ["political_studies_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_III" }, # Sustained
            "uncertainty": { "minimum_unknown_factors": 1, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["unrest"], "must_not_contain": ["peaceful assembly"] }
        }
    },
    {
        "scenario_id": "GS-007",
        "name": "Capitol Riot (Jan 6)",
        "input_text": "Crowd breaches US Capitol building. Security overwhelmed. Casualties reported.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["politics", "security"],
                "must_activate_agents": ["political_studies_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_IV" }, # Insurgency/Challenge
            "uncertainty": { "minimum_unknown_factors": 2, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["breach"], "must_not_contain": ["peaceful"] }
        }
    },
    {
        "scenario_id": "GS-008",
        "name": "Sri Lanka Palace Storming",
        "input_text": "Protesters occupy presidential palace in Sri Lanka. President flees.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["politics", "security"],
                "must_activate_agents": ["political_studies_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_IV" },
            "uncertainty": { "minimum_unknown_factors": 3, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["collapse"], "must_not_contain": [] }
        }
    },
    {
        "scenario_id": "GS-009",
        "name": "Iran Mahsa Amini Protests",
        "input_text": "Nationwide protests in Iran following death in custody. Internet blackout.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["politics", "security"],
                "must_activate_agents": ["political_studies_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_IV" },
            "uncertainty": { "minimum_unknown_factors": 3, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["crackdown"], "must_not_contain": [] }
        }
    },
    {
        "scenario_id": "GS-010",
        "name": "Brazil Congress Attack",
        "input_text": "Supporters of former president storm Brazilian Congress and Supreme Court.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["politics", "security"],
                "must_activate_agents": ["political_studies_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_IV" },
            "uncertainty": { "minimum_unknown_factors": 2, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["storm"], "must_not_contain": [] }
        }
    },

    # --- AMBIGUOUS / RUMOR (Must enforce Uncertainty) ---
    {
        "scenario_id": "GS-011",
        "name": "Coup Rumor in China",
        "input_text": "Unverified reports of military movement in Beijing. Flights cancelled.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["politics"],
                "must_activate_agents": [],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" }, # Until confirmed
            "uncertainty": { "minimum_unknown_factors": 5, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["unverified"], "must_not_contain": ["confirmed"] }
        }
    },
    {
        "scenario_id": "GS-012",
        "name": "Kim Jong Un Health Scare",
        "input_text": "Rumors of North Korean leader being in critical condition. No official statement.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["politics"],
                "must_activate_agents": [],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" },
            "uncertainty": { "minimum_unknown_factors": 4, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["speculation"], "must_not_contain": ["dead"] }
        }
    },
    {
        "scenario_id": "GS-013",
        "name": "Putin Health Rumor",
        "input_text": "Tabloid report claims Putin suffered cardiac arrest. Kremlin denies.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["politics"],
                "must_activate_agents": [],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" },
            "uncertainty": { "minimum_unknown_factors": 4, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["denial"], "must_not_contain": ["confirmed"] }
        }
    },
    {
        "scenario_id": "GS-014",
        "name": "Ghost of Kyiv",
        "input_text": "Viral social media posts claim ace pilot shot down 6 jets.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["security"],
                "must_activate_agents": [],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_III" },
            "uncertainty": { "minimum_unknown_factors": 3, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["unconfirmed"], "must_not_contain": ["verified"] }
        }
    },
    {
        "scenario_id": "GS-015",
        "name": "Deepfake CEO",
        "input_text": "Video of CEO announcing bankruptcy circulates. Stock drops. Company calls it fake.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["finance", "technology"],
                "must_activate_agents": ["temporal_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" },
            "uncertainty": { "minimum_unknown_factors": 2, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["fake"], "must_not_contain": [] }
        }
    },
    
    # --- LOW INTENSITY / PEACEFUL ---
    {
        "scenario_id": "GS-016",
        "name": "Climate Summit Protest",
        "input_text": "Peaceful march of 50,000 activists at COP summit. No arrests.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["politics"],
                "must_activate_agents": ["political_studies_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" }, # Must be BAND_I (Peaceful)
            "uncertainty": { "minimum_unknown_factors": 0, "forbidden_confidence": "LOW" }, # High confidence acceptable
            "narrative_invariants": { "must_contain_keywords": ["activists"], "must_not_contain": ["violent"] }
        }
    },
    {
        "scenario_id": "GS-017",
        "name": "Election Night (Generic)",
        "input_text": "Polls close in peaceful general election. Vote counting underway.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["politics"],
                "must_activate_agents": ["political_studies_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" },
            "uncertainty": { "minimum_unknown_factors": 1, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["counting"], "must_not_contain": ["fraud"] }
        }
    },
    {
        "scenario_id": "GS-018",
        "name": "Trade Deal Signing",
        "input_text": "Leaders sign historic free trade agreement reducing tariffs.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["macroeconomics"],
                "must_activate_agents": ["political_studies_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" },
            "uncertainty": { "minimum_unknown_factors": 0, "forbidden_confidence": "LOW" },
            "narrative_invariants": { "must_contain_keywords": ["agreement"], "must_not_contain": ["dispute"] }
        }
    },
     {
        "scenario_id": "GS-019",
        "name": "Tech IPO",
        "input_text": "Major tech unicorn lists on Nasdaq. Shares surge 20%.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["finance", "technology"],
                "must_activate_agents": ["temporal_analyst"],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" },
            "uncertainty": { "minimum_unknown_factors": 0, "forbidden_confidence": "LOW" },
            "narrative_invariants": { "must_contain_keywords": ["market"], "must_not_contain": [] }
        }
    },
    {
        "scenario_id": "GS-020",
        "name": "Scientific Discovery",
        "input_text": "Researchers announce cure for malaria. Peer review pending.",
        "expected_behavior": {
            "routing": {
                "must_include_domains": ["technology"],
                "must_activate_agents": [],
                "forbidden_agents": []
            },
            "metrics": { "conflict_intensity_band": "BAND_I" },
            "uncertainty": { "minimum_unknown_factors": 1, "forbidden_confidence": "HIGH" },
            "narrative_invariants": { "must_contain_keywords": ["research"], "must_not_contain": ["political"] }
        }
    }
]

if not os.path.exists(SCENARIOS_DIR):
    os.makedirs(SCENARIOS_DIR)

for s in scenarios:
    path = os.path.join(SCENARIOS_DIR, f"{s['scenario_id']}.json")
    with open(path, 'w') as f:
        json.dump(s, f, indent=2)

print(f"Generated {len(scenarios)} scenarios in {SCENARIOS_DIR}")
