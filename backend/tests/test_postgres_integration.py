from __future__ import annotations

from typing import Any

import pytest

from config import get_default_connection
from database import DatabaseManager
from routers import query, statistics


DEMO_PROJECT_ID = "bproj_003"
DEMO_TABLE = "manage_requirements_perf_demo"
DEMO_INDEX = "idx_req_perf_project_deleted_order"

PROJECT_STATS_DIRECT_SQL = f"""
WITH req_stats AS (
    SELECT project_id,
           COUNT(*) FILTER (WHERE deleted = FALSE) AS total_requirements,
           COUNT(*) FILTER (WHERE requirement_type = 'top_level' AND deleted = FALSE) AS top_level_count,
           COUNT(*) FILTER (WHERE requirement_type = 'low_level' AND deleted = FALSE) AS low_level_count,
           COUNT(*) FILTER (WHERE status = 'completed' AND deleted = FALSE) AS completed_count,
           COUNT(*) FILTER (WHERE status = 'in_progress' AND deleted = FALSE) AS in_progress_count,
           COUNT(*) FILTER (WHERE status = 'draft' AND deleted = FALSE) AS draft_count
    FROM manage_requirements
    GROUP BY project_id
),
def_stats AS (
    SELECT project_id,
           COUNT(*) AS total_defects,
           COUNT(*) FILTER (WHERE severity = 'critical') AS critical_defects,
           COUNT(*) FILTER (WHERE status IN ('open', 'in_progress')) AS open_defects
    FROM manage_defects
    GROUP BY project_id
),
tc_stats AS (
    SELECT project_id, COUNT(*) AS total_test_cases
    FROM manage_test_cases
    GROUP BY project_id
),
ms_stats AS (
    SELECT project_id,
           COUNT(*) AS total_milestones,
           COUNT(*) FILTER (WHERE is_baseline = TRUE) AS baseline_count
    FROM manage_milestones
    GROUP BY project_id
),
br_stats AS (
    SELECT project_id, COUNT(*) AS total_branches
    FROM manage_branches
    GROUP BY project_id
)
SELECT
    p.project_id,
    p.name AS project_name,
    COALESCE(r.total_requirements, 0) AS total_requirements,
    COALESCE(d.total_defects, 0) AS total_defects,
    CASE
        WHEN COALESCE(r.total_requirements, 0) > 0
        THEN ROUND((COALESCE(r.completed_count, 0)::NUMERIC / r.total_requirements) * 100, 2)
        ELSE 0
    END AS completion_rate_percent
FROM manage_projects p
LEFT JOIN req_stats r ON r.project_id = p.project_id
LEFT JOIN def_stats d ON d.project_id = p.project_id
LEFT JOIN tc_stats tc ON tc.project_id = p.project_id
LEFT JOIN ms_stats m ON m.project_id = p.project_id
LEFT JOIN br_stats b ON b.project_id = p.project_id
WHERE p.project_id = '{DEMO_PROJECT_ID}';
""".strip()

REQUIREMENT_DETAILS_DIRECT_SQL = f"""
WITH test_stats AS (
    SELECT requirement_id, COUNT(DISTINCT test_case_id) AS test_case_count
    FROM manage_requirement_test_links
    GROUP BY requirement_id
),
defect_stats AS (
    SELECT requirement_id,
           COUNT(DISTINCT defect_id) AS defect_count,
           COUNT(DISTINCT CASE WHEN status IN ('open', 'in_progress') THEN defect_id END) AS open_defect_count
    FROM manage_defects
    GROUP BY requirement_id
)
SELECT
    r.req_id,
    r.title AS requirement_title,
    p.name AS project_name,
    COALESCE(ts.test_case_count, 0) AS test_case_count,
    COALESCE(ds.defect_count, 0) AS defect_count,
    COALESCE(ds.open_defect_count, 0) AS open_defect_count
FROM manage_requirements r
JOIN manage_projects p ON p.project_id = r.project_id
LEFT JOIN test_stats ts ON ts.requirement_id = r.req_id
LEFT JOIN defect_stats ds ON ds.requirement_id = r.req_id
WHERE r.deleted = FALSE
  AND r.project_id = '{DEMO_PROJECT_ID}'
ORDER BY r.created_at DESC
LIMIT 8;
""".strip()


def _cleanup_demo_objects(db: DatabaseManager) -> None:
    db.execute(f"DROP INDEX IF EXISTS public.{DEMO_INDEX}")
    db.execute(f"DROP TABLE IF EXISTS public.{DEMO_TABLE}")


def _plan_lines(result: dict[str, Any]) -> list[str]:
    return [row["QUERY PLAN"] for row in result["rows"] if "QUERY PLAN" in row]


@pytest.fixture(scope="module")
def real_postgres_env() -> dict[str, Any]:
    settings = get_default_connection()
    db = DatabaseManager()
    db.connect(**settings)

    original_query_db = query.db
    original_statistics_db = statistics.db
    query.db = db
    statistics.db = db

    try:
        query.delete_benchmark()
    except Exception:
        pass
    _cleanup_demo_objects(db)
    query.import_benchmark()

    try:
        yield {"db": db, "query": query, "statistics": statistics}
    finally:
        _cleanup_demo_objects(db)
        try:
            query.delete_benchmark()
        except Exception:
            pass
        query.db = original_query_db
        statistics.db = original_statistics_db
        db.disconnect()


@pytest.fixture(autouse=True)
def cleanup_demo_objects_between_tests(real_postgres_env) -> None:
    db = real_postgres_env["db"]
    _cleanup_demo_objects(db)
    try:
        yield
    finally:
        _cleanup_demo_objects(db)


def test_benchmark_import_and_summary_against_real_postgres(real_postgres_env) -> None:
    summary = real_postgres_env["query"].get_benchmark_summary()["summary"]

    assert summary == {
        "products": 10,
        "product_members": 60,
        "projects": 20,
        "project_members": 120,
        "requirements": 10000,
        "requirement_links": 1000,
        "test_cases": 500,
        "requirement_test_links": 500,
        "defects": 500,
        "milestones": 100,
        "milestone_nodes": 1000,
        "branches": 200,
        "change_sets": 1000,
        "audit_logs": 2000,
        "total_records": 17010,
        "has_benchmark_data": True,
    }


def test_views_match_direct_sql_against_real_postgres(real_postgres_env) -> None:
    db = real_postgres_env["db"]

    project_view = db.execute(
        """
        SELECT project_id, project_name, total_requirements, total_defects, completion_rate_percent
        FROM v_project_statistics
        WHERE project_id = %s
        """,
        (DEMO_PROJECT_ID,),
    )
    project_direct = db.execute(PROJECT_STATS_DIRECT_SQL)
    assert project_view["rows"] == project_direct["rows"]

    requirement_view = db.execute(
        """
        SELECT req_id, requirement_title, project_name, test_case_count, defect_count, open_defect_count
        FROM v_requirement_details
        WHERE project_id = %s
        ORDER BY requirement_created_at DESC
        LIMIT 8
        """,
        (DEMO_PROJECT_ID,),
    )
    requirement_direct = db.execute(REQUIREMENT_DETAILS_DIRECT_SQL)
    assert requirement_view["rows"] == requirement_direct["rows"]


def test_complex_query_functions_against_real_postgres(real_postgres_env) -> None:
    db = real_postgres_env["db"]
    stats = real_postgres_env["statistics"]

    progress = stats.get_project_progress(DEMO_PROJECT_ID)
    trace = stats.get_requirement_trace(DEMO_PROJECT_ID)
    risk = stats.get_milestone_delivery_risk(DEMO_PROJECT_ID)

    expected_requirement_count = db.execute(
        "SELECT COUNT(*) AS c FROM manage_requirements WHERE project_id = %s AND deleted = FALSE",
        (DEMO_PROJECT_ID,),
    )["rows"][0]["c"]
    expected_defect_count = db.execute(
        "SELECT COUNT(*) AS c FROM manage_defects WHERE project_id = %s",
        (DEMO_PROJECT_ID,),
    )["rows"][0]["c"]
    expected_milestone_count = db.execute(
        "SELECT COUNT(*) AS c FROM manage_milestones WHERE project_id = %s",
        (DEMO_PROJECT_ID,),
    )["rows"][0]["c"]

    assert progress["project_id"] == DEMO_PROJECT_ID
    assert progress["total_requirements"] == expected_requirement_count
    assert progress["total_defects"] == expected_defect_count
    assert trace["total"] == expected_requirement_count
    assert risk["total"] == expected_milestone_count
    assert {
        "req_id",
        "requirement_title",
        "test_case_count",
        "total_defect_count",
        "open_defect_count",
    }.issubset(trace["items"][0].keys())
    assert {
        "milestone_id",
        "risk_score",
        "risk_level",
        "pending_change_count",
    }.issubset(risk["items"][0].keys())


def test_explain_analyze_uses_index_against_real_postgres(real_postgres_env) -> None:
    db = real_postgres_env["db"]

    _cleanup_demo_objects(db)
    try:
        db.execute(
            f"""
            CREATE TABLE public.{DEMO_TABLE} AS
            SELECT *
            FROM public.manage_requirements
            WHERE req_id LIKE 'breq_%'
            """
        )
        db.execute(f"ANALYZE public.{DEMO_TABLE}")

        before = db.execute(
            f"""
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT req_id, title, status
            FROM public.{DEMO_TABLE}
            WHERE project_id = '{DEMO_PROJECT_ID}' AND deleted = FALSE
            ORDER BY order_index
            """
        )
        before_lines = _plan_lines(before)
        assert any("Seq Scan on manage_requirements_perf_demo" in line for line in before_lines)

        db.execute(
            f"""
            CREATE INDEX IF NOT EXISTS {DEMO_INDEX}
            ON public.{DEMO_TABLE}(project_id, deleted, order_index)
            """
        )
        db.execute(f"ANALYZE public.{DEMO_TABLE}")

        after = db.execute(
            f"""
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT req_id, title, status
            FROM public.{DEMO_TABLE}
            WHERE project_id = '{DEMO_PROJECT_ID}' AND deleted = FALSE
            ORDER BY order_index
            """
        )
        after_lines = _plan_lines(after)
        assert any(
            "Bitmap Heap Scan on manage_requirements_perf_demo" in line
            or "Index Scan using idx_req_perf_project_deleted_order" in line
            for line in after_lines
        )
        assert any(DEMO_INDEX in line for line in after_lines)
    finally:
        _cleanup_demo_objects(db)
