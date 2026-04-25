ROLE = "ask-next"


def schema(*, option_schema, routes, tracks):
    source_ref = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "path": {"type": "string"},
            "line": {"type": "integer", "minimum": 1},
            "claim": {"type": "string"},
        },
        "required": ["path", "line", "claim"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {"type": "string", "enum": ["ask_user", "record_fact", "ready_for_score"]},
            "route": {"type": "string", "enum": sorted(routes)},
            "track": {"type": "string", "enum": list(tracks)},
            "question": {"type": "string"},
            "answer": {"type": "string"},
            "source": {"type": "string"},
            "source_refs": {"type": "array", "items": source_ref},
            "skip_eligible": {"type": "boolean"},
            "skip_kind": {"type": "string", "enum": ["defer", "decide_later"]},
            "options": {
                "type": "array",
                "minItems": 2,
                "maxItems": 3,
                "items": option_schema,
            },
            "reason": {"type": "string"},
        },
        "required": [
            "action",
            "route",
            "track",
            "question",
            "answer",
            "source",
            "source_refs",
            "skip_eligible",
            "skip_kind",
            "options",
            "reason",
        ],
    }


def prompt(*, context):
    return (
        "You are the coplan Socratic interviewer. Inspect the original request, transcript, ambiguity snapshot, and bundle context; choose the single next action that most reduces implementation-changing ambiguity.\n"
        "Return JSON only. Ask about the user's intent, core change, ownership, public behavior, or non-obvious tradeoff. Do not ask process questions about how to build a plan bundle, how to verify the planner, or how many agents to run unless that is the user's actual task.\n"
        "If user judgment is needed, action=ask_user with route user_decision or code_plus_decision. If a repo/research fact is enough and directly grounded in context, action=record_fact with route code_fact or research_confirmation. If at least three answered rounds exist and no material question remains, action=ready_for_score.\n"
        "For route=code_fact, source_refs must include at least one repo-root-relative path, 1-based line number, and concrete claim that grounds the answer. For other routes, source_refs may be empty.\n"
        "Use tracks only as extraction labels: scope, non_goals, outputs, verification, constraints, stop_conditions. Never force a checklist order across those tracks.\n"
        "Brownfield hint: prefer questions about the intended behavioral boundary, source of truth, API/protocol ownership, lifecycle/recovery, migration, or cross-client impact when those could change the implementation.\n"
        "Perspective panel: user-intent guardian asks what outcome changes; maintainer asks what existing behavior must survive; executor asks what static decision it would otherwise have to make; verifier asks what proof is minimally sufficient; Seed Closer asks which unresolved choice would invalidate the plan.\n"
        "Answer prefix guidance: ask concise questions that invite concrete answers like 'Change...', 'Preserve...', 'Exclude...', or 'Prove with...'.\n"
        "Always populate options with 2-3 concise UI choices and exactly one recommended=true item. For action=ask_user, options must not decide for the user; they should offer useful answer directions plus room for free-form correction. For other actions, use neutral fallback options.\n"
        "Set skip_eligible=true only for useful details that can be intentionally deferred without changing the plan contract; set skip_eligible=false for material implementation decisions. Use skip_kind=defer for optional detail and decide_later for explicit future decisions.\n\n"
        f"Context:\n{context}"
    )


def summarize(output):
    return {
        "action": output.get("action"),
        "route": output.get("route"),
        "track": output.get("track"),
    }
