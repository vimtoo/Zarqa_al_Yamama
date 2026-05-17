"""Safe prompt helpers for Gemini Deep Research.

These helpers do not include TheSeer internal system prompts and should only
receive sanitized public-context strings.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional


_SENSITIVE_MARKERS = (
    ".env",
    "api_key",
    "apikey",
    "authorization",
    "bearer ",
    "credential",
    "database_url",
    "password",
    "private_key",
    "secret",
    "token",
)


def _context_to_text(context: Any) -> str:
    if context is None:
        return ""
    if isinstance(context, str):
        return context
    if isinstance(context, Mapping):
        lines = []
        for key, value in context.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    return str(context)


def _sanitize_context(context: Any, max_chars: int = 4000) -> str:
    """Drop obviously sensitive lines from optional prompt context."""
    text = _context_to_text(context)
    safe_lines = []
    for line in text.splitlines():
        lowered = line.lower()
        if any(marker in lowered for marker in _SENSITIVE_MARKERS):
            continue
        safe_lines.append(line)
    return "\n".join(safe_lines).strip()[:max_chars]


def build_deep_research_prompt(user_question: str, context: Optional[Any] = None) -> str:
    """Build a safe, research-only Deep Research prompt.

    The prompt intentionally prohibits forecast probabilities and private-data
    claims because Phase 1 only gathers raw research reports.
    """
    question = _sanitize_context(user_question)
    safe_context = _sanitize_context(context)

    context_block = ""
    if safe_context:
        context_block = f"\nOptional public context:\n{safe_context}\n"

    return (
        "You are supporting an external research-only workflow. "
        "Perform Gemini Deep Research on the question below.\n\n"
        f"Research question:\n{question}\n"
        f"{context_block}\n"
        "Instructions:\n"
        "- Gather relevant public sources and cite each source with URLs when available.\n"
        "- Identify source dates, publishers, and whether each source is primary reporting, official data, analysis, aggregator, or social content when possible.\n"
        "- Identify contradictions between sources and preserve disagreement instead of forcing consensus.\n"
        "- Identify uncertainty, missing evidence, and source limitations.\n"
        "- Distinguish evidence-backed findings from speculation or scenario hypotheses.\n"
        "- Do not generate final probabilities, forecast probabilities, odds, fused estimates, or probability bands.\n"
        "- Do not claim access to private data, local files, credentials, internal tools, or non-public documents.\n"
        "- Do not fabricate citations, publication dates, source titles, or URLs.\n"
        "- If a claim is unsupported by cited sources, label it as unsupported or speculative.\n"
        "- Return a structured research report with sections for sources, evidence-backed findings, contradictions, uncertainty, intelligence gaps, and speculative hypotheses.\n"
    )
