# Ouroboros Eval Reference

## What To Borrow

Ouroboros evaluation is a progressive gate:

- Stage 1: deterministic mechanical verification
- Stage 2: semantic model review against acceptance criteria and goal
- Stage 3: consensus only when uncertainty or drift requires it

coflow currently has planner bundle validation plus executor mechanical evidence, semantic root-agent self-review evidence, and task-done gates.
When adding stronger evaluation behavior to coflow, prefer mechanical checks and recorded evidence first, then constrained semantic judgment, then user-visible halt or escalation gates.

## Evaluation Sources

README and guide:

- `README.md:112`: evaluation is a 3-stage gate.
- `README.md:121`: Mechanical -> Semantic -> Consensus.
- `README.md:140`: manual QA is replaced by automated gates.
- `README.md:162`: evaluation phase summary.
- `README.md:243`: evaluation module role.
- `llms-full.txt:201`: Phase 4 evaluation starts.
- `llms-full.txt:203`: evaluation components.
- `llms-full.txt:210`: Stage 1 mechanical checks.
- `llms-full.txt:214`: Stage 2 semantic checks.
- `llms-full.txt:219`: Stage 3 consensus.
- `docs/guides/evaluation-pipeline.md:1`: guide entrypoint.
- `docs/guides/evaluation-pipeline.md:3`: goal is to reject weak work early.
- `docs/guides/evaluation-pipeline.md:13`: Stage 1 section.
- `docs/guides/evaluation-pipeline.md:26`: Stage 2 section.
- `docs/guides/evaluation-pipeline.md:44`: Stage 3 section.
- `docs/guides/evaluation-pipeline.md:99`: result-reading questions.

## Evaluate Skill And MCP Handler

Important source locations:

- `skills/evaluate/SKILL.md:18`: evaluation pipeline overview.
- `skills/evaluate/SKILL.md:22`: Stage 1 is mechanical and zero-cost.
- `skills/evaluate/SKILL.md:27`: Stage 2 semantic evaluation.
- `skills/evaluate/SKILL.md:33`: Stage 3 multi-model consensus.
- `skills/evaluate/SKILL.md:42`: load MCP tools first.
- `skills/evaluate/SKILL.md:55`: evaluation steps.
- `skills/evaluate/SKILL.md:66`: call `ouroboros_evaluate`.
- `skills/evaluate/SKILL.md:78`: present stage results.
- `skills/evaluate/SKILL.md:90`: fallback uses evaluator agent.
- `src/ouroboros/mcp/tools/evaluation_handlers.py:254`: `EvaluateHandler`.
- `src/ouroboros/mcp/tools/evaluation_handlers.py:258`: handler describes three-stage pipeline.
- `src/ouroboros/mcp/tools/evaluation_handlers.py:270`: tool definition.
- `src/ouroboros/mcp/tools/evaluation_handlers.py:273`: `ouroboros_evaluate` tool name.
- `src/ouroboros/mcp/tools/evaluation_handlers.py:326`: `trigger_consensus` parameter.
- `src/ouroboros/mcp/tools/evaluation_handlers.py:333`: `working_dir` parameter controls Stage 1 command detection.

## Pipeline Code

Important source locations:

- `src/ouroboros/evaluation/pipeline.py:1`: pipeline orchestrator.
- `src/ouroboros/evaluation/pipeline.py:3`: three stages listed.
- `src/ouroboros/evaluation/pipeline.py:37`: `PipelineConfig`.
- `src/ouroboros/evaluation/pipeline.py:60`: `EvaluationPipeline`.
- `src/ouroboros/evaluation/pipeline.py:85`: stage evaluators initialized.
- `src/ouroboros/evaluation/pipeline.py:91`: `evaluate`.
- `src/ouroboros/evaluation/pipeline.py:129`: Stage 1 starts.
- `src/ouroboros/evaluation/pipeline.py:157`: Stage 1 fail stops pipeline.
- `src/ouroboros/evaluation/pipeline.py:166`: Stage 2 starts.
- `src/ouroboros/evaluation/pipeline.py:175`: Stage 2 non-compliance can fail unless consensus is forced.
- `src/ouroboros/evaluation/pipeline.py:186`: trigger context build.
- `src/ouroboros/evaluation/pipeline.py:209`: Stage 3 starts if triggered.
- `src/ouroboros/evaluation/pipeline.py:241`: no-consensus approval derives from Stage 2.
- `src/ouroboros/evaluation/pipeline.py:254`: final result builder.
- `src/ouroboros/evaluation/pipeline.py:328`: convenience runner.

## Stage 1 Mechanical

Important source locations:

- `src/ouroboros/evaluation/mechanical.py:1`: Stage 1 purpose.
- `src/ouroboros/evaluation/mechanical.py:3`: zero-cost automated checks.
- `src/ouroboros/evaluation/mechanical.py:28`: `MechanicalConfig`.
- `src/ouroboros/evaluation/mechanical.py:42`: coverage threshold.
- `src/ouroboros/evaluation/mechanical.py:69`: async command runner.
- `src/ouroboros/evaluation/mechanical.py:125`: coverage parser.
- `src/ouroboros/evaluation/mechanical.py:152`: `MechanicalVerifier`.
- `src/ouroboros/evaluation/mechanical.py:171`: `verify`.
- `src/ouroboros/evaluation/mechanical.py:200`: runs each check.
- `src/ouroboros/evaluation/mechanical.py:209`: determines overall pass/fail.
- `src/ouroboros/evaluation/mechanical.py:212`: coverage threshold check.
- `src/ouroboros/evaluation/mechanical.py:256`: single-check runner.

## Stage 2 Semantic

Important source locations:

- `src/ouroboros/evaluation/semantic.py:1`: Stage 2 purpose.
- `src/ouroboros/evaluation/semantic.py:30`: semantic result schema.
- `src/ouroboros/evaluation/semantic.py:66`: `SemanticConfig`.
- `src/ouroboros/evaluation/semantic.py:77`: default model.
- `src/ouroboros/evaluation/semantic.py:78`: temperature.
- `src/ouroboros/evaluation/semantic.py:80`: satisfaction threshold.
- `src/ouroboros/evaluation/semantic.py:83`: loads semantic-evaluator prompt.
- `src/ouroboros/evaluation/semantic.py:90`: builds evaluation prompt.
- `src/ouroboros/evaluation/semantic.py:145`: anti-gaming verification instructions.
- `src/ouroboros/evaluation/semantic.py:152`: transparency requirements.
- `src/ouroboros/evaluation/semantic.py:161`: semantic response parser.
- `src/ouroboros/evaluation/semantic.py:193`: required fields.
- `src/ouroboros/evaluation/semantic.py:239`: returns semantic result.
- `src/ouroboros/evaluation/semantic.py:262`: `SemanticEvaluator`.
- `src/ouroboros/evaluation/semantic.py:287`: evaluator entrypoint.
- `src/ouroboros/evaluation/semantic.py:310`: messages are built.
- `src/ouroboros/agents/semantic-evaluator.md:1`: evaluator system prompt.
- `src/ouroboros/agents/semantic-evaluator.md:3`: JSON-only output.
- `src/ouroboros/agents/semantic-evaluator.md:15`: evaluation criteria.
- `src/ouroboros/agents/semantic-evaluator.md:25`: passing artifact thresholds.

## Stage 3 Consensus

Important source locations:

- `src/ouroboros/evaluation/trigger.py:1`: trigger matrix.
- `src/ouroboros/evaluation/trigger.py:3`: six trigger conditions.
- `src/ouroboros/evaluation/trigger.py:25`: trigger type enum.
- `src/ouroboros/evaluation/trigger.py:40`: trigger context.
- `src/ouroboros/evaluation/trigger.py:83`: trigger config thresholds.
- `src/ouroboros/evaluation/trigger.py:96`: `ConsensusTrigger`.
- `src/ouroboros/evaluation/trigger.py:117`: evaluates triggers.
- `src/ouroboros/evaluation/trigger.py:133`: manual consensus has highest priority.
- `src/ouroboros/evaluation/trigger.py:150`: priority check order.
- `src/ouroboros/evaluation/trigger.py:228`: drift trigger.
- `src/ouroboros/evaluation/trigger.py:250`: uncertainty trigger.
- `src/ouroboros/evaluation/consensus.py:1`: Stage 3 consensus.
- `src/ouroboros/evaluation/consensus.py:5`: simple consensus.
- `src/ouroboros/evaluation/consensus.py:10`: deliberative consensus.
- `src/ouroboros/evaluation/consensus.py:52`: default consensus models.
- `src/ouroboros/evaluation/consensus.py:57`: single-model perspectives.
- `src/ouroboros/evaluation/consensus.py:83`: multi-model credential check.
- `src/ouroboros/evaluation/consensus.py:93`: vote schema.
- `src/ouroboros/evaluation/consensus.py:121`: `ConsensusConfig`.
- `src/ouroboros/evaluation/consensus.py:140`: loads consensus-reviewer prompt.
- `src/ouroboros/evaluation/consensus.py:147`: consensus prompt.
- `src/ouroboros/evaluation/consensus.py:179`: vote parser.
- `src/ouroboros/evaluation/consensus.py:239`: `ConsensusEvaluator`.
- `src/ouroboros/evaluation/consensus.py:269`: evaluate entrypoint.
- `src/ouroboros/evaluation/consensus.py:302`: multi-model evaluation.
- `src/ouroboros/evaluation/consensus.py:349`: single-model multi-perspective fallback.
- `src/ouroboros/agents/consensus-reviewer.md:1`: consensus reviewer prompt.
- `src/ouroboros/agents/consensus-reviewer.md:3`: JSON-only vote output.
- `src/ouroboros/agents/consensus-reviewer.md:10`: approval criteria.

## Coflow Mapping

Use this mapping when comparing designs:

- Ouroboros Stage 1 maps to coflow repo-native verification commands and `co.py flow evidence --kind mechanical`.
- Ouroboros Stage 2 maps to coflow root-agent semantic self-review records and future schema-bound evaluators.
- Ouroboros Stage 3 maps to a future coflow consensus or escalation gate, not to current required behavior.
- Ouroboros drift and uncertainty triggers map to coflow halt conditions or planner review failures when they affect user-visible contract.

Do not skip coflow's mechanical evidence just because a semantic reviewer passes.
The strongest Ouroboros-compatible direction for coflow is progressive verification: cheap deterministic checks first, then constrained AI judgment, then escalation only when needed.
