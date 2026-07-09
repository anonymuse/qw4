# ADR-002: Make Transport And Runtime Physics The First Milestone

Status: accepted.

Date: 2026-07-09.

## Context

DS5 depends on a local Apple Silicon cluster connected by a high-speed Thunderbolt/RDMA-style interconnect. The project can fail before model loading if inter-node latency, throughput, synchronization, copy behavior, or worker failure behavior is incompatible with decode-shaped MoE traffic.

The project also risks wasting time on transformer code before proving that the physical cluster can support the intended execution pattern.

## Decision

The first coding milestone will be a transport and simulated-MoE benchmark, not a model runtime.

It will measure:

- node discovery;
- ping/pong latency;
- block transfer throughput;
- concurrent link behavior;
- checksummed activation/result packet movement;
- worker health reporting;
- scheduler overhead;
- simulated Qwen3-shaped MoE routing traces.

It will not load full Qwen3 weights or implement the transformer.

## Rationale

This milestone is the smallest credible technical finding. It can produce a useful result even if the result is negative.

If transport costs dominate synthetic Qwen-shaped activation movement, full runtime work should pivot before kernel development.

If the transport profile is promising, the project can proceed to model metadata inspection, placement simulation, and worker runtime prototypes with evidence.

## Required Artifacts

Each benchmark run must emit:

- `run.json`;
- `events.jsonl`;
- `latency.csv`;
- `throughput.csv`;
- `summary.md`.

Each run must record:

- git commit;
- hostnames and node roles;
- software version;
- scenario config;
- message sizes;
- transfer counts;
- checksums;
- p50/p95/p99 latency;
- throughput;
- failure/retry events.

## Consequences

The first week prioritizes cluster validation, benchmark artifacts, and simulated routing over model loading.

The project should not start Qwen kernel optimization until this milestone produces a clear go/no-go result.

