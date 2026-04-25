# Example Plan Bundle

Use this only for density calibration. Create real bundles with `co.py flow init`.

## Directory

```text
.agents/plan/
  exec.yaml
  add-health-endpoint/
    plan_seed.yaml
    tasks.yaml
    interview.yaml
    status.yaml
    notes.yaml
    evidence.yaml
    flow_log.ndjson
    evidence/
```

## `exec.yaml`

```yaml
active_plan_id: add-health-endpoint
plan_dir: .agents/plan/add-health-endpoint
```

## `plan_seed.yaml`

```yaml
status: ready
generated_at: "2026-04-25T00:00:00Z"
round_count: 5
ambiguity_score_id: S2
closure_audit:
  status: passed
  summary: All execution-changing decisions are closed.
  material_blockers: []
  question: ""
  round_count: 5
  score_id: S2
seed:
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
  verification_expectations:
    - Run focused route verification and final broader HTTP verification.
  execution_boundaries:
    - The executor changes route handling and tests only.
  source_round_ids:
    - Q1
    - Q2
    - Q3
    - Q4
    - Q5
  deferred_items: []
  summary: The bundle should add a public OK health endpoint and prove it with focused and final verification.
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
initial_context: Add a lightweight unauthenticated readiness endpoint.
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
    summary: Produce an executable task bundle.
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
    question: Is the health endpoint meant to be public infrastructure readiness, or part of an authenticated API surface?
    answer: Keep it public and lightweight.
    source: from-user
  - id: Q2
    route: code_plus_decision
    track: verification
    question: Given the existing HTTP test surface, should final verification include the broader HTTP integration suite after the focused route test?
    answer: Run focused verification first and include broad final verification.
    source: from-user
  - id: Q3
    route: user_decision
    track: non_goals
    question: Should this include auth redesign, deployment config, or monitoring changes?
    answer: No, exclude auth redesign, deployment changes, and broader monitoring work.
    source: from-user
  - id: Q4
    route: code_plus_decision
    track: constraints
    question: Given the existing route style, should the response body stay exactly OK?
    answer: Yes, keep the response body exactly OK.
    source: from-user
  - id: Q5
    route: user_decision
    track: stop_conditions
    question: When should execution halt instead of repairing locally?
    answer: Halt only for a user decision or external environment issue.
    source: from-user
pending_user_question: null
deferred_items: []
agent_runs: []
ambiguity_ledger:
  - score_id: S1
    ambiguity: 0.19
    ready: true
    round_count: 4
  - score_id: S2
    ambiguity: 0.16
    ready: true
    round_count: 5
completion_candidate_streak: 2
ambiguity:
  latest:
    id: S2
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
      options:
        - label: Broader HTTP suite
          description: Run the existing broader HTTP integration coverage after the focused route test.
          recommended: true
        - label: Focused route only
          description: Limit final verification to the new health endpoint contract.
          recommended: false
    summary: Requirements are clear enough for bundle generation.
    round_count: 5
    scoring_temperature_intent: 0.1
    model: gpt-5.5
    reasoning_effort: medium
  history: []
closure_audit:
  status: passed
  summary: All execution-changing decisions are closed.
  material_blockers: []
  question: ""
  round_count: 5
  score_id: S2
seed_review:
  status: approved
  fingerprint: <sha256>
  comment: Plan seed approved.
  feedback: []
closure:
  ready: true
  summary: All execution-changing decisions are closed.
  material_blockers: []
  checks:
    desired_output_explicit:
      passed: true
      summary: The desired output is explicit.
    user_tradeoffs_explicit:
      passed: true
      summary: Scope, non-goals, and response constraints came from user judgment.
    closure_audit_passed:
      passed: true
      summary: Broader verification scope was clarified.
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
current_task: null
tasks:
  T1: Todo
  FV1: Todo
halt: null
bundle_inspection:
  author:
    files_read:
      - AGENTS.md
    commands_considered:
      - cargo test health_route_returns_ok -- --exact
    grounding_summary: Existing tests and repo instructions ground the task boundaries.
```

## `notes.yaml`

```yaml
entries:
  - id: N1
    kind: decision
    text: Plan seed approved.
    why: User approved the presented plan seed.
    affects:
      - plan_seed.yaml
      - status.yaml#phase
    source: co.py flow respond
```

## `evidence.yaml`

```yaml
records: []
```
