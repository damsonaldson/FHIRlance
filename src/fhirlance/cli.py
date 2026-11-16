"""CLI entrypoint for FHIRlance."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

from fhirlance.dataset import validate_dataset
from fhirlance.formatters import SUPPORTED_OUTPUT_FORMATS, format_dataset_report

_MAX_DISPLAYED_ISSUES = 20
_CLI_USAGE_EXIT_CODE = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fhirlance",
        description="High-performance FHIR R4 structural and IG profile validator.",
    )
    parser.add_argument("target", type=Path, help="FHIR JSON/NDJSON file or directory to validate")
    parser.add_argument(
        "--profile",
        action="append",
        default=None,
        help="Additional StructureDefinition profile URL to validate against (repeatable)",
    )
    parser.add_argument(
        "-ig",
        "--ig",
        action="append",
        default=None,
        dest="ig_sources",
        help=(
            "FHIR IG package (.tgz, directory, StructureDefinition JSON, "
            "or package#version) to load at runtime (repeatable)"
        ),
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Validate multiple files across worker processes",
    )
    parser.add_argument(
        "-tx",
        "--tx",
        "-term",
        "--term",
        dest="tx",
        default="local",
        help="Terminology validation mode: local (default), off, or remote TX server URL",
    )
    parser.add_argument(
        "--strict-extensible",
        action="store_true",
        help="Treat extensible binding violations with unknown code systems as errors",
    )
    parser.add_argument(
        "--best-practice",
        action="store_true",
        help=(
            "Emit best-practice warnings "
            "(dom-6 narrative, Observation.performer, preferred bindings)"
        ),
    )
    parser.add_argument(
        "--format",
        choices=SUPPORTED_OUTPUT_FORMATS,
        default=None,
        dest="output_format",
        help="Output format: text (default), json, operation-outcome, sarif, junit",
    )
    parser.add_argument(
        "--operation-outcome",
        action="store_true",
        dest="as_operation_outcome",
        help=(
            "Emit standard FHIR R4 OperationOutcome JSON (shorthand for --format operation-outcome)"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print full JSON report (shorthand for --format json)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        dest="output_path",
        help="Write output to file instead of stdout",
    )
    return parser


def _format_text_lines(report: dict[str, Any], elapsed: float) -> list[str]:
    lines = [
        f"Validated {report['total_resources']} resource(s) in {elapsed:.4f}s | "
        f"valid={report['valid_resources']} invalid={report['invalid_resources']} "
        f"({report['compliance_rate']:.2f}%)"
    ]
    lines.extend(f"  - {item}" for item in report.get("issues", [])[:_MAX_DISPLAYED_ISSUES])
    return lines


def main(argv: list[str] | None = None) -> int:
    """Run the FHIRlance CLI and return a POSIX exit status."""
    args = _build_parser().parse_args(argv)

    t0 = time.perf_counter()
    try:
        report = validate_dataset(
            args.target,
            parallel=args.parallel,
            profile_urls=args.profile,
            ig_sources=args.ig_sources,
            tx=args.tx,
            strict_extensible=args.strict_extensible,
            best_practice=args.best_practice,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return _CLI_USAGE_EXIT_CODE

    elapsed = time.perf_counter() - t0
    report["elapsed_seconds"] = round(elapsed, 4)

    if args.output_format:
        effective_format = args.output_format
    elif args.as_operation_outcome:
        effective_format = "operation-outcome"
    elif args.as_json:
        effective_format = "json"
    else:
        effective_format = "text"

    formatted = format_dataset_report(
        report,
        effective_format,
        max_displayed_issues=_MAX_DISPLAYED_ISSUES,
    )

    if args.output_path:
        args.output_path.write_text(formatted, encoding="utf-8")
    else:
        print(formatted)

    return 0 if (report["invalid_resources"] == 0 and not report["issues"]) else 1


if __name__ == "__main__":
    sys.exit(main())
