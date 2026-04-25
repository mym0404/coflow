# Runtime

## Operating Model

coflow provides two complementary Codex skills:

- `coplan` creates a decision-complete plan bundle under `.agents/plan/{plan-id}`.
- `coexec` executes the active bundle selected by `.agents/plan/exec.yaml`.

The runtime has three planner-side roles:

- Root agent: the Codex App or Codex CLI agent in the user-facing session.
- `co` CLI: the flow manager and mechanical owner of state transitions.
- Codex CLI agents: subprocess subagents launched by `co` for bounded JSON judgments.

The root agent should interact with bundles through `skills/coplan/scripts/co`.
The CLI prints YAML for normal command responses, and `required_action` is the next-step contract.
The root agent should not compute gate readiness, interview next steps, ambiguity, or execution status itself.

## Flow Ownership

`co` exists because Codex App and Codex CLI users do not have a development SDK that lets this repository enforce agent behavior directly in code.
The reliable control point is therefore the CLI contract:

- `co` owns bundle files, validation, state transitions, event records, evidence records, review freshness, and halt or finish gates.
- Root-agent-facing skill instructions should keep the agent as a thin stdout-driven adapter.
- If `co` can decide or validate a step mechanically, prefer adding the rule to `skills/coplan/scripts/co` over relying on prose instructions in the root agent skill.
- Codex CLI subagents are implementation details of `co`; their JSON output is normalized by `co` before it reaches the root agent.

The plan and exec strategy is modeled after the local Ouroboros project, especially its specification-first interview, ambiguity gate, execution orchestration, and evaluation gate ideas.
Use `.agents/knowledge/references/OUROBOROUS.md` and the linked `OUROBOROS-PLAN`, `OUROBOROS-EXEC`, and `OUROBOROS-EVAL` reference docs when comparing design intent.
Those references are advisory source material; coflow is a Codex App/CLI-specific adaptation and should not inherit every Ouroboros behavior by default.

## Plan-Exec Synchronization

Keep planning and execution concepts synchronized whenever changing either side of the workflow.

- When changing the executable plan bundle, planner gates, task schema, or `exec.yaml` handoff, verify that `coexec` can still execute the approved plan without making new planning decisions.
- When changing executor behavior, status output, repair rules, evidence handling, halt rules, or finish gates, verify that `coplan` still produces a bundle with enough static contract for that executor.
- The planner side owns the approved user contract; the executor side owns sequential local execution, progress state, evidence, repair, halt, and finish.
- If a behavior change blurs that boundary, update `skills/coplan/SKILL.md`, `skills/coexec/SKILL.md`, `skills/coplan/references/root-agent-co-guide.md`, `skills/coplan/references/bundle-schema.md`, `skills/coplan/references/gates-and-examples.md`, `skills/coexec/README.md`, and `skills/coplan/scripts/co` together.

## Planner Path

Use `skills/coplan/SKILL.md` as the planner entrypoint.

Core flow:

- initialize with `skills/coplan/scripts/co planner init --plan-id <id> --title "<title>"`.
- explore the target repository before asking the user.
- use `co planner interview ask-next` and record user answers through `co`.
- run `co planner validate` before pre-draft review.
- run `co planner review run --stage pre-draft` before showing the draft.
- finalize with `co planner finalize` only after the draft is approved.

Direct bundle edits are limited to `draft.md`, `plan.yaml`, and `tasks.yaml` after skeleton generation.
CLI-owned files such as `interview.yaml`, `status.yaml`, `events.yaml`, `notes.yaml`, and `evidence.yaml` are not edited directly.

Planner flow is valid only when the root agent follows `co` stdout instead of recreating the full flow from memory.
When changing planner behavior, keep `skills/coplan/references/root-agent-co-guide.md`, `skills/coplan/SKILL.md`, `skills/coplan/README.md`, and `skills/coplan/scripts/co` aligned around that contract.

## Executor Path

Use `skills/coexec/SKILL.md` as the executor entrypoint.

Core flow:

- start each loop with `skills/coplan/scripts/co exec status`.
- start execution from `ready_for_exec` with `co exec start`.
- claim exactly one ready task with `co exec claim <task-id>`.
- record verification output with `co exec evidence add`.
- complete tasks with `co exec complete-task`.
- finish only with `co exec finish` after every task, including final verification, is done.

Executor work must not redesign the approved plan contract.
If a needed change would alter user-visible behavior, acceptance criteria, task order, dependencies, or non-goals, halt through `co exec halt`.

Executor flow is status-driven.
The root agent starts each loop with `co exec status`, then follows `required_action`, `allowed_now`, and `forbidden_now`.

## Reference Tier

- `skills/coplan/references/root-agent-co-guide.md` describes the shared stdout contract.
- `skills/coplan/references/bundle-schema.md` describes bundle files and required fields.
- `skills/coplan/references/gates-and-examples.md` describes planner and executor gates.
- `skills/coplan/references/interview-algorithm.md` describes ambiguity scoring and interview routing.
- `skills/coplan/references/codex-cli-reviewer.md` describes pre-draft review behavior.
- `skills/coplan/references/example-bundle.md` is only a density and shape example.
