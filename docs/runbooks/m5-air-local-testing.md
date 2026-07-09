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

## Socket-Localhost Smoke

After the single-process loopback smoke passes, run the two-process localhost
TCP path:

```bash
RUN_DIR=artifacts/runs/socket-localhost-smoke \
tools/local/socket-localhost-smoke.sh
```

Or through `make`:

```bash
make socket-localhost-smoke RUN_ID=socket-localhost-smoke
```

This helper starts worker B and worker C as separate local processes, runs the
coordinator against `configs/cluster.socket-localhost.toml`, validates the
generated artifact directory, and prints the summary plus worker logs.
By default it uses `127.0.0.1:17555` and `127.0.0.1:17556` and writes a
temporary config under `/private/tmp` so it does not collide with manual worker
sessions on the documented 7555/7556 ports.

Interpret the result as process-boundary and TCP-localhost validation only. It
is still not Thunderbolt, RDMA-style, multi-host, or final model-inference data.

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

Socket-localhost equivalent:

```bash
zig build --cache-dir /private/tmp/qw4-zig-cache \
  --global-cache-dir /private/tmp/qw4-zig-global-cache \
  --prefix /private/tmp/qw4-zig-out
```

```bash
/private/tmp/qw4-zig-out/bin/ds5-worker --node B --listen 127.0.0.1:7555
```

```bash
/private/tmp/qw4-zig-out/bin/ds5-worker --node C --listen 127.0.0.1:7556
```

```bash
/private/tmp/qw4-zig-out/bin/ds5-coordinator \
  --config configs/cluster.socket-localhost.toml \
  --scenario benchmarks/scenarios/loopback_transport_smoke.toml \
  --out artifacts/runs/socket-localhost-smoke
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
