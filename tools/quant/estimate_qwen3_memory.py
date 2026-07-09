#!/usr/bin/env python3
"""Estimate Qwen3 planning memory from local metadata only."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from model.qwen3_memory import ConfigError, estimate_from_config, format_human_summary, load_config


PLANNING_MODES = ("config", "a-control-only", "a-static-owner", "bc-worker-only")


def apply_planning_mode(config: dict[str, Any], mode: str) -> dict[str, Any]:
    updated = copy.deepcopy(config)
    updated["planning_mode"] = mode
    nodes = updated.get("nodes", [])
    if not isinstance(nodes, list):
        raise ConfigError("nodes must be a list")

    if mode == "config":
        return updated

    fractions = {
        "a-static-owner": {"A": 1.0 / 3.0, "B": 1.0 / 3.0, "C": 1.0 / 3.0},
        "a-control-only": {"A": 0.0, "B": 0.5, "C": 0.5},
        "bc-worker-only": {"A": 0.0, "B": 0.5, "C": 0.5},
    }[mode]
    role_suffix = {
        "a-static-owner": "static-owner planning",
        "a-control-only": "control-only; no core model weights",
        "bc-worker-only": "B/C worker-only placement",
    }[mode]

    role_by_node = {
        "a-static-owner": {
            "A": "coordinator / static-owner planning",
            "B": "primary worker / static-owner planning",
            "C": "primary worker / static-owner planning",
        },
        "a-control-only": {
            "A": "coordinator / control-only",
            "B": "primary worker",
            "C": "primary worker",
        },
        "bc-worker-only": {
            "A": "coordinator / control-only",
            "B": "primary worker / B-C worker-only placement",
            "C": "primary worker / B-C worker-only placement",
        },
    }[mode]

    for node in nodes:
        if not isinstance(node, dict):
            continue
        name = str(node.get("name", ""))
        if name in fractions:
            node["static_fraction"] = fractions[name]
            if name == "A" and fractions[name] == 0.0:
                node["static_cap_gb"] = 0.0
                node["kv_fraction"] = 0.0
            node["role"] = role_by_node.get(name, f"{node.get('role', name)} / {role_suffix}")

    if mode in {"a-control-only", "bc-worker-only"}:
        for group in updated.get("static_weight_groups", []):
            if not isinstance(group, dict):
                continue
            placement = group.get("placement")
            if not isinstance(placement, dict) or placement.get("type") != "replicated":
                continue
            placement_nodes = placement.get("nodes")
            if isinstance(placement_nodes, list):
                placement["nodes"] = [name for name in placement_nodes if name != "A"]
                group["notes"] = str(group.get("notes", "")) + " Mode overlay removes A from replicated static placement."
    return updated


def apply_expert_bits(config: dict[str, Any], bits: float) -> dict[str, Any]:
    updated = copy.deepcopy(config)
    groups = updated.get("static_weight_groups", [])
    quant_classes = updated.get("quantization", {}).get("classes", {})
    expert_quant_name = None
    for group in groups:
        if isinstance(group, dict) and group.get("name") == "moe_experts":
            expert_quant_name = str(group.get("quant_class", ""))
            break
    if not expert_quant_name or expert_quant_name not in quant_classes:
        raise ConfigError("could not find moe_experts quantization class")
    quant_classes[expert_quant_name]["bits_per_parameter"] = bits
    quant_classes[expert_quant_name]["description"] = (
        f"Sensitivity sweep override for expert planning at {bits:g} bits/parameter; not a quality claim."
    )
    updated["expert_quant_sweep_bits"] = bits
    return updated


def parse_bits(value: str) -> list[float]:
    bits: list[float] = []
    for item in value.split(","):
        stripped = item.strip()
        if not stripped:
            continue
        parsed = float(stripped)
        if parsed <= 0:
            raise argparse.ArgumentTypeError("sweep bits must be positive")
        bits.append(parsed)
    if not bits:
        raise argparse.ArgumentTypeError("at least one sweep bit value is required")
    return bits


def estimate_one(config: dict[str, Any], config_path: Path, mode: str) -> dict[str, Any]:
    result = estimate_from_config(config, config_path=str(config_path))
    result["planning_mode"] = mode
    if "expert_quant_sweep_bits" in config:
        result["expert_quant_sweep_bits"] = config["expert_quant_sweep_bits"]
    return result


def format_sweep_summary(wrapper: dict[str, Any]) -> str:
    lines = [
        "Qwen3 planning memory sensitivity sweep",
        f"Mode: {wrapper['planning_mode']}",
        "",
        "Expert bits  Aggregate static  Worst node static  Result",
    ]
    for result in wrapper["results"]:
        nodes = result["static"]["nodes"]
        worst = max(nodes, key=lambda item: item["total_static_bytes"] - item["static_cap_bytes"])
        passed = all(node["passes_static_cap"] for node in nodes)
        bits = result.get("expert_quant_sweep_bits", "config")
        lines.append(
            f"{bits!s:>11}  "
            f"{result['static']['aggregate_total_static_bytes'] / 1_000_000_000:>15.2f} GB  "
            f"{worst['name']}={worst['total_static_bytes'] / 1_000_000_000:>8.2f} GB  "
            f"{'PASS' if passed else 'FAIL'}"
        )
    lines.extend(
        [
            "",
            "This is a planning-memory sensitivity sweep only.",
            "It does not claim quantization quality, routing quality, or model accuracy.",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate DS5 Qwen3-235B-A22B static placement and KV-cache memory "
            "without downloading or loading model weights."
        )
    )
    parser.add_argument("--config", required=True, help="Path to the local JSON planning config.")
    parser.add_argument("--mode", choices=PLANNING_MODES, default="config", help="Planning mode overlay.")
    parser.add_argument(
        "--sweep-expert-bits",
        type=parse_bits,
        help="Comma-separated expert quantization bit sensitivity sweep, for example 2,3,4,8.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of the human summary.")
    parser.add_argument("--json-out", help="Optional path to also write the machine-readable JSON result.")
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    try:
        config = apply_planning_mode(load_config(config_path), args.mode)
        if args.sweep_expert_bits:
            results = [
                estimate_one(apply_expert_bits(config, bits), config_path, args.mode)
                for bits in args.sweep_expert_bits
            ]
            result: dict[str, Any] = {
                "schema_version": "phase0.memory_sensitivity.v1",
                "config_path": str(config_path),
                "planning_mode": args.mode,
                "sweep_axis": "moe_experts.bits_per_parameter",
                "results": results,
                "limits": [
                    "Memory sensitivity only; no quality, routing, or throughput claim.",
                    "Does not download or inspect model weights.",
                ],
            }
        else:
            result = estimate_one(config, config_path, args.mode)
    except (OSError, json.JSONDecodeError, ConfigError, ValueError) as exc:
        print(f"estimate_qwen3_memory: {exc}", file=sys.stderr)
        return 2

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif args.sweep_expert_bits:
        print(format_sweep_summary(result))
        print("")
        print("Machine-readable JSON: rerun with --json or add --json-out PATH.")
    else:
        print(format_human_summary(result))
        print("")
        print(f"Planning mode: {args.mode}")
        print("Machine-readable JSON: rerun with --json or add --json-out PATH.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
