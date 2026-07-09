# Overnight Agent Work Pack: Phase 0 Kickoff

Date: 2026-07-09.

Purpose: prepare DS5 for the first coding milestone without loading the full model. This pack is designed for multiple agents working in parallel overnight with minimal path conflicts.

## North Star

Create the Phase 0 foundation for the first publishable finding:

> Can an M5 Pro coordinator coordinate Qwen3-shaped MoE activation/result movement across two M5 Max workers without interconnect and scheduling overhead dominating decode-shaped work?

The overnight work should produce a runnable skeleton, deterministic configs, benchmark artifact schemas, and the first transport/simulated-MoE harness pieces.

## Work Pack Map

| Agent | Task | Primary artifact |
|---|---|---|
| A | Repo scaffold and Zig build skeleton | `build.zig`, `src/`, CLI stubs |
| B | Benchmark artifact schemas and fixtures | `benchmarks/schemas/`, `tests/fixtures/` |
| C | Loopback transport prototype | `src/transport/`, transport smoke command |
| D | Cluster configs and scenario definitions | `configs/`, `benchmarks/scenarios/` |
| E | Qwen placement and memory feasibility tools | `src/model/`, `tools/model_inspect/`, `tools/quant/` |
| F | Reporting and publication templates | `tools/report/`, `publication/`, `docs/findings/` |

## Recommended Kickoff Order

Start immediately:

1. Agent A: repo scaffold and build skeleton.
2. Agent B: schemas and sample artifacts.
3. Agent D: configs and benchmark scenarios.
4. Agent E: placement and memory feasibility tools.

Start after A has a minimal skeleton, or work in isolated files:

5. Agent C: loopback transport prototype.

Start after B defines schemas, or draft templates with placeholders:

6. Agent F: reporting and publication templates.

## Shared Rules

- Do not implement the full transformer.
- Do not download model weights.
- Do not add dependencies without documenting why.
- Prefer Zig 1.0 for runtime code.
- Python is allowed only for tooling, validation, and reporting, using the standard library unless justified.
- Every benchmark command must emit machine-readable output.
- Every generated run artifact belongs under `artifacts/runs/`.
- Do not claim hardware performance from loopback or synthetic runs.
- Keep Qwen3-specific naming visible. Do not introduce generic runtime abstractions.
- Preserve exact top-8 routing semantics in all simulated packet formats.

## Merge Discipline

Each agent should stay inside its owned paths. If a shared file is needed, make the smallest possible edit and call it out in the handoff.

Shared files that may see edits:

- `README.md`;
- `.gitignore`;
- `docs/runbooks/cluster-setup.md`;
- `docs/assumptions.md`.

Avoid editing another agent's primary paths unless blocked.

## Definition Of Done For The Overnight Pack

By morning, the repo should contain:

- a compiling or clearly stubbed Zig build;
- worker and coordinator CLI entry points;
- deterministic example cluster and scenario configs;
- benchmark artifact schemas;
- sample benchmark artifacts;
- a loopback transport smoke path or a documented reason it could not run;
- a placement-memory estimator that does not require full model weights;
- a report generator or report template for Phase 0 results;
- updated docs showing how to run the first local smoke tests.

## Morning Integration Checklist

1. Run `git status --short`.
2. Review each agent handoff.
3. Check that no full-model, GPU, cloud, or generic-runtime scope slipped in.
4. Run available build/tests locally.
5. Validate sample artifacts against schemas.
6. Read the Phase 0 summary template and confirm it can accept real cluster measurements.
7. Create a single integration commit after review.

