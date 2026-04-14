"""Best-effort recovery for a locally installed PostgreSQL instance."""

from __future__ import annotations

import os
import socket
import subprocess
import tempfile
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

    @property
    def pg_isready(self) -> Path:
        return self.bin_dir / "pg_isready.exe"


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

        timeout_seconds = _start_timeout_seconds()
        process = subprocess.Popen(
            [
                str(installation.pg_ctl),
                "start",
                "-D",
                str(installation.data_dir),
                "-l",
                str(log_file),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if _tcp_ready(port) and _query_ready(installation, host, port):
                _terminate_helper_process(process)
                return {
                    "managed": True,
                    "started": True,
                    "recovered_stale_pid": recovered_stale_pid,
                    "data_dir": str(installation.data_dir),
                    "log_file": str(log_file),
                }

            returncode = process.poll()
            if returncode not in {None, 0}:
                raise RuntimeError(
                    "本地 PostgreSQL 自动启动失败："
                    f"pg_ctl 退出码 {returncode}。请检查日志文件 {log_file}"
                )

            time.sleep(0.5)

        if not (_tcp_ready(port) and _query_ready(installation, host, port)):
            _terminate_helper_process(process)
            raise RuntimeError(
                f"本地 PostgreSQL 在端口 {port} 启动超时，请检查日志文件 {log_file}"
            )

        _terminate_helper_process(process)

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

    try:
        pid_file.unlink(missing_ok=True)
    except OSError:
        return False
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
        configured = Path(value).expanduser()
        if _can_write_log_file(configured):
            return configured
    fallback = _default_log_file(installation)
    if _can_write_log_file(fallback):
        return fallback
    return installation.data_dir / "pg_ctl-start.log"


def _default_log_file(installation: LocalPostgresInstallation) -> Path:
    runtime_dir = Path(tempfile.gettempdir()) / "dbms-visual-manager" / "postgres"
    return runtime_dir / f"pg_ctl-start-{installation.port}.log"


def _can_write_log_file(path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8"):
            pass
    except OSError:
        return False
    return True


def _is_local_host(host: str) -> bool:
    return host.strip().lower() in LOCAL_HOSTS


def _terminate_helper_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is None:
        process.terminate()


def _query_ready(
    installation: LocalPostgresInstallation,
    host: str,
    port: int,
) -> bool:
    if not installation.pg_isready.exists():
        return True

    result = subprocess.run(
        [
            str(installation.pg_isready),
            "-h",
            host or "localhost",
            "-p",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=2,
        check=False,
    )
    return result.returncode == 0
