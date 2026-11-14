"""CLI entrypoint for FHIRlance."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from fhirlance.dataset import validate_dataset

_MAX_DISPLAYED_ISSUES = 20
_CLI_USAGE_EXIT_CODE = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fhirlance",
        description="High-performance FHIR R4 structural and IG profile validator.",
    )
    parser.add_argument("target", type=Path, help="FHIR JSON/NDJSON file or directory to validate")
    parser.add_argument(
        "--no-canadian",
        action="store_true",
        help="Disable Canadian profile presence and JHN/address checks",
    )
    parser.add_argument(
        "--profile",
        action="append",
        default=None,
        help="Additional StructureDefinition profile URL to validate against (repeatable)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Validate multiple files across worker processes",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print full JSON report",
    )
    return parser


def _format_text_lines(report: dict[str, Any], elapsed: float) -> list[str]:
    lines = [
        f"Validated {report['total_resources']} resource(s) in {elapsed:.4f}s | "
        f"valid={report['valid_resources']} invalid={report['invalid_resources']} "
        f"({report['compliance_rate']:.2f}%)"
    ]
    lines.extend(f"  - {item}" for item in report["issues"][:_MAX_DISPLAYED_ISSUES])
    return lines


def main(argv: list[str] | None = None) -> int:
    """Run the FHIRlance CLI and return a POSIX exit status."""
    args = _build_parser().parse_args(argv)

    t0 = time.perf_counter()
    try:
        report = validate_dataset(
            args.target,
            parallel=args.parallel,
            require_canadian_profile=not args.no_canadian,
            profile_urls=args.profile,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return _CLI_USAGE_EXIT_CODE

    elapsed = time.perf_counter() - t0
    report["elapsed_seconds"] = round(elapsed, 4)

    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        for line in _format_text_lines(report, elapsed):
            print(line)

    return 0 if report["invalid_resources"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
