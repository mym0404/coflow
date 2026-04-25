# Verification

## Repo-Native Commands

This repository has no project-level `package.json`, `pyproject.toml`, `Makefile`, `justfile`, or CI workflow.

Use the smallest command that matches the changed surface:

- CLI syntax: `python3 -m py_compile skills/coplan/scripts/co`.
- CLI environment: `skills/coplan/scripts/co doctor`.
- CLI command shape: `skills/coplan/scripts/co --help`, `skills/coplan/scripts/co planner --help`, and `skills/coplan/scripts/co exec --help`.
- Knowledge routing: verify that every `.agents/knowledge/*.md` route named by `AGENTS.md` exists.
- Repo path references: verify important repo-root-relative paths named in `AGENTS.md` and `.agents/knowledge/*.md` exist.

## Coverage Notes

- `co doctor` checks Python and PyYAML availability; it does not validate planner or executor behavior.
- `py_compile` catches Python syntax errors only.
- Help commands verify argparse registration only.
- Planner review, interview scoring, and ask-next paths require the `codex` CLI and can launch subprocess subagents.
- Full planner and executor behavior is not covered by a committed automated test suite.

## Knowledge Checks

For knowledge-only changes, verify:

- Root `AGENTS.md` routes to `.agents/knowledge/index.md`.
- `.agents/knowledge/index.md` routes to `.agents/knowledge/runtime.md` and `.agents/knowledge/verification.md`.
- Knowledge docs use repo-root-relative paths, not workspace-absolute paths.
- Product docs under `skills/` remain treated as shipped content, not as an alternate knowledge home.
