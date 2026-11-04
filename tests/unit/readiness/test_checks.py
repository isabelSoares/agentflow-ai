"""Unit tests for US1 criterion evaluators (runner mocked; fully offline)."""

from __future__ import annotations

from pathlib import Path

import pytest

from healthcare_support.readiness import checks
from healthcare_support.readiness.models import CriterionStatus
from healthcare_support.readiness.runner import RunOutcome


def _outcome(ok: bool, unable: bool = False, summary: str = "ok") -> RunOutcome:
    return RunOutcome(ok=ok, unable_to_verify=unable, summary=summary)


@pytest.fixture
def mock_run(monkeypatch: pytest.MonkeyPatch):
    def _install(outcomes: dict[str, RunOutcome]):
        def fake_run(argv: list[str], *, timeout: int, cwd: str | None = None) -> RunOutcome:
            key = argv[-1] if argv[0] in {"npm"} else " ".join(argv[:3])
            return outcomes.get(key, outcomes.get("default", _outcome(True)))

        monkeypatch.setattr(checks, "run_command", fake_run)

    return _install


def test_offline_tests_pass(mock_run) -> None:
    mock_run({"default": _outcome(True)})
    result = checks.check_offline_tests(timeout=10)
    assert result.status == CriterionStatus.PASS
    assert result.name == "offline-tests"
    assert result.category == "tests"
    assert result.remediation == ""


def test_offline_tests_fail_has_remediation(mock_run) -> None:
    mock_run({"default": _outcome(False, summary="3 failed")})
    result = checks.check_offline_tests(timeout=10)
    assert result.status == CriterionStatus.FAIL
    assert "pytest" in result.remediation


def test_missing_tool_is_unable_to_verify_not_pass(mock_run) -> None:
    mock_run({"default": _outcome(False, unable=True, summary="tool not found")})
    for check in (checks.check_lint, checks.check_format, checks.check_type_check):
        result = check(timeout=10)
        assert result.status == CriterionStatus.UNABLE_TO_VERIFY
        assert result.remediation  # non-empty


def test_timeout_is_unable_to_verify(mock_run) -> None:
    mock_run({"default": _outcome(False, unable=True, summary="timed out after 10s")})
    result = checks.check_coverage_gate(timeout=10)
    assert result.status == CriterionStatus.UNABLE_TO_VERIFY


def test_frontend_checks_block_when_frontend_missing(
    mock_run, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(checks, "REPO_ROOT", tmp_path)
    mock_run({"default": _outcome(True)})
    for check in (checks.check_frontend_tests, checks.check_frontend_build):
        result = check(timeout=10)
        assert result.status == CriterionStatus.UNABLE_TO_VERIFY


def test_deployment_config_detects_missing_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(checks, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(checks, "_tracked_files", lambda: ["README.md"])
    result = checks.check_deployment_config(timeout=10)
    assert result.status == CriterionStatus.FAIL
    assert "Dockerfile" in result.details


def test_deployment_config_detects_committed_env_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(checks, "REPO_ROOT", tmp_path)
    (tmp_path / "Dockerfile").write_text("FROM python:3.13")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI")
    monkeypatch.setattr(checks, "_tracked_files", lambda: [".env"])
    result = checks.check_deployment_config(timeout=10)
    assert result.status == CriterionStatus.FAIL
    assert ".env" in result.details


def test_deployment_config_passes_on_healthy_tree(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(checks, "REPO_ROOT", tmp_path)
    (tmp_path / "Dockerfile").write_text("FROM python:3.13")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI")
    monkeypatch.setattr(checks, "_tracked_files", lambda: ["Dockerfile", "README.md"])
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    result = checks.check_deployment_config(timeout=10)
    assert result.status == CriterionStatus.PASS


def test_run_all_checks_evaluates_every_criterion(
    mock_run, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(checks, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(checks, "_tracked_files", lambda: ["README.md"])
    mock_run({"default": _outcome(True)})
    results = checks.run_all_checks(timeout=10)
    names = {r.name for r in results}
    assert names == set(checks.REMEDIATION.keys())
    assert len(results) == len(names)  # zero silently skipped
