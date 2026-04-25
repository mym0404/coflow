#!/usr/bin/env python3
import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PLAN_ROOT = Path(".agents/plan")
EXEC_FILE = PLAN_ROOT / "exec.yaml"
CLI_COMMAND_NAME = "co.py"
BOOTSTRAP_DIR = Path.home() / ".cache" / "codex-co"
BOOTSTRAP_VENV = BOOTSTRAP_DIR / "venv"
BOOTSTRAP_PYTHON = BOOTSTRAP_VENV / "bin" / "python"
VALID_PHASES = {
    "planning",
    "seed_review",
    "ready_for_exec",
    "executing",
    "halted",
    "complete",
}
TASK_STATES = {"Todo", "Doing", "Done"}
REVIEW_STATUSES = {"not_run", "passed", "failed"}
REVIEW_STAGES = {"bundle"}
REQUIRED_REVIEWERS = ("contract_reviewer", "verification_reviewer")
INTERVIEW_STATUSES = {"open", "closed"}
INTERVIEW_TRACK_STATUSES = {"open", "closed"}
SEED_REVIEW_STATUSES = {"not_presented", "presented", "approved"}
INTERVIEW_ROUTE_ORDER = (
    "code_fact",
    "user_decision",
    "code_plus_decision",
    "research_confirmation",
)
INTERVIEW_ROUTES = set(INTERVIEW_ROUTE_ORDER)
INTERVIEW_REQUIRED_TRACKS = (
    "scope",
    "non_goals",
    "outputs",
    "verification",
    "constraints",
    "stop_conditions",
)
INTERVIEW_REQUIRED_TRACK_SET = set(INTERVIEW_REQUIRED_TRACKS)
INTERVIEW_REQUIRED_USER_TRACKS = ()
INTERVIEW_NON_USER_ROUTES = {"code_fact", "research_confirmation"}
INTERVIEW_USER_ROUTES = {"user_decision", "code_plus_decision"}
INTERVIEW_NON_USER_STREAK_LIMIT = 3
INTERVIEW_TRACK_FOCUS_LIMIT = 3
INTERVIEW_MIN_TOTAL_ROUNDS = 3
INTERVIEW_MIN_USER_ROUNDS = 1
INTERVIEW_COMPLETION_CANDIDATE_STREAK_REQUIRED = 2
INTERVIEW_CLOSURE_AUDIT_STATUSES = {"not_run", "passed", "failed"}
INTERVIEW_SKIP_KINDS = {"defer", "decide_later"}
QUESTION_OPTION_LABEL_MAX = 40
QUESTION_OPTION_DESCRIPTION_MAX = 160
INTERVIEW_CLOSURE_CHECKS = (
    "desired_output_explicit",
    "user_tradeoffs_explicit",
    "closure_audit_passed",
    "executor_determinism",
    "verification_proves_behavior",
    "no_material_questions",
)
INTERVIEW_HIDDEN_ASSUMPTION_PURPOSE = "hidden_assumption_followup"
INTERVIEW_CLOSURE_AUDIT_PURPOSE = "closure_audit_followup"
INTERVIEW_QUESTION_PURPOSES = {
    INTERVIEW_HIDDEN_ASSUMPTION_PURPOSE,
    INTERVIEW_CLOSURE_AUDIT_PURPOSE,
}
INTERVIEW_CLOSURE_CHECK_SUMMARIES = {
    "desired_output_explicit": "Seed captures the intended output before task authoring.",
    "user_tradeoffs_explicit": "Material user-owned tradeoffs are settled or intentionally deferred.",
    "closure_audit_passed": "Seed Closer audit passed before bundle authoring.",
    "executor_determinism": "Executor inputs are deterministic enough for a static plan.",
    "verification_proves_behavior": "Verification expectations are explicit enough for executor proof.",
    "no_material_questions": "No material user question remains pending.",
}
INTERVIEW_SOURCE_PREFIXES = {
    "code_fact": ("from-code",),
    "research_confirmation": ("from-research",),
    "user_decision": ("from-user",),
    "code_plus_decision": ("from-user",),
}
AMBIGUITY_THRESHOLD = 0.2
AMBIGUITY_SCORING_TEMPERATURE_INTENT = 0.1
AMBIGUITY_WEIGHTS = {
    "greenfield": {
        "goal_clarity": 0.40,
        "constraint_clarity": 0.30,
        "success_criteria_clarity": 0.30,
    },
    "brownfield": {
        "goal_clarity": 0.35,
        "constraint_clarity": 0.25,
        "success_criteria_clarity": 0.25,
        "context_clarity": 0.15,
    },
}
AMBIGUITY_FLOORS = {
    "goal_clarity": 0.75,
    "constraint_clarity": 0.65,
    "success_criteria_clarity": 0.70,
    "context_clarity": 0.60,
}
CODEX_AGENT_DEFAULT_MODEL = "gpt-5.5"
CODEX_AGENT_DEFAULT_SANDBOX = "read-only"
CODEX_AGENT_REASONING_EFFORT = "medium"
CODEX_AGENT_DEFAULT_TIMEOUT_SECONDS = 600
CODEX_AGENT_CLI_NAME = "codex"
CODEX_AGENT_MAX_COFLOW_DEPTH = 5
CODEX_AGENT_DEPTH_ENV_KEY = "_COFLOW_CODEX_DEPTH"
CODEX_AGENT_DISABLE_FEATURES = ("plugins",)
CODEX_AGENT_STRIP_ENV_KEYS = {
    "OUROBOROS_AGENT_RUNTIME",
    "OUROBOROS_LLM_BACKEND",
    "CODEX_SESSION_ID",
    "CODEX_THREAD_ID",
    "CODEX_PARENT_AGENT_ID",
    "CODEX_EXECUTION_ID",
    "CLAUDECODE",
}
CODEX_AGENT_WRAPPER_MAGIC_HEADERS = (
    b"\xcf\xfa\xed\xfe",
    b"\xce\xfa\xed\xfe",
    b"\x7fELF",
)
NOTE_KINDS = {"discovery", "decision", "risk", "revision", "repair", "halt"}
CONTRACT_REPAIR_ROOTS = {"files", "implementation_notes", "verification"}
FLOW_CONTRACT_VERSION = "1"
FLOW_ROOT_ACTION_TYPES = {
    "ask_user",
    "present_plan_seed",
    "notify_plan_done",
    "execute_task",
    "repair_task",
    "report_halt",
    "report_complete",
    "report_error",
}
FLOW_LOG_FILE = "flow_log.ndjson"
CURRENT_FLOW_COMMAND = None


class ExError(Exception):
    pass


class GateError(ExError):
    def __init__(self, message, data, required_action, next_command=None):
        super().__init__(message)
        self.data = data
        self.required_action = required_action
        self.next_command = next_command


def require_yaml():
    try:
        import yaml  # type: ignore
    except Exception as exc:
        bootstrap_pyyaml(exc)
        raise ExError("PyYAML bootstrap did not restart co") from exc
    return yaml


def bootstrap_pyyaml(original_exc):
    if os.environ.get("EX_BOOTSTRAPPED") == "1":
        raise ExError(
            "PyYAML is required but bootstrap failed after re-exec. "
            f"Bootstrap python: {BOOTSTRAP_PYTHON}"
        ) from original_exc
    try:
        BOOTSTRAP_DIR.mkdir(parents=True, exist_ok=True)
        if BOOTSTRAP_PYTHON.exists() and python_can_import_yaml(BOOTSTRAP_PYTHON):
            reexec_with_bootstrap_python()
        if not BOOTSTRAP_PYTHON.exists():
            subprocess.run(
                [sys.executable, "-m", "venv", str(BOOTSTRAP_VENV)],
                check=True,
                text=True,
                capture_output=True,
            )
        subprocess.run(
            [str(BOOTSTRAP_PYTHON), "-m", "pip", "install", "--upgrade", "pip", "PyYAML"],
            check=True,
            text=True,
            capture_output=True,
        )
    except Exception as exc:
        raise ExError(
            f"PyYAML bootstrap failed. Bootstrap venv: {BOOTSTRAP_VENV}. "
            f"Original import error: {original_exc}"
        ) from exc
    reexec_with_bootstrap_python()


def reexec_with_bootstrap_python():
    env = os.environ.copy()
    env["EX_BOOTSTRAPPED"] = "1"
    os.execvpe(str(BOOTSTRAP_PYTHON), [str(BOOTSTRAP_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]], env)


def python_can_import_yaml(python):
    if not Path(python).exists():
        return False
    result = subprocess.run(
        [str(python), "-c", "import yaml; print(yaml.__version__)"],
        check=False,
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def read_stdin():
    return sys.stdin.read()


def load_yaml(path):
    yaml = require_yaml()
    if not path.exists():
        raise ExError(f"missing file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if data is not None else {}


def dump_yaml(data):
    yaml = require_yaml()
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = dump_yaml(data)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def print_yaml(data):
    sys.stdout.write(dump_yaml(data))


def result_with_required_action(data, required_action, next_command=None):
    result = {"ok": data.get("ok", True)}
    for key, value in data.items():
        if key != "ok":
            result[key] = value
    result["required_action"] = required_action
    if next_command:
        result["next_command"] = next_command
    return result


def dump_json(data):
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)


def hash_text(value):
    text = "" if value is None else str(value)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def flow_log_path(plan_dir):
    return plan_dir / FLOW_LOG_FILE


def next_flow_log_seq(plan_dir):
    path = flow_log_path(plan_dir)
    if not path.exists():
        return 1
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle) + 1
    except OSError:
        return 1


def active_plan_dir_or_none():
    try:
        data = load_yaml(EXEC_FILE)
        plan_dir = data.get("plan_dir")
        if not plan_dir:
            return None
        path = Path(str(plan_dir))
        return path if path.exists() else None
    except Exception:
        return None


def current_phase_or_none(plan_dir):
    try:
        status_path = plan_dir / "status.yaml"
        if not status_path.exists():
            return None
        return load_yaml(status_path).get("phase")
    except Exception:
        return None


def json_safe(value):
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def append_flow_log(plan_dir, event, **fields):
    if not plan_dir:
        return
    try:
        plan_dir = Path(plan_dir)
        plan_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "seq": next_flow_log_seq(plan_dir),
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event": event,
            "plan_id": plan_dir.name,
            "phase": current_phase_or_none(plan_dir),
        }
        entry.update({key: json_safe(value) for key, value in fields.items() if value is not None})
        with flow_log_path(plan_dir).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception:
        return


def summarize_codex_output(role, output):
    if not isinstance(output, dict):
        return {"type": type(output).__name__}
    if role == "score":
        return {
            "project_mode": output.get("project_mode"),
            "weakest_dimension": output.get("weakest_dimension"),
        }
    if role == "ask-next":
        return {
            "action": output.get("action"),
            "route": output.get("route"),
            "track": output.get("track"),
        }
    if role == "bundle_author":
        tasks = output.get("tasks", {}).get("tasks", []) if isinstance(output.get("tasks"), dict) else []
        return {
            "task_count": len(tasks) if isinstance(tasks, list) else None,
        }
    if role in {"seed_feedback", "seed_reviser"}:
        return {
            "action": output.get("action"),
            "track": output.get("track"),
        }
    if role in REQUIRED_REVIEWERS:
        return {
            "status": output.get("status"),
            "issue_count": len(output.get("issues", [])) if isinstance(output.get("issues"), list) else None,
        }
    return {key: output.get(key) for key in ("status", "action", "summary") if key in output}


def flow_command_name(args):
    command = getattr(args, "command", None)
    if command != "flow":
        return None
    flow_command = getattr(args, "flow_command", None)
    return f"flow {flow_command}" if flow_command else "flow"


def log_flow_command_start(plan_dir, command, **fields):
    data = {
        "command": command,
        "phase_before": current_phase_or_none(plan_dir),
    }
    data.update(fields)
    append_flow_log(
        plan_dir,
        "flow.command.start",
        **data,
    )


def log_flow_command_error(message):
    plan_dir = active_plan_dir_or_none()
    append_flow_log(
        plan_dir,
        "flow.command.error",
        command=CURRENT_FLOW_COMMAND,
        ok=False,
        error=str(message),
        phase_after=current_phase_or_none(plan_dir) if plan_dir else None,
    )


def is_codex_wrapper_binary(path):
    try:
        with open(path, "rb") as handle:
            return handle.read(4) in CODEX_AGENT_WRAPPER_MAGIC_HEADERS
    except OSError:
        return False


def find_real_codex_cli(skip):
    skip_path = Path(skip).resolve()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / CODEX_AGENT_CLI_NAME
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            continue
        if candidate.resolve() == skip_path:
            continue
        if is_codex_wrapper_binary(candidate):
            continue
        return str(candidate)
    return None


def resolve_codex_cli_path():
    candidate = shutil.which(CODEX_AGENT_CLI_NAME) or CODEX_AGENT_CLI_NAME
    path = Path(candidate).expanduser()
    if not path.exists() or not is_codex_wrapper_binary(path):
        return str(path) if path.exists() else candidate
    return find_real_codex_cli(path) or str(path)


def build_codex_child_env(base_env=None):
    env = dict(os.environ if base_env is None else base_env)
    for key in CODEX_AGENT_STRIP_ENV_KEYS:
        env.pop(key, None)
    for key in list(env):
        if "MCP" in key or "RMCP" in key:
            env.pop(key, None)
    try:
        depth = int(env.get(CODEX_AGENT_DEPTH_ENV_KEY, "0")) + 1
    except (TypeError, ValueError):
        depth = 1
    if depth > CODEX_AGENT_MAX_COFLOW_DEPTH:
        raise ExError(f"maximum coflow Codex subagent depth exceeded: {CODEX_AGENT_MAX_COFLOW_DEPTH}")
    env[CODEX_AGENT_DEPTH_ENV_KEY] = str(depth)
    return env


def write_output_schema_tempfile(schema):
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
    try:
        json.dump(schema, handle, ensure_ascii=False)
        handle.flush()
        return Path(handle.name)
    finally:
        handle.close()


def build_codex_exec_command(
    *,
    output_last_message_path,
    output_schema_path=None,
    cwd=None,
    model=CODEX_AGENT_DEFAULT_MODEL,
    sandbox=CODEX_AGENT_DEFAULT_SANDBOX,
):
    command = [
        resolve_codex_cli_path(),
        "exec",
        "--json",
        "--skip-git-repo-check",
        "--ephemeral",
        "-c",
        f'model_reasoning_effort="{CODEX_AGENT_REASONING_EFFORT}"',
        "--sandbox",
        sandbox,
        "-C",
        str(cwd or Path.cwd()),
        "--output-last-message",
        str(output_last_message_path),
    ]
    for feature in CODEX_AGENT_DISABLE_FEATURES:
        command.extend(["--disable", feature])
    if output_schema_path:
        command.extend(["--output-schema", str(output_schema_path)])
    if model:
        command.extend(["--model", model])
    command.append("-")
    return command


def read_last_message_json(path):
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        raise ExError("codex exec produced an empty last message")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    raise ExError("codex exec last message is not JSON")


def run_codex_agent(role, prompt, schema, *, cwd=None, plan_dir=None):
    output_handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False)
    output_path = Path(output_handle.name)
    output_handle.close()
    schema_path = write_output_schema_tempfile(schema)
    command = build_codex_exec_command(
        output_last_message_path=output_path,
        output_schema_path=schema_path,
        cwd=cwd,
    )
    start = datetime.now(timezone.utc)
    append_flow_log(
        plan_dir,
        "codex_agent.start",
        role=role,
        prompt_hash=hash_text(prompt),
        prompt_bytes=len(prompt.encode("utf-8")),
    )
    logged_end = False
    try:
        process = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            cwd=str(cwd or Path.cwd()),
            env=build_codex_child_env(),
            timeout=CODEX_AGENT_DEFAULT_TIMEOUT_SECONDS,
        )
        if process.returncode != 0:
            stderr = process.stderr.strip()
            stdout = process.stdout.strip()
            detail = stderr or stdout or f"exit code {process.returncode}"
            append_flow_log(
                plan_dir,
                "codex_agent.end",
                role=role,
                status="failed",
                duration_ms=int((datetime.now(timezone.utc) - start).total_seconds() * 1000),
                error_hash=hash_text(detail),
            )
            logged_end = True
            raise ExError(f"codex agent {role} failed: {detail}")
        output = read_last_message_json(output_path)
        if not isinstance(output, dict):
            append_flow_log(
                plan_dir,
                "codex_agent.end",
                role=role,
                status="failed",
                duration_ms=int((datetime.now(timezone.utc) - start).total_seconds() * 1000),
                error_hash=hash_text("output must be a JSON object"),
            )
            logged_end = True
            raise ExError(f"codex agent {role} output must be a JSON object")
        append_flow_log(
            plan_dir,
            "codex_agent.end",
            role=role,
            status="passed",
            duration_ms=int((datetime.now(timezone.utc) - start).total_seconds() * 1000),
            output_summary=summarize_codex_output(role, output),
        )
        logged_end = True
        return {
            "role": role,
            "model": CODEX_AGENT_DEFAULT_MODEL,
            "sandbox": CODEX_AGENT_DEFAULT_SANDBOX,
            "model_reasoning_effort": CODEX_AGENT_REASONING_EFFORT,
            "command": command,
            "output": output,
            "stdout_tail": process.stdout.strip().splitlines()[-20:],
        }
    except Exception as exc:
        if not logged_end:
            append_flow_log(
                plan_dir,
                "codex_agent.end",
                role=role,
                status="failed",
                duration_ms=int((datetime.now(timezone.utc) - start).total_seconds() * 1000),
                error_hash=hash_text(str(exc)),
            )
        raise
    finally:
        output_path.unlink(missing_ok=True)
        schema_path.unlink(missing_ok=True)


def run_codex_agents_parallel(agent_specs, *, cwd=None, plan_dir=None):
    if not agent_specs:
        return {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(agent_specs)) as executor:
        future_to_role = {
            executor.submit(
                run_codex_agent,
                spec["role"],
                spec["prompt"],
                spec["schema"],
                cwd=cwd,
                plan_dir=plan_dir,
            ): spec["role"]
            for spec in agent_specs
        }
        return {
            future_to_role[future]: future.result()
            for future in concurrent.futures.as_completed(future_to_role)
        }


def parse_yaml_value(text):
    yaml = require_yaml()
    try:
        return yaml.safe_load(text)
    except Exception as exc:
        raise ExError(f"value is not valid YAML: {exc}") from exc


def normalize_bool(value):
    if isinstance(value, bool):
        return value
    lowered = str(value).lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ExError("expected true or false")


def active_plan():
    data = load_yaml(EXEC_FILE)
    plan_id = data.get("active_plan_id")
    plan_dir = data.get("plan_dir")
    if not plan_id or not plan_dir:
        raise ExError(".agents/plan/exec.yaml is missing active_plan_id or plan_dir")
    return str(plan_id), Path(str(plan_dir))


def read_text_file(path):
    try:
        return path.read_text()
    except FileNotFoundError as exc:
        raise ExError(f"missing file: {path}") from exc


def next_id(items, prefix):
    max_seen = 0
    for item in items:
        raw = str(item.get("id", ""))
        if raw.startswith(prefix):
            suffix = raw[len(prefix) :]
            if suffix.isdigit():
                max_seen = max(max_seen, int(suffix))
    return f"{prefix}{max_seen + 1}"


def append_note(plan_dir, kind, text, why, affects, source):
    if kind not in NOTE_KINDS:
        raise ExError(f"unknown note kind: {kind}")
    path = plan_dir / "notes.yaml"
    data = load_yaml(path)
    entries = data.setdefault("entries", [])
    entry = {
        "id": next_id(entries, "N"),
        "kind": kind,
        "text": text,
        "why": why,
        "affects": affects,
        "source": source,
    }
    entries.append(entry)
    write_yaml(path, data)
    return entry


def notes_entries(notes):
    entries = notes.get("entries", [])
    if not isinstance(entries, list):
        raise ExError("notes.yaml entries must be a list")
    return entries


def filter_notes(entries, kind=None, task_id=None):
    filtered = entries
    if kind:
        filtered = [entry for entry in filtered if entry.get("kind") == kind]
    if task_id:
        task_key = f"task:{task_id}"
        filtered = [
            entry
            for entry in filtered
            if task_key in (entry.get("affects") or [])
        ]
    return filtered


def limit_notes(entries, limit):
    if limit is None:
        return entries
    if limit <= 0:
        raise ExError("--limit must be greater than 0")
    return entries[-limit:]


def exec_notes_view(bundle, current_id):
    entries = notes_entries(bundle["notes"])
    return {
        "recent": limit_notes(entries, 5),
        "current_task": filter_notes(entries, task_id=current_id) if current_id else [],
    }


def load_bundle():
    plan_id, plan_dir = active_plan()
    plan_seed_path = plan_dir / "plan_seed.yaml"
    return {
        "plan_id": plan_id,
        "plan_dir": plan_dir,
        "tasks": load_yaml(plan_dir / "tasks.yaml"),
        "plan_seed": load_yaml(plan_seed_path) if plan_seed_path.exists() else None,
        "interview": load_yaml(plan_dir / "interview.yaml"),
        "status": load_yaml(plan_dir / "status.yaml"),
        "notes": load_yaml(plan_dir / "notes.yaml"),
        "evidence": load_yaml(plan_dir / "evidence.yaml"),
    }


def task_list(bundle):
    tasks = bundle["tasks"].get("tasks", [])
    if not isinstance(tasks, list):
        raise ExError("tasks.yaml must contain tasks: []")
    return tasks


def task_map(bundle):
    result = {}
    for task in task_list(bundle):
        task_id = task.get("id")
        if not task_id:
            raise ExError("each task must have id")
        if task_id in result:
            raise ExError(f"duplicate task id: {task_id}")
        result[task_id] = task
    return result


def task_status(bundle):
    status_tasks = bundle["status"].get("tasks", {})
    if not isinstance(status_tasks, dict):
        raise ExError("status.yaml tasks must be a mapping")
    return status_tasks


def evidence_records(bundle):
    records = bundle["evidence"].get("records", [])
    if not isinstance(records, list):
        raise ExError("evidence.yaml records must be a list")
    return records


def validate_plan_id(plan_id):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", plan_id):
        raise ExError("plan-id must be stable kebab-case")


def default_closure_audit():
    return {
        "status": "not_run",
        "summary": "",
        "material_blockers": [],
        "question": "",
        "round_count": 0,
        "score_id": None,
    }


def default_interview(initial_context=""):
    return {
        "status": "open",
        "initial_context": initial_context,
        "non_user_answer_streak": 0,
        "required_tracks": {
            track: {"status": "open", "summary": ""}
            for track in INTERVIEW_REQUIRED_TRACKS
        },
        "rounds": [],
        "pending_user_question": None,
        "agent_runs": [],
        "ambiguity": {"latest": None, "history": []},
        "ambiguity_ledger": [],
        "completion_candidate_streak": 0,
        "closure_audit": default_closure_audit(),
        "deferred_items": [],
        "seed_review": {
            "status": "not_presented",
            "fingerprint": None,
            "comment": "",
            "feedback": [],
        },
        "closure": {
            "ready": False,
            "summary": "",
            "material_blockers": [],
            "checks": {
                check: {"passed": False, "summary": ""}
                for check in INTERVIEW_CLOSURE_CHECKS
            },
        },
    }


def validate_interview(data):
    data.setdefault("initial_context", "")
    data.setdefault("ambiguity_ledger", [])
    data.setdefault("completion_candidate_streak", 0)
    data.setdefault("closure_audit", default_closure_audit())
    data.setdefault("deferred_items", [])
    data.setdefault(
        "seed_review",
        {"status": "not_presented", "fingerprint": None, "comment": "", "feedback": []},
    )
    require_fields(
        data,
        [
            "status",
            "initial_context",
            "non_user_answer_streak",
            "required_tracks",
            "rounds",
            "pending_user_question",
            "agent_runs",
            "ambiguity",
            "ambiguity_ledger",
            "completion_candidate_streak",
            "closure_audit",
            "deferred_items",
            "seed_review",
            "closure",
        ],
        "interview.yaml",
    )
    if data["status"] not in INTERVIEW_STATUSES:
        raise ExError("interview.yaml status must be open or closed")
    if not isinstance(data["initial_context"], str):
        raise ExError("interview.yaml initial_context must be a string")
    if not isinstance(data["non_user_answer_streak"], int) or data["non_user_answer_streak"] < 0:
        raise ExError("interview.yaml non_user_answer_streak must be a non-negative integer")
    tracks = data["required_tracks"]
    if not isinstance(tracks, dict):
        raise ExError("interview.yaml required_tracks must be a mapping")
    missing_tracks = sorted(INTERVIEW_REQUIRED_TRACK_SET - set(tracks.keys()))
    if missing_tracks:
        raise ExError("interview.yaml missing required tracks: " + ", ".join(missing_tracks))
    for track_name in INTERVIEW_REQUIRED_TRACKS:
        track = tracks[track_name]
        if not isinstance(track, dict):
            raise ExError(f"interview track {track_name} must be a mapping")
        require_fields(track, ["status", "summary"], f"interview track {track_name}")
        if track["status"] not in INTERVIEW_TRACK_STATUSES:
            raise ExError(f"interview track {track_name} status must be open or closed")
        if not isinstance(track["summary"], str):
            raise ExError(f"interview track {track_name} summary must be a string")
    rounds = data["rounds"]
    if not isinstance(rounds, list):
        raise ExError("interview.yaml rounds must be a list")
    for round_item in rounds:
        if not isinstance(round_item, dict):
            raise ExError("interview.yaml rounds must contain mappings")
        require_fields(round_item, ["id", "route", "track", "question", "answer", "source"], "interview round")
        if round_item["route"] not in INTERVIEW_ROUTES:
            raise ExError(f"interview round {round_item['id']} has invalid route")
        if round_item["track"] not in INTERVIEW_REQUIRED_TRACK_SET:
            raise ExError(f"interview round {round_item['id']} has invalid track")
        purpose = round_item.get("purpose")
        if purpose is not None and purpose not in INTERVIEW_QUESTION_PURPOSES:
            raise ExError(f"interview round {round_item['id']} has invalid purpose")
        source = str(round_item.get("source", "")).lower()
        source_prefixes = INTERVIEW_SOURCE_PREFIXES[round_item["route"]]
        if not any(source.startswith(prefix) for prefix in source_prefixes):
            raise ExError(
                f"interview round {round_item['id']} source must match route {round_item['route']}"
            )
    pending = data["pending_user_question"]
    if pending is not None:
        if not isinstance(pending, dict):
            raise ExError("interview.yaml pending_user_question must be null or a mapping")
        require_fields(pending, ["id", "route", "track", "question", "options"], "pending_user_question")
        if pending["route"] not in INTERVIEW_USER_ROUTES:
            raise ExError("pending_user_question route must require user judgment")
        if pending["track"] not in INTERVIEW_REQUIRED_TRACK_SET:
            raise ExError("pending_user_question track is invalid")
        purpose = pending.get("purpose")
        if purpose is not None and purpose not in INTERVIEW_QUESTION_PURPOSES:
            raise ExError("pending_user_question purpose is invalid")
        skip_eligible = pending.get("skip_eligible", False)
        if not isinstance(skip_eligible, bool):
            raise ExError("pending_user_question skip_eligible must be true or false")
        skip_kind = pending.get("skip_kind")
        if skip_kind is not None and skip_kind not in INTERVIEW_SKIP_KINDS:
            raise ExError("pending_user_question skip_kind is invalid")
        options = pending.get("options", [])
        validate_question_options(options, "pending_user_question options")
    if not isinstance(data["agent_runs"], list):
        raise ExError("interview.yaml agent_runs must be a list")
    if not isinstance(data["ambiguity_ledger"], list):
        raise ExError("interview.yaml ambiguity_ledger must be a list")
    if (
        not isinstance(data["completion_candidate_streak"], int)
        or data["completion_candidate_streak"] < 0
    ):
        raise ExError("interview.yaml completion_candidate_streak must be a non-negative integer")
    if not isinstance(data["deferred_items"], list):
        raise ExError("interview.yaml deferred_items must be a list")
    seed_review = data["seed_review"]
    if not isinstance(seed_review, dict):
        raise ExError("interview.yaml seed_review must be a mapping")
    require_fields(seed_review, ["status", "fingerprint", "comment", "feedback"], "interview.yaml seed_review")
    if seed_review["status"] not in SEED_REVIEW_STATUSES:
        raise ExError("interview.yaml seed_review.status is invalid")
    if seed_review["fingerprint"] is not None and not isinstance(seed_review["fingerprint"], str):
        raise ExError("interview.yaml seed_review.fingerprint must be a string or null")
    if not isinstance(seed_review["comment"], str):
        raise ExError("interview.yaml seed_review.comment must be a string")
    if not isinstance(seed_review["feedback"], list):
        raise ExError("interview.yaml seed_review.feedback must be a list")
    ambiguity = data["ambiguity"]
    if not isinstance(ambiguity, dict):
        raise ExError("interview.yaml ambiguity must be a mapping")
    require_fields(ambiguity, ["latest", "history"], "interview.yaml ambiguity")
    if ambiguity["latest"] is not None and not isinstance(ambiguity["latest"], dict):
        raise ExError("interview.yaml ambiguity.latest must be null or a mapping")
    if not isinstance(ambiguity["history"], list):
        raise ExError("interview.yaml ambiguity.history must be a list")
    audit = data["closure_audit"]
    if not isinstance(audit, dict):
        raise ExError("interview.yaml closure_audit must be a mapping")
    require_fields(
        audit,
        ["status", "summary", "material_blockers", "question", "round_count", "score_id"],
        "interview.yaml closure_audit",
    )
    if audit["status"] not in INTERVIEW_CLOSURE_AUDIT_STATUSES:
        raise ExError("interview.yaml closure_audit.status is invalid")
    if not isinstance(audit["summary"], str):
        raise ExError("interview.yaml closure_audit.summary must be a string")
    if not isinstance(audit["material_blockers"], list):
        raise ExError("interview.yaml closure_audit.material_blockers must be a list")
    if not isinstance(audit["question"], str):
        raise ExError("interview.yaml closure_audit.question must be a string")
    if not isinstance(audit["round_count"], int) or audit["round_count"] < 0:
        raise ExError("interview.yaml closure_audit.round_count must be a non-negative integer")
    if audit["score_id"] is not None and not isinstance(audit["score_id"], str):
        raise ExError("interview.yaml closure_audit.score_id must be a string or null")
    closure = data["closure"]
    if not isinstance(closure, dict):
        raise ExError("interview.yaml closure must be a mapping")
    require_fields(closure, ["ready", "summary", "material_blockers", "checks"], "interview.yaml closure")
    if not isinstance(closure["ready"], bool):
        raise ExError("interview.yaml closure.ready must be true or false")
    if not isinstance(closure["summary"], str):
        raise ExError("interview.yaml closure.summary must be a string")
    if not isinstance(closure["material_blockers"], list):
        raise ExError("interview.yaml closure.material_blockers must be a list")
    checks = closure["checks"]
    if not isinstance(checks, dict):
        raise ExError("interview.yaml closure.checks must be a mapping")
    for check_name in INTERVIEW_CLOSURE_CHECKS:
        checks.setdefault(check_name, {"passed": False, "summary": ""})
    missing_checks = sorted(set(INTERVIEW_CLOSURE_CHECKS) - set(checks.keys()))
    if missing_checks:
        raise ExError("interview.yaml closure.checks missing: " + ", ".join(missing_checks))
    for check_name in INTERVIEW_CLOSURE_CHECKS:
        check = checks[check_name]
        if not isinstance(check, dict):
            raise ExError(f"interview closure check {check_name} must be a mapping")
        require_fields(check, ["passed", "summary"], f"interview closure check {check_name}")
        if not isinstance(check["passed"], bool):
            raise ExError(f"interview closure check {check_name}.passed must be true or false")
        if not isinstance(check["summary"], str):
            raise ExError(f"interview closure check {check_name}.summary must be a string")


def interview_open_tracks(interview):
    tracks = interview.get("required_tracks", {})
    return [
        name
        for name in INTERVIEW_REQUIRED_TRACKS
        if tracks.get(name, {}).get("status") != "closed"
    ]


def interview_user_round_count(interview):
    return sum(1 for item in interview.get("rounds", []) if item.get("route") in INTERVIEW_USER_ROUTES)


def interview_answered_round_count(interview):
    return len(interview.get("rounds", []))


def interview_round_tracks(interview):
    tracks = {track: 0 for track in INTERVIEW_REQUIRED_TRACKS}
    user_tracks = {track: 0 for track in INTERVIEW_REQUIRED_TRACKS}
    for item in interview.get("rounds", []):
        track = item.get("track")
        if track not in tracks:
            continue
        tracks[track] += 1
        if item.get("route") in INTERVIEW_USER_ROUTES:
            user_tracks[track] += 1
    return tracks, user_tracks


def hidden_assumption_followup(latest):
    followup = latest.get("recommended_followup") if isinstance(latest, dict) else None
    if isinstance(followup, dict):
        route = followup.get("route")
        track = followup.get("track")
        question = str(followup.get("question", "")).strip()
        if route in INTERVIEW_USER_ROUTES and track in INTERVIEW_REQUIRED_TRACK_SET and question:
            return {
                "route": route,
                "track": track,
                "question": question,
                "options": followup.get("options") or question_options_for_kind(None),
            }
    return {
        "route": "user_decision",
        "track": "constraints",
        "question": (
            "Before finalizing this plan, what implementation-changing assumption "
            "about the existing codebase, docs, or product behavior should be settled?"
        ),
        "options": question_options_for_kind(None),
    }


def is_deferred_answer(answer):
    normalized = str(answer).strip().lower()
    if normalized.startswith("intentional deferral"):
        return True
    if normalized in {"skip", "defer", "deferred", "decide later", "later", "unknown"}:
        return True
    return any(token in normalized for token in ["보류", "나중", "몰라", "모름"])


def interview_closure_blockers(interview):
    rounds = interview.get("rounds", [])
    blockers = []
    if len(rounds) < INTERVIEW_MIN_TOTAL_ROUNDS:
        blockers.append(f"total_rounds<{INTERVIEW_MIN_TOTAL_ROUNDS}")
    user_rounds = interview_user_round_count(interview)
    if user_rounds < INTERVIEW_MIN_USER_ROUNDS:
        blockers.append(f"user_judgment_rounds<{INTERVIEW_MIN_USER_ROUNDS}")
    if interview.get("non_user_answer_streak", 0) >= INTERVIEW_NON_USER_STREAK_LIMIT:
        blockers.append("non_user_answer_streak_requires_user_judgment")
    if interview.get("completion_candidate_streak", 0) < INTERVIEW_COMPLETION_CANDIDATE_STREAK_REQUIRED:
        blockers.append(
            "completion_candidate_streak"
            f"<{INTERVIEW_COMPLETION_CANDIDATE_STREAK_REQUIRED}"
        )
    audit = interview.get("closure_audit", {})
    latest = interview.get("ambiguity", {}).get("latest") or {}
    if audit.get("status") != "passed":
        blockers.append("closure_audit_not_passed")
    elif audit.get("round_count") != len(rounds) or audit.get("score_id") != latest.get("id"):
        blockers.append("closure_audit_stale")
    missing_checks = [
        check
        for check, state in interview.get("closure", {}).get("checks", {}).items()
        if state.get("passed") is not True
    ]
    if missing_checks:
        blockers.append("missing_closure_checks=" + ",".join(missing_checks))
    blockers.extend(interview_ambiguity_blockers(interview))
    return blockers


def interview_ambiguity_blockers(interview):
    latest = interview.get("ambiguity", {}).get("latest")
    if not isinstance(latest, dict):
        return ["missing_ambiguity_score"]
    blockers = []
    if interview_answered_round_count(interview) < INTERVIEW_MIN_TOTAL_ROUNDS:
        blockers.append(f"total_rounds<{INTERVIEW_MIN_TOTAL_ROUNDS}")
    if latest.get("round_count") != len(interview.get("rounds", [])):
        blockers.append("ambiguity_score_stale")
    score = latest.get("ambiguity")
    if not isinstance(score, (int, float)):
        blockers.append("ambiguity_score_missing")
    elif score > AMBIGUITY_THRESHOLD:
        blockers.append(f"ambiguity>{AMBIGUITY_THRESHOLD}")
    floor_failures = latest.get("floor_failures", [])
    if floor_failures:
        blockers.append("clarity_floors_failed=" + ",".join(str(item) for item in floor_failures))
    if latest.get("ready") is not True:
        blockers.append("ambiguity_ready=false")
    return blockers


def interview_focus_blocker(interview, next_track):
    rounds = interview.get("rounds", [])
    if len(rounds) < INTERVIEW_TRACK_FOCUS_LIMIT - 1:
        return None
    recent_tracks = [item.get("track") for item in rounds[-(INTERVIEW_TRACK_FOCUS_LIMIT - 1):]]
    if any(track != next_track for track in recent_tracks):
        return None
    other_open_tracks = [
        track
        for track in interview_open_tracks(interview)
        if track != next_track
    ]
    if not other_open_tracks:
        return None
    return (
        f"track_focus_limit: ask a zoom-out question for one of "
        f"{','.join(other_open_tracks)} before another {next_track} round"
    )


def interview_seed_ready(interview):
    validate_interview(interview)
    return (
        interview.get("status") == "closed"
        and interview.get("closure", {}).get("ready") is True
        and not interview_open_tracks(interview)
        and not interview_closure_blockers(interview)
        and not interview.get("closure", {}).get("material_blockers")
    )


def require_interview_closed(plan_dir, action):
    interview = load_yaml(plan_dir / "interview.yaml")
    if not interview_seed_ready(interview):
        open_tracks = interview_open_tracks(interview)
        blockers = interview.get("closure", {}).get("material_blockers", [])
        details = []
        if open_tracks:
            details.append("open_tracks=" + ",".join(open_tracks))
        if blockers:
            details.append("material_blockers=" + ",".join(str(item) for item in blockers))
        if interview.get("status") != "closed":
            details.append("status=" + str(interview.get("status")))
        if interview.get("closure", {}).get("ready") is not True:
            details.append("closure.ready=false")
        suffix = "; ".join(details) if details else "interview is not closed"
        raise ExError(f"{action} requires closed interview: {suffix}")


def validate_tasks(data):
    require_fields(data, ["tasks"], "tasks.yaml")
    if not isinstance(data["tasks"], list):
        raise ExError("tasks.yaml tasks must be a list")
    task_items = data["tasks"]
    task_ids = {task.get("id") for task in task_items if isinstance(task, dict)}
    ids = set()
    graph = {}
    final_count = 0
    for task in task_items:
        if not isinstance(task, dict):
            raise ExError("each task must be a mapping")
        required = [
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
        ]
        require_fields(task, required, f"task {task.get('id', '<missing>')}")
        if "status" in task:
            raise ExError(f"task {task['id']} must not contain status")
        if task["id"] in ids:
            raise ExError(f"duplicate task id: {task['id']}")
        for string_field in ["id", "title", "context"]:
            if not isinstance(task[string_field], str) or not task[string_field].strip():
                raise ExError(f"task {task['id']} {string_field} must be a non-empty string")
        ids.add(task["id"])
        if task["kind"] not in {"execution", "checkpoint", "final_verification"}:
            raise ExError(f"task {task['id']} has invalid kind")
        if task["kind"] == "final_verification":
            final_count += 1
        depends_on = task["depends_on"]
        if not isinstance(depends_on, list):
            raise ExError(f"task {task['id']} depends_on must be a list")
        graph[task["id"]] = depends_on
        start_when = task["start_when"]
        if not isinstance(start_when, dict):
            raise ExError(f"task {task['id']} start_when must be a mapping")
        require_fields(start_when, ["description"], f"task {task['id']} start_when")
        if not isinstance(start_when["description"], str) or not start_when["description"].strip():
            raise ExError(f"task {task['id']} start_when.description must be a non-empty string")
        files = task["files"]
        if not isinstance(files, dict):
            raise ExError(f"task {task['id']} files must be a mapping")
        require_fields(files, ["primary", "generated_incidental"], f"task {task['id']} files")
        if not isinstance(files["primary"], list):
            raise ExError(f"task {task['id']} files.primary must be a list")
        if not isinstance(files["generated_incidental"], list):
            raise ExError(f"task {task['id']} files.generated_incidental must be a list")
        for list_field in ["must_do", "must_not_do", "implementation_notes", "acceptance_criteria", "expected_evidence", "reopen_when"]:
            if not isinstance(task[list_field], list):
                raise ExError(f"task {task['id']} {list_field} must be a list")
        for list_field in ["must_do", "acceptance_criteria"]:
            if not task[list_field]:
                raise ExError(f"task {task['id']} {list_field} must not be empty")
            if any(not isinstance(item, str) or not item.strip() for item in task[list_field]):
                raise ExError(f"task {task['id']} {list_field} items must be non-empty strings")
        verification = task["verification"]
        if not isinstance(verification, dict):
            raise ExError(f"task {task['id']} verification must be a mapping")
        require_fields(verification, ["evidence_required", "steps"], f"task {task['id']} verification")
        if not isinstance(verification["evidence_required"], bool):
            raise ExError(f"task {task['id']} verification.evidence_required must be true or false")
        if not isinstance(verification["steps"], list):
            raise ExError(f"task {task['id']} verification.steps must be a list")
        if not verification["steps"]:
            raise ExError(f"task {task['id']} verification.steps must not be empty")
        if verification["evidence_required"] and not task["expected_evidence"]:
            raise ExError(f"task {task['id']} expected_evidence must not be empty when evidence is required")
        step_ids = set()
        for step in verification["steps"]:
            if not isinstance(step, dict):
                raise ExError(f"task {task['id']} verification step must be a mapping")
            require_fields(step, ["id", "command", "success_signal"], f"task {task['id']} verification step")
            for step_field in ["id", "command", "success_signal"]:
                if not isinstance(step[step_field], str) or not step[step_field].strip():
                    raise ExError(f"task {task['id']} verification step {step_field} must be a non-empty string")
            if step["id"] in step_ids:
                raise ExError(f"task {task['id']} has duplicate step id: {step['id']}")
            step_ids.add(step["id"])
        for expected in task.get("expected_evidence", []):
            if not isinstance(expected, dict):
                raise ExError(f"task {task['id']} expected_evidence must contain mappings")
            require_fields(expected, ["step_id", "file"], f"task {task['id']} expected_evidence")
            if expected["step_id"] not in step_ids:
                raise ExError(f"task {task['id']} expected_evidence references unknown step: {expected['step_id']}")
            validate_expected_evidence_path(expected["file"], f"task {task['id']} expected_evidence")
        for dep in task["depends_on"]:
            if dep == task["id"]:
                raise ExError(f"task {task['id']} must not depend on itself")
            if dep not in ids and dep not in task_ids:
                raise ExError(f"task {task['id']} depends on unknown task: {dep}")
    if data["tasks"] and final_count == 0:
        raise ExError("tasks.yaml must contain at least one final_verification task")
    validate_task_graph_acyclic(graph)


def validate_expected_evidence_path(value, label):
    if not isinstance(value, str):
        raise ExError(f"{label} file must be a string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ExError(f"{label} file must be a relative path under evidence/")
    if not value.startswith("evidence/") or value == "evidence/":
        raise ExError(f"{label} file must be under evidence/")


def bundle_validation_feedback(exc):
    return (
        "The authored bundle failed local validation before review. "
        f"Fix this exact validation error and return a complete corrected bundle: {exc}"
    )


def validate_task_graph_acyclic(graph):
    visiting = set()
    visited = set()

    def visit(task_id, trail):
        if task_id in visiting:
            cycle = " -> ".join([*trail, task_id])
            raise ExError(f"task dependency cycle detected: {cycle}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dep in graph.get(task_id, []):
            visit(dep, [*trail, task_id])
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in graph:
        visit(task_id, [])


def planning_context_fingerprint(interview):
    payload = {
        "initial_context": interview.get("initial_context"),
        "required_tracks": interview.get("required_tracks"),
        "rounds": interview.get("rounds"),
        "ambiguity_latest": interview.get("ambiguity", {}).get("latest"),
        "completion_candidate_streak": interview.get("completion_candidate_streak"),
        "closure_audit": interview.get("closure_audit"),
        "deferred_items": interview.get("deferred_items"),
        "closure": interview.get("closure"),
    }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def planning_context_coverage(interview):
    track_rounds, user_track_rounds = interview_round_tracks(interview)
    missing_tracks = [
        track for track in INTERVIEW_REQUIRED_TRACKS if track_rounds.get(track, 0) == 0
    ]
    missing_user_decision_tracks = [
        track
        for track in INTERVIEW_REQUIRED_USER_TRACKS
        if user_track_rounds.get(track, 0) == 0
    ]
    verification_summary = (
        interview.get("required_tracks", {}).get("verification", {}).get("summary", "")
    )
    return {
        "track_rounds": track_rounds,
        "user_decision_rounds": user_track_rounds,
        "missing_tracks": missing_tracks,
        "missing_user_decision_tracks": missing_user_decision_tracks,
        "verification_ready": bool(str(verification_summary).strip()),
        "closure_audit_passed": interview.get("closure_audit", {}).get("status") == "passed",
    }


def build_planning_context(plan_id, plan_dir, title, interview):
    validate_interview(interview)
    rounds = interview.get("rounds", [])
    facts = {route: [] for route in INTERVIEW_ROUTE_ORDER}
    track_context = {}
    for track in INTERVIEW_REQUIRED_TRACKS:
        track_rounds = [
            {
                "id": item.get("id"),
                "route": item.get("route"),
                "question": item.get("question"),
                "answer": item.get("answer"),
                "source": item.get("source"),
                "purpose": item.get("purpose"),
            }
            for item in rounds
            if item.get("track") == track
        ]
        track_context[track] = {
            "summary": interview.get("required_tracks", {}).get(track, {}).get("summary", ""),
            "rounds": track_rounds,
        }
    for item in rounds:
        route = item.get("route")
        if route in facts:
            facts[route].append(
                {
                    "id": item.get("id"),
                    "track": item.get("track"),
                    "question": item.get("question"),
                    "answer": item.get("answer"),
                    "source": item.get("source"),
                    "purpose": item.get("purpose"),
                }
            )
    latest = interview.get("ambiguity", {}).get("latest") or {}
    coverage = planning_context_coverage(interview)
    required_inputs = []
    for track in INTERVIEW_REQUIRED_TRACKS:
        summary = track_context[track]["summary"]
        required_inputs.append(
            {
                "track": track,
                "summary": summary,
                "round_ids": [item["id"] for item in track_context[track]["rounds"]],
            }
        )
    return {
        "fingerprint": planning_context_fingerprint(interview),
        "summary": {
            "plan_id": plan_id,
            "title": title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "round_count": len(rounds),
        },
        "initial_context": interview.get("initial_context", ""),
        "track_context": track_context,
        "facts": facts,
        "deferred_items": interview.get("deferred_items", []),
        "completion_candidate_streak": interview.get("completion_candidate_streak", 0),
        "closure_audit": interview.get("closure_audit", default_closure_audit()),
        "plan_seed": load_plan_seed(plan_dir) if (plan_dir / "plan_seed.yaml").exists() else None,
        "coverage": coverage,
        "ambiguity": {
            "ready": latest.get("ready") is True,
            "threshold": latest.get("threshold", AMBIGUITY_THRESHOLD),
            "ambiguity": latest.get("ambiguity"),
            "weakest_dimension": latest.get("weakest_dimension", ""),
            "floor_failures": latest.get("floor_failures", []),
            "recommended_followup": latest.get("recommended_followup"),
        },
        "authoring_contract": {
            "editable_files": ["tasks.yaml"],
            "required_inputs": required_inputs,
        },
    }


def default_review_state():
    return {
        "status": "not_run",
        "stage": "bundle",
        "required_reviewers": list(REQUIRED_REVIEWERS),
        "passed_reviewers": [],
        "last_run_id": None,
        "fingerprint": None,
    }


def validate_status(data, tasks_data=None):
    require_fields(data, ["phase", "review", "current_task", "tasks", "halt"], "status.yaml")
    if data["phase"] not in VALID_PHASES:
        raise ExError(f"invalid phase: {data['phase']}")
    review = data["review"]
    if not isinstance(review, dict):
        raise ExError("status.yaml review must be a mapping")
    require_fields(
        review,
        ["status", "stage", "required_reviewers", "passed_reviewers", "last_run_id", "fingerprint"],
        "status.yaml review",
    )
    if review["status"] not in REVIEW_STATUSES:
        raise ExError("status.yaml review.status must be not_run, passed, or failed")
    if review["stage"] not in REVIEW_STAGES:
        raise ExError("status.yaml review.stage must be bundle")
    if review["required_reviewers"] != list(REQUIRED_REVIEWERS):
        raise ExError("status.yaml review.required_reviewers must match required reviewers")
    if not isinstance(review["passed_reviewers"], list):
        raise ExError("status.yaml review.passed_reviewers must be a list")
    for task_id, state in data["tasks"].items():
        if state not in TASK_STATES:
            raise ExError(f"invalid task state for {task_id}: {state}")
    if tasks_data is not None:
        task_ids = {task["id"] for task in tasks_data.get("tasks", [])}
        status_ids = set(data["tasks"].keys())
        missing = sorted(task_ids - status_ids)
        extra = sorted(status_ids - task_ids)
        if missing:
            raise ExError(f"status.yaml missing tasks: {', '.join(missing)}")
        if extra:
            raise ExError(f"status.yaml has unknown tasks: {', '.join(extra)}")


def require_fields(data, fields, label):
    for field in fields:
        if field not in data:
            raise ExError(f"{label} missing required field: {field}")


def sync_status_tasks(plan_dir, tasks_data):
    status = load_yaml(plan_dir / "status.yaml")
    statuses = status.setdefault("tasks", {})
    new_statuses = {}
    for task in tasks_data.get("tasks", []):
        task_id = task["id"]
        new_statuses[task_id] = statuses.get(task_id, "Todo")
    status["tasks"] = new_statuses
    current = status.get("current_task")
    if current and current not in new_statuses:
        status["current_task"] = None
    validate_status(status, tasks_data)
    write_yaml(plan_dir / "status.yaml", status)


def review_fingerprint(plan_dir):
    interview = load_yaml(plan_dir / "interview.yaml")
    payload = {
        "tasks": load_yaml(plan_dir / "tasks.yaml"),
        "interview_contract": interview_contract_payload(interview),
        "plan_seed": load_plan_seed(plan_dir) if (plan_dir / "plan_seed.yaml").exists() else None,
    }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def interview_contract_payload(interview):
    return {
        "initial_context": interview.get("initial_context"),
        "required_tracks": interview.get("required_tracks"),
        "rounds": interview.get("rounds"),
        "ambiguity": interview.get("ambiguity"),
        "ambiguity_ledger": interview.get("ambiguity_ledger"),
        "completion_candidate_streak": interview.get("completion_candidate_streak"),
        "closure_audit": interview.get("closure_audit"),
        "deferred_items": interview.get("deferred_items"),
        "closure": interview.get("closure"),
    }


def load_plan_seed(plan_dir):
    path = plan_dir / "plan_seed.yaml"
    if not path.exists():
        raise ExError("plan_seed.yaml is missing")
    data = load_yaml(path)
    validate_plan_seed(data)
    return data


def validate_plan_seed(data):
    require_fields(
        data,
        [
            "status",
            "generated_at",
            "round_count",
            "ambiguity_score_id",
            "closure_audit",
            "seed",
        ],
        "plan_seed.yaml",
    )
    if data["status"] != "ready":
        raise ExError("plan_seed.yaml status must be ready")
    seed = data["seed"]
    if not isinstance(seed, dict):
        raise ExError("plan_seed.yaml seed must be a mapping")
    require_fields(
        seed,
        [
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
        "plan_seed.yaml seed",
    )
    if not str(seed.get("goal", "")).strip():
        raise ExError("plan_seed.yaml seed.goal must not be empty")
    for field in [
        "context",
        "non_goals",
        "constraints",
        "success_criteria",
        "verification_expectations",
        "execution_boundaries",
        "source_round_ids",
        "deferred_items",
    ]:
        if not isinstance(seed[field], list):
            raise ExError(f"plan_seed.yaml seed.{field} must be a list")


def plan_seed_is_current(plan_dir, interview=None):
    if not (plan_dir / "plan_seed.yaml").exists():
        return False
    interview = interview or load_yaml(plan_dir / "interview.yaml")
    validate_interview(interview)
    latest = interview.get("ambiguity", {}).get("latest") or {}
    audit = interview.get("closure_audit", {})
    try:
        seed = load_plan_seed(plan_dir)
    except ExError:
        return False
    return (
        seed.get("round_count") == len(interview.get("rounds", []))
        and seed.get("ambiguity_score_id") == latest.get("id")
        and seed.get("closure_audit", {}).get("status") == "passed"
        and audit.get("status") == "passed"
        and audit.get("round_count") == len(interview.get("rounds", []))
        and audit.get("score_id") == latest.get("id")
    )


def require_review_passed(plan_dir, status, action):
    review = status.get("review", {})
    if review.get("status") != "passed":
        raise ExError(f"{action} requires bundle review PASS")
    current_fingerprint = review_fingerprint(plan_dir)
    if review.get("fingerprint") != current_fingerprint:
        raise ExError(f"{action} requires fresh bundle review PASS")


def reset_review_status(plan_dir):
    status = load_yaml(plan_dir / "status.yaml")
    status["review"] = default_review_state()
    validate_status(status, load_yaml(plan_dir / "tasks.yaml"))
    write_yaml(plan_dir / "status.yaml", status)


def reset_seed_review_state(plan_dir, preserve_feedback=False):
    interview = load_yaml(plan_dir / "interview.yaml")
    feedback = []
    if preserve_feedback:
        existing = interview.get("seed_review", {}).get("feedback", [])
        feedback = existing if isinstance(existing, list) else []
    interview["seed_review"] = {
        "status": "not_presented",
        "fingerprint": None,
        "comment": "",
        "feedback": feedback,
    }
    validate_interview(interview)
    write_yaml(plan_dir / "interview.yaml", interview)


def mark_seed_review_presented(plan_dir):
    interview = load_yaml(plan_dir / "interview.yaml")
    seed_review = interview.setdefault("seed_review", {})
    seed_review["status"] = "presented"
    seed_review["fingerprint"] = review_fingerprint(plan_dir)
    seed_review.setdefault("comment", "")
    seed_review.setdefault("feedback", [])
    validate_interview(interview)
    write_yaml(plan_dir / "interview.yaml", interview)


def mark_seed_review_approved(plan_dir, comment):
    interview = load_yaml(plan_dir / "interview.yaml")
    seed_review = interview.setdefault("seed_review", {})
    seed_review["status"] = "approved"
    seed_review["fingerprint"] = review_fingerprint(plan_dir)
    seed_review["comment"] = comment or "Plan seed approved."
    seed_review.setdefault("feedback", [])
    validate_interview(interview)
    write_yaml(plan_dir / "interview.yaml", interview)


def append_seed_review_feedback(plan_dir, feedback, classification):
    interview = load_yaml(plan_dir / "interview.yaml")
    seed_review = interview.setdefault("seed_review", {})
    seed_review.setdefault("feedback", []).append(
        {
            "id": next_id(seed_review.get("feedback", []), "F"),
            "action": classification.get("action"),
            "summary": classification.get("summary", ""),
            "feedback": feedback,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    seed_review["status"] = "presented"
    seed_review["fingerprint"] = review_fingerprint(plan_dir)
    seed_review.setdefault("comment", "")
    validate_interview(interview)
    write_yaml(plan_dir / "interview.yaml", interview)


def next_review_run_id(status):
    raw = str(status.get("review", {}).get("last_run_id") or "")
    if raw.startswith("R") and raw[1:].isdigit():
        return f"R{int(raw[1:]) + 1}"
    return "R1"


def status_groups(bundle):
    statuses = task_status(bundle)
    return {
        "done": [task_id for task_id, state in statuses.items() if state == "Done"],
        "doing": [task_id for task_id, state in statuses.items() if state == "Doing"],
        "todo": [task_id for task_id, state in statuses.items() if state == "Todo"],
    }


def is_ready(task, statuses):
    if statuses.get(task["id"]) != "Todo":
        return False
    return all(statuses.get(dep) == "Done" for dep in task.get("depends_on", []))


def ready_tasks(bundle):
    statuses = task_status(bundle)
    if bundle["status"].get("phase") not in {"ready_for_exec", "executing"}:
        return []
    if bundle["status"].get("current_task"):
        return []
    return [task for task in task_list(bundle) if is_ready(task, statuses)]


def final_tasks(bundle):
    return [task for task in task_list(bundle) if task.get("kind") == "final_verification"]


def can_finish(bundle):
    statuses = task_status(bundle)
    if not task_list(bundle):
        return False
    if any(state != "Done" for state in statuses.values()):
        return False
    finals = final_tasks(bundle)
    return bool(finals) and all(statuses.get(task["id"]) == "Done" for task in finals)


def find_task(bundle, task_id):
    tasks = task_map(bundle)
    if task_id not in tasks:
        raise ExError(f"unknown task: {task_id}")
    return tasks[task_id]


def task_step(task, step_id):
    for step in task.get("verification", {}).get("steps", []):
        if step.get("id") == step_id:
            return step
    raise ExError(f"task {task['id']} has no verification step: {step_id}")


def expected_evidence_for_task(task):
    return task.get("expected_evidence", [])


def recorded_evidence_for_task(bundle, task_id):
    return [record for record in evidence_records(bundle) if record.get("task_id") == task_id]


def required_evidence_missing(bundle, task):
    if not task.get("verification", {}).get("evidence_required", False):
        return []
    records = recorded_evidence_for_task(bundle, task["id"])
    recorded = {(record.get("step_id"), record.get("artifact")) for record in records if record.get("success") is True}
    missing = []
    for expected in expected_evidence_for_task(task):
        key = (expected.get("step_id"), expected.get("file"))
        if key not in recorded:
            missing.append(expected.get("file"))
    return missing


def agent_context(plan_dir):
    plan_seed_path = plan_dir / "plan_seed.yaml"
    plan_id, _ = active_plan()
    interview = load_yaml(plan_dir / "interview.yaml")
    plan_seed = load_yaml(plan_seed_path) if plan_seed_path.exists() else None
    title = plan_seed["seed"]["title"] if plan_seed else plan_dir.name.replace("-", " ").title()
    bundle = {
        "tasks": load_yaml(plan_dir / "tasks.yaml"),
        "plan_seed": plan_seed,
        "context_pack": build_planning_context(plan_id, plan_dir, title, interview),
        "interview": interview,
        "status": load_yaml(plan_dir / "status.yaml"),
        "notes": load_yaml(plan_dir / "notes.yaml"),
    }
    return dump_json(
        {
            "repo_root": str(Path.cwd()),
            "bundle_path": str(plan_dir),
            "bundle": bundle,
        }
    )


def append_interview_agent_run(plan_dir, interview, role, status, output=None, error=None, command_options=None):
    runs = interview.setdefault("agent_runs", [])
    run = {
        "id": next_id(runs, "A"),
        "role": role,
        "model": CODEX_AGENT_DEFAULT_MODEL,
        "sandbox": CODEX_AGENT_DEFAULT_SANDBOX,
        "reasoning_effort": CODEX_AGENT_REASONING_EFFORT,
        "command_options": command_options
        or {
            "json": True,
            "skip_git_repo_check": True,
            "ephemeral": True,
            "sandbox": CODEX_AGENT_DEFAULT_SANDBOX,
            "model": CODEX_AGENT_DEFAULT_MODEL,
            "model_reasoning_effort": CODEX_AGENT_REASONING_EFFORT,
        },
        "status": status,
        "output": output,
        "error": error,
    }
    runs.append(run)
    write_yaml(plan_dir / "interview.yaml", interview)
    return run


def run_interview_codex_agent(plan_dir, interview, role, prompt, schema):
    try:
        result = run_codex_agent(role, prompt, schema, cwd=Path.cwd(), plan_dir=plan_dir)
    except Exception as exc:
        append_interview_agent_run(plan_dir, interview, role, "failed", error=str(exc))
        raise
    append_interview_agent_run(plan_dir, interview, role, "passed", output=result["output"])
    return result["output"]


def question_option_schema():
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "label": {"type": "string", "minLength": 1, "maxLength": QUESTION_OPTION_LABEL_MAX},
            "description": {
                "type": "string",
                "minLength": 1,
                "maxLength": QUESTION_OPTION_DESCRIPTION_MAX,
            },
            "recommended": {"type": "boolean"},
        },
        "required": ["label", "description", "recommended"],
    }


def validate_question_options(options, label):
    if not isinstance(options, list):
        raise ExError(f"{label} must be a list")
    if not 2 <= len(options) <= 3:
        raise ExError(f"{label} must contain 2 or 3 items")
    recommended_count = 0
    seen = set()
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ExError(f"{label}[{index}] must be a mapping")
        require_fields(option, ["label", "description", "recommended"], f"{label}[{index}]")
        option_label = str(option["label"]).strip()
        description = str(option["description"]).strip()
        if not option_label:
            raise ExError(f"{label}[{index}].label must not be empty")
        if len(option_label) > QUESTION_OPTION_LABEL_MAX:
            raise ExError(f"{label}[{index}].label is too long")
        if option_label in seen:
            raise ExError(f"{label} labels must be unique")
        seen.add(option_label)
        if not description:
            raise ExError(f"{label}[{index}].description must not be empty")
        if len(description) > QUESTION_OPTION_DESCRIPTION_MAX:
            raise ExError(f"{label}[{index}].description is too long")
        if not isinstance(option["recommended"], bool):
            raise ExError(f"{label}[{index}].recommended must be true or false")
        if option["recommended"]:
            recommended_count += 1
    if recommended_count != 1:
        raise ExError(f"{label} must contain exactly one recommended option")


def normalize_question_options(options):
    validate_question_options(options, "question options")
    normalized = []
    for option in options:
        normalized.append(
            {
                "label": str(option["label"]).strip(),
                "description": str(option["description"]).strip(),
                "recommended": bool(option["recommended"]),
            }
        )
    return normalized


def question_options_for_kind(kind):
    if kind == "defer":
        return [
            {
                "label": "직접 답변",
                "description": "현재 판단을 직접 입력합니다.",
                "recommended": True,
            },
            {
                "label": "지금은 보류",
                "description": "실행 결정을 바꾸지 않는 세부사항이면 보류합니다.",
                "recommended": False,
            },
        ]
    return [
        {
            "label": "직접 답변",
            "description": "현재 판단을 직접 입력합니다.",
            "recommended": True,
        },
        {
            "label": "질문 수정 필요",
            "description": "질문이 의도와 맞지 않음을 답변으로 기록합니다.",
            "recommended": False,
        },
    ]


def ask_next_schema():
    option = question_option_schema()
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {"type": "string", "enum": ["ask_user", "record_fact", "ready_for_score"]},
            "route": {"type": "string", "enum": sorted(INTERVIEW_ROUTES)},
            "track": {"type": "string", "enum": list(INTERVIEW_REQUIRED_TRACKS)},
            "question": {"type": "string"},
            "answer": {"type": "string"},
            "source": {"type": "string"},
            "skip_eligible": {"type": "boolean"},
            "skip_kind": {"type": "string", "enum": ["defer", "decide_later"]},
            "options": {
                "type": "array",
                "minItems": 2,
                "maxItems": 3,
                "items": option,
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
            "skip_eligible",
            "skip_kind",
            "options",
            "reason",
        ],
    }


def score_schema():
    component = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "clarity_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "justification": {"type": "string"},
        },
        "required": ["clarity_score", "justification"],
    }
    option = question_option_schema()
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
                    "route": {"type": "string", "enum": sorted(INTERVIEW_USER_ROUTES)},
                    "track": {"type": "string", "enum": list(INTERVIEW_REQUIRED_TRACKS)},
                    "question": {"type": "string"},
                    "options": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 3,
                        "items": option,
                    },
                },
                "required": ["route", "track", "question", "options"],
            },
            "summary": {"type": "string"},
        },
        "required": ["project_mode", "components", "weakest_dimension", "recommended_followup", "summary"],
    }


def closure_audit_schema():
    option = question_option_schema()
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {"type": "string", "enum": ["pass", "ask_user"]},
            "route": {"type": "string", "enum": sorted(INTERVIEW_USER_ROUTES)},
            "track": {"type": "string", "enum": list(INTERVIEW_REQUIRED_TRACKS)},
            "question": {"type": "string"},
            "summary": {"type": "string"},
            "material_blockers": {"type": "array", "items": {"type": "string"}},
            "skip_eligible": {"type": "boolean"},
            "skip_kind": {"type": "string", "enum": ["defer", "decide_later"]},
            "options": {
                "type": "array",
                "minItems": 2,
                "maxItems": 3,
                "items": option,
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


def plan_seed_schema():
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


def review_schema():
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


def ask_next_prompt(plan_dir):
    return (
        "You are the coplan Socratic interviewer. Inspect the original request, transcript, ambiguity snapshot, and bundle context; choose the single next action that most reduces implementation-changing ambiguity.\n"
        "Return JSON only. Ask about the user's intent, core change, ownership, public behavior, or non-obvious tradeoff. Do not ask process questions about how to build a plan bundle, how to verify the planner, or how many agents to run unless that is the user's actual task.\n"
        "If user judgment is needed, action=ask_user with route user_decision or code_plus_decision. If a repo/research fact is enough and directly grounded in context, action=record_fact with route code_fact or research_confirmation. If at least three answered rounds exist and no material question remains, action=ready_for_score.\n"
        "Use tracks only as extraction labels: scope, non_goals, outputs, verification, constraints, stop_conditions. Never force a checklist order across those tracks.\n"
        "Brownfield hint: prefer questions about the intended behavioral boundary, source of truth, API/protocol ownership, lifecycle/recovery, migration, or cross-client impact when those could change the implementation.\n"
        "Perspective panel: user-intent guardian asks what outcome changes; maintainer asks what existing behavior must survive; executor asks what static decision it would otherwise have to make; verifier asks what proof is minimally sufficient; Seed Closer asks which unresolved choice would invalidate the plan.\n"
        "Answer prefix guidance: ask concise questions that invite concrete answers like 'Change...', 'Preserve...', 'Exclude...', or 'Prove with...'.\n"
        "Always populate options with 2-3 concise UI choices and exactly one recommended=true item. For action=ask_user, options must not decide for the user; they should offer useful answer directions plus room for free-form correction. For other actions, use neutral fallback options.\n"
        "Set skip_eligible=true only for useful details that can be intentionally deferred without changing the plan contract; set skip_eligible=false for material implementation decisions. Use skip_kind=defer for optional detail and decide_later for explicit future decisions.\n\n"
        f"Context:\n{agent_context(plan_dir)}"
    )


def score_prompt(plan_dir, project_mode):
    return (
        "You are the coplan ambiguity scoring agent. Score requirement clarity from 0.0 to 1.0. Use low-variance judgment; scoring_temperature_intent is 0.1. Return JSON only.\n"
        "Score goal_clarity, constraint_clarity, success_criteria_clarity, and context_clarity. For greenfield, still provide context_clarity but it will not be weighted.\n"
        f"Requested project_mode: {project_mode}.\n"
        "Treat intentional deferrals in deferred_items as settled unless they would force the executor to choose behavior, ownership, migration, or verification policy. Set recommended_followup to the single best question for exposing a user-owned tradeoff or brownfield context gap before execution. For brownfield work with weak context_clarity, prefer a repository-specific code/docs/behavior boundary question.\n"
        "recommended_followup must include options with 2-3 concise UI choices and exactly one recommended=true item. Options must help the user answer, not make hidden planning decisions.\n"
        "Do not declare readiness in prose; the CLI will compute weighted clarity and ambiguity.\n\n"
        f"Context:\n{agent_context(plan_dir)}"
    )


def closure_audit_prompt(plan_dir):
    return (
        "You are the coplan closure_auditor using Seed Closer criteria. Decide only whether the interview is ready for plan_seed extraction and bundle authoring. Return JSON only.\n"
        "A low ambiguity score is not sufficient. PASS only when no implementation-changing decision remains for ownership/source of truth, API/protocol, lifecycle/recovery, migration, cross-client impact, execution boundaries, or verification expectations.\n"
        "If any material decision remains, action=ask_user and ask exactly one highest-impact follow-up. Do not ask about planning mechanics, bundle files, reviewer setup, or validation process unless the user's task is specifically about those systems.\n"
        "Always populate options with 2-3 concise UI choices and exactly one recommended=true item. For action=ask_user, options must preserve the user's final judgment and allow free-form correction. For action=pass, use neutral fallback options.\n"
        "Set skip_eligible=false for material blockers. Use skip_eligible=true only when the item can be intentionally deferred without changing executor behavior.\n\n"
        f"Context:\n{agent_context(plan_dir)}"
    )


def plan_seed_prompt(plan_dir):
    return (
        "You are the coplan seed_architect. Extract an internal plan seed from the original request, interview transcript, ambiguity ledger, closure audit, and deferred items. Return JSON only.\n"
        "The seed is the source of truth for bundle_author. It must capture the user's intended core change, constraints, success criteria, non-goals, context, verification expectations, and execution boundaries without inventing new decisions.\n"
        "Use the six tracks only as classification hints; do not require every track to have a transcript item. Preserve intentional deferrals as deferred_items only when they do not force executor planning.\n"
        "No TBD placeholders. If something material is missing, the closure audit should have failed earlier; extract the best settled contract from the transcript.\n\n"
        f"Context:\n{agent_context(plan_dir)}"
    )


def seed_reviser_prompt(plan_dir, feedback):
    return (
        "You are the coplan seed_reviser. Rewrite plan_seed.yaml seed content for wording-only user feedback. Return JSON only using the same seed schema.\n"
        "Preserve the existing goal, constraints, non-goals, success criteria, execution boundaries, verification expectations, deferred items, and source_round_ids unless the wording can be clarified without changing meaning.\n"
        "If the feedback requires a semantic change, keep the existing seed meaning and summarize the limitation in wording; the CLI routes semantic feedback through interview instead.\n\n"
        f"Feedback:\n{feedback}\n\n"
        f"Context:\n{agent_context(plan_dir)}"
    )


def reviewer_prompt(plan_dir, reviewer):
    if reviewer == "contract_reviewer":
        focus = (
            "Review whether tasks.yaml faithfully implements plan_seed.yaml. "
            "Block hidden decisions, scope drift, contradictions, task DAG assumptions, file scope problems, and acceptance criteria that ask execution to choose between materially different user-visible behaviors."
        )
    else:
        focus = (
            "Review whether verification commands, evidence, final verification, and success signals are minimally sufficient for plan_seed.yaml. "
            "Block if verification would not prove the user's intended behavior or if it asks the executor to invent proof policy."
        )
    return (
        f"You are the {reviewer} for a coplan bundle. {focus}\n"
        "Return JSON only with status PASS or FAIL. This is a post-author bundle review. Do not re-check mechanical schema fields owned by CLI validation unless the semantics are meaningless.\n\n"
        f"Context:\n{agent_context(plan_dir)}"
    )


def create_pending_question(
    plan_dir,
    interview,
    route,
    track,
    question,
    *,
    purpose=None,
    enforce_focus=True,
    skip_eligible=False,
    skip_kind=None,
    options=None,
):
    if interview.get("status") == "closed":
        raise ExError("interview is closed; reopen a track before asking more questions")
    if interview.get("pending_user_question") is not None:
        raise ExError("pending user question already exists; record its answer before asking another")
    if track not in INTERVIEW_REQUIRED_TRACK_SET:
        raise ExError(f"unknown interview track: {track}")
    if route not in INTERVIEW_USER_ROUTES:
        raise ExError("interview ask only supports user_decision or code_plus_decision")
    if purpose is not None and purpose not in INTERVIEW_QUESTION_PURPOSES:
        raise ExError(f"unknown interview question purpose: {purpose}")
    if skip_kind is not None and skip_kind not in INTERVIEW_SKIP_KINDS:
        raise ExError(f"unknown interview skip kind: {skip_kind}")
    if enforce_focus:
        focus_blocker = interview_focus_blocker(interview, track)
        if focus_blocker:
            raise ExError(focus_blocker)
    pending = {
        "id": next_id(interview.get("rounds", []), "Q"),
        "route": route,
        "track": track,
        "question": question,
        "skip_eligible": bool(skip_eligible),
        "options": normalize_question_options(
            options or question_options_for_kind(skip_kind if skip_eligible else None)
        ),
    }
    if purpose:
        pending["purpose"] = purpose
    if skip_kind is not None:
        pending["skip_kind"] = skip_kind
    interview["pending_user_question"] = pending
    validate_interview(interview)
    write_yaml(plan_dir / "interview.yaml", interview)
    append_flow_log(
        plan_dir,
        "interview.question.created",
        question_id=pending["id"],
        route=route,
        track=track,
        purpose=purpose,
        skip_eligible=bool(skip_eligible),
        skip_kind=skip_kind,
        option_count=len(pending["options"]),
        question_hash=hash_text(question),
        question_bytes=len(question.encode("utf-8")),
    )
    return pending


def component_score(components, name):
    component = components.get(name)
    if not isinstance(component, dict):
        raise ExError(f"ambiguity scorer missing component: {name}")
    value = component.get("clarity_score")
    if not isinstance(value, (int, float)) or value < 0 or value > 1:
        raise ExError(f"ambiguity scorer component {name} must be 0.0-1.0")
    return float(value)


def normalize_ambiguity_score(output, interview, requested_mode):
    project_mode = output.get("project_mode")
    if requested_mode != "auto":
        project_mode = requested_mode
    if project_mode not in AMBIGUITY_WEIGHTS:
        raise ExError("ambiguity scorer project_mode must be greenfield or brownfield")
    components = output.get("components")
    if not isinstance(components, dict):
        raise ExError("ambiguity scorer components must be a mapping")
    weights = AMBIGUITY_WEIGHTS[project_mode]
    weighted_clarity = 0.0
    floor_failures = []
    normalized_components = {}
    for name, weight in weights.items():
        clarity = component_score(components, name)
        weighted_clarity += clarity * weight
        floor = AMBIGUITY_FLOORS[name]
        if clarity < floor:
            floor_failures.append(f"{name} {clarity:.2f} < {floor:.2f}")
        normalized_components[name] = {
            "clarity_score": clarity,
            "weight": weight,
            "justification": str(components[name].get("justification", "")),
        }
    if project_mode == "greenfield" and "context_clarity" in components:
        normalized_components["context_clarity"] = {
            "clarity_score": component_score(components, "context_clarity"),
            "weight": 0.0,
            "justification": str(components["context_clarity"].get("justification", "")),
        }
    ambiguity = max(0.0, min(1.0, 1.0 - weighted_clarity))
    ready = ambiguity <= AMBIGUITY_THRESHOLD and not floor_failures
    history = interview.get("ambiguity", {}).get("history", [])
    return {
        "id": next_id(history, "S"),
        "project_mode": project_mode,
        "threshold": AMBIGUITY_THRESHOLD,
        "weighted_clarity": round(weighted_clarity, 4),
        "ambiguity": round(ambiguity, 4),
        "ready": ready,
        "floor_failures": floor_failures,
        "components": normalized_components,
        "weakest_dimension": str(output.get("weakest_dimension", "")),
        "recommended_followup": output.get("recommended_followup"),
        "summary": str(output.get("summary", "")),
        "round_count": len(interview.get("rounds", [])),
        "scoring_temperature_intent": AMBIGUITY_SCORING_TEMPERATURE_INTENT,
        "model": CODEX_AGENT_DEFAULT_MODEL,
        "reasoning_effort": CODEX_AGENT_REASONING_EFFORT,
    }


def current_task_status(bundle, current_id):
    task = find_task(bundle, current_id)
    return {
        "task": task,
        "summary": {
            "id": current_id,
            "title": task.get("title"),
            "status": task_status(bundle).get(current_id),
            "next_required_action": f"Continue {current_id} until required evidence is recorded and completion gates pass.",
        },
        "view": {
            "files": task.get("files"),
            "verification": task.get("verification"),
            "acceptance_criteria": task.get("acceptance_criteria"),
        },
        "evidence_state": {
            "required": [item.get("file") for item in expected_evidence_for_task(task)],
            "recorded": [
                record.get("artifact")
                for record in recorded_evidence_for_task(bundle, current_id)
            ],
        },
    }


def safe_evidence_name(name):
    if os.path.isabs(name):
        raise ExError("--name must be relative to evidence/")
    if ".." in Path(name).parts:
        raise ExError("--name must not contain ..")
    return name


def set_nested(data, path, value=None, add=False, remove=False):
    parts = path.split(".")
    if parts[0] not in CONTRACT_REPAIR_ROOTS:
        raise ExError("repair field must start with files, implementation_notes, or verification")
    target = data
    for part in parts[:-1]:
        if not isinstance(target, dict):
            raise ExError(f"cannot traverse field path: {path}")
        target = target.setdefault(part, {})
    leaf = parts[-1]
    if add:
        existing = target.setdefault(leaf, [])
        if not isinstance(existing, list):
            raise ExError(f"field is not a list: {path}")
        existing.append(value)
    elif remove:
        existing = target.get(leaf)
        if not isinstance(existing, list):
            raise ExError(f"field is not a list: {path}")
        target[leaf] = [item for item in existing if item != value]
    else:
        target[leaf] = value


def flow_mode_from_phase(phase):
    if phase in {"planning", "seed_review"}:
        return "planner"
    if phase in {"ready_for_exec", "executing"}:
        return "executor"
    if phase == "halted":
        return "halted"
    if phase == "complete":
        return "complete"
    return "unknown"


def flow_result(data, root_action, *, mode=None):
    action_type = root_action.get("type")
    if action_type not in FLOW_ROOT_ACTION_TYPES:
        raise ExError(f"unknown flow root action: {action_type}")
    result = {
        "contract_version": FLOW_CONTRACT_VERSION,
        "mode": mode or data.get("mode") or "unknown",
    }
    if data.get("phase") is not None:
        result["phase"] = data["phase"]
    result["root_action"] = root_action
    return result


def print_flow_result(data, root_action, *, mode=None):
    result = flow_result(
        data,
        root_action,
        mode=mode,
    )
    plan_dir = active_plan_dir_or_none()
    command_ok = result.get("mode") != "error" and data.get("ok", True) is not False
    append_flow_log(
        plan_dir,
        "root_action.emit",
        command=CURRENT_FLOW_COMMAND,
        mode=result.get("mode"),
        root_action=root_action.get("type"),
    )
    append_flow_log(
        plan_dir,
        "flow.command.end",
        command=CURRENT_FLOW_COMMAND,
        ok=command_ok,
        phase_after=current_phase_or_none(plan_dir) if plan_dir else None,
        root_action=root_action.get("type"),
        mode=result.get("mode"),
    )
    print_yaml(result)


def flow_error_data():
    data = {"ok": False}
    plan_dir = active_plan_dir_or_none()
    phase = current_phase_or_none(plan_dir) if plan_dir else None
    if phase:
        data["phase"] = phase
    return data


def print_flow_error(message):
    print_flow_result(
        flow_error_data(),
        report_error_action(message),
        mode="error",
    )


def active_plan_summary(bundle):
    return {"id": bundle["plan_id"]}


def report_error_action(message):
    return {
        "type": "report_error",
        "message": message,
    }


def ask_user_action(pending):
    action = {
        "type": "ask_user",
        "question": pending["question"],
        "options": pending["options"],
        "response_command": f"{CLI_COMMAND_NAME} flow respond --stdin",
    }
    if pending.get("skip_eligible"):
        action["skip_eligible"] = True
        action["skip_kind"] = pending.get("skip_kind") or "defer"
    return action


def present_plan_seed_action(plan_dir):
    return {
        "type": "present_plan_seed",
        "plan_seed": load_plan_seed(plan_dir),
        "response_command": f"{CLI_COMMAND_NAME} flow respond --stdin",
    }


def notify_plan_done_action(bundle):
    return {
        "type": "notify_plan_done",
        "active_plan": active_plan_summary(bundle),
        "message": "플랜이 완료되었습니다. 실행을 시작하려면 coexec를 실행하세요.",
    }


def report_halt_action(bundle):
    return {"type": "report_halt", "halt": bundle["status"].get("halt")}


def report_complete_action(bundle):
    return {
        "type": "report_complete",
        "active_plan": active_plan_summary(bundle),
        "progress": status_groups(bundle),
    }


def task_root_action(bundle, action_type):
    current_id = bundle["status"].get("current_task")
    if not current_id:
        raise ExError("no current task is claimed")
    task_state = current_task_status(bundle, current_id)
    latest_failed = [
        record
        for record in recorded_evidence_for_task(bundle, current_id)
        if record.get("success") is False
    ]
    action = {
        "type": action_type,
        "active_plan": active_plan_summary(bundle),
        "task": task_state["task"],
        "plan_seed": bundle.get("plan_seed"),
        "status": task_state["summary"],
        "task_view": task_state["view"],
        "evidence_state": task_state["evidence_state"],
        "notes": exec_notes_view(bundle, current_id),
    }
    if latest_failed:
        action["latest_failed_evidence"] = latest_failed[-1]
    return action


def init_plan(plan_id, title, initial_context=""):
    require_yaml()
    validate_plan_id(plan_id)
    plan_dir = PLAN_ROOT / plan_id
    if plan_dir.exists():
        raise ExError(f"{plan_dir} already exists; choose a new plan id")
    (plan_dir / "evidence").mkdir(parents=True, exist_ok=True)
    PLAN_ROOT.mkdir(parents=True, exist_ok=True)
    write_yaml(EXEC_FILE, {"active_plan_id": plan_id, "plan_dir": str(plan_dir)})
    write_yaml(plan_dir / "tasks.yaml", {"tasks": []})
    write_yaml(plan_dir / "interview.yaml", default_interview(initial_context))
    write_yaml(
        plan_dir / "status.yaml",
        {
            "phase": "planning",
            "review": default_review_state(),
            "current_task": None,
            "tasks": {},
            "halt": None,
        },
    )
    write_yaml(plan_dir / "notes.yaml", {"entries": []})
    write_yaml(plan_dir / "evidence.yaml", {"records": []})
    return plan_dir


def track_summary_from_rounds(interview, track):
    answers = [
        str(item.get("answer", "")).strip()
        for item in interview.get("rounds", [])
        if item.get("track") == track and str(item.get("answer", "")).strip()
    ]
    return " / ".join(answers[-2:]) if answers else ""


def non_user_streak_question(interview):
    if interview.get("non_user_answer_streak", 0) >= INTERVIEW_NON_USER_STREAK_LIMIT:
        return {
            "route": "user_decision",
            "track": "scope",
            "question": "Before using more inferred facts, what user-owned intent or tradeoff should guide this plan?",
        }
    return None


def record_interview_round(plan_dir, *, route, track, question, answer, source):
    interview = load_yaml(plan_dir / "interview.yaml")
    validate_interview(interview)
    if interview.get("status") == "closed":
        raise ExError("interview is closed; reopen a track before recording more answers")
    if track not in INTERVIEW_REQUIRED_TRACK_SET:
        raise ExError(f"unknown interview track: {track}")
    if (
        interview.get("non_user_answer_streak", 0) >= INTERVIEW_NON_USER_STREAK_LIMIT
        and route not in INTERVIEW_USER_ROUTES
    ):
        raise ExError("next interview answer must require user judgment after 3 non-user answers")
    focus_blocker = interview_focus_blocker(interview, track)
    if focus_blocker:
        raise ExError(focus_blocker)
    pending = interview.get("pending_user_question")
    if route in INTERVIEW_USER_ROUTES:
        if pending is None:
            raise ExError("user-judgment answers require a pending question")
        if pending.get("route") != route or pending.get("track") != track or pending.get("question") != question:
            raise ExError("user-judgment answer must match the pending user question")
        round_id = pending["id"]
        purpose = pending.get("purpose")
        skip_kind = pending.get("skip_kind") if pending.get("skip_eligible") else None
    else:
        if pending is not None:
            raise ExError("record the pending user answer before adding non-user interview facts")
        round_id = next_id(interview.get("rounds", []), "Q")
        purpose = None
        skip_kind = None
    round_item = {
        "id": round_id,
        "route": route,
        "track": track,
        "question": question,
        "answer": answer,
        "source": source,
    }
    if purpose:
        round_item["purpose"] = purpose
    if skip_kind and is_deferred_answer(answer):
        round_item["deferred"] = True
        round_item["skip_kind"] = skip_kind
        interview.setdefault("deferred_items", []).append(
            {
                "round_id": round_id,
                "track": track,
                "kind": skip_kind,
                "question": question,
                "answer": answer,
            }
        )
    interview.setdefault("rounds", []).append(round_item)
    interview["non_user_answer_streak"] = (
        interview.get("non_user_answer_streak", 0) + 1
        if route in INTERVIEW_NON_USER_ROUTES
        else 0
    )
    interview["status"] = "open"
    interview["pending_user_question"] = None
    interview["closure"]["ready"] = False
    interview["closure"]["summary"] = ""
    interview["closure_audit"] = default_closure_audit()
    interview["completion_candidate_streak"] = 0
    interview["seed_review"] = {
        "status": "not_presented",
        "fingerprint": None,
        "comment": "",
        "feedback": [],
    }
    validate_interview(interview)
    write_yaml(plan_dir / "interview.yaml", interview)
    reset_review_status(plan_dir)
    append_flow_log(
        plan_dir,
        "interview.answer.recorded",
        round_id=round_id,
        route=route,
        track=track,
        source=source,
        question_hash=hash_text(question),
        answer_hash=hash_text(answer),
        answer_bytes=len(str(answer).encode("utf-8")),
    )
    return round_item


def score_interview_internal(plan_dir, mode="auto"):
    interview = load_yaml(plan_dir / "interview.yaml")
    validate_interview(interview)
    if interview_answered_round_count(interview) < INTERVIEW_MIN_TOTAL_ROUNDS:
        raise ExError(
            f"ambiguity scoring requires at least {INTERVIEW_MIN_TOTAL_ROUNDS} answered interview rounds"
        )
    output = run_interview_codex_agent(
        plan_dir,
        interview,
        "score",
        score_prompt(plan_dir, mode),
        score_schema(),
    )
    interview = load_yaml(plan_dir / "interview.yaml")
    score = normalize_ambiguity_score(output, interview, mode)
    ambiguity = interview.setdefault("ambiguity", {"latest": None, "history": []})
    ambiguity.setdefault("history", []).append(score)
    ambiguity["latest"] = score
    interview.setdefault("ambiguity_ledger", []).append(
        {
            "score_id": score["id"],
            "round_count": score["round_count"],
            "ambiguity": score["ambiguity"],
            "ready": score["ready"],
            "weakest_dimension": score["weakest_dimension"],
            "summary": score["summary"],
        }
    )
    if score.get("ready") is True:
        interview["completion_candidate_streak"] = interview.get("completion_candidate_streak", 0) + 1
    else:
        interview["completion_candidate_streak"] = 0
    interview["closure_audit"] = default_closure_audit()
    interview["seed_review"] = {
        "status": "not_presented",
        "fingerprint": None,
        "comment": "",
        "feedback": [],
    }
    validate_interview(interview)
    write_yaml(plan_dir / "interview.yaml", interview)
    reset_review_status(plan_dir)
    append_flow_log(
        plan_dir,
        "interview.score",
        score_id=score["id"],
        ready=score.get("ready"),
        ambiguity=score.get("ambiguity"),
        weakest_dimension=score.get("weakest_dimension"),
        round_count=score.get("round_count"),
    )
    return score


def closure_audit_is_current(interview):
    latest = interview.get("ambiguity", {}).get("latest") or {}
    audit = interview.get("closure_audit", {})
    return (
        audit.get("status") == "passed"
        and audit.get("round_count") == len(interview.get("rounds", []))
        and audit.get("score_id") == latest.get("id")
    )


def run_closure_audit_internal(plan_dir):
    interview = load_yaml(plan_dir / "interview.yaml")
    validate_interview(interview)
    latest = interview.get("ambiguity", {}).get("latest") or {}
    if latest.get("ready") is not True:
        raise ExError("closure audit requires a ready ambiguity score")
    if interview.get("completion_candidate_streak", 0) < INTERVIEW_COMPLETION_CANDIDATE_STREAK_REQUIRED:
        raise ExError("closure audit requires readiness streak")
    output = run_interview_codex_agent(
        plan_dir,
        interview,
        "closure_auditor",
        closure_audit_prompt(plan_dir),
        closure_audit_schema(),
    )
    interview = load_yaml(plan_dir / "interview.yaml")
    audit = {
        "status": "passed" if output["action"] == "pass" else "failed",
        "summary": output["summary"],
        "material_blockers": output.get("material_blockers", []),
        "question": output.get("question", ""),
        "round_count": len(interview.get("rounds", [])),
        "score_id": latest.get("id"),
    }
    if audit["status"] == "passed" and audit["material_blockers"]:
        raise ExError("closure_auditor cannot pass with material_blockers")
    interview["closure_audit"] = audit
    interview["closure"]["material_blockers"] = list(output.get("material_blockers", []))
    validate_interview(interview)
    write_yaml(plan_dir / "interview.yaml", interview)
    reset_review_status(plan_dir)
    append_flow_log(
        plan_dir,
        "interview.closure_audit",
        status=audit["status"],
        score_id=audit["score_id"],
        blocker_count=len(audit["material_blockers"]),
        question_hash=hash_text(audit["question"]),
    )
    if output["action"] == "ask_user":
        if not str(output.get("question", "")).strip():
            raise ExError("closure_auditor ask_user requires a question")
        pending = create_pending_question(
            plan_dir,
            load_yaml(plan_dir / "interview.yaml"),
            output["route"],
            output["track"],
            output["question"],
            purpose=INTERVIEW_CLOSURE_AUDIT_PURPOSE,
            enforce_focus=False,
            skip_eligible=output.get("skip_eligible") is True,
            skip_kind=output.get("skip_kind"),
            options=output.get("options"),
        )
        return {"root_action": ask_user_action(pending)}
    return {"audit": audit}


def write_plan_seed_internal(plan_dir):
    interview = load_yaml(plan_dir / "interview.yaml")
    validate_interview(interview)
    if not closure_audit_is_current(interview):
        raise ExError("plan_seed.yaml requires a current passed closure audit")
    output = run_interview_codex_agent(
        plan_dir,
        interview,
        "seed_architect",
        plan_seed_prompt(plan_dir),
        plan_seed_schema(),
    )
    latest = interview.get("ambiguity", {}).get("latest") or {}
    plan_seed = {
        "status": "ready",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "round_count": len(interview.get("rounds", [])),
        "ambiguity_score_id": latest.get("id"),
        "closure_audit": interview.get("closure_audit"),
        "seed": output,
    }
    validate_plan_seed(plan_seed)
    write_yaml(plan_dir / "plan_seed.yaml", plan_seed)
    reset_review_status(plan_dir)
    reset_seed_review_state(plan_dir)
    append_flow_log(
        plan_dir,
        "plan_seed.generated",
        round_count=plan_seed["round_count"],
        ambiguity_score_id=plan_seed["ambiguity_score_id"],
        goal_hash=hash_text(output.get("goal")),
    )
    return plan_seed


def revise_plan_seed_internal(plan_dir, feedback):
    interview = load_yaml(plan_dir / "interview.yaml")
    validate_interview(interview)
    if not plan_seed_is_current(plan_dir, interview):
        raise ExError("seed revision requires a current plan_seed.yaml")
    output = run_interview_codex_agent(
        plan_dir,
        interview,
        "seed_reviser",
        seed_reviser_prompt(plan_dir, feedback),
        plan_seed_schema(),
    )
    latest = interview.get("ambiguity", {}).get("latest") or {}
    plan_seed = {
        "status": "ready",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "round_count": len(interview.get("rounds", [])),
        "ambiguity_score_id": latest.get("id"),
        "closure_audit": interview.get("closure_audit"),
        "seed": output,
    }
    validate_plan_seed(plan_seed)
    write_yaml(plan_dir / "plan_seed.yaml", plan_seed)
    reset_review_status(plan_dir)
    reset_seed_review_state(plan_dir, preserve_feedback=True)
    append_flow_log(
        plan_dir,
        "plan_seed.revised",
        round_count=plan_seed["round_count"],
        ambiguity_score_id=plan_seed["ambiguity_score_id"],
        feedback_hash=hash_text(feedback),
        goal_hash=hash_text(output.get("goal")),
    )
    return plan_seed


def close_interview_if_ready(plan_dir):
    interview = load_yaml(plan_dir / "interview.yaml")
    validate_interview(interview)
    latest = interview.get("ambiguity", {}).get("latest") or {}
    if latest.get("ready") is not True:
        return False
    if interview.get("pending_user_question") is not None:
        return False
    if interview.get("closure", {}).get("material_blockers"):
        return False
    if not closure_audit_is_current(interview):
        return False
    if not plan_seed_is_current(plan_dir, interview):
        return False
    for track in INTERVIEW_REQUIRED_TRACKS:
        interview["required_tracks"][track]["status"] = "closed"
        interview["required_tracks"][track]["summary"] = track_summary_from_rounds(interview, track)
    summary = latest.get("summary") or "Interview gates satisfied by recorded rounds and ambiguity score."
    for check in INTERVIEW_CLOSURE_CHECKS:
        interview["closure"]["checks"][check] = {
            "passed": True,
            "summary": INTERVIEW_CLOSURE_CHECK_SUMMARIES[check],
        }
    blockers = interview_closure_blockers(interview)
    if blockers:
        return False
    interview["status"] = "closed"
    interview["closure"]["ready"] = True
    interview["closure"]["summary"] = summary
    validate_interview(interview)
    write_yaml(plan_dir / "interview.yaml", interview)
    reset_review_status(plan_dir)
    append_flow_log(
        plan_dir,
        "interview.closed",
        round_count=len(interview.get("rounds", [])),
        closed_tracks=list(INTERVIEW_REQUIRED_TRACKS),
        summary_hash=hash_text(summary),
    )
    return True


def advance_interview_until_boundary(plan_dir, max_steps=8):
    for _ in range(max_steps):
        interview = load_yaml(plan_dir / "interview.yaml")
        validate_interview(interview)
        pending = interview.get("pending_user_question")
        if pending is not None:
            return ask_user_action(pending)
        if interview_seed_ready(interview):
            return None
        question = non_user_streak_question(interview)
        if question:
            pending = create_pending_question(
                plan_dir,
                interview,
                question["route"],
                question["track"],
                question["question"],
                options=question.get("options"),
            )
            return ask_user_action(pending)
        if interview_answered_round_count(interview) < INTERVIEW_MIN_TOTAL_ROUNDS:
            output = run_interview_codex_agent(
                plan_dir,
                interview,
                "ask-next",
                ask_next_prompt(plan_dir),
                ask_next_schema(),
            )
            if output["action"] == "ask_user":
                interview = load_yaml(plan_dir / "interview.yaml")
                pending = create_pending_question(
                    plan_dir,
                    interview,
                    output["route"],
                    output["track"],
                    output["question"],
                    skip_eligible=output.get("skip_eligible") is True,
                    skip_kind=output.get("skip_kind"),
                    options=output.get("options"),
                )
                return ask_user_action(pending)
            if output["action"] == "record_fact":
                record_interview_round(
                    plan_dir,
                    route=output["route"],
                    track=output["track"],
                    question=output["question"],
                    answer=output["answer"],
                    source=output["source"],
                )
                continue
            pending = create_pending_question(
                plan_dir,
                load_yaml(plan_dir / "interview.yaml"),
                "user_decision",
                "scope",
                "What is the core change you want this plan to preserve above all else?",
                enforce_focus=False,
            )
            return ask_user_action(pending)
        latest = interview.get("ambiguity", {}).get("latest")
        if not isinstance(latest, dict) or latest.get("round_count") != len(interview.get("rounds", [])):
            score_interview_internal(plan_dir)
            continue
        latest = load_yaml(plan_dir / "interview.yaml").get("ambiguity", {}).get("latest") or {}
        followup = latest.get("recommended_followup")
        if followup and latest.get("ready") is not True:
            interview = load_yaml(plan_dir / "interview.yaml")
            if not (
                isinstance(followup, dict)
                and followup.get("route") in INTERVIEW_USER_ROUTES
                and followup.get("track") in INTERVIEW_REQUIRED_TRACK_SET
                and str(followup.get("question", "")).strip()
            ):
                followup = hidden_assumption_followup(latest)
            pending = create_pending_question(
                plan_dir,
                interview,
                followup["route"],
                followup["track"],
                followup["question"],
                enforce_focus=False,
                options=followup.get("options"),
            )
            return ask_user_action(pending)
        interview = load_yaml(plan_dir / "interview.yaml")
        if (
            latest.get("ready") is True
            and interview.get("completion_candidate_streak", 0)
            >= INTERVIEW_COMPLETION_CANDIDATE_STREAK_REQUIRED
            and not closure_audit_is_current(interview)
        ):
            audit_result = run_closure_audit_internal(plan_dir)
            if audit_result.get("root_action"):
                return audit_result["root_action"]
            continue
        interview = load_yaml(plan_dir / "interview.yaml")
        if closure_audit_is_current(interview) and not plan_seed_is_current(plan_dir, interview):
            write_plan_seed_internal(plan_dir)
            continue
        if close_interview_if_ready(plan_dir):
            return None
        interview = load_yaml(plan_dir / "interview.yaml")
        output = run_interview_codex_agent(
            plan_dir,
            interview,
            "ask-next",
            ask_next_prompt(plan_dir),
            ask_next_schema(),
        )
        if output["action"] == "ask_user":
            interview = load_yaml(plan_dir / "interview.yaml")
            pending = create_pending_question(
                plan_dir,
                interview,
                output["route"],
                output["track"],
                output["question"],
                skip_eligible=output.get("skip_eligible") is True,
                skip_kind=output.get("skip_kind"),
                options=output.get("options"),
            )
            return ask_user_action(pending)
        if output["action"] == "record_fact":
            record_interview_round(
                plan_dir,
                route=output["route"],
                track=output["track"],
                question=output["question"],
                answer=output["answer"],
                source=output["source"],
            )
            continue
        if output["action"] == "ready_for_score":
            if interview_answered_round_count(load_yaml(plan_dir / "interview.yaml")) < INTERVIEW_MIN_TOTAL_ROUNDS:
                continue
            score_interview_internal(plan_dir)
            continue
    raise ExError("interview flow did not reach a root boundary")


def bundle_author_schema():
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


def bundle_author_prompt(plan_dir, review_results=None, feedback=None):
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
        f"Context:\n{agent_context(plan_dir)}"
        f"{extra}"
    )


def write_authored_bundle(plan_dir, output):
    tasks = output.get("tasks")
    if not isinstance(tasks, dict):
        raise ExError("bundle_author must return tasks mapping")
    validate_tasks(tasks)
    write_yaml(plan_dir / "tasks.yaml", tasks)
    sync_status_tasks(plan_dir, tasks)
    reset_review_status(plan_dir)
    append_flow_log(
        plan_dir,
        "bundle.authored",
        tasks_hash=hash_text(dump_json(tasks)),
        task_count=len(tasks.get("tasks", [])) if isinstance(tasks.get("tasks"), list) else None,
    )


def validate_bundle_internal(plan_dir):
    require_interview_closed(plan_dir, "flow validation")
    interview = load_yaml(plan_dir / "interview.yaml")
    if not plan_seed_is_current(plan_dir, interview):
        raise ExError("plan_seed.yaml must match the closed interview")
    load_plan_seed(plan_dir)
    tasks = load_yaml(plan_dir / "tasks.yaml")
    status = load_yaml(plan_dir / "status.yaml")
    validate_tasks(tasks)
    validate_status(status, tasks)


def run_review_internal(plan_dir):
    validate_bundle_internal(plan_dir)
    tasks = load_yaml(plan_dir / "tasks.yaml")
    status = load_yaml(plan_dir / "status.yaml")
    reviewer_outputs = run_codex_agents_parallel(
        [
            {"role": reviewer, "prompt": reviewer_prompt(plan_dir, reviewer), "schema": review_schema()}
            for reviewer in REQUIRED_REVIEWERS
        ],
        cwd=Path.cwd(),
        plan_dir=plan_dir,
    )
    results = []
    passed_reviewers = []
    for reviewer in REQUIRED_REVIEWERS:
        result = reviewer_outputs[reviewer]["output"]
        review_status = result["status"]
        if review_status == "PASS":
            passed_reviewers.append(reviewer)
        results.append({"reviewer": reviewer, **result})
        append_flow_log(
            plan_dir,
            "review.result",
            role=reviewer,
            status=review_status,
            issue_count=len(result.get("issues", [])) if isinstance(result.get("issues"), list) else None,
        )
        append_note(
            plan_dir,
            "decision" if review_status == "PASS" else "risk",
            f"{reviewer} {review_status}: {result['summary']}",
            "Codex CLI bundle review.",
            ["plan_seed.yaml", "tasks.yaml"],
            f"{CLI_COMMAND_NAME} flow next",
        )
    previous_status = status
    status = load_yaml(plan_dir / "status.yaml")
    status["review"] = {
        **default_review_state(),
        "status": "passed" if len(passed_reviewers) == len(REQUIRED_REVIEWERS) else "failed",
        "stage": "bundle",
        "required_reviewers": list(REQUIRED_REVIEWERS),
        "passed_reviewers": passed_reviewers,
        "last_run_id": next_review_run_id(previous_status),
        "fingerprint": review_fingerprint(plan_dir) if len(passed_reviewers) == len(REQUIRED_REVIEWERS) else None,
    }
    validate_status(status, tasks)
    write_yaml(plan_dir / "status.yaml", status)
    append_flow_log(
        plan_dir,
        "review.join",
        status=status["review"]["status"],
        passed_reviewers=passed_reviewers,
        required_reviewers=list(REQUIRED_REVIEWERS),
    )
    return {"review": status["review"], "results": results}


def review_followup_question(review_results):
    for result in review_results or []:
        issues = result.get("issues") if isinstance(result, dict) else None
        if isinstance(issues, list) and issues:
            issue = str(issues[0]).strip()
            reviewer = str(result.get("reviewer", "reviewer"))
            track = "verification" if "verification" in reviewer else "constraints"
            return {
                "track": track,
                "question": (
                    "Bundle review could not resolve this seed conflict without user intent: "
                    f"{issue} What should the approved plan contract say?"
                ),
            }
    return {
        "track": "constraints",
        "question": (
            "Bundle review found a plan_seed conflict that the author could not repair. "
            "What user-facing contract should take precedence?"
        ),
    }


def author_and_review_until_boundary(plan_dir, feedback=None):
    interview = load_yaml(plan_dir / "interview.yaml")
    validate_interview(interview)
    if not plan_seed_is_current(plan_dir, interview):
        raise ExError("bundle authoring requires a current plan_seed.yaml")
    review_results = None
    validation_feedback = None
    for _ in range(3):
        author_feedback = "\n".join(item for item in [feedback, validation_feedback] if item)
        output = run_codex_agent(
            "bundle_author",
            bundle_author_prompt(plan_dir, review_results=review_results, feedback=author_feedback),
            bundle_author_schema(),
            cwd=Path.cwd(),
            plan_dir=plan_dir,
        )["output"]
        try:
            write_authored_bundle(plan_dir, output)
        except ExError as exc:
            validation_feedback = bundle_validation_feedback(exc)
            append_flow_log(
                plan_dir,
                "bundle.validation_failed",
                error=str(exc),
            )
            continue
        validation_feedback = None
        review = run_review_internal(plan_dir)
        if review["review"]["status"] == "passed":
            status = load_yaml(plan_dir / "status.yaml")
            previous_phase = status.get("phase")
            status["phase"] = "seed_review"
            validate_status(status, load_yaml(plan_dir / "tasks.yaml"))
            write_yaml(plan_dir / "status.yaml", status)
            mark_seed_review_presented(plan_dir)
            append_flow_log(
                plan_dir,
                "state.transition",
                file="status.yaml",
                field="phase",
                previous=previous_phase,
                current="seed_review",
                reason="review_passed",
            )
            return {
                "review": review["review"],
                "author_summary": output.get("summary", ""),
                "root_action": present_plan_seed_action(plan_dir),
            }
        review_results = review["results"]
    interview = load_yaml(plan_dir / "interview.yaml")
    interview["status"] = "open"
    interview["closure"]["ready"] = False
    interview["closure"]["summary"] = ""
    interview["closure_audit"] = default_closure_audit()
    write_yaml(plan_dir / "interview.yaml", interview)
    reset_review_status(plan_dir)
    followup = review_followup_question(review_results)
    interview = load_yaml(plan_dir / "interview.yaml")
    interview["required_tracks"][followup["track"]]["status"] = "open"
    write_yaml(plan_dir / "interview.yaml", interview)
    pending = create_pending_question(
        plan_dir,
        load_yaml(plan_dir / "interview.yaml"),
        "user_decision",
        followup["track"],
        followup["question"],
        enforce_focus=False,
    )
    return {"review_results": review_results, "root_action": ask_user_action(pending)}


def planner_needs_authoring(plan_dir):
    status = load_yaml(plan_dir / "status.yaml")
    if status.get("review", {}).get("status") != "passed":
        return True
    try:
        validate_bundle_internal(plan_dir)
        require_review_passed(plan_dir, status, "flow")
    except ExError:
        return True
    return False


def approve_and_finalize(plan_dir, comment):
    require_interview_closed(plan_dir, "plan seed approval")
    load_plan_seed(plan_dir)
    status = load_yaml(plan_dir / "status.yaml")
    if status.get("phase") != "seed_review":
        raise ExError("plan seed approval requires seed_review phase")
    require_review_passed(plan_dir, status, "plan seed approval")
    previous_phase = status.get("phase")
    status["phase"] = "ready_for_exec"
    validate_status(status, load_yaml(plan_dir / "tasks.yaml"))
    write_yaml(plan_dir / "status.yaml", status)
    mark_seed_review_approved(plan_dir, comment)
    append_flow_log(
        plan_dir,
        "state.transition",
        file="status.yaml",
        field="phase",
        previous=previous_phase,
        current="ready_for_exec",
        reason="plan_seed_approved",
    )
    append_note(
        plan_dir,
        "decision",
        comment or "Plan seed approved.",
        "Plan seed approval comment.",
        ["plan_seed.yaml", "status.yaml#phase"],
        f"{CLI_COMMAND_NAME} flow respond",
    )
    tasks = load_yaml(plan_dir / "tasks.yaml")
    status = load_yaml(plan_dir / "status.yaml")
    validate_tasks(tasks)
    validate_status(status, tasks)
    require_review_passed(plan_dir, status, "flow finalize")


def feedback_schema():
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {"type": "string", "enum": ["approve", "wording_change", "meaning_change"]},
            "track": {"type": "string", "enum": list(INTERVIEW_REQUIRED_TRACKS)},
            "question": {"type": "string"},
            "answer": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": ["action", "track", "question", "answer", "summary"],
    }


def classify_seed_feedback(plan_dir, feedback):
    normalized = feedback.strip().lower()
    approval_words = {"approve", "approved", "yes", "ok", "ship", "looks good", "승인", "좋아", "좋습니다", "확정"}
    if normalized in approval_words:
        return {
            "action": "approve",
            "track": "scope",
            "question": "",
            "answer": feedback,
            "summary": "Plan seed approved.",
        }
    prompt = (
        "Classify this plan seed feedback for coflow. Return JSON only.\n"
        "approve means the user accepts the plan seed. wording_change means text-only polish. "
        "meaning_change means scope, output, verification, constraints, or stop conditions changed.\n\n"
        f"Plan seed:\n{dump_json(load_plan_seed(plan_dir))}\n\nFeedback:\n{feedback}"
    )
    return run_codex_agent("seed_feedback", prompt, feedback_schema(), cwd=Path.cwd(), plan_dir=plan_dir)["output"]


def apply_seed_feedback(plan_dir, feedback):
    classification = classify_seed_feedback(plan_dir, feedback)
    append_flow_log(
        plan_dir,
        "seed_feedback.classified",
        action=classification.get("action"),
        track=classification.get("track"),
        feedback_hash=hash_text(feedback),
        feedback_bytes=len(feedback.encode("utf-8")),
        summary_hash=hash_text(classification.get("summary")),
    )
    append_seed_review_feedback(plan_dir, feedback, classification)
    action = classification["action"]
    if action == "approve":
        approve_and_finalize(plan_dir, classification.get("summary") or feedback)
        return {"feedback": classification}
    if action == "wording_change":
        append_note(
            plan_dir,
            "revision",
            classification.get("summary") or feedback,
            "User requested wording-only plan seed feedback.",
            ["plan_seed.yaml"],
            f"{CLI_COMMAND_NAME} flow respond",
        )
        revise_plan_seed_internal(plan_dir, feedback)
        result = author_and_review_until_boundary(plan_dir)
        result["feedback"] = classification
        return result
    track = classification["track"]
    interview = load_yaml(plan_dir / "interview.yaml")
    interview["status"] = "open"
    interview["closure"]["ready"] = False
    interview["closure"]["summary"] = ""
    interview["closure_audit"] = default_closure_audit()
    interview["completion_candidate_streak"] = 0
    interview["seed_review"] = {
        "status": "not_presented",
        "fingerprint": None,
        "comment": "",
        "feedback": [],
    }
    interview["required_tracks"][track]["status"] = "open"
    interview["required_tracks"][track]["summary"] = ""
    status = load_yaml(plan_dir / "status.yaml")
    previous_phase = status.get("phase")
    status["phase"] = "planning"
    validate_status(status, load_yaml(plan_dir / "tasks.yaml"))
    write_yaml(plan_dir / "status.yaml", status)
    append_flow_log(
        plan_dir,
        "state.transition",
        file="status.yaml",
        field="phase",
        previous=previous_phase,
        current="planning",
        reason="seed_meaning_change_feedback",
    )
    write_yaml(plan_dir / "interview.yaml", interview)
    reset_review_status(plan_dir)
    pending = create_pending_question(
        plan_dir,
        load_yaml(plan_dir / "interview.yaml"),
        "user_decision",
        track,
        classification["question"] or "What should change in the approved plan contract?",
    )
    record_interview_round(
        plan_dir,
        route=pending["route"],
        track=pending["track"],
        question=pending["question"],
        answer=classification["answer"] or feedback,
        source="from-user:co-flow-seed-feedback",
    )
    return {"feedback": classification}


def start_execution_internal(plan_dir):
    status = load_yaml(plan_dir / "status.yaml")
    tasks = load_yaml(plan_dir / "tasks.yaml")
    validate_status(status, tasks)
    if status["phase"] != "ready_for_exec":
        raise ExError("execution can start only from ready_for_exec")
    previous_phase = status["phase"]
    status["phase"] = "executing"
    write_yaml(plan_dir / "status.yaml", status)
    append_flow_log(
        plan_dir,
        "state.transition",
        file="status.yaml",
        field="phase",
        previous=previous_phase,
        current="executing",
        reason="start_execution",
    )


def claim_task_internal(bundle, task_id):
    if bundle["status"].get("phase") != "executing":
        raise ExError("tasks can be claimed only while phase is executing")
    if bundle["status"].get("current_task"):
        raise ExError(f"current task is already Doing: {bundle['status']['current_task']}")
    task = find_task(bundle, task_id)
    if task not in ready_tasks(bundle):
        raise ExError(f"task is not ready: {task_id}")
    status = bundle["status"]
    previous_current = status.get("current_task")
    previous_task_state = status["tasks"].get(task_id)
    status["current_task"] = task_id
    status["tasks"][task_id] = "Doing"
    write_yaml(bundle["plan_dir"] / "status.yaml", status)
    append_flow_log(
        bundle["plan_dir"],
        "state.transition",
        file="status.yaml",
        field="current_task",
        previous=previous_current,
        current=task_id,
        reason="claim_task",
    )
    append_flow_log(
        bundle["plan_dir"],
        "state.transition",
        file="status.yaml",
        field=f"tasks.{task_id}",
        previous=previous_task_state,
        current="Doing",
        reason="claim_task",
    )
    append_flow_log(bundle["plan_dir"], "task.claimed", task_id=task_id)


def complete_task_internal(bundle, task_id):
    status = bundle["status"]
    task = find_task(bundle, task_id)
    if status.get("current_task") != task_id or task_status(bundle).get(task_id) != "Doing":
        raise ExError(f"task is not currently Doing: {task_id}")
    missing = required_evidence_missing(bundle, task)
    if missing:
        raise ExError("required evidence missing: " + ", ".join(missing))
    previous_current = status.get("current_task")
    previous_task_state = status["tasks"].get(task_id)
    status["tasks"][task_id] = "Done"
    status["current_task"] = None
    write_yaml(bundle["plan_dir"] / "status.yaml", status)
    append_flow_log(
        bundle["plan_dir"],
        "state.transition",
        file="status.yaml",
        field=f"tasks.{task_id}",
        previous=previous_task_state,
        current="Done",
        reason="complete_task",
    )
    append_flow_log(
        bundle["plan_dir"],
        "state.transition",
        file="status.yaml",
        field="current_task",
        previous=previous_current,
        current=None,
        reason="complete_task",
    )
    append_flow_log(bundle["plan_dir"], "task.completed", task_id=task_id)


def finish_internal(bundle):
    if bundle["status"].get("phase") == "halted":
        raise ExError("cannot finish while phase is halted")
    if not can_finish(bundle):
        remaining = [task_id for task_id, state in task_status(bundle).items() if state != "Done"]
        finals = [task["id"] for task in final_tasks(bundle) if task_status(bundle).get(task["id"]) != "Done"]
        raise ExError(f"cannot finish; remaining={remaining}, final_verification_remaining={finals}")
    status = bundle["status"]
    previous_phase = status.get("phase")
    status["phase"] = "complete"
    status["current_task"] = None
    write_yaml(bundle["plan_dir"] / "status.yaml", status)
    append_flow_log(
        bundle["plan_dir"],
        "state.transition",
        file="status.yaml",
        field="phase",
        previous=previous_phase,
        current="complete",
        reason="finish_execution",
    )
    append_flow_log(bundle["plan_dir"], "execution.completed")


def evidence_name_for_step(task, step_id):
    for expected in expected_evidence_for_task(task):
        if expected.get("step_id") == step_id:
            artifact = Path(expected["file"])
            if len(artifact.parts) >= 2 and artifact.parts[0] == "evidence":
                return str(Path(*artifact.parts[1:]))
            return str(artifact)
    return f"{task['id'].lower()}-{step_id}.txt"


def record_current_evidence(step_id, command, exit_code, success):
    bundle = load_bundle()
    current_id = bundle["status"].get("current_task")
    if not current_id:
        raise ExError("evidence requires a current Doing task")
    task = find_task(bundle, current_id)
    task_step(task, step_id)
    if task_status(bundle).get(current_id) != "Doing":
        raise ExError("evidence can be added only for a Doing task")
    name = safe_evidence_name(evidence_name_for_step(task, step_id))
    artifact = Path("evidence") / name
    artifact_path = bundle["plan_dir"] / artifact
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(read_stdin(), encoding="utf-8")
    evidence = bundle["evidence"]
    records = evidence.setdefault("records", [])
    record = {
        "id": next_id(records, "V"),
        "task_id": current_id,
        "step_id": step_id,
        "command": command,
        "exit_code": exit_code,
        "success": normalize_bool(success),
        "artifact": str(artifact),
        "satisfies": [],
    }
    records.append(record)
    write_yaml(bundle["plan_dir"] / "evidence.yaml", evidence)
    if not record["success"]:
        append_note(
            bundle["plan_dir"],
            "risk",
            f"Verification failed for {current_id}/{step_id}.",
            f"Command exited {exit_code}: {command}",
            [f"task:{current_id}", "evidence.yaml", str(artifact)],
            f"{CLI_COMMAND_NAME} flow evidence",
        )
    append_flow_log(
        bundle["plan_dir"],
        "evidence.recorded",
        record_id=record["id"],
        task_id=current_id,
        step_id=step_id,
        command_hash=hash_text(command),
        command_bytes=len(str(command).encode("utf-8")),
        exit_code=exit_code,
        success=record["success"],
        artifact=str(artifact),
    )
    return record


def advance_executor_until_boundary():
    for _ in range(8):
        bundle = load_bundle()
        phase = bundle["status"].get("phase")
        if phase == "ready_for_exec":
            start_execution_internal(bundle["plan_dir"])
            continue
        if phase == "executing":
            current_id = bundle["status"].get("current_task")
            if current_id:
                return {"root_action": task_root_action(bundle, "execute_task")}
            ready = ready_tasks(bundle)
            if ready:
                claim_task_internal(bundle, ready[0]["id"])
                continue
            if can_finish(bundle):
                finish_internal(bundle)
                continue
            raise ExError("execution has no current task, ready task, or finish gate")
        if phase == "halted":
            return {"root_action": report_halt_action(bundle)}
        if phase == "complete":
            return {"root_action": report_complete_action(bundle)}
        raise ExError(f"phase is not executable: {phase}")
    raise ExError("executor flow did not reach a root boundary")


def advance_planner_until_boundary(feedback=None):
    plan_id, plan_dir = active_plan()
    status = load_yaml(plan_dir / "status.yaml")
    phase = status.get("phase")
    if phase == "seed_review":
        return {"root_action": present_plan_seed_action(plan_dir)}
    if phase != "planning":
        raise ExError(f"phase is not plannable: {phase}")
    action = advance_interview_until_boundary(plan_dir)
    if action:
        return {"root_action": action}
    if planner_needs_authoring(plan_dir) or feedback:
        result = author_and_review_until_boundary(plan_dir, feedback=feedback)
        return result
    status = load_yaml(plan_dir / "status.yaml")
    previous_phase = status.get("phase")
    status["phase"] = "seed_review"
    validate_status(status, load_yaml(plan_dir / "tasks.yaml"))
    write_yaml(plan_dir / "status.yaml", status)
    mark_seed_review_presented(plan_dir)
    append_flow_log(
        plan_dir,
        "state.transition",
        file="status.yaml",
        field="phase",
        previous=previous_phase,
        current="seed_review",
        reason="planner_ready_for_seed_review",
    )
    return {"root_action": present_plan_seed_action(plan_dir)}


def advance_flow_until_boundary(feedback=None):
    _, plan_dir = active_plan()
    phase = load_yaml(plan_dir / "status.yaml").get("phase")
    if phase in {"planning", "seed_review"}:
        result = advance_planner_until_boundary(feedback=feedback)
        if result["root_action"]["type"] in {"ask_user", "present_plan_seed"}:
            return result
        return advance_flow_until_boundary()
    return advance_executor_until_boundary()


def flow_status_diagnostic(bundle):
    phase = bundle["status"].get("phase")
    diagnostic = {
        "active_plan": active_plan_summary(bundle),
    }
    if phase == "planning":
        pending = bundle["interview"].get("pending_user_question")
        if pending:
            diagnostic["pending_boundary"] = "ask_user"
            diagnostic["message"] = "A user answer is waiting."
            diagnostic["response_command"] = f"{CLI_COMMAND_NAME} flow respond --stdin"
        else:
            diagnostic["pending_boundary"] = "internal_cli_progress"
            diagnostic["message"] = "Run the next command to let the CLI advance to a root boundary."
            diagnostic["next_command"] = f"{CLI_COMMAND_NAME} flow next"
    elif phase == "seed_review":
        diagnostic["pending_boundary"] = "present_plan_seed"
        diagnostic["message"] = "A plan seed review is waiting."
        diagnostic["response_command"] = f"{CLI_COMMAND_NAME} flow respond --stdin"
    elif phase == "ready_for_exec":
        diagnostic["pending_boundary"] = "internal_cli_progress"
        diagnostic["message"] = "Run the next command to let the CLI claim the next task or finish execution."
        diagnostic["next_command"] = f"{CLI_COMMAND_NAME} flow next"
    elif phase == "executing":
        current_id = bundle["status"].get("current_task")
        diagnostic["pending_boundary"] = "execute_task" if current_id else "internal_cli_progress"
        diagnostic["message"] = (
            "A current task is waiting."
            if current_id
            else "Run the next command to let the CLI claim the next task or finish execution."
        )
        if current_id:
            diagnostic["evidence_command"] = f"{CLI_COMMAND_NAME} flow evidence --stdin"
        else:
            diagnostic["next_command"] = f"{CLI_COMMAND_NAME} flow next"
    elif phase == "halted":
        diagnostic["pending_boundary"] = "report_halt"
        diagnostic["message"] = "The active plan is halted."
    elif phase == "complete":
        diagnostic["pending_boundary"] = "report_complete"
        diagnostic["message"] = "The active plan is complete."
    else:
        diagnostic["pending_boundary"] = "invalid_phase"
        diagnostic["message"] = "Fix the saved phase before continuing."
    return diagnostic


def print_flow_status_snapshot():
    bundle = load_bundle()
    phase = bundle["status"].get("phase")
    result = {
        "contract_version": FLOW_CONTRACT_VERSION,
        "mode": flow_mode_from_phase(phase),
        "phase": phase,
        "diagnostic": flow_status_diagnostic(bundle),
    }
    print_yaml(result)


def print_flow_status_error(message):
    print_yaml(
        {
            "contract_version": FLOW_CONTRACT_VERSION,
            "mode": "error",
            "diagnostic": {
                "message": message,
            },
        }
    )


def print_flow_boundary(result):
    bundle = load_bundle()
    action = result["root_action"]
    data = {
        "phase": bundle["status"].get("phase"),
    }
    print_flow_result(
        data,
        action,
        mode=result.get("mode") or flow_mode_from_phase(bundle["status"].get("phase")),
    )


def flow_init(args):
    if not args.stdin:
        raise ExError("flow init requires --stdin")
    initial_context = read_stdin().strip()
    if not initial_context:
        raise ExError("flow init requires a non-empty stdin body")
    plan_dir = init_plan(args.plan_id, args.title, initial_context)
    log_flow_command_start(
        plan_dir,
        CURRENT_FLOW_COMMAND or "flow init",
        phase_before=None,
        phase_after="planning",
    )
    result = advance_flow_until_boundary()
    print_flow_boundary(result)


def flow_next(_args):
    result = advance_flow_until_boundary()
    print_flow_boundary(result)


def flow_status(_args):
    print_flow_status_snapshot()


def flow_respond(args):
    if not args.stdin:
        raise ExError("flow respond requires --stdin")
    response = read_stdin().strip()
    if not response:
        raise ExError("flow respond requires a non-empty response on stdin")
    _, plan_dir = active_plan()
    status = load_yaml(plan_dir / "status.yaml")
    phase = status.get("phase")
    if phase == "seed_review":
        feedback_result = apply_seed_feedback(plan_dir, response)
        if feedback_result.get("root_action"):
            print_flow_boundary(feedback_result)
            return
        bundle = load_bundle()
        print_flow_boundary({"mode": "planner", "root_action": notify_plan_done_action(bundle)})
        return
    interview = load_yaml(plan_dir / "interview.yaml")
    pending = interview.get("pending_user_question")
    if pending is None:
        raise ExError("no pending user question or plan seed review is waiting for response")
    recorded_response = response
    if pending.get("skip_eligible") and is_deferred_answer(response):
        recorded_response = (
            f"Intentional deferral ({pending.get('skip_kind') or 'defer'}): "
            "the user chose to defer this question."
        )
    record_interview_round(
        plan_dir,
        route=pending["route"],
        track=pending["track"],
        question=pending["question"],
        answer=recorded_response,
        source="from-user:co-flow-respond",
    )
    result = advance_flow_until_boundary()
    print_flow_boundary(result)


def flow_evidence(args):
    if not args.stdin:
        raise ExError("flow evidence requires --stdin")
    record = record_current_evidence(args.step, args.evidence_command, args.exit_code, args.success)
    if not record["success"]:
        bundle = load_bundle()
        print_flow_boundary({"root_action": task_root_action(bundle, "repair_task")})
        return
    bundle = load_bundle()
    current_id = bundle["status"].get("current_task")
    if current_id:
        task = find_task(bundle, current_id)
        if not required_evidence_missing(bundle, task):
            complete_task_internal(bundle, current_id)
    result = advance_flow_until_boundary()
    print_flow_boundary(result)


def flow_repair(args):
    bundle = load_bundle()
    current_id = bundle["status"].get("current_task")
    if not current_id:
        raise ExError("flow repair requires a current Doing task")
    if args.set_value is None and args.add_value is None and args.remove_value is None:
        raise ExError("repair requires one of --set, --add, or --remove")
    task = find_task(bundle, current_id)
    if args.set_value is not None:
        set_nested(task, args.field, parse_yaml_value(args.set_value))
    elif args.add_value is not None:
        set_nested(task, args.field, parse_yaml_value(args.add_value), add=True)
    else:
        set_nested(task, args.field, parse_yaml_value(args.remove_value), remove=True)
    validate_tasks(bundle["tasks"])
    write_yaml(bundle["plan_dir"] / "tasks.yaml", bundle["tasks"])
    note = append_note(
        bundle["plan_dir"],
        "repair",
        f"Repaired {current_id} field {args.field}.",
        args.reason,
        [f"task:{current_id}", f"tasks.yaml#{current_id}.{args.field}"],
        f"{CLI_COMMAND_NAME} flow repair",
    )
    operation = "set" if args.set_value is not None else "add" if args.add_value is not None else "remove"
    append_flow_log(
        bundle["plan_dir"],
        "repair.applied",
        task_id=current_id,
        field=args.field,
        operation=operation,
        reason_hash=hash_text(args.reason),
    )
    bundle = load_bundle()
    print_flow_boundary({"root_action": task_root_action(bundle, "execute_task")})


def flow_halt(args):
    bundle = load_bundle()
    current_id = bundle["status"].get("current_task")
    if args.kind not in {"user_decision", "external_environment"}:
        raise ExError("halt kind must be user_decision or external_environment")
    if current_id:
        find_task(bundle, current_id)
    status = bundle["status"]
    previous_phase = status.get("phase")
    status["phase"] = "halted"
    status["halt"] = {"kind": args.kind, "task": current_id, "reason": args.reason}
    write_yaml(bundle["plan_dir"] / "status.yaml", status)
    append_flow_log(
        bundle["plan_dir"],
        "state.transition",
        file="status.yaml",
        field="phase",
        previous=previous_phase,
        current="halted",
        reason="halt",
    )
    note = append_note(
        bundle["plan_dir"],
        "halt",
        f"Execution halted: {args.reason}",
        args.kind,
        [item for item in [f"task:{current_id}" if current_id else None, "status.yaml#halt"] if item],
        f"{CLI_COMMAND_NAME} flow halt",
    )
    append_flow_log(
        bundle["plan_dir"],
        "halt.recorded",
        kind=args.kind,
        task_id=current_id,
        reason_hash=hash_text(args.reason),
    )
    bundle = load_bundle()
    print_flow_boundary({"root_action": report_halt_action(bundle)})


def build_parser():
    parser = argparse.ArgumentParser(prog=CLI_COMMAND_NAME)
    sub = parser.add_subparsers(dest="command", required=True)

    flow = sub.add_parser("flow")
    flow_sub = flow.add_subparsers(dest="flow_command", required=True)

    flow_init_parser = flow_sub.add_parser("init")
    flow_init_parser.add_argument("--plan-id", required=True)
    flow_init_parser.add_argument("--title", required=True)
    flow_init_parser.add_argument("--stdin", action="store_true", required=True)
    flow_init_parser.set_defaults(func=flow_init)

    flow_next_parser = flow_sub.add_parser("next")
    flow_next_parser.set_defaults(func=flow_next)

    flow_status_parser = flow_sub.add_parser("status")
    flow_status_parser.set_defaults(func=flow_status)

    flow_respond_parser = flow_sub.add_parser("respond")
    flow_respond_parser.add_argument("--stdin", action="store_true")
    flow_respond_parser.set_defaults(func=flow_respond)

    flow_evidence_parser = flow_sub.add_parser("evidence")
    flow_evidence_parser.add_argument("--step", required=True)
    flow_evidence_parser.add_argument("--command", dest="evidence_command", required=True)
    flow_evidence_parser.add_argument("--exit-code", type=int, required=True)
    flow_evidence_parser.add_argument("--success", choices=["true", "false"], required=True)
    flow_evidence_parser.add_argument("--stdin", action="store_true")
    flow_evidence_parser.set_defaults(func=flow_evidence)

    flow_repair_parser = flow_sub.add_parser("repair")
    flow_repair_parser.add_argument("--field", required=True)
    flow_repair_parser.add_argument("--reason", required=True)
    flow_repair_parser.add_argument("--set", dest="set_value")
    flow_repair_parser.add_argument("--add", dest="add_value")
    flow_repair_parser.add_argument("--remove", dest="remove_value")
    flow_repair_parser.set_defaults(func=flow_repair)

    flow_halt_parser = flow_sub.add_parser("halt")
    flow_halt_parser.add_argument("--kind", choices=["user_decision", "external_environment"], required=True)
    flow_halt_parser.add_argument("--reason", required=True)
    flow_halt_parser.set_defaults(func=flow_halt)

    return parser


def main(argv=None):
    global CURRENT_FLOW_COMMAND
    parser = build_parser()
    args = parser.parse_args(argv)
    CURRENT_FLOW_COMMAND = flow_command_name(args)
    try:
        require_yaml()
        if getattr(args, "command", None) == "flow" and getattr(args, "flow_command", None) not in {"init", "status"}:
            log_flow_command_start(active_plan_dir_or_none(), CURRENT_FLOW_COMMAND)
        args.func(args)
    except GateError as exc:
        data = {"ok": False, "error": str(exc)}
        data.update(exc.data)
        if getattr(args, "command", None) == "flow":
            log_flow_command_error(str(exc))
            print_flow_result(
                flow_error_data(),
                report_error_action(str(exc)),
                mode="error",
            )
        else:
            print_yaml(result_with_required_action(data, exc.required_action, exc.next_command))
        return 1
    except ExError as exc:
        if getattr(args, "command", None) == "flow":
            if getattr(args, "flow_command", None) == "status":
                print_flow_status_error(str(exc))
                return 1
            log_flow_command_error(str(exc))
            print_flow_error(str(exc))
            return 1
        sys.stdout.write("error: " + repr(str(exc)) + "\n")
        sys.stdout.write(
            f"required_action: 'Read error, satisfy the blocked gate or fix command input, then rerun the appropriate {CLI_COMMAND_NAME} command.'\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
