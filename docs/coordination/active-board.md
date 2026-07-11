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

1. `DS5-F001A: Placement Contract Hardening` is complete via PR #19.
2. If only the MacBook Air is available, run `DS5-F000L: Local Phase 0 Artifact Rehearsal` as prep-only artifact plumbing work.
3. Run `DS5-F000: Phase 0 Transport Finding` on the target A/B/C topology when cluster hardware is available.
4. Complete `DS5-F001B: Runtime Placement Evidence`.
5. Start `DS5-F002` only after both prerequisites are satisfied: `DS5-F001A` complete and `DS5-F000` target-hardware transport evidence supports continued distributed decode work.

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
| ARB recovery | merged | PR #15 `codex/recover-merge-13-apply-14` reverted the accidental PR #13 merge and applied the ARB plan from PR #14 to `main`. | Treat PR #14 as superseded and PR #13's original F002 runtime framing as reverted. |
| DS5-F001A Placement Contract Hardening | merged | PR #19 `codex/ds5-f001a-placement-hardening` merged to `main` at `9573e1b` on 2026-07-09. | Treat the placement-contract gate as complete; `DS5-F000` target-hardware transport evidence remains required before `DS5-F002`. |

## Task Board

| ID | Owner | Status | Branch/worktree | Owned paths | Validation | Handoff |
|---|---|---|---|---|---|---|
| A | unassigned | merged seed | PR #2 and later integration branches | `build.zig`, `src/`, CLI stubs | `zig build test` when Zig is available | `docs/work-packs/2026-07-09-overnight/agent-a-repo-scaffold.md` |
| B | unassigned | merged seed | PR #5 and later integration branches | `benchmarks/schemas/`, `tests/fixtures/` | `python3 tools/report/validate_run.py tests/fixtures/artifacts/transport-smoke` | `docs/work-packs/2026-07-09-overnight/agent-b-benchmark-schemas.md` |
| C | unassigned | merged seed | PR #3, PR #4, and PR #5 | `src/transport/`, transport smoke command | loopback transport smoke command | `docs/work-packs/2026-07-09-overnight/agent-c-loopback-transport.md` |
| D | unassigned | merged seed | PR #2 and later integration branches | `configs/`, `benchmarks/scenarios/` | scenario parser or smoke run | `docs/work-packs/2026-07-09-overnight/agent-d-configs-scenarios.md` |
| E / DS5-F001 | unassigned | umbrella split after ARB review | PR #12 merged to `main` | `src/model/`, `tools/model_inspect/`, `configs/`, `configs/schemas/`, `tests/model/`, `docs/findings/`, `docs/backlog/` | Subfeature-specific validation | Parent feature is now split into `DS5-F001A` planning hardening and `DS5-F001B` runtime evidence. |
| ARB-PLAN | Codex | merged via recovery PR #15 | `codex/recover-merge-13-apply-14` / `/Users/jessewhite/.codex/worktrees/dd81/qw4` | `README.md`, `docs/backlog/`, `docs/coordination/active-board.md` | `git diff --check origin/main..HEAD`; `make test` passed on recovery branch | PR #14 was superseded after accidental PR #13 merge; PR #15 landed the ARB plan and reverted premature F002 scaffold from `main`. |
| DS5-F001A | Codex | merged via PR #19 | `codex/ds5-f001a-placement-hardening` / `/Users/jessewhite/.codex/worktrees/fdf6/qw4` | `src/model/`, `tools/model_inspect/`, `configs/`, `configs/schemas/`, `tests/model/`, `docs/findings/`, `docs/backlog/`, `docs/coordination/active-board.md` | `make pdd-topology-validate`; `PYTHONPYCACHEPREFIX=/private/tmp/qw4-pycache python3 -m unittest tests.model.test_pdd_topology`; `make test`; `git diff --check` all passed | Placement-contract hardening gate is complete. Continue to `DS5-F000` target-hardware transport evidence before `DS5-F002`. |
| DS5-F000 | unassigned | next target-hardware feature; routing-payload scaffold available as prep evidence | fresh branch needed from `main` | `src/transport/`, `benchmarks/`, `tools/report/`, `docs/findings/`, `docs/backlog/` | target-hardware A/B/C run plus artifact schema validation | Answer Phase 0 transport go/no-go before fused routing or model-runtime work. Routing-payload scaffold validation may be referenced only as preparatory schema/test evidence, not target-hardware proof. |
| DS5-F000L | Codex | local validation passed; ready for review | `codex/ds5-f000-local-artifact-rehearsal` / `/Users/jessewhite/.codex/worktrees/a07c/qw4` | `docs/runbooks/`, `docs/findings/`, `docs/backlog/`, `tools/report/`, `benchmarks/schemas/`, `tests/report/`, `tests/fixtures/`, `docs/coordination/active-board.md` | `python3 tools/report/validate_run.py tests/fixtures/artifacts/transport-smoke` PASS; `python3 tools/report/summarize_phase0.py tests/fixtures/artifacts/transport-smoke` PASS; `make test` PASS; `git diff --check` PASS | Local MacBook Air rehearsal only. Added report/runbook guardrails against treating fixture sensitivity rows as final throughput or target A/B/C evidence. Does not complete `DS5-F000` or unblock `DS5-F001B`/`DS5-F002`. |
| DS5-F000 routing-payload integration follow-up | Codex | validation passed after PR #19 rebase; ready for review | `codex/ds5-f000-routing-payload-integration` / `/Users/jessewhite/.codex/worktrees/9b0b/qw4` | `docs/backlog/feature-000-phase0-transport-finding.md`, `docs/backlog/feature-002-fused-gating-zero-copy-routing.md`, `docs/findings/phase0-routing-payload-scaffold.md`, `tools/model_inspect/README.md`, `configs/qwen3_phase0_routing_payload.json`, `configs/schemas/phase0-routing-payload.schema.json`, `tests/model/test_phase0_routing_payload.py`, `docs/coordination/active-board.md` | `make phase0-routing-payload-validate`; `PYTHONPYCACHEPREFIX=/private/tmp/qw4-pycache python3 -m unittest tests.model.test_phase0_routing_payload`; `make test`; `git diff --check` passed | Integrates the merged scaffold into DS5-F000/F002 planning language without treating it as F002 runtime work. DS5-F002 remains blocked because `DS5-F000` is not complete. |
| DS5-F001B | unassigned | queued after `DS5-F001A` and Phase 0 go/no-go | fresh branch needed from `main` | runtime startup paths, `src/model/`, `tools/model_inspect/`, `configs/`, `docs/findings/`, `docs/backlog/` | startup/warmup memory ledger validation and worker ownership logs | Prove runtime placement behavior separately from scaffold/planning evidence. |
| F | unassigned | merged seed | PR #2 and later integration branches | `tools/report/`, `publication/`, `docs/findings/` | report generation from fixture artifacts | `docs/work-packs/2026-07-09-overnight/agent-f-reporting-publication.md` |

## Worktree Census

Classification rules: `active` means still tied to an open coordination task or this census branch; `merged` means the task/PR appears merged and the clean worktree can be considered for pruning after confirmation; `stale-clean` means a clean detached duplicate with no apparent unique local state; `needs-rescue` means uncommitted changes, unmerged commits, or unclear useful state; `unknown` means there is not enough evidence to classify safely.

| Path | Branch or commit | Clean/dirty | Related PR/branch/task | Classification | Recommendation | Prune safety |
|---|---|---|---|---|---|---|
| `/Users/jessewhite/Code/personal/qw4` | `main` at `90b3fbd` | clean | primary checkout, `origin/main` | active | Preserve as stable integration checkout. | preserve |
| `/Users/jessewhite/.codex/worktrees/5e1a/qw4` | `codex/arb-plan-refresh` at `4cbd099` plus PR #14 board update | dirty | draft PR #14 | active | Review and merge after validation; preserve until merged or explicitly abandoned. | preserve |
| `/Users/jessewhite/.codex/worktrees/b5b8/qw4` | `codex/ds5-f001-pdd-artifacts` at `0c9c944` | clean | PR #12 merged to `main` at `90b3fbd` | merged | Cleanup candidate after owner confirmation. | confirm before prune |
| `/Users/jessewhite/.codex/worktrees/dd81/qw4` | `codex/ds5-f000-routing-payload-scaffold` | unknown | Phase 0 routing-payload scaffold branch | active | Preserve until scaffold branch/PR state is confirmed. | preserve |
| `/Users/jessewhite/.codex/worktrees/9b0b/qw4` | `codex/ds5-f000-routing-payload-integration` | clean after follow-up commit | DS5-F000 routing-payload integration follow-up | active | Review draft PR when opened. | preserve |

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
| `codex/arb-plan-refresh` | superseded by PR #15 | PR #14 conflicted after accidental PR #13 merge. PR #15 applied equivalent ARB-plan content on top of current `main`. | Preserve only until branch cleanup is explicitly confirmed. |
| `codex/ds5-f001-pdd-artifacts` | merged branch cleanup | Branch tip `0c9c944` is included in the PR #12 merge at `90b3fbd`; worktree `/Users/jessewhite/.codex/worktrees/b5b8/qw4` is clean. | Delete branch or prune worktree only after separate confirmation. |
| `codex/ds5-f000-routing-payload-scaffold` | active/cleanup pending | Worktree `/Users/jessewhite/.codex/worktrees/dd81/qw4` exists at `14ac8d7`; scaffold is now treated as DS5-F000 preparatory evidence. | Preserve until PR/merge state is confirmed. |
| `codex/ds5-f000-routing-payload-integration` | validation passed; ready for review | Follow-up branch from current `origin/main` integrates routing-payload scaffold language into DS5-F000/F002 docs. | Review draft PR when opened. |
| `codex/ds5-f000-local-artifact-rehearsal` | validation passed; ready for review | Local MacBook-only DS5-F000L artifact/report rehearsal from current `origin/main`. | Review as prep-only artifact plumbing. It is not target-hardware evidence and does not change the DS5-F000 go/no-go. |

## Stale Or Detached Worktrees Needing Owner Confirmation

| Worktree set | State | Confirmation needed |
|---|---|---|
| None detected in current `git worktree list` | Current worktrees are `main`, `codex/arb-plan-refresh`, `codex/ds5-f001-pdd-artifacts`, and `codex/ds5-f002-routing-scaffold`. | Preserve active/review worktrees until their branches are resolved. |

## Integration Queue

| Item | Source | Status | Coordinator notes |
|---|---|---|---|
| Confirm build and test commands | all tasks | open | Keep commands in runbooks once stable. |
| Decide whether to keep `docs/backlog/` as aliases only | coordination | open | `docs/backlog/README.md` is currently a real feature catalogue; keep `docs/coordination/` as the active operating board. |
| Incorporate ARB feedback into feature plan | PR #15 / `/Users/jessewhite/Downloads/20260609-ARB/20260609-ARB.md` | merged | PR #15 reverted accidental PR #13 and landed the ARB project plan, splitting `DS5-F001` into `DS5-F001A` and `DS5-F001B`, with `DS5-F000` inserted before fused routing. |
| Review routing-payload scaffold against ARB gate order | `codex/ds5-f000-routing-payload-integration` | ready for review | Treat scaffold validation as DS5-F000 preparatory schema/test evidence only. `DS5-F001A` is complete via PR #19, and DS5-F002 remains blocked until `DS5-F000` is complete. |
| Prepare local-only DS5-F000 rehearsal | `DS5-F000L` | validation passed; ready for review | MacBook-only artifact/report rehearsal passed fixture validation, summary generation, `make test`, and `git diff --check`. Review as prep-only plumbing; do not claim target-hardware evidence or proceed to `DS5-F001B`/`DS5-F002`. |
| Clean up merged F001 artifact branch/worktree | `codex/ds5-f001-pdd-artifacts` | open | PR #12 is merged and the worktree is clean; prune/delete only after explicit branch-cleanup confirmation. |

## Coordinator Checklist

1. Pull or inspect each worktree.
2. Read each handoff before diff review.
3. Run the validation command listed in the task board.
4. Check shared files for conflicting edits.
5. Update task status and integration queue.
6. Merge or reassign only after validation results are recorded.

## Next Coordinator Actions

1. Start `DS5-F000L` from current `main` while only the MacBook Air is available; keep it explicitly local-only and prep-only.
2. Run `DS5-F000` on the target A/B/C topology when cluster hardware is available, before fused routing or model-runtime work.
3. Keep `DS5-F001B` and `DS5-F002` blocked until `DS5-F000` target-hardware evidence supports continued distributed decode work.
4. Confirm whether to prune `/Users/jessewhite/.codex/worktrees/b5b8/qw4` and delete `codex/ds5-f001-pdd-artifacts` now that PR #12 is merged.
5. Delete branches only after a separate branch-cleanup confirmation pass.
6. Start any new DS5 work from `main` with one task, one branch, one worktree, and one task-board row.
