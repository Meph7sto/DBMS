"""Statistics API - exposes views and complex queries."""

from fastapi import APIRouter, HTTPException
from database import db


router = APIRouter(prefix="/api/stats", tags=["statistics"])
DEMO_PROJECT_ID = "bproj_003"
PERFORMANCE_VIEW_SCENARIOS = {
    "projectStats": {
        "label": "v_project_statistics 视图结果",
        "view_sql": (
            "SELECT project_id, project_name, total_requirements, total_defects, completion_rate_percent "
            "FROM v_project_statistics ORDER BY completion_rate_percent DESC LIMIT 8;"
        ),
        "direct_sql": """
WITH req_stats AS (
    SELECT project_id,
           COUNT(*) FILTER (WHERE deleted = FALSE) AS total_requirements,
           COUNT(*) FILTER (WHERE status = 'completed' AND deleted = FALSE) AS completed_count
    FROM manage_requirements
    GROUP BY project_id
),
def_stats AS (
    SELECT project_id, COUNT(*) AS total_defects
    FROM manage_defects
    GROUP BY project_id
)
SELECT p.project_id, p.name AS project_name,
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
ORDER BY completion_rate_percent DESC
LIMIT 8;
""".strip(),
        "pitch": "答辩时先说明页面直接读取 v_project_statistics，再展示展开后的直接 SQL，强调视图把项目级统计口径固定成了统一对象。",
    },
    "requirementDetails": {
        "label": "v_requirement_details 视图结果",
        "view_sql": (
            "SELECT req_id, requirement_title, project_name, test_case_count, defect_count, open_defect_count "
            f"FROM v_requirement_details WHERE project_id = '{DEMO_PROJECT_ID}' "
            "ORDER BY requirement_created_at DESC LIMIT 8;"
        ),
        "direct_sql": f"""
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
SELECT r.req_id,
       r.title AS requirement_title,
       p.name AS project_name,
       COALESCE(ts.test_case_count, 0) AS test_case_count,
       COALESCE(ds.defect_count, 0) AS defect_count,
       COALESCE(ds.open_defect_count, 0) AS open_defect_count
FROM manage_requirements r
JOIN manage_projects p ON p.project_id = r.project_id
LEFT JOIN test_stats ts ON ts.requirement_id = r.req_id
LEFT JOIN defect_stats ds ON ds.requirement_id = r.req_id
WHERE r.project_id = '{DEMO_PROJECT_ID}' AND r.deleted = FALSE
ORDER BY r.created_at DESC
LIMIT 8;
""".strip(),
        "pitch": "答辩时先展示需求详情视图结果，再说明右侧直接 SQL 是等价展开查询，视图减少了页面重复拼接多表聚合 SQL 的负担。",
    },
}


def _raise_statistics_error(exc: Exception):
    message = str(exc)
    if 'relation "' in message.lower() and "does not exist" in message.lower():
        detail = "错误：统计视图或函数尚未初始化，请先执行数据库建模脚本。"
    else:
        detail = f"错误：统计查询执行失败（{message}）"
    raise HTTPException(status_code=400, detail=detail)


def _get_performance_scenario(scenario_key: str):
    scenario = PERFORMANCE_VIEW_SCENARIOS.get(scenario_key)
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"错误：未找到性能演示场景『{scenario_key}』",
        )
    return scenario


@router.get("/performance/guide")
def get_performance_guide():
    return {
        "demo_project_id": DEMO_PROJECT_ID,
        "view_scenarios": PERFORMANCE_VIEW_SCENARIOS,
        "index_demo": {
            "demo_table": "manage_requirements_perf_demo",
            "index_name": "idx_req_perf_project_deleted_order",
            "query_sql": (
                "SELECT req_id, title, status FROM public.manage_requirements_perf_demo "
                f"WHERE project_id = '{DEMO_PROJECT_ID}' AND deleted = FALSE ORDER BY order_index;"
            ),
        },
        "error_demo_route": "/query",
    }


@router.get("/performance/preview/{scenario_key}")
def get_performance_preview(scenario_key: str):
    scenario = _get_performance_scenario(scenario_key)
    try:
        result = db.execute(scenario["view_sql"])
        return {
            "ok": True,
            "scenario_key": scenario_key,
            "label": scenario["label"],
            "view_sql": scenario["view_sql"],
            "direct_sql": scenario["direct_sql"],
            "pitch": scenario["pitch"],
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
        }
    except Exception as exc:
        _raise_statistics_error(exc)


@router.get("/projects")
def list_project_statistics():
    """Return all projects with aggregated statistics from v_project_statistics view."""
    try:
        result = db.execute("SELECT * FROM v_project_statistics ORDER BY project_name")
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        _raise_statistics_error(exc)


@router.get("/project/{project_id}")
def get_project_statistics(project_id: str):
    """Return statistics for a single project."""
    try:
        result = db.execute(
            "SELECT * FROM v_project_statistics WHERE project_id = %s",
            (project_id,),
        )
        if not result["rows"]:
            raise HTTPException(
                status_code=404,
                detail=f"错误：项目ID『{project_id}』不存在",
            )
        return result["rows"][0]
    except HTTPException:
        raise
    except Exception as exc:
        _raise_statistics_error(exc)


@router.get("/project/{project_id}/trace")
def get_requirement_trace(project_id: str):
    """Return requirement traceability for a project (complex query 1)."""
    try:
        result = db.execute(
            "SELECT * FROM fn_requirement_trace(%s)",
            (project_id,),
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        _raise_statistics_error(exc)


@router.get("/project/{project_id}/progress")
def get_project_progress(project_id: str):
    """Return project progress with CTE aggregations (complex query 2)."""
    try:
        result = db.execute(
            "SELECT * FROM fn_project_progress(%s)",
            (project_id,),
        )
        if not result["rows"]:
            raise HTTPException(
                status_code=404,
                detail=f"错误：项目ID『{project_id}』不存在",
            )
        return result["rows"][0]
    except HTTPException:
        raise
    except Exception as exc:
        _raise_statistics_error(exc)


@router.get("/project/{project_id}/milestone-risk")
def get_milestone_delivery_risk(project_id: str):
    """Return milestone delivery risk analysis for a project (complex query 3)."""
    try:
        result = db.execute(
            "SELECT * FROM fn_milestone_delivery_risk(%s)",
            (project_id,),
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        _raise_statistics_error(exc)


@router.get("/requirements/details")
def list_requirement_details(project_id: str = None):
    """Return requirement details view, optionally filtered by project."""
    try:
        if project_id:
            result = db.execute(
                "SELECT * FROM v_requirement_details WHERE project_id = %s "
                "ORDER BY requirement_created_at DESC",
                (project_id,),
            )
        else:
            result = db.execute(
                "SELECT * FROM v_requirement_details ORDER BY requirement_created_at DESC LIMIT 100"
            )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        _raise_statistics_error(exc)
