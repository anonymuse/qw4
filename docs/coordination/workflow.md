# Sustainable Workflow

Status: recommended operating model.

This workflow is for coordinating DS5 across Codex chats, agents, tasks, and Git worktrees without losing track of active state.

## Mental Model

Use three separate layers:

| Layer | What belongs here | What does not belong here |
|---|---|---|
| Chat | Short-lived execution and clarification | Durable task state |
| `docs/coordination/active-board.md` | Current task state, ownership, branch, validation, handoff | Long design arguments |
| Git branch/worktree | Actual code and docs changes for one task | Multiple unrelated tasks |

If a fact must survive beyond the current chat, put it in the active board, a task file, a runbook, or an ADR.

## The Simple Rule

One task gets one branch, one worktree, and one task-board row.

Do not let one worktree become a kitchen sink for multiple agents. Do not let one agent keep working in detached HEAD after it has useful changes.

## Recommended Local Layout

Keep the primary checkout as the stable integration view:

```text
/Users/jessewhite/Code/personal/qw4
```

Use Codex-created worktrees as disposable task spaces:

```text
/Users/jessewhite/.codex/worktrees/<id>/qw4
```

The primary checkout should usually stay on `main`. Task work should happen in a branch named for the work:

```text
codex/coordination-workflow
codex/agent-e-placement-feasibility
codex/transport-loopback-smoke
```

## Starting A Task

1. Open or create one worktree for the task.
2. Create a branch before editing.
3. Add or update one row in `docs/coordination/active-board.md`.
4. Put the branch/worktree in that row.
5. Give the agent a prompt that starts with the task ID and owned paths.

Prompt header example:

```text
Task: E - placement feasibility
Branch: codex/agent-e-placement-feasibility
Owned paths: src/model/, tools/model_inspect/, tools/quant/
Start with docs/coordination/README.md and docs/coordination/active-board.md.
End with the handoff template.
```

## During A Task

- Keep edits inside owned paths unless the active board says otherwise.
- If a shared file must change, note it in the handoff.
- Run the validation command listed in the active board.
- Update the task row when status changes.
- Do not use chat as the only record of decisions.

## Ending A Task

Every task should end in exactly one of these states:

| State | Meaning | Next action |
|---|---|---|
| Committed | Work is complete and committed on a branch | Review, PR, or merge |
| Partial | Useful work exists but is not complete | Commit with honest message or leave clearly marked |
| Blocked | Cannot proceed without a decision or missing input | Record blocker in active board |
| Abandoned | Work should not continue | Preserve notes, then remove stale worktree when safe |

Use `docs/coordination/handoff-template.md` for the final note.

## Daily Coordinator Pass

Run this from the primary checkout:

```sh
git worktree list
git branch --all --verbose --no-abbrev
```

Then update `docs/coordination/active-board.md`:

- mark merged tasks as done;
- mark stale detached worktrees as inspect or remove;
- record branches waiting for review;
- record blocked tasks with the exact decision needed.

## Pruning Rule

A worktree can be removed when all are true:

- its useful changes are committed, merged, or explicitly abandoned;
- no task-board row points to it as active;
- no agent is still using that Codex thread.

Prefer pruning stale worktrees during the daily coordinator pass, not while an agent is mid-task.

## Commit And PR Policy

Use direct commits for small docs-only coordination changes when you are working solo.

Use PRs when:

- code changes behavior;
- multiple agents touched nearby files;
- the branch is a checkpoint you may want to compare or revert;
- you want GitHub checks or comments to become part of the coordination record.

The default sustainable path is:

1. branch;
2. focused changes;
3. validation;
4. commit;
5. PR only if review or CI adds value.

## Current Cleanup Recommendation

The current repository has several Codex worktrees, including detached HEAD worktrees at the same commit. Do not delete them blindly. First classify each one:

| Category | Action |
|---|---|
| Named branch with unique commits | Review and merge/close |
| Detached HEAD with uncommitted changes | Create a branch or commit elsewhere before pruning |
| Detached HEAD with no changes at `main` | Safe candidate for removal after confirming no active thread uses it |
| Backup branch | Keep until the related work is merged and verified |
