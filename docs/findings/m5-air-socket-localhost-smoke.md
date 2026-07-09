# M5 Air Socket-Localhost Smoke Finding

Status: local M5 Air socket-localhost result.
Date: 2026-07-09.

## Scope

This finding records a two-worker, multi-process TCP smoke on the MacBook Air M5 after PR #2 merged to `main`.

This is still local-only. It validates process boundaries, localhost TCP worker IO, artifact reporting, aggregation, and Qwen-shaped simulation plumbing. It is not Thunderbolt cluster evidence, not worker-node performance, and not final model inference performance.

## Source Under Test

| Field | Value |
|---|---|
| Repository | `https://github.com/anonymuse/qw4.git` |
| Branch used | `agent/socket-localhost-smoke` from `origin/main` |
| Exact code commit tested | `dabe268153a9fd663d3a0ef7ba61bf157000b23d` |
| Source event | Merge commit for PR #2 |
| Run artifact ID | `m5-air-socket-localhost-smoke` |
| Artifact schema | `phase0.artifacts.v1` |

## Commands

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
make socket-smoke RUN_ID=m5-air-socket-localhost-smoke
```

Validation and reporting:

```bash
python3 -B tools/report/validate_run.py artifacts/runs/m5-air-socket-localhost-smoke
python3 -B tools/report/summarize_phase0.py artifacts/runs/m5-air-socket-localhost-smoke
make qwen-moe-sim RUN_ID=m5-air-socket-localhost-smoke
make aggregate-report
```

## Pass/Fail

| Check | Result | Notes |
|---|---:|---|
| Worker B process | PASS | Completed 550 transfers, 123,122,560 bytes received, 0 checksum failures. |
| Worker C process | PASS | Completed 550 transfers, 123,122,560 bytes received, 0 checksum failures. |
| Coordinator socket smoke | PASS | `mode=socket_localhost`, 1,000 transfers, 223,859,200 bytes sent, 0 checksum failures. |
| Artifact validation | PASS | `artifacts/runs/m5-air-socket-localhost-smoke` conforms to `phase0.artifacts.v1`. |
| Summary report | PASS | Report marks the run loopback-only/non-hardware-interpretable. |
| Qwen MoE simulation helper | PASS | Produced `phase0.qwen_moe_transport_sim.v1` JSON from the socket-localhost source run. |
| Aggregate report | PASS | Listed socket-localhost separately from loopback and real-cluster rows. |

## Artifact Summary

| Field | Value |
|---|---|
| Run ID | `m5-air-socket-localhost-smoke` |
| Git commit in artifact | `dabe268153a9fd663d3a0ef7ba61bf157000b23d` |
| Started | `2026-07-09T13:22:06Z` |
| Ended | `2026-07-09T13:22:10Z` |
| Duration | 4,612 ms |
| Transport mode | `socket_localhost` |
| Socket mode | `tcp_localhost` |
| Network path | `127.0.0.1` |
| Hardware interpretable | `false` |
| Warmup count | 10 |
| Total transfers | 1,000 |
| Bytes sent | 223,859,200 |
| Checksum failures | 0 |
| Failures/retries/reconnects/timeouts | 0 / 0 / 0 / 0 |

Selected socket-localhost latency rows:

| Node pair | Message bytes | p50 us | p95 us | p99 us |
|---|---:|---:|---:|---:|
| A-B | 64 | 39 | 66 | 67 |
| A-B | 1,048,576 | 9,810 | 10,045 | 10,132 |
| A-C | 64 | 42 | 52 | 63 |
| A-C | 1,048,576 | 9,806 | 10,018 | 10,157 |

Selected socket-localhost throughput rows:

| Node pair | Block bytes | Transfers | MiB/s |
|---|---:|---:|---:|
| A-B | 1,048,576 | 100 | 46 |
| A-C | 1,048,576 | 100 | 47 |

These values are localhost TCP regression signals only. They must not be compared to Thunderbolt or real-cluster expectations.

## Qwen-Shaped Simulation Readout

The simulation helper consumed the socket-localhost artifact without loading model weights.

| Remote expert rate | Bytes per simulated token | Transport upper bound tokens/sec |
|---:|---:|---:|
| 0.125 | 1,540,096 | 32.0 |
| 0.25 | 3,080,192 | 16.0 |
| 0.5 | 6,160,384 | 8.0 |
| 0.75 | 9,240,576 | 5.33 |
| 1.0 | 12,320,768 | 4.0 |

This is a non-hardware simulation derived from localhost measurements. It helps exercise the reporting shape and highlights sensitivity to remote expert traffic, but it is not an inference or cluster-capacity claim.

## Actionable Findings

1. The socket-localhost path works across separate worker processes and still validates under `phase0.artifacts.v1`.
2. The artifact correctly distinguishes `socket_localhost` from `single_process_loopback` and marks `hardware_interpretable=false`.
3. The validator rejects hardware interpretation for localhost-class paths, which reduces the risk of accidental performance overclaiming.
4. The aggregate report now gives a useful local comparison row while preserving the warning that loopback/socket-localhost rows are non-hardware data.
5. The next real blocker is not repo plumbing; it is a measured non-local A-B/A-C transport run with confirmed network path.

## What This Does Not Prove

- It does not prove Thunderbolt Bridge performance.
- It does not prove final three-node M5 Pro/M5 Max behavior.
- It does not prove worker-node throughput under real interconnect conditions.
- It does not prove model inference performance.
- It does not download or run full Qwen3-235B-A22B weights.

## Next Test

Run the same socket worker/coordinator flow on two actual worker hosts after recording the confirmed network path. The run should remain invalid for hardware claims until `environment.hardware_interpretable=true` is backed by a non-local path and the artifact records that path explicitly.
