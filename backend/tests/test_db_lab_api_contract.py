from __future__ import annotations

import pytest
from fastapi import HTTPException


def test_requirements_api_enforces_parent_rules_and_soft_delete(api_modules, fake_db) -> None:
    crud = api_modules["crud"]
    fake_db.seed_project("proj_a", name="项目A")
    fake_db.seed_project("proj_b", name="项目B")
    fake_db.seed_requirement(
        "req_top_a",
        project_id="proj_a",
        title="顶层A",
        requirement_type="top_level",
    )
    fake_db.seed_requirement(
        "req_top_b",
        project_id="proj_b",
        title="顶层B",
        requirement_type="top_level",
    )

    ok = crud.create_requirement(
        crud.RequirementCreate(
            project_id="proj_a",
            requirement_type="low_level",
            title="低层需求",
            status="draft",
            parent_id="req_top_a",
        )
    )
    low_level_id = ok["id"]
    assert fake_db.requirements[low_level_id]["parent_id"] == "req_top_a"

    with pytest.raises(HTTPException) as exc:
        crud.create_requirement(
            crud.RequirementCreate(
                project_id="proj_a",
                requirement_type="low_level",
                title="非法状态",
                status="bad_status",
                parent_id="req_top_a",
            )
        )
    assert exc.value.status_code == 400
    assert "状态值" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        crud.create_requirement(
            crud.RequirementCreate(
                project_id="proj_a",
                requirement_type="top_level",
                title="错误顶层",
                status="draft",
                parent_id="req_top_a",
            )
        )
    assert exc.value.status_code == 400
    assert "top_level" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        crud.create_requirement(
            crud.RequirementCreate(
                project_id="proj_a",
                requirement_type="low_level",
                title="跨项目父节点",
                status="draft",
                parent_id="req_top_b",
            )
        )
    assert exc.value.status_code == 400
    assert "不属于同一项目" in exc.value.detail

    task = crud.create_requirement(
        crud.RequirementCreate(
            project_id="proj_a",
            requirement_type="task",
            title="实现任务",
            status="draft",
            parent_id=low_level_id,
        )
    )
    task_id = task["id"]

    with pytest.raises(HTTPException) as exc:
        crud.update_requirement(
            low_level_id,
            crud.RequirementUpdate(parent_id=task_id),
        )
    assert exc.value.status_code == 400
    assert "父需求类型必须为 top_level" in exc.value.detail

    delete_resp = crud.delete_requirement(low_level_id)
    assert delete_resp["ok"] is True
    assert fake_db.requirements[low_level_id]["deleted"] is True


@pytest.mark.xfail(
    reason="当前层级校验会先拦截非法父类型，递归循环检测分支难以按实验文档要求真正触发",
    strict=False,
)
def test_requirement_cycle_detection_should_reject_descendant_parent(api_modules, fake_db) -> None:
    crud = api_modules["crud"]
    fake_db.seed_project("proj_a", name="项目A")
    fake_db.seed_requirement(
        "req_top_a",
        project_id="proj_a",
        title="顶层A",
        requirement_type="top_level",
    )

    low_level = crud.create_requirement(
        crud.RequirementCreate(
            project_id="proj_a",
            requirement_type="low_level",
            title="低层需求",
            status="draft",
            parent_id="req_top_a",
        )
    )
    task = crud.create_requirement(
        crud.RequirementCreate(
            project_id="proj_a",
            requirement_type="task",
            title="实现任务",
            status="draft",
            parent_id=low_level["id"],
        )
    )

    with pytest.raises(HTTPException) as exc:
        crud.update_requirement(
            low_level["id"],
            crud.RequirementUpdate(parent_id=task["id"]),
        )
    assert exc.value.status_code == 400
    assert "循环父子关系" in exc.value.detail


@pytest.mark.xfail(
    reason="当前实现把需求优先级校验错误复用了缺陷优先级集合，导致 high 被拒绝",
    strict=False,
)
def test_requirement_priority_should_accept_low_medium_high_per_fr4(api_modules, fake_db) -> None:
    crud = api_modules["crud"]
    fake_db.seed_project("proj_a", name="项目A")
    fake_db.seed_requirement(
        "req_top_a",
        project_id="proj_a",
        title="顶层A",
        requirement_type="top_level",
    )

    result = crud.create_requirement(
        crud.RequirementCreate(
            project_id="proj_a",
            requirement_type="low_level",
            title="优先级需求",
            status="draft",
            priority="high",
            parent_id="req_top_a",
        )
    )
    assert result["ok"] is True


def test_requirement_test_link_and_defect_endpoints_enforce_cross_project_rules(api_modules, fake_db) -> None:
    crud = api_modules["crud"]
    extended_crud = api_modules["extended_crud"]
    fake_db.seed_project("proj_a", name="项目A")
    fake_db.seed_project("proj_b", name="项目B")
    fake_db.seed_requirement(
        "req_a",
        project_id="proj_a",
        title="需求A",
        requirement_type="top_level",
    )
    fake_db.seed_requirement(
        "req_b",
        project_id="proj_b",
        title="需求B",
        requirement_type="top_level",
    )
    fake_db.seed_test_case("tc_a", project_id="proj_a", title="用例A", status="active")
    fake_db.seed_test_case("tc_b", project_id="proj_b", title="用例B", status="active")

    link_ok = extended_crud.create_requirement_test_link(
        extended_crud.RequirementTestLinkCreate(
            requirement_id="req_a",
            test_case_id="tc_a",
            link_type="verification",
        )
    )
    assert link_ok["ok"] is True

    with pytest.raises(HTTPException) as exc:
        extended_crud.create_requirement_test_link(
            extended_crud.RequirementTestLinkCreate(
                requirement_id="req_a",
                test_case_id="tc_b",
                link_type="verification",
            )
        )
    assert exc.value.status_code == 400
    assert "必须属于同一项目" in exc.value.detail

    defect_ok = crud.create_defect(
        crud.DefectCreate(
            project_id="proj_a",
            requirement_id="req_a",
            title="缺陷A",
            severity="critical",
            priority="P1",
            status="open",
        )
    )
    assert defect_ok["ok"] is True

    with pytest.raises(HTTPException) as exc:
        crud.create_defect(
            crud.DefectCreate(
                project_id="proj_a",
                requirement_id="req_a",
                title="非法严重程度",
                severity="fatal",
                priority="P1",
                status="open",
            )
        )
    assert exc.value.status_code == 400
    assert "严重程度" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        crud.create_defect(
            crud.DefectCreate(
                project_id="proj_a",
                requirement_id="req_b",
                title="跨项目缺陷",
                severity="high",
                priority="P2",
                status="open",
            )
        )
    assert exc.value.status_code == 400
    assert "不属于项目" in exc.value.detail


def test_branch_change_set_and_milestone_restrict_behaviors(api_modules, fake_db) -> None:
    crud = api_modules["crud"]
    extended_crud = api_modules["extended_crud"]
    fake_db.seed_project("proj_a", name="项目A")
    fake_db.seed_project("proj_b", name="项目B")
    fake_db.seed_requirement(
        "req_a",
        project_id="proj_a",
        title="需求A",
        requirement_type="top_level",
    )
    fake_db.seed_requirement(
        "req_b",
        project_id="proj_b",
        title="需求B",
        requirement_type="top_level",
    )
    fake_db.seed_milestone("ms_a", project_id="proj_a", name="基线A", is_baseline=True)
    fake_db.seed_milestone("ms_b", project_id="proj_b", name="基线B", is_baseline=True)

    branch_ok = extended_crud.create_branch(
        extended_crud.BranchCreate(
            project_id="proj_a",
            base_milestone_id="ms_a",
            name="feature-a",
            status="active",
            metadata={"owner": "alice"},
        )
    )
    branch_id = branch_ok["id"]

    with pytest.raises(HTTPException) as exc:
        extended_crud.create_branch(
            extended_crud.BranchCreate(
                project_id="proj_a",
                base_milestone_id="ms_a",
                name="feature-a",
                status="active",
            )
        )
    assert exc.value.status_code == 400
    assert "唯一约束" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        extended_crud.create_branch(
            extended_crud.BranchCreate(
                project_id="proj_a",
                base_milestone_id="ms_b",
                name="feature-cross",
                status="active",
            )
        )
    assert exc.value.status_code == 400
    assert "不属于当前项目" in exc.value.detail

    change_ok = extended_crud.create_change_set(
        extended_crud.ChangeSetCreate(
            branch_id=branch_id,
            change_type="modified",
            requirement_id="req_a",
            before_data={"title": "旧标题"},
            after_data={"title": "新标题"},
        )
    )
    assert change_ok["ok"] is True

    with pytest.raises(HTTPException) as exc:
        extended_crud.create_change_set(
            extended_crud.ChangeSetCreate(
                branch_id=branch_id,
                change_type="rename",
                requirement_id="req_a",
            )
        )
    assert exc.value.status_code == 400
    assert "变更类型" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        extended_crud.create_change_set(
            extended_crud.ChangeSetCreate(
                branch_id=branch_id,
                change_type="modified",
                requirement_id="req_b",
            )
        )
    assert exc.value.status_code == 400
    assert "不属于当前分支所在项目" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        crud.delete_milestone("ms_a")
    assert exc.value.status_code == 400
    assert "外键引用无效" in exc.value.detail


def test_comments_and_audit_logs_validate_scope(api_modules, fake_db) -> None:
    extended_crud = api_modules["extended_crud"]
    fake_db.seed_product("prod_a", name="产品A")
    fake_db.seed_product("prod_b", name="产品B")
    fake_db.seed_project("proj_a", name="项目A", product_id="prod_a")
    fake_db.seed_project("proj_b", name="项目B", product_id="prod_b")
    fake_db.seed_requirement(
        "req_a",
        project_id="proj_a",
        title="需求A",
        requirement_type="top_level",
    )
    fake_db.seed_requirement(
        "req_b",
        project_id="proj_b",
        title="需求B",
        requirement_type="top_level",
    )
    fake_db.seed_comment(
        "cmt_b",
        project_id="proj_b",
        target_type="requirement",
        target_id="req_b",
        content="跨项目回复源",
    )

    comment_ok = extended_crud.create_comment(
        extended_crud.CommentCreate(
            project_id="proj_a",
            target_type="requirement",
            target_id="req_a",
            content="这是评论",
            created_by="tester",
        )
    )
    assert comment_ok["ok"] is True

    with pytest.raises(HTTPException) as exc:
        extended_crud.create_comment(
            extended_crud.CommentCreate(
                project_id="proj_a",
                target_type="story",
                target_id="req_a",
                content="无效目标类型",
                created_by="tester",
            )
        )
    assert exc.value.status_code == 400
    assert "评论目标类型" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        extended_crud.create_comment(
            extended_crud.CommentCreate(
                project_id="proj_a",
                target_type="requirement",
                target_id="req_b",
                content="跨项目评论",
                created_by="tester",
            )
        )
    assert exc.value.status_code == 400
    assert "不属于当前项目" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        extended_crud.create_comment(
            extended_crud.CommentCreate(
                project_id="proj_a",
                target_type="requirement",
                target_id="req_a",
                content="跨项目回复",
                reply_to_id="cmt_b",
                created_by="tester",
            )
        )
    assert exc.value.status_code == 400
    assert "外键引用无效" in exc.value.detail

    audit_ok = extended_crud.create_audit_log(
        extended_crud.AuditLogCreate(
            project_id="proj_a",
            product_id="prod_a",
            actor="tester",
            action="create",
            target_type="requirement",
            target_id="req_a",
            detail={"source": "api"},
        )
    )
    assert audit_ok["ok"] is True

    with pytest.raises(HTTPException) as exc:
        extended_crud.create_audit_log(
            extended_crud.AuditLogCreate(
                project_id="proj_a",
                product_id="prod_b",
                actor="tester",
                action="create",
                target_type="requirement",
                target_id="req_a",
                detail={"source": "api"},
            )
        )
    assert exc.value.status_code == 400
    assert exc.value.detail.startswith("错误：")


def test_complex_queries_return_expected_fields_and_handle_empty_projects(api_modules, fake_db) -> None:
    statistics = api_modules["statistics"]
    fake_db.seed_product("prod_a", name="产品A")
    fake_db.seed_project("proj_a", name="项目A", product_id="prod_a")
    fake_db.seed_project("proj_empty", name="空项目")

    fake_db.seed_requirement(
        "req_top",
        project_id="proj_a",
        title="顶层需求",
        requirement_type="top_level",
        status="in_progress",
        priority="high",
    )
    fake_db.seed_requirement(
        "req_child",
        project_id="proj_a",
        title="子需求",
        requirement_type="low_level",
        status="completed",
        parent_id="req_top",
    )
    fake_db.seed_test_case("tc_a", project_id="proj_a", title="测试用例A", status="active")
    fake_db.seed_requirement_test_link("req_top", "tc_a")
    fake_db.seed_defect(
        "def_a",
        project_id="proj_a",
        requirement_id="req_top",
        title="关键缺陷",
        severity="critical",
        priority="P0",
        status="open",
    )
    fake_db.seed_milestone(
        "ms_a",
        project_id="proj_a",
        name="里程碑A",
        milestone_type="baseline",
        is_baseline=True,
        sprint="Sprint 1",
        version="v1.0",
    )
    fake_db.seed_milestone_node("snap_a", milestone_id="ms_a", requirement_id="req_top", status="in_progress")
    fake_db.seed_requirement_link("req_top", "req_child", link_type="depends_on")
    fake_db.seed_branch("branch_a", project_id="proj_a", base_milestone_id="ms_a", name="branch-a")
    fake_db.seed_change_set("chg_a", branch_id="branch_a", change_type="modified", requirement_id="req_top")

    trace = statistics.get_requirement_trace("proj_a")
    assert trace["total"] == 2
    assert {
        "req_id",
        "requirement_title",
        "requirement_type",
        "status",
        "priority",
        "assignee",
        "project_name",
        "test_cases",
        "defects",
        "test_case_count",
        "total_defect_count",
        "open_defect_count",
    }.issubset(trace["items"][0].keys())

    progress = statistics.get_project_progress("proj_a")
    assert {
        "project_id",
        "project_name",
        "project_status",
        "total_requirements",
        "completed_requirements",
        "completion_rate_percent",
        "total_defects",
        "critical_defects",
        "covered_requirements",
        "test_coverage_rate_percent",
        "total_milestones",
        "baseline_count",
    }.issubset(progress.keys())
    assert progress["critical_defects"] == 1

    risk = statistics.get_milestone_delivery_risk("proj_a")
    assert risk["total"] == 1
    assert {
        "milestone_id",
        "milestone_name",
        "milestone_type",
        "is_baseline",
        "project_name",
        "scoped_requirement_count",
        "uncovered_requirement_count",
        "blocked_requirement_count",
        "unresolved_defect_count",
        "critical_defect_count",
        "active_branch_count",
        "pending_change_count",
        "risk_score",
        "risk_level",
    }.issubset(risk["items"][0].keys())

    empty_trace = statistics.get_requirement_trace("proj_empty")
    assert empty_trace == {"items": [], "total": 0}

    empty_progress = statistics.get_project_progress("proj_empty")
    assert empty_progress["total_requirements"] == 0
    assert empty_progress["total_milestones"] == 0

    empty_risk = statistics.get_milestone_delivery_risk("proj_empty")
    assert empty_risk == {"items": [], "total": 0}

    with pytest.raises(HTTPException) as exc:
        statistics.get_project_progress("proj_missing")
    assert exc.value.status_code == 404
    assert "不存在" in exc.value.detail
