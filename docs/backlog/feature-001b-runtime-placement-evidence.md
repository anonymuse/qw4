# Feature DS5-F001B: Runtime Placement Evidence

Status: queued after `DS5-F001A` and the Phase 0 transport go/no-go.

Epic: `DS5-E01: Runtime Topology And Placement`

Complexity Score: 8/10 for runtime startup integration, measured ledgers, and worker ownership logs.

PM Validation Gate: `PM-GATE-RT-01: Runtime Placement And Memory-Cap Conformance`

Governing baseline: [DS5 Project Plan After ARB Refresh](project-plan.md), [DS5-F001 Umbrella](feature-001-pdd-topology.md), and [DS5-F000](feature-000-phase0-transport-finding.md).

## Technical Scope

Convert the hardened placement contract into runtime evidence: startup and warmup should load the placement manifest, emit measured allocation ledgers, and prove Node A/B/C ownership behavior.

This feature is still not approval for full model loading, tokenizer integration, speculative decoding, prefetch, or Metal kernels unless separate feature gates explicitly add and measure those systems.

## Rigid Acceptance Criteria

- Runtime startup loads the hardened placement manifest and fails closed on semantic validation errors.
- Startup and warmup emit `memory_ledger.json` or an equivalent machine-readable per-node allocation artifact.
- The ledger separates measured allocations from placeholders and assumptions.
- Node A reports exactly 0 primary MoE decode bytes.
- Node A allocation classes are explicitly limited to non-primary MoE decode roles such as orchestration, routing metadata, telemetry, transport, scheduling, and scratch.
- Worker startup logs prove B owns layers 0-46 and C owns layers 47-93.
- Workers preserve the configured static cap and runtime headroom throughout startup and warmup.
- Completion evidence includes a human-readable summary that separates measured runtime evidence from remaining assumptions.

## PM Validation Evidence

The merge request must attach or reference:

- runtime-loaded manifest;
- startup and warmup memory ledgers;
- worker startup logs proving layer ownership;
- Node A allocation report;
- validation commands and results;
- any benchmark artifacts used to support runtime claims.

## Merge Blockers

- Any Node A primary MoE decode allocation.
- Any B/C memory reserve below the approved cap or headroom requirement.
- Any runtime evidence that silently falls back to a different manifest than the reviewed fixture.
- Any claim that runtime startup evidence proves model quality, tokenizer correctness, fused routing performance, cold-prefetch viability, or Metal-kernel stability.
