# DS5-F000 Artifact Readiness Runbook

Status: prep-only readiness checklist; target A/B/C hardware sequence not yet run.

## Purpose

Use this runbook before the first DS5-F000 target-hardware transport run. It
checks that the artifact contract, validator, report path, and operator command
sequence are ready to collect evidence for:

- p50/p95/p99 latency by message size;
- throughput by block size;
- scheduler overhead per simulated token;
- concurrent A-B and A-C interference;
- checksum failures;
- reconnect, retry, timeout, and worker-health behavior;
- projected decode impact from transport-derived remote expert-rate sweeps.

This runbook does not record a target-hardware finding. Loopback, localhost, and
fixture evidence remain scaffolding only.

## Readiness Audit

| Acceptance area | Machine-readable gate | Current readiness |
|---|---|---|
| Required artifact set | `tools/report/validate_run.py` requires `run.json`, `events.jsonl`, `latency.csv`, `throughput.csv`, and `summary.md`. | Ready for validation. |
| A/B/C topology | `run.json` must include node A as coordinator and nodes B/C as workers. | Ready for validation. |
| Qwen-shaped traffic | `run.json.scenario.qwen_shape` must match 94 layers, hidden size 4096, top-k 8, B layers 0-46, C layers 47-93. | Ready for validation. |
| Latency percentiles | Run-level latency metrics and `latency.csv` must cover every scenario message size for A-B and A-C with p50/p95/p99 ordering. | Ready for validation. |
| Throughput sweep | Run-level throughput metrics and solo `throughput.csv` rows must cover every scenario block size for A-B and A-C. | Ready for validation. |
| Concurrent interference | Run-level interference metrics and concurrent `throughput.csv` rows must include simultaneous A-B/A-C traffic. | Ready for validation. |
| Checksums | `run.json.checksums` totals must balance, checksum failure status must match, and failed checksums must have `checksum_verified` fail events. | Ready for validation. |
| Reconnect behavior | Non-zero failure, retry, reconnect, and timeout counters must be backed by matching events. | Ready for validation. |
| Worker health | Worker B and C discovery and health events are required. | Ready for validation. |
| Projected decode impact | Every remote expert rate must include local rate, bytes per simulated token, simulated transport time, scheduler overhead input, formula text, and upper-bound tokens/sec. | Ready for validation. |
| Hardware interpretation | `hardware_interpretable` requires `scenario.kind = real_cluster` and a non-empty confirmed network path. | Ready for validation. |

## Preflight On All Nodes

Run these commands on A, B, and C and save output into the run notes:

```bash
hostname
sw_vers
system_profiler SPHardwareDataType
sysctl -n hw.model
sysctl -n hw.memsize
zig version
python3 --version
git rev-parse HEAD
git status --short --branch
```

Record the intended physical path before running the coordinator:

```text
Node A address: <A_THUNDERBOLT_OR_ETHERNET_ADDRESS>
Node B address: <B_THUNDERBOLT_OR_ETHERNET_ADDRESS>
Node C address: <C_THUNDERBOLT_OR_ETHERNET_ADDRESS>
Confirmed network path: <Thunderbolt Bridge / Ethernet / other>
Wi-Fi fallback disabled or ruled out: <yes/no and evidence>
Clock sync note: <NTP / manual check / other>
Power mode and background load notes: <notes>
```

If the path cannot be confirmed as non-loopback and non-localhost, run artifacts
must set `hardware_interpretable` to `false`.

## Target A/B/C Command Sequence

Not yet run. Replace placeholders, keep the generated artifacts, and paste the
final command lines into the finding.

On worker B:

```bash
git checkout codex/ds5-f000-artifact-readiness
git rev-parse HEAD
zig build run-worker -- --node B --listen 0.0.0.0:7555
```

On worker C:

```bash
git checkout codex/ds5-f000-artifact-readiness
git rev-parse HEAD
zig build run-worker -- --node C --listen 0.0.0.0:7556
```

On coordinator A, create or update the untracked local cluster config from the
example and replace the placeholders:

```bash
cp configs/cluster.local.example.toml configs/cluster.local.toml
```

Required config substitutions:

```text
<B_HOST_OR_ADDRESS> = <B_THUNDERBOLT_OR_ETHERNET_ADDRESS>
<C_HOST_OR_ADDRESS> = <C_THUNDERBOLT_OR_ETHERNET_ADDRESS>
<CONFIRMED_NETWORK_PATH> = <Thunderbolt Bridge / Ethernet / other>
```

Then run the target Phase 0 scenario from coordinator A:

```bash
python3 tools/bench/run_phase0.py \
  --config configs/cluster.local.toml \
  --scenario benchmarks/scenarios/qwen3_moe_transport_smoke.toml \
  --out-root artifacts/runs \
  --label ds5-f000-abc \
  --repeats 3 \
  --validate
```

The helper expands each run to `artifacts/runs/ds5-f000-abc-<timestamp>-NN/`.
Each generated run directory must validate independently.

## Post-Run Validation

For each generated run directory:

```bash
python3 tools/report/validate_run.py artifacts/runs/<run-id>
python3 tools/report/summarize_phase0.py artifacts/runs/<run-id> > artifacts/runs/<run-id>/report-summary.md
python3 tools/report/aggregate_phase0.py artifacts/runs/<run-id>
```

For a batch:

```bash
python3 tools/report/aggregate_phase0.py --root artifacts/runs
```

The summary may support a finding only when:

- `run.json.environment.hardware_interpretable` is `true`;
- `run.json.scenario.kind` is `real_cluster`;
- `run.json.environment.confirmed_network_path` names the actual non-loopback
  path;
- both worker links have validated latency, throughput, concurrent, checksum,
  health, reconnect, scheduler, and projection coverage;
- `summary.md` and the generated report do not describe loopback or localhost
  data as hardware-cluster evidence.

## Scaffolding Evidence Rules

The checked-in fixture under `tests/fixtures/artifacts/transport-smoke` is
synthetic loopback scaffolding. It exists to exercise schema and report
validation, including non-zero retry/reconnect behavior. It must not be cited as
Thunderbolt, inter-node, or target-hardware performance evidence.

Loopback or socket-localhost runs are useful only for:

- artifact completeness;
- validator regressions;
- checksum and event plumbing;
- summary/report formatting;
- command ergonomics before target hardware is available.

They cannot answer the DS5-F000 go/no-go question.
