# Feature DS5-F001: Prefill/Decode Disaggregation (PDD) Topology

Status: in progress as planning constants only; runtime goal not met.

Epic: `DS5-E01: Runtime Topology And Placement`

Complexity Score: 8/10 for Zig 1.0 bare-metal implementation difficulty.

PM Validation Gate: `PM-GATE-RT-01: Runtime Placement And Memory-Cap Conformance`

Governing baseline: `DS5_Model_Runtime_Placement_Spec_v0.2_Qwen3_235B_A22B.md`, [DS5 Assumptions](/Users/jessewhite/.codex/worktrees/c9a3/qw4/docs/assumptions.md), and [ADR-002](/Users/jessewhite/.codex/worktrees/c9a3/qw4/docs/decisions/ADR-002-phase0-transport-first.md).

## Technical Scope

Implement the DS5 asymmetric cluster split for `Qwen3-235B-A22B-Instruct-2507`:

- Node A, an M5 Pro, acts as the orchestration brain.
- Node A hosts the tokenizer, Q8_0 layer-gating routing tensors, scheduler, health/telemetry control plane, and Qwen2.5-3B speculative drafter.
- Node A is forbidden from owning primary MoE decode weights.
- Node B, an M5 Max, is the static resident owner for attention weights and KV cache pages for layers 0-46.
- Node C, an M5 Max, is the static resident owner for attention weights and KV cache pages for layers 47-93.
- Placement manifests must encode layer ownership, tensor class, quantization class, owner node, residency mode, allocator pool, and per-node memory ledger.
- Runtime startup must fail closed when a manifest violates node ownership, Qwen shape constants, or memory-headroom rules.

Existing implementation signals:

- `src/common/protocol.zig` already pins the 94-layer shape and B/C split.
- `configs/qwen3_235b_a22b_planning.json` already models 48GB nodes, 33.6GB static caps, and 14.4GB runtime reserves.
- No tokenizer, speculative drafter, primary-weight loader, KV allocator, or runtime memory auditor exists yet.

## Rigid Acceptance Criteria

- Node A allocates exactly 0 bytes to primary MoE decode weights. This must be proven by a runtime memory ledger emitted at startup and after warmup.
- Node A may allocate tokenizer, routing tensors, speculative drafter, telemetry, transport, scheduler, and scratch buffers only if the allocation class is explicitly identified as non-primary MoE decode weight.
- Node B owns layers 0-46 attention weights and KV cache pages; Node C owns layers 47-93 attention weights and KV cache pages.
- Nodes B and C each maintain at least 30% UMA memory headroom, equal to 14.4GB on a 48GB worker, throughout startup, warmup, and the acceptance benchmark.
- Per-worker static residency must stay at or below 33.6GB unless an override is explicit, recorded, and approved by the PM gate.
- Placement tests must reject any manifest that assigns B-owned layers to C, C-owned layers to B, or primary MoE decode weights to Node A.
- The PDD implementation must preserve exact Qwen top-8 routing semantics and must not introduce topology-aware routing substitutions.
- Completion evidence must include machine-readable placement and memory artifacts, plus a human-readable summary that separates measured results from assumptions.

## PM Validation Evidence

The merge request must attach or reference:

- placement manifest fixture and runtime-loaded manifest;
- `memory_ledger.json` or equivalent per-node allocation artifact;
- worker startup logs proving B/C ownership split;
- Node A allocation report showing 0 primary MoE decode bytes;
- benchmark artifacts required by the DS5 acceptance baseline: `run.json`, `events.jsonl`, `latency.csv`, `throughput.csv`, and `summary.md`;
- tests covering valid and invalid placement manifests.

## Merge Blockers

- Any Node A allocation of primary MoE decode weights.
- Any B/C memory reserve below 30%.
- Any claim that the 144GB cluster behaves as a single shared-memory pool.
- Any route or placement optimization that changes Qwen top-8 expert semantics.

