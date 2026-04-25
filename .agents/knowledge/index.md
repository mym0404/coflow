# Knowledge Index

## Repository Shape

coflow contains Codex skills that coordinate a plan-then-execute workflow through the bundled `co` CLI.

- `skills/coplan` defines the planner skill.
- `skills/coexec` defines the executor skill.
- `skills/coplan/scripts/co flow` owns plan bundle state, validation, review, execution state, and evidence records.

## Design Principles

- coflow serves Codex App and Codex CLI users that need a plan-and-execute workflow without a dedicated development SDK.
- `coplan` has three runtime roles: the root agent in the user surface, the `co` CLI, and Codex CLI agents launched by `co`.
- The `co` CLI is the flow manager. It must mechanically own state transitions, gate checks, interview routing, review execution, executor status, and `root_action` selection.
- The root agent is a thin adapter. It runs `co flow`, parses stdout YAML, performs the exact `root_action`, and avoids replacing `co` with its own flow logic.
- Codex CLI agents are subagents private to `co`; they provide schema-bound JSON judgments for interview action, ambiguity scoring, bundle authoring, draft feedback classification, and pre-draft review.
- The plan and exec strategy is inspired by the local Ouroboros project, but coflow is a Codex App/CLI adaptation rather than a full port.
- Repository changes do not need migration paths or backward compatibility unless the user explicitly asks for them.

## Routes

- Runtime, architecture, workflow docs, and flow log analysis: `.agents/knowledge/runtime.md`.
- Verification and blind spots: `.agents/knowledge/verification.md`.
- Ouroboros reference overview: `.agents/knowledge/references/OUROBOROUS.md`.
- Ouroboros plan reference: `.agents/knowledge/references/OUROBOROS-PLAN.md`.
- Ouroboros exec reference: `.agents/knowledge/references/OUROBOROS-EXEC.md`.
- Ouroboros eval reference: `.agents/knowledge/references/OUROBOROS-EVAL.md`.
- Planner source contract: `skills/coplan/SKILL.md`.
- Executor source contract: `skills/coexec/SKILL.md`.
- Planner workflow reference: `skills/coplan/references/workflow.md`.
- Executor workflow reference: `skills/coexec/references/workflow.md`.
- Shared CLI guide: `skills/coplan/references/root-agent-co-guide.md`.
- Bundle schema: `skills/coplan/references/bundle-schema.md`.

## Product Docs

The Markdown and YAML files under `skills/` are installed skill content and product documentation.
Do not migrate them into `.agents/knowledge` unless the skill layout itself is being redesigned.
`COPLAN.md` and `COEXEC.md` are user-facing docs; do not use them as agent-facing workflow references.

## UI Surface

N/A. This repository has no application UI or design-system surface.
