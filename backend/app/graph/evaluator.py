"""
Sufficiency Evaluator (Deterministic)
Rule-based evaluation of EvidencePacks for recursion control.
Strict adherence to Rule 6.
"""

import logging
from typing import Literal, Dict
from app.graph.schema import EvidencePack, EvidenceItem

logger = logging.getLogger(__name__)

EvaluationOutcome = Literal["PASS", "FAIL_CONTINUE", "TERMINATE_MAX_DEPTH", "TERMINATE_GOVERNOR_HALT"]

class SufficiencyEvaluator:
    """
    Deterministic logic to decide if research is sufficient.
    No LLM calls allowed.
    """

    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self.min_sources = 2

    def evaluate(self, pack: EvidencePack) -> EvaluationOutcome:
        """
        Evaluate if the evidence pack meets v1.1 sufficiency standards.
        Input: EvidencePack
        Output: PASS | FAIL_CONTINUE | TERMINATE_MAX_DEPTH | TERMINATE_GOVERNOR_HALT
        """
        depth = pack.recursion_stats.get("depth", 0)

        # 1. Governance Halt Check
        if pack.governor_halt_report:
            logger.warning("Evaluator: Governance Halt detected. Terminating.")
            return "TERMINATE_GOVERNOR_HALT"

        # 2. Max Depth Check
        if depth >= self.max_depth:
            logger.info("Evaluator: Max depth reached. Terminating.")
            return "TERMINATE_MAX_DEPTH"
            
        # 3. Source Count Check
        unique_sources = set(item.source_url for item in pack.items)
        if len(unique_sources) < self.min_sources:
             logger.info(f"Evaluator: Insufficient sources ({len(unique_sources)} < {self.min_sources}). Continuing.")
             return "FAIL_CONTINUE"
             
        # 4. Critical Logic (Contradictions, Missing Info)
        # Assuming missing_information is populated by previous extraction step
        if pack.missing_information:
             # Check if missing info is substantial (not just 'none')
             # Simple heuristic: if list is not empty and doesn't say "none"
             first_miss = pack.missing_information[0].lower()
             if "none" not in first_miss and "sufficient" not in first_miss:
                 logger.info("Evaluator: Missing information flagged. Continuing.")
                 return "FAIL_CONTINUE"
                 
        if pack.contradictions:
             logger.info("Evaluator: Contradictions detected. Continuing.")
             return "FAIL_CONTINUE"
             
        # If all checks pass
        logger.info("Evaluator: SUFFICIENCY REACHED.")
        return "PASS"

evaluator = SufficiencyEvaluator()
