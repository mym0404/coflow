import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from co.shared.errors import AgentSpawnError


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
        raise AgentSpawnError(f"maximum coflow Codex subagent depth exceeded: {CODEX_AGENT_MAX_COFLOW_DEPTH}")
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
        raise AgentSpawnError("codex exec produced an empty last message")
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
    raise AgentSpawnError("codex exec last message is not JSON")


def run_codex_agent(role, prompt, schema, *, cwd=None, plan_dir=None, append_flow_log, hash_text, summarize_output):
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
            raise AgentSpawnError(f"codex agent {role} failed: {detail}")
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
            raise AgentSpawnError(f"codex agent {role} output must be a JSON object")
        append_flow_log(
            plan_dir,
            "codex_agent.end",
            role=role,
            status="passed",
            duration_ms=int((datetime.now(timezone.utc) - start).total_seconds() * 1000),
            output_summary=summarize_output(role, output),
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

