ROLE = "bundle_author"


def schema():
    string_array = {"type": "array", "items": {"type": "string"}}
    verification_step = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string"},
            "command": {"type": "string"},
            "success_signal": {"type": "string"},
        },
        "required": ["id", "command", "success_signal"],
    }
    expected_evidence = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "step_id": {"type": "string"},
            "file": {"type": "string", "pattern": "^evidence/[^/].+"},
        },
        "required": ["step_id", "file"],
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
                    "evidence_required": {"type": "boolean"},
                    "steps": {"type": "array", "items": verification_step},
                },
                "required": ["evidence_required", "steps"],
            },
            "acceptance_criteria": string_array,
            "expected_evidence": {"type": "array", "items": expected_evidence},
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
            "expected_evidence",
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
        },
        "required": ["tasks", "summary"],
    }


def prompt(*, context, review_results=None, feedback=None, dump_json):
    extra = ""
    if review_results:
        extra += "\nBundle review findings to fix:\n" + dump_json(review_results)
    if feedback:
        extra += "\nUser seed feedback to apply:\n" + feedback
    return (
        "You are the coplan bundle_author. Produce final tasks.yaml content as JSON only.\n"
        "Use plan_seed.yaml as the source of truth. Inspect the repository only to ground implementation boundaries and commands. Do not edit files directly. Do not leave TBD placeholders.\n"
        "Do not expand, narrow, or reinterpret the seed. Project goal, constraints, non-goals, success criteria, execution boundaries, and verification expectations must be projected into task context, must_do, must_not_do, acceptance_criteria, and verification.\n"
        "Every task must satisfy the coflow task schema and include at least one final_verification task.\n"
        "Every expected_evidence.file must be a relative artifact path under evidence/, such as evidence/t01-preflight.txt.\n"
        "Keep execution decisions static so the executor does not need to plan.\n\n"
        f"Context:\n{context}"
        f"{extra}"
    )


def summarize(output):
    tasks = output.get("tasks", {}).get("tasks", []) if isinstance(output.get("tasks"), dict) else []
    return {
        "task_count": len(tasks) if isinstance(tasks, list) else None,
    }
