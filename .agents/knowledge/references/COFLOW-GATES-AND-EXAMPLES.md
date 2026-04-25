# Gates And Examples

This file defines the plan-execute gates enforced by `co flow`.
It is a CLI maintenance reference, not default root-agent context.

## Planner Readiness Gate

A bundle is planner-ready only when:

- `.agents/plan/exec.yaml` points to the active `.agents/plan/{plan-id}/`.
- The bundle was created with `co flow init`.
- `interview.yaml` is closed with every required ambiguity track closed.
- latest ambiguity score is fresh, `<= 0.2`, and all clarity floors pass.
- `draft.md` is written for user review and approved through `co flow respond --stdin`.
- `plan.yaml` contains goal, context, non-goals, constraints, success criteria, verification policy, execution strategy, and stop conditions.
- `tasks.yaml` contains no status fields.
- `tasks.yaml` has at least one `kind: final_verification` task.
- all task dependencies point to known tasks and form an acyclic graph.
- every task has structured verification steps and expected evidence.
- every expected evidence path is a relative path under `evidence/`.
- `status.yaml` task ids match `tasks.yaml` task ids.
- `status.yaml.review.status` is `passed`.
- `status.yaml.review.fingerprint` matches current `plan.yaml`, `tasks.yaml`, and `interview.yaml`.
- `notes.yaml` and `evidence.yaml` are present and CLI-managed.
- `status.yaml.phase` reaches `ready_for_exec`.

## Interview Gate

- `co flow init` creates `interview.yaml` with required tracks open.
- `co flow next/respond` records every material question and answer.
- User-judgment answers require a matching pending question created by `co flow`.
- Route sources must match `from-code...`, `from-user...`, or `from-research...`.
- Closure requires at least one round for every required track.
- Closure requires user-judgment rounds on `scope`, `outputs`, and `verification`.
- Closure requires one answered hidden-assumption follow-up after ambiguity scoring reaches readiness.
- `code_fact` and `research_confirmation` increment `non_user_answer_streak`.
- `user_decision` and `code_plus_decision` reset `non_user_answer_streak`.
- Once `non_user_answer_streak` reaches 3, the next record must be `user_decision` or `code_plus_decision`.
- Once one track has two consecutive rounds, the next record must use another open track.
- Ambiguity scoring must produce a fresh score for the current round count.
- `ambiguity = 1 - sum(clarity_i * weight_i)` must be `<= 0.2`.
- Clarity floors must pass: goal `0.75`, constraints `0.65`, success criteria `0.70`, brownfield context `0.60`.
- Meaning-changing draft feedback reopens the relevant track internally before new answers are recorded.

## Pre-Draft Review Gate

- Pre-draft review runs through `co flow next/respond`.
- `contract_reviewer` and `verification_reviewer` run in parallel.
- Both reviewers must return `PASS`.
- Review results are recorded in `notes.yaml`.
- Passing review stores `status.yaml.review.status: passed` and a fingerprint over `plan.yaml`, `tasks.yaml`, and `interview.yaml`.
- If those files change after review, `co flow` reruns review before presenting or approving the draft.

## Execution Gate

The executor must:

- Start each loop with `co flow next`.
- Execute only the task returned by `root_action.task`.
- Keep exactly one task in `Doing`.
- Record verification artifacts through `co flow evidence`.
- Repair only through `co flow repair`.
- Halt only through `co flow halt`.
- Finish only when `co flow next` returns `root_action.type: report_complete`.

## In-Contract Failure Gate

- Verification failures, missing evidence, stale file scope, and in-contract repair needs keep the task in `Doing`.
- Use `co flow halt` only for `user_decision` or `external_environment`.
- `halted` is not complete and cannot return `report_complete`.

## Evidence Gate

A task with `verification.evidence_required: true` is done only when:

- each required `expected_evidence` entry has a matching successful `evidence.yaml` record
- the artifact path points under the bundle `evidence/` directory
- the recorded `task_id` and `step_id` match the task contract

## Repair Gate

`co flow repair` may modify only contract-compatible envelope fields:

- `files`
- `implementation_notes`
- `verification`

It must append one repair note in `notes.yaml`.

It must not modify:

- task id, title, kind, order, dependencies, acceptance criteria, or reopen conditions
- `plan.yaml`
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
