"""SQL query execution endpoint."""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import db


router = APIRouter(tags=["query"])
DB_DIR = Path(__file__).resolve().parents[2] / "db"
BENCHMARK_SQL_FILE = DB_DIR / "generate_benchmark_data.sql"
BENCHMARK_CLEANUP_SQL_FILE = DB_DIR / "cleanup_benchmark_data.sql"
VISIBLE_DEMO_SQL_FILE = DB_DIR / "visible_demo_data.sql"
VISIBLE_DEMO_CLEANUP_SQL_FILE = DB_DIR / "visible_demo_data_cleanup.sql"


class QueryRequest(BaseModel):
    sql: str


def _raise_query_error(exc: Exception):
    message = str(exc)
    if 'relation "' in message.lower() and "does not exist" in message.lower():
        detail = "错误：当前数据库尚未完成需求管理 schema 初始化，请先执行建库脚本。"
    else:
        detail = f"错误：SQL 执行失败（{message}）"
    raise HTTPException(status_code=400, detail=detail)


def _execute_sql_file(path: Path, missing_detail: str):
    if not path.exists():
        raise HTTPException(status_code=404, detail=missing_detail)
    sql = path.read_text(encoding="utf-8")
    try:
        db.execute(sql)
    except Exception as exc:
        _raise_query_error(exc)


@router.post("/query")
def execute_query(req: QueryRequest):
    stripped = req.sql.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail="错误：SQL 语句不能为空")

    try:
        result = db.execute(stripped)
        return {"ok": True, **result}
    except Exception as exc:
        _raise_query_error(exc)


@router.post("/benchmark/import")
def import_benchmark():
    _execute_sql_file(BENCHMARK_SQL_FILE, "错误：未找到 benchmark 导入脚本")
    return {"ok": True, "message": "benchmark 测试数据导入成功"}

@router.post("/benchmark/delete")
def delete_benchmark():
    _execute_sql_file(BENCHMARK_CLEANUP_SQL_FILE, "错误：未找到 benchmark 清理脚本")
    return {"ok": True, "message": "benchmark 测试数据删除成功"}


@router.get("/benchmark/summary")
def get_benchmark_summary():
    try:
        result = db.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM manage_products WHERE product_id LIKE 'bprod_%') AS products,
                (SELECT COUNT(*) FROM manage_product_members WHERE product_id LIKE 'bprod_%') AS product_members,
                (SELECT COUNT(*) FROM manage_projects WHERE project_id LIKE 'bproj_%') AS projects,
                (SELECT COUNT(*) FROM manage_project_members WHERE project_id LIKE 'bproj_%') AS project_members,
                (SELECT COUNT(*) FROM manage_requirements WHERE req_id LIKE 'breq_%') AS requirements,
                (SELECT COUNT(*) FROM manage_requirement_links WHERE source_req_id LIKE 'breq_%' OR target_req_id LIKE 'breq_%') AS requirement_links,
                (SELECT COUNT(*) FROM manage_test_cases WHERE test_case_id LIKE 'btc_%') AS test_cases,
                (SELECT COUNT(*) FROM manage_requirement_test_links WHERE requirement_id LIKE 'breq_%' OR test_case_id LIKE 'btc_%') AS requirement_test_links,
                (SELECT COUNT(*) FROM manage_defects WHERE defect_id LIKE 'bdef_%') AS defects,
                (SELECT COUNT(*) FROM manage_milestones WHERE milestone_id LIKE 'bms_%') AS milestones,
                (SELECT COUNT(*) FROM manage_milestone_nodes WHERE snapshot_id LIKE 'bsnap_%') AS milestone_nodes,
                (SELECT COUNT(*) FROM manage_branches WHERE branch_id LIKE 'bbranch_%') AS branches,
                (SELECT COUNT(*) FROM manage_change_sets WHERE change_id LIKE 'bcs_%') AS change_sets,
                (SELECT COUNT(*) FROM manage_audit_logs WHERE log_id LIKE 'blog_%') AS audit_logs
            """
        )
        summary = result["rows"][0] if result["rows"] else {}
        total_records = sum(int(value or 0) for value in summary.values())
        return {
            "ok": True,
            "summary": {
                **summary,
                "total_records": total_records,
                "has_benchmark_data": total_records > 0,
            },
        }
    except Exception as exc:
        _raise_query_error(exc)


@router.post("/demo/import")
def import_visible_demo_data():
    _execute_sql_file(VISIBLE_DEMO_SQL_FILE, "错误：未找到演示数据导入脚本")
    return {"ok": True, "message": "演示数据引入成功"}


@router.post("/demo/delete")
def delete_visible_demo_data():
    _execute_sql_file(VISIBLE_DEMO_CLEANUP_SQL_FILE, "错误：未找到演示数据清理脚本")
    return {"ok": True, "message": "演示数据删除成功"}
