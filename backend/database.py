"""Database connection manager using psycopg2."""

from contextlib import contextmanager
import datetime
import decimal
import threading
import uuid
from typing import Any, Dict, Iterator, Optional

import psycopg2
from psycopg2 import errors as pg_errors
from psycopg2 import extensions as pg_extensions
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from local_postgres import ensure_local_postgres_ready
from schema_bootstrap import ensure_requirements_schema


def _serialize_value(val):
    """Convert PostgreSQL types to JSON-serializable Python types."""
    if val is None:
        return None
    if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
        return val.isoformat()
    if isinstance(val, datetime.timedelta):
        return str(val)
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, (bytes, memoryview)):
        return bytes(val).hex()
    return val


def _serialize_row(row: dict) -> dict:
    """Serialize all values in a row dict to JSON-safe types."""
    return {k: _serialize_value(v) for k, v in row.items()}


class DatabaseManager:
    """Thread-safe pooled database manager."""

    def __init__(self):
        self._lock = threading.Lock()
        self._idle = threading.Condition(self._lock)
        self._pool: Optional[ThreadedConnectionPool] = None
        self._active_ops = 0
        self._info: Dict[str, Any] = {}
        self._pool_config = {"minconn": 1, "maxconn": 8}

    @property
    def is_connected(self) -> bool:
        with self._lock:
            pool = self._pool
        if pool is None:
            return False

        conn = None
        try:
            conn = pool.getconn()
            return not conn.closed
        except Exception:
            return False
        finally:
            if conn is not None and pool is not None:
                try:
                    pool.putconn(conn)
                except Exception:
                    pass

    @property
    def connection_info(self) -> Dict[str, Any]:
        return {**self._info}

    def connect(
        self, host: str, port: int, user: str, password: str, database: str
    ) -> Dict[str, Any]:
        """Establish a new connection pool, closing any existing one."""
        bootstrap_info = ensure_local_postgres_ready(host, port)
        pool = None
        version = None
        schema_info = None
        with self._lock:
            try:
                pool = ThreadedConnectionPool(
                    minconn=self._pool_config["minconn"],
                    maxconn=self._pool_config["maxconn"],
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                )
            except UnicodeDecodeError as exc:
                raw_err = getattr(exc, "object", None)
                if raw_err and isinstance(raw_err, bytes):
                    msg = raw_err.decode("gbk", errors="replace")
                    raise RuntimeError(msg)
                raise

            test_conn = None
            try:
                test_conn = pool.getconn()
                test_conn.autocommit = True
                with test_conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
                schema_info = ensure_requirements_schema(test_conn)
            except Exception:
                if test_conn is not None:
                    try:
                        pool.putconn(test_conn, close=True)
                    except Exception:
                        pass
                pool.closeall()
                raise
            else:
                if test_conn is not None:
                    pool.putconn(test_conn)

            self._wait_for_active_ops_locked()
            self._close_internal_locked()
            self._pool = pool
            self._info = {
                "host": host,
                "port": port,
                "user": user,
                "database": database,
                "pool_max_connections": self._pool_config["maxconn"],
            }
            if bootstrap_info is not None:
                self._info["local_postgres"] = bootstrap_info
            if schema_info is not None:
                self._info["schema"] = schema_info
            return {**self._info, "server_version": version}

    def disconnect(self):
        """Close the current connection pool."""
        with self._lock:
            self._wait_for_active_ops_locked()
            self._close_internal_locked()

    def execute(self, query, params=None) -> Dict[str, Any]:
        """Execute SQL and return results as a serializable dict.

        Args:
            query: SQL string or psycopg2.sql.Composed object.
            params: Query parameters for parameterized queries.
        """
        try:
            with self._connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        rows = [_serialize_row(dict(r)) for r in cur.fetchall()]
                        return {
                            "type": "result",
                            "columns": columns,
                            "rows": rows,
                            "row_count": len(rows),
                        }
                    return {
                        "type": "command",
                        "message": f"OK — {cur.rowcount} row(s) affected",
                        "row_count": cur.rowcount,
                    }
        except pg_errors.IntegrityError as exc:
            # Translate psycopg2 IntegrityError to Chinese messages
            msg = str(exc)
            if "unique" in msg.lower() or "duplicate" in msg.lower():
                raise RuntimeError("违反唯一约束：" + msg)
            if "foreign key" in msg.lower():
                raise RuntimeError("外键引用无效：" + msg)
            if "not-null" in msg.lower():
                raise RuntimeError("字段不能为空：" + msg)
            if "check" in msg.lower():
                raise RuntimeError("数据校验失败：" + msg)
            raise RuntimeError("数据完整性错误：" + msg)

    @contextmanager
    def _connection(self) -> Iterator[psycopg2.extensions.connection]:
        """Borrow a connection from the pool for the duration of one operation."""
        with self._lock:
            if self._pool is None:
                raise RuntimeError("Not connected to any database")
            pool = self._pool
            self._active_ops += 1

        conn = None
        try:
            conn = pool.getconn()
            conn.autocommit = True
            yield conn
        finally:
            if conn is not None:
                try:
                    if (
                        not conn.closed
                        and conn.info.transaction_status
                        != pg_extensions.TRANSACTION_STATUS_IDLE
                    ):
                        conn.rollback()
                except Exception:
                    pass
                try:
                    pool.putconn(conn)
                except Exception:
                    pass
            with self._lock:
                self._active_ops -= 1
                if self._active_ops == 0:
                    self._idle.notify_all()

    def _wait_for_active_ops_locked(self):
        """Wait until all borrowed connections have been returned."""
        while self._active_ops > 0:
            self._idle.wait()

    def _close_internal_locked(self):
        """Close the pool without acquiring the lock (caller must hold lock)."""
        if self._pool is not None:
            try:
                self._pool.closeall()
            except Exception:
                pass
        self._pool = None
        self._info = {}


# Singleton instance
db = DatabaseManager()
