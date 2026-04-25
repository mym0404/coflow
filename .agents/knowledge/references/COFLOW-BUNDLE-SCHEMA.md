# Plan Bundle Schema

Each active plan is selected by `.agents/plan/exec.yaml` and stored under `.agents/plan/{plan-id}/`.
Use `~/.codex/skills/coplan/scripts/co.py flow` for CLI-owned state. Direct root-agent edits to bundle files are not part of the public workflow.
This is a CLI maintenance reference, not default root-agent context.

## Directory Layout

```text
.agents/plan/
  exec.yaml
  {plan-id}/
    plan_seed.yaml
    tasks.yaml
    interview.yaml
    status.yaml
    notes.yaml
    evidence.yaml
    flow_log.ndjson
    evidence/
```

## Public Commands

Mutation:

```bash
co.py flow init --plan-id <id> --title "<title>" (--prompt "<request>" | --stdin) [--replace]
co.py flow next
co.py flow respond --stdin
co.py flow evidence --step <step-id> --command "<command>" --exit-code <code> --success true|false --stdin
co.py flow repair --field <path> --reason "<reason>" --set|--add|--remove <yaml-value>
co.py flow halt --kind user_decision|external_environment --reason "<reason>"
co.py flow status
```

Read-only and diagnostics:

```bash
co.py current
co.py show --file tasks|plan-seed|interview|status|notes|evidence
co.py review-context
```

## `plan_seed.yaml`

`plan_seed.yaml` is the user-reviewed planning contract generated after closure audit passes.
`bundle_author` uses it as the source of truth for `tasks.yaml`.

Required top-level fields:

- `status`
- `generated_at`
- `round_count`
- `ambiguity_score_id`
- `closure_audit`
- `seed`

Required `seed` fields:

- `title`
- `goal`
- `context`
- `non_goals`
- `constraints`
- `success_criteria`
- `verification_expectations`
- `execution_boundaries`
- `source_round_ids`
- `deferred_items`
- `summary`

## `tasks.yaml`

`tasks.yaml` is the static execution contract written by `co.py flow`. It must not contain task status.
Global goal, constraints, non-goals, success criteria, execution boundaries, and verification expectations from `plan_seed.yaml` must be projected into task fields so the executor does not make planning decisions.

Required task fields:

- `id`
- `kind`: `execution`, `checkpoint`, or `final_verification`
- `title`
- `depends_on`
- `start_when.description`
- `files.primary`
- `files.generated_incidental`
- `context`
- `must_do`
- `must_not_do`
- `implementation_notes`
- `verification.evidence_required`
- `verification.steps`
- `acceptance_criteria`
- `expected_evidence`
- `reopen_when`

Every verification step requires `id`, `command`, and `success_signal`.
Every expected evidence item requires `step_id` and a relative `file` under `evidence/`.
At least one task must use `kind: final_verification`.
Task dependencies must point to known task ids and must not form a cycle.

## `interview.yaml`

`interview.yaml` is the CLI-owned Socratic ledger.
It stores the initial request, transcript, ambiguity state, closure audit state, deferred items, and plan seed review state.

Valid routes:

- `code_fact`: `from-code...`
- `user_decision`: `from-user...`
- `code_plus_decision`: `from-user...`
- `research_confirmation`: `from-research...`

Required review state fields under `seed_review`:

- `status`: `not_presented`, `presented`, or `approved`
- `fingerprint`
- `comment`
- `feedback`

Required `closure_audit` fields:

- `status`
- `summary`
- `material_blockers`
- `question`
- `round_count`
- `score_id`

Required `closure.checks` fields:

- `desired_output_explicit`
- `user_tradeoffs_explicit`
- `closure_audit_passed`
- `executor_determinism`
- `verification_proves_behavior`
- `no_material_questions`

`co.py flow` closes the interview only when:

- CLI-required extraction tracks are closed when present
- no pending user question remains
- at least three answered rounds exist
- ambiguity readiness has been observed twice in a row
- closure audit passed for the current round count and score id
- `plan_seed.yaml` exists for the current interview
- closure checks passed
- material blockers are empty
- latest ambiguity score is fresh for the current round count
- `ambiguity <= 0.2`
- clarity floors pass

## `status.yaml`

`status.yaml` stores current phase, review gate state, current task, task states, and halt state.

Valid phases:

- `planning`
- `seed_review`
- `ready_for_exec`
- `executing`
- `halted`
- `complete`

Valid review statuses: `not_run`, `passed`, `failed`.
Valid review stage: `bundle`.
Valid task states: `Todo`, `Doing`, `Done`.
Use `halt` only for `user_decision` or `external_environment`.

## `notes.yaml`

`notes.yaml` is append-only semantic memory. It records review findings, decisions, risks, revisions, repairs, and halt notes.
Task-related notes use `task:<task-id>` in `affects`.

## `evidence.yaml`

`evidence.yaml` is the append-only evidence manifest owned by `co.py flow evidence`.
Loose files under `evidence/` are not enough; a task is not complete until required artifacts are recorded in `evidence.yaml`.
