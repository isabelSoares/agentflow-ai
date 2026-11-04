#!/usr/bin/env python3
"""Thin CLI wrapper for the launch readiness check.

Usage:
    uv run python scripts/check_launch_readiness.py [--json] [--timeout SECONDS]

Exit codes: 0 = ready, 1 = not ready, 2 = check error.
"""

from __future__ import annotations

import sys

from healthcare_support.readiness.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
