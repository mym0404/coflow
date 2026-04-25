ROLE = "verification_reviewer"


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
        "You are the verification_reviewer for a coplan bundle. Review whether verification commands, evidence, final verification, and success signals are minimally sufficient for plan_seed.yaml. Block if verification would not prove the user's intended behavior or if it asks the executor to invent proof policy.\n"
        "Return JSON only with status PASS or FAIL. This is a post-author bundle review. Do not re-check mechanical schema fields owned by CLI validation unless the semantics are meaningless.\n\n"
        f"Context:\n{context}"
    )


def summarize(output):
    return {
        "status": output.get("status"),
        "issue_count": len(output.get("issues", [])) if isinstance(output.get("issues"), list) else None,
    }
