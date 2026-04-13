"""SQL query execution endpoint."""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import db


router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    sql: str


@router.post("/query")
def execute_query(req: QueryRequest):
    stripped = req.sql.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail="Empty query")

    try:
        result = db.execute(stripped)
        return {"ok": True, **result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/benchmark/import")
def import_benchmark():
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'generate_benchmark_data.sql'))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Benchmark script not found")
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()
    try:
        db.execute(sql)
        return {"ok": True, "message": "测试数据引入成功"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/benchmark/delete")
def delete_benchmark():
    sql = """
    BEGIN;

    DELETE FROM manage_audit_logs WHERE log_id LIKE 'blog_%';
    DELETE FROM manage_change_sets WHERE change_id LIKE 'bcs_%';
    DELETE FROM manage_branches WHERE branch_id LIKE 'bbranch_%';
    DELETE FROM manage_milestone_nodes WHERE snapshot_id LIKE 'bsnap_%';
    DELETE FROM manage_milestones WHERE milestone_id LIKE 'bms_%';
    DELETE FROM manage_defects WHERE defect_id LIKE 'bdef_%';
    DELETE FROM manage_requirement_test_links WHERE requirement_id LIKE 'breq_%'  OR test_case_id LIKE 'btc_%';
    DELETE FROM manage_test_cases WHERE test_case_id LIKE 'btc_%';
    DELETE FROM manage_requirements WHERE req_id LIKE 'breq_%';
    DELETE FROM manage_projects WHERE project_id LIKE 'bproj_%';
    DELETE FROM manage_product_members WHERE product_id LIKE 'bprod_%' OR user_id LIKE 'bench_user_%';
    DELETE FROM manage_products WHERE product_id LIKE 'bprod_%';

    COMMIT;
    """
    try:
        db.execute(sql)
        return {"ok": True, "message": "测试数据删除成功"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
