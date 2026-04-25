# Coplan Workflow Reference

This is the graph-free, agent-facing workflow reference for the `coplan` skill.
Use `COPLAN.md` only for user-facing Mermaid diagrams.
Keep this file aligned with `SKILL.md`, `agents/openai.yaml`, `scripts/co`, and the other files under `references/` whenever the planning flow, CLI contract, Codex CLI interaction, bundle schema, or gates change.

## Role Contract

| Actor | Responsibility |
|---|---|
| User | Supplies intent, interview answers, draft feedback, and approval. |
| Root agent | Calls `co flow`, asks exact questions, presents exact drafts, and transports responses. |
| `co` CLI | Owns bundle state, interview routing, scoring, bundle authoring, validation, review, approval, finalization, and executor handoff. |
| Codex CLI agents | Return schema-bound JSON for interview actions, ambiguity scoring, bundle authoring, draft feedback classification, and pre-draft review. |
| Bundle files | Store durable state under `.agents/plan/{plan-id}/`. |

## Public Contract

Root-facing mutation is limited to:

```bash
co flow init --plan-id <stable-kebab-id> --title "<title>" [--replace]
co flow next
co flow respond --stdin
co flow status
```

`co flow` returns YAML containing `contract_version`, `mode`, `root_action`, `allowed_commands`, and `forbidden_actions`.

Root-agent rules:

- Parse `root_action.type` before acting.
- Use only `allowed_commands`.
- Never perform `forbidden_actions`.
- Do not call `co planner ...`, patch bundle files, or choose the next flow step.

## Root Loop

| `root_action.type` | Root behavior |
|---|---|
| `continue_flow` | Run `root_action.next_command`, normally `co flow next`. |
| `ask_user` | Ask `root_action.question` exactly and pipe the user's answer to `co flow respond --stdin`. |
| `present_draft` | Present `root_action.draft` exactly and pipe approval or feedback to `co flow respond --stdin`. |
| `execute_task` | Planning is complete; switch to `coexec`. |
| `repair_task` | Stop using `coplan`; switch to `coexec` because execution has begun. |
| `report_halt` | Report the returned halt reason. |
| `report_complete` | Report completion if returned after planner-to-executor handoff logic. |

## CLI-Owned Planning Loop

The root does not execute the internal rows in this table.
They explain what `co flow next/respond` may do before emitting the next root boundary.

| Area | CLI-owned behavior | Possible root boundary |
|---|---|---|
| Init | Create `exec.yaml`, bundle files, initial status, and open interview tracks. | `continue_flow` |
| Pending question | Re-emit the pending question if user input is required. | `ask_user` |
| Interview intake | Record a pending user answer from `co flow respond --stdin` and clear pending metadata. | none until next boundary |
| Deterministic coverage | Record safe repo or research facts when they do not choose user-visible behavior. | none until next boundary |
| Interview action | Call the ask-next Codex CLI agent when deterministic coverage cannot choose the next step. | `ask_user` or internal continuation |
| Scoring | Call the ambiguity scorer, normalize clarity, and enforce freshness for the current round count. | `ask_user` or internal continuation |
| Closure | Close tracks only when coverage, ambiguity, clarity floors, pending question, and closure checks pass. | none until authoring/review boundary |
| Bundle authoring | Call `bundle_author` to generate `draft.md`, `plan.yaml`, and `tasks.yaml`. | none until review passes |
| Deterministic validation | Validate required fields, task DAG, final verification, evidence paths, and status consistency. | none until valid |
| Pre-draft review | Run `contract_reviewer` and `verification_reviewer` in parallel, then join results. | `present_draft` when both pass |
| Review repair | Feed reviewer findings back to `bundle_author`, rewrite, revalidate, and rerun review. | none until review passes |
| Draft approval | Approve, finalize, set execution-ready state, and claim the first executable task. | `execute_task` |
| Draft feedback | Classify feedback as approval, wording change, or meaning change. | `present_draft`, `ask_user`, or `execute_task` |

## Codex CLI Subagents

Codex CLI agents are private implementation details of `co`.
The root agent never invokes them directly.

| Role | Output contract | Used for |
|---|---|---|
| ask-next agent | Schema-bound action JSON | Choosing the next interview action when CLI rules need AI judgment. |
| ambiguity scorer | Schema-bound clarity JSON | Scoring goal, constraints, success criteria, and brownfield context. |
| bundle_author | Schema-bound bundle content | Writing draft, plan, and tasks from the closed interview. |
| contract_reviewer | PASS/FAIL JSON | Checking hidden decisions, scope drift, contradictions, task DAG assumptions, file scope, and acceptance criteria. |
| verification_reviewer | PASS/FAIL JSON | Checking verification commands, evidence meaning, final verification, and success signals. |
| draft feedback classifier | Schema-bound classification JSON | Routing approval, wording-only feedback, and meaning-changing feedback. |

## Draft Feedback Rules

| Feedback class | CLI behavior |
|---|---|
| `approve` | Approve the draft and finalize the plan for execution. |
| `wording_change` | Rewrite user-facing wording, revalidate, rerun review, and present the draft again. |
| `meaning_change` | Reopen the affected interview track, record the feedback as a material answer, rescore, reclose if possible, regenerate/review the bundle, then emit the next root boundary. |

## Internal Gates

| Gate | Enforced by |
|---|---|
| Interview schema, route/source, focus, user-judgment coverage | `co flow next/respond` |
| Ambiguity threshold and clarity floors | `co flow next/respond` through scorer agent and CLI normalization |
| Track closure and closure checks | `co flow next/respond` |
| Bundle schema and task DAG | `co flow next/respond` before draft presentation |
| Pre-draft review freshness | `co flow next/respond` |
| Approval and finalization | `co flow respond --stdin` |

## Non-Negotiable Boundaries

- Bundle files remain CLI-owned.
- Root asks and presents exact `root_action` content.
- Root never computes interview route, ambiguity, closure readiness, review pass state, approval routing, finalization, or executor handoff.
- Root never edits `draft.md`, `plan.yaml`, `tasks.yaml`, `planning_context.yaml`, `interview.yaml`, `status.yaml`, `notes.yaml`, or `evidence.yaml`.
