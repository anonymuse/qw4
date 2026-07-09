# Active Board

Status: active.

This board is the current coordination surface for DS5 agents, chats, tasks, and worktrees. Update it when a task starts, pauses, hands off, or merges.

## Current Focus

Phase 0: build a measurable transport and simulated-MoE foundation before making runtime performance claims.

Primary question:

> Can an M5 Pro coordinator coordinate Qwen3-shaped MoE activation/result movement across two M5 Max workers without interconnect and scheduling overhead dominating decode-shaped work?

## Active Work Packs

| Work pack | Status | Notes |
|---|---|---|
| `docs/work-packs/2026-07-09-overnight/` | active seed | Original multi-agent Phase 0 kickoff pack. Treat as task source material, not the whole coordination system. |

## Task Board

| ID | Owner | Status | Branch/worktree | Owned paths | Validation | Handoff |
|---|---|---|---|---|---|---|
| A | unassigned | seed complete | TBD | `build.zig`, `src/`, CLI stubs | `zig build test` when Zig is available | `docs/work-packs/2026-07-09-overnight/agent-a-repo-scaffold.md` |
| B | unassigned | seed complete | TBD | `benchmarks/schemas/`, `tests/fixtures/` | `python3 tools/report/validate_run.py tests/fixtures/artifacts/transport-smoke` | `docs/work-packs/2026-07-09-overnight/agent-b-benchmark-schemas.md` |
| C | unassigned | seed complete | TBD | `src/transport/`, transport smoke command | loopback transport smoke command | `docs/work-packs/2026-07-09-overnight/agent-c-loopback-transport.md` |
| D | unassigned | seed complete | TBD | `configs/`, `benchmarks/scenarios/` | scenario parser or smoke run | `docs/work-packs/2026-07-09-overnight/agent-d-configs-scenarios.md` |
| E | unassigned | seed complete | TBD | `src/model/`, `tools/model_inspect/`, `tools/quant/` | memory estimator tests or fixture run | `docs/work-packs/2026-07-09-overnight/agent-e-placement-feasibility.md` |
| F | unassigned | seed complete | TBD | `tools/report/`, `publication/`, `docs/findings/` | report generation from fixture artifacts | `docs/work-packs/2026-07-09-overnight/agent-f-reporting-publication.md` |

## Integration Queue

| Item | Source | Status | Coordinator notes |
|---|---|---|---|
| Confirm build and test commands | all tasks | open | Keep commands in runbooks once stable. |
| Reconcile completed seed work into current board statuses | all tasks | open | Replace `seed complete` with actual branch and merge state after review. |
| Decide whether to keep `docs/backlog/` as aliases only | coordination | open | Use `docs/coordination/` as the stable source unless a real backlog is needed. |

## Coordinator Checklist

1. Pull or inspect each worktree.
2. Read each handoff before diff review.
3. Run the validation command listed in the task board.
4. Check shared files for conflicting edits.
5. Update task status and integration queue.
6. Merge or reassign only after validation results are recorded.
