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
It runs an approved plan bundle sequentially through `co.py`, with task state, evidence records, repairs, and halt conditions managed mechanically.

## Execution Sources

README and context summary:

- `README.md:120`: `run` executes through Double Diamond decomposition.
- `README.md:161`: Execute phase is Discover -> Define -> Design -> Deliver.
- `README.md:194`: `ooo run` maps to `ouroboros run seed.yaml`.
- `README.md:242`: execution module handles Double Diamond and hierarchical AC decomposition.
- `llms-full.txt:159`: Double Diamond phase starts.
- `llms-full.txt:161`: execution components.
- `llms-full.txt:167`: four phases.
- `llms-full.txt:173`: recursive decomposition.
- `llms-full.txt:178`: max depth and compression constraints.
- `llms-full.txt:354`: AgentRuntime protocol.
- `llms-full.txt:391`: Codex CLI runtime module.

## Run Skill And CLI

Ouroboros run surface:

- `skills/run/SKILL.md:22`: run skill overview.
- `skills/run/SKILL.md:24`: input is seed YAML or path.
- `skills/run/SKILL.md:25`: validation step.
- `skills/run/SKILL.md:26`: orchestrator runs workflow with PAL routing.
- `skills/run/SKILL.md:34`: load MCP tools first.
- `skills/run/SKILL.md:47`: execution steps start.
- `skills/run/SKILL.md:61`: starts background execution with `ouroboros_start_execute_seed`.
- `skills/run/SKILL.md:79`: user chooses polling strategy.
- `skills/run/SKILL.md:129`: progress polling via AC tree HUD.
- `skills/run/SKILL.md:194`: final result fetched by job id.
- `skills/run/SKILL.md:206`: post-execution QA is automatic.
- `src/ouroboros/cli/commands/run.py:32`: Typer group defaults to workflow.
- `src/ouroboros/cli/commands/run.py:55`: only Codex runtime backend is exposed in this version.
- `src/ouroboros/cli/commands/run.py:294`: `_run_orchestrator`.
- `src/ouroboros/cli/commands/run.py:325`: loads Seed YAML.
- `src/ouroboros/cli/commands/run.py:334`: resolves max decomposition depth.
- `src/ouroboros/cli/commands/run.py:365`: event store path.
- `src/ouroboros/cli/commands/run.py:370`: resolves project dir.
- `src/ouroboros/cli/commands/run.py:404`: creates agent runtime.
- `src/ouroboros/cli/commands/run.py:408`: constructs `OrchestratorRunner`.
- `src/ouroboros/cli/commands/run.py:441`: executes seed.
- `src/ouroboros/cli/commands/run.py:452`: post-execution QA starts.
- `src/ouroboros/cli/commands/run.py:505`: `workflow` command.
- `src/ouroboros/cli/commands/run.py:600`: workflow docstring.

## Double Diamond Code

The Double Diamond implementation is the clearest conceptual source for coflow task decomposition, but coflow currently uses static `tasks.yaml` plus executor state rather than recursive AC execution.

Important source locations:

- `src/ouroboros/execution/double_diamond.py:1`: module purpose.
- `src/ouroboros/execution/double_diamond.py:3`: four phases listed.
- `src/ouroboros/execution/double_diamond.py:9`: module implementation scope.
- `src/ouroboros/execution/double_diamond.py:61`: topological sort to levels.
- `src/ouroboros/execution/double_diamond.py:65`: dependency levels are for parallel execution.
- `src/ouroboros/execution/double_diamond.py:151`: phase prompts.
- `src/ouroboros/execution/double_diamond.py:153`: Discover prompt.
- `src/ouroboros/execution/double_diamond.py:172`: Define prompt.
- `src/ouroboros/execution/double_diamond.py:192`: Design prompt.
- `src/ouroboros/execution/double_diamond.py:212`: Deliver prompt.
- `src/ouroboros/execution/double_diamond.py:239`: `Phase` enum.
- `src/ouroboros/execution/double_diamond.py:242`: diverge/converge pattern.
- `src/ouroboros/execution/double_diamond.py:270`: next-phase sequence.

## Decomposition And Subagents

Ouroboros decomposes non-atomic ACs into child ACs, validates shape, and isolates child execution.

Important source locations:

- `src/ouroboros/execution/decomposition.py:1`: decomposition purpose.
- `src/ouroboros/execution/decomposition.py:9`: decomposition rules.
- `src/ouroboros/execution/decomposition.py:56`: constraints.
- `src/ouroboros/execution/decomposition.py:63`: result model.
- `src/ouroboros/execution/decomposition.py:110`: decomposition system prompt.
- `src/ouroboros/execution/decomposition.py:121`: 2-5 child ACs.
- `src/ouroboros/execution/decomposition.py:127`: user prompt template.
- `src/ouroboros/execution/decomposition.py:138`: JSON output requirement.
- `src/ouroboros/execution/decomposition.py:194`: child validation.
- `src/ouroboros/execution/decomposition.py:261`: context compression.
- `src/ouroboros/execution/decomposition.py:288`: `decompose_ac`.
- `src/ouroboros/execution/decomposition.py:327`: max depth check.
- `src/ouroboros/execution/subagent.py:1`: subagent isolation and lifecycle.
- `src/ouroboros/execution/subagent.py:8`: isolation ACs.
- `src/ouroboros/execution/subagent.py:70`: `validate_child_result`.
- `src/ouroboros/execution/subagent.py:92`: unsuccessful child check.
- `src/ouroboros/execution/subagent.py:107`: required phases for non-decomposed results.
- `src/ouroboros/execution/subagent.py:127`: decomposed results require Discover and Define.
- `src/ouroboros/execution/subagent.py:162`: subagent started event.
- `src/ouroboros/execution/subagent.py:191`: subagent completed event.
- `src/ouroboros/execution/subagent.py:220`: subagent failed event.
- `src/ouroboros/execution/subagent.py:249`: subagent validated event.

## Orchestrator And Codex Runtime

Ouroboros has a richer runtime abstraction than coflow.
coflow should only borrow the parts that can be expressed as `co.py` state transitions, stdout contracts, and verification gates.

Important source locations:

- `src/ouroboros/orchestrator/parallel_executor.py:1`: parallel AC execution orchestrator.
- `src/ouroboros/orchestrator/parallel_executor.py:6`: features.
- `src/ouroboros/orchestrator/parallel_executor.py:106`: decomposition constants.
- `src/ouroboros/orchestrator/parallel_executor.py:156`: stall detection constants.
- `src/ouroboros/orchestrator/parallel_executor.py:331`: verification report rendering.
- `src/ouroboros/orchestrator/codex_cli_runtime.py:1`: Codex CLI runtime.
- `src/ouroboros/orchestrator/codex_cli_runtime.py:61`: runtime class.
- `src/ouroboros/orchestrator/codex_cli_runtime.py:83`: initialization.
- `src/ouroboros/orchestrator/codex_cli_runtime.py:136`: permission mode resolution.
- `src/ouroboros/orchestrator/codex_cli_runtime.py:154`: CLI path resolution.
- `src/ouroboros/orchestrator/codex_cli_runtime.py:181`: runtime handle builder.
- `src/ouroboros/orchestrator/codex_cli_runtime.py:212`: prompt composition for Codex CLI exec mode.
- `src/ouroboros/orchestrator/codex_cli_runtime.py:273`: built-in MCP handler loading.
- `src/ouroboros/orchestrator/codex_cli_runtime.py:292`: intercepted skill arguments.
- `src/ouroboros/mcp/tools/execution_handlers.py:107`: `ExecuteSeedHandler`.
- `src/ouroboros/mcp/tools/execution_handlers.py:123`: MCP tool definition.
- `src/ouroboros/mcp/tools/execution_handlers.py:186`: handler entrypoint.
- `src/ouroboros/mcp/tools/execution_handlers.py:285`: subagent dispatch payload.
- `src/ouroboros/mcp/tools/execution_handlers.py:295`: plugin dispatch gate.
- `src/ouroboros/mcp/tools/execution_handlers.py:316`: in-process seed parsing path.

## Coflow Mapping

Use this mapping when comparing designs:

- Ouroboros Seed execution maps to coflow `co.py flow next`, `co.py flow evidence`, `co.py flow task-done`, `co.py flow repair`, and `co.py flow halt`.
- Ouroboros parallel AC execution maps conceptually to `tasks.yaml.depends_on`, but coflow currently executes one `Doing` task at a time.
- Ouroboros subagent isolation maps conceptually to Codex CLI subagents used by `co.py` during planning review and scoring, not to arbitrary executor delegation.
- Ouroboros post-execution QA maps conceptually to coflow final verification tasks with required mechanical and semantic verification records.
- Ouroboros event sourcing maps only loosely to coflow `status.yaml`, `evidence.yaml`, and `notes.yaml`; coflow does not maintain an executor event log or SQLite replay model.

Do not import Ouroboros parallelism into coflow by default.
If coflow adopts parallel execution later, it should first make ownership, evidence, and collision boundaries mechanically explicit in `co.py`.
