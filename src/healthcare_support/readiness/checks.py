"""Criterion evaluators for the launch readiness check.

Every evaluator is deterministic (constitution Principle II) and returns
a CriterionResult whose details/remediation never contain secret values
or PII (Principle I). Gate commands mirror .github/workflows/ci.yml so
local and CI verdicts are identical.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from healthcare_support.readiness.models import CriterionResult, CriterionStatus
from healthcare_support.readiness.runner import DEFAULT_TIMEOUT_SECONDS, run_command

REPO_ROOT = Path(__file__).resolve().parents[3]

REMEDIATION: dict[str, str] = {
    "offline-tests": (
        'Run `uv run pytest -m "not live_llm and not live_speech"` and fix the failing tests.'
    ),
    "frontend-tests": "Run `npm test` in frontend/ and fix the failing tests.",
    "lint": "Run `uv run ruff check src tests` and fix the reported issues.",
    "format": "Run `uv run ruff format src tests` and commit the result.",
    "type-check": "Run `uv run mypy src` and fix the reported type errors.",
    "coverage-gate": (
        "Coverage is below the 80% gate; add tests or run "
        "`uv run pytest --cov=src/healthcare_support --cov-report=term-missing` to see gaps."
    ),
    "frontend-build": "Run `npm run build` in frontend/ and fix the build errors.",
    "deployment-config": (
        "Ensure the Dockerfile and .github/workflows/ci.yml exist and that no .env "
        "file is committed; set required environment variables in the deployment environment."
    ),
    "dependency-audit": (
        "Run `uv run pip-audit --strict` on the exported locked requirements and upgrade "
        "vulnerable dependencies in uv.lock."
    ),
    "committed-secrets": (
        "Remove the detected credential pattern from the listed tracked file(s), rotate the "
        "exposed credential, and keep secrets in environment variables or a secrets manager."
    ),
    "no-pii-in-boundary": (
        "Ensure API response models stay sanitized (extra=forbid, no PII/secret fields) and "
        "that no log statement includes secret answers or credentials."
    ),
}

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("openai-style-key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    (
        "generic-credential-assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*"
            r"[\"'](?P<value>[A-Za-z0-9_\-./+=]{12,})[\"']"
        ),
    ),
]

# Obviously fake placeholder values used in tests/docs must not be flagged.
_FAKE_VALUE_MARKERS = (
    "test",
    "invalid",
    "example",
    "dummy",
    "placeholder",
    "changeme",
    "fake",
    "redacted",
    "xxxx",
)

_FORBIDDEN_RESPONSE_FIELDS = {"secret_answer", "secret", "password", "phone", "date_of_birth"}
_LOG_CALL = re.compile(r"\.(debug|info|warning|error|critical|exception)\(")


def _result(
    name: str,
    category: str,
    *,
    ok: bool,
    unable_to_verify: bool = False,
    details: str,
) -> CriterionResult:
    if unable_to_verify:
        status = CriterionStatus.UNABLE_TO_VERIFY
    elif ok:
        status = CriterionStatus.PASS
    else:
        status = CriterionStatus.FAIL
    return CriterionResult(
        name=name,
        category=category,
        status=status,
        details=details,
        remediation="" if status == CriterionStatus.PASS else REMEDIATION[name],
    )


def _tool(name: str, *args: str) -> list[str]:
    """Prefer the locked uv environment; fall back to PATH lookup."""
    if shutil.which("uv") is not None:
        return ["uv", "run", name, *args]
    return [name, *args]


def check_offline_tests(timeout: int) -> CriterionResult:
    outcome = run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "not live_llm and not live_speech",
            "--cov=src/healthcare_support",
            "--cov-branch",
            "--cov-fail-under=80",
            "-q",
        ],
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )
    return _result(
        "offline-tests",
        "tests",
        ok=outcome.ok,
        unable_to_verify=outcome.unable_to_verify,
        details="offline test suite passed" if outcome.ok else outcome.summary,
    )


def check_coverage_gate(timeout: int) -> CriterionResult:
    """Coverage gate is enforced by the offline test run's --cov-fail-under.

    Evaluated separately so a coverage-only failure is reported distinctly:
    re-run coverage reporting and parse the total percentage.
    """
    outcome = run_command(
        [
            sys.executable,
            "-m",
            "coverage",
            "report",
            "--fail-under=80",
        ],
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )
    return _result(
        "coverage-gate",
        "quality-gates",
        ok=outcome.ok,
        unable_to_verify=outcome.unable_to_verify,
        details="coverage >= 80%" if outcome.ok else outcome.summary,
    )


def _simple_gate(
    name: str,
    category: str,
    argv: list[str],
    timeout: int,
    *,
    cwd: Path | None = None,
) -> CriterionResult:
    outcome = run_command(argv, timeout=timeout, cwd=str(cwd) if cwd else str(REPO_ROOT))
    return _result(
        name,
        category,
        ok=outcome.ok,
        unable_to_verify=outcome.unable_to_verify,
        details=f"{name} passed" if outcome.ok else outcome.summary,
    )


def check_lint(timeout: int) -> CriterionResult:
    return _simple_gate("lint", "quality-gates", _tool("ruff", "check", "src", "tests"), timeout)


def check_format(timeout: int) -> CriterionResult:
    return _simple_gate(
        "format", "quality-gates", _tool("ruff", "format", "--check", "src", "tests"), timeout
    )


def check_type_check(timeout: int) -> CriterionResult:
    return _simple_gate(
        "type-check", "quality-gates", [sys.executable, "-m", "mypy", "src"], timeout
    )


def _frontend_present() -> bool:
    return (REPO_ROOT / "frontend" / "package.json").is_file()


def check_frontend_tests(timeout: int) -> CriterionResult:
    if not _frontend_present():
        return _result(
            "frontend-tests",
            "tests",
            ok=False,
            unable_to_verify=True,
            details="frontend/ directory not present",
        )
    return _simple_gate(
        "frontend-tests", "tests", ["npm", "test"], timeout, cwd=REPO_ROOT / "frontend"
    )


def check_frontend_build(timeout: int) -> CriterionResult:
    if not _frontend_present():
        return _result(
            "frontend-build",
            "quality-gates",
            ok=False,
            unable_to_verify=True,
            details="frontend/ directory not present",
        )
    return _simple_gate(
        "frontend-build",
        "quality-gates",
        ["npm", "run", "build"],
        timeout,
        cwd=REPO_ROOT / "frontend",
    )


def _tracked_files() -> list[str] | None:
    proc = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    if proc.returncode != 0:
        return None
    return [line for line in proc.stdout.splitlines() if line.strip()]


def check_deployment_config(timeout: int) -> CriterionResult:
    """Deployment artifacts present; no .env committed; env names reported only."""
    problems: list[str] = []
    for artifact in ("Dockerfile", ".github/workflows/ci.yml"):
        if not (REPO_ROOT / artifact).exists():
            problems.append(f"missing {artifact}")
    tracked = _tracked_files()
    if tracked is None:
        return _result(
            "deployment-config",
            "deployment",
            ok=False,
            unable_to_verify=True,
            details="could not list tracked files (git unavailable)",
        )
    env_committed = [
        f
        for f in tracked
        if (name := os.path.basename(f)) == ".env"
        or (name.startswith(".env.") and not name.endswith(".example"))
    ]
    if env_committed:
        problems.append(f"committed env file(s): {', '.join(env_committed)}")
    llm_env_names = ["GROQ_API_KEY"]
    present = [n for n in llm_env_names if os.environ.get(n)]
    details = (
        "deployment artifacts present; required env names set: "
        + (", ".join(present) if present else "none")
        if not problems
        else "; ".join(problems)
    )
    return _result(
        "deployment-config",
        "deployment",
        ok=not problems,
        details=details,
    )


def check_dependency_audit(timeout: int) -> CriterionResult:
    if shutil.which("uv") is None:
        return _result(
            "dependency-audit",
            "security",
            ok=False,
            unable_to_verify=True,
            details="uv not found on PATH",
        )
    with tempfile.NamedTemporaryFile("w", suffix="-requirements.txt", delete=False) as tmp:
        req_path = tmp.name
    export = run_command(
        [
            "uv",
            "export",
            "--locked",
            "--format",
            "requirements.txt",
            "--no-editable",
            "--no-emit-project",
            "--output-file",
            req_path,
        ],
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )
    if export.unable_to_verify or not export.ok:
        return _result(
            "dependency-audit",
            "security",
            ok=False,
            unable_to_verify=export.unable_to_verify,
            details=export.summary,
        )
    audit = run_command(
        [sys.executable, "-m", "pip_audit", "--strict", "-r", req_path],
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )
    return _result(
        "dependency-audit",
        "security",
        ok=audit.ok,
        unable_to_verify=audit.unable_to_verify,
        details="no known vulnerabilities in locked dependencies" if audit.ok else audit.summary,
    )


def scan_for_committed_secrets() -> tuple[bool, str]:
    """Scan tracked files for credential patterns.

    Returns (ok, details) where details names only file paths and pattern
    names — never the matched value.
    """
    tracked = _tracked_files()
    if tracked is None:
        return False, "could not list tracked files (git unavailable)"
    findings: list[str] = []
    for rel in tracked:
        path = REPO_ROOT / rel
        if not path.is_file() or path.stat().st_size > 1_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern_name, pattern in _SECRET_PATTERNS:
            for match in pattern.finditer(content):
                value = (match.groupdict().get("value") or match.group(0)).lower()
                if any(marker in value for marker in _FAKE_VALUE_MARKERS):
                    continue
                findings.append(f"{rel} ({pattern_name})")
                break
    if findings:
        return False, "potential committed secrets in: " + "; ".join(sorted(set(findings)))
    return True, "no credential patterns found in tracked files"


def check_committed_secrets(timeout: int) -> CriterionResult:
    ok, details = scan_for_committed_secrets()
    return _result("committed-secrets", "security", ok=ok, details=details)


def _load_schemas() -> Any:
    """Import the API schemas lazily so this module stays API-independent."""
    from healthcare_support.api import schemas

    return schemas


def check_no_pii_in_boundary(timeout: int) -> CriterionResult:
    """Verify API response models are sanitized and logs carry no secrets.

    Deterministic source inspection (Principle II): response schemas must
    forbid extra fields and declare no PII/secret field names, and no log
    call in api/ or observability/ may reference secret-answer fields.
    """
    schemas = _load_schemas()

    problems: list[str] = []
    for model_name in ("HealthResponse", "ConversationTurnResponse"):
        model = getattr(schemas, model_name, None)
        if model is None:
            problems.append(f"missing response model {model_name}")
            continue
        if model.model_config.get("extra") != "forbid":
            problems.append(f"{model_name} does not forbid extra fields")
        leaked = _FORBIDDEN_RESPONSE_FIELDS & set(model.model_fields)
        if leaked:
            problems.append(f"{model_name} exposes fields: {sorted(leaked)}")
    for package in ("api", "observability"):
        for source in (REPO_ROOT / "src" / "healthcare_support" / package).rglob("*.py"):
            for line in source.read_text(encoding="utf-8", errors="ignore").splitlines():
                if _LOG_CALL.search(line) and "secret_answer" in line:
                    problems.append(f"log statement may include secret answer in {source.name}")
    details = (
        "response models sanitized; no secret fields in log statements"
        if not problems
        else "; ".join(problems)
    )
    return _result("no-pii-in-boundary", "security", ok=not problems, details=details)


def run_all_checks(timeout: int = DEFAULT_TIMEOUT_SECONDS) -> list[CriterionResult]:
    """Evaluate every go/no-go criterion; none are silently skipped."""
    return [
        check_offline_tests(timeout),
        check_frontend_tests(timeout),
        check_lint(timeout),
        check_format(timeout),
        check_type_check(timeout),
        check_coverage_gate(timeout),
        check_frontend_build(timeout),
        check_deployment_config(timeout),
        check_dependency_audit(timeout),
        check_committed_secrets(timeout),
        check_no_pii_in_boundary(timeout),
    ]
