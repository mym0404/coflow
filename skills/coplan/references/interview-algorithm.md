# Interview Algorithm

Use this algorithm during `coplan` planning. It mirrors the Ouroboros ambiguity philosophy with a lightweight `codex exec` backend.

## Routing

Route each material question through exactly one path:

| Route | Use For | Source |
|---|---|---|
| `code_fact` | Exact repository facts that do not choose future behavior. | `from-code...` |
| `user_decision` | Goals, scope, non-goals, desired behavior, success criteria, preferences, and tradeoffs. | `from-user...` |
| `code_plus_decision` | Repo facts where applying the pattern needs human judgment. | `from-user...` |
| `research_confirmation` | External facts from docs or web research. | `from-research...` |

When any part of a question requires judgment, route the whole round as `user_decision` or `code_plus_decision`.

## Loop

1. Explore local repo facts before the first interview question.
2. Run `co planner interview status`.
3. Run `co planner interview ask-next --runner codex`.
4. If the result creates a pending question, ask the user that exact question.
5. Record the matching answer with `co planner interview record`.
6. If the result is `ready_for_score`, run `co planner interview score --runner codex --mode auto`.
7. After any material round, run `co planner interview score --runner codex --mode auto`.
8. Close only tracks that are execution-clear.
9. Pass closure challenge items with `co planner interview closure-check`.
10. If ambiguity is not ready, ask the follow-up that targets the weakest dimension.
11. Repeat until ambiguity, tracks, floors, closure checks, and root acceptance all pass.

## Ambiguity Math

The interview does not close when the planner feels ready. It closes when weighted ambiguity says the bundle can become executable.

```text
weighted_clarity = sum(clarity_i * weight_i)
ambiguity = 1 - weighted_clarity
```

Greenfield weights:

- goal clarity: `0.40`
- constraint clarity: `0.30`
- success criteria clarity: `0.30`

Brownfield weights:

- goal clarity: `0.35`
- constraint clarity: `0.25`
- success criteria clarity: `0.25`
- context clarity: `0.15`

Readiness threshold:

- `ambiguity <= 0.2`

Required floors:

- goal clarity `>= 0.75`
- constraint clarity `>= 0.65`
- success criteria clarity `>= 0.70`
- brownfield context clarity `>= 0.60`

## Hard Guards

- Every required track has at least one round.
- `scope`, `outputs`, and `verification` each have user-judgment rounds.
- `pending_user_question` is `null`.
- `source` matches the route prefix.
- After 3 consecutive `code_fact` or `research_confirmation` rounds, the next round must require user judgment.
- After 2 consecutive rounds on one track, the next round must zoom out to another open track.
- Latest ambiguity score is fresh for the current round count.
- Every closure check passes.
- `closure.material_blockers` is empty.

## Root Acceptance Guard

When `codex exec` scoring says ready, the root agent still checks from the user's point of view:

- Is the desired output explicit?
- Are user-owned tradeoffs stated by the user, not inferred from code?
- Would two executors make the same implementation choices?
- Would verification prove user-visible behavior, not only repo mechanics?
- Is any remaining question more than wording polish?

If any answer is weak, use `co planner interview blocker add --reason "..."` or ask one focused follow-up.

## Draft Feedback Re-Entry

If the user gives meaning-changing feedback after `draft.md` is shown, the interview is already closed. Do not call `co planner interview record` first.

1. Run `co planner interview track open <track> --reason "draft feedback"`.
2. Run `co planner interview ask --route user_decision|code_plus_decision --track <track> --question "<question>"`.
3. If the user already supplied the answer in the feedback, immediately record that answer with the exact same question.
4. Rerun `co planner interview score --runner codex --mode auto`.
5. Close the affected track and then close the interview again.
6. Patch only the impacted `draft.md`, `plan.yaml`, and `tasks.yaml` sections.
7. Rerun `co planner validate` and `co planner review run --runner codex --stage pre-draft`.
