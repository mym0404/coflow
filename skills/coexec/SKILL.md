---
name: coexec
description: Executor-only skill that runs the active `.agents/plan/{plan-id}` YAML bundle through `co`.
---

# Coexec

Run the active YAML plan-execute bundle selected by `.agents/plan/exec.yaml`.

You are the executor. You do not redesign the approved user contract. You execute locally and sequentially, using `~/.codex/skills/coplan/scripts/co` for every bundle read, write, state transition, event, note, and evidence operation. Do not read or edit bundle YAML files directly.

## Core Principles

- `Status First`: start each loop with `co exec status`; it is the current execution context and drift guard.
- `Follow Co Output`: treat `co` stdout YAML as the contract and follow `required_action`, `allowed_now`, and `forbidden_now`.
- `Static Contract, Dynamic State`: `tasks.yaml` is the immutable execution contract; `status.yaml` is current progress; `events.yaml` and `evidence.yaml` are CLI-managed append-only records.
- `Ready Before Doing`: only tasks returned by `co exec ready` may be claimed.
- `One Doing Task`: if a task is `Doing`, finish, repair, add evidence, or halt that task before claiming another.
- `In-Contract Failures Stay Doing`: ordinary failures keep the current task in `Doing` until repaired, evidenced, completed, or halted.
- `Halt Is Exceptional`: use `co exec halt` only for a real `user_decision` or `external_environment` stop condition.
- `User Contract Is Immutable`: do not change dependencies, task order, acceptance criteria, non-goals, or user-visible behavior during execution.
- `Repair Envelope Only`: `co exec repair` may modify only contract-compatible envelope fields such as `files`, `implementation_notes`, or `verification`.
- `Verify Ruthlessly`: do not mark a task done until required evidence is recorded and acceptance still fits the contract.

## Execution Workflow

Before the first `co` call, use the shared stdout contract in [../coplan/references/root-agent-co-guide.md](../coplan/references/root-agent-co-guide.md).

### Step 1: Load Current Context

Run:

```bash
~/.codex/skills/coplan/scripts/co exec status
```

Use its output as the source for:

- active plan id and directory
- current phase
- current `Doing` task, if any
- ready tasks
- allowed and forbidden commands
- required and recorded evidence
- current task files, verification steps, and acceptance criteria

Do not inspect bundle YAML files directly.

### Step 2: Start Or Continue Execution

- If phase is `ready_for_exec`, run `co exec start`.
- If phase is `executing` and a task is already `Doing`, continue that task.
- If phase is `executing` and no task is `Doing`, run `co exec ready` and claim exactly one ready task with `co exec claim <task-id>`.
- If phase is `halted`, stop and report the halt reason from `co exec status`.
- If phase is `complete`, report completion.

### Step 3: Execute The Current Task

- Use `co exec show-task <task-id>` or `co exec status` for the task contract.
- Work only inside the declared task scope unless the change is contract-compatible envelope drift.
- If file scope, implementation notes, or verification are stale but the user contract is unchanged, run `co exec repair <task-id> --field <path> --reason "..." --set|--add|--remove <yaml-value>`.
- If the next change would alter user-visible behavior, acceptance criteria, dependencies, task order, or non-goals, run `co exec halt --kind user_decision --task <task-id> --reason "..."`.
- If an external environment issue prevents progress after reasonable local repair, run `co exec halt --kind external_environment --task <task-id> --reason "..."`.

### Step 4: Record Evidence

After running a verification command, record its output through `co`:

```bash
<command> 2>&1 | ~/.codex/skills/coplan/scripts/co exec evidence add \
  --task <task-id> \
  --step <step-id> \
  --name <artifact-name.txt> \
  --command "<command>" \
  --exit-code <code> \
  --success true|false \
  --stdin
```

`co` writes the artifact under `evidence/`, appends the manifest record to `evidence.yaml`, and appends an event to `events.yaml`.

### Step 5: Complete Or Continue Repair

- Run `co exec complete-task <task-id>` only after acceptance criteria are satisfied and required evidence has been recorded.
- If completion fails because evidence is missing, keep the task in `Doing`, record or repair evidence, and retry.
- If verification fails but the failure stays inside the current task contract, keep the task in `Doing` and continue fixing in the same turn.
- After a task reaches `Done`, run `co exec status` again and continue to the next ready task.

### Step 6: Finish

- `co exec finish` is allowed only when every task is `Done` and every `kind: final_verification` task is `Done`.
- Do not declare completion before `co exec finish` succeeds.

## Hard Gates

- Do not read or write bundle YAML directly.
- Do not stop on a fixable in-contract failure.
- Do not claim a second task while one task is `Doing`.
- Do not mark a task done without required evidence in `evidence.yaml`.
- Do not finish before final verification tasks are done.

## Output Expectations

- If `co exec finish` succeeds, the first line of the final report must be exactly `최종 완료 🎉`.
- If execution stops early, the first line must name the open gate: current task, `halted` phase, or external environment issue.
- Report the active plan id and path from `co current`.
- Report task transitions, evidence records, repair events, and verification results.
