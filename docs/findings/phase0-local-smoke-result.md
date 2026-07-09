# Phase 0 Local Smoke Result

Status: local-only scaffold result. This is not a hardware-cluster finding.

## Objective

Establish a reproducible local path from coordinator execution to `phase0.artifacts.v1`
artifacts before spending the next sprint tranche on real cluster measurements.

## Current Local Evidence

The checked-in fixture under `tests/fixtures/artifacts/transport-smoke/` validates
the artifact contract and represents protocol/artifact plumbing only. It must not
be read as Thunderbolt, RDMA-style, or multi-host performance data.

## Local Modes

| Mode | Meaning | Hardware interpretable |
|---|---|---:|
| `single_process_loopback` | Coordinator calls in-process framed protocol path. | no |
| `socket_localhost` | Coordinator talks to separate local worker processes over TCP localhost. | no |
| `real_cluster` | Coordinator talks to non-local worker addresses. Requires confirmed network path. | only when explicitly recorded |

## Reproduction

```bash
make test
make loopback-smoke RUN_ID=phase0-local-loopback
make validate-artifacts RUN_ID=phase0-local-loopback
make summarize-report RUN_ID=phase0-local-loopback
```

For socket-localhost, run the two worker commands from `make socket-workers` in
separate terminals, then:

```bash
make socket-smoke RUN_ID=phase0-socket-localhost
make validate-artifacts RUN_ID=phase0-socket-localhost
```

## Real-Cluster Placeholders

| Result | Artifact run | Status |
|---|---|---|
| A-B confirmed path | TBD | not run |
| A-C confirmed path | TBD | not run |
| Concurrent A-B/A-C | TBD | not run |
| Qwen-shaped MoE simulation from real transport | TBD | not run |

## Negative Finding Policy

A negative local or real-cluster result is first-class if artifacts identify the
limiting factor: checksum failures, worker timeouts, reconnect instability,
throughput collapse, latency jitter, or coordinator overhead. The next action is
then redesign or pivot, not transformer implementation.
