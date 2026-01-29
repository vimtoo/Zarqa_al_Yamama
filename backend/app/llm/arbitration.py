
from enum import Enum
from typing import Optional, List, Dict
import logging

logger = logging.getLogger("arbitration_policy")

class ArbitrationLane(Enum):
    FORBIDDEN = "forbidden"      # No Gemini Allowed (Probabilities, Weights, Claims)
    ADVISORY = "advisory"        # Gemini Allowed for Synthesis/Wording
    CROSSCHECK = "crosscheck"    # Dual Model Required (High Sensitivity)

class TaskType(Enum):
    SYNTHESIS = "synthesis"      # Writing, Summarizing
    DECISION = "decision"        # Routing, Scoring, Judging
    EXTRACTION = "extraction"    # Extracting entities/metrics

class Sensitivity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ArbitrationPolicy:
    """
    Arbitration Policy for LLM Provider Selection.
    Enforces 'Gemini Advisory-Only' Doctrine.
    """
    
    # Agents allowed to use Gemini for specific tasks
    ALLOWED_ADVISORY = {
        "ThinkTankAnalyst",
        "ReportWriter"
    }
    
    # Agents consistently forbidden from Gemini for decision/scoring
    FORBIDDEN_DECISION_MAKERS = {
        "TemporalAnalyst",       # Probabilities
        "PoliticalStudiesAnalyst", # Weights/Scores
        "DomainRouter",          # Routing
        "Governor",              # Final Adjudication
        "IndependenceAnalyzer"   # Claims/Consensus
    }

    @classmethod
    def get_lane(cls, agent_name: str, task_type: TaskType = TaskType.DECISION, sensitivity: Sensitivity = Sensitivity.MEDIUM) -> ArbitrationLane:
        """
        Determine the Arbitration Lane based on Agent, Task, and Sensitivity.
        """
        
        # RULE 1: Forbidden Deciders never touch Gemini for Decisions/Extraction
        if agent_name in cls.FORBIDDEN_DECISION_MAKERS:
            if task_type in (TaskType.DECISION, TaskType.EXTRACTION):
                return ArbitrationLane.FORBIDDEN
        
        # RULE 2: Advisory Lane for Allowed Synthesis Agents
        if agent_name in cls.ALLOWED_ADVISORY:
            if task_type == TaskType.SYNTHESIS:
                return ArbitrationLane.ADVISORY
            
        # RULE 3: High Sensitivity triggers Crosscheck (Conceptual for now)
        if sensitivity == Sensitivity.HIGH:
            return ArbitrationLane.CROSSCHECK
            
        # Default: Forbidden if not explicitly allowed for advisory
        # (Conservative default)
        return ArbitrationLane.FORBIDDEN

    @classmethod
    def resolve_model(cls, lane: ArbitrationLane, gemini_enabled: bool, primary_model: str = "default") -> Dict[str, str]:
        """
        Resolve the final model to use and logging metadata.
        Returns dict with keys: model_used, reason, lane.
        """
        if not gemini_enabled:
            return {
                "model_used": primary_model,
                "reason": "gemini_disabled",
                "lane": lane.value
            }
            
        if lane == ArbitrationLane.FORBIDDEN:
            return {
                "model_used": primary_model,
                "reason": "lane_forbidden",
                "lane": lane.value
            }
            
        if lane == ArbitrationLane.ADVISORY:
            # Advisory allows Gemini
            return {
                "model_used": "gemini-pro",
                "reason": "advisory_lane_allowed",
                "lane": lane.value
            }
            
        if lane == ArbitrationLane.CROSSCHECK:
            # Crosscheck not fully implemented in plumbing, default to primary for safety
            # But doctrine says "triggers dual-model". We return primary but flag it.
            return {
                "model_used": primary_model,
                "reason": "crosscheck_primary",
                "lane": lane.value
            }
            
        return {
            "model_used": primary_model,
            "reason": "default_fallback",
            "lane": "unknown"
        }
