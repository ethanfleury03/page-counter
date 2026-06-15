"""Read-only SSH status polling for the printer/controller."""

from __future__ import annotations

import json
import os
import re
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import paramiko
except ImportError:  # pragma: no cover - handled at runtime in the GUI
    paramiko = None


CONFIG_PATH = Path("printer_config.json")
EXAMPLE_CONFIG_PATH = Path("printer_config.example.json")
JOB_STATE_PATH = Path("last_job_state.json")
CONNECT_TIMEOUT_SECONDS = 5
COMMAND_TIMEOUT_SECONDS = 8
DEFAULT_POLL_INTERVAL_SECONDS = 1
FORCED_POLL_INTERVAL_SECONDS = 1
DEFAULT_CONNECTIONS = (
    {
        "name": "Printer Controller",
        "host": "192.168.100.200",
        "port": 22,
        "username": "root",
        "password": "root",
        "status_commands": [
            "hostname",
            "date",
            "pwd",
            "ls -lh /pes_client.log",
            "ls -lh /var/log/pdl/pdl.log",
            "ls -lh /var/log/gymea/gymea.log",
            "ls -lh /var/log/kareela/kareela.log",
            "ls -lh /var/log/kenmare/kenmare.log",
            "ls -lh /var/log/kirrawee/kirrawee.log",
            "grep -Ei \"page|job|copy|quantity|sheet|print\" /var/log/kareela/kareela.log 2>/dev/null | tail -n 80",
            "find /var/log -maxdepth 2 -type f 2>/dev/null | sort",
        ],
        "log_paths": [
            "/pes_client.log",
            "/var/log/pdl/pdl.log",
            "/var/log/gymea/gymea.log",
            "/var/log/kareela/kareela.log",
            "/var/log/kenmare/kenmare.log",
            "/var/log/kirrawee/kirrawee.log",
            "/var/log/messages",
        ],
    },
)


@dataclass(frozen=True)
class ConnectionConfig:
    name: str
    host: str
    port: int
    username: str
    password: str
    password_env: str
    status_commands: tuple[str, ...]
    log_paths: tuple[str, ...]


@dataclass(frozen=True)
class PrinterStatusSummary:
    job_id: str
    job_name: str
    job_state: str
    job_pages_current: int | None
    job_pages_total: int | None
    completed_pages: int | None
    job_media_length_m: float | None
    locked_job_id: str
    job_lock_status: str
    printhead_lifetime_page_count: int | None
    printed_media_length_m: float | None
    engine_state: str
    ready_for_print_data: bool | None
    last_print_time: str
    last_spit_time: str
    last_declog_time: str
    pages_since_last_wipe: int | None
    meters_since_last_wipe: float | None
    is_primed: bool | None
    is_capped: bool | None
    latest_kareela_activity: str
    latest_controller_activity: str


@dataclass(frozen=True)
class ConnectionResult:
    name: str
    host: str
    ok: bool
    message: str
    command_output: str
    summary: PrinterStatusSummary | None = None


def load_config(path: Path = CONFIG_PATH) -> list[ConnectionConfig]:
    if not path.exists():
        return [_parse_connection(item) for item in DEFAULT_CONNECTIONS]

    data = _read_json_file(path)
    connections = data.get("connections", [])
    if not isinstance(connections, list) or not connections:
        raise ValueError("printer_config.json must contain at least one connection.")

    return [_parse_connection(item) for item in connections]


def poll_all(path: Path = CONFIG_PATH) -> list[ConnectionResult]:
    return [poll_connection(connection) for connection in load_config(path)]


def load_poll_interval_seconds(path: Path = CONFIG_PATH) -> int:
    normalize_poll_interval_seconds(path)
    return FORCED_POLL_INTERVAL_SECONDS


def normalize_poll_interval_seconds(path: Path = CONFIG_PATH) -> None:
    """Keep older printer_config.json files from preserving the former 5s poll."""
    if not path.exists():
        return

    try:
        data = _read_json_file(path)
    except (OSError, json.JSONDecodeError):
        return

    if not isinstance(data, dict):
        return

    if data.get("poll_interval_seconds") == FORCED_POLL_INTERVAL_SECONDS:
        return

    data["poll_interval_seconds"] = FORCED_POLL_INTERVAL_SECONDS
    try:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def _read_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def poll_connection(connection: ConnectionConfig) -> ConnectionResult:
    if paramiko is None:
        return ConnectionResult(
            name=connection.name,
            host=connection.host,
            ok=False,
            message="Python package 'paramiko' is not installed. Run: pip install -r requirements.txt",
            command_output="",
        )

    password = os.environ.get(connection.password_env, "") or connection.password
    if not password:
        return ConnectionResult(
            name=connection.name,
            host=connection.host,
            ok=False,
            message=f"Missing password env var: {connection.password_env}",
            command_output="",
        )

    try:
        _check_tcp_port(connection.host, connection.port)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=connection.host,
            port=connection.port,
            username=connection.username,
            password=password,
            timeout=CONNECT_TIMEOUT_SECONDS,
            banner_timeout=CONNECT_TIMEOUT_SECONDS,
            auth_timeout=CONNECT_TIMEOUT_SECONDS,
            look_for_keys=False,
            allow_agent=False,
        )
        try:
            output = _run_status_commands(client, connection)
        finally:
            client.close()
    except Exception as exc:
        return ConnectionResult(
            name=connection.name,
            host=connection.host,
            ok=False,
            message=str(exc),
            command_output="",
        )

    state = _load_job_state()
    summary = parse_printer_status(output, active_job_id=state.get("active_job_id", ""))
    _save_job_state(_next_job_state(state, summary))
    return ConnectionResult(
        name=connection.name,
        host=connection.host,
        ok=True,
        message="Connected and read status data",
        command_output=output,
        summary=summary,
    )


def parse_printer_status(text: str, active_job_id: str = "") -> PrinterStatusSummary:
    job_status = _last_job_status(text, job_id=active_job_id)
    job_completion = _last_job_completion(text, job_id=active_job_id)
    if active_job_id and not job_status["job_id"] and not job_completion["job_id"]:
        job_status = _last_job_status(text)
        job_completion = _last_job_completion(text)
    printhead_lifetime_page_count = _last_int(r"Page Count:\s*([0-9]+)", text)
    printed_length = _last_float(r"Printed Media:\s*\(Length:\s*([0-9.]+)\s*m", text)
    engine_state = _last_text(r"Engine State:\s*([^,\n]+)", text) or "unknown"
    ready = _last_bool(r"Ready for Print Data:\s*(True|False)", text)
    last_print = _last_quoted_value("last_print_time", text)
    last_spit = _last_quoted_value("last_spit_time", text)
    last_declog = _last_quoted_value("last_declog_time", text)
    pages_since_wipe = _last_int(r"'pages_since_last_wipe':\s*([0-9]+)", text)
    meters_since_wipe = _last_float(r"'meters_since_last_wipe':\s*([0-9.]+)", text)
    is_primed = _last_bool(r"'is_primed':\s*(True|False)", text)
    is_capped = _last_bool(r"'is_capped':\s*(True|False)", text)
    latest_kareela_activity = _latest_activity(text, service_name="Kareela")
    latest_controller_activity = _latest_activity(text)
    job_id = job_status["job_id"] or job_completion["job_id"] or "unknown"
    job_name = job_status["job_name"] or job_completion["job_name"] or "unknown"
    job_state = _current_job_state(job_status, job_completion)

    return PrinterStatusSummary(
        job_id=job_id,
        job_name=job_name,
        job_state=job_state,
        job_pages_current=job_status["pages_current"],
        job_pages_total=job_status["pages_total"],
        completed_pages=job_completion["completed_pages"],
        job_media_length_m=job_completion["media_length_m"],
        locked_job_id=active_job_id or "none",
        job_lock_status=_job_lock_status(active_job_id, job_id, job_state),
        printhead_lifetime_page_count=printhead_lifetime_page_count,
        printed_media_length_m=printed_length,
        engine_state=engine_state,
        ready_for_print_data=ready,
        last_print_time=last_print or "unknown",
        last_spit_time=last_spit or "unknown",
        last_declog_time=last_declog or "unknown",
        pages_since_last_wipe=pages_since_wipe,
        meters_since_last_wipe=meters_since_wipe,
        is_primed=is_primed,
        is_capped=is_capped,
        latest_kareela_activity=latest_kareela_activity,
        latest_controller_activity=latest_controller_activity,
    )


def _parse_connection(item: dict[str, Any]) -> ConnectionConfig:
    return ConnectionConfig(
        name=str(item.get("name") or item.get("host") or "Printer"),
        host=str(item["host"]),
        port=int(item.get("port", 22)),
        username=str(item["username"]),
        password=str(item.get("password", "")),
        password_env=str(item.get("password_env") or "PAGE_COUNT_RIP_PRINTER_PASSWORD"),
        status_commands=tuple(_safe_commands(item.get("status_commands", []))),
        log_paths=tuple(str(path) for path in item.get("log_paths", [])),
    )


def _safe_commands(commands: list[Any]) -> list[str]:
    safe_prefixes = ("hostname", "date", "pwd", "ls ", "tail ", "cat ", "grep ", "find ")
    safe_commands = []
    for command in commands:
        command_text = str(command).strip()
        if command_text == "ls" or command_text in {"hostname", "date", "pwd"}:
            safe_commands.append(command_text)
        elif command_text.startswith(safe_prefixes):
            safe_commands.append(command_text)
    return safe_commands


def _check_tcp_port(host: str, port: int) -> None:
    with socket.create_connection((host, port), timeout=CONNECT_TIMEOUT_SECONDS):
        return


def _run_status_commands(client: Any, connection: ConnectionConfig) -> str:
    command_output = []
    commands = list(connection.status_commands)
    commands.extend(f"tail -n 40 {path}" for path in connection.log_paths)

    for command in commands:
        stdin, stdout, stderr = client.exec_command(command, timeout=COMMAND_TIMEOUT_SECONDS)
        stdin.close()
        output = stdout.read().decode("utf-8", errors="replace").strip()
        error = stderr.read().decode("utf-8", errors="replace").strip()
        exit_status = stdout.channel.recv_exit_status()
        command_output.append(f"$ {command}")
        if output:
            command_output.append(output)
        if error:
            command_output.append(error)
        command_output.append(f"[exit {exit_status}]")

    return "\n".join(command_output)


def _last_text(pattern: str, text: str) -> str | None:
    matches = re.findall(pattern, text)
    if not matches:
        return None
    return str(matches[-1]).strip()


def _last_int(pattern: str, text: str) -> int | None:
    value = _last_text(pattern, text)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _last_float(pattern: str, text: str) -> float | None:
    value = _last_text(pattern, text)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _last_bool(pattern: str, text: str) -> bool | None:
    value = _last_text(pattern, text)
    if value is None:
        return None
    return value == "True"


def _last_quoted_value(key: str, text: str) -> str | None:
    return _last_text(rf"'{re.escape(key)}':\s*'([^']+)'", text)


def _last_job_status(text: str, job_id: str = "") -> dict[str, Any]:
    pattern = re.compile(
        r"(?:GymeaJobQueueCtlr: Status change: Job|"
        r"PrintSessionMgr::notifyJobStatus\(\):)\s+"
        r"(?P<job_id>[0-9a-fA-F]+),\s*"
        r"'(?P<job_name>[^']*)',\s*"
        r"(?P<job_state>[A-Z_]+),\s*"
        r"pages\s+(?P<pages_current>\d+)/(?P<pages_total>\d+),\s*"
        r"length \(m\)\s+(?P<length>[0-9.]+)"
    )
    matches = [
        match
        for match in pattern.finditer(text)
        if not job_id or match.group("job_id") == job_id
    ]
    if not matches:
        return {
            "job_id": "",
            "job_name": "",
            "job_state": "",
            "pages_current": None,
            "pages_total": None,
            "length": None,
            "position": -1,
        }

    match = matches[-1]
    return {
        "job_id": match.group("job_id"),
        "job_name": match.group("job_name"),
        "job_state": match.group("job_state"),
        "pages_current": int(match.group("pages_current")),
        "pages_total": int(match.group("pages_total")),
        "length": float(match.group("length")),
        "position": match.start(),
    }


def _last_job_completion(text: str, job_id: str = "") -> dict[str, Any]:
    completed_job_pattern = re.compile(
        r"Completed job\s+(?P<job_id>[0-9a-fA-F]+),\s*"
        r"'(?P<job_name>[^']*)',\s*"
        r"(?P<job_state>[A-Z_]+),.*?"
        r"pages\s+(?P<completed_pages>\d+),\s*"
        r"media\s+(?P<media_length>[0-9.]+)m"
    )
    completion_pattern = re.compile(
        r"notifyJobCompletion\(\): printed: pages = "
        r"(?P<completed_pages>\d+), media length = (?P<media_length>[0-9.]+)"
    )
    completed_job_matches = [
        match
        for match in completed_job_pattern.finditer(text)
        if not job_id or match.group("job_id") == job_id
    ]
    completion_matches = list(completion_pattern.finditer(text))

    result: dict[str, Any] = {
        "job_id": "",
        "job_name": "",
        "job_state": "",
        "completed_pages": None,
        "media_length_m": None,
        "position": -1,
    }
    if completed_job_matches:
        match = completed_job_matches[-1]
        result.update(
            {
                "job_id": match.group("job_id"),
                "job_name": match.group("job_name"),
                "job_state": match.group("job_state"),
                "completed_pages": int(match.group("completed_pages")),
                "media_length_m": float(match.group("media_length")),
                "position": match.start(),
            }
        )
    if completion_matches:
        match = completion_matches[-1]
        if not job_id or result["job_id"] == job_id:
            result["completed_pages"] = int(match.group("completed_pages"))
            result["media_length_m"] = float(match.group("media_length"))
            result["position"] = max(result["position"], match.start())
    return result


def _current_job_state(job_status: dict[str, Any], job_completion: dict[str, Any]) -> str:
    if job_completion["position"] > job_status["position"] and job_completion["job_state"]:
        return str(job_completion["job_state"])
    return str(job_status["job_state"] or job_completion["job_state"] or "unknown")


def _job_lock_status(active_job_id: str, parsed_job_id: str, job_state: str) -> str:
    if not active_job_id:
        return "unlocked"
    if parsed_job_id == active_job_id and job_state in {"PRINTING", "STARTING", "IDLE"}:
        return "locked"
    if parsed_job_id == active_job_id:
        return "releasing after completion"
    return "locked; no current tail match"


def _load_job_state(path: Path = JOB_STATE_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    active_job_id = data.get("active_job_id", "")
    return {"active_job_id": str(active_job_id)} if active_job_id else {}


def _save_job_state(state: dict[str, str], path: Path = JOB_STATE_PATH) -> None:
    if state:
        path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif path.exists():
        path.unlink()


def _next_job_state(
    current_state: dict[str, str],
    summary: PrinterStatusSummary,
) -> dict[str, str]:
    active_job_id = current_state.get("active_job_id", "")
    if summary.job_id == "unknown":
        return current_state
    if summary.job_state == "PRINTING":
        return {"active_job_id": summary.job_id}
    if active_job_id and summary.job_id == active_job_id:
        if summary.job_state in {"CANCELLED", "COMPLETE", "COMPLETED", "DONE", "FAILED"}:
            return {}
        if summary.completed_pages is not None:
            return {}
    return current_state


def _latest_activity(text: str, service_name: str | None = None) -> str:
    activity_patterns = (
        "Changing state",
        "Starting ",
        "Finished ",
        "prepare_for_printing",
        "pre_job",
        "last_print_time",
        "CustomSpit",
        "PeriodicIdle",
    )
    candidates = []
    for line in text.splitlines():
        if service_name and service_name not in line:
            continue
        if any(pattern in line for pattern in activity_patterns):
            candidates.append(line.strip())
    return candidates[-1] if candidates else "No printer activity markers found in tailed logs."
