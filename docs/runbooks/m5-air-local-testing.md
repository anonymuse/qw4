# M5 Air Local Testing Runbook

Status: local developer runbook.

## Scope

This runbook is for validating DS5/QW4 repo plumbing on a MacBook Air with Apple M5. Treat every result from this runbook as local M5 Air and loopback-only unless a later run explicitly records a non-local hardware path.

This runbook must not be used to claim:

- Thunderbolt cluster performance;
- final worker-node performance;
- final model inference performance;
- full Qwen3-235B-A22B placement success;
- any result from downloaded full model weights.

The default smoke path does not download weights and does not run the model.

## Toolchain Capture

Run these first and paste the output into the finding:

```bash
zig version
python3 --version
git --version
git status --short --branch
git rev-parse HEAD
git remote -v
gh --version
gh auth status
sw_vers
system_profiler SPHardwareDataType
sysctl -n hw.model
sysctl -n hw.memsize
```

`system_profiler SPHardwareDataType` is preferred for hardware identity when `sysctl` is blocked by a local sandbox.

## One Command Smoke

From the repository root:

```bash
tools/local/m5-air-local-smoke.sh
```

Optional output locations:

```bash
RUN_DIR=artifacts/runs/m5-air-loopback-smoke \
MEMORY_JSON=/tmp/qwen3_memory_estimate.json \
tools/local/m5-air-local-smoke.sh
```

The helper runs:

- `zig build test`;
- fixture validation;
- loopback coordinator smoke;
- generated artifact validation;
- Qwen3 planning memory estimate;
- Phase 0 summary generation.

## Direct Commands

Use these when debugging a specific stage.

```bash
zig build test
```

```bash
python3 -B tools/report/validate_run.py tests/fixtures/artifacts/transport-smoke
```

```bash
python3 -B tools/quant/estimate_qwen3_memory.py \
  --config configs/qwen3_235b_a22b_planning.json \
  --json-out /tmp/qwen3_memory_estimate.json
```

```bash
zig build run-coordinator -- \
  --config configs/cluster.loopback.toml \
  --scenario benchmarks/scenarios/loopback_transport_smoke.toml \
  --out artifacts/runs/m5-air-loopback-smoke
```

```bash
python3 -B tools/report/validate_run.py artifacts/runs/m5-air-loopback-smoke
```

```bash
python3 -B tools/report/summarize_phase0.py artifacts/runs/m5-air-loopback-smoke
```

## Expected Results

The loopback run should produce:

- `run.json`;
- `events.jsonl`;
- `latency.csv`;
- `throughput.csv`;
- `summary.md`.

The generated run should validate as `phase0.artifacts.v1`.

The run should report `environment.hardware_interpretable = false` and a loopback transport path. If it does not, stop and fix run classification before publishing the result.

## Interpretation Rules

Use this run to validate developer ergonomics, artifact shape, report parsing, checksum plumbing, and the planning memory estimator.

Do not use this run to set cluster throughput targets. Single-process loopback can be useful for finding broken schemas, broken scripts, bad provenance, and local regressions, but it is not a hardware transport measurement.

Memory estimator output is a planning aid only. A PASS in the estimator is not a deployment claim. A FAIL in the estimator is actionable because it narrows the next design question.

## Cleanup

Generated artifacts are ignored by git:

```bash
git status --short artifacts/runs/m5-air-loopback-smoke
```

Remove local generated output only when it is no longer needed for inspection:

```bash
rm -rf artifacts/runs/m5-air-loopback-smoke
rm -f /tmp/qwen3_memory_estimate.json
```
