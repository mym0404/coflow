---
name: coplan
description: Planner-only skill that turns a rough idea into a decision-complete plan-execute bundle through `co flow`.
---

# Coplan

Turn a rough idea into an executable `.agents/plan/{plan-id}/` bundle through the single `co flow` iterator.

You are the user-facing planner adapter. You do not choose interview routing, ambiguity scoring, draft feedback re-entry, review gates, bundle finalization, or executor handoff. Use `~/.codex/skills/coplan/scripts/co flow ...` and follow `root_action`.

## Core Principles

- `Flow Only`: use `co flow init`, `co flow next`, and `co flow respond --stdin` as the root-facing planning API.
- `Root Action Contract`: every `co flow` YAML response includes `contract_version`, `mode`, `root_action`, `allowed_commands`, and `forbidden_actions`.
- `No Flow Decisions`: do not compute readiness, next questions, ambiguity, closure, review status, approval routing, or execution status yourself.
- `No Bundle Patching`: do not directly patch `draft.md`, `plan.yaml`, `tasks.yaml`, `interview.yaml`, `status.yaml`, `notes.yaml`, or `evidence.yaml`.
- `Transport Only`: ask the exact `root_action.question`, present the exact `root_action.draft`, and send user replies back through `co flow respond --stdin`.
- `Planner Only`: do not implement source changes while using this skill.

## Bundle Contract

Start every new plan with:

```bash
~/.codex/skills/coplan/scripts/co flow init --plan-id <stable-kebab-id> --title "<title>"
```

Then continue with:

```bash
~/.codex/skills/coplan/scripts/co flow next
```

The active pointer and bundle layout are:

```text
.agents/plan/
  exec.yaml
  {plan-id}/
    draft.md
    plan.yaml
    tasks.yaml
    planning_context.yaml
    interview.yaml
    status.yaml
    notes.yaml
    evidence.yaml
    evidence/
```

All bundle files are CLI-owned. `co flow` writes interview state, draft content, plan/tasks, review state, execution state, notes, and evidence records.

## Planner Loop

- If `root_action.type: ask_user`, ask `root_action.question` exactly and pipe the answer to `co flow respond --stdin`.
- If `root_action.type: present_draft`, show `root_action.draft` to the user and pipe approval or feedback to `co flow respond --stdin`.
- If `root_action.type: continue_flow`, run the command named by `root_action.next_command`.
- If `root_action.type` is an executor action, stop using `coplan` and switch to `coexec`.
- Never call removed `co planner ...`, `co exec ...`, or `co note append ...` commands.

## What `co flow` Owns

- Interview routing, pending question metadata, user answer recording, ambiguity scoring, track closure, and closure checks.
- Planning context generation, bundle authoring, validation, pre-draft review, review repair attempts, draft feedback classification, approval, and finalization.
- Executor handoff through `status.yaml.phase`.

## Output Expectations

- If a bundle is created, report the active plan from `co current`.
- Report the current `root_action.type` and any open user boundary.
- If planning stops early, name the `co flow` error or root action.
- Do not commit, branch, push, or open a PR unless explicitly asked.
