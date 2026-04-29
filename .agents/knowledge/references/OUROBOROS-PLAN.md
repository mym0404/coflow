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

- `README.md:104`: result of one loop starts.
- `README.md:110`: interview exposes hidden assumptions.
- `README.md:111`: Seed is an immutable specification.
- `README.md:117`: interview, seed, run, evaluate summary.
- `README.md:138`: Socratic interview forces clarity before code.
- `README.md:139`: ambiguity gate blocks premature code.
- `README.md:159`: Interview phase.
- `README.md:160`: Seed phase.
- `README.md:311`: ambiguity is inverse weighted clarity.
- `README.md:317`: scoring uses low temperature for reproducibility.
- `README.md:321`: goal clarity weights.
- `README.md:322`: constraint clarity weights.
- `README.md:323`: success criteria weights.
- `README.md:324`: brownfield context clarity.
- `README.md:326`: threshold is ambiguity <= 0.2.
- `llms-full.txt:101`: Big Bang phase starts.
- `llms-full.txt:103`: planning components.
- `llms-full.txt:108`: plan process steps.
- `llms-full.txt:128`: ambiguity gate.

## Interview Skill Prompt

Ouroboros' `interview` skill is a useful reference for root-agent routing, but coflow intentionally moves more control into `co.py`.

Important source locations:

- `skills/interview/SKILL.md:82`: MCP mode is preferred.
- `skills/interview/SKILL.md:86`: MCP is question generator, main session is answerer/router.
- `skills/interview/SKILL.md:92`: role split starts.
- `skills/interview/SKILL.md:93`: MCP generates Socratic questions and scores ambiguity.
- `skills/interview/SKILL.md:94`: main session reads code or routes to user.
- `skills/interview/SKILL.md:95`: user answers only human decisions.
- `skills/interview/SKILL.md:110`: code-answer route.
- `skills/interview/SKILL.md:118`: auto-confirm factual path.
- `skills/interview/SKILL.md:140`: code confirmation path.
- `skills/interview/SKILL.md:160`: human judgment path.
- `skills/interview/SKILL.md:166`: code plus judgment path.
- `skills/interview/SKILL.md:174`: research interlude path.
- `skills/interview/SKILL.md:198`: when in doubt, ask user.
- `skills/interview/SKILL.md:212`: visible ambiguity ledger.
- `skills/interview/SKILL.md:218`: Seed-ready acceptance guard.
- `skills/interview/SKILL.md:240`: dialectic rhythm guard.

coflow mirrors part of this with `code_fact`, `user_decision`, `code_plus_decision`, and `research_confirmation` routes in `skills/coplan/scripts/co.py`.
When strengthening coplan, make those routes more mechanical inside `co.py` rather than relying on root-agent memory.

## Planning Code

Ouroboros interview and seed generation code:

- `src/ouroboros/bigbang/interview.py:1`: module purpose.
- `src/ouroboros/bigbang/interview.py:32`: interview round constants.
- `src/ouroboros/bigbang/interview.py:42`: internal interview perspectives.
- `src/ouroboros/bigbang/interview.py:62`: perspective prompts are lazy-loaded from agent markdown files.
- `src/ouroboros/bigbang/interview.py:90`: interview status enum.
- `src/ouroboros/bigbang/interview.py:98`: round model.
- `src/ouroboros/bigbang/interview.py:114`: persistent interview state model.
- `src/ouroboros/bigbang/interview.py:140`: ambiguity score stored on state.
- `src/ouroboros/bigbang/interview.py:149`: seed-ready threshold mirror.
- `src/ouroboros/bigbang/interview.py:197`: `InterviewEngine`.
- `src/ouroboros/bigbang/interview.py:201`: engine orchestrates question generation, response collection, persistence, and progress.
- `src/ouroboros/bigbang/interview.py:254`: `start_interview`.
- `src/ouroboros/bigbang/ambiguity.py:1`: ambiguity scoring module.
- `src/ouroboros/bigbang/ambiguity.py:29`: ambiguity threshold constant.
- `src/ouroboros/bigbang/ambiguity.py:34`: per-dimension clarity floors.
- `src/ouroboros/bigbang/ambiguity.py:40`: greenfield weights.
- `src/ouroboros/bigbang/ambiguity.py:45`: brownfield weights.
- `src/ouroboros/bigbang/ambiguity.py:51`: reproducible scoring temperature.
- `src/ouroboros/bigbang/ambiguity.py:183`: `AmbiguityScore`.
- `src/ouroboros/bigbang/ambiguity.py:196`: ready-for-seed property.
- `src/ouroboros/bigbang/ambiguity.py:206`: completion floor failures.
- `src/ouroboros/bigbang/ambiguity.py:234`: seed completion qualifier.
- `src/ouroboros/bigbang/ambiguity.py:246`: `AmbiguityScorer`.
- `src/ouroboros/bigbang/seed_generator.py:1`: Seed generation module.
- `src/ouroboros/bigbang/seed_generator.py:7`: SeedGenerator steps.
- `src/ouroboros/bigbang/seed_generator.py:45`: `SeedGenerator`.
- `src/ouroboros/bigbang/seed_generator.py:81`: `generate`.
- `src/ouroboros/bigbang/seed_generator.py:90`: Gen 1 and Gen 2+ modes.
- `src/ouroboros/bigbang/seed_generator.py:114`: ambiguity gate before seed.
- `src/ouroboros/bigbang/seed_generator.py:135`: requirement extraction.
- `src/ouroboros/bigbang/seed_generator.py:150`: seed build.

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
