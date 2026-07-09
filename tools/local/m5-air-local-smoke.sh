#!/usr/bin/env sh
set -eu

RUN_DIR="${RUN_DIR:-artifacts/runs/m5-air-loopback-smoke}"
MEMORY_JSON="${MEMORY_JSON:-/tmp/qwen3_memory_estimate.json}"

CONFIG="configs/cluster.loopback.toml"
SCENARIO="benchmarks/scenarios/loopback_transport_smoke.toml"
MEMORY_CONFIG="configs/qwen3_235b_a22b_planning.json"
FIXTURE_DIR="tests/fixtures/artifacts/transport-smoke"

step() {
  printf '\n==> %s\n' "$1"
}

printf '%s\n' "M5 Air local smoke: loopback-only validation."
printf '%s\n' "This does not claim Thunderbolt cluster, worker-node, or model inference performance."

step "Zig build tests"
zig build test

step "Fixture artifact validation"
python3 -B tools/report/validate_run.py "$FIXTURE_DIR"

step "Loopback transport smoke"
zig build run-coordinator -- \
  --config "$CONFIG" \
  --scenario "$SCENARIO" \
  --out "$RUN_DIR"

step "Generated artifact validation"
python3 -B tools/report/validate_run.py "$RUN_DIR"

step "Qwen3 planning memory estimate"
python3 -B tools/quant/estimate_qwen3_memory.py \
  --config "$MEMORY_CONFIG" \
  --json-out "$MEMORY_JSON"

step "Phase 0 summary"
python3 -B tools/report/summarize_phase0.py "$RUN_DIR"

printf '\n%s\n' "Local smoke complete."
printf '%s\n' "Run artifacts: $RUN_DIR"
printf '%s\n' "Memory estimate JSON: $MEMORY_JSON"
