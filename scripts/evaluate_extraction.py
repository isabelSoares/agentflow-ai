"""Evaluate structured extraction results against a versioned synthetic dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from banking_support.evaluation import evaluate_extraction


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate_extraction(args.dataset)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
