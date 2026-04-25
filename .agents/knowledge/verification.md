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
- Skill runtime prompt placement: verify that `skills/*/references/` does not exist or contains no files; root-agent runtime instructions must live directly in `skills/*/SKILL.md`.
- Skill stdout contract: verify that `co flow` stdout YAML and `root_action` handling rules live directly in `skills/coplan/SKILL.md` and `skills/coexec/SKILL.md`, not in a separate shared reference file.
- Maintenance knowledge placement: verify that bundle schema, gate examples, and example bundles live under `.agents/knowledge/references/`, not under `skills/*/references/`.
- Skill prompt hard gate: verify that `skills/*/SKILL.md` says the agent is the root agent, contains the essential execution workflow directly, and uses references only as supplemental runtime guides.
- Skill content hard gate: verify that `skills/*/SKILL.md` does not contain maintenance-history wording, old-vs-new explanations, or internal-algorithm responsibility disclaimers that the root agent does not need to perform the skill.
- Internal algorithm placement: verify that interview and pre-draft review algorithms are not routed as skill references; implementation details should stay in `skills/coplan/scripts/co` with only ownership guidance in repo knowledge.

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
- `skills/*/SKILL.md` stays synchronized with `.agents/knowledge/runtime.md` and the shipped skill behavior without Mermaid diagrams.
- `skills/*/references/` stays empty.
- `skills/*/SKILL.md` remains self-contained enough to run the skill without treating references as the main instruction body.
- `COPLAN.md` and `COEXEC.md` remain user-facing graph docs, not agent-facing knowledge routes.
- `.agents/knowledge/runtime.md` describes `flow_log.ndjson` structure and how to analyze root/CLI/subagent responsibility boundaries.
- Root-facing `co flow` stdout docs stay focused on `contract_version`, `mode`, `phase`, and `root_action`, without internal scores, route or track metadata, progress snapshots, or allowlist fields.
