ROLE = "closure_auditor"


def schema(*, option_schema, tracks, user_routes):
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {"type": "string", "enum": ["pass", "ask_user"]},
            "route": {"type": "string", "enum": sorted(user_routes)},
            "track": {"type": "string", "enum": list(tracks)},
            "question": {"type": "string"},
            "summary": {"type": "string"},
            "material_blockers": {"type": "array", "items": {"type": "string"}},
            "skip_eligible": {"type": "boolean"},
            "skip_kind": {"type": "string", "enum": ["defer", "decide_later"]},
            "options": {
                "type": "array",
                "minItems": 2,
                "maxItems": 3,
                "items": option_schema,
            },
        },
        "required": [
            "action",
            "route",
            "track",
            "question",
            "summary",
            "material_blockers",
            "skip_eligible",
            "skip_kind",
            "options",
        ],
    }


def prompt(*, context):
    return (
        "You are the coplan closure_auditor using Seed Closer criteria. Decide only whether the interview is ready for plan_seed extraction and bundle authoring. Return JSON only.\n"
        "A low ambiguity score is not sufficient. PASS only when no implementation-changing decision remains for ownership/source of truth, API/protocol, lifecycle/recovery, migration, cross-client impact, execution boundaries, or verification expectations.\n"
        "If any material decision remains, action=ask_user and ask exactly one highest-impact follow-up. Do not ask about planning mechanics, bundle files, reviewer setup, or validation process unless the user's task is specifically about those systems.\n"
        "Always populate options with 2-3 concise UI choices and exactly one recommended=true item. For action=ask_user, options must preserve the user's final judgment and allow free-form correction. For action=pass, use neutral fallback options.\n"
        "Set skip_eligible=false for material blockers. Use skip_eligible=true only when the item can be intentionally deferred without changing executor behavior.\n\n"
        f"Context:\n{context}"
    )


def summarize(output):
    return {key: output.get(key) for key in ("status", "action", "summary") if key in output}
