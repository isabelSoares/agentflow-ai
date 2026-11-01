"""Contract tests for the floating, rounded, highlighted topbar presentation."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
STYLES = ROOT / "frontend" / "src" / "styles.css"


def _rule_blocks(selector: str) -> list[str]:
    text = STYLES.read_text(encoding="utf-8")
    return re.findall(rf"\.{re.escape(selector)}\s*\{{(.*?)\}}", text, re.DOTALL)


def _mobile_block() -> str:
    text = STYLES.read_text(encoding="utf-8")
    match = re.search(r"@media \(max-width: 700px\)\s*\{(.*?)\n\}", text, re.DOTALL)
    assert match is not None, "missing mobile media query"
    return match.group(1)


def test_topbar_is_sticky_floating_and_highlighted() -> None:
    blocks = _rule_blocks("site-header")
    assert len(blocks) >= 2, "expected a base rule and a mobile override"

    base = blocks[0]
    for declaration in (
        "position: sticky",
        "top:",
        "margin:",
        "padding:",
        "border:",
        "border-radius:",
        "box-shadow:",
        "backdrop-filter:",
    ):
        assert declaration in base, f"topbar rule is missing {declaration}"

    assert "border-bottom:" not in base
    assert "border-radius: var(--radius-lg)" in base


def test_mobile_topbar_keeps_spacing_and_rounding() -> None:
    mobile = _mobile_block()

    assert ".site-header" in mobile
    header_rule = re.search(r"\.site-header\s*\{(.*?)\}", mobile, re.DOTALL)
    assert header_rule is not None
    block = header_rule.group(1)

    assert "margin:" in block
    assert "padding:" in block
    assert "border-radius: var(--radius-md)" in block


def test_page_shell_provides_left_and_right_margins() -> None:
    blocks = _rule_blocks("app-shell")
    assert any("padding: 0 28px 40px" in block for block in blocks)
    assert "padding: 0 16px 32px" in _mobile_block()
