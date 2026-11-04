"""CLI entry point for the launch readiness check.

Contract: contracts/cli-schema.md — flags --json and --timeout SECONDS;
exit 0 = ready, 1 = not ready, 2 = check error.
"""

from __future__ import annotations

import argparse
import logging
import sys

from healthcare_support.readiness.checks import run_all_checks
from healthcare_support.readiness.models import ReadinessReport
from healthcare_support.readiness.report import render_json, render_text
from healthcare_support.readiness.runner import DEFAULT_TIMEOUT_SECONDS

logger = logging.getLogger("healthcare_support.readiness")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="check_launch_readiness",
        description="Verify whether the project is ready to launch (fail-closed).",
    )
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="per-criterion timeout in seconds (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if args.timeout <= 0:
        print("error: --timeout must be positive", file=sys.stderr)
        return 2
    try:
        results = run_all_checks(timeout=args.timeout)
        report = ReadinessReport(results=results)
    except Exception as exc:
        logger.error("readiness check failed to run: %s", type(exc).__name__)
        print(f"error: readiness check could not complete: {type(exc).__name__}", file=sys.stderr)
        return 2
    for result in report.results:
        logger.info(
            "readiness criterion %s=%s category=%s",
            result.name,
            result.status.value,
            result.category,
        )
    output = render_json(report) if args.json else render_text(report)
    print(output)
    return 0 if report.verdict == "ready" else 1
