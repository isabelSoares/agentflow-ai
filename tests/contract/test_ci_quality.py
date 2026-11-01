"""Contract tests for offline CI quality gates."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_quality_workflow_enforces_offline_coverage_and_existing_gates() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()

    assert "not live_llm and not live_speech" in workflow
    assert "--cov=src/banking_support" in workflow
    assert "--cov-branch" in workflow
    assert "--cov-fail-under=80" in workflow
    assert "uv run ruff check src tests" in workflow
    assert "uv run ruff format --check src tests" in workflow
    assert "uv run mypy src" in workflow
    assert "GROQ_API_KEY" in workflow


def test_frontend_workflow_typechecks_and_builds_the_client() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()

    assert "frontend/package-lock.json" in workflow
    assert "npm ci" in workflow
    assert "npm test" in workflow
    assert "npm run build" in workflow
