from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException


class DummyDB:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple | None]] = []
        self.should_fail = False

    def execute(self, sql: str, params=None):
        self.calls.append((sql, params))
        if self.should_fail:
            raise RuntimeError("synthetic db failure")
        return {"type": "command", "message": "OK", "row_count": 1}


def test_import_benchmark_executes_sql_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from routers import query

    sql_file = tmp_path / "benchmark.sql"
    sql_file.write_text("SELECT 1;", encoding="utf-8")
    dummy_db = DummyDB()

    monkeypatch.setattr(query, "BENCHMARK_SQL_FILE", sql_file, raising=True)
    monkeypatch.setattr(query, "db", dummy_db, raising=True)

    result = query.import_benchmark()

    assert result["ok"] is True
    assert dummy_db.calls == [("SELECT 1;", None)]


def test_import_benchmark_returns_404_when_sql_file_is_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from routers import query

    missing_file = tmp_path / "missing.sql"
    dummy_db = DummyDB()

    monkeypatch.setattr(query, "BENCHMARK_SQL_FILE", missing_file, raising=True)
    monkeypatch.setattr(query, "db", dummy_db, raising=True)

    with pytest.raises(HTTPException) as exc:
        query.import_benchmark()

    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail.lower()
    assert dummy_db.calls == []


def test_delete_benchmark_executes_full_cleanup_script(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from routers import query

    cleanup_file = tmp_path / "cleanup.sql"
    cleanup_file.write_text(
        "\n".join(
            [
                "BEGIN;",
                "DELETE FROM manage_requirement_links WHERE source_req_id LIKE 'breq_%';",
                "DELETE FROM manage_project_members WHERE project_id LIKE 'bproj_%';",
                "COMMIT;",
            ]
        ),
        encoding="utf-8",
    )
    dummy_db = DummyDB()

    monkeypatch.setattr(query, "BENCHMARK_CLEANUP_SQL_FILE", cleanup_file, raising=True)
    monkeypatch.setattr(query, "db", dummy_db, raising=True)

    result = query.delete_benchmark()

    assert result["ok"] is True
    assert len(dummy_db.calls) == 1
    executed_sql, params = dummy_db.calls[0]
    assert "DELETE FROM manage_requirement_links" in executed_sql
    assert "DELETE FROM manage_project_members" in executed_sql
    assert params is None


def test_delete_benchmark_surfaces_database_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from routers import query

    cleanup_file = tmp_path / "cleanup.sql"
    cleanup_file.write_text("BEGIN;\nCOMMIT;", encoding="utf-8")
    dummy_db = DummyDB()
    dummy_db.should_fail = True

    monkeypatch.setattr(query, "BENCHMARK_CLEANUP_SQL_FILE", cleanup_file, raising=True)
    monkeypatch.setattr(query, "db", dummy_db, raising=True)

    with pytest.raises(HTTPException) as exc:
        query.delete_benchmark()

    assert exc.value.status_code == 400
    assert "synthetic db failure" in exc.value.detail
