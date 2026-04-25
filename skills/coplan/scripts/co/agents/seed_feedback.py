ROLE = "seed_feedback"


def schema(*, tracks):
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {"type": "string", "enum": ["approve", "wording_change", "meaning_change"]},
            "track": {"type": "string", "enum": list(tracks)},
            "question": {"type": "string"},
            "answer": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": ["action", "track", "question", "answer", "summary"],
    }


def prompt(*, plan_seed_json, feedback):
    return (
        "Classify this plan seed feedback for coflow. Return JSON only.\n"
        "approve means the user accepts the plan seed. wording_change means text-only polish. "
        "meaning_change means scope, output, verification, constraints, or stop conditions changed.\n\n"
        f"Plan seed:\n{plan_seed_json}\n\nFeedback:\n{feedback}"
    )


def summarize(output):
    return {
        "action": output.get("action"),
        "track": output.get("track"),
    }
