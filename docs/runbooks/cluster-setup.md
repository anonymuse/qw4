# Cluster Setup Runbook

Status: Phase 0 draft.

## Goal

Validate the physical DS5 cluster before model runtime work begins.

The first runbook objective is to replace planning assumptions with measured transport, storage, memory, and worker-health data.

## Node Labels

| Label | Hardware | Role |
|---|---|---|
| A | MacBook Pro M5 Pro, 48GB UMA | Coordinator/orchestrator/control plane |
| B | MacBook Pro M5 Max, 48GB UMA | Synthetic LLM data-plane worker |
| C | MacBook Pro M5 Max, 48GB UMA | Synthetic LLM data-plane worker |

Optional support nodes must not carry core model weights unless a later ADR gives a narrow reason.

## Preflight Checklist

- Assign stable hostnames or static IPs for A, B, and C.
- Confirm the intended Thunderbolt topology.
- Disable unrelated high-bandwidth workloads during benchmarks.
- Record macOS version, chip, memory, storage model, and power mode per node.
- Confirm all nodes can reach each other over the intended link.
- Record whether traffic is using Thunderbolt Bridge, Ethernet, Wi-Fi fallback, or another path.
- Keep clocks reasonably synchronized for trace correlation.

## Phase 0 Measurements

Use [DS5-F000 Artifact Readiness](ds5-f000-artifact-readiness.md) for the
prep-only validator checklist and [DS5-F000 Cluster Operator Packet](ds5-f000-cluster-operator-packet.md)
for the exact target A/B/C command sequence.

Measure the following before runtime claims:

| Area | Required measurement |
|---|---|
| Link latency | p50/p95/p99 by message size and node pair |
| Link throughput | sustained bandwidth by block size and node pair |
| Concurrent traffic | A-B and A-C simultaneous transfer interference |
| Copy behavior | user/kernel copy overhead and checksum cost |
| Worker health | heartbeat, reconnect, timeout, and failure reporting |
| Storage | sequential throughput with 16/64/128/256MiB blocks |
| Memory pressure | allocation behavior near runtime reserve limits |
| Metal | command-buffer overhead for small no-op and fused-shape kernels |

## First Target Commands

Loopback smoke on one host:

Worker B:

```bash
zig build run-worker -- --node B --listen 127.0.0.1:7555
```

Worker C:

```bash
zig build run-worker -- --node C --listen 127.0.0.1:7556
```

Coordinator:

```bash
zig build run-coordinator -- \
  --config configs/cluster.loopback.toml \
  --scenario benchmarks/scenarios/loopback_transport_smoke.toml \
  --out artifacts/runs/loopback-smoke
```

Real A/B/C cluster smoke after copying `configs/cluster.local.example.toml`
to an untracked local config and replacing placeholder hostnames:

Worker B:

```bash
zig build run-worker -- --node B --listen 0.0.0.0:7555
```

Worker C:

```bash
zig build run-worker -- --node C --listen 0.0.0.0:7556
```

Coordinator:

```bash
zig build run-coordinator -- \
  --config configs/cluster.local.toml \
  --scenario benchmarks/scenarios/qwen3_moe_transport_smoke.toml \
  --out artifacts/runs/transport-smoke
```

These are target commands for the first coding milestone.

## Expected Artifacts

The coordinator should produce:

- `artifacts/runs/<run-id>/run.json`;
- `artifacts/runs/<run-id>/events.jsonl`;
- `artifacts/runs/<run-id>/latency.csv`;
- `artifacts/runs/<run-id>/throughput.csv`;
- `artifacts/runs/<run-id>/summary.md`.

Generated run artifacts are ignored by git.

## Failure Handling

If a worker disappears, the coordinator must log:

- node ID;
- last heartbeat time;
- in-flight scenario step;
- bytes sent and acknowledged;
- retry count;
- timeout duration;
- whether the run is still valid.

If the network silently falls back to a slower path, the run must be marked invalid until the path is confirmed.

## Go/No-Go Decision

Proceed to model metadata and placement simulation only after transport artifacts show a reproducible operating envelope.

If the measured envelope is weak, publish the limit and revise the architecture before implementing transformer code.
