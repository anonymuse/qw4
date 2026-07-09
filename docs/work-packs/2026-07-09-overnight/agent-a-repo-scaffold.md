# Agent A: Repo Scaffold And Zig Build Skeleton

## Objective

Create the minimal repository scaffold needed for DS5 Phase 0 commands. This is not the runtime implementation. It is the structure that lets the other agents land work cleanly.

## Read First

- `README.md`
- `docs/assumptions.md`
- `docs/repository-architecture.md`
- `docs/minimum-viable-finding.md`
- `docs/decisions/ADR-002-phase0-transport-first.md`

## Owned Paths

- `build.zig`
- `src/common/`
- `src/coordinator/`
- `src/worker/`
- `src/main.zig` if useful
- `.gitignore` only for generated build/run artifacts

## Deliverables

Create a minimal Zig build with these intended commands:

```bash
zig build run-coordinator -- --help
zig build run-worker -- --help
zig build test
```

The coordinator and worker can be stubs, but they should:

- parse `--help`;
- print deterministic usage;
- accept `--node`, `--listen`, `--config`, `--scenario`, and `--out` where appropriate;
- return nonzero on invalid arguments;
- avoid network behavior unless Agent C wires it in.

Suggested initial modules:

```text
src/common/args.zig
src/common/metrics.zig
src/common/protocol.zig
src/coordinator/main.zig
src/worker/main.zig
```

## Acceptance Checks

Run what is available:

```bash
zig build test
zig build run-coordinator -- --help
zig build run-worker -- --help
```

If Zig is unavailable, document that in the handoff and ensure the code is syntactically conservative.

## Do Not

- Do not implement model loading.
- Do not introduce a plugin architecture.
- Do not add external dependencies.
- Do not add Metal or MLX yet.
- Do not create broad abstractions for hypothetical future models.

## Handoff Notes

Report:

- commands run;
- files created;
- any build failures;
- how Agent C should plug transport into the CLI.

