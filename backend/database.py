"""Database connection manager using psycopg2."""

import threading
import decimal
import datetime
import uuid
from typing import Optional, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import errors as pg_errors


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
    """Thread-safe single-connection database manager."""

    def __init__(self):
        self._connection: Optional[psycopg2.extensions.connection] = None
        self._lock = threading.Lock()
        self._info: Dict[str, Any] = {}

    @property
    def is_connected(self) -> bool:
        with self._lock:
            if self._connection is None:
                return False
            try:
                return not self._connection.closed
            except Exception:
                return False

    @property
    def connection_info(self) -> Dict[str, Any]:
        return {**self._info}

    def connect(
        self, host: str, port: int, user: str, password: str, database: str
    ) -> Dict[str, Any]:
        """Establish a new database connection, closing any existing one."""
        with self._lock:
            self._close_internal()
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                )
            except UnicodeDecodeError as exc:
                raw_err = getattr(exc, 'object', None)
                if raw_err and isinstance(raw_err, bytes):
                    msg = raw_err.decode('gbk', errors='replace')
                    raise RuntimeError(msg)
                raise
            conn.autocommit = True
            self._connection = conn
            self._info = {
                "host": host,
                "port": port,
                "user": user,
                "database": database,
            }
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
            return {**self._info, "server_version": version}

    def disconnect(self):
        """Close the current connection."""
        with self._lock:
            self._close_internal()

    def execute(self, query, params=None) -> Dict[str, Any]:
        """Execute SQL and return results as a serializable dict.

        Args:
            query: SQL string or psycopg2.sql.Composed object.
            params: Query parameters for parameterized queries.
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to any database")

        with self._lock:
            try:
                with self._connection.cursor(cursor_factory=RealDictCursor) as cur:
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
                elif "foreign key" in msg.lower():
                    raise RuntimeError("外键引用无效：" + msg)
                elif "not-null" in msg.lower():
                    raise RuntimeError("字段不能为空：" + msg)
                elif "check" in msg.lower():
                    raise RuntimeError("数据校验失败：" + msg)
                else:
                    raise RuntimeError("数据完整性错误：" + msg)

    def _close_internal(self):
        """Close connection without acquiring lock (caller must hold lock)."""
        if self._connection and not self._connection.closed:
            try:
                self._connection.close()
            except Exception:
                pass
        self._connection = None
        self._info = {}


# Singleton instance
db = DatabaseManager()
