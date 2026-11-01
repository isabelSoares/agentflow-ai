"""Contract tests for the demo browser client routing configuration."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[2]
API_CLIENT = ROOT / "frontend" / "src" / "api.ts"
VITE_CONFIG = ROOT / "frontend" / "vite.config.ts"
README = ROOT / "README.md"


def test_browser_client_defaults_to_the_api_prefix() -> None:
    source = API_CLIENT.read_text(encoding="utf-8")

    assert "VITE_API_BASE_URL" in source
    assert "return '/api'" in source
    assert "return configured.replace(/\\/+$/, '')" in source
    assert "${API_BASE}${path}" in source


def test_dev_and_preview_proxies_forward_the_api_prefix() -> None:
    source = VITE_CONFIG.read_text(encoding="utf-8")

    assert source.count("'/api':") == 2
    assert source.count("target: 'http://127.0.0.1:8000'") == 2
    assert source.count("rewrite: (path) => path.replace(/^\\/api/, '')") == 2
    assert "server:" in source
    assert "preview:" in source


def test_documentation_describes_the_api_routing_contract() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "The browser client defaults to `/api`" in readme
    assert "route `/api` to the backend" in readme
    assert "Troubleshooting a 404 on session start" in readme
