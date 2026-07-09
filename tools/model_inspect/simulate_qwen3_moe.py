#!/usr/bin/env python3
"""Convert Phase 0 transport measurements into Qwen-shaped MoE transport simulations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_run(run_dir: Path) -> dict[str, Any]:
    return json.loads((run_dir / "run.json").read_text(encoding="utf-8"))


def closest_latency(metrics: list[dict[str, Any]], target_size: int) -> dict[str, Any]:
    if not metrics:
        return {"p50_us": 0, "p95_us": 0, "p99_us": 0, "message_size_bytes": target_size}
    return min(metrics, key=lambda item: abs(int(item.get("message_size_bytes", 0)) - target_size))


def max_throughput(metrics: list[dict[str, Any]]) -> float:
    best_mib = max((float(item.get("mib_per_sec", 0.0)) for item in metrics), default=0.0)
    return best_mib * 1024 * 1024


def parse_rates(value: str) -> list[float]:
    rates = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not rates:
        raise argparse.ArgumentTypeError("at least one rate is required")
    for rate in rates:
        if rate < 0 or rate > 1:
            raise argparse.ArgumentTypeError("rates must be in [0, 1]")
    return rates


def simulate(run: dict[str, Any], rates: list[float], tokens: int) -> dict[str, Any]:
    scenario = run.get("scenario", {})
    qwen = scenario.get("qwen_shape", {})
    metrics = run.get("metrics", {})
    layers = int(qwen.get("layers", 94))
    hidden_size = int(qwen.get("hidden_size", 4096))
    top_k = int(qwen.get("top_k", 8))
    activation_bytes = hidden_size * 2
    packet_bytes = activation_bytes
    latency = closest_latency(metrics.get("latency_by_message_size", []), packet_bytes)
    throughput_bps = max_throughput(metrics.get("throughput_by_block_size", []))

    rows = []
    for rate in rates:
        remote_expert_packets_per_token = layers * top_k * rate
        bytes_per_token = int(remote_expert_packets_per_token * packet_bytes * 2)
        latency_us_per_token_p50 = remote_expert_packets_per_token * float(latency.get("p50_us", 0.0)) * 2
        latency_us_per_token_p95 = remote_expert_packets_per_token * float(latency.get("p95_us", 0.0)) * 2
        throughput_us_per_token = (bytes_per_token / throughput_bps * 1_000_000) if throughput_bps > 0 else 0.0
        transport_us_per_token = max(latency_us_per_token_p95, throughput_us_per_token)
        rows.append(
            {
                "remote_expert_rate": rate,
                "local_expert_rate": 1.0 - rate,
                "layers": layers,
                "top_k": top_k,
                "activation_bytes": activation_bytes,
                "bytes_per_simulated_token": bytes_per_token,
                "latency_us_per_token_p50": latency_us_per_token_p50,
                "latency_us_per_token_p95": latency_us_per_token_p95,
                "throughput_us_per_token": throughput_us_per_token,
                "transport_us_per_token_upper_bound": transport_us_per_token,
                "tokens_per_sec_transport_upper_bound": (1_000_000 / transport_us_per_token) if transport_us_per_token > 0 else 0.0,
            }
        )

    return {
        "schema_version": "phase0.qwen_moe_transport_sim.v1",
        "source_run_id": run.get("run_id"),
        "source_transport_mode": (run.get("environment") or {}).get("transport_mode"),
        "source_hardware_interpretable": (run.get("environment") or {}).get("hardware_interpretable", False),
        "simulated_tokens": tokens,
        "simulation_contract": [
            "Uses Qwen3 shape constants only: 94 layers, hidden size 4096, top-k 8 unless overridden by run.json.",
            "Does not change Qwen top-8 routing semantics.",
            "Does not load model weights or claim quality.",
            "Loopback/socket-localhost source runs remain non-hardware simulations.",
        ],
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulate Qwen-shaped MoE transport cost from Phase 0 artifacts.")
    parser.add_argument("--run-dir", required=True, type=Path, help="Artifact run directory.")
    parser.add_argument("--remote-rates", type=parse_rates, default=parse_rates("0,0.125,0.25,0.5,0.75,1.0"))
    parser.add_argument("--tokens", type=int, default=64, help="Number of simulated decode tokens.")
    parser.add_argument("--json-out", type=Path, help="Optional JSON output path.")
    args = parser.parse_args(argv)

    result = simulate(load_run(args.run_dir), args.remote_rates, args.tokens)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
