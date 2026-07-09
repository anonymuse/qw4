# Feature DS5-F001A: Placement Contract Hardening

Status: next feature work; current DS5-F001 scaffold partially satisfies this goal.

Epic: `DS5-E01: Runtime Topology And Placement`

Complexity Score: 5/10 for manifest, validator, tests, and evidence metadata hardening.

PM Validation Gate: `PM-GATE-RT-01: Runtime Placement And Memory-Cap Conformance`

Governing baseline: [DS5 Project Plan After ARB Refresh](project-plan.md), [DS5-F001 Umbrella](feature-001-pdd-topology.md), [DS5 Assumptions](../assumptions.md), and [ADR-002](../decisions/ADR-002-phase0-transport-first.md).

## Technical Scope

Harden the planning placement contract so the repo can safely treat the DS5-F001 scaffold as complete planning evidence before moving to transport or runtime work.

This feature remains scaffold/planning work. It must not claim measured runtime memory, model-load readiness, tokenizer integration, speculative decoding, KV allocator behavior, or Metal-kernel behavior.

Existing implementation signals:

- `configs/qwen3_pdd_topology_phase1.json` defines the Phase 1 placement manifest.
- `src/model/pdd_topology.py` performs semantic validation and ledger generation.
- `tests/model/test_pdd_topology.py` covers valid and invalid placement manifests.
- `make pdd-topology-validate` emits a planning ledger and acceptance summary.

## Rigid Acceptance Criteria

- The Python validator enforces:
  - `model.name == "Qwen3-235B-A22B"`;
  - `model.variant == "Qwen3-235B-A22B-Instruct-2507"`;
  - `model.layers == 94`;
  - `model.experts == 128`;
  - `model.active_experts == 8`.
- Invalid tests cover wrong model name, wrong variant, wrong expert count, and wrong active expert count.
- The manifest and generated ledger include machine-readable memory-accounting evidence metadata that states byte values are placeholder cap tests unless measured or derived from pinned tensor metadata.
- The manifest and generated ledger include a planning-only context-length assumption.
- The manifest and generated ledger include tensor-class policy placeholders for router/gate, attention, hot MoE experts, cold MoE experts, and KV cache.
- The manifest encodes runtime path constraints that keep Node A off the steady-state decode critical path outside correctness mode.
- The docs state that JSON Schema validation is structural and the Python validator is the authoritative semantic gate for Phase 1 placement invariants.
- `make test` and `make pdd-topology-validate` pass.

## PM Validation Evidence

The merge request must attach or reference:

- updated manifest fixture;
- updated generated ledger;
- updated generated human-readable summary;
- unit-test output showing model-constant mismatch failures;
- command output for `make test` and `make pdd-topology-validate`.

## Merge Blockers

- Any model identity, expert-count, or active-expert mismatch that passes validation.
- Any byte bucket that can be mistaken for measured or derived Qwen tensor placement.
- Any Node A runtime-path language that permits steady-state per-layer decode routing in performance mode.
- Any doc that treats current scaffold evidence as startup, warmup, or full-runtime proof.
