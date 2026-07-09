#!/usr/bin/env python3
"""Aggregate multiple DS5 Phase 0 artifact directories."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def load_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError:
        return []


def number(value: str | None) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def summarize_run(run_dir: Path) -> dict[str, Any]:
    run = load_json(run_dir / "run.json")
    latency = load_csv(run_dir / "latency.csv")
    throughput = load_csv(run_dir / "throughput.csv")
    environment = run.get("environment", {}) if isinstance(run.get("environment"), dict) else {}
    scenario = run.get("scenario", {}) if isinstance(run.get("scenario"), dict) else {}
    return {
        "run_dir": str(run_dir),
        "run_id": run.get("run_id", run_dir.name),
        "valid": run.get("valid", False),
        "scenario": scenario.get("name", "unknown"),
        "scenario_kind": scenario.get("kind", "unknown"),
        "transport_mode": environment.get("transport_mode", environment.get("network_path", "unknown")),
        "socket_mode": environment.get("socket_mode", "unknown"),
        "network_path": environment.get("network_path", "unknown"),
        "hardware_interpretable": environment.get("hardware_interpretable", False),
        "checksum_failures": (run.get("checksums") or {}).get("failed", "unknown"),
        "latency_p95_us_max": max([number(row.get("p95_us")) for row in latency] or [0.0]),
        "throughput_mib_s_max": max([number(row.get("mib_per_sec")) for row in throughput] or [0.0]),
    }


def markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Phase 0 Aggregate Comparison",
        "",
        "| Run | Kind | Transport | Hardware data | Max p95 us | Max MiB/s | Checksums |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['run_id']} | {row['scenario_kind']} | {row['transport_mode']} | "
            f"{'yes' if row['hardware_interpretable'] else 'no'} | "
            f"{row['latency_p95_us_max']:.3f} | {row['throughput_mib_s_max']:.3f} | "
            f"{row['checksum_failures']} |"
        )
    kinds = {row["scenario_kind"] for row in rows}
    for expected in ("loopback", "socket_localhost", "real_cluster"):
        if expected not in kinds:
            lines.append(f"| missing | {expected} | placeholder | no | 0 | 0 | unknown |")
    lines.extend(
        [
            "",
            "Loopback and socket-localhost rows are not hardware-cluster data.",
            "A real-cluster row is interpretable only when `hardware_interpretable` is true.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate DS5 Phase 0 runs.")
    parser.add_argument("run_dirs", nargs="*", type=Path, help="Artifact run directories.")
    parser.add_argument("--root", type=Path, help="Scan direct children of an artifact root.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    args = parser.parse_args(argv)

    run_dirs = list(args.run_dirs)
    if args.root:
        run_dirs.extend(sorted(child for child in args.root.iterdir() if child.is_dir()))
    if not run_dirs:
        parser.error("provide run directories or --root")

    rows = [summarize_run(run_dir) for run_dir in run_dirs]
    if args.json:
        print(json.dumps({"schema_version": "phase0.aggregate.v1", "runs": rows}, indent=2, sort_keys=True))
    else:
        sys.stdout.write(markdown(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
