# Knowledge Index

## Repository Shape

coflow contains Codex skills that coordinate a plan-then-execute workflow through the bundled `co` CLI.

- `skills/coplan` defines the planner skill.
- `skills/coexec` defines the executor skill.
- `skills/coplan/scripts/co` owns plan bundle state, validation, review, execution state, and evidence records.

## Design Principles

- coflow serves Codex App and Codex CLI users that need a plan-and-execute workflow without a dedicated development SDK.
- `coplan` has three runtime roles: the root agent in the user surface, the `co` CLI, and Codex CLI agents launched by `co`.
- The `co` CLI is the flow manager. It must mechanically own state transitions, gate checks, interview routing, review execution, and executor status.
- The root agent is a thin adapter. It runs `co`, parses stdout YAML, asks the exact pending user question when instructed, records the answer through `co`, and avoids replacing `co` with its own flow logic.
- Codex CLI agents are subagents private to `co`; they provide read-only JSON judgments for interview action, ambiguity scoring, and pre-draft review.
- The plan and exec strategy is inspired by the local Ouroboros project, but coflow is a Codex App/CLI adaptation rather than a full port.

## Routes

- Runtime and architecture: `.agents/knowledge/runtime.md`.
- Verification and blind spots: `.agents/knowledge/verification.md`.
- Ouroboros reference overview: `.agents/knowledge/references/OUROBOROUS.md`.
- Ouroboros plan reference: `.agents/knowledge/references/OUROBOROS-PLAN.md`.
- Ouroboros exec reference: `.agents/knowledge/references/OUROBOROS-EXEC.md`.
- Ouroboros eval reference: `.agents/knowledge/references/OUROBOROS-EVAL.md`.
- Planner source contract: `skills/coplan/SKILL.md`.
- Executor source contract: `skills/coexec/SKILL.md`.
- Shared CLI guide: `skills/coplan/references/root-agent-co-guide.md`.
- Bundle schema: `skills/coplan/references/bundle-schema.md`.

## Product Docs

The Markdown and YAML files under `skills/` are installed skill content and product documentation.
Do not migrate them into `.agents/knowledge` unless the skill layout itself is being redesigned.

## UI Surface

N/A. This repository has no application UI or design-system surface.
