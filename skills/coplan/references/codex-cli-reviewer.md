# Codex CLI Pre-Draft Review

Use this reference after `co planner generate-skeleton`, direct bundle patching, and `co planner validate`.

Review is mandatory and runs through `codex exec`. Multiple Codex CLI reviewers must run in parallel.

## Command

```bash
co planner review run --runner codex --stage pre-draft
```

The command runs both required reviewers in parallel:

- `contract_reviewer`
- `verification_reviewer`

Both must return `PASS`. Results are stored in `notes.yaml`, `events.yaml`, and `status.yaml.review`.

## Rerun Discipline

- Fix only valid findings.
- Patch only the smallest necessary parts of `draft.md`, `plan.yaml`, or `tasks.yaml`.
- Rerun review after any semantic change to `plan.yaml`, `tasks.yaml`, or `interview.yaml`.
- Wording-only `draft.md` edits do not invalidate the review fingerprint.
- If `approve-draft` or `finalize` says review is stale, rerun pre-draft review.

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
- whether the verification proves the user's intended behavior

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

`co planner validate` owns those. Reviewers may still fail if the structures exist but are meaningless, misleading, flaky, or contradicted by repo reality.
