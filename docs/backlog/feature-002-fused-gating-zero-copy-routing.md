# Feature DS5-F002: Fused Gating And Zero-Copy Routing Protocol

Status: blocked. `DS5-F001A: Placement Contract Hardening` is complete via PR #19, but `DS5-F000: Phase 0 Transport Finding` must still support continued distributed decode work before fused routing starts.

Epic: `DS5-E02: Routing Transport`

Complexity Score: 9/10 for Zig 1.0 bare-metal implementation difficulty.

PM Validation Gate: `PM-GATE-TR-01: Thunderbolt Block-Routing Transport Evidence`

Governing baseline: `DS5_Benchmark_and_Acceptance_Spec_v0.2_Qwen3_235B_A22B.md`, [Minimum Viable Finding](../minimum-viable-finding.md), [ADR-002](../decisions/ADR-002-phase0-transport-first.md), and [DS5-F000](feature-000-phase0-transport-finding.md).

## Technical Scope

After the prerequisite gates complete, develop the DS5 Thunderbolt 5 routing interface so Node A avoids layer-by-layer network roundtrips during decode-shaped MoE traffic:

- Node A evaluates block routing sequences concurrently.
- Node A emits one compact routing packet per block and destination set instead of synchronous per-layer control messages.
- Nodes B and C consume the compact packet and schedule local work from the embedded routing sequence.
- The future transport layer exposes measured copy-count telemetry, buffer ownership, checksum behavior, and per-block synchronization timing.
- The protocol must support both correctness mode and future local-router mirror validation without changing Qwen top-8 semantics.

Existing implementation signals:

- `src/transport/root.zig` contains Phase 0 frame/transport machinery.
- `benchmarks/scenarios/qwen3_moe_transport_smoke.toml` contains synthetic Qwen-shaped traffic.
- Phase 0 routing-payload schema fixtures may validate Qwen-shaped record assumptions for `DS5-F000`, but they are preparatory schema/test artifacts only.
- Phase 0 zero-copy fields are unmeasured design assumptions; the scaffold explicitly records that measured copy counts are unavailable.
- No Thunderbolt-specific zero-copy implementation or fused routing packet exists yet.

Prerequisite:

- `DS5-F001A` placement-contract hardening is complete via PR #19.
- Complete `DS5-F000` with target-hardware transport artifacts before implementing fused routing.
- Both gates are required. Loopback, local smoke, or routing-payload scaffold results may inform this feature, but they do not unblock it while `DS5-F000` remains incomplete.

## Rigid Acceptance Criteria

- The routing payload structure must strictly follow this record shape:

```text
{
  layer_id,
  active_expert_ids[8],
  weight_coefficients[8],
  target_nodes
}
```

- A block packet may contain a sequence of these records, but every record must preserve the exact field shape above.
- `layer_id` must be validated against the 0-93 Qwen3 layer range.
- `active_expert_ids` must contain exactly 8 expert IDs per routed layer.
- `weight_coefficients` must contain exactly 8 coefficients aligned by index to `active_expert_ids`.
- `target_nodes` must only identify valid DS5 compute workers for this topology: B, C, or both.
- Network synchronization latency must remain below 8 microseconds per block on the acceptance hardware.
- The `<8us` claim must be backed by p50, p95, and p99 measurements, not a local-loopback estimate.
- The implementation must report measured copy counts and prove that the hot path does not introduce avoidable heap-to-heap payload copies; design budgets or schema fields are not telemetry.
- All packet tests must include malformed length, invalid layer, duplicate or out-of-range experts, invalid target node, checksum failure, and replay/out-of-order cases.
- Benchmark artifacts must expose per-message-size latency, block throughput, concurrent A-B/A-C interference, scheduler overhead, and checksum failures.

## PM Validation Evidence

The merge request must attach or reference:

- protocol fixture bytes for valid and invalid fused routing packets;
- hardware run artifacts for A/B/C topology, not loopback-only artifacts;
- p50/p95/p99 per-block sync latency proving `<8us`;
- measured copy-count telemetry from the routing path;
- failure/retry traces in `events.jsonl`;
- updated schema documentation for the fused routing packet.

## Merge Blockers

- Any routing packet that omits or renames required payload fields.
- Any block sync result at or above 8 microseconds without a PM-approved scope change or ADR.
- Any performance claim based only on localhost, synthetic sleep timing, or unchecked payloads.
- Any routing shortcut that changes Qwen top-8 semantics to fit topology.
- Any use of Phase 0 routing-payload scaffold fields as measured copy-count telemetry or fused-routing runtime evidence.
