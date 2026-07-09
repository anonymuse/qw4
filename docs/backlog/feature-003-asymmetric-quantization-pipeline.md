# Feature DS5-F003: Asymmetric Quantization Pipeline

Status: deferred until placement-contract and Phase 0 transport gates justify deeper runtime work; Python planning and memory estimation exist, Zig runtime goal not met.

Epic: `DS5-E03: Quantization And Memory Runtime`

Complexity Score: 8/10 for Zig 1.0 bare-metal implementation difficulty.

PM Validation Gate: `PM-GATE-QNT-01: Quantization Envelope And Quality-Drift Evidence`

Governing baseline: `DS5_Model_Runtime_Placement_Spec_v0.2_Qwen3_235B_A22B.md`, `DS5_Benchmark_and_Acceptance_Spec_v0.2_Qwen3_235B_A22B.md`, [DS5 Assumptions](../assumptions.md), [Risk Register](../risk-register.md), and [Project Plan After ARB Refresh](project-plan.md).

## Technical Scope

Build Zig memory allocators and placement manifests that support heterogeneous precision by tensor class:

- Attention layers must be locked to Q8_0 or FP8-E4M3 unless a PM-approved ADR changes the accepted precision class.
- Gating routers must be locked to Q8_0 or FP8-E4M3 to prevent routing drift.
- MoE routed experts must support aggressive quantization targets of IQ2_XXS or BitNet-class approximately 2.06 bpw.
- Allocators must account for quantized payload bytes, scale/metadata bytes, alignment waste, Metal heap overhead, transport staging, and KV cache pressure.
- The pipeline must refuse a manifest that fits only by undercounting scales, metadata, alignment, duplicated tensors, or runtime reserves.
- Quality-drift validation must be part of the gate. Memory fit alone is insufficient.

Existing implementation signals:

- `configs/qwen3_235b_a22b_planning.json` contains planning quantization classes for FP16, Q8 planning, and IQ2 planning.
- `src/model/qwen3_memory.py` and `tools/quant/estimate_qwen3_memory.py` estimate planning memory.
- No Zig allocator, quantized tensor loader, calibration path, or model-quality validation harness exists yet.

## Rigid Acceptance Criteria

- Attention tensors and gating/router tensors must be rejected if encoded below Q8_0 or FP8-E4M3 without an explicit PM-approved override.
- Expert tensors must support IQ2_XXS or BitNet-class approximately 2.06 bpw manifests, including scales and metadata in memory accounting.
- Active token memory reads on compute nodes must not exceed approximately 3.66GB per step in the acceptance profile.
- The 3.66GB read envelope must be measured on B and C independently and reported by tensor class.
- Allocator telemetry must separate resident weights, hot expert weights, cold promotion buffers, KV cache, Metal heaps, transport rings, scratch, metadata, and fragmentation.
- The manifest validator must fail closed on unknown quantization classes, missing scale metadata, impossible alignment, or per-node memory overage.
- Router output equivalence tests must compare Q8_0 or FP8-E4M3 gating against an approved higher-precision reference on fixed prompts.
- Expert quality tests must report drift for IQ2_XXS or BitNet-class experts against a higher-precision reference before merge.

## PM Validation Evidence

The merge request must attach or reference:

- quantization manifest fixtures for attention, router, and expert tensors;
- allocator memory ledger showing all payload and metadata classes;
- per-step active-read measurements proving the 3.66GB envelope;
- router equivalence report;
- expert quality-drift report;
- tests for manifest rejection and allocator reserve enforcement.

## Merge Blockers

- Any memory estimate that excludes scales, metadata, alignment, duplicated tensors, KV cache, Metal heaps, transport buffers, or OS/runtime reserve.
- Any low-bit router or gate quantization without PM-approved evidence.
- Any claim that IQ2 or BitNet quality is acceptable before quality-drift measurements exist.
- Any acceptance profile that only proves fit on aggregate 144GB memory rather than per-node caps.
