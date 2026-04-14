"""Best-effort recovery for a locally installed PostgreSQL instance."""

from __future__ import annotations

import os
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", ""}
DEFAULT_INSTALL_DIR = Path("W:/DB/PostgreSQL")
_BOOTSTRAP_LOCK = threading.Lock()


@dataclass(frozen=True)
class LocalPostgresInstallation:
    """Filesystem locations for one local PostgreSQL installation."""

    install_dir: Path
    bin_dir: Path
    data_dir: Path
    port: int

    @property
    def pg_ctl(self) -> Path:
        return self.bin_dir / "pg_ctl.exe"


def ensure_local_postgres_ready(host: str, port: int) -> dict[str, Any] | None:
    """Start the configured local PostgreSQL instance when it is reachable by host/port."""
    if not _auto_start_enabled() or not _is_local_host(host):
        return None

    with _BOOTSTRAP_LOCK:
        if _tcp_ready(port):
            return None

        installation = _find_installation(port)
        if installation is None:
            return None

        log_file = _get_log_file(installation)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        recovered_stale_pid = _remove_stale_pid_file(installation, port)
        if _tcp_ready(port):
            return {
                "managed": True,
                "started": False,
                "recovered_stale_pid": recovered_stale_pid,
                "data_dir": str(installation.data_dir),
                "log_file": str(log_file),
            }

        result = subprocess.run(
            [
                str(installation.pg_ctl),
                "start",
                "-D",
                str(installation.data_dir),
                "-l",
                str(log_file),
                "-w",
                "-t",
                str(_start_timeout_seconds()),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_start_timeout_seconds() + 5,
            check=False,
        )
        if result.returncode != 0 and not _wait_for_ready(port, seconds=2.0):
            summary = _summarize_process_result(result)
            raise RuntimeError(
                "本地 PostgreSQL 自动启动失败："
                f"{summary}。请检查日志文件 {log_file}"
            )

        if not _wait_for_ready(port, seconds=_start_timeout_seconds()):
            raise RuntimeError(
                f"本地 PostgreSQL 在端口 {port} 启动超时，请检查日志文件 {log_file}"
            )

        return {
            "managed": True,
            "started": True,
            "recovered_stale_pid": recovered_stale_pid,
            "data_dir": str(installation.data_dir),
            "log_file": str(log_file),
        }


def _find_installation(expected_port: int) -> LocalPostgresInstallation | None:
    for install_dir in _candidate_install_dirs():
        bin_dir = Path(os.getenv("LOCAL_PG_BIN_DIR", install_dir / "bin"))
        data_dir = Path(os.getenv("LOCAL_PG_DATA_DIR", install_dir / "data"))
        pg_ctl = bin_dir / "pg_ctl.exe"
        if not pg_ctl.exists() or not data_dir.exists():
            continue

        configured_port = _read_configured_port(data_dir)
        if configured_port != expected_port:
            continue

        return LocalPostgresInstallation(
            install_dir=install_dir,
            bin_dir=bin_dir,
            data_dir=data_dir,
            port=configured_port,
        )
    return None


def _candidate_install_dirs() -> list[Path]:
    values = [
        os.getenv("LOCAL_PG_INSTALL_DIR"),
        str(DEFAULT_INSTALL_DIR),
    ]
    install_dirs: list[Path] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        path = Path(value).expanduser()
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        install_dirs.append(path)
    return install_dirs


def _read_configured_port(data_dir: Path) -> int | None:
    config_path = data_dir / "postgresql.conf"
    if not config_path.exists():
        return None

    for line in config_path.read_text(encoding="utf-8", errors="replace").splitlines():
        content = line.split("#", maxsplit=1)[0].strip()
        if not content or not content.startswith("port"):
            continue
        _, value = content.split("=", maxsplit=1)
        try:
            return int(value.strip().strip("'\""))
        except ValueError:
            return None
    return None


def _remove_stale_pid_file(installation: LocalPostgresInstallation, port: int) -> bool:
    pid_file = installation.data_dir / "postmaster.pid"
    if not pid_file.exists():
        return False

    pid = _read_pid(pid_file)
    if pid is not None and _process_exists(pid):
        return False
    if _tcp_ready(port):
        return False

    pid_file.unlink(missing_ok=True)
    return True


def _read_pid(pid_file: Path) -> int | None:
    try:
        first_line = pid_file.read_text(encoding="utf-8", errors="replace").splitlines()[0]
        return int(first_line.strip())
    except (IndexError, OSError, ValueError):
        return None


def _process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _tcp_ready(port: int, timeout: float = 0.6) -> bool:
    for host in ("127.0.0.1", "localhost"):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def _wait_for_ready(port: int, *, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if _tcp_ready(port):
            return True
        time.sleep(0.5)
    return _tcp_ready(port)


def _auto_start_enabled() -> bool:
    value = os.getenv("LOCAL_PG_AUTO_START", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _start_timeout_seconds() -> int:
    raw = os.getenv("LOCAL_PG_START_TIMEOUT", "30").strip()
    try:
        seconds = int(raw)
    except ValueError:
        return 30
    return max(seconds, 5)


def _get_log_file(installation: LocalPostgresInstallation) -> Path:
    value = os.getenv("LOCAL_PG_LOG_FILE")
    if value:
        return Path(value).expanduser()
    return installation.install_dir / "pg_ctl-start.log"


def _is_local_host(host: str) -> bool:
    return host.strip().lower() in LOCAL_HOSTS


def _summarize_process_result(result: subprocess.CompletedProcess[str]) -> str:
    for text in (result.stderr, result.stdout):
        if text and text.strip():
            return text.strip().splitlines()[-1]
    return f"pg_ctl 退出码 {result.returncode}"
