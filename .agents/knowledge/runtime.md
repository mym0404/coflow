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
- Interview routing, scoring thresholds, reviewer prompts, and reviewer schemas are CLI internals in `skills/coplan/scripts/co`, not root-agent reference material.
- Root-facing `co flow` stdout should not expose internal scores, route or track metadata, reviewer findings, progress snapshots, or command allowlists unless that data is required to perform the current `root_action`.

The plan and exec strategy is modeled after the local Ouroboros project, especially its specification-first interview, ambiguity gate, execution orchestration, and evaluation gate ideas.
Use `.agents/knowledge/references/OUROBOROUS.md` and the linked `OUROBOROS-PLAN`, `OUROBOROS-EXEC`, and `OUROBOROS-EVAL` reference docs when comparing design intent.
Those references are advisory source material; coflow is a Codex App/CLI-specific adaptation and should not inherit every Ouroboros behavior by default.

## Plan-Exec Synchronization

Keep planning and execution concepts synchronized whenever changing either side of the workflow.

- When changing the executable plan bundle, planner gates, task schema, or `exec.yaml` handoff, verify that `coexec` can still execute the approved plan without making new planning decisions.
- When changing executor behavior, status output, repair rules, evidence handling, halt rules, or finish gates, verify that `coplan` still produces a bundle with enough static contract for that executor.
- The planner side owns the approved user contract; the executor side owns sequential local execution, progress state, evidence, repair, halt, and finish.
- If a behavior change blurs that boundary, update `skills/coplan/SKILL.md`, `skills/coexec/SKILL.md`, and `skills/coplan/scripts/co` together. Update `.agents/knowledge/references/COFLOW-BUNDLE-SCHEMA.md` or `.agents/knowledge/references/COFLOW-GATES-AND-EXAMPLES.md` only when CLI-owned schema or gate details change.

## Workflow Docs

Keep user-facing graphs and root-agent skill prompts synchronized with runtime behavior.

- `COPLAN.md` and `COEXEC.md` are user-facing docs and the only Mermaid graph home.
- User-facing graph docs must contain both Mermaid graph types: `sequenceDiagram` for actor and time order, and `flowchart` for branches, loops, and parallel or repeated work.
- User-facing Mermaid flowcharts use consistent role labels and styling: green for `[유저]`, blue for `[추론기계]`, gray for `[기계]`, and yellow for `[추론형식]`.
- `skills/coplan/SKILL.md` contains the root-agent planner workflow prompt.
- `skills/coexec/SKILL.md` contains the root-agent executor workflow prompt.
- `skills/*/references/` is not used.
- Project maintenance references must live under `.agents/knowledge/`, not under `skills/*/references/`.
- Skill prompts should use concise tables, root action contracts, and execution loops instead of Mermaid diagrams.
- When changing planner or executor state transitions, root actions, interview loops, review loops, draft feedback handling, evidence handling, repair, halt, or finish behavior, update the relevant user-facing graph doc and the relevant `SKILL.md` in the same change.
- Planner parallel reviewer execution must stay visible in `COPLAN.md` and `skills/coplan/SKILL.md`; executor single-current-task execution must stay visible in `COEXEC.md` and `skills/coexec/SKILL.md`.

## Flow Log

Each active plan records an append-only runtime trace at `.agents/plan/{plan-id}/flow_log.ndjson`.
The log is always on for `co flow` and is for development feedback, not user-facing contract state.
`notes.yaml` remains the durable contract and decision note surface; `flow_log.ndjson` records runtime behavior for later analysis.

The log uses JSON Lines.
Every event includes `seq`, `ts`, `event`, `plan_id`, and `phase` when an active plan exists.
Common optional fields include `command`, `ok`, `phase_before`, `phase_after`, `root_action`, `task_id`, `track`, `route`, `role`, `status`, `duration_ms`, `input_hash`, `stdin_bytes`, and `output_summary`.
Raw user answers, raw prompts, and full draft bodies are not stored; the CLI records hashes, byte lengths, and bounded summaries.

High-value event families:

- `flow.command.*` shows public `co flow` command boundaries and errors.
- `root_action.emit` shows exactly where control returns to the root agent.
- `interview.*` shows pending question creation, answer recording, ambiguity scoring, and interview closure.
- `codex_agent.*` shows private Codex CLI subagent execution behind the CLI.
- `bundle.authored`, `review.result`, and `review.join` show bundle generation and parallel review behavior.
- `draft_feedback.classified` shows draft feedback routing.
- `state.transition`, `task.claimed`, `task.completed`, `evidence.recorded`, `repair.applied`, `halt.recorded`, and `execution.completed` show executor orchestration.

Use the flow log to check responsibility boundaries:

- Root stays thin when each `root_action.emit` is followed by an allowed `flow.command.*` boundary instead of direct bundle edits.
- Interview behaves like an iterator when one `flow respond` is followed by CLI-owned scoring, closure, question creation, authoring, or draft presentation events.
- Codex CLI agents remain internal details when `codex_agent.*` appears between CLI events rather than as root-facing commands.
- Executor task selection stays in the CLI when `task.claimed` and `task.completed` are emitted by flow events.
- Verification failure reaches the right boundary when failed `evidence.recorded` is followed by `root_action.emit` with `repair_task`.

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

- `skills/coplan/SKILL.md` describes the root-agent planner workflow and `co flow` stdout contract.
- `skills/coexec/SKILL.md` describes the root-agent executor workflow and `co flow` stdout contract.
- `.agents/knowledge/references/COFLOW-BUNDLE-SCHEMA.md` describes CLI-owned bundle files and required fields for maintenance.
- `.agents/knowledge/references/COFLOW-GATES-AND-EXAMPLES.md` describes CLI-owned planner and executor gates for maintenance.
- `.agents/knowledge/references/COFLOW-EXAMPLE-BUNDLE.md` is only a density and shape example.
- Internal interview and pre-draft review algorithms live in `skills/coplan/scripts/co`; repo knowledge records the ownership rule, not a separate root-facing reference file.
