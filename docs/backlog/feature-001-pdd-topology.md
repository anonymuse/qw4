# Feature DS5-F001: Prefill/Decode Disaggregation (PDD) Topology

Status: umbrella feature split after ARB feedback.

Epic: `DS5-E01: Runtime Topology And Placement`

Complexity Score: 8/10 for full runtime conformance; subfeature complexity is tracked separately.

PM Validation Gate: `PM-GATE-RT-01: Runtime Placement And Memory-Cap Conformance`

Governing baseline: `DS5_Model_Runtime_Placement_Spec_v0.2_Qwen3_235B_A22B.md`, [DS5 Assumptions](../assumptions.md), [ADR-002](../decisions/ADR-002-phase0-transport-first.md), and [Project Plan After ARB Refresh](project-plan.md).

## ARB Split

The ARB refresh accepted the current DS5-F001 work as scaffold/planning evidence, not runtime evidence.

DS5-F001 is therefore split into:

| Subfeature | Status | Purpose |
|---|---|---|
| [DS5-F001A: Placement Contract Hardening](feature-001a-placement-contract-hardening.md) | next feature work | Finish the manifest, semantic validator, invalid tests, and planning-evidence metadata. |
| [DS5-F001B: Runtime Placement Evidence](feature-001b-runtime-placement-evidence.md) | queued after F001A and Phase 0 transport go/no-go | Prove runtime startup and warmup memory ledgers plus worker ownership logs. |

Current implementation satisfies part of F001A. It does not satisfy F001B.

## Technical Scope

Implement the DS5 asymmetric cluster split for `Qwen3-235B-A22B-Instruct-2507`:

- Node A, an M5 Pro, acts as the orchestration brain.
- Node A may host tokenizer, routing metadata, scheduler, health/telemetry control plane, transport, and correctness-mode routing support only when those allocations are explicitly identified as non-primary MoE decode weight.
- Node A is forbidden from owning primary MoE decode weights.
- Node A must not become the steady-state per-layer decode routing critical path in performance mode.
- Node B, an M5 Max, is the static resident owner for layers 0-46.
- Node C, an M5 Max, is the static resident owner for layers 47-93.
- Placement manifests must encode layer ownership, tensor class, quantization class, owner node, residency mode, allocator pool, memory ledger, evidence metadata, context-length assumption, and runtime path constraints.
- Runtime startup must fail closed when a manifest violates node ownership, Qwen shape constants, or memory-headroom rules.

Existing implementation signals:

- `configs/qwen3_pdd_topology_phase1.json` defines a placement manifest fixture.
- `src/model/pdd_topology.py` performs semantic validation and ledger generation.
- `tests/model/test_pdd_topology.py` covers valid and invalid placement manifests.
- `make pdd-topology-validate` emits scaffold/planning artifacts.
- No tokenizer, speculative drafter, primary-weight loader, KV allocator, runtime memory auditor, or Metal worker runtime exists yet.

## Parent Acceptance Criteria

DS5-F001 is complete only when both subfeatures are complete:

- F001A proves the placement contract is internally auditable as scaffold/planning evidence.
- F001B proves runtime startup and warmup obey the hardened placement contract.

Completion evidence must include machine-readable placement and memory artifacts plus a human-readable summary that separates measured results from assumptions.

## Merge Blockers

- Any Node A allocation of primary MoE decode weights.
- Any B/C memory reserve below the approved cap or headroom requirement.
- Any claim that the 144GB cluster behaves as a single shared-memory pool.
- Any route or placement optimization that changes Qwen top-8 expert semantics.
- Any doc that treats the current scaffold/planning ledger as startup, warmup, or full-runtime proof.
