---
name: coexec
description: Executor-only skill that runs the active `.agents/plan/{plan-id}` bundle through `co flow`.
---

# Coexec

Run the active plan-execute bundle selected by `.agents/plan/exec.yaml`.

You are the executor. You do not redesign the approved user contract or choose the next task. Use `~/.codex/skills/coplan/scripts/co flow ...` for bundle state, task selection, evidence, repair, halt, and finish gates. Do not read or edit bundle YAML files directly.

## Core Principles

- `Flow First`: start and resume with `co flow next`; use `co flow status` only for diagnostics.
- `Root Action Contract`: every flow response includes `contract_version`, `mode`, `root_action`, `allowed_commands`, and `forbidden_actions`.
- `One Current Task`: implement only the task in `root_action.task` when `root_action.type: execute_task`.
- `Evidence Through Flow`: after running a verification command, pipe output to `co flow evidence`.
- `Repair Through Flow`: if task metadata is stale but the user contract is unchanged, use `co flow repair`.
- `Halt Through Flow`: halt only for a real `user_decision` or `external_environment` stop condition.
- `No Direct State Changes`: never call removed `co exec ...`, mutate bundle YAML, claim tasks, complete tasks, or finish manually.

## Required Context

Always read these context docs first before running `co flow` with this skill.

Read [../coplan/references/root-agent-co-guide.md](../coplan/references/root-agent-co-guide.md) for the root-agent, CLI, stdout YAML, `root_action`, allowed command, and forbidden action contract.

Read [references/workflow.md](references/workflow.md) as the synchronized structured workflow reference for how root agent, `co` CLI, task state, evidence, repair, halt, and completion interact.

Use [../coplan/references/bundle-schema.md](../coplan/references/bundle-schema.md) to understand the approved static task contract and evidence ledger. Use [../coplan/references/gates-and-examples.md](../coplan/references/gates-and-examples.md) to understand execution, evidence, repair, halt, and finish gates.

These references explain the system boundary. They do not authorize choosing tasks, completing tasks, finishing execution, or editing CLI-owned bundle files directly.

## Execution Loop

Run:

```bash
~/.codex/skills/coplan/scripts/co flow next
```

Then follow `root_action.type`:

- `execute_task`: edit source files only within `root_action.task`, run the named verification, then record evidence.
- `repair_task`: repair within the current task contract, rerun verification, then record evidence.
- `report_halt`: stop and report `root_action.halt`.
- `report_complete`: report final completion.
- `continue_flow`: run `root_action.next_command`.

Record verification output with:

```bash
<command> 2>&1 | ~/.codex/skills/coplan/scripts/co flow evidence \
  --step <step-id> \
  --command "<command>" \
  --exit-code <code> \
  --success true|false \
  --stdin
```

Repair only the allowed task envelope:

```bash
~/.codex/skills/coplan/scripts/co flow repair \
  --field <files|implementation_notes|verification path> \
  --reason "<reason>" \
  --set|--add|--remove <yaml-value>
```

Halt with:

```bash
~/.codex/skills/coplan/scripts/co flow halt \
  --kind user_decision|external_environment \
  --reason "<reason>"
```

## Hard Gates

- Do not claim or switch tasks yourself.
- Do not complete a task yourself.
- Do not finish execution yourself.
- Do not mark evidence by writing loose files under `evidence/`.
- Do not widen scope, dependencies, acceptance criteria, non-goals, or user-visible behavior during execution.

## Output Expectations

- If `root_action.type: report_complete`, the first line of the final report must be exactly `최종 완료 🎉`.
- If execution stops early, name the current `root_action.type` or `root_action.halt`.
- Report evidence records, repair or halt notes, and verification results.
