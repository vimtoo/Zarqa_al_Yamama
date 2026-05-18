"""Test-only helpers for Gemini sidecar secret hygiene checks."""

from __future__ import annotations


FAKE_SECRET_LIKE_VALUES = (
    "AIzaFakeSidecarSecretValueForRedaction12345",
    "sk-fakeSidecarSecretValueForRedaction12345",
    "Bearer fakeBearerTokenForRedaction12345",
    "api_key=fake_sidecar_api_key_value",
    "password=fake_sidecar_password_value",
    "token=fake_sidecar_token_value",
    "secret=fake_sidecar_secret_value",
    "Authorization: Bearer fakeAuthorizationToken12345",
    "[REDACTED_API_KEY]",
)


def assert_fake_secret_values_absent(payload: str) -> None:
    """Assert fake secret-like strings are absent from serialized artifacts."""
    for value in FAKE_SECRET_LIKE_VALUES:
        assert value not in payload
