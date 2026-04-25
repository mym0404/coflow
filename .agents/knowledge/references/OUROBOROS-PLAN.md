# Ouroboros Plan Reference

## What To Borrow

Ouroboros planning is a specification-first flow:

- start from vague user intent
- run Socratic interview
- measure ambiguity
- generate an immutable Seed only after the ambiguity gate passes

coflow's `coplan` is the Codex adaptation of this idea.
The equivalent durable output is not an Ouroboros Seed; it is a plan bundle under `.agents/plan/{plan-id}/` with `draft.md`, `plan.yaml`, and `tasks.yaml`.

## Core Planning Sources

Ouroboros README and model-context references:

- `/Users/mj/projects/ouroboros/README.md:104`: result of one loop starts.
- `/Users/mj/projects/ouroboros/README.md:110`: interview exposes hidden assumptions.
- `/Users/mj/projects/ouroboros/README.md:111`: Seed is an immutable specification.
- `/Users/mj/projects/ouroboros/README.md:117`: interview, seed, run, evaluate summary.
- `/Users/mj/projects/ouroboros/README.md:138`: Socratic interview forces clarity before code.
- `/Users/mj/projects/ouroboros/README.md:139`: ambiguity gate blocks premature code.
- `/Users/mj/projects/ouroboros/README.md:159`: Interview phase.
- `/Users/mj/projects/ouroboros/README.md:160`: Seed phase.
- `/Users/mj/projects/ouroboros/README.md:311`: ambiguity is inverse weighted clarity.
- `/Users/mj/projects/ouroboros/README.md:317`: scoring uses low temperature for reproducibility.
- `/Users/mj/projects/ouroboros/README.md:321`: goal clarity weights.
- `/Users/mj/projects/ouroboros/README.md:322`: constraint clarity weights.
- `/Users/mj/projects/ouroboros/README.md:323`: success criteria weights.
- `/Users/mj/projects/ouroboros/README.md:324`: brownfield context clarity.
- `/Users/mj/projects/ouroboros/README.md:326`: threshold is ambiguity <= 0.2.
- `/Users/mj/projects/ouroboros/llms-full.txt:101`: Big Bang phase starts.
- `/Users/mj/projects/ouroboros/llms-full.txt:103`: planning components.
- `/Users/mj/projects/ouroboros/llms-full.txt:108`: plan process steps.
- `/Users/mj/projects/ouroboros/llms-full.txt:128`: ambiguity gate.

## Interview Skill Prompt

Ouroboros' `interview` skill is a useful reference for root-agent routing, but coflow intentionally moves more control into `co.py`.

Important source locations:

- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:82`: MCP mode is preferred.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:86`: MCP is question generator, main session is answerer/router.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:92`: role split starts.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:93`: MCP generates Socratic questions and scores ambiguity.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:94`: main session reads code or routes to user.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:95`: user answers only human decisions.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:110`: code-answer route.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:118`: auto-confirm factual path.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:140`: code confirmation path.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:160`: human judgment path.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:166`: code plus judgment path.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:174`: research interlude path.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:198`: when in doubt, ask user.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:212`: visible ambiguity ledger.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:218`: Seed-ready acceptance guard.
- `/Users/mj/projects/ouroboros/skills/interview/SKILL.md:240`: dialectic rhythm guard.

coflow mirrors part of this with `code_fact`, `user_decision`, `code_plus_decision`, and `research_confirmation` routes in `skills/coplan/scripts/co.py`.
When strengthening coplan, make those routes more mechanical inside `co.py` rather than relying on root-agent memory.

## Planning Code

Ouroboros interview and seed generation code:

- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:1`: module purpose.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:32`: interview round constants.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:42`: internal interview perspectives.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:62`: perspective prompts are lazy-loaded from agent markdown files.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:90`: interview status enum.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:98`: round model.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:114`: persistent interview state model.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:140`: ambiguity score stored on state.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:149`: seed-ready threshold mirror.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:197`: `InterviewEngine`.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:201`: engine orchestrates question generation, response collection, persistence, and progress.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/interview.py:254`: `start_interview`.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:1`: ambiguity scoring module.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:29`: ambiguity threshold constant.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:34`: per-dimension clarity floors.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:40`: greenfield weights.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:45`: brownfield weights.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:51`: reproducible scoring temperature.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:183`: `AmbiguityScore`.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:196`: ready-for-seed property.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:206`: completion floor failures.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:234`: seed completion qualifier.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/ambiguity.py:246`: `AmbiguityScorer`.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/seed_generator.py:1`: Seed generation module.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/seed_generator.py:7`: SeedGenerator steps.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/seed_generator.py:45`: `SeedGenerator`.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/seed_generator.py:81`: `generate`.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/seed_generator.py:90`: Gen 1 and Gen 2+ modes.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/seed_generator.py:114`: ambiguity gate before seed.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/seed_generator.py:135`: requirement extraction.
- `/Users/mj/projects/ouroboros/src/ouroboros/bigbang/seed_generator.py:150`: seed build.

## Coflow Mapping

Use this mapping when comparing designs:

- Ouroboros `InterviewEngine` maps to coflow internal interview handling behind `co.py flow next/respond`.
- Ouroboros ambiguity threshold maps to coflow `AMBIGUITY_THRESHOLD`.
- Ouroboros clarity floors map to coflow `AMBIGUITY_FLOORS`.
- Ouroboros Seed maps conceptually to coflow `plan_seed.yaml`, which then authors finalized `draft.md`, `plan.yaml`, and `tasks.yaml`.
- Ouroboros Seed immutability maps to coflow's post-finalize executor contract.
- Ouroboros root skill routing maps to coflow root-agent stdout loop, but coflow should make the CLI own more decisions.

Do not assume coflow needs the full Ouroboros MCP question-generator shape.
For coflow, the high-value invariant is mechanical control through `co.py` stdout and bundle validation.
