"""CRUD API with application-layer integrity constraints and Chinese error messages."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from database import db
import uuid


router = APIRouter(prefix="/api/crud", tags=["crud"])


# ─── 中文错误消息映射 ────────────────────────────────────────

ERROR_MESSAGES = {
    "empty_name": "错误：名称不能为空",
    "empty_title": "错误：标题不能为空",
    "empty_required_field": "错误：必填字段『{field}』不能为空",
    "duplicate_name": "错误：名称『{name}』已存在，请使用其他名称",
    "product_not_found": "错误：指定的产品ID『{id}』不存在，无法创建项目",
    "parent_req_not_found": "错误：父需求ID『{id}』不存在，无法创建子需求",
    "project_not_found": "错误：指定的项目ID『{id}』不存在",
    "requirement_not_found": "错误：指定的需求ID『{id}』不存在",
    "defect_not_found": "错误：指定的缺陷ID『{id}』不存在",
    "test_case_not_found": "错误：指定的测试用例ID『{id}』不存在",
    "milestone_not_found": "错误：指定的里程碑ID『{id}』不存在",
    "invalid_status": "错误：状态值『{value}』不在允许的范围内（{allowed}）",
    "invalid_severity": "错误：严重程度『{value}』不在允许的范围内（critical/high/medium/low）",
    "invalid_priority": "错误：优先级『{value}』不在允许的范围内（P0/P1/P2/P3）",
    "invalid_role": "错误：角色『{value}』不在允许的范围内（owner/admin/member/viewer）",
    "fk_violation": "错误：外键引用无效（{detail}）",
    "unique_violation": "错误：违反唯一约束（{detail}）",
    "not_null_violation": "错误：字段『{column}』不能为空",
    "internal_error": "错误：服务器内部错误（{detail}）",
}


def err(key: str, **kwargs) -> str:
    return ERROR_MESSAGES.get(key, key).format(**kwargs)


def handle_db_error(exc: Exception) -> HTTPException:
    """Translate psycopg2 errors to Chinese error messages."""
    msg = str(exc)
    if "duplicate key" in msg.lower() or "unique" in msg.lower():
        return HTTPException(status_code=400, detail=err("unique_violation", detail=msg))
    if "fk_violation" in msg.lower() or "foreign key" in msg.lower():
        return HTTPException(status_code=400, detail=err("fk_violation", detail=msg))
    if "not_null" in msg.lower():
        return HTTPException(status_code=400, detail=err("not_null_violation", detail=msg))
    return HTTPException(status_code=400, detail=err("internal_error", detail=msg))


# ─── 通用响应模型 ────────────────────────────────────────────

class ItemResponse(BaseModel):
    id: str
    ok: bool = True


class ListResponse(BaseModel):
    items: List[Any]
    total: int


# ─── 产品 CRUD ───────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: str = "active"
    roadmap: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = []
    created_by: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    roadmap: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None


VALID_PRODUCT_STATUS = {"active", "archived"}
VALID_ROLES = {"owner", "admin", "member", "viewer"}


@router.get("/products")
def list_products():
    try:
        result = db.execute(
            "SELECT * FROM manage_products ORDER BY created_at DESC"
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/products")
def create_product(item: ProductCreate):
    if not item.name or not item.name.strip():
        raise HTTPException(status_code=400, detail=err("empty_name"))
    if item.status not in VALID_PRODUCT_STATUS:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_status", value=item.status, allowed="active/archived"),
        )
    product_id = f"prod_{uuid.uuid4().hex[:8]}"
    try:
        result = db.execute(
            """INSERT INTO manage_products
               (product_id, name, description, status, roadmap, version, tags, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s::JSONB, %s)""",
            (product_id, item.name.strip(), item.description, item.status,
             item.roadmap, item.version, item.tags, item.created_by),
        )
        return {"ok": True, "id": product_id}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/products/{product_id}")
def update_product(product_id: str, item: ProductUpdate):
    if item.status is not None and item.status not in VALID_PRODUCT_STATUS:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_status", value=item.status, allowed="active/archived"),
        )
    sets, params = [], []
    for field, value in [
        ("name", item.name), ("description", item.description),
        ("status", item.status), ("roadmap", item.roadmap),
        ("version", item.version), ("tags", item.tags),
    ]:
        if value is not None:
            sets.append(f"{field} = %s" if field != "tags" else f"{field} = %s::JSONB")
            params.append(value)
    if not sets:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")
    params.append(product_id)
    try:
        result = db.execute(
            f"UPDATE manage_products SET {', '.join(sets)}, updated_at = NOW() "
            f"WHERE product_id = %s",
            tuple(params),
        )
        if result["row_count"] == 0:
            raise HTTPException(status_code=404, detail=err("product_not_found", id=product_id))
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/products/{product_id}")
def delete_product(product_id: str):
    try:
        result = db.execute(
            "DELETE FROM manage_products WHERE product_id = %s",
            (product_id,),
        )
        if result["row_count"] == 0:
            raise HTTPException(status_code=404, detail=err("product_not_found", id=product_id))
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise handle_db_error(exc)


# ─── 项目 CRUD ───────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: str = "active"
    product_id: Optional[str] = None
    created_by: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    product_id: Optional[str] = None


VALID_PROJECT_STATUS = {"active", "archived"}


@router.get("/projects")
def list_projects():
    try:
        result = db.execute(
            """SELECT p.*, pr.name as product_name
               FROM manage_projects p
               LEFT JOIN manage_products pr ON pr.product_id = p.product_id
               ORDER BY p.created_at DESC"""
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/projects")
def create_project(item: ProjectCreate):
    if not item.name or not item.name.strip():
        raise HTTPException(status_code=400, detail=err("empty_name"))
    if item.status not in VALID_PROJECT_STATUS:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_status", value=item.status, allowed="active/archived"),
        )
    if item.product_id:
        check = db.execute(
            "SELECT 1 FROM manage_products WHERE product_id = %s",
            (item.product_id,),
        )
        if not check["rows"]:
            raise HTTPException(
                status_code=400,
                detail=err("product_not_found", id=item.product_id),
            )
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    try:
        db.execute(
            """INSERT INTO manage_projects
               (project_id, name, description, status, product_id, created_by)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (project_id, item.name.strip(), item.description, item.status,
             item.product_id, item.created_by),
        )
        return {"ok": True, "id": project_id}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/projects/{project_id}")
def update_project(project_id: str, item: ProjectUpdate):
    if item.status is not None and item.status not in VALID_PROJECT_STATUS:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_status", value=item.status, allowed="active/archived"),
        )
    if item.product_id is not None:
        check = db.execute(
            "SELECT 1 FROM manage_products WHERE product_id = %s",
            (item.product_id,),
        )
        if not check["rows"]:
            raise HTTPException(
                status_code=400,
                detail=err("product_not_found", id=item.product_id),
            )
    sets, params = [], []
    for field, value in [
        ("name", item.name), ("description", item.description),
        ("status", item.status), ("product_id", item.product_id),
    ]:
        if value is not None:
            sets.append(f"{field} = %s")
            params.append(value)
    if not sets:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")
    params.append(project_id)
    try:
        result = db.execute(
            f"UPDATE manage_projects SET {', '.join(sets)}, updated_at = NOW() "
            f"WHERE project_id = %s",
            tuple(params),
        )
        if result["row_count"] == 0:
            raise HTTPException(status_code=404, detail=err("project_not_found", id=project_id))
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/projects/{project_id}")
def delete_project(project_id: str):
    try:
        result = db.execute(
            "DELETE FROM manage_projects WHERE project_id = %s",
            (project_id,),
        )
        if result["row_count"] == 0:
            raise HTTPException(status_code=404, detail=err("project_not_found", id=project_id))
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise handle_db_error(exc)


# ─── 需求 CRUD ───────────────────────────────────────────────

class RequirementCreate(BaseModel):
    project_id: str = Field(..., min_length=1)
    requirement_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: str = "draft"
    priority: Optional[str] = None
    assignee: Optional[str] = None
    parent_id: Optional[str] = None
    order_index: int = 0
    created_by: Optional[str] = None


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    parent_id: Optional[str] = None
    order_index: Optional[int] = None


VALID_REQ_TYPES = {"top_level", "low_level", "task"}
VALID_REQ_STATUS = {"draft", "under_review", "confirmed", "in_progress", "completed", "archived"}
VALID_PRIORITIES = {"low", "medium", "high"}


@router.get("/requirements")
def list_requirements(project_id: Optional[str] = None):
    try:
        if project_id:
            result = db.execute(
                """SELECT r.*, p.name as project_name
                   FROM manage_requirements r
                   JOIN manage_projects p ON p.project_id = r.project_id
                   WHERE r.project_id = %s AND r.deleted = FALSE
                   ORDER BY r.order_index""",
                (project_id,),
            )
        else:
            result = db.execute(
                """SELECT r.*, p.name as project_name
                   FROM manage_requirements r
                   JOIN manage_projects p ON p.project_id = r.project_id
                   WHERE r.deleted = FALSE
                   ORDER BY r.created_at DESC
                   LIMIT 100""",
            )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/requirements")
def create_requirement(item: RequirementCreate):
    if not item.title or not item.title.strip():
        raise HTTPException(status_code=400, detail=err("empty_title"))
    if item.requirement_type not in VALID_REQ_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"错误：需求类型『{item.requirement_type}』不在允许的范围内（top_level/low_level/task）",
        )
    if item.status not in VALID_REQ_STATUS:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_status", value=item.status,
                       allowed="draft/under_review/confirmed/in_progress/completed/archived"),
        )
    if item.priority and item.priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_priority", value=item.priority),
        )
    check = db.execute(
        "SELECT 1 FROM manage_projects WHERE project_id = %s",
        (item.project_id,),
    )
    if not check["rows"]:
        raise HTTPException(status_code=400, detail=err("project_not_found", id=item.project_id))
    if item.parent_id:
        check = db.execute(
            "SELECT 1 FROM manage_requirements WHERE req_id = %s",
            (item.parent_id,),
        )
        if not check["rows"]:
            raise HTTPException(status_code=400, detail=err("parent_req_not_found", id=item.parent_id))
    req_id = f"req_{uuid.uuid4().hex[:8]}"
    try:
        db.execute(
            """INSERT INTO manage_requirements
               (req_id, project_id, requirement_type, title, description, status,
                priority, assignee, parent_id, order_index, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (req_id, item.project_id, item.requirement_type, item.title.strip(),
             item.description, item.status, item.priority, item.assignee,
             item.parent_id, item.order_index, item.created_by),
        )
        return {"ok": True, "id": req_id}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/requirements/{req_id}")
def update_requirement(req_id: str, item: RequirementUpdate):
    if item.status is not None and item.status not in VALID_REQ_STATUS:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_status", value=item.status,
                       allowed="draft/under_review/confirmed/in_progress/completed/archived"),
        )
    if item.priority is not None and item.priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_priority", value=item.priority),
        )
    if item.parent_id is not None:
        check = db.execute(
            "SELECT 1 FROM manage_requirements WHERE req_id = %s",
            (item.parent_id,),
        )
        if not check["rows"]:
            raise HTTPException(status_code=400, detail=err("parent_req_not_found", id=item.parent_id))
    sets, params = [], []
    for field, value in [
        ("title", item.title), ("description", item.description),
        ("status", item.status), ("priority", item.priority),
        ("assignee", item.assignee), ("parent_id", item.parent_id),
        ("order_index", item.order_index),
    ]:
        if value is not None:
            sets.append(f"{field} = %s")
            params.append(value)
    if not sets:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")
    params.extend([req_id, False])
    try:
        result = db.execute(
            f"UPDATE manage_requirements SET {', '.join(sets)}, updated_at = NOW() "
            f"WHERE req_id = %s AND deleted = %s",
            tuple(params),
        )
        if result["row_count"] == 0:
            raise HTTPException(status_code=404, detail=err("requirement_not_found", id=req_id))
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/requirements/{req_id}")
def delete_requirement(req_id: str):
    try:
        result = db.execute(
            "UPDATE manage_requirements SET deleted = TRUE, updated_at = NOW() "
            "WHERE req_id = %s AND deleted = FALSE",
            (req_id,),
        )
        if result["row_count"] == 0:
            raise HTTPException(status_code=404, detail=err("requirement_not_found", id=req_id))
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise handle_db_error(exc)


# ─── 缺陷 CRUD ───────────────────────────────────────────────

class DefectCreate(BaseModel):
    project_id: str = Field(..., min_length=1)
    requirement_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    reproduce_steps: str = ""
    severity: str = "medium"
    priority: str = "P2"
    status: str = "open"
    reporter: Optional[str] = None
    current_assignee: Optional[str] = None
    created_by: Optional[str] = None


class DefectUpdate(BaseModel):
    title: Optional[str] = None
    reproduce_steps: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    current_assignee: Optional[str] = None


VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_DEFECT_STATUS = {"open", "in_progress", "resolved", "verified", "closed", "rejected"}


@router.get("/defects")
def list_defects(project_id: Optional[str] = None):
    try:
        if project_id:
            result = db.execute(
                """SELECT d.*, r.title as requirement_title, p.name as project_name
                   FROM manage_defects d
                   JOIN manage_projects p ON p.project_id = d.project_id
                   LEFT JOIN manage_requirements r ON r.req_id = d.requirement_id
                   WHERE d.project_id = %s
                   ORDER BY d.created_at DESC""",
                (project_id,),
            )
        else:
            result = db.execute(
                """SELECT d.*, r.title as requirement_title, p.name as project_name
                   FROM manage_defects d
                   JOIN manage_projects p ON p.project_id = d.project_id
                   LEFT JOIN manage_requirements r ON r.req_id = d.requirement_id
                   ORDER BY d.created_at DESC
                   LIMIT 100""",
            )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/defects")
def create_defect(item: DefectCreate):
    if not item.title or not item.title.strip():
        raise HTTPException(status_code=400, detail=err("empty_title"))
    if item.severity not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail=err("invalid_severity", value=item.severity))
    if item.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=err("invalid_priority", value=item.priority))
    if item.status not in VALID_DEFECT_STATUS:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_status", value=item.status,
                       allowed="open/in_progress/resolved/verified/closed/rejected"),
        )
    check = db.execute(
        "SELECT 1 FROM manage_projects WHERE project_id = %s",
        (item.project_id,),
    )
    if not check["rows"]:
        raise HTTPException(status_code=400, detail=err("project_not_found", id=item.project_id))
    check = db.execute(
        "SELECT 1 FROM manage_requirements WHERE req_id = %s",
        (item.requirement_id,),
    )
    if not check["rows"]:
        raise HTTPException(status_code=400, detail=err("requirement_not_found", id=item.requirement_id))
    defect_id = f"def_{uuid.uuid4().hex[:8]}"
    try:
        db.execute(
            """INSERT INTO manage_defects
               (defect_id, project_id, requirement_id, title, reproduce_steps,
                severity, priority, status, reporter, current_assignee, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (defect_id, item.project_id, item.requirement_id, item.title.strip(),
             item.reproduce_steps, item.severity, item.priority, item.status,
             item.reporter, item.current_assignee, item.created_by),
        )
        return {"ok": True, "id": defect_id}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/defects/{defect_id}")
def update_defect(defect_id: str, item: DefectUpdate):
    if item.severity is not None and item.severity not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail=err("invalid_severity", value=item.severity))
    if item.priority is not None and item.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=err("invalid_priority", value=item.priority))
    if item.status is not None and item.status not in VALID_DEFECT_STATUS:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_status", value=item.status,
                       allowed="open/in_progress/resolved/verified/closed/rejected"),
        )
    sets, params = [], []
    for field, value in [
        ("title", item.title), ("reproduce_steps", item.reproduce_steps),
        ("severity", item.severity), ("priority", item.priority),
        ("status", item.status), ("current_assignee", item.current_assignee),
    ]:
        if value is not None:
            sets.append(f"{field} = %s")
            params.append(value)
    if not sets:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")
    params.append(defect_id)
    try:
        result = db.execute(
            f"UPDATE manage_defects SET {', '.join(sets)}, updated_at = NOW() "
            f"WHERE defect_id = %s",
            tuple(params),
        )
        if result["row_count"] == 0:
            raise HTTPException(status_code=404, detail=err("defect_not_found", id=defect_id))
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise handle_db_error(exc)


# ─── 测试用例 CRUD ───────────────────────────────────────────

class TestCaseCreate(BaseModel):
    project_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: str = "draft"
    source: Optional[str] = None
    created_by: Optional[str] = None


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


VALID_TC_STATUS = {"draft", "active", "deprecated"}


@router.get("/test-cases")
def list_test_cases(project_id: Optional[str] = None):
    try:
        if project_id:
            result = db.execute(
                """SELECT tc.*, p.name as project_name
                   FROM manage_test_cases tc
                   JOIN manage_projects p ON p.project_id = tc.project_id
                   WHERE tc.project_id = %s
                   ORDER BY tc.created_at DESC""",
                (project_id,),
            )
        else:
            result = db.execute(
                """SELECT tc.*, p.name as project_name
                   FROM manage_test_cases tc
                   JOIN manage_projects p ON p.project_id = tc.project_id
                   ORDER BY tc.created_at DESC
                   LIMIT 100""",
            )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/test-cases")
def create_test_case(item: TestCaseCreate):
    if not item.title or not item.title.strip():
        raise HTTPException(status_code=400, detail=err("empty_title"))
    if item.status not in VALID_TC_STATUS:
        raise HTTPException(
            status_code=400,
            detail=err("invalid_status", value=item.status, allowed="draft/active/deprecated"),
        )
    check = db.execute(
        "SELECT 1 FROM manage_projects WHERE project_id = %s",
        (item.project_id,),
    )
    if not check["rows"]:
        raise HTTPException(status_code=400, detail=err("project_not_found", id=item.project_id))
    tc_id = f"tc_{uuid.uuid4().hex[:8]}"
    try:
        db.execute(
            """INSERT INTO manage_test_cases
               (test_case_id, project_id, title, description, status, source, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (tc_id, item.project_id, item.title.strip(), item.description,
             item.status, item.source, item.created_by),
        )
        return {"ok": True, "id": tc_id}
    except Exception as exc:
        raise handle_db_error(exc)


# ─── 里程碑 CRUD ─────────────────────────────────────────────

class MilestoneCreate(BaseModel):
    project_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    message: Optional[str] = None
    milestone_type: str = "regular"
    is_baseline: bool = False
    sprint: Optional[str] = None
    version: Optional[str] = None
    created_by: Optional[str] = None


VALID_MILESTONE_TYPES = {"regular", "baseline", "branch", "merge"}


@router.get("/milestones")
def list_milestones(project_id: Optional[str] = None):
    try:
        if project_id:
            result = db.execute(
                """SELECT m.*, p.name as project_name
                   FROM manage_milestones m
                   JOIN manage_projects p ON p.project_id = m.project_id
                   WHERE m.project_id = %s
                   ORDER BY m.created_at DESC""",
                (project_id,),
            )
        else:
            result = db.execute(
                """SELECT m.*, p.name as project_name
                   FROM manage_milestones m
                   JOIN manage_projects p ON p.project_id = m.project_id
                   ORDER BY m.created_at DESC
                   LIMIT 100""",
            )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/milestones")
def create_milestone(item: MilestoneCreate):
    if not item.name or not item.name.strip():
        raise HTTPException(status_code=400, detail=err("empty_name"))
    if item.milestone_type not in VALID_MILESTONE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"错误：里程碑类型『{item.milestone_type}』不在允许的范围内（regular/baseline/branch/merge）",
        )
    check = db.execute(
        "SELECT 1 FROM manage_projects WHERE project_id = %s",
        (item.project_id,),
    )
    if not check["rows"]:
        raise HTTPException(status_code=400, detail=err("project_not_found", id=item.project_id))
    ms_id = f"ms_{uuid.uuid4().hex[:8]}"
    try:
        db.execute(
            """INSERT INTO manage_milestones
               (milestone_id, project_id, name, description, message,
                milestone_type, is_baseline, sprint, version, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (ms_id, item.project_id, item.name.strip(), item.description,
             item.message, item.milestone_type, item.is_baseline,
             item.sprint, item.version, item.created_by),
        )
        return {"ok": True, "id": ms_id}
    except Exception as exc:
        raise handle_db_error(exc)
