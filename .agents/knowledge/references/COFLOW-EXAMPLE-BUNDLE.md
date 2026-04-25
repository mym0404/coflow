# Example Plan Bundle

Use this only for density calibration. Create real bundles with `co flow init`.

## Directory

```text
.agents/plan/
  exec.yaml
  add-health-endpoint/
    draft.md
    plan.yaml
    tasks.yaml
    interview.yaml
    status.yaml
    notes.yaml
    evidence.yaml
    evidence/
```

## `exec.yaml`

```yaml
active_plan_id: add-health-endpoint
plan_dir: .agents/plan/add-health-endpoint
```

## `draft.md`

```md
# Add health endpoint

## Goal
Add a lightweight unauthenticated readiness endpoint.

## Scope

| Included | Excluded |
|---|---|
| Add `GET /health`. | Auth redesign and deployment changes. |
| Add focused and final verification. | Broader monitoring work. |

## Known Facts

| Fact | Source |
|---|---|
| `src/http/mod.rs` owns route registration. | from-code: local exploration |

## Verification Direction

| Check | Expected Signal |
|---|---|
| Focused route test | HTTP 200 with body `OK`. |
| Final verification | Focused and broad checks pass. |
```

## `plan.yaml`

```yaml
title: Add health endpoint
goal: Ship a deployment-readiness endpoint with focused and final verification.
context:
  - src/http/mod.rs owns route registration.
non_goals:
  - Auth redesign.
  - Deployment changes.
constraints:
  - Keep the response body exactly OK.
success_criteria:
  - GET /health returns HTTP 200 with body OK.
verification_policy:
  - Prefer focused verification before broad verification.
execution_strategy:
  - Execute the focused test, implementation, and final verification sequentially.
stop_conditions:
  - user_decision
  - external_environment
```

## `tasks.yaml`

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

  - id: FV1
    kind: final_verification
    title: Run final verification
    depends_on: [T1]
    start_when:
      description: All execution tasks are Done.
    files:
      primary:
        - tests/http_health.rs
      generated_incidental: []
    context: Final verification proves the route still fits the bundle contract.
    must_do:
      - Run focused and broad verification.
    must_not_do:
      - Do not add new implementation scope.
    implementation_notes:
      - Reopen the relevant task if final verification fails.
    verification:
      evidence_required: true
      steps:
        - id: focused-final
          command: cargo test health_route_returns_ok -- --exact
          success_signal: Exit code 0 and the named test reports ok.
    acceptance_criteria:
      - Focused verification passes.
    expected_evidence:
      - step_id: focused-final
        file: evidence/fv1-focused-final.txt
    reopen_when:
      - Any final verification command fails.
```

## `interview.yaml`

```yaml
status: closed
non_user_answer_streak: 0
required_tracks:
  scope:
    status: closed
    summary: Add only a lightweight health endpoint and focused verification.
  non_goals:
    status: closed
    summary: Do not redesign auth or deployment.
  outputs:
    status: closed
    summary: Produce the executable plan bundle; implementation happens later.
  verification:
    status: closed
    summary: Focused and final verification evidence must be recorded.
  constraints:
    status: closed
    summary: Keep the response body exactly OK.
  stop_conditions:
    status: closed
    summary: Halt only for user decision or external environment.
rounds:
  - id: Q1
    route: user_decision
    track: scope
    question: Should the health endpoint include auth or stay public?
    answer: Keep it public and lightweight.
    source: from-user
  - id: Q2
    route: user_decision
    track: verification
    question: Is a focused route test enough, or should final verification also run the broader suite?
    answer: Run focused verification first and include broad final verification.
    source: from-user
  - id: Q3
    route: user_decision
    track: outputs
    question: Should the output be only the executable bundle, or include implementation changes too?
    answer: Produce only the executable plan bundle.
    source: from-user
  - id: Q4
    route: user_decision
    track: non_goals
    question: Should auth or deployment configuration be part of this plan?
    answer: No, exclude auth redesign and deployment changes.
    source: from-user
  - id: Q5
    route: code_plus_decision
    track: constraints
    question: Given the existing route style, should the response body stay exactly OK?
    answer: Yes, keep the response body exactly OK.
    source: from-user
  - id: Q6
    route: user_decision
    track: stop_conditions
    question: When should execution halt instead of repairing locally?
    answer: Halt only for a user decision or external environment issue.
    source: from-user
  - id: Q7
    route: code_plus_decision
    track: verification
    question: Which broader suite should final verification run?
    answer: Run the broader HTTP integration suite after the focused health check.
    source: from-user
    purpose: hidden_assumption_followup
pending_user_question: null
agent_runs: []
ambiguity:
  latest:
    id: S1
    project_mode: brownfield
    threshold: 0.2
    weighted_clarity: 0.84
    ambiguity: 0.16
    ready: true
    floor_failures: []
    components:
      goal_clarity:
        clarity_score: 0.9
        weight: 0.35
        justification: Goal and endpoint behavior are explicit.
      constraint_clarity:
        clarity_score: 0.85
        weight: 0.25
        justification: Auth and deployment exclusions are explicit.
      success_criteria_clarity:
        clarity_score: 0.82
        weight: 0.25
        justification: HTTP status and body are measurable.
      context_clarity:
        clarity_score: 0.7
        weight: 0.15
        justification: Route ownership and test surface are known.
    weakest_dimension: context_clarity
    recommended_followup:
      route: code_plus_decision
      track: verification
      question: Which broader suite should final verification run?
    summary: Requirements are clear enough for bundle generation.
    round_count: 7
    scoring_temperature_intent: 0.1
    model: gpt-5.5
    reasoning_effort: medium
  history: []
closure:
  ready: true
  summary: All execution-changing decisions are closed.
  material_blockers: []
  checks:
    desired_output_explicit:
      passed: true
      summary: The bundle output and no implementation output are explicit.
    user_tradeoffs_explicit:
      passed: true
      summary: Scope, non-goals, and response constraints came from user judgment.
    hidden_assumptions_reviewed:
      passed: true
      summary: Broader verification scope was clarified before drafting.
    executor_determinism:
      passed: true
      summary: The executor has one route contract and concrete file surface.
    verification_proves_behavior:
      passed: true
      summary: Verification proves the public OK health response.
    no_material_questions:
      passed: true
      summary: Remaining questions would only polish wording.
```

## `status.yaml`

```yaml
phase: ready_for_exec
review:
  status: passed
  stage: pre-draft
  required_reviewers:
    - contract_reviewer
    - verification_reviewer
  passed_reviewers:
    - contract_reviewer
    - verification_reviewer
  last_run_id: R1
  fingerprint: <sha256>
current_task: null
tasks:
  T1: Todo
  FV1: Todo
halt: null
```

## `notes.yaml`

```yaml
entries:
  - id: N1
    kind: decision
    text: contract_reviewer PASS: scope and acceptance criteria are aligned.
    why: Codex CLI pre-draft plan review.
    affects:
      - plan.yaml
      - tasks.yaml
    source: co flow next
```

## `evidence.yaml`

```yaml
records: []
```
