# DS5 Agile Backlog

Status: active backlog after ARB feedback incorporation.

Created: 2026-07-09.

## Baseline

This backlog codifies the five mandatory composite-architecture pillars as trackable DS5 Features and Epics.

The governing source pack named in [Documentation Reconciliation](../documentation-reconciliation.md) is the master planning baseline:

- `DS5_Project_Spec_v0.2_Qwen3_235B_A22B.md`
- `DS5_System_Architecture_v0.2_Qwen3_235B_A22B.md`
- `DS5_Model_Runtime_Placement_Spec_v0.2_Qwen3_235B_A22B.md`
- `DS5_Benchmark_and_Acceptance_Spec_v0.2_Qwen3_235B_A22B.md`
- `DS5_Execution_Plan_Input_v0.2_Qwen3_235B_A22B.md`

The source-pack files themselves are not present in this worktree. Gate names below are therefore normalized against the repo-visible baseline in [Assumptions](../assumptions.md), [Minimum Viable Finding](../minimum-viable-finding.md), [ADR-001](../decisions/ADR-001-model-selection.md), [ADR-002](../decisions/ADR-002-phase0-transport-first.md), and [Risk Register](../risk-register.md).

## Current Goal Status

The requested backlog conversion is complete in this directory, and the ARB feedback in `/Users/jessewhite/Downloads/20260609-ARB/20260609-ARB.md` has been folded into [Project Plan After ARB Refresh](project-plan.md).

The underlying runtime goals are not complete. The repo currently contains Phase 0 constants, transport scaffolding, benchmark schemas, local smoke findings, and placement planning tools. It does not yet contain a full tokenizer/runtime, primary MoE weight loader, fused router protocol, heterogeneous Zig allocator, NVMe prefetcher, or Metal expert kernels.

Current goal order:

1. Complete `DS5-F001A: Placement Contract Hardening`.
2. Run `DS5-F000: Phase 0 Transport Finding`.
3. Complete `DS5-F001B: Runtime Placement Evidence`.
4. Start `DS5-F002` only after the Phase 0 finding supports continued distributed decode work.

The ARB decision is conditional approval for continued Phase 1 placement-contract work. It is not approval for model loading, tokenizer integration, speculative decoding, fused routing, prefetch work, or Metal kernels.

## Epic Catalogue

| Epic ID | Epic | Outcome |
|---|---|---|
| DS5-E01 | Runtime Topology And Placement | Prove the asymmetric Node A/B/C placement can run within strict memory ownership and headroom rules. |
| DS5-E02 | Routing Transport | Prove fused routing packets and transport synchronization are compatible with decode-shaped MoE traffic. |
| DS5-E03 | Quantization And Memory Runtime | Prove heterogeneous precision can fit the model envelope without unmeasured routing or quality drift. |
| DS5-E04 | Cold Expert Promotion | Prove cold expert promotion can hide storage latency without making NVMe part of the steady-state hot path. |
| DS5-E05 | Metal Worker Kernels | Prove worker-local Metal execution can run extended generation loops without command-buffer timeouts. |

## PM Validation Gate Catalogue

| Gate ID | Gate | Governing Source | Completion Meaning |
|---|---|---|---|
| PM-GATE-PH0-01 | Phase 0 Transport And Simulated-MoE Finding | Minimum Viable Finding and ADR-002 | Target-hardware A/B/C transport artifacts answer the first physical go/no-go question before deeper runtime work. |
| PM-GATE-RT-01 | Runtime Placement And Memory-Cap Conformance | Model Runtime Placement Spec | Runtime placement matches Node A/B/C ownership and per-node memory caps under measured allocation telemetry. |
| PM-GATE-TR-01 | Thunderbolt Block-Routing Transport Evidence | Benchmark And Acceptance Spec | Fused block-routing traffic meets packet, latency, checksum, concurrency, and artifact requirements on acceptance hardware. |
| PM-GATE-QNT-01 | Quantization Envelope And Quality-Drift Evidence | Model Runtime Placement Spec and Benchmark And Acceptance Spec | Tensor precision, active-read envelope, allocator accounting, and quality drift pass measured acceptance checks. |
| PM-GATE-PF-01 | Storage Promotion And Cold-Miss Latency-Hiding Evidence | System Architecture Spec and Model Runtime Placement Spec | Cold expert prefetch proves direct-I/O behavior, 7 to 8 token lead time, and zero storage-attributed decode stalls. |
| PM-GATE-MTL-01 | Metal Kernel Stability And Long-Run TDR Evidence | System Architecture Spec and Benchmark And Acceptance Spec | Fragmented Metal execution proves long-run stability, telemetry coverage, and zero WindowServer command-buffer timeout events. |

## Consolidated Feature Backlog

| ID | Epic | Feature | Status | Complexity | PM Validation Gate | Feature File |
|---|---|---|---|---:|---|---|
| DS5-F001 | DS5-E01 Runtime Topology And Placement | Prefill/Decode Disaggregation (PDD) Topology | Umbrella split into F001A and F001B; parent goal not met | 8 | `PM-GATE-RT-01: Runtime Placement And Memory-Cap Conformance` | [feature-001-pdd-topology.md](feature-001-pdd-topology.md) |
| DS5-F001A | DS5-E01 Runtime Topology And Placement | Placement Contract Hardening | Next feature work; current scaffold partially satisfies it | 5 | `PM-GATE-RT-01: Runtime Placement And Memory-Cap Conformance` | [feature-001a-placement-contract-hardening.md](feature-001a-placement-contract-hardening.md) |
| DS5-F000 | DS5-E02 Routing Transport | Phase 0 Transport Finding | Queued after F001A; target-hardware finding not complete | 7 | `PM-GATE-PH0-01: Phase 0 Transport And Simulated-MoE Finding` | [feature-000-phase0-transport-finding.md](feature-000-phase0-transport-finding.md) |
| DS5-F001B | DS5-E01 Runtime Topology And Placement | Runtime Placement Evidence | Queued after F001A and Phase 0 go/no-go | 8 | `PM-GATE-RT-01: Runtime Placement And Memory-Cap Conformance` | [feature-001b-runtime-placement-evidence.md](feature-001b-runtime-placement-evidence.md) |
| DS5-F002 | DS5-E02 Routing Transport | Fused Gating And Zero-Copy Routing Protocol | Blocked until Phase 0 finding supports continued distributed decode work | 9 | `PM-GATE-TR-01: Thunderbolt Block-Routing Transport Evidence` | [feature-002-fused-gating-zero-copy-routing.md](feature-002-fused-gating-zero-copy-routing.md) |
| DS5-F003 | DS5-E03 Quantization And Memory Runtime | Asymmetric Quantization Pipeline | Deferred; Python planning estimator only, runtime goal not met | 8 | `PM-GATE-QNT-01: Quantization Envelope And Quality-Drift Evidence` | [feature-003-asymmetric-quantization-pipeline.md](feature-003-asymmetric-quantization-pipeline.md) |
| DS5-F004 | DS5-E04 Cold Expert Promotion | Asynchronous Rolling Pre-fetch Buffer | Deferred; goal not met | 10 | `PM-GATE-PF-01: Storage Promotion And Cold-Miss Latency-Hiding Evidence` | [feature-004-async-rolling-prefetch-buffer.md](feature-004-async-rolling-prefetch-buffer.md) |
| DS5-F005 | DS5-E05 Metal Worker Kernels | Localized Metal Kernel Fragmentation | Deferred; goal not met | 9 | `PM-GATE-MTL-01: Metal Kernel Stability And Long-Run TDR Evidence` | [feature-005-localized-metal-kernel-fragmentation.md](feature-005-localized-metal-kernel-fragmentation.md) |

## Merge Governance

Every feature must satisfy the general DS5 governance rules before merge:

- Preserve exact Qwen top-8 routing semantics.
- Emit reproducible, machine-readable benchmark artifacts for performance claims.
- Refuse manifests that exceed per-node static caps unless the override is explicit and recorded.
- Keep measured evidence separate from planning assumptions in docs and summaries.
- Avoid full-runtime claims until the Phase 0 transport and simulated-MoE milestone has a clear go/no-go result.

## Quarantined Claims That Affect This Backlog

The repo-visible baseline quarantines several claims that appear in the composite architecture. They are still represented as feature targets here because they were requested, but they cannot merge on assertion alone:

- `<8us` network synchronization target before measurement.
- 94 percent hot-expert pinning claim.
- BitNet/IQ2-heavy quantization safety claims.
- `O_DIRECT` or Linux-like storage controls on macOS.
- Any steady-state active-weight decode path that depends on NVMe.
