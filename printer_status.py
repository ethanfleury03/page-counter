"""Read-only SSH status polling for the printer/controller."""

from __future__ import annotations

import json
import os
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
CONNECT_TIMEOUT_SECONDS = 5
COMMAND_TIMEOUT_SECONDS = 8
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
            "ls /",
            "ls /var",
            "ls /var/log",
            "find /var/log -maxdepth 2 -type f 2>/dev/null | sort",
        ],
        "log_paths": [],
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
class ConnectionResult:
    name: str
    host: str
    ok: bool
    message: str
    command_output: str


def load_config(path: Path = CONFIG_PATH) -> list[ConnectionConfig]:
    if not path.exists():
        return [_parse_connection(item) for item in DEFAULT_CONNECTIONS]

    data = json.loads(path.read_text(encoding="utf-8"))
    connections = data.get("connections", [])
    if not isinstance(connections, list) or not connections:
        raise ValueError("printer_config.json must contain at least one connection.")

    return [_parse_connection(item) for item in connections]


def poll_all(path: Path = CONFIG_PATH) -> list[ConnectionResult]:
    return [poll_connection(connection) for connection in load_config(path)]


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

    return ConnectionResult(
        name=connection.name,
        host=connection.host,
        ok=True,
        message="Connected and read status data",
        command_output=output,
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
