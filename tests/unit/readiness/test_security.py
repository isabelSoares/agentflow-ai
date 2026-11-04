"""US3 tests for security criteria (offline; values never leaked)."""

from __future__ import annotations

from pathlib import Path

import pytest

from healthcare_support.readiness import checks
from healthcare_support.readiness.models import CriterionStatus
from healthcare_support.readiness.runner import RunOutcome


def test_committed_secrets_scan_detects_patterns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(checks, "REPO_ROOT", tmp_path)
    (tmp_path / "config.py").write_text('AWS_KEY = "AKIAIOSFODNN7ABCDEFG"\n')
    monkeypatch.setattr(checks, "_tracked_files", lambda: ["config.py"])
    ok, details = checks.scan_for_committed_secrets()
    assert ok is False
    assert "config.py" in details
    assert "aws-access-key" in details
    assert "AKIAIOSFODNN7ABCDEFG" not in details  # value never reported


def test_committed_secrets_scan_detects_private_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(checks, "REPO_ROOT", tmp_path)
    (tmp_path / "key.pem").write_text("-----BEGIN RSA PRIVATE KEY-----\nMII...\n")
    monkeypatch.setattr(checks, "_tracked_files", lambda: ["key.pem"])
    ok, details = checks.scan_for_committed_secrets()
    assert ok is False
    assert "private-key-block" in details
    assert "MII" not in details


def test_committed_secrets_scan_ignores_fake_placeholder_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(checks, "REPO_ROOT", tmp_path)
    (tmp_path / "test_client.py").write_text(
        'client = OpenAISpeechToText(api_key="test-key-123")\n'
    )
    monkeypatch.setattr(checks, "_tracked_files", lambda: ["test_client.py"])
    ok, _ = checks.scan_for_committed_secrets()
    assert ok is True


def test_committed_secrets_scan_clean_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(checks, "REPO_ROOT", tmp_path)
    (tmp_path / "main.py").write_text("x = 1\n")
    monkeypatch.setattr(checks, "_tracked_files", lambda: ["main.py"])
    ok, details = checks.scan_for_committed_secrets()
    assert ok is True
    result = checks.check_committed_secrets(timeout=10)
    assert result.status == CriterionStatus.PASS
    assert result.remediation == ""


def test_dependency_audit_fail_on_vulnerabilities(monkeypatch: pytest.MonkeyPatch) -> None:
    outcomes = iter(
        [
            RunOutcome(ok=True, unable_to_verify=False, summary="exported"),
            RunOutcome(ok=False, unable_to_verify=False, summary="1 vulnerability found"),
        ]
    )
    monkeypatch.setattr(checks, "run_command", lambda *a, **k: next(outcomes))
    result = checks.check_dependency_audit(timeout=10)
    assert result.status == CriterionStatus.FAIL
    assert result.remediation == checks.REMEDIATION["dependency-audit"]


def test_dependency_audit_unable_to_verify_without_uv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(checks.shutil, "which", lambda name: None)
    result = checks.check_dependency_audit(timeout=10)
    assert result.status == CriterionStatus.UNABLE_TO_VERIFY


def test_no_pii_boundary_passes_for_sanitized_schemas() -> None:
    result = checks.check_no_pii_in_boundary(timeout=10)
    assert result.status == CriterionStatus.PASS, result.details


def test_no_pii_boundary_detects_leaky_model(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    from pydantic import BaseModel

    class LeakyResponse(BaseModel):
        model_config = {"extra": "allow"}
        secret_answer: str

    class HealthyResponse(BaseModel):
        model_config = {"extra": "forbid"}
        status: str

    fake_schemas = SimpleNamespace(
        HealthResponse=HealthyResponse, ConversationTurnResponse=LeakyResponse
    )
    monkeypatch.setattr(checks, "_load_schemas", lambda: fake_schemas)
    result = checks.check_no_pii_in_boundary(timeout=10)
    assert result.status == CriterionStatus.FAIL
    assert "secret_answer" in result.details
