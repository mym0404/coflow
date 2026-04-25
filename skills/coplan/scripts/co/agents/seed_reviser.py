ROLE = "seed_reviser"


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


def prompt(*, context, feedback):
    return (
        "You are the coplan seed_reviser. Rewrite plan_seed.yaml seed content for wording-only user feedback. Return JSON only using the same seed schema.\n"
        "Preserve the existing goal, constraints, non-goals, success criteria, execution boundaries, verification expectations, deferred items, and source_round_ids unless the wording can be clarified without changing meaning.\n"
        "If the feedback requires a semantic change, keep the existing seed meaning and summarize the limitation in wording; the CLI routes semantic feedback through interview instead.\n\n"
        f"Feedback:\n{feedback}\n\n"
        f"Context:\n{context}"
    )


def summarize(output):
    return {
        "action": output.get("action"),
        "track": output.get("track"),
    }
