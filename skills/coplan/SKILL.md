---
name: coplan
description: Planner-only skill that turns a rough idea into an ambiguity-scored plan-execute bundle managed through `co`.
---

# Coplan

Turn a rough idea into a decision-complete plan-execute bundle under `.agents/plan/{plan-id}/`.

You are the planner. You do not implement code, execute tasks, or close work items. Use `~/.codex/skills/coplan/scripts/co` for state, validation, Codex CLI interview agents, ambiguity scoring, and pre-draft review.

## Core Principles

- `CLI For State`: use `co` for every state transition, interview ledger update, event, note, evidence, validation, and review gate.
- `Direct Bundle Drafting`: after `co planner generate-skeleton`, directly patch only `draft.md`, `plan.yaml`, and `tasks.yaml` with the smallest correct diff.
- `Ledger Files Are CLI-Owned`: never directly edit `interview.yaml`, `status.yaml`, `events.yaml`, `notes.yaml`, or `evidence.yaml`.
- `Explore Before Asking`: discover repository facts first, then ask only about intent, tradeoffs, or missing decisions.
- `Follow Co Output`: do not compute readiness or gate state yourself; call `co`, read stdout YAML, and follow `required_action` and `next_command`.
- `Pre-Draft Review`: run Codex CLI plan review before showing `draft.md` to the user.
- `Planner Only`: do not mutate source code or execute task implementation steps.

## Bundle Contract

Start every new plan with:

```bash
~/.codex/skills/coplan/scripts/co planner init --plan-id <stable-kebab-id> --title "<title>"
```

The active pointer and bundle layout are:

```text
.agents/plan/
  exec.yaml
  {plan-id}/
    draft.md
    plan.yaml
    tasks.yaml
    interview.yaml
    status.yaml
    notes.yaml
    events.yaml
    evidence.yaml
    evidence/
```

Review state is stored in `status.yaml.review`. New work uses the current structure above.

Before writing bundle content, read [references/root-agent-co-guide.md](references/root-agent-co-guide.md) and [references/bundle-schema.md](references/bundle-schema.md). Treat [references/gates-and-examples.md](references/gates-and-examples.md), [references/interview-algorithm.md](references/interview-algorithm.md), and [references/codex-cli-reviewer.md](references/codex-cli-reviewer.md) as maintenance references for changing `co`, not as normal root-agent control logic.

## Planner Workflow

### Phase 1: Init, Explore, Interview, Score

- Run `co planner init` before creating bundle content.
- Parse every `co` stdout YAML response and follow `required_action`.
- Run `next_command` when present and no user decision is needed.
- Run a local repository sweep before any interview question.
- Use `co planner interview ask-next --runner codex` to let `co` choose the next interview action.
- If stdout includes `pending_user_question`, ask that exact question and record the answer with `co planner interview record`.
- If stdout reports a material gap that the root agent can see, use `co planner interview blocker add|clear --reason "..."`.
- Attempt `co planner interview close --summary "..."` only when `required_action` indicates the interview is ready to close; if it fails, satisfy the returned error and `required_action`.

### Phase 2: Skeleton, Direct Patch, Pre-Draft Review

- Run `co planner generate-skeleton` after the interview closes.
- Directly patch only `draft.md`, `plan.yaml`, and `tasks.yaml` until the bundle is decision-complete.
- Run `co planner validate` for structural validation before approval.
- Run `co planner review run --runner codex --stage pre-draft`.
- Fix valid reviewer findings by directly patching the relevant bundle files, then rerun the failed review path.
- Do not show `draft.md` to the user until pre-draft review passes.

### Phase 3: User Draft Review

- Present `draft.md` from `co show --file draft`.
- If feedback changes scope, outputs, verification, constraints, or stop conditions, reopen the relevant track first with `co planner interview track open <track> --reason "draft feedback"`.
- For meaning-changing feedback, create a matching pending question with `co planner interview ask`, then record the supplied user answer with `co planner interview record`.
- After meaning-changing feedback, rerun ambiguity scoring, close the affected track and interview, patch only the impacted bundle files, then rerun `co planner validate` and pre-draft review.
- If feedback changes wording only, patch `draft.md` only.
- On approval, run:

```bash
~/.codex/skills/coplan/scripts/co planner approve-draft --comment "<summary>"
```

### Phase 4: Finalize

- Run `co planner validate`.
- Run `co planner finalize`; it requires a closed ambiguity-ready interview, fresh pre-draft review PASS, approved draft, and valid plan/tasks.
- Report the active plan path from `co current`, the files changed, and any open gate.
- Do not implement source changes or execute the plan.

## Task Writing Rules

- `tasks.yaml` is static. It contains no `status`.
- Every task includes `id`, `kind`, `title`, `depends_on`, `start_when`, `files`, `context`, `must_do`, `must_not_do`, `implementation_notes`, `verification`, `acceptance_criteria`, `expected_evidence`, and `reopen_when`.
- `kind` is `execution`, `checkpoint`, or `final_verification`.
- `depends_on` is the machine-readable DAG. `start_when.description` is the human-readable readiness guard.
- `verification.steps[]` must include `id`, `command`, and `success_signal`.
- `expected_evidence[]` maps each required step to an `evidence/...` artifact path.
- At least one task must use `kind: final_verification`.

## Interview Rules

- `code_fact`: use only for repo facts found by local exploration or Codex CLI read-only inspection.
- `user_decision`: use for goals, scope, non-goals, success criteria, preferences, and tradeoffs.
- `code_plus_decision`: use when code facts exist but applying them to this plan needs human judgment.
- `research_confirmation`: use for external facts that require web or documentation research.
- `user_decision` and `code_plus_decision` require a pending user question and an actual user answer.
- Required tracks: `scope`, `non_goals`, `outputs`, `verification`, `constraints`, and `stop_conditions`.
- `scope`, `outputs`, and `verification` each require at least one user-judgment round.
- After three consecutive non-user answers, the next answer must require user judgment.
- After two consecutive rounds on one track, ask a zoom-out question for another open track.
- Do not manually compute ambiguity, clarity floors, closure readiness, or review readiness; run the `co` command indicated by stdout and follow `required_action`.

## Output Expectations

- If a bundle is created, report the active plan from `co current`.
- Report direct bundle files changed and CLI-managed state transitions separately.
- If planning stops before finalization, name the open gate.
- Do not commit, branch, push, or open a PR unless explicitly asked.
