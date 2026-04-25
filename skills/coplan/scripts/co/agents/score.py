ROLE = "score"


def schema(*, option_schema, tracks, user_routes):
    component = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "clarity_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "justification": {"type": "string"},
        },
        "required": ["clarity_score", "justification"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "project_mode": {"type": "string", "enum": ["greenfield", "brownfield"]},
            "components": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "goal_clarity": component,
                    "constraint_clarity": component,
                    "success_criteria_clarity": component,
                    "context_clarity": component,
                },
                "required": [
                    "goal_clarity",
                    "constraint_clarity",
                    "success_criteria_clarity",
                    "context_clarity",
                ],
            },
            "weakest_dimension": {"type": "string"},
            "recommended_followup": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "route": {"type": "string", "enum": sorted(user_routes)},
                    "track": {"type": "string", "enum": list(tracks)},
                    "question": {"type": "string"},
                    "options": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 3,
                        "items": option_schema,
                    },
                },
                "required": ["route", "track", "question", "options"],
            },
            "summary": {"type": "string"},
        },
        "required": ["project_mode", "components", "weakest_dimension", "recommended_followup", "summary"],
    }


def prompt(*, context, project_mode):
    return (
        "You are the coplan ambiguity scoring agent. Score requirement clarity from 0.0 to 1.0. Use low-variance judgment; scoring_temperature_intent is 0.1. Return JSON only.\n"
        "Score goal_clarity, constraint_clarity, success_criteria_clarity, and context_clarity. For greenfield, still provide context_clarity but it will not be weighted.\n"
        f"Requested project_mode: {project_mode}.\n"
        "Treat intentional deferrals in deferred_items as settled unless they would force the executor to choose behavior, ownership, migration, or verification policy. Set recommended_followup to the single best question for exposing a user-owned tradeoff or brownfield context gap before execution. For brownfield work with weak context_clarity, prefer a repository-specific code/docs/behavior boundary question.\n"
        "recommended_followup must include options with 2-3 concise UI choices and exactly one recommended=true item. Options must help the user answer, not make hidden planning decisions.\n"
        "Do not declare readiness in prose; the CLI will compute weighted clarity and ambiguity.\n\n"
        f"Context:\n{context}"
    )


def summarize(output):
    return {
        "project_mode": output.get("project_mode"),
        "weakest_dimension": output.get("weakest_dimension"),
    }
