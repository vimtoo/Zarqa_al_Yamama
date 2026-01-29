# backend/app/llm/antigravity.py
"""
ANTIGRAVITY: SINGLE PROMPT AUTHORITY
------------------------------------
This module is the SOLE source of truth for all LLM prompts in the Zarqa system,
structurally enforced by client.py.

GOVERNANCE STATUS:
- V2 Authority: ACTIVE
- V1 Legacy Leaks: DOCUMENTED (Non-Blocking)
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional


DEFAULT_SYSTEM_PROMPT = (
    "You are an analytical instrument inside Zarqa al-Yamama. "
    "Output JSON only. Do not speculate. Cite evidence IDs only."
)

PROMPTS: Dict[str, Dict[str, str]] = {
    "market_adapter_v1": {
        "micro": (
            "TASK: Convert Market Classifier output into STRICT AgentOutput JSON.\n"
            "INTERNAL SIGNALS ONLY. No external facts. evidence must be [].\n"
            "claims 1-3 max, type=internal_signal, horizon=SHORT_TERM.\n"
            "signals must include scenario_is_market (0/1).\n"
            "Output JSON only."
        )
    },
    "context_adapter_v1": {
        "micro": (
            "TASK: Extract 2-6 atomic claims from provided EvidenceItem list.\n"
            "Every claim MUST reference evidence_ids.\n"
            "No new evidence. No causality inference. Tag horizon.\n"
            "Output AgentOutput JSON only."
        )
    },
    "json_repair_v1": {
        "micro": (
            "You are a JSON repair tool. Return corrected JSON only.\n"
            "Do not add facts. If missing info, add uncertainty_notes.\n"
        )
    },
    "domain_router_v2": {
        "system": "You are the ZARQA Domain Router. Classification expert.",
        "micro": (
            "Output STRICT JSON object with keys: domains (list), primary_domain (str), confidence (float), reasoning (str).\n"
            "Example: {'domains': ['geopolitics', 'finance'], 'primary_domain': 'geopolitics', 'confidence': 0.9, 'reasoning': '...'}\n"
            "Task:\n"
            "1. Identify ALL relevant domains (multi-label).\n"
            "2. Identify the PRIMARY domain (root cause).\n"
            "3. Provide brief reasoning.\n"
            "4. Assign confidence (0.0 - 1.0).\n"
        )
    },
    "conflict_metrics_v1": {
        "system": "You are a Conflict Data Analyst. Output strict JSON.",
        "micro": (
            "Analyze the conflict dynamics in the provided text.\n"
            "--- ANCHOR CATALOG (REQUIRED) ---\n"
            "Band A (0-20): Isolated Incidents (Peaceful Protests ~5, Minor Scuffles ~15)\n"
            "Band B (21-40): Organized Unrest (Riots ~25, Police Clashes ~35)\n"
            "Band C (41-60): Sustained Violent Activity (Insurgency ~45, Paramilitary ~55)\n"
            "Band D (61-80): Insurgency-Level Violence (Lost Control ~65, Mass Events ~75)\n"
            "Band E (81-100): Civil War Intensity (Fronts ~85, Collapse ~95)\n\n"
            "Task: Map to an Anchor ID first, then assign Score.\n"
            "Output Dictionary:\n"
            "- velocity: (float) Rate of change/acceleration.\n"
            "- intensity_score: (float 0-100) MUST align with selected anchor.\n"
            "- anchor_id: (str) The ID from catalog (e.g. 'B1').\n"
            "- band: (str) 'A', 'B', 'C', 'D', or 'E'.\n"
            "- hotspots: (list[str]) Specific locations.\n"
            "- trend: (enum) 'accelerating', 'stable', 'decelerating'\n"
        )
    },
    "bias_triangulation_v1": {
        "system": "You are a Bias Analyst. You detect underlying source conflict. Output strictly valid JSON.",
        "micro": (
            "Analyze the disagreement and bias in the provided sources.\n"
            "Task: Generate a Bias Triangulation Report (JSON).\n"
            "Requirements:\n"
            "1. classify consensus_status: Consensus | Divided | Polarized | Chaos\n"
            "2. identify divergence_point: The core factual or normative dispute.\n"
            "3. list positions: source_id (Source X), stance (Supports/Refutes/Neutral), bias_rating (e.g. Pro-Gov, Corporate, etc)\n"
            "4. identify unrepresented_perspective: List[str] (Who is missing?)\n"
        )
    },
}


def build_messages(
    agent_name: str,
    scenario: str,
    payload: Dict[str, Any],
    evidence: Optional[Any] = None,
    mode: str = "normal",
) -> List[Dict[str, str]]:
    """
    Minimal runnable message builder.
    - mode="normal": system + micro prompt + payload JSON
    - mode="repair": system + repair prompt + payload JSON
    """
    if mode == "repair":
        micro = PROMPTS["json_repair_v1"]["micro"]
        system_content = PROMPTS["json_repair_v1"].get("system", DEFAULT_SYSTEM_PROMPT)
    else:
        config = PROMPTS.get(agent_name, {})
        micro = config.get("micro", "")
        system_content = config.get("system", DEFAULT_SYSTEM_PROMPT)

    input_obj = {"scenario": scenario, "payload": payload}
    if evidence is not None:
        input_obj["evidence"] = evidence

    user_content = micro + "\n\nINPUT_JSON:\n" + json.dumps(input_obj, ensure_ascii=False)

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def prompt_fingerprint(prompt_id: str, version: str, content: str = "") -> str:
    """
    Stable hash fingerprint. If content is provided, hash it; otherwise hash id+version.
    """
    base = content if content else f"{prompt_id}:{version}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
