# DS5 Assumptions

Status: planning baseline, pending Phase 0 measurement.

Source pack date: 2026-07-08. Local baseline created: 2026-07-09.

## Authoritative Model Target

The DS5 target model is `Qwen3-235B-A22B`.

The first runtime target is `Qwen3-235B-A22B-Instruct-2507`.

The `Qwen3-235B-A22B-Thinking-2507` variant is deferred until the non-thinking instruct path is correct, measurable, and stable.

Bring-up and comparison models are allowed only when explicitly marked as one of:

- bring-up target;
- benchmark comparator;
- fallback runtime;
- archived alternative.

They are not the DS5 final target.

## Hardware Assumptions

| Node | Role | Hardware | Memory | Runtime stance |
|---|---|---|---:|---|
| A | Coordinator / orchestrator | MacBook Pro M5 Pro | 48GB UMA | Control plane, scheduler, state, routing policy, telemetry, benchmark control, limited compute |
| B | Primary worker | MacBook Pro M5 Max | 48GB UMA | Decode worker, layer ownership, expert execution, KV ownership |
| C | Primary worker | MacBook Pro M5 Max | 48GB UMA | Decode worker, layer ownership, expert execution, KV ownership |
| Optional minis | Support | Mac mini | 16GB UMA | Telemetry, dashboards, runners, logging, synthetic load |
| Optional RTX box | Auxiliary | RTX 5080 FE, AMD 9700X, 64GB RAM | 64GB RAM | Preprocessing, quantization experiments, reference comparisons |

The cluster has 144GB raw memory, but DS5 must not treat that as one shared memory pool.

The planning static-weight cap is:

```text
48GB * 0.70 = 33.6GB static cap per node
48GB * 0.30 = 14.4GB runtime reserve per node
144GB * 0.70 = 100.8GB aggregate static planning cap
```

The runtime reserve covers KV cache, Metal heaps, staging buffers, transport rings, allocator fragmentation, OS overhead, telemetry, and promotion scratch.

## Model Assumptions

| Dimension | Planning value |
|---|---:|
| Total parameters | 235B |
| Activated parameters | 22B |
| Layers | 94 |
| Experts | 128 |
| Activated experts | 8 |
| Hidden size | 4096 |
| Attention heads | 64 Q heads |
| KV heads | 4 KV heads |
| Head dimension | 128 |
| First performance context | 8K-32K |
| Stretch context | 64K |
| Research-only context | 128K-262K |

These values must be verified against pinned model artifact metadata before any final placement claim.

## Runtime Invariants

- Preserve exact Qwen top-8 routing semantics.
- Use placement, caching, and promotion for locality; do not alter routing to force locality.
- Keep router and gate tensors FP16 or Q8 until evidence supports anything lower.
- Keep the steady-state decode hot path resident in unified memory.
- Use NVMe for cold backing, promotion, prefetch, long-context backing, and artifacts, not normal active-weight decode.
- Start with Node A correctness routing only as a validation mode.
- Move performance routing to B/C local router mirrors after correctness is proven.
- Emit benchmark data in machine-readable formats.
- Refuse manifests that exceed static caps unless an override is explicit and recorded.

## Invalid Assumptions

These assumptions are stale or forbidden:

- DS5 is a general-purpose inference runtime.
- DS5 supports arbitrary model plugins in the first implementation.
- Qwen3 can be safely replaced by Gemma, DeepSeek, GLM, Mixtral, or dense 70B targets.
- The Apple Silicon cluster forms a true 144GB shared-memory machine.
- Thunderbolt 5 behaves like magic RDMA without copies, jitter, or OS overhead.
- Per-token expert streaming from NVMe is acceptable in the steady-state decode path.
- Topology-aware routing may change Qwen expert selection.
- BitNet/IQ2-heavy quantization is safe without quality evidence.
- `O_DIRECT` or Linux-like storage controls can be assumed on macOS.
- 128K, 262K, 1M token, or `>12 tok/s` claims are credible before benchmark artifacts exist.

## Measurements Required Before Runtime Claims

| Assumption | Required Phase 0 evidence |
|---|---|
| Thunderbolt latency | p50/p95/p99 by message size and link pair |
| Thunderbolt throughput | sustained bandwidth by block size and concurrent link pattern |
| Copy behavior | user/kernel copy overhead, memory allocation behavior, and checksum cost |
| Worker stability | long-running worker health and reconnect behavior |
| macOS storage path | sequential throughput and cache behavior for 16/64/128/256MiB blocks |
| Metal overhead | command-buffer overhead for small and fused kernels |
| UMA pressure | allocation, fragmentation, and memory-pressure behavior near reserve limits |

