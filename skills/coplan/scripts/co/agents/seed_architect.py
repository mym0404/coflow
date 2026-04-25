ROLE = "seed_architect"


def schema():
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string"},
            "goal": {"type": "string"},
            "context": string_array,
            "non_goals": string_array,
            "constraints": string_array,
            "success_criteria": string_array,
            "verification_expectations": string_array,
            "execution_boundaries": string_array,
            "source_round_ids": string_array,
            "deferred_items": string_array,
            "summary": {"type": "string"},
        },
        "required": [
            "title",
            "goal",
            "context",
            "non_goals",
            "constraints",
            "success_criteria",
            "verification_expectations",
            "execution_boundaries",
            "source_round_ids",
            "deferred_items",
            "summary",
        ],
    }


def prompt(*, context):
    return (
        "You are the coplan seed_architect. Extract an internal plan seed from the original request, interview transcript, ambiguity ledger, closure audit, and deferred items. Return JSON only.\n"
        "The seed is the source of truth for bundle_author. It must capture the user's intended core change, constraints, success criteria, non-goals, context, verification expectations, and execution boundaries without inventing new decisions.\n"
        "Use the six tracks only as classification hints; do not require every track to have a transcript item. Preserve intentional deferrals as deferred_items only when they do not force executor planning.\n"
        "No TBD placeholders. If something material is missing, the closure audit should have failed earlier; extract the best settled contract from the transcript.\n\n"
        f"Context:\n{context}"
    )


def summarize(output):
    return {key: output.get(key) for key in ("status", "action", "summary") if key in output}
