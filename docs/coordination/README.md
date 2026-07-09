# Coordination

Status: active coordination baseline.

Use this directory as the stable entry point for multi-agent DS5 work. Date-stamped work packs can still exist, but agents should start here before reading a specific task file.

## Start Here For Each Agent

1. Read `README.md` at the repository root.
2. Read this file.
3. Read `docs/coordination/workflow.md`.
4. Read `docs/coordination/active-board.md`.
5. Read the task file assigned to the agent.
6. Check `git status --short` before editing.
7. Stay inside the task's owned paths unless the task explicitly allows a shared file edit.
8. End with a short handoff using `docs/coordination/handoff-template.md`.

## Coordination Model

| Layer | Purpose | Update cadence |
|---|---|---|
| Root `README.md` | Project source of truth and current thesis | Only when project direction changes |
| `docs/coordination/workflow.md` | Sustainable branch, worktree, task, and handoff workflow | When the coordination process changes |
| `docs/coordination/active-board.md` | Current task board, ownership, and integration state | Every active coordination session |
| `docs/work-packs/` | Dated batches of scoped agent work | When planning a batch |
| `docs/findings/` | Measured or publishable conclusions | After validated runs |
| `docs/decisions/` | Durable architectural decisions | When changing direction |
| `docs/runbooks/` | Commands and procedures | Whenever commands change |

## Worktree Rules

- Use one worktree per agent or major task.
- Keep branch names task-scoped, for example `codex/agent-e-placement-feasibility`.
- Put the active task ID in the first line of every agent prompt.
- Do not use chat transcripts as the only source of task state; update the active board or task file.
- Prefer small, reviewable changes that can merge independently.

## Path Ownership

Each active task should declare:

- owned paths;
- shared paths;
- forbidden paths;
- expected tests or validation commands;
- handoff notes.

Agents may edit owned paths freely within the task scope. Shared paths require a short note in the handoff. Forbidden paths require a new task or explicit coordinator approval.

## Handoff Contract

Every agent should finish with:

- task ID and branch/worktree;
- files changed;
- commands run and results;
- remaining risks or follow-up tasks;
- integration notes for the coordinator.

Use `docs/coordination/handoff-template.md` for consistency.
