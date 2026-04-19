from __future__ import annotations

import shutil
import sys
import tempfile
import types
from pathlib import Path
from typing import Any

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _install_psycopg2_stub() -> None:
    if "psycopg2" in sys.modules:
        return
    try:
        __import__("psycopg2")
        return
    except ImportError:
        pass

    psycopg2 = types.ModuleType("psycopg2")

    class IntegrityError(Exception):
        pass

    class DummyConnection:
        closed = False

    class ThreadedConnectionPool:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

        def getconn(self):
            raise RuntimeError("psycopg2 stub pool is not available in tests")

        def putconn(self, conn, close: bool = False) -> None:
            return None

        def closeall(self) -> None:
            return None

    class RealDictCursor:
        pass

    class SQL:
        def __init__(self, text: str) -> None:
            self.text = text

        def format(self, *parts) -> "SQL":
            rendered = self.text
            for part in parts:
                rendered = rendered.replace("{}", str(part), 1)
            return SQL(rendered)

        def __str__(self) -> str:
            return self.text

    class Identifier:
        def __init__(self, *parts: str) -> None:
            self.parts = parts

        def __str__(self) -> str:
            return ".".join(f'"{part}"' for part in self.parts)

    def connect(*args, **kwargs):
        raise RuntimeError("psycopg2 is unavailable in the sandboxed test environment")

    psycopg2.connect = connect

    errors = types.ModuleType("psycopg2.errors")
    errors.IntegrityError = IntegrityError

    extensions = types.ModuleType("psycopg2.extensions")
    extensions.TRANSACTION_STATUS_IDLE = 0
    extensions.connection = DummyConnection

    extras = types.ModuleType("psycopg2.extras")
    extras.RealDictCursor = RealDictCursor

    pool = types.ModuleType("psycopg2.pool")
    pool.ThreadedConnectionPool = ThreadedConnectionPool

    sql = types.ModuleType("psycopg2.sql")
    sql.SQL = SQL
    sql.Identifier = Identifier

    psycopg2.errors = errors
    psycopg2.extensions = extensions
    psycopg2.extras = extras
    psycopg2.pool = pool
    psycopg2.sql = sql

    sys.modules["psycopg2"] = psycopg2
    sys.modules["psycopg2.errors"] = errors
    sys.modules["psycopg2.extensions"] = extensions
    sys.modules["psycopg2.extras"] = extras
    sys.modules["psycopg2.pool"] = pool
    sys.modules["psycopg2.sql"] = sql


_install_psycopg2_stub()


from tests.fake_db import FakeDB


@pytest.fixture
def fake_db() -> FakeDB:
    return FakeDB()


@pytest.fixture
def tmp_path() -> Path:
    base_dir = BACKEND_DIR / ".pytest_tmp"
    base_dir.mkdir(exist_ok=True)
    path = Path(tempfile.mkdtemp(dir=base_dir))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def api_modules(monkeypatch: pytest.MonkeyPatch, fake_db: FakeDB) -> dict[str, object]:
    import database
    from routers import connection, crud, extended_crud, explore, query, statistics

    for module in (database, connection, crud, extended_crud, explore, query, statistics):
        monkeypatch.setattr(module, "db", fake_db, raising=True)

    return {
        "connection": connection,
        "crud": crud,
        "extended_crud": extended_crud,
        "explore": explore,
        "query": query,
        "statistics": statistics,
    }


def pytest_configure(config: pytest.Config) -> None:
    config._constraint_matrix_records = []


@pytest.fixture
def constraint_matrix_recorder(request: pytest.FixtureRequest):
    records: list[dict[str, Any]] = request.config._constraint_matrix_records

    def record(entry: dict[str, Any]) -> None:
        records.append(entry)

    return record


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    records: list[dict[str, Any]] = getattr(config, "_constraint_matrix_records", [])
    if not records:
        return

    total = len(records)
    kind_counts: dict[str, int] = {}
    for record in records:
        kind = str(record.get("kind", "unknown"))
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

    terminalreporter.write_sep("=", "Constraint Integrity Matrix")
    terminalreporter.write_line(f"Collected results: {total}")
    for kind, count in sorted(kind_counts.items()):
        terminalreporter.write_line(f"  {kind}: {count}")

    for record in records:
        case_id = record.get("case_id", "unknown")
        kind = record.get("kind", "unknown")
        outcome = record.get("outcome", "ok")
        detail = record.get("detail", "")
        if detail:
            terminalreporter.write_line(f"  [{kind}] {case_id}: {outcome} - {detail}")
        else:
            terminalreporter.write_line(f"  [{kind}] {case_id}: {outcome}")
