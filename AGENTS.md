# AGENTS.md

## Project Overview

coflow is a repository of Codex skills for planning and executing work through the shared `co.py` CLI.
It currently ships two skills:

- `skills/coplan`: planner-only skill that turns ambiguous work into a gated plan bundle.
- `skills/coexec`: executor-only skill that runs the active plan bundle sequentially.

## Tech Stack

- Python CLI: `skills/coplan/scripts/co.py`.
- Codex skill manifests and instructions: `skills/*/SKILL.md`.
- YAML metadata: `skills/*/agents/openai.yaml`.
- User-facing Markdown docs: `COPLAN.md` and `COEXEC.md`.
- Root-agent skill runtime prompts: `skills/coplan/SKILL.md` and `skills/coexec/SKILL.md`.
- Project maintenance knowledge references: `.agents/knowledge/references/COFLOW-*.md`.

## Runtime Start

- Start with `.agents/knowledge/runtime.md` for the repo-level runtime map.
- Use `skills/coplan/SKILL.md` when planning a new bundle.
- Use `skills/coexec/SKILL.md` when executing an approved bundle.
- Treat `skills/coplan/scripts/co.py flow` stdout YAML and `root_action` as the runtime contract.
- When changing either the plan bundle/planner side or the executor side, keep the plan-exec concept synchronized so `coplan` still produces an executable static contract and `coexec` still executes it without making new planning decisions.
- Migration paths and backward compatibility are not required for repository changes unless the user explicitly asks for them.

## Verification

- Start with `.agents/knowledge/verification.md`.
- There is no project-level test runner or CI config in this repository.
- For CLI changes, use `python3 -m py_compile skills/coplan/scripts/co.py` and targeted `skills/coplan/scripts/co.py ...` command checks.
- For knowledge changes, verify root routing and repo-root-relative path references.
- For semantic plan-exec quality checks, use `.agents/knowledge/semantic-verification.md` after mechanical verification.

## UI Surface

- N/A. This repository ships Codex skills and a CLI, not an application UI.

## Knowledge Router

- Evergreen repo knowledge starts at `.agents/knowledge/index.md`.
- Runtime and architecture: `.agents/knowledge/runtime.md`.
- Verification and blind spots: `.agents/knowledge/verification.md`.
- Semantic verification checklist: `.agents/knowledge/semantic-verification.md`.
- Ouroboros inspiration references: `.agents/knowledge/references/OUROBOROUS.md`.
- Skill source docs remain under `skills/` because those files are root-agent runtime skill content, not a secondary knowledge home.
- `skills/*/references/` is not used; all root-agent runtime instructions belong directly in `skills/*/SKILL.md`.
- Bundle schema, gate details, example bundles, and other project maintenance documents belong under `.agents/knowledge/`.
- `COPLAN.md` and `COEXEC.md` are user-facing docs, not agent-facing knowledge routes.
