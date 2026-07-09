#!/usr/bin/env python3
"""Validate the DS5-F000 Phase 0 routing-payload scaffold and emit planning artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.phase0_routing_payload import (  # noqa: E402
    RoutingPlanValidationError,
    format_artifact_summary,
    load_manifest,
    validate_manifest,
    write_finding_summary,
    write_routing_artifact,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a DS5-F000 Phase 0 routing-payload scaffold without loading model weights "
            "or unblocking DS5-F002."
        )
    )
    parser.add_argument("--manifest", required=True, type=Path, help="Routing scaffold manifest JSON.")
    parser.add_argument("--artifact-out", type=Path, help="Machine-readable routing artifact JSON output.")
    parser.add_argument("--summary-out", type=Path, help="Human-readable finding markdown output.")
    args = parser.parse_args(argv)

    try:
        manifest = load_manifest(args.manifest)
        artifact = validate_manifest(manifest, manifest_path=str(args.manifest))
    except RoutingPlanValidationError as exc:
        parser.exit(2, f"routing scaffold validation failed: {exc}\n")

    artifact_out = args.artifact_out or Path(artifact["artifact_policy"]["default_artifact_path"])
    summary_out = args.summary_out or Path(artifact["artifact_policy"]["default_summary_path"])
    write_routing_artifact(artifact, artifact_out)
    write_finding_summary(artifact, summary_out)
    print(format_artifact_summary(artifact))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
