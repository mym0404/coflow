# AGENTS.md

## Project Overview

coflow is a repository of Codex skills for planning and executing work through the shared `co` CLI.
It currently ships two skills:

- `skills/coplan`: planner-only skill that turns ambiguous work into a gated plan bundle.
- `skills/coexec`: executor-only skill that runs the active plan bundle sequentially.

## Tech Stack

- Python CLI: `skills/coplan/scripts/co`.
- Codex skill manifests and instructions: `skills/*/SKILL.md`.
- YAML metadata: `skills/*/agents/openai.yaml`.
- Markdown runtime and reference docs: `skills/*/README.md` and `skills/coplan/references/*.md`.

## Runtime Start

- Start with `.agents/knowledge/runtime.md` for the repo-level runtime map.
- Use `skills/coplan/SKILL.md` when planning a new bundle.
- Use `skills/coexec/SKILL.md` when executing an approved bundle.
- Treat `skills/coplan/scripts/co flow` stdout YAML and `root_action` as the runtime contract.
- When changing either the plan bundle/planner side or the executor side, keep the plan-exec concept synchronized so `coplan` still produces an executable static contract and `coexec` still executes it without making new planning decisions.
- Migration paths and backward compatibility are not required for repository changes unless the user explicitly asks for them.

## Verification

- Start with `.agents/knowledge/verification.md`.
- There is no project-level test runner or CI config in this repository.
- For CLI changes, use `python3 -m py_compile skills/coplan/scripts/co` and targeted `skills/coplan/scripts/co ...` command checks.
- For knowledge changes, verify root routing and repo-root-relative path references.

## UI Surface

- N/A. This repository ships Codex skills and a CLI, not an application UI.

## Knowledge Router

- Evergreen repo knowledge starts at `.agents/knowledge/index.md`.
- Runtime and architecture: `.agents/knowledge/runtime.md`.
- Verification and blind spots: `.agents/knowledge/verification.md`.
- Ouroboros inspiration references: `.agents/knowledge/references/OUROBOROUS.md`.
- Skill source docs remain under `skills/` because those files are the shipped product content, not a secondary knowledge home.
