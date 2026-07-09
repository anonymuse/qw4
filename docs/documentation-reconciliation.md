# Documentation Reconciliation

Status: active DS5 baseline reconciliation.

## Active Baseline Documents

The Qwen3 update pack is the current source of project intent, subject to the clarifications in this repository.

| Source document | Status |
|---|---|
| `ADR_001_Model_Selection_Qwen3_235B_A22B.md` | Accepted source for model selection |
| `DS5_Project_Spec_v0.2_Qwen3_235B_A22B.md` | Active planning baseline |
| `DS5_System_Architecture_v0.2_Qwen3_235B_A22B.md` | Active planning baseline, pending Phase 0 measurements |
| `DS5_Model_Runtime_Placement_Spec_v0.2_Qwen3_235B_A22B.md` | Active runtime and placement baseline |
| `DS5_Benchmark_and_Acceptance_Spec_v0.2_Qwen3_235B_A22B.md` | Active benchmark gate baseline |
| `DS5_Risk_Register_v0.2_Qwen3_235B_A22B.md` | Active risk seed |
| `DS5_Execution_Plan_Input_v0.2_Qwen3_235B_A22B.md` | Active backlog seed, but first week is narrowed in this repo |
| `DS5_README_Qwen3_Document_Update_Pack.md` | Active documentation index |

## Documents Requiring Update Or Archive

| Document | Problem | Required action |
|---|---|---|
| `DS5_Composite_Architecture_Planning_Model.md` | Uses "Qwen3-235B-A22B-class" language instead of exact model lock | Update to `Qwen3-235B-A22B-Instruct-2507`, import ADR-001 and risk IDs, mark Phase 0 measurements as unresolved |
| `JW4_project_brief.md` | Gemma, two-node, learning-engine scope | Archive as precursor or split as separate project; do not treat as active DS5 target |
| `ChatGPT DS5 Analysis.md` | Source analysis rather than execution baseline | Archive as model-selection source and link from ADR-001 |
| `Deepseek DS5 Analysis.md` | Recommends DeepSeek-V3/R1 as target | Archive as alternative study; retain PDD and expert-locality ideas only |
| `Gemini DS5 Analysis.md` | Recommends conflicting static expert split / Mixtral path | Archive as alternative study; retain diagrams only if corrected |
| `Gemini Project Spec.md` | Contains speculative or invalid runtime claims | Archive as speculative draft; do not use as execution baseline |
| `Z.AI DS5 Analysis.md` | Recommends Mixtral but flags streaming risk | Archive; retain warning about per-token expert streaming |

## Specific Quarantine Notes

The Gemini-derived material contains several ideas that must not enter implementation without a new ADR:

- topology-aware routing that changes model top-k semantics;
- claimed `<8us` network synchronization target before measurement;
- pooled 144GB memory language;
- 94 percent hot-expert pinning claim;
- BitNet/IQ2 safety claims;
- O_DIRECT-style macOS storage claims;
- 1M token fuzz target;
- early `>12 tok/s` target treated as guaranteed.

## Still Useful From DS4/JW4

The earlier framing remains useful where it reinforces:

- specialization over generality;
- measurement before abstraction;
- manifests and explicit configuration;
- benchmark-first engineering;
- small runnable milestones;
- traceable failure modes;
- local-first execution;
- solo-builder scope discipline.

It is stale where it implies Gemma, two-node execution, generalized inference, or learning-engine acceptance criteria.

## Active DS5 Source Of Truth

DS5 is a narrow Qwen3-235B-A22B local distributed inference project for a three-node Apple Silicon cluster.

The first implementation path validates transport, scheduling, and simulated MoE movement before loading the full transformer.

