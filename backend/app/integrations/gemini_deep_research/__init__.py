"""
Gemini Deep Research integration package.

Clean selective branch scope:
- Phase 1: client wrapper
- Phase 2: evidence normalizer
- Phase 3A: shadow comparator
- Phase 3B: shadow runner
- Phase 3C: evaluation policy

No Phase 4 assist-mode imports.
No workflow integration.
No live Gemini enablement by default.
"""

from app.integrations.gemini_deep_research.client import GeminiDeepResearchClient
from app.integrations.gemini_deep_research.models import (
    GeminiDeepResearchRequest,
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
    GeminiDeepResearchError,
    GeminiInteractionMetadata,
    GeminiEvidencePack,
    GeminiShadowRun,
    GeminiEvaluationDecision,
)
from app.integrations.gemini_deep_research.normalizer import GeminiEvidenceNormalizer
from app.integrations.gemini_deep_research.shadow_compare import GeminiShadowComparator
from app.integrations.gemini_deep_research.shadow_runner import GeminiShadowRunner
from app.integrations.gemini_deep_research.evaluation_policy import GeminiShadowEvaluationPolicy

__all__ = [
    "GeminiDeepResearchClient",
    "GeminiDeepResearchRequest",
    "GeminiDeepResearchResult",
    "GeminiDeepResearchStatus",
    "GeminiDeepResearchError",
    "GeminiInteractionMetadata",
    "GeminiEvidencePack",
    "GeminiShadowRun",
    "GeminiEvaluationDecision",
    "GeminiEvidenceNormalizer",
    "GeminiShadowComparator",
    "GeminiShadowRunner",
    "GeminiShadowEvaluationPolicy",
]
