# DS5

DS5 is a model-specific local distributed inference project for `Qwen3-235B-A22B`, with `Qwen3-235B-A22B-Instruct-2507` as the first concrete runtime target.

The project does not aim to become a general inference framework. It aims to test whether a narrow runtime can exploit Qwen3 MoE structure, Apple Silicon unified memory, and a small Thunderbolt/RDMA-style local cluster well enough to produce a credible open-source technical finding.

## Source Of Truth

The active DS5 direction is:

- Target model: `Qwen3-235B-A22B-Instruct-2507`.
- Deferred variant: `Qwen3-235B-A22B-Thinking-2507`.
- Hardware topology: one M5 Pro coordinator/orchestrator plus two M5 Max data-plane workers, each with 48GB unified memory.
- Coordinator role: orchestration, routing policy, scheduling, state, health, telemetry, benchmark control, and limited compute.
- Worker role: synthetic LLM data-plane work in Phase 0, then primary model execution, layer ownership, expert execution, KV ownership, and local router mirrors after correctness mode.
- Optional Mac mini role: support services only.
- Optional RTX/Windows/Linux role: tooling, preprocessing, quantization experiments, dataset generation, or reference comparison only.

The core thesis:

> A model-specific local distributed inference engine can exploit Qwen3-235B-A22B's MoE structure, Apple Silicon unified memory, and a small RDMA-style local cluster more effectively than a general-purpose runtime for this exact topology and workload.

This is not a claim that DS5 will outperform data-center GPUs.

## First Technical Finding

The first publishable milestone is a transport and simulated-MoE study:

> Can an M5 Pro orchestrator agent keep two M5 Max synthetic LLM data-plane workers fed with Qwen3-shaped activation/result traffic without transport, scheduling, or control-plane overhead dominating decode-shaped work?

This milestone does not load the full model. It validates the physical and runtime assumptions first.

Model-independent SSD/NVMe measurements may be run as separate adjunct evidence for future cold backing, promotion, artifacts, or long-context backing. They are not part of the Phase 0 distributed-decode go/no-go unless a separate storage-readiness task says so.

## Non-Goals

- No general model plugin system.
- No CUDA or non-Apple primary backend.
- No cloud-first serving platform.
- No throughput claims before benchmark artifacts exist.
- No routing substitutions that change Qwen top-8 expert semantics.
- No assumption that Thunderbolt networking behaves like true shared memory or magic RDMA.
- No steady-state active-weight decode path that depends on NVMe.
- No tokenizer, KV allocator, speculative decoding, fused routing, Metal kernels, or model loading in Phase 0.

## Documentation Index

- [Assumptions](docs/assumptions.md)
- [Coordination](docs/coordination/README.md)
- [Sustainable Workflow](docs/coordination/workflow.md)
- [Active Board](docs/coordination/active-board.md)
- [Documentation Reconciliation](docs/documentation-reconciliation.md)
- [Project Plan](docs/backlog/project-plan.md)
- [Agile Backlog](docs/backlog/README.md)
- [Risk Register](docs/risk-register.md)
- [Minimum Viable Finding](docs/minimum-viable-finding.md)
- [Research Agent Review](docs/research/2026-07-11-research-agent-review.md)
- [Phase 0 Transport Finding Template](docs/findings/phase0-transport-template.md)
- [Repository Architecture](docs/repository-architecture.md)
- [ADR-001: Select Qwen3-235B-A22B](docs/decisions/ADR-001-model-selection.md)
- [ADR-002: Phase 0 Transport First](docs/decisions/ADR-002-phase0-transport-first.md)
- [Cluster Setup Runbook](docs/runbooks/cluster-setup.md)
- [DS5-F000 Cluster Operator Packet](docs/runbooks/ds5-f000-cluster-operator-packet.md)
- [Local Model Metadata Runbook](docs/runbooks/local-model-metadata.md)
- [Overnight Agent Work Pack](docs/work-packs/2026-07-09-overnight/README.md)

## Implementation Posture

Build the smallest measurable system first:

1. Discover nodes.
2. Measure link latency and block throughput.
3. Emit machine-readable benchmark artifacts.
4. Simulate Qwen-shaped MoE activation traffic.
5. Decide whether the transport, scheduling, and control-plane model justify moving toward runtime placement evidence.

Every benchmark must be reproducible from a command and must emit machine-readable output.
