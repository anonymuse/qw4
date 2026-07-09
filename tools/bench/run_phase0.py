#!/usr/bin/env python3
"""Run repeatable DS5 Phase 0 coordinator scenarios."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_command(command: list[str], cwd: Path) -> int:
    print("+ " + " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=str(cwd))
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DS5 Phase 0 scenarios repeatedly.")
    parser.add_argument("--config", required=True, help="Cluster config path.")
    parser.add_argument("--scenario", required=True, help="Scenario TOML path.")
    parser.add_argument("--out-root", default="artifacts/runs", help="Artifact root.")
    parser.add_argument("--label", default="phase0", help="Run directory label prefix.")
    parser.add_argument("--repeats", type=int, default=1, help="Number of repeated coordinator runs.")
    parser.add_argument("--validate", action="store_true", help="Validate each completed run artifact directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    args = parser.parse_args(argv)

    if args.repeats < 1:
        parser.error("--repeats must be >= 1")

    out_root = Path(args.out_root)
    run_dirs: list[Path] = []
    for index in range(args.repeats):
        stamp = time.strftime("%Y%m%d-%H%M%S")
        run_dir = out_root / f"{args.label}-{stamp}-{index + 1:02d}"
        run_dirs.append(run_dir)
        command = [
            "zig",
            "build",
            "run-coordinator",
            "--",
            "--config",
            args.config,
            "--scenario",
            args.scenario,
            "--out",
            str(run_dir),
        ]
        if args.dry_run:
            print("+ " + " ".join(command))
        else:
            code = run_command(command, REPO_ROOT)
            if code != 0:
                return code
            if args.validate:
                code = run_command(["python3", "tools/report/validate_run.py", str(run_dir)], REPO_ROOT)
                if code != 0:
                    return code
        time.sleep(1)

    print("Run directories:")
    for run_dir in run_dirs:
        print(f"  {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
