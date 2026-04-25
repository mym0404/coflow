# Semantic Verification

Semantic verification is a model-judged checklist for deciding whether coflow's shipped skill outputs preserve the intended Ouroboros-inspired plan-exec philosophy.
Use it after mechanical verification when changes touch `skills/coplan/SKILL.md`, `skills/coexec/SKILL.md`, `skills/coplan/scripts/co.py`, `skills/coplan/scripts/co/agents/*.py`, `.agents/knowledge/references/*.md`, `COPLAN.md`, or `COEXEC.md`.

## Scope

Evaluate the current repository artifacts, not the intent of a proposed design.

Required inputs:

- `skills/coplan/SKILL.md`
- `skills/coexec/SKILL.md`
- `skills/coplan/scripts/co.py`
- `skills/coplan/scripts/co/agents/*.py`
- `.agents/knowledge/index.md`
- `.agents/knowledge/runtime.md`
- `.agents/knowledge/verification.md`
- `.agents/knowledge/references/OUROBOROUS.md`
- `.agents/knowledge/references/OUROBOROS-PLAN.md`
- `.agents/knowledge/references/OUROBOROS-EXEC.md`
- `.agents/knowledge/references/OUROBOROS-EVAL.md`
- `.agents/knowledge/references/COFLOW-BUNDLE-SCHEMA.md`
- `.agents/knowledge/references/COFLOW-GATES-AND-EXAMPLES.md`

Optional inputs when documentation changed:

- `COPLAN.md`
- `COEXEC.md`
- `skills/*/agents/openai.yaml`

## Method

The evaluator must read the relevant artifacts first, then score each criterion from evidence.
Do not give credit for claims that exist only in maintenance knowledge when the shipped root-agent prompts or CLI behavior contradict them.

Score each criterion on a 0-3 scale:

| Score | Meaning |
|---|---|
| 3 | Strongly reflected in shipped prompt or CLI behavior, with concrete gates or context that guide the agent without improvisation. |
| 2 | Mostly reflected, but one non-blocking detail is implicit, weakly enforced, or documented outside the most active runtime path. |
| 1 | Partially reflected, but an important context, gate, or ownership detail is missing from the shipped prompt or CLI path. |
| 0 | Missing, contradicted, or left to agent improvisation. |

Overall result:

- `PASS`: total score is at least 21 and every criterion scores at least 2.
- `REVIEW`: total score is 17-20, or any criterion scores 1 while the risk is isolated.
- `FAIL`: total score is 16 or lower, or any criterion scores 0 in a way that can cause wrong planning, execution, or verification.

Report format:

Start with the verdict and total score, then use a compact Markdown table.

```text
Semantic verification: PASS|REVIEW|FAIL
Total: <score>/24

| Criterion | Score | Judgment |
|---|---:|---|
| C1 Ouroboros full flow | <0-3> | <evidence and gap> |
| C2 Ouroboros interview | <0-3> | <evidence and gap> |
| C3 Plan seed review | <0-3> | <evidence and gap> |
| C4 Role philosophy | <0-3> | <evidence and gap> |
| C5 Thin root agents | <0-3> | <evidence and gap> |
| C6 Task purpose context | <0-3> | <evidence and gap> |
| C7 Project state context | <0-3> | <evidence and gap> |
| C8 Subagent prompt context | <0-3> | <evidence and gap> |
```

Keep each criterion note grounded in representative file paths and line numbers.

## Checklist

### C1 Ouroboros Full Flow

Question: Does coflow preserve the full Ouroboros flow closely enough for this repository's Codex App/CLI adaptation?

Full credit requires:

- The workflow follows a staged path from interview to seed, execution, verification, and completion or halt.
- Planning produces a user-reviewed contract before execution starts.
- Execution runs from the approved static contract instead of re-planning the user's intent.
- Verification evidence is recorded and checked before task or plan completion.
- Feedback, failed review, failed evidence, and halt states route back through explicit gates instead of silent continuation.

High-risk failures:

- Execution can begin before the user-reviewed seed or equivalent plan contract is approved.
- The executor can redesign the plan instead of executing the approved contract.
- Verification is treated as a report-only afterthought rather than a gate.

### C2 Ouroboros Interview

Question: Does `coplan` preserve the Ouroboros interview process closely enough for coflow's adaptation?

Full credit requires:

- Socratic interview asks about implementation-changing ambiguity instead of process mechanics.
- Ambiguity is scored against goal, constraints, success criteria, and brownfield context.
- Low ambiguity alone is not enough; closure requires a separate audit.
- Seed or plan contract is generated only after interview readiness and closure gates.
- Intentional deferrals are allowed only when they do not force executor planning.

High-risk failures:

- A fixed checklist replaces adaptive interview routing.
- User decisions are skipped when material behavior, ownership, migration, or verification policy is unresolved.
- The seed or task bundle can be authored from vague input without ambiguity and closure gates.

### C3 Plan Seed Review

Question: Does `coplan` preserve the Ouroboros plan seed review philosophy and algorithm?

Full credit requires:

- The plan seed is treated as the user-reviewed source of truth before execution.
- The root agent presents the plan seed without summarizing, rewriting, or deciding approval.
- User approval is recorded explicitly before `ready_for_exec`.
- User feedback is classified before mutation, with wording-only changes revised directly and semantic changes routed back through interview.
- Bundle freshness is tied to the current plan seed, tasks, and semantic interview contract.

High-risk failures:

- Root agent approval or summarization replaces user seed review.
- Feedback can silently mutate the approved contract without reopening the right planning gate.
- Tasks remain executable after plan seed or interview contract drift without a fresh bundle fingerprint.

### C4 Role Philosophy

Question: Is the root agent / CLI / subagent split preserved?

Full credit requires:

- Root agents only perform the current `root_action`.
- `co.py` owns state transitions, gates, validation, task selection, evidence, halt, and completion.
- Subagents are private to `co.py` and return schema-bound judgments.
- Root-facing stdout exposes only the information needed for the current boundary.
- Maintenance knowledge explains the split without asking the root agent to enforce hidden algorithms.

High-risk failures:

- Root prompts ask the root agent to compute readiness, choose the next task, edit bundle YAML, or interpret subagent results.
- Subagent prompts or outputs become a user-facing contract.
- CLI validation is replaced by prose instructions.

### C5 Thin Root Agents

Question: Do `coplan` and `coexec` root agents communicate with `co.py` using minimal information?

Full credit requires:

- `skills/coplan/SKILL.md` and `skills/coexec/SKILL.md` contain the stdout contract and per-action handling, not internal algorithms.
- Root agents forward user answers, approvals, feedback, evidence, halt reasons, and command output without semantic rewriting.
- Root agents do not directly read or edit bundle files for normal workflow decisions.
- Root prompts avoid exposing scoring formulas, route metadata, or progress snapshots unless the action requires them.

High-risk failures:

- Root prompts make the agent summarize or reinterpret user answers before sending them to the CLI.
- Root prompts include enough internal workflow logic that the agent can bypass `co.py`.
- Root agents are told to continue mechanically instead of returning to `co.py flow`.

### C6 Task Purpose Context

Question: Are root agents given enough context about why the current work exists?

Full credit requires:

- Planner context retains the original user request and settled interview answers.
- `plan_seed.yaml` captures goal, constraints, non-goals, success criteria, verification expectations, execution boundaries, and deferred items.
- Executor root actions include the approved `plan_seed` so the agent can detect scope drift.
- Tasks project the global contract into task-level `context`, `must_do`, `must_not_do`, acceptance criteria, and verification.

High-risk failures:

- Executor tasks contain only local file edits with no link back to the user's intended outcome.
- Plan seed context is not carried into task authoring or execution.
- Scope, non-goals, or success criteria are only present in human-facing docs, not the runtime bundle.

### C7 Project State Context

Question: Are root agents given enough context about the current project situation to act agentically within their boundary?

Full credit requires:

- Planner and authoring prompts include repo root, active bundle path, current interview state, existing notes, status, and any current plan seed.
- Brownfield context clarity is explicitly scored and can block readiness.
- `tasks.yaml` carries file scope, generated incidental files, implementation notes, reopen conditions, and verification commands.
- `coexec` root actions include current task state, evidence state, latest failed evidence, and relevant notes.

High-risk failures:

- Brownfield work can pass without repository-specific context.
- Executor repair receives only a failure flag, not enough failed evidence to diagnose within task scope.
- Task file scope or verification commands are left for the executor to invent.

### C8 Subagent Prompt Context

Question: Do CLI-launched subagent prompts receive enough task and project context?

Full credit requires:

- Interview, scoring, closure, seed, bundle author, and feedback subagents receive the same coherent planning context pack.
- Prompts state each subagent's role, output schema expectation, and decision boundary.
- Bundle author receives `plan_seed`, `tasks`, interview contract, status, notes, and repo path context as relevant.
- Subagents are instructed not to edit files directly unless their role explicitly owns writing through normalized CLI output.

High-risk failures:

- Subagents receive isolated snippets that omit original request, transcript, plan seed, or current task contract.
- Reviewers judge tasks without the approved plan seed.
- Subagent outputs can change durable state without CLI normalization and validation.
