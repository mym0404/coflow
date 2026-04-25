# Codex CLI Pre-Draft Review

Use this reference for the pre-draft review that `co flow` runs after bundle authoring.

Review is mandatory and runs through `codex exec`. Multiple Codex CLI reviewers must run in parallel.

## Flow

`co flow next/respond` runs both required reviewers in parallel:

- `contract_reviewer`
- `verification_reviewer`

Both must return `PASS`. Results are stored in `notes.yaml` and `status.yaml.review`.

If review fails, `co flow` sends findings back through `bundle_author`, rewrites the bundle, reruns deterministic validation, and reruns pre-draft review before presenting the draft.

## Reviewer Responsibilities

### `contract_reviewer`

Checks:

- hidden user-visible decisions
- scope drift
- contradictions between draft, plan, and tasks
- task DAG assumptions
- file scope
- acceptance criteria

It should fail when the executor would need to choose between materially different user-visible behaviors.

### `verification_reviewer`

Checks:

- commands
- evidence paths and meaning
- final verification task
- success signals
- whether verification proves the user's intended behavior

It should fail when verification is a ritual rather than a meaningful executable scenario.

## Output Shape

Each reviewer returns JSON:

```json
{
  "status": "PASS",
  "summary": "The plan is decision-complete for this lens.",
  "issues": [],
  "optional_tightenings": []
}
```

Failure example:

```json
{
  "status": "FAIL",
  "summary": "Final verification does not prove the public behavior.",
  "issues": [
    "tasks.yaml FV1 success_signal only says the command exits 0; it does not name the behavior being proven."
  ],
  "optional_tightenings": []
}
```

## Deterministic Validation Ownership

Reviewers do not own these mechanical checks:

- required YAML files and fields
- task dependency acyclicity
- `status.yaml` task-id consistency
- evidence path formatting
- missing final verification task
- task status embedded in `tasks.yaml`

`co flow` deterministic validation owns those. Reviewers may still fail if the structures exist but are meaningless, misleading, flaky, or contradicted by repo reality.
