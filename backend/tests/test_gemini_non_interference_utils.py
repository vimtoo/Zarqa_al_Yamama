from __future__ import annotations

import dataclasses
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path

import pytest

from gemini_non_interference_utils import (
    REDACTED,
    assert_canonical_equal,
    assert_no_agent_output_for_gemini,
    assert_no_gemini_keys,
    assert_protected_keys_unchanged,
    build_default_exclusions,
    canonical_json_dump,
    canonicalize_report,
    canonicalize_value,
    capture_artifact,
    capture_report_artifact,
    diff_canonical,
    load_artifact,
    load_report_artifact,
    normalize_datetime,
    normalize_path_string,
    protected_state_keys,
    remove_nondeterministic_fields,
)


class MockEnum(Enum):
    SUPPORTED = "SUPPORTED"


@dataclasses.dataclass
class MockDataclass:
    name: str
    count: int


class MockPydanticLike:
    def model_dump(self, mode: str = "python"):
        return {"mode": mode, "value": "ok"}


def test_canonical_json_dump_is_deterministic_for_different_key_order():
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}

    assert canonical_json_dump(left) == canonical_json_dump(right)


def test_canonicalize_value_converts_datetime_consistently():
    value = datetime(2026, 5, 16, 10, 30, tzinfo=timezone.utc)

    assert canonicalize_value(value) == "2026-05-16T10:30:00Z"
    assert normalize_datetime(value) == "2026-05-16T10:30:00Z"


def test_canonicalize_value_converts_path_to_posix_string():
    value = Path("foo") / "bar" / "baz.txt"

    assert canonicalize_value(value) == "foo/bar/baz.txt"


def test_normalize_path_string_converts_backslashes():
    assert normalize_path_string(r"foo\bar\baz.txt") == "foo/bar/baz.txt"


def test_canonicalize_value_converts_sets_to_sorted_lists():
    assert canonicalize_value({"b", "a", "c"}) == ["a", "b", "c"]


def test_canonicalize_value_preserves_list_order():
    assert canonicalize_value(["b", "a", "c"]) == ["b", "a", "c"]


def test_canonicalize_report_normalizes_newlines_and_trailing_whitespace():
    report = "Line 1  \r\nLine 2\t\n\n"

    assert canonicalize_report(report) == "Line 1\nLine 2"


def test_remove_nondeterministic_fields_removes_request_id():
    value = {"request_id": "req-1", "scenario": "stable"}

    assert remove_nondeterministic_fields(value, {"request_id"}) == {"scenario": "stable"}


def test_remove_nondeterministic_fields_removes_nested_timestamp():
    value = {"metadata": {"timestamp": "now", "domain": "general"}}

    assert remove_nondeterministic_fields(value, {"timestamp"}) == {
        "metadata": {"domain": "general"}
    }


def test_default_exclusions_do_not_remove_agent_outputs():
    value = {"agent_outputs": {"context": {"status": "SUPPORTED"}}, "request_id": "req-1"}

    result = canonicalize_value(value, exclusions=build_default_exclusions())

    assert "agent_outputs" in result
    assert "request_id" not in result


def test_default_exclusions_do_not_remove_final_report():
    value = {"final_report": "Important forecast text", "run_id": "run-1"}

    result = canonicalize_value(value, exclusions=build_default_exclusions())

    assert result == {"final_report": "Important forecast text"}


def test_assert_canonical_equal_passes_for_equivalent_objects():
    assert_canonical_equal({"b": 2, "a": 1}, {"a": 1, "b": 2})


def test_assert_canonical_equal_raises_useful_diff_for_different_objects():
    with pytest.raises(AssertionError, match="first differing path: \\$.a"):
        assert_canonical_equal({"a": 1}, {"a": 2}, label="state")


def test_protected_state_keys_includes_all_required_keys():
    required = {
        "agent_outputs",
        "signals",
        "horizon_forecasts",
        "fusion_result",
        "fusion_result_v2",
        "final_report",
        "executive_summary",
        "report_path",
        "governor_result",
        "critic_result",
        "quantifier_result",
        "deduped_evidence",
        "evidence_clusters",
        "independence_summary",
        "qualitative_forecast",
        "qualitative_forecast_label",
    }

    assert required.issubset(protected_state_keys())


def test_assert_protected_keys_unchanged_passes_when_unchanged():
    before = {"agent_outputs": {"a": 1}, "fusion_result_v2": {"p": 0.7}}
    after = {"agent_outputs": {"a": 1}, "fusion_result_v2": {"p": 0.7}}

    assert_protected_keys_unchanged(before, after)


def test_assert_protected_keys_unchanged_fails_when_agent_outputs_changes():
    before = {"agent_outputs": {"a": 1}}
    after = {"agent_outputs": {"a": 2}}

    with pytest.raises(AssertionError, match="Protected key changed: agent_outputs"):
        assert_protected_keys_unchanged(before, after)


def test_assert_protected_keys_unchanged_fails_when_fusion_result_v2_changes():
    before = {"fusion_result_v2": {"p50": 0.6}}
    after = {"fusion_result_v2": {"p50": 0.7}}

    with pytest.raises(AssertionError, match="Protected key changed: fusion_result_v2"):
        assert_protected_keys_unchanged(before, after)


def test_assert_protected_keys_unchanged_fails_when_executive_summary_changes():
    before = {"executive_summary": "old"}
    after = {"executive_summary": "new"}

    with pytest.raises(AssertionError, match="Protected key changed: executive_summary"):
        assert_protected_keys_unchanged(before, after)


def test_assert_protected_keys_unchanged_detects_added_protected_key():
    with pytest.raises(AssertionError, match="Protected key added: final_report"):
        assert_protected_keys_unchanged({}, {"final_report": "new"})


def test_assert_protected_keys_unchanged_detects_removed_protected_key():
    with pytest.raises(AssertionError, match="Protected key removed: final_report"):
        assert_protected_keys_unchanged({"final_report": "old"}, {})


def test_assert_no_gemini_keys_passes_without_gemini_keys():
    assert_no_gemini_keys({"scenario": "Assess risk"})


def test_assert_no_gemini_keys_fails_when_review_key_exists():
    with pytest.raises(AssertionError, match="gemini_assist_review"):
        assert_no_gemini_keys({"gemini_assist_review": {"run_id": "run-1"}})


def test_assert_no_agent_output_for_gemini_passes_without_gemini_output():
    assert_no_agent_output_for_gemini({"agent_outputs": {"context_interpreter": {}}})


def test_assert_no_agent_output_for_gemini_fails_when_gemini_output_exists():
    with pytest.raises(AssertionError, match="gemini_deep_research"):
        assert_no_agent_output_for_gemini(
            {"agent_outputs": {"gemini_deep_research": {"status": "SUPPORTED"}}}
        )


def test_capture_artifact_writes_deterministic_json_to_tmp_path(tmp_path):
    path = tmp_path / "baseline" / "state.json"

    capture_artifact(path, {"b": 2, "a": 1})

    assert path.read_text(encoding="utf-8") == '{\n  "a": 1,\n  "b": 2\n}'


def test_load_artifact_reads_same_canonical_content(tmp_path):
    path = tmp_path / "state.json"
    capture_artifact(path, {"request_id": "req-1", "scenario": "stable"}, {"request_id"})

    assert load_artifact(path) == {"scenario": "stable"}


def test_capture_report_artifact_writes_normalized_markdown(tmp_path):
    path = tmp_path / "report.md"

    capture_report_artifact(path, "# Title  \r\nBody\n\n")

    assert path.read_text(encoding="utf-8") == "# Title\nBody"


def test_load_report_artifact_reads_normalized_markdown(tmp_path):
    path = tmp_path / "report.md"
    path.write_text("# Title  \r\nBody\n\n", encoding="utf-8")

    assert load_report_artifact(path) == "# Title\nBody"


def test_secret_like_fields_are_redacted_during_canonicalization():
    value = {
        "api_key": "do-not-show",
        "bearer_token": "do-not-show",
        "nested": {"password": "do-not-show"},
        "scenario": "stable",
    }

    result = canonicalize_value(value)

    assert result["api_key"] == REDACTED
    assert result["bearer_token"] == REDACTED
    assert result["nested"]["password"] == REDACTED
    assert "do-not-show" not in canonical_json_dump(value)


def test_pydantic_like_objects_with_model_dump_are_handled():
    assert canonicalize_value(MockPydanticLike()) == {"mode": "json", "value": "ok"}


def test_dataclasses_are_handled():
    assert canonicalize_value(MockDataclass(name="x", count=2)) == {"count": 2, "name": "x"}


def test_enums_are_handled():
    assert canonicalize_value(MockEnum.SUPPORTED) == "SUPPORTED"


def test_dates_are_handled():
    assert canonicalize_value(date(2026, 5, 16)) == "2026-05-16"


def test_tuples_are_converted_to_lists():
    assert canonicalize_value(("b", "a")) == ["b", "a"]


def test_diff_canonical_reports_values_match_when_equal():
    assert diff_canonical({"a": 1}, {"a": 1}) == "Canonical diff: values match."


def test_diff_canonical_includes_changed_field_name_when_different():
    diff = diff_canonical({"a": 1}, {"a": 2}, label="state")

    assert "Canonical diff for state" in diff
    assert "$.a" in diff
    assert '"a": 1' in diff
    assert '"a": 2' in diff


def test_no_production_paths_are_used_in_artifact_helper_tests(tmp_path):
    path = tmp_path / "fixtures" / "state.json"

    capture_artifact(path, {"scenario": "stable"})

    assert str(path).startswith(str(tmp_path))
    assert "data/research" not in str(path)
