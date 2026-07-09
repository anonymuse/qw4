# Repository Architecture

Status: proposed structure before production code.

The repository should keep experiments, runtime, tools, benchmarks, docs, and publication artifacts separate. The early repo should stay legible to a technically sophisticated reader.

## Proposed Layout

```text
build.zig
configs/
  cluster.local.example.toml
  scenarios/
src/
  common/
  transport/
  coordinator/
  worker/
  model/
  kernels/
benchmarks/
  schemas/
  scenarios/
tools/
  model_inspect/
  quant/
  report/
tests/
  fixtures/
docs/
  assumptions.md
  decisions/
  runbooks/
  findings/
artifacts/
  runs/
publication/
  figures/
  writeups/
```

## Directory Purposes

| Path | Purpose |
|---|---|
| `configs/` | Deterministic cluster, node, and experiment configuration files |
| `src/common/` | Shared protocol structs, config loading, metrics, checksums, clocks, and trace IDs |
| `src/transport/` | Node discovery, ping/pong latency, block transfer, connection management, and transport benchmarks |
| `src/coordinator/` | Node A orchestration, scheduling traces, simulated MoE routing, worker health, and benchmark control |
| `src/worker/` | Node B/C worker daemon, health reporting, block echo/reduce, memory accounting, and future execution endpoints |
| `src/model/` | Qwen metadata schema, manifest parsing, tensor shape accounting, and placement math |
| `src/kernels/` | Future Metal runtime and shaders; empty until transport and placement justify kernel work |
| `benchmarks/schemas/` | JSON/JSONL/CSV schemas for benchmark artifacts |
| `benchmarks/scenarios/` | Reproducible benchmark scenario definitions |
| `tools/model_inspect/` | Python or small utilities for safetensors/model metadata inspection |
| `tools/quant/` | Quantization feasibility, memory estimates, and manifest generation |
| `tools/report/` | Convert benchmark artifacts into markdown tables and figures |
| `tests/fixtures/` | Small deterministic protocol, manifest, and routing fixtures |
| `docs/` | Assumptions, ADRs, runbooks, risks, findings, and project governance |
| `artifacts/runs/` | Generated benchmark output; ignored by git |
| `publication/` | Figures, writeups, and public technical report material |

## Dependency Policy

- Prefer Zig 1.0 for first runtime and transport code.
- Use C/C++ only where macOS APIs or Metal integration justify it.
- Use Python only for model inspection, conversion, report generation, or test harnesses where it saves substantial time.
- Do not add dependencies without a short rationale in the relevant ADR or README section.
- Do not introduce broad abstractions before two concrete use cases require them.

## Naming Policy

The implementation should name Qwen3-specific concepts directly. Avoid generic model-runtime naming unless the code is genuinely shared infrastructure.

Good early names:

- `qwen3_moe_transport_smoke`;
- `Ds5ActivationPacket`;
- `PlacementManifest`;
- `ExpertTier`;
- `NodeRole`.

Avoid early names:

- `UniversalModelRuntime`;
- `BackendPlugin`;
- `GenericExpertEngine`;
- `ModelAdapter`.

