# Gates And Examples

This file defines the plan-execute gates enforced by `co`.

## Planner Readiness Gate

A bundle is planner-ready only when:

- `.agents/plan/exec.yaml` points to the active `.agents/plan/{plan-id}/`.
- The bundle was created with `co planner init`.
- `interview.yaml` is closed with every required ambiguity track closed.
- latest ambiguity score is fresh, `<= 0.2`, and all clarity floors pass.
- `draft.md` is written for user review and approved through `co planner approve-draft`.
- `plan.yaml` contains goal, context, non-goals, constraints, success criteria, verification policy, execution strategy, and stop conditions.
- `tasks.yaml` contains no status fields.
- `tasks.yaml` has at least one `kind: final_verification` task.
- all task dependencies point to known tasks and form an acyclic graph.
- every task has structured verification steps and expected evidence.
- every expected evidence path is a relative path under `evidence/`.
- `status.yaml` task ids match `tasks.yaml` task ids.
- `status.yaml.review.status` is `passed`.
- `status.yaml.review.fingerprint` matches current `plan.yaml`, `tasks.yaml`, and `interview.yaml`.
- `events.yaml` and `evidence.yaml` are present and CLI-managed.
- `co planner finalize` succeeds.

## Interview Gate

- `co planner init` creates `interview.yaml` with required tracks open.
- The planner records every material question and answer through `co planner interview record`.
- User-judgment answers require a matching pending question from `co planner interview ask` or `co planner interview ask-next`.
- `ask-next` may return `ask_user`, `record_fact`, or `ready_for_score`; `ready_for_score` means the root agent should run `co planner interview score --mode auto`.
- Route sources must match `from-code...`, `from-user...`, or `from-research...`.
- Closure requires at least one round for every required track.
- Closure requires user-judgment rounds on `scope`, `outputs`, and `verification`.
- `code_fact` and `research_confirmation` increment `non_user_answer_streak`.
- `user_decision` and `code_plus_decision` reset `non_user_answer_streak`.
- Once `non_user_answer_streak` reaches 3, the next record must be `user_decision` or `code_plus_decision`.
- Once one track has two consecutive rounds, the next record must use another open track.
- `co planner interview score` must produce a fresh score for the current round count.
- `ambiguity = 1 - sum(clarity_i * weight_i)` must be `<= 0.2`.
- Clarity floors must pass: goal `0.75`, constraints `0.65`, success criteria `0.70`, brownfield context `0.60`.
- `co planner interview close` fails until every closure check has passed.
- `co planner interview close` fails while any required track is open or any material blocker remains.
- `co planner approve-draft` and `co planner finalize` fail until the interview is closed.
- Meaning-changing draft feedback must reopen the relevant track before any new record is added.

## Pre-Draft Review Gate

- Pre-draft review runs through `co planner review run --stage pre-draft`.
- `co planner review run --stage pre-draft` runs `contract_reviewer` and `verification_reviewer` in parallel.
- Any future command that invokes multiple Codex CLI agents must use the same parallel execution rule.
- `contract_reviewer` checks hidden decisions, scope drift, contradictions, task DAG assumptions, file scope, and acceptance criteria.
- `verification_reviewer` checks commands, evidence, final verification, and success signals.
- Both reviewers must return `PASS`.
- Failed review results are recorded in `notes.yaml` and `events.yaml`.
- Passing review stores `status.yaml.review.status: passed` and a fingerprint over `plan.yaml`, `tasks.yaml`, and `interview.yaml`.
- If those files change after review, `approve-draft` and `finalize` fail until review passes again.
- Wording-only changes to `draft.md` do not invalidate the review fingerprint.

## Direct Patch Gate

- `draft.md`, `plan.yaml`, and `tasks.yaml` may be patched directly after `co planner generate-skeleton`.
- `interview.yaml`, `status.yaml`, `events.yaml`, `notes.yaml`, and `evidence.yaml` remain CLI-owned.
- Direct changes to `plan.yaml` or `tasks.yaml` must be followed by `co planner validate` and pre-draft review.

## Execution Gate

The executor must:

- Start each loop with `co exec status`.
- Run `co exec start` only from `ready_for_exec`.
- Claim only a task returned by `co exec ready`.
- Keep exactly one task in `Doing`.
- Record verification artifacts through `co exec evidence add`.
- Complete a task only through `co exec complete-task`.
- Finish only through `co exec finish`.

## In-Contract Failure Gate

- Verification failures, missing evidence, stale file scope, and in-contract repair needs keep the task in `Doing`.
- Use `co exec halt` only for `user_decision` or `external_environment`.
- `halted` is not complete and `co exec finish` must fail while halted.

## Evidence Gate

A task with `verification.evidence_required: true` is done only when:

- each required `expected_evidence` entry has a matching successful `evidence.yaml` record
- the artifact path points under the bundle `evidence/` directory
- the recorded `task_id` and `step_id` match the task contract

## Repair Gate

`co exec repair` may modify only contract-compatible envelope fields:

- `files`
- `implementation_notes`
- `verification`

It must append one event in `events.yaml` and one repair note in `notes.yaml`.

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
          failure_policy: Keep T1 in Doing and continue repair unless halt is required.
    acceptance_criteria:
      - The test asserts HTTP 200 and body OK.
    expected_evidence:
      - step_id: focused-before
        file: evidence/t1-focused-before.txt
    reopen_when:
      - HTTP harness or endpoint contract changes.
```
