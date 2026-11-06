"""Contract tests for dependency scanning and update automation."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_dependency_audit_covers_schedule_and_dependency_changes() -> None:
    workflow = (ROOT / ".github/workflows/dependency-audit.yml").read_text()
    dependabot = (ROOT / ".github/dependabot.yml").read_text()

    assert "schedule:" in workflow
    assert "pull_request:" in workflow
    assert '"pyproject.toml"' in workflow
    assert '"uv.lock"' in workflow
    assert "uv sync --locked" in workflow
    assert "uv export --locked --format requirements.txt" in workflow
    assert "pip-audit --strict -r" in workflow
    assert "package-ecosystem: uv" in dependabot
    assert "package-ecosystem: npm" in dependabot
    assert "package-ecosystem: github-actions" in dependabot
    assert "package-ecosystem: docker" in dependabot
