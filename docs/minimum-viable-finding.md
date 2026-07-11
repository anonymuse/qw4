# Minimum Viable Technical Finding

Status: first publishable milestone definition.

Backlog tracking: [DS5-F000 Phase 0 Transport Finding](backlog/feature-000-phase0-transport-finding.md).

## Sharp Question

Can an M5 Pro orchestrator agent keep two M5 Max synthetic LLM data-plane workers fed with Qwen3-shaped activation/result traffic without transport, scheduling, or control-plane overhead dominating decode-shaped work?

## Why This Is The First Finding

The full model does not need to be loaded to test the first hard dependency: physical transfer, orchestration, and control-plane cost.

If transport and scheduling fail under synthetic Qwen-shaped traffic, full transformer work should stop or pivot. If they pass, the project earns the right to proceed toward metadata inspection, placement simulation, and worker runtime prototypes.

## Scope

The milestone simulates:

- Node A as coordinator/orchestrator, benchmark controller, and control plane;
- Nodes B and C as synthetic LLM data-plane workers;
- 94 layers;
- hidden size 4096;
- top-8 selected experts per MoE layer;
- B owns layers 0-46;
- C owns layers 47-93;
- one activation packet per destination node per layer;
- configurable local versus remote expert rates;
- configurable block sizes for activation/result traffic;
- worker health and trace reporting.

The milestone does not implement:

- tokenizer;
- attention kernels;
- actual expert matmul;
- real Qwen weights;
- quantized model loading;
- KV allocator or real long-context management;
- speculative decoding;
- fused routing;
- Metal kernels;
- tool-call decoding.

Model-independent SSD/NVMe measurements are allowed only as separate adjunct
evidence for future cold backing, promotion, artifacts, or long-context backing.
They do not decide the Phase 0 go/no-go unless a separate storage-readiness task
is created and labeled independently.

## Proposed Commands

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

For the full target-hardware operator sequence, use
[DS5-F000 Cluster Operator Packet](runbooks/ds5-f000-cluster-operator-packet.md).

## Required Output

Each run should produce:

- `run.json`;
- `events.jsonl`;
- `latency.csv`;
- `throughput.csv`;
- `summary.md`.

## Metrics

Required metrics:

- node discovery latency;
- worker health status;
- p50/p95/p99 round-trip latency by message size;
- sustained throughput by block size;
- checksum failures;
- scheduler overhead per simulated token;
- control-plane overhead per simulated token;
- bytes sent per simulated token;
- per-layer simulated transport time;
- concurrent A-B and A-C link interference;
- reconnect behavior;
- predicted upper-bound tokens/sec by remote-expert-rate scenario.

## Success

The milestone succeeds if it produces repeatable A/B/C runs with checksummed transfers, machine-readable artifacts, and a clear curve showing where transport cost is tolerable or intolerable for decode-shaped traffic.

## Failure

The milestone fails if:

- the link is unstable;
- latency jitter dominates small messages;
- throughput collapses under concurrent links;
- checksummed block movement cannot be made repeatable;
- coordinator scheduling overhead is material compared with transfer time;
- reconnect and worker failure behavior cannot be traced.

Failure is still useful if the artifacts clearly show why the architecture should pivot.

## Decision Unlocked

After this milestone, decide one of:

- proceed to model metadata and placement simulation;
- redesign packetization and scheduling;
- reduce remote expert movement assumptions;
- abandon distributed decode as the first public finding and publish the measured limit.
