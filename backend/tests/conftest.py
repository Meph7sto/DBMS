from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _install_psycopg2_stub() -> None:
    if "psycopg2" in sys.modules:
        return

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
