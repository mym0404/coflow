# Coexec Workflow Reference

This is the graph-free, agent-facing workflow reference for the `coexec` skill.
Use `COEXEC.md` only for user-facing Mermaid diagrams.
Keep this file aligned with `SKILL.md`, `agents/openai.yaml`, `skills/coplan/scripts/co`, and the other files under `references/` whenever execution order, CLI output, state mutation, evidence, repair, halt, or finish rules change.

## Role Contract

| Actor | Responsibility |
|---|---|
| User | Receives halt reasons and completion reports. |
| Root agent | Implements only the current task returned by `co flow`. |
| `co` CLI | Owns execution phase transitions, task selection, claims, evidence records, repair records, halt, and finish gates. |
| Bundle files | Store the approved contract and execution state under `.agents/plan/{plan-id}/`. |

## Public Contract

Root-facing executor mutation is limited to:

```bash
co flow next
co flow evidence --step <step-id> --command "<cmd>" --exit-code <code> --success true|false --stdin
co flow repair --field <path> --reason "..." --set|--add|--remove <yaml>
co flow halt --kind user_decision|external_environment --reason "..."
co flow status
```

The root does not call `co exec ...`, claim tasks, complete tasks, or finish execution.

## Root Loop

| `root_action.type` | Root behavior |
|---|---|
| `continue_flow` | Run `root_action.next_command`, normally `co flow next`. |
| `execute_task` | Edit source only within `root_action.task`, run the named verification, and record output through `co flow evidence`. |
| `repair_task` | Repair only inside the current task contract, rerun verification, and record output through `co flow evidence`. |
| `report_halt` | Stop and report `root_action.halt`. |
| `report_complete` | Report final completion. |

## CLI-Owned Execution Loop

The root does not execute the internal rows in this table.
They explain what `co flow next/evidence/repair/halt` may do before emitting the next root boundary.

| Area | CLI-owned behavior | Possible root boundary |
|---|---|---|
| Start | Move `ready_for_exec` to `executing` when execution begins. | `continue_flow` or `execute_task` |
| Claim | Select and claim the first ready task when no current task exists. | `execute_task` |
| Current task | Re-emit the current task while it remains `Doing`. | `execute_task` |
| Evidence intake | Store command output, exit code, success flag, artifact path, and manifest entry. | none until completion check |
| Failed evidence | Keep the task `Doing`, append a risk note, and preserve current task ownership. | `repair_task` |
| Completion gate | Check required expected evidence for the current task. | `execute_task` or internal continuation |
| Task completion | Mark the current task `Done` and clear `current_task`. | next claim, `report_complete`, or halt/error boundary |
| Next task | Claim the next ready task after dependencies pass. | `execute_task` |
| Finish | Complete only when all tasks and final verification are `Done`. | `report_complete` |
| Halt | Record halt only for `user_decision` or `external_environment`. | `report_halt` |
| Repair | Modify only allowed task envelope fields and append a repair note. | `repair_task` or next execution boundary |

## Evidence Contract

Record verification output through `co flow evidence`:

```bash
<command> 2>&1 | co flow evidence \
  --step <step-id> \
  --command "<command>" \
  --exit-code <code> \
  --success true|false \
  --stdin
```

Evidence is not complete just because a loose file exists under `evidence/`.
The CLI must record the evidence in `evidence.yaml`.

Successful evidence can complete the current task and advance to the next root boundary.
Failed evidence keeps the task `Doing`, records a risk note, and returns `repair_task`.

## Repair Contract

Repair is limited to the current task envelope:

- `files`
- `implementation_notes`
- `verification`

Repair must not modify:

- task id, title, kind, order, or dependencies
- acceptance criteria
- reopen conditions
- `plan.yaml`
- user-visible scope, non-goals, or success criteria

## Halt Contract

Halt only for:

- `user_decision`
- `external_environment`

`halted` is not complete and cannot return `report_complete`.

## Execution Gates

| Gate | Enforced by |
|---|---|
| Start | `co flow next` |
| Ready task claim | `co flow next` |
| One `Doing` task | `co flow next` and `co flow evidence` |
| Evidence ledger | `co flow evidence` |
| Task completion | `co flow evidence` |
| Repair envelope | `co flow repair` |
| Halt kind | `co flow halt` |
| Finish | `co flow next` |

## Non-Negotiable Boundaries

- Root implements only the current task returned by `root_action.task`.
- Root never chooses, claims, completes, skips, or reorders tasks.
- Root never broadens user-visible behavior, acceptance criteria, non-goals, dependencies, or task order during execution.
- Root never edits bundle YAML directly.
