# Ouroboros Eval Reference

## What To Borrow

Ouroboros evaluation is a progressive gate:

- Stage 1: deterministic mechanical verification
- Stage 2: semantic model review against acceptance criteria and goal
- Stage 3: consensus only when uncertainty or drift requires it

coflow currently has planner pre-draft review and executor evidence gates.
When adding stronger evaluation behavior to coflow, prefer mechanical checks and recorded evidence first, then schema-bound model judgment, then user-visible halt or review gates.

## Evaluation Sources

README and guide:

- `/Users/mj/projects/ouroboros/README.md:112`: evaluation is a 3-stage gate.
- `/Users/mj/projects/ouroboros/README.md:121`: Mechanical -> Semantic -> Consensus.
- `/Users/mj/projects/ouroboros/README.md:140`: manual QA is replaced by automated gates.
- `/Users/mj/projects/ouroboros/README.md:162`: evaluation phase summary.
- `/Users/mj/projects/ouroboros/README.md:243`: evaluation module role.
- `/Users/mj/projects/ouroboros/llms-full.txt:201`: Phase 4 evaluation starts.
- `/Users/mj/projects/ouroboros/llms-full.txt:203`: evaluation components.
- `/Users/mj/projects/ouroboros/llms-full.txt:210`: Stage 1 mechanical checks.
- `/Users/mj/projects/ouroboros/llms-full.txt:214`: Stage 2 semantic checks.
- `/Users/mj/projects/ouroboros/llms-full.txt:219`: Stage 3 consensus.
- `/Users/mj/projects/ouroboros/docs/guides/evaluation-pipeline.md:1`: guide entrypoint.
- `/Users/mj/projects/ouroboros/docs/guides/evaluation-pipeline.md:3`: goal is to reject weak work early.
- `/Users/mj/projects/ouroboros/docs/guides/evaluation-pipeline.md:13`: Stage 1 section.
- `/Users/mj/projects/ouroboros/docs/guides/evaluation-pipeline.md:26`: Stage 2 section.
- `/Users/mj/projects/ouroboros/docs/guides/evaluation-pipeline.md:44`: Stage 3 section.
- `/Users/mj/projects/ouroboros/docs/guides/evaluation-pipeline.md:99`: result-reading questions.

## Evaluate Skill And MCP Handler

Important source locations:

- `/Users/mj/projects/ouroboros/skills/evaluate/SKILL.md:18`: evaluation pipeline overview.
- `/Users/mj/projects/ouroboros/skills/evaluate/SKILL.md:22`: Stage 1 is mechanical and zero-cost.
- `/Users/mj/projects/ouroboros/skills/evaluate/SKILL.md:27`: Stage 2 semantic evaluation.
- `/Users/mj/projects/ouroboros/skills/evaluate/SKILL.md:33`: Stage 3 multi-model consensus.
- `/Users/mj/projects/ouroboros/skills/evaluate/SKILL.md:42`: load MCP tools first.
- `/Users/mj/projects/ouroboros/skills/evaluate/SKILL.md:55`: evaluation steps.
- `/Users/mj/projects/ouroboros/skills/evaluate/SKILL.md:66`: call `ouroboros_evaluate`.
- `/Users/mj/projects/ouroboros/skills/evaluate/SKILL.md:78`: present stage results.
- `/Users/mj/projects/ouroboros/skills/evaluate/SKILL.md:90`: fallback uses evaluator agent.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:254`: `EvaluateHandler`.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:258`: handler describes three-stage pipeline.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:270`: tool definition.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:273`: `ouroboros_evaluate` tool name.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:326`: `trigger_consensus` parameter.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:333`: `working_dir` parameter controls Stage 1 command detection.

## Pipeline Code

Important source locations:

- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:1`: pipeline orchestrator.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:3`: three stages listed.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:37`: `PipelineConfig`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:60`: `EvaluationPipeline`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:85`: stage evaluators initialized.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:91`: `evaluate`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:129`: Stage 1 starts.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:157`: Stage 1 fail stops pipeline.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:166`: Stage 2 starts.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:175`: Stage 2 non-compliance can fail unless consensus is forced.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:186`: trigger context build.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:209`: Stage 3 starts if triggered.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:241`: no-consensus approval derives from Stage 2.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:254`: final result builder.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/pipeline.py:328`: convenience runner.

## Stage 1 Mechanical

Important source locations:

- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:1`: Stage 1 purpose.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:3`: zero-cost automated checks.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:28`: `MechanicalConfig`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:42`: coverage threshold.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:69`: async command runner.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:125`: coverage parser.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:152`: `MechanicalVerifier`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:171`: `verify`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:200`: runs each check.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:209`: determines overall pass/fail.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:212`: coverage threshold check.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/mechanical.py:256`: single-check runner.

## Stage 2 Semantic

Important source locations:

- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:1`: Stage 2 purpose.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:30`: semantic result schema.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:66`: `SemanticConfig`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:77`: default model.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:78`: temperature.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:80`: satisfaction threshold.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:83`: loads semantic-evaluator prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:90`: builds evaluation prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:145`: anti-gaming verification instructions.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:152`: transparency requirements.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:161`: semantic response parser.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:193`: required fields.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:239`: returns semantic result.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:262`: `SemanticEvaluator`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:287`: evaluator entrypoint.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/semantic.py:310`: messages are built.
- `/Users/mj/projects/ouroboros/src/ouroboros/agents/semantic-evaluator.md:1`: evaluator system prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/agents/semantic-evaluator.md:3`: JSON-only output.
- `/Users/mj/projects/ouroboros/src/ouroboros/agents/semantic-evaluator.md:15`: evaluation criteria.
- `/Users/mj/projects/ouroboros/src/ouroboros/agents/semantic-evaluator.md:25`: passing artifact thresholds.

## Stage 3 Consensus

Important source locations:

- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:1`: trigger matrix.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:3`: six trigger conditions.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:25`: trigger type enum.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:40`: trigger context.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:83`: trigger config thresholds.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:96`: `ConsensusTrigger`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:117`: evaluates triggers.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:133`: manual consensus has highest priority.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:150`: priority check order.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:228`: drift trigger.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/trigger.py:250`: uncertainty trigger.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:1`: Stage 3 consensus.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:5`: simple consensus.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:10`: deliberative consensus.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:52`: default consensus models.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:57`: single-model perspectives.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:83`: multi-model credential check.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:93`: vote schema.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:121`: `ConsensusConfig`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:140`: loads consensus-reviewer prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:147`: consensus prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:179`: vote parser.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:239`: `ConsensusEvaluator`.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:269`: evaluate entrypoint.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:302`: multi-model evaluation.
- `/Users/mj/projects/ouroboros/src/ouroboros/evaluation/consensus.py:349`: single-model multi-perspective fallback.
- `/Users/mj/projects/ouroboros/src/ouroboros/agents/consensus-reviewer.md:1`: consensus reviewer prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/agents/consensus-reviewer.md:3`: JSON-only vote output.
- `/Users/mj/projects/ouroboros/src/ouroboros/agents/consensus-reviewer.md:10`: approval criteria.

## Coflow Mapping

Use this mapping when comparing designs:

- Ouroboros Stage 1 maps to coflow repo-native verification commands and `co flow evidence`.
- Ouroboros Stage 2 maps to coflow Codex CLI pre-draft reviewers and any future schema-bound evaluator.
- Ouroboros Stage 3 maps to a future coflow consensus or escalation gate, not to current required behavior.
- Ouroboros drift and uncertainty triggers map to coflow halt conditions or planner review failures when they affect user-visible contract.

Do not skip coflow's mechanical evidence just because a semantic reviewer passes.
The strongest Ouroboros-compatible direction for coflow is progressive verification: cheap deterministic checks first, then constrained AI judgment, then escalation only when needed.
