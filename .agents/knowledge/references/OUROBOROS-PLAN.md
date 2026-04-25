# Ouroboros Plan Reference

## What To Borrow

Ouroboros planning is a specification-first flow:

- start from vague user intent
- run Socratic interview
- measure ambiguity
- generate an immutable Seed only after the ambiguity gate passes

coflow's `coplan` is the Codex adaptation of this idea.
The equivalent durable output is a plan bundle under `.agents/plan/{plan-id}/` with `plan_seed.yaml` as the user-reviewed contract and `tasks.yaml` as the executor contract.

## Core Planning Sources

Ouroboros README and model-context references:

- `ouroboros/README.md:104`: result of one loop starts.
- `ouroboros/README.md:110`: interview exposes hidden assumptions.
- `ouroboros/README.md:111`: Seed is an immutable specification.
- `ouroboros/README.md:117`: interview, seed, run, evaluate summary.
- `ouroboros/README.md:138`: Socratic interview forces clarity before code.
- `ouroboros/README.md:139`: ambiguity gate blocks premature code.
- `ouroboros/README.md:159`: Interview phase.
- `ouroboros/README.md:160`: Seed phase.
- `ouroboros/README.md:311`: ambiguity is inverse weighted clarity.
- `ouroboros/README.md:317`: scoring uses low temperature for reproducibility.
- `ouroboros/README.md:321`: goal clarity weights.
- `ouroboros/README.md:322`: constraint clarity weights.
- `ouroboros/README.md:323`: success criteria weights.
- `ouroboros/README.md:324`: brownfield context clarity.
- `ouroboros/README.md:326`: threshold is ambiguity <= 0.2.
- `ouroboros/llms-full.txt:101`: Big Bang phase starts.
- `ouroboros/llms-full.txt:103`: planning components.
- `ouroboros/llms-full.txt:108`: plan process steps.
- `ouroboros/llms-full.txt:128`: ambiguity gate.

## Interview Skill Prompt

Ouroboros' `interview` skill is a useful reference for root-agent routing, but coflow intentionally moves more control into `co.py`.

Important source locations:

- `ouroboros/skills/interview/SKILL.md:82`: MCP mode is preferred.
- `ouroboros/skills/interview/SKILL.md:86`: MCP is question generator, main session is answerer/router.
- `ouroboros/skills/interview/SKILL.md:92`: role split starts.
- `ouroboros/skills/interview/SKILL.md:93`: MCP generates Socratic questions and scores ambiguity.
- `ouroboros/skills/interview/SKILL.md:94`: main session reads code or routes to user.
- `ouroboros/skills/interview/SKILL.md:95`: user answers only human decisions.
- `ouroboros/skills/interview/SKILL.md:110`: code-answer route.
- `ouroboros/skills/interview/SKILL.md:118`: auto-confirm factual path.
- `ouroboros/skills/interview/SKILL.md:140`: code confirmation path.
- `ouroboros/skills/interview/SKILL.md:160`: human judgment path.
- `ouroboros/skills/interview/SKILL.md:166`: code plus judgment path.
- `ouroboros/skills/interview/SKILL.md:174`: research interlude path.
- `ouroboros/skills/interview/SKILL.md:198`: when in doubt, ask user.
- `ouroboros/skills/interview/SKILL.md:212`: visible ambiguity ledger.
- `ouroboros/skills/interview/SKILL.md:218`: Seed-ready acceptance guard.
- `ouroboros/skills/interview/SKILL.md:240`: dialectic rhythm guard.

coflow mirrors part of this with `code_fact`, `user_decision`, `code_plus_decision`, and `research_confirmation` routes in `skills/coplan/scripts/co.py`.
When strengthening coplan, make those routes more mechanical inside `co.py` rather than relying on root-agent memory.

## Planning Code

Ouroboros interview and seed generation code:

- `ouroboros/src/ouroboros/bigbang/interview.py:1`: module purpose.
- `ouroboros/src/ouroboros/bigbang/interview.py:32`: interview round constants.
- `ouroboros/src/ouroboros/bigbang/interview.py:42`: internal interview perspectives.
- `ouroboros/src/ouroboros/bigbang/interview.py:62`: perspective prompts are lazy-loaded from agent markdown files.
- `ouroboros/src/ouroboros/bigbang/interview.py:90`: interview status enum.
- `ouroboros/src/ouroboros/bigbang/interview.py:98`: round model.
- `ouroboros/src/ouroboros/bigbang/interview.py:114`: persistent interview state model.
- `ouroboros/src/ouroboros/bigbang/interview.py:140`: ambiguity score stored on state.
- `ouroboros/src/ouroboros/bigbang/interview.py:149`: seed-ready threshold mirror.
- `ouroboros/src/ouroboros/bigbang/interview.py:197`: `InterviewEngine`.
- `ouroboros/src/ouroboros/bigbang/interview.py:201`: engine orchestrates question generation, response collection, persistence, and progress.
- `ouroboros/src/ouroboros/bigbang/interview.py:254`: `start_interview`.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:1`: ambiguity scoring module.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:29`: ambiguity threshold constant.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:34`: per-dimension clarity floors.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:40`: greenfield weights.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:45`: brownfield weights.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:51`: reproducible scoring temperature.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:183`: `AmbiguityScore`.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:196`: ready-for-seed property.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:206`: completion floor failures.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:234`: seed completion qualifier.
- `ouroboros/src/ouroboros/bigbang/ambiguity.py:246`: `AmbiguityScorer`.
- `ouroboros/src/ouroboros/bigbang/seed_generator.py:1`: Seed generation module.
- `ouroboros/src/ouroboros/bigbang/seed_generator.py:7`: SeedGenerator steps.
- `ouroboros/src/ouroboros/bigbang/seed_generator.py:45`: `SeedGenerator`.
- `ouroboros/src/ouroboros/bigbang/seed_generator.py:81`: `generate`.
- `ouroboros/src/ouroboros/bigbang/seed_generator.py:90`: Gen 1 and Gen 2+ modes.
- `ouroboros/src/ouroboros/bigbang/seed_generator.py:114`: ambiguity gate before seed.
- `ouroboros/src/ouroboros/bigbang/seed_generator.py:135`: requirement extraction.
- `ouroboros/src/ouroboros/bigbang/seed_generator.py:150`: seed build.

## Coflow Mapping

Use this mapping when comparing designs:

- Ouroboros `InterviewEngine` maps to coflow internal interview handling behind `co.py flow next/respond`.
- Ouroboros ambiguity threshold maps to coflow `AMBIGUITY_THRESHOLD`.
- Ouroboros clarity floors map to coflow `AMBIGUITY_FLOORS`.
- Ouroboros Seed maps conceptually to coflow `plan_seed.yaml`, which then authors finalized `tasks.yaml`.
- Ouroboros Seed immutability maps to coflow's post-finalize executor contract.
- Ouroboros root skill routing maps to coflow root-agent stdout loop, but coflow should make the CLI own more decisions.

Do not assume coflow needs the full Ouroboros MCP question-generator shape.
For coflow, the high-value invariant is mechanical control through `co.py` stdout and bundle validation.
