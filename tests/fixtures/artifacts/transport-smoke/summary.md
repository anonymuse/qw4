# transport-smoke

## Run

- run_id: transport-smoke
- git_commit: cb71e857564818e292967c1b94eac13979f335a1
- started_at: 2026-07-09T03:00:00Z
- ended_at: 2026-07-09T03:00:05Z
- valid: true
- data kind: synthetic fixture, not real cluster data

## Scenario

- scenario: qwen3_moe_transport_smoke
- message sizes: 4096, 16384, 65536, 1048576 bytes
- block sizes: 1048576, 4194304 bytes
- transfer count: 40
- warmup count: 4
- checksum mode: sha256
- Qwen shape: 94 layers, hidden size 4096, top-k 8, one packet per destination node per layer

## Nodes

- node roles: A coordinator fixture-a, B worker fixture-b, C worker fixture-c
- layer ownership: B owns layers 0-46, C owns layers 47-93
- transport: synthetic-loopback

## Latency

| node_pair | message_size_bytes | p50 | p95 | p99 |
|---|---:|---:|---:|---:|
| A-B | 4096 | 240.0 us | 310.0 us | 355.0 us |
| A-C | 4096 | 245.0 us | 318.0 us | 366.0 us |
| A-B | 1048576 | 2150.0 us | 2480.0 us | 2710.0 us |
| A-C | 1048576 | 2190.0 us | 2525.0 us | 2765.0 us |

## Throughput

| node_pair | block_size_bytes | throughput |
|---|---:|---:|
| A-B | 1048576 | 476.19 MiB/s |
| A-C | 1048576 | 459.77 MiB/s |
| A-B | 4194304 | 551.72 MiB/s |
| A-C | 4194304 | 529.8 MiB/s |

Concurrent-link interference at 4194304 bytes was 7.56 percent on A-B and
6.0 percent on A-C in the synthetic fixture.

## Reliability

- checksum failures: 0
- failures: 1
- retries: 1
- reconnects: 1
- timeouts: 0
- retry event: C heartbeat_gap recovered after one retry

## Interpretation

This fixture proves the artifact contract, not the hardware result. Predicted
upper-bound tokens/sec by remote-expert-rate scenario:

| remote_expert_rate | predicted upper-bound tokens/sec |
|---:|---:|
| 0.0 | 24.0 |
| 0.25 | 16.5 |
| 0.5 | 11.2 |
| 0.75 | 8.1 |
| 1.0 | 6.0 |
