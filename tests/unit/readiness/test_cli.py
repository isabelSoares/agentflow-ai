"""US1 CLI end-to-end tests with stubbed criteria (offline)."""

from __future__ import annotations

import json

import pytest

from healthcare_support.readiness import cli
from healthcare_support.readiness.models import CriterionResult, CriterionStatus


def _results(all_pass: bool) -> list[CriterionResult]:
    status = CriterionStatus.PASS if all_pass else CriterionStatus.FAIL
    return [
        CriterionResult(
            name="lint",
            category="quality-gates",
            status=status,
            details="details",
            remediation="" if all_pass else "run ruff",
        )
    ]


def test_main_exit_0_when_ready(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(cli, "run_all_checks", lambda timeout: _results(True))
    assert cli.main([]) == 0
    out = capsys.readouterr().out
    assert "LAUNCH READINESS: READY" in out


def test_main_exit_1_when_not_ready(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(cli, "run_all_checks", lambda timeout: _results(False))
    assert cli.main([]) == 1
    out = capsys.readouterr().out
    assert "LAUNCH READINESS: NOT READY" in out
    assert "run ruff" in out


def test_main_json_output_schema(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(cli, "run_all_checks", lambda timeout: _results(False))
    assert cli.main(["--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "not_ready"
    assert payload["results"][0]["name"] == "lint"


def test_main_exit_2_on_invalid_timeout(capsys: pytest.CaptureFixture) -> None:
    assert cli.main(["--timeout", "0"]) == 2


def test_main_exit_2_when_check_errors(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    def boom(timeout: int) -> list[CriterionResult]:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "run_all_checks", boom)
    assert cli.main([]) == 2
