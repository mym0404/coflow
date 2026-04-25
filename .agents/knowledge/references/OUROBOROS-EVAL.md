# Ouroboros Eval Reference

## What To Borrow

Ouroboros evaluation is a progressive gate:

- Stage 1: deterministic mechanical verification
- Stage 2: semantic model review against acceptance criteria and goal
- Stage 3: consensus only when uncertainty or drift requires it

coflow currently has planner bundle review and executor evidence gates.
When adding stronger evaluation behavior to coflow, prefer mechanical checks and recorded evidence first, then schema-bound model judgment, then user-visible halt or review gates.

## Evaluation Sources

README and guide:

- `ouroboros/README.md:112`: evaluation is a 3-stage gate.
- `ouroboros/README.md:121`: Mechanical -> Semantic -> Consensus.
- `ouroboros/README.md:140`: manual QA is replaced by automated gates.
- `ouroboros/README.md:162`: evaluation phase summary.
- `ouroboros/README.md:243`: evaluation module role.
- `ouroboros/llms-full.txt:201`: Phase 4 evaluation starts.
- `ouroboros/llms-full.txt:203`: evaluation components.
- `ouroboros/llms-full.txt:210`: Stage 1 mechanical checks.
- `ouroboros/llms-full.txt:214`: Stage 2 semantic checks.
- `ouroboros/llms-full.txt:219`: Stage 3 consensus.
- `ouroboros/docs/guides/evaluation-pipeline.md:1`: guide entrypoint.
- `ouroboros/docs/guides/evaluation-pipeline.md:3`: goal is to reject weak work early.
- `ouroboros/docs/guides/evaluation-pipeline.md:13`: Stage 1 section.
- `ouroboros/docs/guides/evaluation-pipeline.md:26`: Stage 2 section.
- `ouroboros/docs/guides/evaluation-pipeline.md:44`: Stage 3 section.
- `ouroboros/docs/guides/evaluation-pipeline.md:99`: result-reading questions.

## Evaluate Skill And MCP Handler

Important source locations:

- `ouroboros/skills/evaluate/SKILL.md:18`: evaluation pipeline overview.
- `ouroboros/skills/evaluate/SKILL.md:22`: Stage 1 is mechanical and zero-cost.
- `ouroboros/skills/evaluate/SKILL.md:27`: Stage 2 semantic evaluation.
- `ouroboros/skills/evaluate/SKILL.md:33`: Stage 3 multi-model consensus.
- `ouroboros/skills/evaluate/SKILL.md:42`: load MCP tools first.
- `ouroboros/skills/evaluate/SKILL.md:55`: evaluation steps.
- `ouroboros/skills/evaluate/SKILL.md:66`: call `ouroboros_evaluate`.
- `ouroboros/skills/evaluate/SKILL.md:78`: present stage results.
- `ouroboros/skills/evaluate/SKILL.md:90`: fallback uses evaluator agent.
- `ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:254`: `EvaluateHandler`.
- `ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:258`: handler describes three-stage pipeline.
- `ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:270`: tool definition.
- `ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:273`: `ouroboros_evaluate` tool name.
- `ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:326`: `trigger_consensus` parameter.
- `ouroboros/src/ouroboros/mcp/tools/evaluation_handlers.py:333`: `working_dir` parameter controls Stage 1 command detection.

## Pipeline Code

Important source locations:

- `ouroboros/src/ouroboros/evaluation/pipeline.py:1`: pipeline orchestrator.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:3`: three stages listed.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:37`: `PipelineConfig`.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:60`: `EvaluationPipeline`.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:85`: stage evaluators initialized.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:91`: `evaluate`.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:129`: Stage 1 starts.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:157`: Stage 1 fail stops pipeline.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:166`: Stage 2 starts.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:175`: Stage 2 non-compliance can fail unless consensus is forced.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:186`: trigger context build.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:209`: Stage 3 starts if triggered.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:241`: no-consensus approval derives from Stage 2.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:254`: final result builder.
- `ouroboros/src/ouroboros/evaluation/pipeline.py:328`: convenience runner.

## Stage 1 Mechanical

Important source locations:

- `ouroboros/src/ouroboros/evaluation/mechanical.py:1`: Stage 1 purpose.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:3`: zero-cost automated checks.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:28`: `MechanicalConfig`.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:42`: coverage threshold.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:69`: async command runner.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:125`: coverage parser.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:152`: `MechanicalVerifier`.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:171`: `verify`.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:200`: runs each check.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:209`: determines overall pass/fail.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:212`: coverage threshold check.
- `ouroboros/src/ouroboros/evaluation/mechanical.py:256`: single-check runner.

## Stage 2 Semantic

Important source locations:

- `ouroboros/src/ouroboros/evaluation/semantic.py:1`: Stage 2 purpose.
- `ouroboros/src/ouroboros/evaluation/semantic.py:30`: semantic result schema.
- `ouroboros/src/ouroboros/evaluation/semantic.py:66`: `SemanticConfig`.
- `ouroboros/src/ouroboros/evaluation/semantic.py:77`: default model.
- `ouroboros/src/ouroboros/evaluation/semantic.py:78`: temperature.
- `ouroboros/src/ouroboros/evaluation/semantic.py:80`: satisfaction threshold.
- `ouroboros/src/ouroboros/evaluation/semantic.py:83`: loads semantic-evaluator prompt.
- `ouroboros/src/ouroboros/evaluation/semantic.py:90`: builds evaluation prompt.
- `ouroboros/src/ouroboros/evaluation/semantic.py:145`: anti-gaming verification instructions.
- `ouroboros/src/ouroboros/evaluation/semantic.py:152`: transparency requirements.
- `ouroboros/src/ouroboros/evaluation/semantic.py:161`: semantic response parser.
- `ouroboros/src/ouroboros/evaluation/semantic.py:193`: required fields.
- `ouroboros/src/ouroboros/evaluation/semantic.py:239`: returns semantic result.
- `ouroboros/src/ouroboros/evaluation/semantic.py:262`: `SemanticEvaluator`.
- `ouroboros/src/ouroboros/evaluation/semantic.py:287`: evaluator entrypoint.
- `ouroboros/src/ouroboros/evaluation/semantic.py:310`: messages are built.
- `ouroboros/src/ouroboros/agents/semantic-evaluator.md:1`: evaluator system prompt.
- `ouroboros/src/ouroboros/agents/semantic-evaluator.md:3`: JSON-only output.
- `ouroboros/src/ouroboros/agents/semantic-evaluator.md:15`: evaluation criteria.
- `ouroboros/src/ouroboros/agents/semantic-evaluator.md:25`: passing artifact thresholds.

## Stage 3 Consensus

Important source locations:

- `ouroboros/src/ouroboros/evaluation/trigger.py:1`: trigger matrix.
- `ouroboros/src/ouroboros/evaluation/trigger.py:3`: six trigger conditions.
- `ouroboros/src/ouroboros/evaluation/trigger.py:25`: trigger type enum.
- `ouroboros/src/ouroboros/evaluation/trigger.py:40`: trigger context.
- `ouroboros/src/ouroboros/evaluation/trigger.py:83`: trigger config thresholds.
- `ouroboros/src/ouroboros/evaluation/trigger.py:96`: `ConsensusTrigger`.
- `ouroboros/src/ouroboros/evaluation/trigger.py:117`: evaluates triggers.
- `ouroboros/src/ouroboros/evaluation/trigger.py:133`: manual consensus has highest priority.
- `ouroboros/src/ouroboros/evaluation/trigger.py:150`: priority check order.
- `ouroboros/src/ouroboros/evaluation/trigger.py:228`: drift trigger.
- `ouroboros/src/ouroboros/evaluation/trigger.py:250`: uncertainty trigger.
- `ouroboros/src/ouroboros/evaluation/consensus.py:1`: Stage 3 consensus.
- `ouroboros/src/ouroboros/evaluation/consensus.py:5`: simple consensus.
- `ouroboros/src/ouroboros/evaluation/consensus.py:10`: deliberative consensus.
- `ouroboros/src/ouroboros/evaluation/consensus.py:52`: default consensus models.
- `ouroboros/src/ouroboros/evaluation/consensus.py:57`: single-model perspectives.
- `ouroboros/src/ouroboros/evaluation/consensus.py:83`: multi-model credential check.
- `ouroboros/src/ouroboros/evaluation/consensus.py:93`: vote schema.
- `ouroboros/src/ouroboros/evaluation/consensus.py:121`: `ConsensusConfig`.
- `ouroboros/src/ouroboros/evaluation/consensus.py:140`: loads consensus-reviewer prompt.
- `ouroboros/src/ouroboros/evaluation/consensus.py:147`: consensus prompt.
- `ouroboros/src/ouroboros/evaluation/consensus.py:179`: vote parser.
- `ouroboros/src/ouroboros/evaluation/consensus.py:239`: `ConsensusEvaluator`.
- `ouroboros/src/ouroboros/evaluation/consensus.py:269`: evaluate entrypoint.
- `ouroboros/src/ouroboros/evaluation/consensus.py:302`: multi-model evaluation.
- `ouroboros/src/ouroboros/evaluation/consensus.py:349`: single-model multi-perspective fallback.
- `ouroboros/src/ouroboros/agents/consensus-reviewer.md:1`: consensus reviewer prompt.
- `ouroboros/src/ouroboros/agents/consensus-reviewer.md:3`: JSON-only vote output.
- `ouroboros/src/ouroboros/agents/consensus-reviewer.md:10`: approval criteria.

## Coflow Mapping

Use this mapping when comparing designs:

- Ouroboros Stage 1 maps to coflow repo-native verification commands and `co.py flow evidence`.
- Ouroboros Stage 2 maps to coflow Codex CLI bundle reviewers and any future schema-bound evaluator.
- Ouroboros Stage 3 maps to a future coflow consensus or escalation gate, not to current required behavior.
- Ouroboros drift and uncertainty triggers map to coflow halt conditions or planner review failures when they affect user-visible contract.

Do not skip coflow's mechanical evidence just because a semantic reviewer passes.
The strongest Ouroboros-compatible direction for coflow is progressive verification: cheap deterministic checks first, then constrained AI judgment, then escalation only when needed.
