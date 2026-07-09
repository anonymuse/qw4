# Feature DS5-F004: Asynchronous Rolling Pre-fetch Buffer

Status: not started; runtime goal not met.

Epic: `DS5-E04: Cold Expert Promotion`

Complexity Score: 10/10 for Zig 1.0 bare-metal implementation difficulty.

PM Validation Gate: `PM-GATE-PF-01: Storage Promotion And Cold-Miss Latency-Hiding Evidence`

Governing baseline: `DS5_Model_Runtime_Placement_Spec_v0.2_Qwen3_235B_A22B.md`, `DS5_System_Architecture_v0.2_Qwen3_235B_A22B.md`, [DS5 Assumptions](/Users/jessewhite/.codex/worktrees/c9a3/qw4/docs/assumptions.md), and [Risk Register](/Users/jessewhite/.codex/worktrees/c9a3/qw4/docs/risk-register.md).

## Technical Scope

Implement the Zig orchestrator and worker support for the DS5 routing entropy heatmap and rolling prefetch buffer:

- Track expert hotness from observed routing distributions without changing Qwen top-8 semantics.
- Pin the 94% hot expert set in UMA memory for the active workload profile.
- Treat remaining cold experts as local NVMe-backed promotion candidates, not as steady-state active decode dependencies.
- Stream cold experts into a rotating VRAM/Metal buffer 7 to 8 tokens ahead of execution when a cold expert probability crosses 5%.
- Use asynchronous I/O and direct-I/O semantics for cold expert promotion.
- Report promotion hits, misses, late arrivals, evictions, and decode stalls in benchmark artifacts.

Important baseline constraint:

The repo-visible assumptions quarantine both the 94% hot-expert pinning claim and Linux-like `O_DIRECT` expectations on macOS until measured. This feature remains mandatory in the backlog, but it cannot merge until the storage and hotness claims have acceptance evidence or an approved ADR narrows the platform contract.

## Rigid Acceptance Criteria

- The runtime must maintain a routing entropy heatmap keyed by layer, expert ID, workload profile, and recent token window.
- The hot set must pin 94% of predicted active expert demand in UMA memory for the acceptance workload.
- If a cold expert's predicted probability crosses 5%, the expert must be scheduled for promotion into a rotating VRAM/Metal buffer 7 to 8 tokens ahead of execution.
- The promotion path must use `io.async` and `O_DIRECT` or a PM-approved platform equivalent that proves direct-I/O semantics on the target acceptance hardware.
- Cold expert promotion must fully hide I/O latency in the acceptance benchmark: promoted expert readiness must precede execution with zero decode stall attributed to storage.
- The implementation must emit per-expert promotion timing, promotion lead distance, bytes read, storage latency, buffer residency, eviction reason, and stall counters.
- The steady-state hot decode path must remain resident in UMA memory and must not depend on NVMe per token.
- Acceptance tests must include hot-set stability, cold-probability threshold crossing, promotion cancellation, buffer rotation, late I/O, checksum failure, and storage backpressure.

## PM Validation Evidence

The merge request must attach or reference:

- routing entropy heatmap artifact for the acceptance workload;
- hot/cold expert residency ledger;
- storage benchmark artifacts for 16MiB, 64MiB, 128MiB, and 256MiB block sizes;
- promotion trace proving 7 to 8 token lead distance;
- stall report proving hidden I/O latency under the acceptance scenario;
- platform note proving `O_DIRECT` availability or the approved equivalent.

## Merge Blockers

- Any implementation that streams active hot-path weights from NVMe during steady-state decode.
- Any hotness claim that is not tied to measured routing traces.
- Any use of buffered filesystem I/O presented as `O_DIRECT` without PM-approved platform evidence.
- Any cold expert promotion that causes decode stalls in the acceptance scenario.

