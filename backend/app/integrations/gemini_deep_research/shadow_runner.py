"""Workflow-independent Phase 3B runner for Gemini Deep Research shadow checks."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.integrations.gemini_deep_research.client import GeminiDeepResearchClient
from app.integrations.gemini_deep_research.models import (
    GeminiDeepResearchResult,
    GeminiDeepResearchStatus,
    GeminiEvidencePack,
    GeminiShadowRun,
    GeminiShadowRunnerResult,
)
from app.integrations.gemini_deep_research.normalizer import GeminiEvidenceNormalizer
from app.integrations.gemini_deep_research.prompts import build_deep_research_prompt
from app.integrations.gemini_deep_research.shadow_compare import GeminiShadowComparator
from app.integrations.gemini_deep_research.storage import (
    save_evidence_pack_artifact,
    save_raw_result_artifact,
    save_runner_result_artifact,
    save_shadow_report_artifact,
    save_shadow_run_artifact,
)


RISK_RANK = {"low": 0, "unknown": 1, "medium": 2, "high": 3, "critical": 4}


class GeminiShadowRunner:
    """Standalone diagnostic runner for the Gemini shadow pipeline."""

    def __init__(
        self,
        *,
        client: Optional[GeminiDeepResearchClient] = None,
        normalizer: Optional[GeminiEvidenceNormalizer] = None,
        comparator: Optional[GeminiShadowComparator] = None,
    ) -> None:
        self.client = client or GeminiDeepResearchClient()
        self.normalizer = normalizer or GeminiEvidenceNormalizer()
        self.comparator = comparator or GeminiShadowComparator()
        self.warnings: List[str] = []
        self._last_load_error: Optional[str] = None
        self._last_markdown_report: Optional[str] = None

    def run(
        self,
        query: str,
        seer_output_path: str | Path | None = None,
        seer_outputs: Optional[Dict[str, Any]] = None,
        mock: bool = False,
        model: Optional[str] = None,
        output_dir: str | Path | None = None,
        timeout_seconds: Optional[int] = None,
        no_save: bool = False,
    ) -> GeminiShadowRunnerResult:
        """Run the standalone shadow pipeline without touching production workflow state."""
        self.warnings = []
        self._last_load_error = None
        self._last_markdown_report = None
        clean_query = (query or "").strip()
        if not clean_query:
            return self._failure_result(
                status="failed",
                query=query,
                mock=mock,
                model=model,
                error_message="A query is required.",
            )

        resolved_seer_outputs = self._resolve_seer_outputs(seer_output_path, seer_outputs)
        if self._last_load_error:
            return self._failure_result(
                status="failed",
                query=clean_query,
                mock=mock,
                model=model,
                error_message=self._last_load_error,
            )

        selected_model = model or self.client.get_default_model()
        if not mock and not self._live_mode_enabled():
            return self._failure_result(
                status="disabled",
                query=clean_query,
                mock=False,
                model=selected_model,
                error_message=(
                    "Live Gemini Deep Research is disabled. Set SEER_USE_GEMINI_DEEP_RESEARCH=1 "
                    "and configure GEMINI_API_KEY, or rerun with --mock."
                ),
            )

        try:
            raw_result = self._run_research(
                clean_query,
                model=selected_model,
                timeout_seconds=timeout_seconds,
                mock=mock,
            )
            if mock:
                raw_result = self._phase3b_mock_result(clean_query, selected_model, raw_result)

            pack = self.normalizer.normalize_result(
                raw_result,
                original_question=clean_query,
                improved_prompt=build_deep_research_prompt(clean_query),
            )
            shadow_run = self.comparator.compare(
                pack,
                resolved_seer_outputs,
                query=clean_query,
                run_id=raw_result.run_id,
            )
            markdown_report = self.comparator.render_markdown_report(shadow_run)
            self._last_markdown_report = markdown_report

            runner_status = self._runner_status(raw_result, mock)
            runner_result = GeminiShadowRunnerResult(
                run_id=raw_result.run_id,
                status=runner_status,
                query=clean_query,
                mock=mock,
                model=raw_result.model,
                recommendation=shadow_run.recommendation,
                overall_risk=shadow_run.risk_assessment.overall_risk,
                warnings=self._combined_warnings(pack, shadow_run),
                error_message=raw_result.error_message,
                metadata={
                    "gemini_interaction_id": raw_result.interaction_id,
                    "seer_output_path": str(seer_output_path) if seer_output_path else None,
                    "saved": not no_save,
                },
            )
            if not no_save:
                runner_result = self._save_artifacts(
                    raw_result=raw_result,
                    pack=pack,
                    shadow_run=shadow_run,
                    runner_result=runner_result,
                    output_dir=output_dir,
                )
            return runner_result
        except Exception as exc:  # noqa: BLE001 - CLI diagnostics must fail structurally
            return self._failure_result(
                status="failed",
                query=clean_query,
                mock=mock,
                model=selected_model,
                error_message=f"Gemini shadow runner failed closed: {exc.__class__.__name__}",
            )

    def load_seer_outputs(self, path: str | Path) -> Dict[str, Any]:
        """Load flexible saved TheSeer JSON output for local comparison."""
        self._last_load_error = None
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self._last_load_error = f"Invalid seer-output JSON: {exc.msg}"
            return {}
        except OSError as exc:
            self._last_load_error = f"Could not read seer-output JSON: {exc.__class__.__name__}"
            return {}

        if isinstance(payload, dict):
            return payload
        self.warnings.append("Loaded seer-output JSON was not an object; using empty comparison input.")
        return self.build_empty_seer_outputs()

    def build_empty_seer_outputs(self) -> Dict[str, Any]:
        """Return an empty but comparator-compatible TheSeer output shape."""
        return {
            "sources": [],
            "evidence_items": [],
            "claims": [],
            "agents_executed": [],
            "warnings": ["No saved TheSeer output was provided for shadow comparison."],
        }

    def save_outputs(self, result: GeminiShadowRunnerResult) -> Dict[str, Optional[str]]:
        """Return saved output paths from a runner result."""
        return {
            "raw_result_path": result.raw_result_path,
            "evidence_pack_path": result.evidence_pack_path,
            "shadow_run_json_path": result.shadow_run_json_path,
            "shadow_report_path": result.shadow_report_path,
        }

    def run_cli(self, argv: Optional[List[str]] = None) -> int:
        """CLI entrypoint for standalone Gemini shadow runs."""
        parser = self._build_parser()
        args = parser.parse_args(argv)

        query = args.query
        if args.query_file:
            try:
                query = Path(args.query_file).read_text(encoding="utf-8").strip()
            except OSError as exc:
                print(f"error: could not read query file: {exc.__class__.__name__}", file=sys.stderr)
                return 1

        if not query:
            print("error: --query or --query-file is required", file=sys.stderr)
            return 1

        result = self.run(
            query=query,
            seer_output_path=args.seer_output,
            mock=args.mock,
            model=args.model,
            output_dir=args.output_dir,
            timeout_seconds=args.timeout_seconds,
            no_save=args.no_save,
        )

        if args.print_report and self._last_markdown_report:
            print(self._last_markdown_report)

        if args.json:
            print(result.model_dump_json(indent=2))
        else:
            print(self._summary_text(result))

        risk_exit = self._risk_exit_code(result, args.fail_on_risk)
        if risk_exit:
            return risk_exit
        return self._status_exit_code(result.status)

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Run a workflow-independent Gemini Deep Research shadow comparison.",
        )
        parser.add_argument("--query", help="Research question to run.")
        parser.add_argument("--query-file", help="Path to a text file containing the query.")
        parser.add_argument("--seer-output", help="Optional saved TheSeer output JSON for comparison.")
        parser.add_argument("--output-dir", help="Optional output directory for shadow artifacts.")
        parser.add_argument("--model", help="Optional Gemini model override.")
        parser.add_argument("--timeout-seconds", type=int, help="Optional Gemini timeout override.")
        parser.add_argument("--mock", action="store_true", help="Run without calling Gemini.")
        parser.add_argument("--no-save", action="store_true", help="Run without writing artifacts.")
        parser.add_argument("--print-report", action="store_true", help="Print the markdown comparison report.")
        parser.add_argument("--json", action="store_true", help="Print a JSON runner summary.")
        parser.add_argument(
            "--fail-on-risk",
            choices=["HIGH", "CRITICAL"],
            help="Exit nonzero if overall risk is at or above this threshold.",
        )
        return parser

    def _resolve_seer_outputs(
        self,
        seer_output_path: str | Path | None,
        seer_outputs: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if seer_outputs is not None:
            if isinstance(seer_outputs, dict):
                return seer_outputs
            self.warnings.append("Direct seer_outputs input was not a dictionary; using empty comparison input.")
            return self.build_empty_seer_outputs()
        if seer_output_path:
            return self.load_seer_outputs(seer_output_path)
        self.warnings.append("No seer-output path was provided; using empty comparison input.")
        return self.build_empty_seer_outputs()

    def _live_mode_enabled(self) -> bool:
        return bool(self.client.is_enabled() and getattr(self.client, "api_key", None))

    def _run_research(
        self,
        query: str,
        *,
        model: Optional[str],
        timeout_seconds: Optional[int],
        mock: bool,
    ) -> GeminiDeepResearchResult:
        return asyncio.run(
            self.client.run_research(
                query,
                model=model,
                timeout_seconds=timeout_seconds,
                mock=mock,
            )
        )

    def _phase3b_mock_result(
        self,
        query: str,
        model: str,
        client_result: GeminiDeepResearchResult,
    ) -> GeminiDeepResearchResult:
        digest = hashlib.sha256(f"{query}:{model}".encode("utf-8")).hexdigest()[:12]
        run_id = f"mock-shadow-{digest}"
        raw_report = (
            "# Mock Gemini Deep Research Shadow Report\n\n"
            "## Sources\n"
            "- Reuters Red Sea shipping update: https://www.reuters.com/world/middle-east/red-sea-shipping-example\n"
            "- RAND regional deterrence assessment: https://www.rand.org/pubs/research_reports/RRA0000.html\n\n"
            "## Evidence-Backed Findings\n"
            "- Reuters reported current shipping disruptions around the Red Sea remain operationally relevant "
            "https://www.reuters.com/world/middle-east/red-sea-shipping-example\n"
            "- RAND assessed that regional deterrence risks require continued monitoring over coming months "
            "https://www.rand.org/pubs/research_reports/RRA0000.html\n\n"
            "## Contradictions\n"
            "- Mock mode found no resolved contradiction in the provided local inputs.\n\n"
            "## Uncertainty\n"
            "- Mock mode does not access live sources and cannot verify publication freshness.\n"
        )
        return client_result.model_copy(update={
            "run_id": run_id,
            "interaction_id": f"mock-{digest}",
            "model": model,
            "mode": "shadow",
            "prompt": build_deep_research_prompt(query),
            "status": GeminiDeepResearchStatus.COMPLETED,
            "raw_report": raw_report,
            "raw_response": {
                "id": "mock_interaction",
                "status": "completed",
                "mock": True,
                "phase": "phase_3b_shadow_runner",
            },
            "citations": [
                {
                    "title": "Reuters Red Sea shipping update",
                    "url": "https://www.reuters.com/world/middle-east/red-sea-shipping-example",
                },
                {
                    "title": "RAND regional deterrence assessment",
                    "url": "https://www.rand.org/pubs/research_reports/RRA0000.html",
                },
            ],
            "metadata": {
                **(client_result.metadata or {}),
                "mock": True,
                "phase": "phase_3b_shadow_runner",
            },
        })

    def _runner_status(self, raw_result: GeminiDeepResearchResult, mock: bool) -> str:
        if mock and raw_result.status == GeminiDeepResearchStatus.COMPLETED:
            return "mock_completed"
        if raw_result.status == GeminiDeepResearchStatus.COMPLETED:
            return "completed"
        if raw_result.status == GeminiDeepResearchStatus.TIMEOUT:
            return "timeout"
        if raw_result.status == GeminiDeepResearchStatus.DISABLED:
            return "disabled"
        return "failed"

    def _combined_warnings(
        self,
        pack: GeminiEvidencePack,
        shadow_run: GeminiShadowRun,
    ) -> List[str]:
        warnings = list(self.warnings)
        warnings.extend(f"{warning.code}: {warning.message}" for warning in pack.normalizer_warnings)
        warnings.extend(shadow_run.warnings)
        return list(dict.fromkeys(warnings))

    def _save_artifacts(
        self,
        *,
        raw_result: GeminiDeepResearchResult,
        pack: GeminiEvidencePack,
        shadow_run: GeminiShadowRun,
        runner_result: GeminiShadowRunnerResult,
        output_dir: str | Path | None,
    ) -> GeminiShadowRunnerResult:
        raw_path = save_raw_result_artifact(raw_result, runner_result.run_id, output_dir)
        pack_path = save_evidence_pack_artifact(pack, runner_result.run_id, output_dir)
        shadow_json_path = save_shadow_run_artifact(shadow_run, output_dir)
        shadow_report_path = save_shadow_report_artifact(shadow_run, output_dir)
        updated = runner_result.model_copy(update={
            "raw_result_path": str(raw_path),
            "evidence_pack_path": str(pack_path),
            "shadow_run_json_path": str(shadow_json_path),
            "shadow_report_path": str(shadow_report_path),
        })
        runner_result_path = save_runner_result_artifact(updated, runner_result.run_id, output_dir)
        return updated.model_copy(update={
            "metadata": {
                **updated.metadata,
                "runner_result_path": str(runner_result_path),
            },
        })

    def _failure_result(
        self,
        *,
        status: str,
        query: Optional[str],
        mock: bool,
        model: Optional[str],
        error_message: str,
    ) -> GeminiShadowRunnerResult:
        return GeminiShadowRunnerResult(
            status=status,  # type: ignore[arg-type]
            query=query,
            mock=mock,
            model=model,
            warnings=list(self.warnings),
            error_message=error_message,
        )

    def _summary_text(self, result: GeminiShadowRunnerResult) -> str:
        lines = [
            f"Gemini shadow runner status: {result.status}",
            f"run_id: {result.run_id}",
            f"recommendation: {result.recommendation or 'none'}",
            f"overall_risk: {result.overall_risk or 'unknown'}",
        ]
        for label, path in (
            ("raw_result", result.raw_result_path),
            ("evidence_pack", result.evidence_pack_path),
            ("shadow_run", result.shadow_run_json_path),
            ("shadow_report", result.shadow_report_path),
        ):
            if path:
                lines.append(f"{label}: {path}")
        if result.error_message:
            lines.append(f"error: {result.error_message}")
        return "\n".join(lines)

    def _risk_exit_code(
        self,
        result: GeminiShadowRunnerResult,
        threshold: Optional[str],
    ) -> int:
        if not threshold or not result.overall_risk:
            return 0
        return 2 if RISK_RANK.get(result.overall_risk.lower(), 0) >= RISK_RANK[threshold.lower()] else 0

    def _status_exit_code(self, status: str) -> int:
        if status in {"completed", "mock_completed"}:
            return 0
        if status == "disabled":
            return 3
        if status == "timeout":
            return 4
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """Module entrypoint for `python -m app.integrations...shadow_runner`."""
    return GeminiShadowRunner().run_cli(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
