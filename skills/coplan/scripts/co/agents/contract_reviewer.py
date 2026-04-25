ROLE = "contract_reviewer"


def schema():
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {"type": "string", "enum": ["PASS", "FAIL"]},
            "summary": {"type": "string"},
            "issues": {"type": "array", "items": {"type": "string"}},
            "optional_tightenings": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["status", "summary", "issues", "optional_tightenings"],
    }


def prompt(*, context):
    return (
        "You are the contract_reviewer for a coplan bundle. Review whether tasks.yaml faithfully implements plan_seed.yaml. Block hidden decisions, scope drift, contradictions, task DAG assumptions, file scope problems, and acceptance criteria that ask execution to choose between materially different user-visible behaviors.\n"
        "Return JSON only with status PASS or FAIL. This is a post-author bundle review. Do not re-check mechanical schema fields owned by CLI validation unless the semantics are meaningless.\n\n"
        f"Context:\n{context}"
    )


def summarize(output):
    return {
        "status": output.get("status"),
        "issue_count": len(output.get("issues", [])) if isinstance(output.get("issues"), list) else None,
    }
