# Verification

## Repo-Native Commands

This repository has no project-level `package.json`, `pyproject.toml`, `Makefile`, `justfile`, or CI workflow.

Use the smallest command that matches the changed surface:

- CLI syntax: `python3 -m py_compile skills/coplan/scripts/co`.
- CLI environment: `skills/coplan/scripts/co doctor`.
- CLI command shape: `skills/coplan/scripts/co --help` and `skills/coplan/scripts/co flow --help`.
- Flow log smoke: `co flow init`, `co flow next`, and `co flow respond --stdin` should append core events to `.agents/plan/{plan-id}/flow_log.ndjson`.
- Knowledge routing: verify that every `.agents/knowledge/*.md` route named by `AGENTS.md` exists.
- Repo path references: verify important repo-root-relative paths named in `AGENTS.md` and `.agents/knowledge/*.md` exist.
- User-facing graph docs: verify that `COPLAN.md` and `COEXEC.md` exist, each contains both `sequenceDiagram` and `flowchart`, and each keeps role labels and styling where Mermaid supports it.
- Agent workflow references: verify that `skills/coplan/references/workflow.md` and `skills/coexec/references/workflow.md` exist, contain no Mermaid diagrams, and describe root actions, CLI-owned state, gates, and non-negotiable boundaries in structured text.

## Coverage Notes

- `co doctor` checks Python and PyYAML availability; it does not validate planner or executor behavior.
- `py_compile` catches Python syntax errors only.
- Help commands verify argparse registration only.
- Planner review, interview scoring, bundle authoring, feedback classification, and ask-next paths require the `codex` CLI and can launch subprocess subagents.
- Flow log smoke checks should confirm event presence and order, not exact timestamps or sequence numbers beyond monotonic append behavior.
- Full planner and executor behavior is not covered by a committed automated test suite.

## Knowledge Checks

For knowledge-only changes, verify:

- Root `AGENTS.md` routes to `.agents/knowledge/index.md`.
- `.agents/knowledge/index.md` routes to `.agents/knowledge/runtime.md` and `.agents/knowledge/verification.md`.
- Knowledge docs use repo-root-relative paths, not workspace-absolute paths.
- Product docs under `skills/` remain treated as shipped content, not as an alternate knowledge home.
- Agent-facing workflow references stay synchronized with `.agents/knowledge/runtime.md` and the shipped skill behavior without Mermaid diagrams.
- `COPLAN.md` and `COEXEC.md` remain user-facing graph docs, not agent-facing knowledge routes.
- `.agents/knowledge/runtime.md` describes `flow_log.ndjson` structure and how to analyze root/CLI/subagent responsibility boundaries.
