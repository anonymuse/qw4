# Active Board

Status: active.

This board is the current coordination surface for DS5 agents, chats, tasks, and worktrees. Update it when a task starts, pauses, hands off, or merges.

## Current Focus

Phase 0: build a measurable transport and simulated-MoE foundation before making runtime performance claims.

Primary question:

> Can an M5 Pro coordinator coordinate Qwen3-shaped MoE activation/result movement across two M5 Max workers without interconnect and scheduling overhead dominating decode-shaped work?

ARB refresh result:

> Conditionally approved for continued Phase 1 placement-contract work. Not approved for model loading, tokenizer integration, speculative decoding, fused routing, prefetch work, or Metal kernels.

Current goal sequence:

1. Complete `DS5-F001A: Placement Contract Hardening`.
2. Run `DS5-F000: Phase 0 Transport Finding`.
3. Complete `DS5-F001B: Runtime Placement Evidence`.
4. Start `DS5-F002` only after Phase 0 transport evidence supports continued distributed decode work.

## Active Work Packs

| Work pack | Status | Notes |
|---|---|---|
| `docs/work-packs/2026-07-09-overnight/` | merged seed | Original multi-agent Phase 0 kickoff pack. Treat as task source material, not the whole coordination system. Seed work through PR #8 is merged to `main`; remaining work is tracked through the backlog and fresh task rows. |

## Merged Coordination Workflow Status

Last census: 2026-07-09 from `/Users/jessewhite/.codex/worktrees/5e1a/qw4`.

| Item | Current truth | Evidence | Next action |
|---|---|---|---|
| Coordination workflow | merged | PR #7 `codex/coordination-workflow` merged to `main` at `ebe0996` on 2026-07-09. | Keep `docs/coordination/` as the stable coordination entry point. |
| Backlog docs | merged | PR #6 `codex/create-feature-backlog-docs` merged to `main` at `f440910`; branch tip `41decce` is reachable. | Use `docs/backlog/README.md` as current backlog catalogue. |
| Concurrent transport harness | merged | PR #5 `codex/add-concurrent-transport-harness` merged to `main` at `1a435ba`; branch tip `b99a9d9` is reachable. | Treat associated clean worktree as cleanup candidate after owner confirmation. |
| DS5-F001 PDD topology | merged | PR #8 `codex/ds5-f001-pdd-topology` merged to `main` at `310ad6d`; remote PR tip `df32794` is merged, while local branch tip `a483426` is a clean divergent equivalent/older local tip. | Review local branch before branch cleanup; preserve until confirmed redundant. |
| DS5-F001 PDD artifacts | merged | PR #12 `codex/ds5-f001-pdd-artifacts` merged to `main` at `90b3fbd` on 2026-07-09. | Treat as scaffold/planning evidence only; complete `DS5-F001A` before deeper runtime work. |
| Open PRs | one draft | `gh pr list --state open --limit 50` found draft PR #13 `codex/ds5-f002-routing-scaffold` on 2026-07-09. | Review against the ARB gate order before merging. |

## Task Board

| ID | Owner | Status | Branch/worktree | Owned paths | Validation | Handoff |
|---|---|---|---|---|---|---|
| A | unassigned | merged seed | PR #2 and later integration branches | `build.zig`, `src/`, CLI stubs | `zig build test` when Zig is available | `docs/work-packs/2026-07-09-overnight/agent-a-repo-scaffold.md` |
| B | unassigned | merged seed | PR #5 and later integration branches | `benchmarks/schemas/`, `tests/fixtures/` | `python3 tools/report/validate_run.py tests/fixtures/artifacts/transport-smoke` | `docs/work-packs/2026-07-09-overnight/agent-b-benchmark-schemas.md` |
| C | unassigned | merged seed | PR #3, PR #4, and PR #5 | `src/transport/`, transport smoke command | loopback transport smoke command | `docs/work-packs/2026-07-09-overnight/agent-c-loopback-transport.md` |
| D | unassigned | merged seed | PR #2 and later integration branches | `configs/`, `benchmarks/scenarios/` | scenario parser or smoke run | `docs/work-packs/2026-07-09-overnight/agent-d-configs-scenarios.md` |
| E / DS5-F001 | unassigned | umbrella split after ARB review | PR #12 merged to `main` | `src/model/`, `tools/model_inspect/`, `configs/`, `configs/schemas/`, `tests/model/`, `docs/findings/`, `docs/backlog/` | Subfeature-specific validation | Parent feature is now split into `DS5-F001A` planning hardening and `DS5-F001B` runtime evidence. |
| ARB-PLAN | Codex | ready for review | `codex/arb-plan-refresh` / `/Users/jessewhite/.codex/worktrees/5e1a/qw4` | `README.md`, `docs/backlog/`, `docs/coordination/active-board.md` | `git diff --check` | Incorporates `/Users/jessewhite/Downloads/20260609-ARB/20260609-ARB.md` into project plan and feature goals. |
| DS5-F001A | unassigned | next feature work | fresh branch needed from `main` | `src/model/`, `tools/model_inspect/`, `configs/`, `configs/schemas/`, `tests/model/`, `docs/findings/`, `docs/backlog/` | `make test`; `make pdd-topology-validate` | Harden placement contract, model constants, evidence metadata, context assumption, tensor-class placeholders, runtime-path constraints, and schema-authority docs. |
| DS5-F000 | unassigned | queued after `DS5-F001A` | fresh branch needed from `main` | `src/transport/`, `benchmarks/`, `tools/report/`, `docs/findings/`, `docs/backlog/` | target-hardware A/B/C run plus artifact schema validation | Answer Phase 0 transport go/no-go before fused routing or model-runtime work. |
| DS5-F001B | unassigned | queued after `DS5-F001A` and Phase 0 go/no-go | fresh branch needed from `main` | runtime startup paths, `src/model/`, `tools/model_inspect/`, `configs/`, `docs/findings/`, `docs/backlog/` | startup/warmup memory ledger validation and worker ownership logs | Prove runtime placement behavior separately from scaffold/planning evidence. |
| F | unassigned | merged seed | PR #2 and later integration branches | `tools/report/`, `publication/`, `docs/findings/` | report generation from fixture artifacts | `docs/work-packs/2026-07-09-overnight/agent-f-reporting-publication.md` |

## Worktree Census

Classification rules: `active` means still tied to an open coordination task or this census branch; `merged` means the task/PR appears merged and the clean worktree can be considered for pruning after confirmation; `stale-clean` means a clean detached duplicate with no apparent unique local state; `needs-rescue` means uncommitted changes, unmerged commits, or unclear useful state; `unknown` means there is not enough evidence to classify safely.

| Path | Branch or commit | Clean/dirty | Related PR/branch/task | Classification | Recommendation | Prune safety |
|---|---|---|---|---|---|---|
| `/Users/jessewhite/Code/personal/qw4` | `main` at `90b3fbd` | clean | primary checkout, `origin/main` | active | Preserve as stable integration checkout. | preserve |
| `/Users/jessewhite/.codex/worktrees/5e1a/qw4` | `codex/arb-plan-refresh` at `90b3fbd` plus docs edits | dirty | ARB project-plan refresh | active | Review and merge after validation; preserve until merged or explicitly abandoned. | preserve |
| `/Users/jessewhite/.codex/worktrees/b5b8/qw4` | `codex/ds5-f001-pdd-artifacts` at `0c9c944` | clean | PR #12 merged to `main` at `90b3fbd` | merged | Cleanup candidate after owner confirmation. | confirm before prune |
| `/Users/jessewhite/.codex/worktrees/dd81/qw4` | `codex/ds5-f002-routing-scaffold` at `63a52a5` | clean | draft PR #13 | active review | Preserve; review against the ARB gate order before merge. | preserve |

Pruned during the 2026-07-09 cleanup pass after one-at-a-time owner confirmation:

| Removed path | Former state | Reason |
|---|---|---|
| `/Users/jessewhite/.codex/worktrees/24b4/qw4` | detached `18513a7` | Clean duplicate at merged PR #4 commit. |
| `/Users/jessewhite/.codex/worktrees/9f34/qw4` | detached `18513a7` | Clean duplicate at merged PR #4 commit. |
| `/Users/jessewhite/.codex/worktrees/baee/qw4` | detached `18513a7` | Clean duplicate at merged PR #4 commit. |
| `/Users/jessewhite/.codex/worktrees/c156/qw4` | detached `18513a7` | Clean duplicate at merged PR #4 commit. |
| `/Users/jessewhite/.codex/worktrees/4bbd/qw4` | detached `310ad6d` | Clean duplicate at merged PR #8 commit. |
| `/Users/jessewhite/.codex/worktrees/f10b/qw4` | detached `310ad6d` | Clean duplicate at merged PR #8 commit. |
| `/Users/jessewhite/.codex/worktrees/13d1/qw4` | `codex/add-concurrent-transport-harness` at `b99a9d9` | Clean worktree for PR #5 branch already merged by ancestry. |
| `/Users/jessewhite/.codex/worktrees/c9a3/qw4` | `codex/create-feature-backlog-docs` at `41decce` | Clean worktree for PR #6 branch already merged by ancestry. |
| `/Users/jessewhite/.codex/worktrees/c0ae/qw4` | `codex/ds5-localmodel-testing-main` at `18513a7` | Clean worktree for branch already merged by ancestry. |
| `/Users/jessewhite/.codex/worktrees/02dd/qw4` | detached `d9efe4e` | Clean backup-checkout duplicate; branch pointer preserved after `97fa` was rescued. |
| `/Users/jessewhite/.codex/worktrees/908a/qw4` | `codex/ds5-f001-pdd-topology` at `a483426` | Clean worktree; patch content appeared represented on `main` by PR #8 though branch commit was not an ancestor. |

## Active Branches Waiting For Review Or Cleanup

| Branch | Status | Evidence | Next action |
|---|---|---|---|
| `codex/arb-plan-refresh` | active review | Current docs-only branch incorporates the 20260609 ARB feedback into the project plan, backlog feature split, and active board. | Review and merge after docs validation. |
| `codex/ds5-f001-pdd-artifacts` | merged branch cleanup | Branch tip `0c9c944` is included in the PR #12 merge at `90b3fbd`; worktree `/Users/jessewhite/.codex/worktrees/b5b8/qw4` is clean. | Delete branch or prune worktree only after separate confirmation. |
| `codex/ds5-f002-routing-scaffold` | draft PR #13 with ARB gate conflict risk | Branch tip `63a52a5` exists on origin and starts after `90b3fbd`, but F002 is now blocked behind `DS5-F001A` and `DS5-F000`. | Preserve; rebase or retarget after the ARB plan lands, and do not merge as runtime progress until prerequisites are resolved. |

## Stale Or Detached Worktrees Needing Owner Confirmation

| Worktree set | State | Confirmation needed |
|---|---|---|
| None detected in current `git worktree list` | Current worktrees are `main`, `codex/arb-plan-refresh`, `codex/ds5-f001-pdd-artifacts`, and `codex/ds5-f002-routing-scaffold`. | Preserve active/review worktrees until their branches are resolved. |

## Integration Queue

| Item | Source | Status | Coordinator notes |
|---|---|---|---|
| Confirm build and test commands | all tasks | open | Keep commands in runbooks once stable. |
| Decide whether to keep `docs/backlog/` as aliases only | coordination | open | `docs/backlog/README.md` is currently a real feature catalogue; keep `docs/coordination/` as the active operating board. |
| Incorporate ARB feedback into feature plan | `/Users/jessewhite/Downloads/20260609-ARB/20260609-ARB.md` | in review | Branch `codex/arb-plan-refresh` adds the ARB project plan and splits `DS5-F001` into `DS5-F001A` and `DS5-F001B`, with `DS5-F000` inserted before fused routing. |
| Review F002 routing scaffold against ARB gate order | draft PR #13 / `codex/ds5-f002-routing-scaffold` | open | Preserve the branch, but do not treat F002 as unblocked until `DS5-F001A` and `DS5-F000` are resolved. |
| Clean up merged F001 artifact branch/worktree | `codex/ds5-f001-pdd-artifacts` | open | PR #12 is merged and the worktree is clean; prune/delete only after explicit branch-cleanup confirmation. |

## Coordinator Checklist

1. Pull or inspect each worktree.
2. Read each handoff before diff review.
3. Run the validation command listed in the task board.
4. Check shared files for conflicting edits.
5. Update task status and integration queue.
6. Merge or reassign only after validation results are recorded.

## Next Coordinator Actions

1. Review and merge `codex/arb-plan-refresh`, then start `DS5-F001A` from `main`.
2. After `DS5-F001A`, run `DS5-F000` on the target A/B/C topology before fused routing or model-runtime work.
3. Review draft PR #13 `codex/ds5-f002-routing-scaffold` against the ARB gate order; preserve it, but do not merge it as unblocked runtime work unless prerequisites are satisfied or scope is narrowed.
4. Confirm whether to prune `/Users/jessewhite/.codex/worktrees/b5b8/qw4` and delete `codex/ds5-f001-pdd-artifacts` now that PR #12 is merged.
5. Delete branches only after a separate branch-cleanup confirmation pass.
6. Start any new DS5 work from `main` with one task, one branch, one worktree, and one task-board row.
