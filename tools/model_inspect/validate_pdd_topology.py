#!/usr/bin/env python3
"""Validate the DS5-F001 Phase 1 PDD placement manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.pdd_topology import (  # noqa: E402
    PlacementValidationError,
    format_ledger_summary,
    load_manifest,
    validate_manifest,
    write_finding_summary,
    write_memory_ledger,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate DS5-F001 PDD topology scaffolding and optionally emit acceptance artifacts."
    )
    parser.add_argument(
        "--manifest",
        default=str(REPO_ROOT / "configs" / "qwen3_pdd_topology_phase1.json"),
        help="Path to the PDD placement manifest.",
    )
    parser.add_argument("--ledger-out", help="Optional path for the machine-readable memory ledger JSON.")
    parser.add_argument("--summary-out", help="Optional path for the human-readable finding summary Markdown.")
    parser.add_argument("--json", action="store_true", help="Print the memory ledger JSON to stdout.")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    try:
        manifest = load_manifest(manifest_path)
        ledger = validate_manifest(manifest, manifest_path=str(manifest_path))
    except (OSError, json.JSONDecodeError, PlacementValidationError) as exc:
        print(f"validate_pdd_topology: {exc}", file=sys.stderr)
        return 2

    if args.ledger_out:
        write_memory_ledger(ledger, args.ledger_out)
    if args.summary_out:
        write_finding_summary(ledger, args.summary_out)

    if args.json:
        print(json.dumps(ledger, indent=2, sort_keys=True))
    else:
        print(format_ledger_summary(ledger))
        if args.ledger_out:
            print("")
            print(f"Machine-readable memory ledger: {args.ledger_out}")
        else:
            print("")
            print("Machine-readable memory ledger: rerun with --json or add --ledger-out PATH.")
        if args.summary_out:
            print(f"Human-readable finding summary: {args.summary_out}")
        else:
            print("Human-readable finding summary: add --summary-out PATH.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
