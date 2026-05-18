from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.integrations.gemini_deep_research.models import (  # noqa: E402
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
)
from app.integrations.gemini_deep_research.shadow_runner import GeminiShadowRunner  # noqa: E402
from fixtures.gemini_sidecar_fixtures import assert_sidecar_path  # noqa: E402
from gemini_non_interference_utils import canonical_json_dump  # noqa: E402


class FakeClient:
    def __init__(
        self,
        *,
        status: GeminiDeepResearchStatus = GeminiDeepResearchStatus.COMPLETED,
        report: str | None = None,
        enabled: bool = True,
        api_key: str | None = "fake-key",
    ) -> None:
        self.status = status
        self.report = report
        self.enabled = enabled
        self.api_key = api_key
        self.called = False

    def get_default_model(self) -> str:
        return "fake-gemini-model"

    def is_enabled(self) -> bool:
        return self.enabled

    async def run_research(
        self,
        prompt: str,
        model: str | None = None,
        timeout_seconds: int | None = None,
        mock: bool = False,
    ) -> GeminiDeepResearchResult:
        self.called = True
        return GeminiDeepResearchResult(
            run_id="fake-run",
            interaction_id="fake-interaction",
            model=model or "fake-gemini-model",
            mode="shadow",
            prompt=prompt,
            status=self.status,
            raw_report=self.report if self.report is not None else (
                "Reuters reported current maritime disruption "
                "https://www.reuters.com/world/middle-east/red-sea-shipping-example"
            ),
            raw_response={"mock": mock},
            error_message="fake timeout" if self.status == GeminiDeepResearchStatus.TIMEOUT else (
                "fake failure" if self.status == GeminiDeepResearchStatus.FAILED else None
            ),
            error_type="fake_error" if self.status != GeminiDeepResearchStatus.COMPLETED else None,
        )


def _seer_outputs() -> dict:
    return {
        "sources": [
            {
                "url": "https://www.reuters.com/world/middle-east/red-sea-shipping-example",
                "domain": "reuters.com",
                "source_type": "primary_reporting",
            }
        ],
        "evidence_items": [
            {
                "id": "seer-evidence-1",
                "url": "https://www.reuters.com/world/middle-east/red-sea-shipping-example",
                "canonical_url": "https://reuters.com/world/middle-east/red-sea-shipping-example",
                "domain": "reuters.com",
                "snippet": "Reuters reported current maritime disruption.",
                "content_hash": "a" * 64,
            }
        ],
        "claims": [
            {
                "id": "seer-claim-1",
                "text": "Reuters reported current maritime disruption.",
                "evidence_ids": ["seer-evidence-1"],
            }
        ],
        "agents_executed": ["context_interpreter"],
    }


def test_runner_completes_in_mock_mode(tmp_path):
    result = GeminiShadowRunner(client=FakeClient()).run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=True,
        output_dir=tmp_path,
    )

    assert result.status == "mock_completed"
    assert result.recommendation
    assert result.overall_risk


def test_runner_creates_expected_artifact_files(tmp_path):
    result = GeminiShadowRunner(client=FakeClient()).run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=True,
        output_dir=tmp_path,
    )

    run_dir = tmp_path / result.run_id
    assert (run_dir / "raw_result.json").exists()
    assert (run_dir / "evidence_pack.json").exists()
    assert (run_dir / "shadow_run.json").exists()
    assert (run_dir / "shadow_report.md").exists()
    assert (run_dir / "runner_result.json").exists()


def test_runner_no_save_creates_no_files(tmp_path):
    result = GeminiShadowRunner(client=FakeClient()).run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=True,
        output_dir=tmp_path,
        no_save=True,
    )

    assert result.status == "mock_completed"
    assert result.raw_result_path is None
    assert list(tmp_path.iterdir()) == []


def test_runner_loads_seer_outputs_from_json(tmp_path):
    path = tmp_path / "seer.json"
    path.write_text(json.dumps(_seer_outputs()), encoding="utf-8")

    loaded = GeminiShadowRunner(client=FakeClient()).load_seer_outputs(path)

    assert loaded["sources"][0]["domain"] == "reuters.com"


def test_runner_tolerates_missing_optional_seer_output_path(tmp_path):
    result = GeminiShadowRunner(client=FakeClient()).run(
        "Assess the Red Sea escalation risk.",
        mock=True,
        output_dir=tmp_path,
        no_save=True,
    )

    assert result.status == "mock_completed"
    assert any("No seer-output path" in warning for warning in result.warnings)


def test_runner_returns_structured_error_for_invalid_seer_output_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not valid json", encoding="utf-8")

    result = GeminiShadowRunner(client=FakeClient()).run(
        "Assess the Red Sea escalation risk.",
        seer_output_path=path,
        mock=True,
        output_dir=tmp_path,
    )

    assert result.status == "failed"
    assert "Invalid seer-output JSON" in result.error_message


def test_cli_requires_query_or_query_file(capsys):
    exit_code = GeminiShadowRunner(client=FakeClient()).run_cli(["--mock"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--query or --query-file is required" in captured.err


def test_cli_accepts_query_file(tmp_path):
    query_file = tmp_path / "query.txt"
    query_file.write_text("Assess the Red Sea escalation risk.", encoding="utf-8")

    exit_code = GeminiShadowRunner(client=FakeClient()).run_cli([
        "--query-file",
        str(query_file),
        "--mock",
        "--no-save",
    ])

    assert exit_code == 0


def test_cli_mock_returns_exit_code_zero():
    exit_code = GeminiShadowRunner(client=FakeClient()).run_cli([
        "--query",
        "Assess the Red Sea escalation risk.",
        "--mock",
        "--no-save",
    ])

    assert exit_code == 0


def test_cli_json_prints_valid_json_summary(capsys):
    exit_code = GeminiShadowRunner(client=FakeClient()).run_cli([
        "--query",
        "Assess the Red Sea escalation risk.",
        "--mock",
        "--no-save",
        "--json",
    ])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "mock_completed"
    assert "raw_report" not in payload


def test_cli_print_report_prints_markdown_report(capsys):
    exit_code = GeminiShadowRunner(client=FakeClient()).run_cli([
        "--query",
        "Assess the Red Sea escalation risk.",
        "--mock",
        "--no-save",
        "--print-report",
    ])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# Gemini Deep Research Shadow Comparison" in captured.out


def test_live_mode_disabled_returns_disabled_and_does_not_call_client():
    client = FakeClient(enabled=False, api_key=None)

    result = GeminiShadowRunner(client=client).run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=False,
        no_save=True,
    )

    assert result.status == "disabled"
    assert client.called is False


def test_timeout_result_returns_timeout_status(tmp_path):
    result = GeminiShadowRunner(
        client=FakeClient(status=GeminiDeepResearchStatus.TIMEOUT)
    ).run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=False,
        output_dir=tmp_path,
    )

    assert result.status == "timeout"
    assert result.error_message == "fake timeout"


def test_failed_result_returns_failed_status(tmp_path):
    result = GeminiShadowRunner(
        client=FakeClient(status=GeminiDeepResearchStatus.FAILED)
    ).run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=False,
        output_dir=tmp_path,
    )

    assert result.status == "failed"
    assert result.error_message == "fake failure"


def test_fail_on_risk_exits_code_two_when_threshold_is_breached(capsys):
    client = FakeClient(report="Broad narrative without citations or URLs.")

    exit_code = GeminiShadowRunner(client=client).run_cli([
        "--query",
        "Assess the Red Sea escalation risk.",
        "--no-save",
        "--fail-on-risk",
        "HIGH",
    ])

    capsys.readouterr()
    assert exit_code == 2


def test_runner_does_not_import_workflow_module():
    source = Path(
        "backend/app/integrations/gemini_deep_research/shadow_runner.py"
    ).read_text(encoding="utf-8")
    GeminiShadowRunner(client=FakeClient()).run(
        "Assess the Red Sea escalation risk.",
        mock=True,
        no_save=True,
    )

    assert "import workflow" not in source
    assert "from app.workflow" not in source
    assert "app.workflow" not in sys.modules


def test_runner_does_not_write_agent_outputs():
    source = Path(
        "backend/app/integrations/gemini_deep_research/shadow_runner.py"
    ).read_text(encoding="utf-8")

    assert ("agent" + "_outputs") not in source


def test_runner_does_not_create_forecast_artifact_models():
    source = Path(
        "backend/app/integrations/gemini_deep_research/shadow_runner.py"
    ).read_text(encoding="utf-8")

    for model_name in ("Signal", "HorizonForecast", "FusionResult"):
        assert f"{model_name}(" not in source


def test_mock_output_contains_no_final_forecast_probabilities(tmp_path):
    result = GeminiShadowRunner(client=FakeClient()).run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=True,
        output_dir=tmp_path,
    )
    raw_payload = json.loads((tmp_path / result.run_id / "raw_result.json").read_text(encoding="utf-8"))
    report = raw_payload["raw_report"].lower()

    assert "probability" not in report
    assert "chance" not in report
    assert "%" not in report


def test_malformed_or_incomplete_inputs_do_not_throw_unhandled_exception():
    result = GeminiShadowRunner(client=FakeClient()).run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=["not", "a", "dict"],  # type: ignore[arg-type]
        mock=True,
        no_save=True,
    )

    assert result.status == "mock_completed"
    assert result.warnings


def test_phase4la_saved_review_artifact_paths_remain_sidecar_local(tmp_path):
    result = GeminiShadowRunner(client=FakeClient()).run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=True,
        output_dir=tmp_path,
    )

    paths = GeminiShadowRunner(client=FakeClient()).save_outputs(result)

    assert paths
    for value in paths.values():
        assert value is not None
        assert_sidecar_path(value, tmp_path)
        parts = Path(value).parts
        assert "agent_outputs" not in parts
        assert "forecast_outputs" not in parts
        assert "reports" not in parts


def test_phase4la_review_artifact_serialization_is_deterministic(tmp_path):
    runner = GeminiShadowRunner(client=FakeClient())
    first = runner.run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=True,
        output_dir=tmp_path / "first",
    )
    second = runner.run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=True,
        output_dir=tmp_path / "second",
    )

    first_payload = json.loads(
        Path(first.metadata["runner_result_path"]).read_text(encoding="utf-8")
    )
    second_payload = json.loads(
        Path(second.metadata["runner_result_path"]).read_text(encoding="utf-8")
    )
    path_exclusions = {
        "raw_result_path",
        "evidence_pack_path",
        "shadow_run_json_path",
        "shadow_report_path",
        "runner_result_path",
    }

    assert canonical_json_dump(first_payload, exclusions=path_exclusions) == canonical_json_dump(
        second_payload,
        exclusions=path_exclusions,
    )


def test_phase4la_shadow_runner_does_not_mutate_production_like_state(tmp_path):
    state = {
        "agent_outputs": {"context_interpreter": {"summary": "existing"}},
        "signals": [{"id": "sig-1"}],
        "horizon_forecasts": [{"id": "horizon-1"}],
        "fusion_result": {"status": "existing"},
        "final_report": "Existing report",
    }
    before = canonical_json_dump(state)

    GeminiShadowRunner(client=FakeClient()).run(
        "Assess the Red Sea escalation risk.",
        seer_outputs=_seer_outputs(),
        mock=True,
        output_dir=tmp_path,
    )

    assert canonical_json_dump(state) == before
