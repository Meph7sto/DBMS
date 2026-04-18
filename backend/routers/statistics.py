"""Statistics API - exposes views and complex queries."""

from fastapi import APIRouter, HTTPException
from database import db


router = APIRouter(prefix="/api/stats", tags=["statistics"])


@router.get("/projects")
def list_project_statistics():
    """Return all projects with aggregated statistics from v_project_statistics view."""
    try:
        result = db.execute("SELECT * FROM v_project_statistics ORDER BY project_name")
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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
        raise HTTPException(status_code=400, detail=str(exc))


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
        raise HTTPException(status_code=400, detail=str(exc))


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
        raise HTTPException(status_code=400, detail=str(exc))


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
        raise HTTPException(status_code=400, detail=str(exc))


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
        raise HTTPException(status_code=400, detail=str(exc))
