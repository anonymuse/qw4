#!/usr/bin/env python3
"""Estimate Qwen3 planning memory from local metadata only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.qwen3_memory import ConfigError, estimate_from_config, format_human_summary, load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate DS5 Qwen3-235B-A22B static placement and KV-cache memory "
            "without downloading or loading model weights."
        )
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the local JSON planning config.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of the human summary.",
    )
    parser.add_argument(
        "--json-out",
        help="Optional path to also write the machine-readable JSON result.",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    try:
        config = load_config(config_path)
        result = estimate_from_config(config, config_path=str(config_path))
    except (OSError, json.JSONDecodeError, ConfigError) as exc:
        print(f"estimate_qwen3_memory: {exc}", file=sys.stderr)
        return 2

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_human_summary(result))
        print("")
        print("Machine-readable JSON: rerun with --json or add --json-out PATH.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

