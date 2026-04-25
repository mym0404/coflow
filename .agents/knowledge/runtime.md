# Runtime

## Operating Model

coflow provides two complementary Codex skills:

- `coplan` creates a decision-complete plan bundle under `.agents/plan/{plan-id}`.
- `coexec` executes the active bundle selected by `.agents/plan/exec.yaml`.

The runtime has three roles:

- Root agent: the Codex App or Codex CLI agent in the user-facing session.
- `co` CLI: the flow manager and mechanical owner of state transitions.
- Codex CLI agents: subprocess subagents launched by `co` for bounded JSON judgments.

The root agent should interact with bundles through `skills/coplan/scripts/co flow`.
The CLI prints YAML, and `root_action` is the next-step contract.
The root agent should not compute gate readiness, interview next steps, ambiguity, review status, task readiness, task completion, or execution finish state itself.

## Flow Ownership

`co` exists because Codex App and Codex CLI users do not have a development SDK that lets this repository enforce agent behavior directly in code.
The reliable control point is therefore the `co flow` contract:

- `co` owns bundle files, validation, state transitions, notes, evidence records, review freshness, halt gates, and finish gates.
- Root-agent-facing skill instructions should keep the agent as a thin `root_action` adapter.
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

- initialize with `skills/coplan/scripts/co flow init --plan-id <id> --title "<title>"`.
- continue with `skills/coplan/scripts/co flow next`.
- ask exact `root_action.question` values and pipe answers to `co flow respond --stdin`.
- present exact `root_action.draft` values and pipe approval or feedback to `co flow respond --stdin`.
- switch to `coexec` when `root_action.type` becomes `execute_task`, `repair_task`, `report_halt`, or `report_complete`.

The root agent does not directly edit bundle files.
CLI-owned files include `draft.md`, `plan.yaml`, `tasks.yaml`, `planning_context.yaml`, `interview.yaml`, `status.yaml`, `notes.yaml`, and `evidence.yaml`.

## Executor Path

Use `skills/coexec/SKILL.md` as the executor entrypoint.

Core flow:

- start each loop with `skills/coplan/scripts/co flow next`.
- implement only `root_action.task` when `root_action.type: execute_task`.
- record verification output with `co flow evidence`.
- repair only task envelope fields with `co flow repair`.
- halt only through `co flow halt`.
- report completion only after `root_action.type: report_complete`.

Executor work must not redesign the approved plan contract.
If a needed change would alter user-visible behavior, acceptance criteria, task order, dependencies, or non-goals, halt through `co flow halt`.

## Reference Tier

- `skills/coplan/references/root-agent-co-guide.md` describes the shared `co flow` stdout contract.
- `skills/coplan/references/bundle-schema.md` describes bundle files and required fields.
- `skills/coplan/references/gates-and-examples.md` describes planner and executor gates.
- `skills/coplan/references/interview-algorithm.md` describes ambiguity scoring and interview routing internals.
- `skills/coplan/references/codex-cli-reviewer.md` describes pre-draft review behavior.
- `skills/coplan/references/example-bundle.md` is only a density and shape example.
