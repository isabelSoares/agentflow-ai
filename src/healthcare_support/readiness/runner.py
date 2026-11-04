"""Subprocess runner with per-criterion timeout.

Runs gate commands, captures summarized output only (raw output may
contain secrets and MUST NOT be forwarded into the report), and maps
timeouts / missing tools to UNABLE_TO_VERIFY (fail-closed).
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

DEFAULT_TIMEOUT_SECONDS = 240


@dataclass(frozen=True)
class RunOutcome:
    """Result of running one gate command."""

    ok: bool
    unable_to_verify: bool
    summary: str


def _summarize(stdout: str, stderr: str, max_lines: int = 5) -> str:
    """Keep only the last few lines of output; never forward raw dumps."""
    text = (stderr.strip() or stdout.strip()).splitlines()
    tail = text[-max_lines:] if text else ["(no output)"]
    return " | ".join(line.strip() for line in tail if line.strip())


def run_command(
    argv: list[str],
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    cwd: str | None = None,
) -> RunOutcome:
    """Run a command and classify the outcome.

    Returns ``unable_to_verify=True`` when the tool is missing, the
    command times out, or it cannot be spawned — never treated as pass.
    """
    if shutil.which(argv[0]) is None and "/" not in argv[0]:
        return RunOutcome(
            ok=False,
            unable_to_verify=True,
            summary=f"tool {argv[0]!r} not found on PATH",
        )
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return RunOutcome(
            ok=False,
            unable_to_verify=True,
            summary=f"timed out after {timeout}s",
        )
    except OSError as exc:
        return RunOutcome(ok=False, unable_to_verify=True, summary=f"could not run: {exc}")
    summary = _summarize(proc.stdout, proc.stderr)
    return RunOutcome(ok=proc.returncode == 0, unable_to_verify=False, summary=summary)
