"""Contract tests for the production container and build context."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_container_uses_staged_non_root_runtime() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()
    workflow = (ROOT / ".github/workflows/container.yml").read_text()

    assert "AS builder" in dockerfile
    assert "FROM python:3.13-slim-bookworm AS runtime" in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert 'test "$uid" = "10001"' in workflow
    assert "Poll health endpoint" in workflow


def test_docker_context_excludes_non_runtime_content() -> None:
    dockerignore = (ROOT / ".dockerignore").read_text()

    for entry in (".git", ".env*", "__pycache__/", "tests/", "specs/", "docs/", "coverage/"):
        assert entry in dockerignore
