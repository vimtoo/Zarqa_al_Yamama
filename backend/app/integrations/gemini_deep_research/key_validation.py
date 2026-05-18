"""
Phase 4Z-C: Fail-Closed API Key / HTTP Header Validation
=========================================================

Validates a Gemini API key value before it is placed into an HTTP header.
The validator is called by GeminiDeepResearchClient.create_interaction() and
poll_interaction() on every non-mock live path, before _post_interaction() is
invoked.

Design rules
------------
* NEVER log or return the raw key value.
* NEVER call Gemini, the network, or any external API.
* Return a structured KeyValidationResult with ok, reason_code, safe_message.
* Reject conservatively: when in doubt, fail closed.

Reason codes
------------
missing                     key is None or not a string
empty                       key is "" after strip
whitespace_only             key is all whitespace
placeholder                 key matches a known placeholder literal
contains_brackets           key contains "[" or "]"
contains_newline            key contains \\n
contains_carriage_return    key contains \\r
contains_tab                key contains \\t
contains_control_character  key contains any ASCII control char (0x00-0x1F, 0x7F)
leading_or_trailing_ws      key has leading or trailing whitespace
contains_space              key contains an internal space
too_short                   key is shorter than MIN_KEY_LENGTH chars
invalid_header_value        key cannot be safely encoded as an ISO-8859-1 HTTP header value
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Minimum plausible length for a real Gemini API key (AIzaSy…, 39 chars)
MIN_KEY_LENGTH = 20

# Known placeholder strings that must never reach the provider.
# All comparisons are case-insensitive.
_PLACEHOLDER_VALUES = frozenset(
    {
        "[redacted_api_key]",
        "redacted_api_key",
        "paste_your_key_here",
        "paste_your_non_production_gemini_key_here",
        "your_non_production_key_here",
        "placeholder",
        "changeme",
        "dummy",
        "test",
        "your_gemini_api_key_here",
        "your_api_key_here",
        "enter_key_here",
        "insert_key_here",
        "none",
        "null",
        "undefined",
        "",  # keep explicit for clarity
    }
)


@dataclass(frozen=True)
class KeyValidationResult:
    """Structured, key-free validation result."""

    ok: bool
    reason_code: str
    safe_message: str

    @classmethod
    def pass_(cls) -> "KeyValidationResult":
        return cls(
            ok=True,
            reason_code="ok",
            safe_message="API key passed header-safety validation.",
        )

    @classmethod
    def fail(cls, reason_code: str, safe_message: str) -> "KeyValidationResult":
        return cls(ok=False, reason_code=reason_code, safe_message=safe_message)


def validate_api_key_for_header(key: Optional[str]) -> KeyValidationResult:
    """
    Validate *key* for safe use as an HTTP header value.

    The raw key is never included in the returned result or in any log output.
    """
    # 1. Type / missing check
    if key is None or not isinstance(key, str):
        return KeyValidationResult.fail(
            "missing",
            "API key is missing or not a string. Set GEMINI_API_KEY before live use.",
        )

    # 2. Empty / whitespace-only
    if not key:
        return KeyValidationResult.fail(
            "empty",
            "API key is an empty string. Set GEMINI_API_KEY before live use.",
        )

    if not key.strip():
        return KeyValidationResult.fail(
            "whitespace_only",
            "API key contains only whitespace characters and cannot be used as an HTTP header value.",
        )

    # 3. Control characters — MUST be checked before strip/whitespace comparison,
    #    because abc\n would otherwise be caught as leading_or_trailing_ws first.
    if "\n" in key:
        return KeyValidationResult.fail(
            "contains_newline",
            "API key contains a newline character (\\n) which is illegal in HTTP header values.",
        )
    if "\r" in key:
        return KeyValidationResult.fail(
            "contains_carriage_return",
            "API key contains a carriage-return character (\\r) which is illegal in HTTP header values.",
        )
    if "\t" in key:
        return KeyValidationResult.fail(
            "contains_tab",
            "API key contains a tab character (\\t) which is illegal in HTTP header values.",
        )
    for ch in key:
        code = ord(ch)
        if code < 0x20 or code == 0x7F:
            return KeyValidationResult.fail(
                "contains_control_character",
                f"API key contains ASCII control character 0x{code:02X} which is illegal in HTTP header values.",
            )

    # 4. Leading / trailing whitespace (spaces, not control chars — those were caught above)
    if key != key.strip():
        return KeyValidationResult.fail(
            "leading_or_trailing_ws",
            "API key has leading or trailing whitespace. Strip the value before use.",
        )

    # 5. Bracket characters (strong signal of a redacted/placeholder value)
    if "[" in key or "]" in key:
        return KeyValidationResult.fail(
            "contains_brackets",
            "API key contains bracket characters ('[' or ']'). "
            "This is a strong indicator of a redacted or placeholder value.",
        )

    # 6. Internal spaces
    if " " in key:
        return KeyValidationResult.fail(
            "contains_space",
            "API key contains an internal space character which is not valid in API keys "
            "and may cause httpx illegal-header-value errors.",
        )

    # 7. Placeholder check (case-insensitive)
    if key.lower() in _PLACEHOLDER_VALUES:
        return KeyValidationResult.fail(
            "placeholder",
            "API key matches a known redacted-marker or default-value string. "
            "Replace it with a real, approved Gemini API key before live use.",
        )

    # 8. Minimum length
    if len(key) < MIN_KEY_LENGTH:
        return KeyValidationResult.fail(
            "too_short",
            f"API key is shorter than {MIN_KEY_LENGTH} characters and is unlikely to be a valid key.",
        )

    # 9. HTTP header value encoding check (ISO-8859-1 per RFC 7230)
    try:
        key.encode("latin-1")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return KeyValidationResult.fail(
            "invalid_header_value",
            "API key contains characters that cannot be encoded as an HTTP header value (ISO-8859-1).",
        )

    return KeyValidationResult.pass_()
