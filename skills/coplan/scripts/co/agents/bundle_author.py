ROLE = "bundle_author"


def schema():
    string_array = {"type": "array", "items": {"type": "string"}}
    non_empty_string_array = {"type": "array", "minItems": 1, "items": {"type": "string"}}
    repo_inspection = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "files_read": non_empty_string_array,
            "commands_considered": non_empty_string_array,
            "grounding_summary": {"type": "string"},
        },
        "required": ["files_read", "commands_considered", "grounding_summary"],
    }
    mechanical_check = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string"},
            "command": {"type": "string"},
            "success_signal": {"type": "string"},
        },
        "required": ["id", "command", "success_signal"],
    }
    semantic_check = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string"},
            "lens": {"type": "string"},
            "review_prompt": {"type": "string"},
            "pass_signal": {"type": "string"},
        },
        "required": ["id", "lens", "review_prompt", "pass_signal"],
    }
    task = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string"},
            "kind": {"type": "string", "enum": ["execution", "checkpoint", "final_verification"]},
            "title": {"type": "string"},
            "depends_on": string_array,
            "start_when": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"description": {"type": "string"}},
                "required": ["description"],
            },
            "files": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "primary": string_array,
                    "generated_incidental": string_array,
                },
                "required": ["primary", "generated_incidental"],
            },
            "context": {"type": "string"},
            "must_do": string_array,
            "must_not_do": string_array,
            "implementation_notes": string_array,
            "verification": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "mechanical": {"type": "array", "minItems": 1, "items": mechanical_check},
                    "semantic": {"type": "array", "minItems": 1, "items": semantic_check},
                },
                "required": ["mechanical", "semantic"],
            },
            "acceptance_criteria": string_array,
            "reopen_when": string_array,
        },
        "required": [
            "id",
            "kind",
            "title",
            "depends_on",
            "start_when",
            "files",
            "context",
            "must_do",
            "must_not_do",
            "implementation_notes",
            "verification",
            "acceptance_criteria",
            "reopen_when",
        ],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "tasks": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"tasks": {"type": "array", "items": task}},
                "required": ["tasks"],
            },
            "summary": {"type": "string"},
            "repo_inspection": repo_inspection,
        },
        "required": ["tasks", "summary", "repo_inspection"],
    }


def prompt(*, context, feedback=None):
    extra = ""
    if feedback:
        extra += "\nUser seed feedback to apply:\n" + feedback
    return (
        "You are the coplan bundle_author. Produce final tasks.yaml content as JSON only.\n"
        "Use plan_seed.yaml as the source of truth. Inspect the repository only to ground implementation boundaries and commands. Do not edit files directly. Do not leave TBD placeholders.\n"
        "Return repo_inspection with the repo files you read, commands you considered, and a concise grounding_summary. Do not include execution evidence artifacts there.\n"
        "Do not expand, narrow, or reinterpret the seed. Project goal, constraints, non-goals, success criteria, execution boundaries, and verification expectations must be projected into task context, must_do, must_not_do, acceptance_criteria, and verification.\n"
        "Every task must satisfy the coflow task schema and include at least one final_verification task. Every task verification must include mechanical command checks and semantic root-agent self-review checks.\n"
        "Mechanical checks are local commands that should pass for the task, including repo-native always-on checks when relevant and focused task-specific checks. Semantic checks are self-review lenses with concrete review prompts and pass signals tied to the approved plan seed and current task acceptance criteria.\n"
        "Final verification tasks must depend on every non-final task and must be full-scope: include broad repo-native mechanical verification using real validation commands such as test, lint, typecheck, build, compile, or repo-native check commands, plus semantic reviews covering plan seed fit, acceptance criteria, regression risk, and evidence interpretation.\n"
        "Keep execution decisions static so the executor does not need to plan.\n\n"
        f"Context:\n{context}"
        f"{extra}"
    )


def summarize(output):
    tasks = output.get("tasks", {}).get("tasks", []) if isinstance(output.get("tasks"), dict) else []
    return {
        "task_count": len(tasks) if isinstance(tasks, list) else None,
        "repo_inspection_files": (
            len(output.get("repo_inspection", {}).get("files_read", []))
            if isinstance(output.get("repo_inspection"), dict)
            and isinstance(output.get("repo_inspection", {}).get("files_read"), list)
            else None
        ),
    }
