# Interview Algorithm

This is a maintenance reference for `co flow` internals. It is not root-agent workflow guidance.

## Routing

Route each material question through exactly one path:

| Route | Use For | Source |
|---|---|---|
| `code_fact` | Exact repository facts that do not choose future behavior. | `from-code...` |
| `user_decision` | Goals, scope, non-goals, desired behavior, success criteria, preferences, and tradeoffs. | `from-user...` |
| `code_plus_decision` | Repo facts where applying the pattern needs human judgment. | `from-user...` |
| `research_confirmation` | External facts from docs or web research. | `from-research...` |

When any part of a question requires judgment, route the whole round as `user_decision` or `code_plus_decision`.

## Internal Loop

`co flow next/respond` owns this loop:

1. Return an existing pending user question as `root_action.type: ask_user`.
2. Ask deterministic missing-track questions before scoring when required coverage is absent.
3. Run the interview action agent only when deterministic coverage does not choose the next step.
4. Record safe `code_fact` or `research_confirmation` rounds internally.
5. Record user answers only from pending question metadata owned by `co flow`.
6. Run ambiguity scoring when the round count changes.
7. If ambiguity is not ready, create the recommended follow-up as a pending user question.
8. If ambiguity and coverage are ready, close tracks, pass closure checks, and close the interview.
9. Continue to bundle authoring without returning control to root.

## Ambiguity Math

The interview closes when weighted ambiguity says the bundle can become executable.

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
- `pending_user_question` is `null` before close.
- `source` matches the route prefix.
- After 3 consecutive `code_fact` or `research_confirmation` rounds, the next round must require user judgment.
- After 2 consecutive rounds on one track, the next round must zoom out to another open track.
- Latest ambiguity score is fresh for the current round count.
- Every closure check passes.
- `closure.material_blockers` is empty.

## Draft Feedback Re-Entry

`co flow respond --stdin` classifies draft feedback:

- `approve`: approve and finalize internally.
- `wording_change`: revise authored bundle text, rerun validation and review, then return `present_draft`.
- `meaning_change`: reopen the affected track, record the supplied user answer, rescore, reclose, regenerate/review the bundle, then return the next root boundary.
