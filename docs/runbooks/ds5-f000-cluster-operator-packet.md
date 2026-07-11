# DS5-F000 Cluster Operator Packet

Status: ready for first target A/B/C run; target-hardware evidence not yet collected.

Use this packet when the intended cluster is physically available:

- Node A: M5 Pro coordinator/orchestrator, benchmark controller, and control plane.
- Node B: M5 Max synthetic LLM data-plane worker.
- Node C: M5 Max synthetic LLM data-plane worker.

The Phase 0 question is:

> Can an M5 Pro orchestrator agent keep two M5 Max synthetic LLM data-plane workers fed with Qwen3-shaped activation/result traffic without transport, scheduling, or control-plane overhead dominating decode-shaped work?

This packet does not load Qwen weights, run tokenizer assets, allocate KV cache
pages, implement speculative decoding, run fused routing, execute Metal kernels,
or make active SSD/NVMe decode-path claims.

## Inputs To Lock Before Running

Use the same Git commit on all three nodes. Record the exact branch or commit in
the finding before starting workers.

```text
Branch or commit on A/B/C: <branch-or-commit>
Node A role: M5 Pro coordinator/orchestrator/control plane
Node B role: M5 Max synthetic LLM data-plane worker
Node C role: M5 Max synthetic LLM data-plane worker
Confirmed network path: <Thunderbolt Bridge / Ethernet / other>
Wi-Fi fallback disabled or ruled out: <yes/no and evidence>
Artifact label: ds5-f000-abc-<YYYYMMDD>-<short-note>
```

Do not interpret artifacts as target-hardware evidence unless the confirmed
network path is non-loopback, non-localhost, and recorded in `run.json`.

## Preflight On A, B, And C

Run on every node and paste the output into the run notes:

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

Record operational conditions:

```text
Power mode: <plugged in / low power disabled / other>
Background load: <quiet / known processes>
Clock sync note: <NTP / manual check / other>
Thermal note: <cold start / warmed / unknown>
```

## Build And Test

Run on Node A before the target run:

```bash
make test
```

If this fails, fix the branch before collecting target-hardware data.

## Configure Node A

Create an untracked local config on Node A:

```bash
cp configs/cluster.local.example.toml configs/cluster.local.toml
```

Replace the placeholders in `configs/cluster.local.toml`:

```text
node-b.local.example:7555 -> <B_THUNDERBOLT_OR_ETHERNET_ADDRESS>:7555
node-c.local.example:7556 -> <C_THUNDERBOLT_OR_ETHERNET_ADDRESS>:7556
confirmed_network_path -> <Thunderbolt Bridge / Ethernet / other>
```

Do not commit `configs/cluster.local.toml`.

## Start Workers

On Node B:

```bash
git checkout <branch-or-commit-used-on-node-a>
git rev-parse HEAD
zig build run-worker -- --node B --listen 0.0.0.0:7555
```

On Node C:

```bash
git checkout <branch-or-commit-used-on-node-a>
git rev-parse HEAD
zig build run-worker -- --node C --listen 0.0.0.0:7556
```

Leave both worker terminals running until Node A completes the coordinator
batch.

## Run Coordinator Batch

On Node A:

```bash
python3 tools/bench/run_phase0.py \
  --config configs/cluster.local.toml \
  --scenario benchmarks/scenarios/qwen3_moe_transport_smoke.toml \
  --out-root artifacts/runs \
  --label ds5-f000-abc \
  --repeats 3 \
  --validate
```

The helper writes run directories like:

```text
artifacts/runs/ds5-f000-abc-<timestamp>-01/
artifacts/runs/ds5-f000-abc-<timestamp>-02/
artifacts/runs/ds5-f000-abc-<timestamp>-03/
```

## Validate And Summarize

For each generated run directory:

```bash
python3 tools/report/validate_run.py artifacts/runs/<run-id>
python3 tools/report/summarize_phase0.py artifacts/runs/<run-id> > artifacts/runs/<run-id>/report-summary.md
python3 tools/model_inspect/simulate_qwen3_moe.py --run-dir artifacts/runs/<run-id>
```

For the batch:

```bash
python3 tools/report/aggregate_phase0.py --root artifacts/runs
```

Validation must pass independently for every run directory before writing a
finding.

## Finding Decision

Write the result with `docs/findings/phase0-transport-template.md`. Choose one
decision:

- `Proceed`: target-hardware transport and control-plane evidence supports
  runtime placement evidence work.
- `Redesign`: transport works, but packetization, scheduling, checksum cost, or
  concurrency behavior must change before runtime work.
- `Reduce assumption`: continue only with lower remote-expert movement
  assumptions.
- `Publish limit`: the measured transport envelope is incompatible with the
  intended decode-shaped traffic.
- `Rerun`: path, artifacts, checksums, or trace coverage are insufficient.

The finding must include a claims ledger:

```text
Measured: <artifact-backed facts>
Projected: <transport-derived simulations>
Assumed: <planning assumptions not proven by this run>
Out of scope: model loading, tokenizer, KV allocator, fused routing, Metal kernels, active SSD/NVMe decode path
```

## Optional Storage Adjunct

SSD/NVMe measurements may be useful for future cold backing, promotion,
artifacts, or long-context backing. Run them only as a separate task and label
their artifact directory separately. They do not answer the DS5-F000 go/no-go
question and must not be used to justify a steady-state active-weight decode
path from storage.
