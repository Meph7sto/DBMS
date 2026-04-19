"""Extended CRUD API for remaining requirement management tables."""

from typing import Any, Optional
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database import db
from routers.crud import VALID_ROLES, err, handle_db_error


router = APIRouter(prefix="/api/crud", tags=["extended-crud"])

VALID_REQUIREMENT_LINK_TYPES = {"blocks", "depends_on", "relates_to", "duplicates"}
VALID_REQUIREMENT_TEST_LINK_TYPES = {"verification", "coverage", "regression"}
VALID_BRANCH_STATUS = {"active", "under_review", "merged", "closed"}
VALID_CHANGE_TYPES = {"added", "modified", "deleted", "moved"}
VALID_COMMENT_TARGETS = {"requirement", "defect", "test_case", "milestone"}


def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def ensure_required_text(value: Optional[str], field_label: str) -> str:
    normalized = normalize_text(value)
    if not normalized:
        raise HTTPException(status_code=400, detail=err("empty_required_field", field=field_label))
    return normalized


def require_product(product_id: str) -> dict[str, Any]:
    result = db.execute(
        "SELECT product_id, name FROM manage_products WHERE product_id = %s",
        (product_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=400, detail=err("product_not_found", id=product_id))
    return result["rows"][0]


def require_project(project_id: str) -> dict[str, Any]:
    result = db.execute(
        "SELECT project_id, name, product_id FROM manage_projects WHERE project_id = %s",
        (project_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=400, detail=err("project_not_found", id=project_id))
    return result["rows"][0]


def require_requirement(requirement_id: str) -> dict[str, Any]:
    result = db.execute(
        """SELECT req_id, project_id, title, requirement_type
           FROM manage_requirements
           WHERE req_id = %s AND deleted = FALSE""",
        (requirement_id,),
    )
    if not result["rows"]:
        raise HTTPException(
            status_code=400,
            detail=err("requirement_not_found", id=requirement_id),
        )
    return result["rows"][0]


def require_test_case(test_case_id: str) -> dict[str, Any]:
    result = db.execute(
        "SELECT test_case_id, project_id, title FROM manage_test_cases WHERE test_case_id = %s",
        (test_case_id,),
    )
    if not result["rows"]:
        raise HTTPException(
            status_code=400,
            detail=err("test_case_not_found", id=test_case_id),
        )
    return result["rows"][0]


def require_milestone(milestone_id: str) -> dict[str, Any]:
    result = db.execute(
        "SELECT milestone_id, project_id, name FROM manage_milestones WHERE milestone_id = %s",
        (milestone_id,),
    )
    if not result["rows"]:
        raise HTTPException(
            status_code=400,
            detail=err("milestone_not_found", id=milestone_id),
        )
    return result["rows"][0]


def require_branch(branch_id: str) -> dict[str, Any]:
    result = db.execute(
        "SELECT branch_id, project_id, name FROM manage_branches WHERE branch_id = %s",
        (branch_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=400, detail=f"错误：指定的分支ID『{branch_id}』不存在")
    return result["rows"][0]


def require_comment(comment_id: str) -> dict[str, Any]:
    result = db.execute(
        "SELECT comment_id, project_id FROM manage_comments WHERE comment_id = %s",
        (comment_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=400, detail=f"错误：指定的评论ID『{comment_id}』不存在")
    return result["rows"][0]


def require_product_member(member_id: int) -> dict[str, Any]:
    result = db.execute(
        "SELECT id, product_id, user_id, role FROM manage_product_members WHERE id = %s",
        (member_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=404, detail=f"错误：指定的产品成员ID『{member_id}』不存在")
    return result["rows"][0]


def require_project_member(member_id: int) -> dict[str, Any]:
    result = db.execute(
        "SELECT id, project_id, user_id, role FROM manage_project_members WHERE id = %s",
        (member_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=404, detail=f"错误：指定的项目成员ID『{member_id}』不存在")
    return result["rows"][0]


def require_requirement_link(link_id: int) -> dict[str, Any]:
    result = db.execute(
        """SELECT link_id, source_req_id, target_req_id, link_type
           FROM manage_requirement_links
           WHERE link_id = %s""",
        (link_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=404, detail=f"错误：指定的需求关联ID『{link_id}』不存在")
    return result["rows"][0]


def require_requirement_test_link(link_id: int) -> dict[str, Any]:
    result = db.execute(
        """SELECT link_id, requirement_id, test_case_id, link_type
           FROM manage_requirement_test_links
           WHERE link_id = %s""",
        (link_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=404, detail=f"错误：指定的需求-用例关联ID『{link_id}』不存在")
    return result["rows"][0]


def require_milestone_node(snapshot_id: str) -> dict[str, Any]:
    result = db.execute(
        "SELECT snapshot_id, milestone_id, requirement_id FROM manage_milestone_nodes WHERE snapshot_id = %s",
        (snapshot_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=404, detail=f"错误：指定的里程碑节点ID『{snapshot_id}』不存在")
    return result["rows"][0]


def require_change_set(change_id: str) -> dict[str, Any]:
    result = db.execute(
        "SELECT change_id, branch_id, requirement_id, change_type FROM manage_change_sets WHERE change_id = %s",
        (change_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=404, detail=f"错误：指定的变更集ID『{change_id}』不存在")
    return result["rows"][0]


def require_comment_record(comment_id: str) -> dict[str, Any]:
    result = db.execute(
        """SELECT comment_id, project_id, target_type, target_id, reply_to_id, content, created_by, deleted
           FROM manage_comments WHERE comment_id = %s""",
        (comment_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=404, detail=f"错误：指定的评论ID『{comment_id}』不存在")
    return result["rows"][0]


def require_audit_log(log_id: str) -> dict[str, Any]:
    result = db.execute(
        """SELECT log_id, project_id, product_id, actor, action, target_type, target_id, detail
           FROM manage_audit_logs WHERE log_id = %s""",
        (log_id,),
    )
    if not result["rows"]:
        raise HTTPException(status_code=404, detail=f"错误：指定的审计日志ID『{log_id}』不存在")
    return result["rows"][0]


def validate_role(role: str):
    if role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=err("invalid_role", value=role))


def validate_requirement_link_pair(source_req_id: str, target_req_id: str, link_type: str):
    if link_type not in VALID_REQUIREMENT_LINK_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"错误：关联类型『{link_type}』不在允许的范围内"
                "（blocks/depends_on/relates_to/duplicates）"
            ),
        )
    if source_req_id == target_req_id:
        raise HTTPException(status_code=400, detail="错误：需求关联的源需求和目标需求不能相同")
    source = require_requirement(source_req_id)
    target = require_requirement(target_req_id)
    if source["project_id"] != target["project_id"]:
        raise HTTPException(status_code=400, detail="错误：需求关联两端必须属于同一项目")


def validate_requirement_test_pair(requirement_id: str, test_case_id: str):
    requirement = require_requirement(requirement_id)
    test_case = require_test_case(test_case_id)
    if requirement["project_id"] != test_case["project_id"]:
        raise HTTPException(status_code=400, detail="错误：需求与测试用例必须属于同一项目")


def validate_requirement_test_link_type(link_type: str):
    if link_type not in VALID_REQUIREMENT_TEST_LINK_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"错误：需求-测试关联类型『{link_type}』不在允许的范围内"
                "（verification/coverage/regression）"
            ),
        )


def validate_milestone_requirement_pair(milestone_id: str, requirement_id: str):
    milestone = require_milestone(milestone_id)
    requirement = require_requirement(requirement_id)
    if milestone["project_id"] != requirement["project_id"]:
        raise HTTPException(status_code=400, detail="错误：里程碑和需求必须属于同一项目")


def validate_branch_reference(project_id: str, base_milestone_id: str):
    milestone = require_milestone(base_milestone_id)
    if milestone["project_id"] != project_id:
        raise HTTPException(status_code=400, detail="错误：基线里程碑不属于当前项目")


def validate_change_set_reference(branch_id: str, requirement_id: Optional[str]):
    branch = require_branch(branch_id)
    if requirement_id:
        requirement = require_requirement(requirement_id)
        if requirement["project_id"] != branch["project_id"]:
            raise HTTPException(status_code=400, detail="错误：变更集中的需求不属于当前分支所在项目")


def validate_comment_target(project_id: str, target_type: str, target_id: str):
    if target_type not in VALID_COMMENT_TARGETS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"错误：评论目标类型『{target_type}』不在允许的范围内"
                "（requirement/defect/test_case/milestone）"
            ),
        )

    project = require_project(project_id)
    del project

    query_map = {
        "requirement": (
            "SELECT req_id AS target_id, project_id FROM manage_requirements WHERE req_id = %s AND deleted = FALSE",
            err("requirement_not_found", id=target_id),
        ),
        "defect": (
            "SELECT defect_id AS target_id, project_id FROM manage_defects WHERE defect_id = %s",
            err("defect_not_found", id=target_id),
        ),
        "test_case": (
            "SELECT test_case_id AS target_id, project_id FROM manage_test_cases WHERE test_case_id = %s",
            err("test_case_not_found", id=target_id),
        ),
        "milestone": (
            "SELECT milestone_id AS target_id, project_id FROM manage_milestones WHERE milestone_id = %s",
            err("milestone_not_found", id=target_id),
        ),
    }
    sql, not_found_message = query_map[target_type]
    result = db.execute(sql, (target_id,))
    if not result["rows"]:
        raise HTTPException(status_code=400, detail=not_found_message)
    if result["rows"][0]["project_id"] != project_id:
        raise HTTPException(status_code=400, detail="错误：评论目标不属于当前项目")


class ProductMemberCreate(BaseModel):
    product_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    role: str = "member"


class ProductMemberUpdate(BaseModel):
    product_id: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None


@router.get("/product-members")
def list_product_members(product_id: Optional[str] = None):
    try:
        if product_id:
            result = db.execute(
                """SELECT pm.*, p.name AS product_name
                   FROM manage_product_members pm
                   JOIN manage_products p ON p.product_id = pm.product_id
                   WHERE pm.product_id = %s
                   ORDER BY pm.created_at DESC""",
                (product_id,),
            )
        else:
            result = db.execute(
                """SELECT pm.*, p.name AS product_name
                   FROM manage_product_members pm
                   JOIN manage_products p ON p.product_id = pm.product_id
                   ORDER BY pm.created_at DESC"""
            )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/product-members")
def create_product_member(item: ProductMemberCreate):
    product_id = ensure_required_text(item.product_id, "product_id")
    user_id = ensure_required_text(item.user_id, "user_id")
    validate_role(item.role)
    require_product(product_id)
    try:
        result = db.execute(
            """INSERT INTO manage_product_members (product_id, user_id, role)
               VALUES (%s, %s, %s)
               RETURNING id""",
            (product_id, user_id, item.role),
        )
        return {"ok": True, "id": result["rows"][0]["id"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/product-members/{member_id}")
def update_product_member(member_id: int, item: ProductMemberUpdate):
    current = require_product_member(member_id)
    data = item.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")

    product_id = normalize_text(data.get("product_id")) if "product_id" in data else current["product_id"]
    user_id = normalize_text(data.get("user_id")) if "user_id" in data else current["user_id"]
    role = data.get("role", current["role"])

    product_id = ensure_required_text(product_id, "product_id")
    user_id = ensure_required_text(user_id, "user_id")
    validate_role(role)
    require_product(product_id)

    try:
        db.execute(
            """UPDATE manage_product_members
               SET product_id = %s, user_id = %s, role = %s, updated_at = NOW()
               WHERE id = %s""",
            (product_id, user_id, role, member_id),
        )
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/product-members/{member_id}")
def delete_product_member(member_id: int):
    require_product_member(member_id)
    try:
        db.execute("DELETE FROM manage_product_members WHERE id = %s", (member_id,))
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


class ProjectMemberCreate(BaseModel):
    project_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    role: str = "member"


class ProjectMemberUpdate(BaseModel):
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None


@router.get("/project-members")
def list_project_members(project_id: Optional[str] = None):
    try:
        if project_id:
            result = db.execute(
                """SELECT pm.*, p.name AS project_name
                   FROM manage_project_members pm
                   JOIN manage_projects p ON p.project_id = pm.project_id
                   WHERE pm.project_id = %s
                   ORDER BY pm.created_at DESC""",
                (project_id,),
            )
        else:
            result = db.execute(
                """SELECT pm.*, p.name AS project_name
                   FROM manage_project_members pm
                   JOIN manage_projects p ON p.project_id = pm.project_id
                   ORDER BY pm.created_at DESC"""
            )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/project-members")
def create_project_member(item: ProjectMemberCreate):
    project_id = ensure_required_text(item.project_id, "project_id")
    user_id = ensure_required_text(item.user_id, "user_id")
    validate_role(item.role)
    require_project(project_id)
    try:
        result = db.execute(
            """INSERT INTO manage_project_members (project_id, user_id, role)
               VALUES (%s, %s, %s)
               RETURNING id""",
            (project_id, user_id, item.role),
        )
        return {"ok": True, "id": result["rows"][0]["id"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/project-members/{member_id}")
def update_project_member(member_id: int, item: ProjectMemberUpdate):
    current = require_project_member(member_id)
    data = item.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")

    project_id = normalize_text(data.get("project_id")) if "project_id" in data else current["project_id"]
    user_id = normalize_text(data.get("user_id")) if "user_id" in data else current["user_id"]
    role = data.get("role", current["role"])

    project_id = ensure_required_text(project_id, "project_id")
    user_id = ensure_required_text(user_id, "user_id")
    validate_role(role)
    require_project(project_id)

    try:
        db.execute(
            """UPDATE manage_project_members
               SET project_id = %s, user_id = %s, role = %s, updated_at = NOW()
               WHERE id = %s""",
            (project_id, user_id, role, member_id),
        )
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/project-members/{member_id}")
def delete_project_member(member_id: int):
    require_project_member(member_id)
    try:
        db.execute("DELETE FROM manage_project_members WHERE id = %s", (member_id,))
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


class RequirementLinkCreate(BaseModel):
    source_req_id: str = Field(..., min_length=1)
    target_req_id: str = Field(..., min_length=1)
    link_type: str = Field(..., min_length=1)
    created_by: Optional[str] = None


class RequirementLinkUpdate(BaseModel):
    source_req_id: Optional[str] = None
    target_req_id: Optional[str] = None
    link_type: Optional[str] = None
    created_by: Optional[str] = None


@router.get("/requirement-links")
def list_requirement_links(project_id: Optional[str] = None):
    try:
        params: list[Any] = []
        where_sql = ""
        if project_id:
            where_sql = "WHERE sr.project_id = %s"
            params.append(project_id)
        result = db.execute(
            f"""SELECT rl.*, sr.title AS source_title, tr.title AS target_title,
                       sr.project_id, p.name AS project_name
                FROM manage_requirement_links rl
                JOIN manage_requirements sr ON sr.req_id = rl.source_req_id
                JOIN manage_requirements tr ON tr.req_id = rl.target_req_id
                JOIN manage_projects p ON p.project_id = sr.project_id
                {where_sql}
                ORDER BY rl.created_at DESC""",
            tuple(params),
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/requirement-links")
def create_requirement_link(item: RequirementLinkCreate):
    source_req_id = ensure_required_text(item.source_req_id, "source_req_id")
    target_req_id = ensure_required_text(item.target_req_id, "target_req_id")
    link_type = ensure_required_text(item.link_type, "link_type")
    created_by = normalize_text(item.created_by)
    validate_requirement_link_pair(source_req_id, target_req_id, link_type)
    try:
        result = db.execute(
            """INSERT INTO manage_requirement_links
               (source_req_id, target_req_id, link_type, created_by)
               VALUES (%s, %s, %s, %s)
               RETURNING link_id""",
            (source_req_id, target_req_id, link_type, created_by),
        )
        return {"ok": True, "id": result["rows"][0]["link_id"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/requirement-links/{link_id}")
def update_requirement_link(link_id: int, item: RequirementLinkUpdate):
    current = require_requirement_link(link_id)
    data = item.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")

    source_req_id = normalize_text(data.get("source_req_id")) if "source_req_id" in data else current["source_req_id"]
    target_req_id = normalize_text(data.get("target_req_id")) if "target_req_id" in data else current["target_req_id"]
    link_type = normalize_text(data.get("link_type")) if "link_type" in data else current["link_type"]
    created_by = normalize_text(data.get("created_by")) if "created_by" in data else current.get("created_by")

    source_req_id = ensure_required_text(source_req_id, "source_req_id")
    target_req_id = ensure_required_text(target_req_id, "target_req_id")
    link_type = ensure_required_text(link_type, "link_type")
    validate_requirement_link_pair(source_req_id, target_req_id, link_type)

    try:
        db.execute(
            """UPDATE manage_requirement_links
               SET source_req_id = %s, target_req_id = %s, link_type = %s, created_by = %s
               WHERE link_id = %s""",
            (source_req_id, target_req_id, link_type, created_by, link_id),
        )
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/requirement-links/{link_id}")
def delete_requirement_link(link_id: int):
    require_requirement_link(link_id)
    try:
        db.execute("DELETE FROM manage_requirement_links WHERE link_id = %s", (link_id,))
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


class RequirementTestLinkCreate(BaseModel):
    requirement_id: str = Field(..., min_length=1)
    test_case_id: str = Field(..., min_length=1)
    link_type: str = "verification"


class RequirementTestLinkUpdate(BaseModel):
    requirement_id: Optional[str] = None
    test_case_id: Optional[str] = None
    link_type: Optional[str] = None


@router.get("/requirement-test-links")
def list_requirement_test_links(project_id: Optional[str] = None):
    try:
        params: list[Any] = []
        where_sql = ""
        if project_id:
            where_sql = "WHERE r.project_id = %s"
            params.append(project_id)
        result = db.execute(
            f"""SELECT rtl.*, r.project_id, r.title AS requirement_title,
                       tc.title AS test_case_title, p.name AS project_name
                FROM manage_requirement_test_links rtl
                JOIN manage_requirements r ON r.req_id = rtl.requirement_id
                JOIN manage_test_cases tc ON tc.test_case_id = rtl.test_case_id
                JOIN manage_projects p ON p.project_id = r.project_id
                {where_sql}
                ORDER BY rtl.created_at DESC""",
            tuple(params),
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/requirement-test-links")
def create_requirement_test_link(item: RequirementTestLinkCreate):
    requirement_id = ensure_required_text(item.requirement_id, "requirement_id")
    test_case_id = ensure_required_text(item.test_case_id, "test_case_id")
    link_type = ensure_required_text(item.link_type, "link_type")
    validate_requirement_test_pair(requirement_id, test_case_id)
    validate_requirement_test_link_type(link_type)
    try:
        result = db.execute(
            """INSERT INTO manage_requirement_test_links
               (requirement_id, test_case_id, link_type)
               VALUES (%s, %s, %s)
               RETURNING link_id""",
            (requirement_id, test_case_id, link_type),
        )
        return {"ok": True, "id": result["rows"][0]["link_id"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/requirement-test-links/{link_id}")
def update_requirement_test_link(link_id: int, item: RequirementTestLinkUpdate):
    current = require_requirement_test_link(link_id)
    data = item.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")

    requirement_id = normalize_text(data.get("requirement_id")) if "requirement_id" in data else current["requirement_id"]
    test_case_id = normalize_text(data.get("test_case_id")) if "test_case_id" in data else current["test_case_id"]
    link_type = normalize_text(data.get("link_type")) if "link_type" in data else current["link_type"]

    requirement_id = ensure_required_text(requirement_id, "requirement_id")
    test_case_id = ensure_required_text(test_case_id, "test_case_id")
    link_type = ensure_required_text(link_type, "link_type")
    validate_requirement_test_pair(requirement_id, test_case_id)
    validate_requirement_test_link_type(link_type)

    try:
        db.execute(
            """UPDATE manage_requirement_test_links
               SET requirement_id = %s, test_case_id = %s, link_type = %s
               WHERE link_id = %s""",
            (requirement_id, test_case_id, link_type, link_id),
        )
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/requirement-test-links/{link_id}")
def delete_requirement_test_link(link_id: int):
    require_requirement_test_link(link_id)
    try:
        db.execute("DELETE FROM manage_requirement_test_links WHERE link_id = %s", (link_id,))
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


class MilestoneNodeCreate(BaseModel):
    milestone_id: str = Field(..., min_length=1)
    requirement_id: str = Field(..., min_length=1)
    requirement_type: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    order_index: int = 0
    snapshot_data: Optional[Any] = None


class MilestoneNodeUpdate(BaseModel):
    milestone_id: Optional[str] = None
    requirement_id: Optional[str] = None
    requirement_type: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    order_index: Optional[int] = None
    snapshot_data: Optional[Any] = None


@router.get("/milestone-nodes")
def list_milestone_nodes(project_id: Optional[str] = None, milestone_id: Optional[str] = None):
    try:
        params: list[Any] = []
        conditions: list[str] = []
        if project_id:
            conditions.append("m.project_id = %s")
            params.append(project_id)
        if milestone_id:
            conditions.append("mn.milestone_id = %s")
            params.append(milestone_id)
        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        result = db.execute(
            f"""SELECT mn.*, m.project_id, m.name AS milestone_name, r.title AS requirement_title,
                       p.name AS project_name
                FROM manage_milestone_nodes mn
                JOIN manage_milestones m ON m.milestone_id = mn.milestone_id
                JOIN manage_projects p ON p.project_id = m.project_id
                LEFT JOIN manage_requirements r ON r.req_id = mn.requirement_id
                {where_sql}
                ORDER BY mn.created_at DESC""",
            tuple(params),
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/milestone-nodes")
def create_milestone_node(item: MilestoneNodeCreate):
    milestone_id = ensure_required_text(item.milestone_id, "milestone_id")
    requirement_id = ensure_required_text(item.requirement_id, "requirement_id")
    validate_milestone_requirement_pair(milestone_id, requirement_id)
    snapshot_id = f"snap_{uuid.uuid4().hex[:8]}"
    try:
        db.execute(
            """INSERT INTO manage_milestone_nodes
               (snapshot_id, milestone_id, requirement_id, requirement_type, status, title,
                description, parent_id, order_index, snapshot_data)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::JSONB)""",
            (
                snapshot_id,
                milestone_id,
                requirement_id,
                normalize_text(item.requirement_type),
                normalize_text(item.status),
                normalize_text(item.title),
                item.description,
                normalize_text(item.parent_id),
                item.order_index,
                item.snapshot_data,
            ),
        )
        return {"ok": True, "id": snapshot_id}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/milestone-nodes/{snapshot_id}")
def update_milestone_node(snapshot_id: str, item: MilestoneNodeUpdate):
    current = require_milestone_node(snapshot_id)
    data = item.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")

    milestone_id = normalize_text(data.get("milestone_id")) if "milestone_id" in data else current["milestone_id"]
    requirement_id = normalize_text(data.get("requirement_id")) if "requirement_id" in data else current["requirement_id"]
    milestone_id = ensure_required_text(milestone_id, "milestone_id")
    requirement_id = ensure_required_text(requirement_id, "requirement_id")
    validate_milestone_requirement_pair(milestone_id, requirement_id)

    sets: list[str] = []
    params: list[Any] = []
    update_map = {
        "milestone_id": milestone_id,
        "requirement_id": requirement_id,
        "requirement_type": normalize_text(data["requirement_type"]) if "requirement_type" in data else None,
        "status": normalize_text(data["status"]) if "status" in data else None,
        "title": normalize_text(data["title"]) if "title" in data else None,
        "description": data["description"] if "description" in data else None,
        "parent_id": normalize_text(data["parent_id"]) if "parent_id" in data else None,
        "order_index": data["order_index"] if "order_index" in data else None,
        "snapshot_data": data["snapshot_data"] if "snapshot_data" in data else None,
    }
    for field, value in update_map.items():
        if field in data or field in {"milestone_id", "requirement_id"}:
            if field == "snapshot_data":
                sets.append(f"{field} = %s::JSONB")
            else:
                sets.append(f"{field} = %s")
            params.append(value)
    params.append(snapshot_id)
    try:
        db.execute(
            f"UPDATE manage_milestone_nodes SET {', '.join(sets)} WHERE snapshot_id = %s",
            tuple(params),
        )
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/milestone-nodes/{snapshot_id}")
def delete_milestone_node(snapshot_id: str):
    require_milestone_node(snapshot_id)
    try:
        db.execute("DELETE FROM manage_milestone_nodes WHERE snapshot_id = %s", (snapshot_id,))
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


class BranchCreate(BaseModel):
    project_id: str = Field(..., min_length=1)
    base_milestone_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    status: str = "active"
    metadata: Optional[Any] = None
    created_by: Optional[str] = None


class BranchUpdate(BaseModel):
    project_id: Optional[str] = None
    base_milestone_id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Any] = None
    created_by: Optional[str] = None


@router.get("/branches")
def list_branches(project_id: Optional[str] = None):
    try:
        params: list[Any] = []
        where_sql = ""
        if project_id:
            where_sql = "WHERE b.project_id = %s"
            params.append(project_id)
        result = db.execute(
            f"""SELECT b.*, p.name AS project_name, m.name AS base_milestone_name
                FROM manage_branches b
                JOIN manage_projects p ON p.project_id = b.project_id
                JOIN manage_milestones m ON m.milestone_id = b.base_milestone_id
                {where_sql}
                ORDER BY b.created_at DESC""",
            tuple(params),
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/branches")
def create_branch(item: BranchCreate):
    project_id = ensure_required_text(item.project_id, "project_id")
    base_milestone_id = ensure_required_text(item.base_milestone_id, "base_milestone_id")
    name = ensure_required_text(item.name, "name")
    if item.status not in VALID_BRANCH_STATUS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"错误：状态值『{item.status}』不在允许的范围内"
                "（active/under_review/merged/closed）"
            ),
        )
    require_project(project_id)
    validate_branch_reference(project_id, base_milestone_id)
    branch_id = f"branch_{uuid.uuid4().hex[:8]}"
    try:
        db.execute(
            """INSERT INTO manage_branches
               (branch_id, project_id, base_milestone_id, name, status, metadata, created_by)
               VALUES (%s, %s, %s, %s, %s, %s::JSONB, %s)""",
            (
                branch_id,
                project_id,
                base_milestone_id,
                name,
                item.status,
                item.metadata,
                normalize_text(item.created_by),
            ),
        )
        return {"ok": True, "id": branch_id}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/branches/{branch_id}")
def update_branch(branch_id: str, item: BranchUpdate):
    current = require_branch(branch_id)
    data = item.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")

    project_id = normalize_text(data.get("project_id")) if "project_id" in data else current["project_id"]
    base_milestone_id = normalize_text(data.get("base_milestone_id")) if "base_milestone_id" in data else None
    name = normalize_text(data.get("name")) if "name" in data else current["name"]
    status = data.get("status", current["status"])

    project_id = ensure_required_text(project_id, "project_id")
    base_milestone_id = ensure_required_text(
        base_milestone_id or data.get("base_milestone_id") or current.get("base_milestone_id"),
        "base_milestone_id",
    )
    name = ensure_required_text(name, "name")
    if status not in VALID_BRANCH_STATUS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"错误：状态值『{status}』不在允许的范围内"
                "（active/under_review/merged/closed）"
            ),
        )
    require_project(project_id)
    validate_branch_reference(project_id, base_milestone_id)

    try:
        db.execute(
            """UPDATE manage_branches
               SET project_id = %s, base_milestone_id = %s, name = %s, status = %s,
                   metadata = %s::JSONB, created_by = %s, updated_at = NOW()
               WHERE branch_id = %s""",
            (
                project_id,
                base_milestone_id,
                name,
                status,
                data.get("metadata"),
                normalize_text(data.get("created_by")),
                branch_id,
            ),
        )
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/branches/{branch_id}")
def delete_branch(branch_id: str):
    require_branch(branch_id)
    try:
        db.execute("DELETE FROM manage_branches WHERE branch_id = %s", (branch_id,))
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


class ChangeSetCreate(BaseModel):
    branch_id: str = Field(..., min_length=1)
    change_type: str = Field(..., min_length=1)
    requirement_id: Optional[str] = None
    before_data: Optional[Any] = None
    after_data: Optional[Any] = None
    created_by: Optional[str] = None


class ChangeSetUpdate(BaseModel):
    branch_id: Optional[str] = None
    change_type: Optional[str] = None
    requirement_id: Optional[str] = None
    before_data: Optional[Any] = None
    after_data: Optional[Any] = None
    created_by: Optional[str] = None


@router.get("/change-sets")
def list_change_sets(project_id: Optional[str] = None, branch_id: Optional[str] = None):
    try:
        params: list[Any] = []
        conditions: list[str] = []
        if project_id:
            conditions.append("b.project_id = %s")
            params.append(project_id)
        if branch_id:
            conditions.append("cs.branch_id = %s")
            params.append(branch_id)
        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        result = db.execute(
            f"""SELECT cs.*, b.project_id, b.name AS branch_name, p.name AS project_name,
                       r.title AS requirement_title
                FROM manage_change_sets cs
                JOIN manage_branches b ON b.branch_id = cs.branch_id
                JOIN manage_projects p ON p.project_id = b.project_id
                LEFT JOIN manage_requirements r ON r.req_id = cs.requirement_id
                {where_sql}
                ORDER BY cs.created_at DESC""",
            tuple(params),
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/change-sets")
def create_change_set(item: ChangeSetCreate):
    branch_id = ensure_required_text(item.branch_id, "branch_id")
    requirement_id = normalize_text(item.requirement_id)
    change_type = ensure_required_text(item.change_type, "change_type")
    if change_type not in VALID_CHANGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"错误：变更类型『{change_type}』不在允许的范围内"
                "（added/modified/deleted/moved）"
            ),
        )
    validate_change_set_reference(branch_id, requirement_id)
    change_id = f"chg_{uuid.uuid4().hex[:8]}"
    try:
        db.execute(
            """INSERT INTO manage_change_sets
               (change_id, branch_id, change_type, requirement_id, before_data, after_data, created_by)
               VALUES (%s, %s, %s, %s, %s::JSONB, %s::JSONB, %s)""",
            (
                change_id,
                branch_id,
                change_type,
                requirement_id,
                item.before_data,
                item.after_data,
                normalize_text(item.created_by),
            ),
        )
        return {"ok": True, "id": change_id}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/change-sets/{change_id}")
def update_change_set(change_id: str, item: ChangeSetUpdate):
    current = require_change_set(change_id)
    data = item.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")

    branch_id = normalize_text(data.get("branch_id")) if "branch_id" in data else current["branch_id"]
    requirement_id = normalize_text(data.get("requirement_id")) if "requirement_id" in data else current["requirement_id"]
    change_type = normalize_text(data.get("change_type")) if "change_type" in data else current["change_type"]

    branch_id = ensure_required_text(branch_id, "branch_id")
    change_type = ensure_required_text(change_type, "change_type")
    if change_type not in VALID_CHANGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"错误：变更类型『{change_type}』不在允许的范围内"
                "（added/modified/deleted/moved）"
            ),
        )
    validate_change_set_reference(branch_id, requirement_id)

    try:
        db.execute(
            """UPDATE manage_change_sets
               SET branch_id = %s, change_type = %s, requirement_id = %s,
                   before_data = %s::JSONB, after_data = %s::JSONB, created_by = %s
               WHERE change_id = %s""",
            (
                branch_id,
                change_type,
                requirement_id,
                data.get("before_data"),
                data.get("after_data"),
                normalize_text(data.get("created_by")),
                change_id,
            ),
        )
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/change-sets/{change_id}")
def delete_change_set(change_id: str):
    require_change_set(change_id)
    try:
        db.execute("DELETE FROM manage_change_sets WHERE change_id = %s", (change_id,))
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


class CommentCreate(BaseModel):
    project_id: str = Field(..., min_length=1)
    target_type: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    reply_to_id: Optional[str] = None
    created_by: str = Field(..., min_length=1)
    deleted: bool = False


class CommentUpdate(BaseModel):
    project_id: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    content: Optional[str] = None
    reply_to_id: Optional[str] = None
    created_by: Optional[str] = None
    deleted: Optional[bool] = None


@router.get("/comments")
def list_comments(project_id: Optional[str] = None):
    try:
        params: list[Any] = []
        where_sql = ""
        if project_id:
            where_sql = "WHERE c.project_id = %s"
            params.append(project_id)
        result = db.execute(
            f"""SELECT c.*, p.name AS project_name
                FROM manage_comments c
                JOIN manage_projects p ON p.project_id = c.project_id
                {where_sql}
                ORDER BY c.created_at DESC""",
            tuple(params),
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/comments")
def create_comment(item: CommentCreate):
    project_id = ensure_required_text(item.project_id, "project_id")
    target_type = ensure_required_text(item.target_type, "target_type")
    target_id = ensure_required_text(item.target_id, "target_id")
    content = ensure_required_text(item.content, "content")
    created_by = ensure_required_text(item.created_by, "created_by")
    reply_to_id = normalize_text(item.reply_to_id)
    validate_comment_target(project_id, target_type, target_id)
    if reply_to_id:
        require_comment(reply_to_id)
    comment_id = f"cmt_{uuid.uuid4().hex[:8]}"
    try:
        db.execute(
            """INSERT INTO manage_comments
               (comment_id, project_id, target_type, target_id, content, reply_to_id, created_by, deleted)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (comment_id, project_id, target_type, target_id, content, reply_to_id, created_by, item.deleted),
        )
        return {"ok": True, "id": comment_id}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/comments/{comment_id}")
def update_comment(comment_id: str, item: CommentUpdate):
    current = require_comment_record(comment_id)
    data = item.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")

    project_id = normalize_text(data.get("project_id")) if "project_id" in data else current["project_id"]
    target_type = normalize_text(data.get("target_type")) if "target_type" in data else current["target_type"]
    target_id = normalize_text(data.get("target_id")) if "target_id" in data else current["target_id"]
    content = normalize_text(data.get("content")) if "content" in data else current["content"]
    created_by = normalize_text(data.get("created_by")) if "created_by" in data else current["created_by"]
    reply_to_id = normalize_text(data.get("reply_to_id")) if "reply_to_id" in data else current["reply_to_id"]
    deleted = data.get("deleted", current["deleted"])

    project_id = ensure_required_text(project_id, "project_id")
    target_type = ensure_required_text(target_type, "target_type")
    target_id = ensure_required_text(target_id, "target_id")
    content = ensure_required_text(content, "content")
    created_by = ensure_required_text(created_by, "created_by")
    validate_comment_target(project_id, target_type, target_id)
    if reply_to_id:
        require_comment(reply_to_id)

    try:
        db.execute(
            """UPDATE manage_comments
               SET project_id = %s, target_type = %s, target_id = %s, content = %s,
                   reply_to_id = %s, created_by = %s, deleted = %s, updated_at = NOW()
               WHERE comment_id = %s""",
            (project_id, target_type, target_id, content, reply_to_id, created_by, deleted, comment_id),
        )
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: str):
    require_comment_record(comment_id)
    try:
        db.execute("DELETE FROM manage_comments WHERE comment_id = %s", (comment_id,))
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


class AuditLogCreate(BaseModel):
    project_id: Optional[str] = None
    product_id: Optional[str] = None
    actor: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    detail: Optional[Any] = None


class AuditLogUpdate(BaseModel):
    project_id: Optional[str] = None
    product_id: Optional[str] = None
    actor: Optional[str] = None
    action: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    detail: Optional[Any] = None


@router.get("/audit-logs")
def list_audit_logs(project_id: Optional[str] = None, product_id: Optional[str] = None):
    try:
        params: list[Any] = []
        conditions: list[str] = []
        if project_id:
            conditions.append("a.project_id = %s")
            params.append(project_id)
        if product_id:
            conditions.append("a.product_id = %s")
            params.append(product_id)
        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        result = db.execute(
            f"""SELECT a.*, p.name AS project_name, pr.name AS product_name
                FROM manage_audit_logs a
                LEFT JOIN manage_projects p ON p.project_id = a.project_id
                LEFT JOIN manage_products pr ON pr.product_id = a.product_id
                {where_sql}
                ORDER BY a.created_at DESC""",
            tuple(params),
        )
        return {"items": result["rows"], "total": result["row_count"]}
    except Exception as exc:
        raise handle_db_error(exc)


@router.post("/audit-logs")
def create_audit_log(item: AuditLogCreate):
    project_id = normalize_text(item.project_id)
    product_id = normalize_text(item.product_id)
    actor = ensure_required_text(item.actor, "actor")
    action = ensure_required_text(item.action, "action")
    if project_id:
        require_project(project_id)
    if product_id:
        require_product(product_id)
    log_id = f"log_{uuid.uuid4().hex[:8]}"
    try:
        db.execute(
            """INSERT INTO manage_audit_logs
               (log_id, project_id, product_id, actor, action, target_type, target_id, detail)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s::JSONB)""",
            (
                log_id,
                project_id,
                product_id,
                actor,
                action,
                normalize_text(item.target_type),
                normalize_text(item.target_id),
                item.detail,
            ),
        )
        return {"ok": True, "id": log_id}
    except Exception as exc:
        raise handle_db_error(exc)


@router.put("/audit-logs/{log_id}")
def update_audit_log(log_id: str, item: AuditLogUpdate):
    current = require_audit_log(log_id)
    data = item.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="没有提供任何更新字段")

    project_id = normalize_text(data.get("project_id")) if "project_id" in data else current["project_id"]
    product_id = normalize_text(data.get("product_id")) if "product_id" in data else current["product_id"]
    actor = normalize_text(data.get("actor")) if "actor" in data else current["actor"]
    action = normalize_text(data.get("action")) if "action" in data else current["action"]

    if project_id:
        require_project(project_id)
    if product_id:
        require_product(product_id)
    actor = ensure_required_text(actor, "actor")
    action = ensure_required_text(action, "action")

    try:
        db.execute(
            """UPDATE manage_audit_logs
               SET project_id = %s, product_id = %s, actor = %s, action = %s,
                   target_type = %s, target_id = %s, detail = %s::JSONB
               WHERE log_id = %s""",
            (
                project_id,
                product_id,
                actor,
                action,
                normalize_text(data.get("target_type")) if "target_type" in data else current["target_type"],
                normalize_text(data.get("target_id")) if "target_id" in data else current["target_id"],
                data.get("detail"),
                log_id,
            ),
        )
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)


@router.delete("/audit-logs/{log_id}")
def delete_audit_log(log_id: str):
    require_audit_log(log_id)
    try:
        db.execute("DELETE FROM manage_audit_logs WHERE log_id = %s", (log_id,))
        return {"ok": True}
    except Exception as exc:
        raise handle_db_error(exc)
