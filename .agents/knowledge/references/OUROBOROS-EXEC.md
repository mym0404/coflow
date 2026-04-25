# Ouroboros Exec Reference

## What To Borrow

Ouroboros execution is based on structured execution from an immutable specification:

- load a Seed
- choose runtime backend
- decompose acceptance criteria
- execute independent work in dependency levels
- run or dispatch subagents
- collect evidence for QA and evaluation

coflow's `coexec` is a smaller Codex adaptation.
It runs an approved plan bundle sequentially through `co`, with task state, evidence records, repairs, and halt conditions managed mechanically.

## Execution Sources

README and context summary:

- `/Users/mj/projects/ouroboros/README.md:120`: `run` executes through Double Diamond decomposition.
- `/Users/mj/projects/ouroboros/README.md:161`: Execute phase is Discover -> Define -> Design -> Deliver.
- `/Users/mj/projects/ouroboros/README.md:194`: `ooo run` maps to `ouroboros run seed.yaml`.
- `/Users/mj/projects/ouroboros/README.md:242`: execution module handles Double Diamond and hierarchical AC decomposition.
- `/Users/mj/projects/ouroboros/llms-full.txt:159`: Double Diamond phase starts.
- `/Users/mj/projects/ouroboros/llms-full.txt:161`: execution components.
- `/Users/mj/projects/ouroboros/llms-full.txt:167`: four phases.
- `/Users/mj/projects/ouroboros/llms-full.txt:173`: recursive decomposition.
- `/Users/mj/projects/ouroboros/llms-full.txt:178`: max depth and compression constraints.
- `/Users/mj/projects/ouroboros/llms-full.txt:354`: AgentRuntime protocol.
- `/Users/mj/projects/ouroboros/llms-full.txt:391`: Codex CLI runtime module.

## Run Skill And CLI

Ouroboros run surface:

- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:22`: run skill overview.
- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:24`: input is seed YAML or path.
- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:25`: validation step.
- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:26`: orchestrator runs workflow with PAL routing.
- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:34`: load MCP tools first.
- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:47`: execution steps start.
- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:61`: starts background execution with `ouroboros_start_execute_seed`.
- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:79`: user chooses polling strategy.
- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:129`: progress polling via AC tree HUD.
- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:194`: final result fetched by job id.
- `/Users/mj/projects/ouroboros/skills/run/SKILL.md:206`: post-execution QA is automatic.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:32`: Typer group defaults to workflow.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:55`: only Codex runtime backend is exposed in this version.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:294`: `_run_orchestrator`.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:325`: loads Seed YAML.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:334`: resolves max decomposition depth.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:365`: event store path.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:370`: resolves project dir.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:404`: creates agent runtime.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:408`: constructs `OrchestratorRunner`.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:441`: executes seed.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:452`: post-execution QA starts.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:505`: `workflow` command.
- `/Users/mj/projects/ouroboros/src/ouroboros/cli/commands/run.py:600`: workflow docstring.

## Double Diamond Code

The Double Diamond implementation is the clearest conceptual source for coflow task decomposition, but coflow currently uses static `tasks.yaml` plus executor state rather than recursive AC execution.

Important source locations:

- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:1`: module purpose.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:3`: four phases listed.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:9`: module implementation scope.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:61`: topological sort to levels.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:65`: dependency levels are for parallel execution.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:151`: phase prompts.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:153`: Discover prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:172`: Define prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:192`: Design prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:212`: Deliver prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:239`: `Phase` enum.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:242`: diverge/converge pattern.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/double_diamond.py:270`: next-phase sequence.

## Decomposition And Subagents

Ouroboros decomposes non-atomic ACs into child ACs, validates shape, and isolates child execution.

Important source locations:

- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:1`: decomposition purpose.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:9`: decomposition rules.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:56`: constraints.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:63`: result model.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:110`: decomposition system prompt.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:121`: 2-5 child ACs.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:127`: user prompt template.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:138`: JSON output requirement.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:194`: child validation.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:261`: context compression.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:288`: `decompose_ac`.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/decomposition.py:327`: max depth check.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/subagent.py:1`: subagent isolation and lifecycle.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/subagent.py:8`: isolation ACs.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/subagent.py:70`: `validate_child_result`.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/subagent.py:92`: unsuccessful child check.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/subagent.py:107`: required phases for non-decomposed results.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/subagent.py:127`: decomposed results require Discover and Define.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/subagent.py:162`: subagent started event.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/subagent.py:191`: subagent completed event.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/subagent.py:220`: subagent failed event.
- `/Users/mj/projects/ouroboros/src/ouroboros/execution/subagent.py:249`: subagent validated event.

## Orchestrator And Codex Runtime

Ouroboros has a richer runtime abstraction than coflow.
coflow should only borrow the parts that can be expressed as `co` state transitions, stdout contracts, and evidence gates.

Important source locations:

- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/parallel_executor.py:1`: parallel AC execution orchestrator.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/parallel_executor.py:6`: features.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/parallel_executor.py:106`: decomposition constants.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/parallel_executor.py:156`: stall detection constants.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/parallel_executor.py:331`: verification report rendering.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/codex_cli_runtime.py:1`: Codex CLI runtime.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/codex_cli_runtime.py:61`: runtime class.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/codex_cli_runtime.py:83`: initialization.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/codex_cli_runtime.py:136`: permission mode resolution.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/codex_cli_runtime.py:154`: CLI path resolution.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/codex_cli_runtime.py:181`: runtime handle builder.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/codex_cli_runtime.py:212`: prompt composition for Codex CLI exec mode.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/codex_cli_runtime.py:273`: built-in MCP handler loading.
- `/Users/mj/projects/ouroboros/src/ouroboros/orchestrator/codex_cli_runtime.py:292`: intercepted skill arguments.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/execution_handlers.py:107`: `ExecuteSeedHandler`.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/execution_handlers.py:123`: MCP tool definition.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/execution_handlers.py:186`: handler entrypoint.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/execution_handlers.py:285`: subagent dispatch payload.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/execution_handlers.py:295`: plugin dispatch gate.
- `/Users/mj/projects/ouroboros/src/ouroboros/mcp/tools/execution_handlers.py:316`: in-process seed parsing path.

## Coflow Mapping

Use this mapping when comparing designs:

- Ouroboros Seed execution maps to coflow `co flow next`, `co flow evidence`, `co flow repair`, and `co flow halt`.
- Ouroboros parallel AC execution maps conceptually to `tasks.yaml.depends_on`, but coflow currently executes one `Doing` task at a time.
- Ouroboros subagent isolation maps conceptually to Codex CLI subagents used by `co` during planning review and scoring, not to arbitrary executor delegation.
- Ouroboros post-execution QA maps conceptually to coflow final verification tasks and required evidence records.
- Ouroboros event sourcing maps only loosely to coflow `status.yaml`, `evidence.yaml`, and `notes.yaml`; coflow does not maintain an executor event log or SQLite replay model.

Do not import Ouroboros parallelism into coflow by default.
If coflow adopts parallel execution later, it should first make ownership, evidence, and collision boundaries mechanically explicit in `co`.
