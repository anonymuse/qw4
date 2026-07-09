# AGENTS.md

## DS5 Codex Workflow

- Start each task from current `main`.
- Use one task, one branch, one worktree, and one pull request.
- Name task branches `codex/<task-name>`.
- Keep `/Users/jessewhite/Code/personal/qw4` as the stable `main` integration checkout.
- Use Codex-managed worktrees under `/Users/jessewhite/.codex/worktrees/<id>/qw4` for task work.
- Create or switch to the task branch before editing.

## Required Startup Reading

Before editing, read:

- `README.md`
- `docs/coordination/README.md`
- `docs/coordination/workflow.md`
- `docs/coordination/active-board.md`

Then check `git status -sb`.

## Task Discipline

- Keep changes scoped to the task's owned paths.
- Update `docs/coordination/active-board.md` or the relevant task file when task state should persist beyond the chat.
- Do not use chat transcripts as the only durable task state.
- Run relevant validation before committing.
- Commit focused changes on the task branch.
- Open a draft PR when GitHub is available.

## Cleanup Discipline

- Do not delete worktrees or branches without explicit user confirmation.
- Prune worktrees only after useful changes are committed, merged, or explicitly abandoned.
- Delete local branches only after confirming they are merged into `origin/main`.
- Treat backup, pre-rebase, divergent, dirty, or unclear branches as preserve-first.
