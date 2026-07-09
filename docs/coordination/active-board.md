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
| `docs/work-packs/2026-07-09-overnight/` | merged seed | Original multi-agent Phase 0 kickoff pack. Treat as task source material, not the whole coordination system. Seed work through PR #8 is merged to `main`; remaining work is tracked through the backlog and fresh task rows. |

## Merged Coordination Workflow Status

Last census: 2026-07-09 from `/Users/jessewhite/.codex/worktrees/83f9/qw4`.

| Item | Current truth | Evidence | Next action |
|---|---|---|---|
| Coordination workflow | merged | PR #7 `codex/coordination-workflow` merged to `main` at `ebe0996` on 2026-07-09. | Keep `docs/coordination/` as the stable coordination entry point. |
| Backlog docs | merged | PR #6 `codex/create-feature-backlog-docs` merged to `main` at `f440910`; branch tip `41decce` is reachable. | Use `docs/backlog/README.md` as current backlog catalogue. |
| Concurrent transport harness | merged | PR #5 `codex/add-concurrent-transport-harness` merged to `main` at `1a435ba`; branch tip `b99a9d9` is reachable. | Treat associated clean worktree as cleanup candidate after owner confirmation. |
| DS5-F001 PDD topology | merged | PR #8 `codex/ds5-f001-pdd-topology` merged to `main` at `310ad6d`; remote PR tip `df32794` is merged, while local branch tip `a483426` is a clean divergent equivalent/older local tip. | Review local branch before branch cleanup; preserve until confirmed redundant. |
| Open PRs | none found | `gh pr list --state open --limit 50` returned no open PRs. | New work should start from `main` or a fresh task branch. |

## Task Board

| ID | Owner | Status | Branch/worktree | Owned paths | Validation | Handoff |
|---|---|---|---|---|---|---|
| A | unassigned | merged seed | PR #2 and later integration branches | `build.zig`, `src/`, CLI stubs | `zig build test` when Zig is available | `docs/work-packs/2026-07-09-overnight/agent-a-repo-scaffold.md` |
| B | unassigned | merged seed | PR #5 and later integration branches | `benchmarks/schemas/`, `tests/fixtures/` | `python3 tools/report/validate_run.py tests/fixtures/artifacts/transport-smoke` | `docs/work-packs/2026-07-09-overnight/agent-b-benchmark-schemas.md` |
| C | unassigned | merged seed | PR #3, PR #4, and PR #5 | `src/transport/`, transport smoke command | loopback transport smoke command | `docs/work-packs/2026-07-09-overnight/agent-c-loopback-transport.md` |
| D | unassigned | merged seed | PR #2 and later integration branches | `configs/`, `benchmarks/scenarios/` | scenario parser or smoke run | `docs/work-packs/2026-07-09-overnight/agent-d-configs-scenarios.md` |
| E | unassigned | active backlog | `codex/ds5-f001-pdd-topology` / DS5-F001 | `src/model/`, `tools/model_inspect/`, `tools/quant/` | memory estimator tests or fixture run | `docs/work-packs/2026-07-09-overnight/agent-e-placement-feasibility.md` |
| F | unassigned | merged seed | PR #2 and later integration branches | `tools/report/`, `publication/`, `docs/findings/` | report generation from fixture artifacts | `docs/work-packs/2026-07-09-overnight/agent-f-reporting-publication.md` |

## Worktree Census

Classification rules: `active` means still tied to an open coordination task or this census branch; `merged` means the task/PR appears merged and the clean worktree can be considered for pruning after confirmation; `stale-clean` means a clean detached duplicate with no apparent unique local state; `needs-rescue` means uncommitted changes, unmerged commits, or unclear useful state; `unknown` means there is not enough evidence to classify safely.

| Path | Branch or commit | Clean/dirty | Related PR/branch/task | Classification | Recommendation | Prune safety |
|---|---|---|---|---|---|---|
| `/Users/jessewhite/Code/personal/qw4` | `main` at `ebe0996` | clean | primary checkout, `origin/main` | active | Preserve as stable integration checkout. | preserve |
| `/Users/jessewhite/.codex/worktrees/83f9/qw4` | `codex/worktree-census` from `ebe0996` | clean after census commit | current census task | active | Open draft PR if possible, then preserve until merged. | preserve |
| `/Users/jessewhite/.codex/worktrees/13d1/qw4` | `codex/add-concurrent-transport-harness` at `b99a9d9` | clean | PR #5 merged | merged | Confirm no active thread still uses it, then prune worktree and later delete branch if desired. | safe to prune after confirmation |
| `/Users/jessewhite/.codex/worktrees/c9a3/qw4` | `codex/create-feature-backlog-docs` at `41decce` | clean | PR #6 merged | merged | Confirm no active thread still uses it, then prune worktree and later delete branch if desired. | safe to prune after confirmation |
| `/Users/jessewhite/.codex/worktrees/c0ae/qw4` | `codex/ds5-localmodel-testing-main` at `18513a7` | clean | PR #4 merged / `codex/continue-ds5-localmodel-testing` | merged | Confirm whether this branch name is still useful; prune worktree after confirmation. | safe to prune after confirmation |
| `/Users/jessewhite/.codex/worktrees/908a/qw4` | `codex/ds5-f001-pdd-topology` at `a483426` | clean | PR #8 merged from remote tip `df32794`; local branch is not an ancestor of `main` | needs-rescue | Compare local branch against merged PR #8 before cleanup; preserve until coordinator confirms no unique local patch value. | needs review |
| `/Users/jessewhite/.codex/worktrees/bc6f/qw4` | `codex/coordination-workflow` at `22dd5c0` | clean | PR #7 merged from remote tip `2688df1`; local branch is not an ancestor of `main` | needs-rescue | Compare local branch against merged PR #7 before cleanup; preserve until coordinator confirms no unique local patch value. | needs review |
| `/Users/jessewhite/.codex/worktrees/02dd/qw4` | detached `d9efe4e` (`backup/local-main-before-origin-sync-20260709`) | clean | backup branch not merged into `main` by ancestry | needs-rescue | Keep until backup branch purpose is reviewed against `main`; do not prune solely because it is clean. | needs review |
| `/Users/jessewhite/.codex/worktrees/97fa/qw4` | detached `d9efe4e` (`backup/local-main-before-origin-sync-20260709`) | dirty: modified `README.md`, `tools/model_inspect/README.md`; untracked local model smoke files | local model metadata/smoke work | needs-rescue | Preserve immediately; create a branch or move useful changes only after owner review. | preserve |
| `/Users/jessewhite/.codex/worktrees/24b4/qw4` | detached `18513a7` | clean | PR #4 merged | stale-clean | Confirm no active thread uses it, then prune worktree. | safe to prune after confirmation |
| `/Users/jessewhite/.codex/worktrees/9f34/qw4` | detached `18513a7` | clean | PR #4 merged | stale-clean | Confirm no active thread uses it, then prune worktree. | safe to prune after confirmation |
| `/Users/jessewhite/.codex/worktrees/baee/qw4` | detached `18513a7` | clean | PR #4 merged | stale-clean | Confirm no active thread uses it, then prune worktree. | safe to prune after confirmation |
| `/Users/jessewhite/.codex/worktrees/c156/qw4` | detached `18513a7` | clean | PR #4 merged | stale-clean | Confirm no active thread uses it, then prune worktree. | safe to prune after confirmation |
| `/Users/jessewhite/.codex/worktrees/4bbd/qw4` | detached `310ad6d` | clean | PR #8 merge commit, reachable from `main` | stale-clean | Confirm no active thread uses it, then prune worktree. | safe to prune after confirmation |
| `/Users/jessewhite/.codex/worktrees/f10b/qw4` | detached `310ad6d` | clean | PR #8 merge commit, reachable from `main` | stale-clean | Confirm no active thread uses it, then prune worktree. | safe to prune after confirmation |

## Active Branches Waiting For Review Or Cleanup

| Branch | Status | Evidence | Next action |
|---|---|---|---|
| `codex/worktree-census` | active | Current docs-only census branch. | Commit active-board update and open draft PR. |
| `codex/ds5-f001-pdd-topology` | cleanup review | PR #8 is merged, but local branch tip `a483426` differs from merged remote tip `df32794`. | Compare before deleting branch or pruning its named worktree. |
| `codex/coordination-workflow` | cleanup review | PR #7 is merged, but local branch tip `22dd5c0` differs from merged remote tip `2688df1`. | Compare before deleting branch or pruning its named worktree. |
| `backup/local-main-before-origin-sync-20260709` | backup review | Detached clean and dirty worktrees point at `d9efe4e`; ancestry check says not merged into `main`. | Decide whether the backup still protects useful state. |
| `codex/add-concurrent-transport-harness` | merged cleanup | Branch tip `b99a9d9` is merged via PR #5. | Cleanup after owner confirmation. |
| `codex/create-feature-backlog-docs` | merged cleanup | Branch tip `41decce` is merged via PR #6. | Cleanup after owner confirmation. |
| `codex/ds5-localmodel-testing-main` | merged cleanup | Points at `18513a7`, same commit as merged PR #4 line. | Cleanup after confirming branch name is not still useful. |

## Stale Or Detached Worktrees Needing Owner Confirmation

| Worktree set | State | Confirmation needed |
|---|---|---|
| Detached `18513a7`: `24b4`, `9f34`, `baee`, `c156` | clean, PR #4 merge commit | Confirm no Codex thread is still using these before pruning. |
| Detached `310ad6d`: `4bbd`, `f10b` | clean, PR #8 merge commit | Confirm no Codex thread is still using these before pruning. |
| Detached `d9efe4e`: `02dd`, `97fa` | backup commit; `97fa` has uncommitted changes | Review and rescue `97fa`; decide whether `02dd` is redundant only after backup review. |

## Integration Queue

| Item | Source | Status | Coordinator notes |
|---|---|---|---|
| Confirm build and test commands | all tasks | open | Keep commands in runbooks once stable. |
| Reconcile completed seed work into current board statuses | all tasks | done | Seed rows now point at merged PR evidence or active backlog work. |
| Decide whether to keep `docs/backlog/` as aliases only | coordination | open | `docs/backlog/README.md` is currently a real feature catalogue; keep `docs/coordination/` as the active operating board. |
| Rescue dirty detached local-model work | `/Users/jessewhite/.codex/worktrees/97fa/qw4` | open | Dirty detached worktree has modified docs and untracked smoke tooling. Preserve until owner decides branch/commit/discard path. |
| Review divergent local copies of merged PR branches | `codex/coordination-workflow`, `codex/ds5-f001-pdd-topology` | open | Local branch tips differ from merged remote PR tips; compare before branch cleanup. |
| Confirm and prune clean stale worktrees | worktree census | open | Only prune after confirming no active Codex thread still uses the worktree. |

## Coordinator Checklist

1. Pull or inspect each worktree.
2. Read each handoff before diff review.
3. Run the validation command listed in the task board.
4. Check shared files for conflicting edits.
5. Update task status and integration queue.
6. Merge or reassign only after validation results are recorded.

## Next Coordinator Actions

1. Review `/Users/jessewhite/.codex/worktrees/97fa/qw4` and rescue or intentionally abandon the dirty detached local-model metadata work.
2. Compare local `codex/coordination-workflow` and `codex/ds5-f001-pdd-topology` against their merged PR tips before branch deletion.
3. Ask owners whether detached clean worktrees at `18513a7` and `310ad6d` are still tied to live Codex threads.
4. After confirmation, prune only clean redundant worktrees; do not remove branches until their branch cleanup has separate confirmation.
5. Start any new DS5 work from `main` with one task, one branch, one worktree, and one task-board row.
