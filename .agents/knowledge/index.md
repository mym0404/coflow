# Knowledge Index

## Repository Shape

coflow contains Codex skills that coordinate a plan-then-execute workflow through the bundled `co.py` CLI.

- `skills/coplan` defines the planner skill.
- `skills/coexec` defines the executor skill.
- `skills/coplan/scripts/co.py flow` owns plan bundle state, validation, execution state, and evidence records.
- `skills/coplan/scripts/co/agents/*.py` contains schema-bound Codex subagent prompts, schemas, and output summaries used by `co.py`.

## Design Principles

- coflow serves Codex App and Codex CLI users that need a plan-and-execute workflow without a dedicated development SDK.
- `coplan` has three runtime roles: the root agent in the user surface, the `co.py` CLI, and Codex CLI agents launched by `co.py`.
- The `co.py` CLI is the flow manager. It must mechanically own state transitions, gate checks, interview routing, closure audit, seed extraction, bundle authoring, executor status, and `root_action` selection.
- The root agent is a thin adapter. It runs `co.py flow`, parses stdout YAML, performs the exact `root_action`, and avoids replacing `co.py` with its own flow logic.
- Codex CLI agents are subagents private to `co.py`; their prompt/schema modules live under `skills/coplan/scripts/co/agents/` and provide schema-bound JSON judgments for interview action, ambiguity scoring, closure audit, seed extraction, bundle authoring, and plan seed feedback classification.
- The plan and exec strategy is inspired by the local Ouroboros project, but coflow is a Codex App/CLI adaptation rather than a full port.
- Repository changes do not need migration paths or backward compatibility unless the user explicitly asks for them.

## Routes

- Runtime, architecture, skill-prompt boundaries, and flow log analysis: `.agents/knowledge/runtime.md`.
- Verification and blind spots: `.agents/knowledge/verification.md`.
- Plan bundle debugging for user-provided repository paths: `.agents/knowledge/DEBUG.md`.
- Semantic model-judged verification checklist: `.agents/knowledge/semantic-verification.md`.
- Ouroboros reference overview: `.agents/knowledge/references/OUROBOROUS.md`.
- Ouroboros plan reference: `.agents/knowledge/references/OUROBOROS-PLAN.md`.
- Ouroboros exec reference: `.agents/knowledge/references/OUROBOROS-EXEC.md`.
- Ouroboros eval reference: `.agents/knowledge/references/OUROBOROS-EVAL.md`.
- Planner source contract: `skills/coplan/SKILL.md`.
- Executor source contract: `skills/coexec/SKILL.md`.
- Bundle schema maintenance reference: `.agents/knowledge/references/COFLOW-BUNDLE-SCHEMA.md`.
- Gate and example maintenance reference: `.agents/knowledge/references/COFLOW-GATES-AND-EXAMPLES.md`.
- Example bundle maintenance reference: `.agents/knowledge/references/COFLOW-EXAMPLE-BUNDLE.md`.

## Product Docs

The Markdown and YAML files under `skills/` are installed skill content and product documentation.
`skills/*/SKILL.md` files are shipped root-agent prompts and remain under `skills/`.
`skills/*/references/` is not used; root-agent runtime instructions live directly in `skills/*/SKILL.md`.
Project maintenance docs belong under `.agents/knowledge/`.
`COPLAN.md` and `COEXEC.md` are user-facing docs; do not use them as agent-facing workflow references.

## UI Surface

N/A. This repository has no application UI or design-system surface.
