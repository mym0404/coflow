# Gates And Examples

This file defines the plan-execute gates enforced by `co.py flow`.
It is a CLI maintenance reference, not default root-agent context.

## Planner Readiness Gate

A bundle is planner-ready only when:

- `.agents/plan/exec.yaml` points to the active `.agents/plan/{plan-id}/`.
- The bundle was created with `co.py flow init`.
- `interview.yaml` stores the initial request and is closed by CLI-owned interview gates.
- latest ambiguity score is fresh, `<= 0.2`, and all clarity floors pass.
- completion candidate streak is at least 2.
- closure audit passed for the current score and round count.
- `plan_seed.yaml` exists and matches the closed interview.
- `tasks.yaml` contains no status fields.
- `tasks.yaml` has at least one `kind: final_verification` task.
- all task dependencies point to known tasks and form an acyclic graph.
- every task has structured verification steps and expected evidence.
- every expected evidence path is a relative path under `evidence/`.
- `status.yaml` task ids match `tasks.yaml` task ids.
- `status.yaml.bundle_inspection.author` records grounded bundle-author repo inspection.
- `interview.yaml.seed_review.status` reaches `approved`.
- `notes.yaml` and `evidence.yaml` are present and CLI-managed.
- `status.yaml.phase` reaches `ready_for_exec`.

## Interview Gate

- `co.py flow init` records the initial request in `interview.yaml.initial_context`.
- `co.py flow next/respond` records every material question and answer.
- User-judgment answers require a matching pending question created by `co.py flow`.
- Pending user questions carry 2-3 CLI-generated UI options with exactly one recommended option.
- Route sources must match `from-code...`, `from-user...`, or `from-research...`.
- Closure requires at least three answered rounds.
- The six interview tracks are extraction labels, not a fixed user-question checklist.
- Ambiguity scoring is not used for closure before the third answered round.
- Closure requires two consecutive readiness candidates.
- Closure requires a passed closure audit that checks material implementation decisions.
- Closure requires `plan_seed.yaml` before bundle authoring.
- Skip-eligible questions can be intentionally deferred and recorded in `deferred_items`.
- `code_fact` and `research_confirmation` increment `non_user_answer_streak`.
- `user_decision` and `code_plus_decision` reset `non_user_answer_streak`.
- Once `non_user_answer_streak` reaches 3, the next record must be `user_decision` or `code_plus_decision`.
- Once one track has two consecutive rounds, the next record must use another open track.
- Ambiguity scoring must produce a fresh score for the current round count.
- `ambiguity = 1 - sum(clarity_i * weight_i)` must be `<= 0.2`.
- Clarity floors must pass: goal `0.75`, constraints `0.65`, success criteria `0.70`, brownfield context `0.60`.
- Meaning-changing plan seed feedback reopens the relevant track internally before new answers are recorded.

## Bundle Authoring Gate

- `bundle_author` runs after `plan_seed.yaml` is current for the closed interview.
- `bundle_author` writes `tasks.yaml` content only through the CLI.
- Local schema validation must pass before the plan seed is presented.

## Execution Gate

The executor must:

- Start each loop with `co.py flow next`.
- Execute only the task returned by `root_action.task`.
- Keep exactly one task in `Doing`.
- Record verification artifacts through `co.py flow evidence`.
- Repair only through `co.py flow repair`.
- Halt only through `co.py flow halt`.
- Finish only when `co.py flow next` returns `root_action.type: report_complete`.

## In-Contract Failure Gate

- Verification failures, missing evidence, stale file scope, and in-contract repair needs keep the task in `Doing`.
- Use `co.py flow halt` only for `user_decision` or `external_environment`.
- `halted` is not complete and cannot return `report_complete`.

## Evidence Gate

A task with `verification.evidence_required: true` is done only when:

- each required `expected_evidence` entry has a matching successful `evidence.yaml` record
- the artifact path points under the bundle `evidence/` directory
- the recorded `task_id` and `step_id` match the task contract

## Repair Gate

`co.py flow repair` may modify only contract-compatible envelope fields:

- `files`
- `implementation_notes`
- `verification`

It must append one repair note in `notes.yaml`.

It must not modify:

- task id, title, kind, order, dependencies, acceptance criteria, or reopen conditions
- user-visible scope, non-goals, or success criteria

## Strong Task Example

```yaml
tasks:
  - id: T1
    kind: execution
    title: Add focused integration test
    depends_on: []
    start_when:
      description: Route is missing and test harness is available.
    files:
      primary:
        - tests/http_health.rs
      generated_incidental: []
    context: The endpoint contract should exist before handler wiring.
    must_do:
      - Match the existing integration test style.
    must_not_do:
      - Do not add unrelated assertions.
    implementation_notes:
      - Assert HTTP 200 and body OK.
    verification:
      evidence_required: true
      steps:
        - id: focused-before
          command: cargo test health_route_returns_ok -- --exact
          success_signal: The test compiles and fails only because the route is missing.
    acceptance_criteria:
      - The test asserts HTTP 200 and body OK.
    expected_evidence:
      - step_id: focused-before
        file: evidence/t1-focused-before.txt
    reopen_when:
      - HTTP harness or endpoint contract changes.
```
