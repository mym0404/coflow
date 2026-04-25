# coflow

Codex skills for planning and executing work through a shared `co` CLI.

## Skills

- `coplan`: turns an ambiguous request into a plan bundle.
- `coexec`: executes the approved bundle.

## Layout

```text
skills/
  coplan/
    SKILL.md
    scripts/co
    references/
  coexec/
    SKILL.md
```

## CLI

Run the bundled CLI from this repo:

```bash
skills/coplan/scripts/co --help
skills/coplan/scripts/co planner --help
skills/coplan/scripts/co exec --help
```

When installed as Codex skills, the same CLI lives at:

```bash
~/.codex/skills/coplan/scripts/co
```

