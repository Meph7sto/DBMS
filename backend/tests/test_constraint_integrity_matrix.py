from __future__ import annotations

import re
import uuid
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
from fastapi import HTTPException

from config import get_default_connection
from database import DatabaseManager
from routers import query


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATCH_SQL = ROOT / "db" / "requirements_db_constraints_patch.sql"

EXPECTED_PRIMARY_KEYS = {
    "manage_products_pkey",
    "manage_product_members_pkey",
    "manage_projects_pkey",
    "manage_project_members_pkey",
    "manage_requirements_pkey",
    "manage_requirement_links_pkey",
    "manage_test_cases_pkey",
    "manage_requirement_test_links_pkey",
    "manage_defects_pkey",
    "manage_milestones_pkey",
    "manage_milestone_nodes_pkey",
    "manage_branches_pkey",
    "manage_change_sets_pkey",
    "manage_comments_pkey",
    "manage_audit_logs_pkey",
}

EXPECTED_UNIQUE_CONSTRAINTS = {
    "manage_products_name_key",
    "uk_product_member",
    "manage_projects_name_key",
    "uk_project_member",
    "uk_requirement_project_req",
    "uk_req_link",
    "uk_test_case_project_case",
    "uk_req_test_link",
    "uk_milestone_project_milestone",
    "uk_project_branch",
}

EXPECTED_CHECK_CONSTRAINTS = {
    "manage_products_status_check",
    "manage_product_members_role_check",
    "manage_projects_status_check",
    "manage_project_members_role_check",
    "manage_requirements_requirement_type_check",
    "manage_requirements_status_check",
    "manage_requirements_priority_check",
    "chk_requirement_parent_not_self",
    "manage_requirement_links_link_type_check",
    "chk_no_self_link",
    "manage_test_cases_status_check",
    "manage_defects_severity_check",
    "manage_defects_priority_check",
    "manage_defects_status_check",
    "manage_milestones_milestone_type_check",
    "manage_branches_status_check",
    "manage_change_sets_change_type_check",
    "manage_comments_target_type_check",
}

EXPECTED_FOREIGN_KEYS = {
    "manage_product_members_product_id_fkey",
    "manage_projects_product_id_fkey",
    "manage_project_members_project_id_fkey",
    "manage_requirements_project_id_fkey",
    "manage_requirements_parent_id_fkey",
    "manage_requirement_links_source_req_id_fkey",
    "manage_requirement_links_target_req_id_fkey",
    "manage_test_cases_project_id_fkey",
    "manage_requirement_test_links_requirement_id_fkey",
    "manage_requirement_test_links_test_case_id_fkey",
    "manage_defects_project_id_fkey",
    "fk_defects_requirement_project",
    "manage_milestones_project_id_fkey",
    "manage_milestone_nodes_milestone_id_fkey",
    "manage_milestone_nodes_requirement_id_fkey",
    "manage_branches_project_id_fkey",
    "manage_branches_base_milestone_id_fkey",
    "manage_change_sets_branch_id_fkey",
    "manage_change_sets_requirement_id_fkey",
    "manage_comments_project_id_fkey",
    "manage_comments_reply_to_id_fkey",
    "manage_audit_logs_project_id_fkey",
    "manage_audit_logs_product_id_fkey",
}

EXPECTED_TRIGGERS = {
    "trg_validate_requirement_hierarchy",
    "trg_validate_requirement_link_scope",
    "trg_validate_requirement_test_link_scope",
    "trg_validate_branch_scope",
    "trg_validate_milestone_node_scope",
    "trg_validate_change_set_scope",
    "trg_validate_comment_scope",
    "trg_validate_audit_log_scope",
}

EXPECTED_NOT_NULL_COLUMNS = {
    "manage_products.product_id",
    "manage_products.name",
    "manage_products.status",
    "manage_products.created_at",
    "manage_products.updated_at",
    "manage_product_members.id",
    "manage_product_members.product_id",
    "manage_product_members.user_id",
    "manage_product_members.role",
    "manage_product_members.created_at",
    "manage_product_members.updated_at",
    "manage_projects.project_id",
    "manage_projects.name",
    "manage_projects.status",
    "manage_projects.created_at",
    "manage_projects.updated_at",
    "manage_project_members.id",
    "manage_project_members.project_id",
    "manage_project_members.user_id",
    "manage_project_members.role",
    "manage_project_members.created_at",
    "manage_project_members.updated_at",
    "manage_requirements.req_id",
    "manage_requirements.project_id",
    "manage_requirements.requirement_type",
    "manage_requirements.status",
    "manage_requirements.title",
    "manage_requirements.order_index",
    "manage_requirements.is_planned",
    "manage_requirements.created_at",
    "manage_requirements.updated_at",
    "manage_requirements.deleted",
    "manage_requirement_links.link_id",
    "manage_requirement_links.source_req_id",
    "manage_requirement_links.target_req_id",
    "manage_requirement_links.link_type",
    "manage_requirement_links.created_at",
    "manage_test_cases.test_case_id",
    "manage_test_cases.project_id",
    "manage_test_cases.title",
    "manage_test_cases.status",
    "manage_test_cases.created_at",
    "manage_requirement_test_links.link_id",
    "manage_requirement_test_links.requirement_id",
    "manage_requirement_test_links.test_case_id",
    "manage_requirement_test_links.link_type",
    "manage_requirement_test_links.created_at",
    "manage_defects.defect_id",
    "manage_defects.project_id",
    "manage_defects.requirement_id",
    "manage_defects.title",
    "manage_defects.reproduce_steps",
    "manage_defects.severity",
    "manage_defects.priority",
    "manage_defects.status",
    "manage_defects.created_at",
    "manage_defects.updated_at",
    "manage_milestones.milestone_id",
    "manage_milestones.project_id",
    "manage_milestones.name",
    "manage_milestones.milestone_type",
    "manage_milestones.is_baseline",
    "manage_milestones.created_at",
    "manage_milestone_nodes.snapshot_id",
    "manage_milestone_nodes.milestone_id",
    "manage_milestone_nodes.requirement_id",
    "manage_milestone_nodes.created_at",
    "manage_branches.branch_id",
    "manage_branches.project_id",
    "manage_branches.base_milestone_id",
    "manage_branches.name",
    "manage_branches.status",
    "manage_branches.created_at",
    "manage_branches.updated_at",
    "manage_change_sets.change_id",
    "manage_change_sets.branch_id",
    "manage_change_sets.change_type",
    "manage_change_sets.created_at",
    "manage_comments.comment_id",
    "manage_comments.project_id",
    "manage_comments.target_type",
    "manage_comments.target_id",
    "manage_comments.content",
    "manage_comments.created_by",
    "manage_comments.created_at",
    "manage_comments.updated_at",
    "manage_comments.deleted",
    "manage_audit_logs.log_id",
    "manage_audit_logs.actor",
    "manage_audit_logs.action",
    "manage_audit_logs.created_at",
}

EXPECTED_TRIGGER_MESSAGES = {
    "非顶层需求必须指定父需求",
    "需求不能将自己设置为父需求",
    "父需求 % 不存在",
    "父需求 % 与当前需求不属于同一项目",
    "顶层需求不能设置父需求",
    "low_level 的父需求必须是 top_level",
    "task 的父需求必须是 top_level 或 low_level",
    "源需求 % 不存在或已删除",
    "目标需求 % 不存在或已删除",
    "需求关联两端必须属于同一项目",
    "需求 % 不存在或已删除",
    "测试用例 % 不存在",
    "需求与测试用例必须属于同一项目",
    "基线里程碑 % 不存在",
    "分支与基线里程碑必须属于同一项目",
    "里程碑 % 不存在",
    "里程碑节点关联的需求 % 不存在或已删除",
    "里程碑节点与需求必须属于同一项目",
    "分支 % 不存在",
    "变更集关联的需求 % 不存在或已删除",
    "变更集与需求必须属于同一项目",
    "不支持的评论目标类型 %",
    "评论目标 % 不存在或已删除",
    "评论所属项目与目标对象不一致",
    "被回复的评论 % 不存在或已删除",
    "评论回复必须发生在同一项目内",
    "审计日志关联的项目 % 不存在",
    "审计日志中的产品与项目归属不一致",
}


def _sql(text: str) -> str:
    return dedent(text).strip()


CONSTRAINT_CASES: list[dict[str, Any]] = [
    {
        "case_id": "ui_unique_product_name",
        "kind": "unique",
        "sql": _sql(
            """
            INSERT INTO manage_products (product_id, name, status)
            VALUES
              ('cm_prod_unique_a_{suffix}', '约束矩阵唯一产品-{suffix}', 'active'),
              ('cm_prod_unique_b_{suffix}', '约束矩阵唯一产品-{suffix}', 'active');
            """
        ),
        "expected": ("违反唯一约束",),
    },
    {
        "case_id": "ui_project_product_fk",
        "kind": "foreign_key",
        "sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status, product_id)
            VALUES ('cm_proj_fk_{suffix}', '约束矩阵外键项目-{suffix}', 'active', 'cm_prod_missing_{suffix}');
            """
        ),
        "expected": ("违反外键约束",),
    },
    {
        "case_id": "ui_product_name_not_null",
        "kind": "not_null",
        "sql": _sql(
            """
            INSERT INTO manage_products (product_id, name, status)
            VALUES ('cm_prod_not_null_{suffix}', NULL, 'active');
            """
        ),
        "expected": ("字段不能为空",),
    },
    {
        "case_id": "ui_product_status_check",
        "kind": "check",
        "sql": _sql(
            """
            INSERT INTO manage_products (product_id, name, status)
            VALUES ('cm_prod_check_{suffix}', '约束矩阵检查产品-{suffix}', 'disabled');
            """
        ),
        "expected": ("数据校验失败",),
    },
    {
        "case_id": "ui_requirement_missing_parent",
        "kind": "trigger_hierarchy",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_hierarchy_{suffix}', '约束矩阵层级项目-{suffix}', 'active');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES (
              'cm_req_hierarchy_{suffix}',
              'cm_proj_hierarchy_{suffix}',
              'low_level',
              'draft',
              '约束矩阵层级需求-{suffix}'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_hierarchy_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_hierarchy_{suffix}';
            """
        ),
        "expected": ("非顶层需求必须指定父需求",),
        "covers": ("trg_validate_requirement_hierarchy",),
        "covers_messages": ("非顶层需求必须指定父需求",),
    },
    {
        "case_id": "requirement_self_parent_update",
        "kind": "trigger_hierarchy",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_cycle_{suffix}', '约束矩阵循环项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_cycle_top_{suffix}', 'cm_proj_cycle_{suffix}', 'top_level', 'draft', '顶层需求-{suffix}');

            INSERT INTO manage_requirements (
              req_id, project_id, requirement_type, status, title, parent_id
            )
            VALUES (
              'cm_req_cycle_low_{suffix}',
              'cm_proj_cycle_{suffix}',
              'low_level',
              'draft',
              '低层需求-{suffix}',
              'cm_req_cycle_top_{suffix}'
            );

            INSERT INTO manage_requirements (
              req_id, project_id, requirement_type, status, title, parent_id
            )
            VALUES (
              'cm_req_cycle_task_{suffix}',
              'cm_proj_cycle_{suffix}',
              'task',
              'draft',
              '任务需求-{suffix}',
              'cm_req_cycle_low_{suffix}'
            );

            """
        ),
        "sql": _sql(
            """
            UPDATE manage_requirements
            SET parent_id = 'cm_req_cycle_task_{suffix}'
            WHERE req_id = 'cm_req_cycle_task_{suffix}';
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirements
            WHERE req_id IN (
              'cm_req_cycle_task_{suffix}',
              'cm_req_cycle_low_{suffix}',
              'cm_req_cycle_top_{suffix}'
            );
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_cycle_{suffix}';
            """
        ),
        "expected": ("需求不能将自己设置为父需求",),
        "covers": ("trg_validate_requirement_hierarchy",),
        "covers_messages": ("需求不能将自己设置为父需求",),
    },
    {
        "case_id": "requirement_parent_not_found",
        "kind": "trigger_hierarchy",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_parent_missing_{suffix}', '父需求缺失项目-{suffix}', 'active');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title, parent_id)
            VALUES (
              'cm_req_parent_missing_{suffix}',
              'cm_proj_parent_missing_{suffix}',
              'low_level',
              'draft',
              '父需求缺失用例-{suffix}',
              'cm_req_missing_parent_{suffix}'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_parent_missing_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_parent_missing_{suffix}';
            """
        ),
        "expected": ("父需求 cm_req_missing_parent_",),
        "covers": ("trg_validate_requirement_hierarchy",),
        "covers_messages": ("父需求 % 不存在",),
    },
    {
        "case_id": "requirement_parent_cross_project",
        "kind": "trigger_hierarchy",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES
              ('cm_proj_parent_a_{suffix}', '父需求范围项目A-{suffix}', 'active'),
              ('cm_proj_parent_b_{suffix}', '父需求范围项目B-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_parent_top_b_{suffix}', 'cm_proj_parent_b_{suffix}', 'top_level', 'draft', '跨项目父需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title, parent_id)
            VALUES (
              'cm_req_parent_cross_{suffix}',
              'cm_proj_parent_a_{suffix}',
              'low_level',
              'draft',
              '跨项目父需求校验-{suffix}',
              'cm_req_parent_top_b_{suffix}'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirements
            WHERE req_id IN ('cm_req_parent_cross_{suffix}', 'cm_req_parent_top_b_{suffix}');
            DELETE FROM manage_projects
            WHERE project_id IN ('cm_proj_parent_a_{suffix}', 'cm_proj_parent_b_{suffix}');
            """
        ),
        "expected": ("与当前需求不属于同一项目",),
        "covers": ("trg_validate_requirement_hierarchy",),
        "covers_messages": ("父需求 % 与当前需求不属于同一项目",),
    },
    {
        "case_id": "top_level_parent_forbidden",
        "kind": "trigger_hierarchy",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_top_parent_{suffix}', '顶层父需求项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_top_parent_{suffix}', 'cm_proj_top_parent_{suffix}', 'top_level', 'draft', '已有顶层需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title, parent_id)
            VALUES (
              'cm_req_top_child_{suffix}',
              'cm_proj_top_parent_{suffix}',
              'top_level',
              'draft',
              '非法顶层子项-{suffix}',
              'cm_req_top_parent_{suffix}'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirements
            WHERE req_id IN ('cm_req_top_child_{suffix}', 'cm_req_top_parent_{suffix}');
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_top_parent_{suffix}';
            """
        ),
        "expected": ("顶层需求不能设置父需求",),
        "covers": ("trg_validate_requirement_hierarchy",),
        "covers_messages": ("顶层需求不能设置父需求",),
    },
    {
        "case_id": "low_level_parent_type_invalid",
        "kind": "trigger_hierarchy",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_low_parent_{suffix}', '低层父类型项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_low_top_{suffix}', 'cm_proj_low_parent_{suffix}', 'top_level', 'draft', '顶层需求-{suffix}');

            INSERT INTO manage_requirements (
              req_id, project_id, requirement_type, status, title, parent_id
            )
            VALUES (
              'cm_req_low_low_{suffix}',
              'cm_proj_low_parent_{suffix}',
              'low_level',
              'draft',
              '低层需求-{suffix}',
              'cm_req_low_top_{suffix}'
            );

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title, parent_id)
            VALUES (
              'cm_req_low_task_{suffix}',
              'cm_proj_low_parent_{suffix}',
              'task',
              'draft',
              '任务父节点-{suffix}',
              'cm_req_low_low_{suffix}'
            );
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title, parent_id)
            VALUES (
              'cm_req_low_invalid_{suffix}',
              'cm_proj_low_parent_{suffix}',
              'low_level',
              'draft',
              '非法低层父类型-{suffix}',
              'cm_req_low_task_{suffix}'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirements
            WHERE req_id IN (
              'cm_req_low_invalid_{suffix}',
              'cm_req_low_task_{suffix}',
              'cm_req_low_low_{suffix}',
              'cm_req_low_top_{suffix}'
            );
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_low_parent_{suffix}';
            """
        ),
        "expected": ("low_level 的父需求必须是 top_level",),
        "covers": ("trg_validate_requirement_hierarchy",),
        "covers_messages": ("low_level 的父需求必须是 top_level",),
    },
    {
        "case_id": "task_parent_type_invalid",
        "kind": "trigger_hierarchy",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_task_parent_{suffix}', '任务父类型项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_task_top_{suffix}', 'cm_proj_task_parent_{suffix}', 'top_level', 'draft', '顶层需求-{suffix}');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title, parent_id)
            VALUES (
              'cm_req_task_parent_{suffix}',
              'cm_proj_task_parent_{suffix}',
              'task',
              'draft',
              '任务父节点-{suffix}',
              'cm_req_task_top_{suffix}'
            );
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title, parent_id)
            VALUES (
              'cm_req_task_invalid_{suffix}',
              'cm_proj_task_parent_{suffix}',
              'task',
              'draft',
              '非法任务父类型-{suffix}',
              'cm_req_task_parent_{suffix}'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirements
            WHERE req_id IN (
              'cm_req_task_invalid_{suffix}',
              'cm_req_task_parent_{suffix}',
              'cm_req_task_top_{suffix}'
            );
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_task_parent_{suffix}';
            """
        ),
        "expected": ("task 的父需求必须是 top_level 或 low_level",),
        "covers": ("trg_validate_requirement_hierarchy",),
        "covers_messages": ("task 的父需求必须是 top_level 或 low_level",),
    },
    {
        "case_id": "requirement_link_cross_project",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES
              ('cm_proj_link_a_{suffix}', '约束矩阵关联项目A-{suffix}', 'active'),
              ('cm_proj_link_b_{suffix}', '约束矩阵关联项目B-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES
              ('cm_req_link_a_{suffix}', 'cm_proj_link_a_{suffix}', 'top_level', 'draft', '需求A-{suffix}'),
              ('cm_req_link_b_{suffix}', 'cm_proj_link_b_{suffix}', 'top_level', 'draft', '需求B-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirement_links (source_req_id, target_req_id, link_type)
            VALUES ('cm_req_link_a_{suffix}', 'cm_req_link_b_{suffix}', 'depends_on');
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirement_links
            WHERE source_req_id IN ('cm_req_link_a_{suffix}', 'cm_req_link_b_{suffix}')
               OR target_req_id IN ('cm_req_link_a_{suffix}', 'cm_req_link_b_{suffix}');
            DELETE FROM manage_requirements
            WHERE req_id IN ('cm_req_link_a_{suffix}', 'cm_req_link_b_{suffix}');
            DELETE FROM manage_projects
            WHERE project_id IN ('cm_proj_link_a_{suffix}', 'cm_proj_link_b_{suffix}');
            """
        ),
        "expected": ("需求关联两端必须属于同一项目",),
        "covers": ("trg_validate_requirement_link_scope",),
        "covers_messages": ("需求关联两端必须属于同一项目",),
    },
    {
        "case_id": "requirement_link_source_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_link_source_{suffix}', '需求关联源缺失项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_link_target_only_{suffix}', 'cm_proj_link_source_{suffix}', 'top_level', 'draft', '存在目标需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirement_links (source_req_id, target_req_id, link_type)
            VALUES ('cm_req_link_missing_{suffix}', 'cm_req_link_target_only_{suffix}', 'blocks');
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirement_links WHERE target_req_id = 'cm_req_link_target_only_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_link_target_only_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_link_source_{suffix}';
            """
        ),
        "expected": ("源需求 cm_req_link_missing_",),
        "covers": ("trg_validate_requirement_link_scope",),
        "covers_messages": ("源需求 % 不存在或已删除",),
    },
    {
        "case_id": "requirement_link_target_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_link_target_{suffix}', '需求关联目标缺失项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_link_source_only_{suffix}', 'cm_proj_link_target_{suffix}', 'top_level', 'draft', '存在源需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirement_links (source_req_id, target_req_id, link_type)
            VALUES ('cm_req_link_source_only_{suffix}', 'cm_req_link_missing_target_{suffix}', 'duplicates');
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirement_links WHERE source_req_id = 'cm_req_link_source_only_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_link_source_only_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_link_target_{suffix}';
            """
        ),
        "expected": ("目标需求 cm_req_link_missing_target_",),
        "covers": ("trg_validate_requirement_link_scope",),
        "covers_messages": ("目标需求 % 不存在或已删除",),
    },
    {
        "case_id": "requirement_link_self_reference",
        "kind": "check",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_self_link_{suffix}', '约束矩阵自关联项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_self_link_{suffix}', 'cm_proj_self_link_{suffix}', 'top_level', 'draft', '自关联需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirement_links (source_req_id, target_req_id, link_type)
            VALUES ('cm_req_self_link_{suffix}', 'cm_req_self_link_{suffix}', 'relates_to');
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirement_links
            WHERE source_req_id = 'cm_req_self_link_{suffix}'
               OR target_req_id = 'cm_req_self_link_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_self_link_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_self_link_{suffix}';
            """
        ),
        "expected": ("违反了检查约束", "chk_no_self_link"),
    },
    {
        "case_id": "ui_requirement_test_cross_project",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES
              ('cm_proj_scope_a_{suffix}', '约束矩阵范围项目A-{suffix}', 'active'),
              ('cm_proj_scope_b_{suffix}', '约束矩阵范围项目B-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_scope_{suffix}', 'cm_proj_scope_a_{suffix}', 'top_level', 'draft', '范围需求-{suffix}');

            INSERT INTO manage_test_cases (test_case_id, project_id, title, status)
            VALUES ('cm_tc_scope_{suffix}', 'cm_proj_scope_b_{suffix}', '范围测试用例-{suffix}', 'draft');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirement_test_links (requirement_id, test_case_id, link_type)
            VALUES ('cm_req_scope_{suffix}', 'cm_tc_scope_{suffix}', 'verification');
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirement_test_links
            WHERE requirement_id = 'cm_req_scope_{suffix}'
               OR test_case_id = 'cm_tc_scope_{suffix}';
            DELETE FROM manage_test_cases WHERE test_case_id = 'cm_tc_scope_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_scope_{suffix}';
            DELETE FROM manage_projects
            WHERE project_id IN ('cm_proj_scope_a_{suffix}', 'cm_proj_scope_b_{suffix}');
            """
        ),
        "expected": ("需求与测试用例必须属于同一项目",),
        "covers": ("trg_validate_requirement_test_link_scope",),
        "covers_messages": ("需求与测试用例必须属于同一项目",),
    },
    {
        "case_id": "requirement_test_link_requirement_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_req_test_req_missing_{suffix}', '需求用例缺需求项目-{suffix}', 'active');

            INSERT INTO manage_test_cases (test_case_id, project_id, title, status)
            VALUES ('cm_tc_req_missing_{suffix}', 'cm_proj_req_test_req_missing_{suffix}', '测试用例-{suffix}', 'active');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirement_test_links (requirement_id, test_case_id, link_type)
            VALUES ('cm_req_missing_for_test_{suffix}', 'cm_tc_req_missing_{suffix}', 'verification');
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirement_test_links WHERE test_case_id = 'cm_tc_req_missing_{suffix}';
            DELETE FROM manage_test_cases WHERE test_case_id = 'cm_tc_req_missing_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_req_test_req_missing_{suffix}';
            """
        ),
        "expected": ("需求 cm_req_missing_for_test_",),
        "covers": ("trg_validate_requirement_test_link_scope",),
        "covers_messages": ("需求 % 不存在或已删除",),
    },
    {
        "case_id": "requirement_test_link_test_case_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_req_test_tc_missing_{suffix}', '需求用例缺用例项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_tc_missing_{suffix}', 'cm_proj_req_test_tc_missing_{suffix}', 'top_level', 'draft', '需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirement_test_links (requirement_id, test_case_id, link_type)
            VALUES ('cm_req_tc_missing_{suffix}', 'cm_tc_missing_for_req_{suffix}', 'coverage');
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirement_test_links WHERE requirement_id = 'cm_req_tc_missing_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_tc_missing_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_req_test_tc_missing_{suffix}';
            """
        ),
        "expected": ("测试用例 cm_tc_missing_for_req_",),
        "covers": ("trg_validate_requirement_test_link_scope",),
        "covers_messages": ("测试用例 % 不存在",),
    },
    {
        "case_id": "duplicate_requirement_test_link",
        "kind": "unique",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_dup_link_{suffix}', '约束矩阵重复关联项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_dup_link_{suffix}', 'cm_proj_dup_link_{suffix}', 'top_level', 'draft', '重复关联需求-{suffix}');

            INSERT INTO manage_test_cases (test_case_id, project_id, title, status)
            VALUES ('cm_tc_dup_link_{suffix}', 'cm_proj_dup_link_{suffix}', '重复关联用例-{suffix}', 'active');

            INSERT INTO manage_requirement_test_links (requirement_id, test_case_id, link_type)
            VALUES ('cm_req_dup_link_{suffix}', 'cm_tc_dup_link_{suffix}', 'verification');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_requirement_test_links (requirement_id, test_case_id, link_type)
            VALUES ('cm_req_dup_link_{suffix}', 'cm_tc_dup_link_{suffix}', 'verification');
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_requirement_test_links
            WHERE requirement_id = 'cm_req_dup_link_{suffix}'
               OR test_case_id = 'cm_tc_dup_link_{suffix}';
            DELETE FROM manage_test_cases WHERE test_case_id = 'cm_tc_dup_link_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_dup_link_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_dup_link_{suffix}';
            """
        ),
        "expected": ("违反唯一约束",),
    },
    {
        "case_id": "branch_cross_project_baseline",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES
              ('cm_proj_branch_a_{suffix}', '约束矩阵分支项目A-{suffix}', 'active'),
              ('cm_proj_branch_b_{suffix}', '约束矩阵分支项目B-{suffix}', 'active');

            INSERT INTO manage_milestones (
              milestone_id, project_id, name, milestone_type, is_baseline
            )
            VALUES (
              'cm_ms_branch_b_{suffix}',
              'cm_proj_branch_b_{suffix}',
              '基线里程碑-{suffix}',
              'baseline',
              TRUE
            );
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_branches (branch_id, project_id, base_milestone_id, name, status)
            VALUES (
              'cm_branch_scope_{suffix}',
              'cm_proj_branch_a_{suffix}',
              'cm_ms_branch_b_{suffix}',
              'branch-scope-{suffix}',
              'active'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_branches WHERE branch_id = 'cm_branch_scope_{suffix}';
            DELETE FROM manage_milestones WHERE milestone_id = 'cm_ms_branch_b_{suffix}';
            DELETE FROM manage_projects
            WHERE project_id IN ('cm_proj_branch_a_{suffix}', 'cm_proj_branch_b_{suffix}');
            """
        ),
        "expected": ("分支与基线里程碑必须属于同一项目",),
        "covers": ("trg_validate_branch_scope",),
        "covers_messages": ("分支与基线里程碑必须属于同一项目",),
    },
    {
        "case_id": "branch_milestone_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_branch_missing_{suffix}', '分支缺里程碑项目-{suffix}', 'active');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_branches (branch_id, project_id, base_milestone_id, name, status)
            VALUES (
              'cm_branch_missing_ms_{suffix}',
              'cm_proj_branch_missing_{suffix}',
              'cm_ms_missing_{suffix}',
              'branch-missing-ms-{suffix}',
              'active'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_branches WHERE branch_id = 'cm_branch_missing_ms_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_branch_missing_{suffix}';
            """
        ),
        "expected": ("基线里程碑 cm_ms_missing_",),
        "covers": ("trg_validate_branch_scope",),
        "covers_messages": ("基线里程碑 % 不存在",),
    },
    {
        "case_id": "milestone_node_cross_project_requirement",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES
              ('cm_proj_node_a_{suffix}', '约束矩阵节点项目A-{suffix}', 'active'),
              ('cm_proj_node_b_{suffix}', '约束矩阵节点项目B-{suffix}', 'active');

            INSERT INTO manage_milestones (
              milestone_id, project_id, name, milestone_type, is_baseline
            )
            VALUES (
              'cm_ms_node_a_{suffix}',
              'cm_proj_node_a_{suffix}',
              '节点里程碑-{suffix}',
              'baseline',
              TRUE
            );

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_node_b_{suffix}', 'cm_proj_node_b_{suffix}', 'top_level', 'draft', '节点需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_milestone_nodes (
              snapshot_id, milestone_id, requirement_id, requirement_type, status, title, order_index, snapshot_data
            )
            VALUES (
              'cm_snap_scope_{suffix}',
              'cm_ms_node_a_{suffix}',
              'cm_req_node_b_{suffix}',
              'top_level',
              'draft',
              '节点快照-{suffix}',
              0,
              NULL
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_milestone_nodes WHERE snapshot_id = 'cm_snap_scope_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_node_b_{suffix}';
            DELETE FROM manage_milestones WHERE milestone_id = 'cm_ms_node_a_{suffix}';
            DELETE FROM manage_projects
            WHERE project_id IN ('cm_proj_node_a_{suffix}', 'cm_proj_node_b_{suffix}');
            """
        ),
        "expected": ("里程碑节点与需求必须属于同一项目",),
        "covers": ("trg_validate_milestone_node_scope",),
        "covers_messages": ("里程碑节点与需求必须属于同一项目",),
    },
    {
        "case_id": "milestone_node_milestone_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_snap_ms_missing_{suffix}', '快照缺里程碑项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_snap_ms_missing_{suffix}', 'cm_proj_snap_ms_missing_{suffix}', 'top_level', 'draft', '快照需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_milestone_nodes (
              snapshot_id, milestone_id, requirement_id, requirement_type, status, title, order_index
            )
            VALUES (
              'cm_snap_missing_ms_{suffix}',
              'cm_ms_missing_node_{suffix}',
              'cm_req_snap_ms_missing_{suffix}',
              'top_level',
              'draft',
              '快照缺里程碑-{suffix}',
              0
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_milestone_nodes WHERE snapshot_id = 'cm_snap_missing_ms_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_snap_ms_missing_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_snap_ms_missing_{suffix}';
            """
        ),
        "expected": ("里程碑 cm_ms_missing_node_",),
        "covers": ("trg_validate_milestone_node_scope",),
        "covers_messages": ("里程碑 % 不存在",),
    },
    {
        "case_id": "milestone_node_requirement_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_snap_req_missing_{suffix}', '快照缺需求项目-{suffix}', 'active');

            INSERT INTO manage_milestones (milestone_id, project_id, name, milestone_type, is_baseline)
            VALUES (
              'cm_ms_snap_req_missing_{suffix}',
              'cm_proj_snap_req_missing_{suffix}',
              '快照里程碑-{suffix}',
              'baseline',
              TRUE
            );
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_milestone_nodes (
              snapshot_id, milestone_id, requirement_id, requirement_type, status, title, order_index
            )
            VALUES (
              'cm_snap_missing_req_{suffix}',
              'cm_ms_snap_req_missing_{suffix}',
              'cm_req_missing_snap_{suffix}',
              'top_level',
              'draft',
              '快照缺需求-{suffix}',
              0
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_milestone_nodes WHERE snapshot_id = 'cm_snap_missing_req_{suffix}';
            DELETE FROM manage_milestones WHERE milestone_id = 'cm_ms_snap_req_missing_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_snap_req_missing_{suffix}';
            """
        ),
        "expected": ("里程碑节点关联的需求 cm_req_missing_snap_",),
        "covers": ("trg_validate_milestone_node_scope",),
        "covers_messages": ("里程碑节点关联的需求 % 不存在或已删除",),
    },
    {
        "case_id": "change_set_cross_project_requirement",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES
              ('cm_proj_change_a_{suffix}', '约束矩阵变更项目A-{suffix}', 'active'),
              ('cm_proj_change_b_{suffix}', '约束矩阵变更项目B-{suffix}', 'active');

            INSERT INTO manage_milestones (
              milestone_id, project_id, name, milestone_type, is_baseline
            )
            VALUES (
              'cm_ms_change_a_{suffix}',
              'cm_proj_change_a_{suffix}',
              '变更里程碑-{suffix}',
              'baseline',
              TRUE
            );

            INSERT INTO manage_branches (branch_id, project_id, base_milestone_id, name, status)
            VALUES (
              'cm_branch_change_{suffix}',
              'cm_proj_change_a_{suffix}',
              'cm_ms_change_a_{suffix}',
              'branch-change-{suffix}',
              'active'
            );

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_change_b_{suffix}', 'cm_proj_change_b_{suffix}', 'top_level', 'draft', '变更需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_change_sets (change_id, branch_id, change_type, requirement_id)
            VALUES (
              'cm_change_scope_{suffix}',
              'cm_branch_change_{suffix}',
              'modified',
              'cm_req_change_b_{suffix}'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_change_sets WHERE change_id = 'cm_change_scope_{suffix}';
            DELETE FROM manage_branches WHERE branch_id = 'cm_branch_change_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_change_b_{suffix}';
            DELETE FROM manage_milestones WHERE milestone_id = 'cm_ms_change_a_{suffix}';
            DELETE FROM manage_projects
            WHERE project_id IN ('cm_proj_change_a_{suffix}', 'cm_proj_change_b_{suffix}');
            """
        ),
        "expected": ("变更集与需求必须属于同一项目",),
        "covers": ("trg_validate_change_set_scope",),
        "covers_messages": ("变更集与需求必须属于同一项目",),
    },
    {
        "case_id": "change_set_branch_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_change_branch_missing_{suffix}', '变更缺分支项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_change_branch_missing_{suffix}', 'cm_proj_change_branch_missing_{suffix}', 'top_level', 'draft', '变更需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_change_sets (change_id, branch_id, change_type, requirement_id)
            VALUES (
              'cm_change_missing_branch_{suffix}',
              'cm_branch_missing_{suffix}',
              'modified',
              'cm_req_change_branch_missing_{suffix}'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_change_sets WHERE change_id = 'cm_change_missing_branch_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_change_branch_missing_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_change_branch_missing_{suffix}';
            """
        ),
        "expected": ("分支 cm_branch_missing_",),
        "covers": ("trg_validate_change_set_scope",),
        "covers_messages": ("分支 % 不存在",),
    },
    {
        "case_id": "change_set_requirement_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_change_req_missing_{suffix}', '变更缺需求项目-{suffix}', 'active');

            INSERT INTO manage_milestones (milestone_id, project_id, name, milestone_type, is_baseline)
            VALUES (
              'cm_ms_change_req_missing_{suffix}',
              'cm_proj_change_req_missing_{suffix}',
              '变更基线-{suffix}',
              'baseline',
              TRUE
            );

            INSERT INTO manage_branches (branch_id, project_id, base_milestone_id, name, status)
            VALUES (
              'cm_branch_change_req_missing_{suffix}',
              'cm_proj_change_req_missing_{suffix}',
              'cm_ms_change_req_missing_{suffix}',
              'branch-change-req-{suffix}',
              'active'
            );
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_change_sets (change_id, branch_id, change_type, requirement_id)
            VALUES (
              'cm_change_missing_req_{suffix}',
              'cm_branch_change_req_missing_{suffix}',
              'modified',
              'cm_req_missing_change_{suffix}'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_change_sets WHERE change_id = 'cm_change_missing_req_{suffix}';
            DELETE FROM manage_branches WHERE branch_id = 'cm_branch_change_req_missing_{suffix}';
            DELETE FROM manage_milestones WHERE milestone_id = 'cm_ms_change_req_missing_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_change_req_missing_{suffix}';
            """
        ),
        "expected": ("变更集关联的需求 cm_req_missing_change_",),
        "covers": ("trg_validate_change_set_scope",),
        "covers_messages": ("变更集关联的需求 % 不存在或已删除",),
    },
    {
        "case_id": "comment_cross_project_target",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES
              ('cm_proj_comment_a_{suffix}', '约束矩阵评论项目A-{suffix}', 'active'),
              ('cm_proj_comment_b_{suffix}', '约束矩阵评论项目B-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES
              ('cm_req_comment_a_{suffix}', 'cm_proj_comment_a_{suffix}', 'top_level', 'draft', '评论需求A-{suffix}'),
              ('cm_req_comment_b_{suffix}', 'cm_proj_comment_b_{suffix}', 'top_level', 'draft', '评论需求B-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_comments (comment_id, project_id, target_type, target_id, content, created_by)
            VALUES (
              'cm_comment_scope_{suffix}',
              'cm_proj_comment_a_{suffix}',
              'requirement',
              'cm_req_comment_b_{suffix}',
              '跨项目评论-{suffix}',
              'constraint-matrix'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_comments WHERE comment_id = 'cm_comment_scope_{suffix}';
            DELETE FROM manage_requirements
            WHERE req_id IN ('cm_req_comment_a_{suffix}', 'cm_req_comment_b_{suffix}');
            DELETE FROM manage_projects
            WHERE project_id IN ('cm_proj_comment_a_{suffix}', 'cm_proj_comment_b_{suffix}');
            """
        ),
        "expected": ("评论所属项目与目标对象不一致",),
        "covers": ("trg_validate_comment_scope",),
        "covers_messages": ("评论所属项目与目标对象不一致",),
    },
    {
        "case_id": "comment_invalid_target_type",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_comment_invalid_type_{suffix}', '评论类型非法项目-{suffix}', 'active');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_comments (comment_id, project_id, target_type, target_id, content, created_by)
            VALUES (
              'cm_comment_invalid_type_{suffix}',
              'cm_proj_comment_invalid_type_{suffix}',
              'story',
              'cm_target_invalid_{suffix}',
              '非法评论类型-{suffix}',
              'constraint-matrix'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_comments WHERE comment_id = 'cm_comment_invalid_type_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_comment_invalid_type_{suffix}';
            """
        ),
        "expected": ("不支持的评论目标类型",),
        "covers": ("trg_validate_comment_scope",),
        "covers_messages": ("不支持的评论目标类型 %",),
    },
    {
        "case_id": "comment_target_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_comment_missing_target_{suffix}', '评论目标缺失项目-{suffix}', 'active');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_comments (comment_id, project_id, target_type, target_id, content, created_by)
            VALUES (
              'cm_comment_missing_target_{suffix}',
              'cm_proj_comment_missing_target_{suffix}',
              'requirement',
              'cm_req_comment_missing_{suffix}',
              '评论目标缺失-{suffix}',
              'constraint-matrix'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_comments WHERE comment_id = 'cm_comment_missing_target_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_comment_missing_target_{suffix}';
            """
        ),
        "expected": ("评论目标 cm_req_comment_missing_",),
        "covers": ("trg_validate_comment_scope",),
        "covers_messages": ("评论目标 % 不存在或已删除",),
    },
    {
        "case_id": "comment_reply_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES ('cm_proj_comment_reply_missing_{suffix}', '评论回复缺失项目-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES ('cm_req_comment_reply_missing_{suffix}', 'cm_proj_comment_reply_missing_{suffix}', 'top_level', 'draft', '评论回复需求-{suffix}');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_comments (comment_id, project_id, target_type, target_id, content, reply_to_id, created_by)
            VALUES (
              'cm_comment_reply_missing_{suffix}',
              'cm_proj_comment_reply_missing_{suffix}',
              'requirement',
              'cm_req_comment_reply_missing_{suffix}',
              '评论回复缺失-{suffix}',
              'cm_comment_missing_reply_{suffix}',
              'constraint-matrix'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_comments WHERE comment_id = 'cm_comment_reply_missing_{suffix}';
            DELETE FROM manage_requirements WHERE req_id = 'cm_req_comment_reply_missing_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_comment_reply_missing_{suffix}';
            """
        ),
        "expected": ("被回复的评论 cm_comment_missing_reply_",),
        "covers": ("trg_validate_comment_scope",),
        "covers_messages": ("被回复的评论 % 不存在或已删除",),
    },
    {
        "case_id": "comment_reply_cross_project",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_projects (project_id, name, status)
            VALUES
              ('cm_proj_comment_reply_a_{suffix}', '评论回复项目A-{suffix}', 'active'),
              ('cm_proj_comment_reply_b_{suffix}', '评论回复项目B-{suffix}', 'active');

            INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
            VALUES
              ('cm_req_comment_reply_a_{suffix}', 'cm_proj_comment_reply_a_{suffix}', 'top_level', 'draft', '评论回复需求A-{suffix}'),
              ('cm_req_comment_reply_b_{suffix}', 'cm_proj_comment_reply_b_{suffix}', 'top_level', 'draft', '评论回复需求B-{suffix}');

            INSERT INTO manage_comments (comment_id, project_id, target_type, target_id, content, created_by)
            VALUES (
              'cm_comment_reply_source_{suffix}',
              'cm_proj_comment_reply_b_{suffix}',
              'requirement',
              'cm_req_comment_reply_b_{suffix}',
              '源评论-{suffix}',
              'constraint-matrix'
            );
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_comments (comment_id, project_id, target_type, target_id, content, reply_to_id, created_by)
            VALUES (
              'cm_comment_reply_cross_{suffix}',
              'cm_proj_comment_reply_a_{suffix}',
              'requirement',
              'cm_req_comment_reply_a_{suffix}',
              '跨项目回复-{suffix}',
              'cm_comment_reply_source_{suffix}',
              'constraint-matrix'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_comments
            WHERE comment_id IN ('cm_comment_reply_cross_{suffix}', 'cm_comment_reply_source_{suffix}');
            DELETE FROM manage_requirements
            WHERE req_id IN ('cm_req_comment_reply_a_{suffix}', 'cm_req_comment_reply_b_{suffix}');
            DELETE FROM manage_projects
            WHERE project_id IN ('cm_proj_comment_reply_a_{suffix}', 'cm_proj_comment_reply_b_{suffix}');
            """
        ),
        "expected": ("评论回复必须发生在同一项目内",),
        "covers": ("trg_validate_comment_scope",),
        "covers_messages": ("评论回复必须发生在同一项目内",),
    },
    {
        "case_id": "audit_log_project_product_mismatch",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_products (product_id, name, status)
            VALUES
              ('cm_prod_audit_a_{suffix}', '约束矩阵审计产品A-{suffix}', 'active'),
              ('cm_prod_audit_b_{suffix}', '约束矩阵审计产品B-{suffix}', 'active');

            INSERT INTO manage_projects (project_id, name, status, product_id)
            VALUES (
              'cm_proj_audit_a_{suffix}',
              '约束矩阵审计项目A-{suffix}',
              'active',
              'cm_prod_audit_a_{suffix}'
            );
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_audit_logs (log_id, project_id, product_id, actor, action)
            VALUES (
              'cm_log_scope_{suffix}',
              'cm_proj_audit_a_{suffix}',
              'cm_prod_audit_b_{suffix}',
              'constraint-matrix',
              'create'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_audit_logs WHERE log_id = 'cm_log_scope_{suffix}';
            DELETE FROM manage_projects WHERE project_id = 'cm_proj_audit_a_{suffix}';
            DELETE FROM manage_products
            WHERE product_id IN ('cm_prod_audit_a_{suffix}', 'cm_prod_audit_b_{suffix}');
            """
        ),
        "expected": ("审计日志中的产品与项目归属不一致",),
        "covers": ("trg_validate_audit_log_scope",),
        "covers_messages": ("审计日志中的产品与项目归属不一致",),
    },
    {
        "case_id": "audit_log_project_missing",
        "kind": "trigger_scope",
        "setup_sql": _sql(
            """
            INSERT INTO manage_products (product_id, name, status)
            VALUES ('cm_prod_audit_missing_proj_{suffix}', '审计缺项目产品-{suffix}', 'active');
            """
        ),
        "sql": _sql(
            """
            INSERT INTO manage_audit_logs (log_id, project_id, product_id, actor, action)
            VALUES (
              'cm_log_missing_proj_{suffix}',
              'cm_proj_missing_audit_{suffix}',
              'cm_prod_audit_missing_proj_{suffix}',
              'constraint-matrix',
              'create'
            );
            """
        ),
        "cleanup_sql": _sql(
            """
            DELETE FROM manage_audit_logs WHERE log_id = 'cm_log_missing_proj_{suffix}';
            DELETE FROM manage_products WHERE product_id = 'cm_prod_audit_missing_proj_{suffix}';
            """
        ),
        "expected": ("审计日志关联的项目 cm_proj_missing_audit_",),
        "covers": ("trg_validate_audit_log_scope",),
        "covers_messages": ("审计日志关联的项目 % 不存在",),
    },
]


@pytest.fixture(scope="module")
def real_query_env() -> dict[str, Any]:
    settings = get_default_connection()
    db = DatabaseManager()
    db.connect(**settings)

    original_query_db = query.db
    query.db = db
    try:
        yield {
            "db": db,
            "execute": lambda sql: query.execute_query(query.QueryRequest(sql=sql)),
        }
    finally:
        query.db = original_query_db
        db.disconnect()


def _render(sql_template: str, suffix: str) -> str:
    return sql_template.format(suffix=suffix)


def _record_case(
    recorder,
    *,
    case: dict[str, Any],
    outcome: str,
    detail: str,
) -> None:
    recorder(
        {
            "case_id": case["case_id"],
            "kind": case["kind"],
            "outcome": outcome,
            "detail": detail,
        }
    )


def _assert_error_detail(case: dict[str, Any], detail: str) -> None:
    for expected in case["expected"]:
        assert expected in detail


def test_constraint_matrix_covers_all_runtime_triggers() -> None:
    schema_text = SCHEMA_PATCH_SQL.read_text(encoding="utf-8")
    trigger_names = {
        match.group(1)
        for match in re.finditer(r"create trigger\s+([a-zA-Z0-9_]+)", schema_text, flags=re.IGNORECASE)
    }
    covered_triggers = {
        trigger_name
        for case in CONSTRAINT_CASES
        for trigger_name in case.get("covers", ())
    }

    assert trigger_names.issubset(covered_triggers)


def test_runtime_matrix_covers_all_reachable_trigger_messages() -> None:
    covered_messages = {
        message
        for case in CONSTRAINT_CASES
        for message in case.get("covers_messages", ())
    }
    assert EXPECTED_TRIGGER_MESSAGES == covered_messages


def test_schema_catalog_contains_all_expected_constraints(real_query_env) -> None:
    db = real_query_env["db"]

    constraints = db.execute(
        """
        SELECT c.conname, c.contype
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'public'
          AND t.relname LIKE 'manage_%'
        """
    )["rows"]

    primary_keys = {row["conname"] for row in constraints if row["contype"] == "p"}
    unique_constraints = {row["conname"] for row in constraints if row["contype"] == "u"}
    check_constraints = {row["conname"] for row in constraints if row["contype"] == "c"}
    foreign_keys = {row["conname"] for row in constraints if row["contype"] == "f"}

    not_null_columns = {
        f"{row['table_name']}.{row['column_name']}"
        for row in db.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name LIKE 'manage_%'
              AND is_nullable = 'NO'
            """
        )["rows"]
    }

    triggers = {
        row["tgname"]
        for row in db.execute(
            """
            SELECT tg.tgname
            FROM pg_trigger tg
            JOIN pg_class t ON t.oid = tg.tgrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'public'
              AND t.relname LIKE 'manage_%'
              AND tg.tgisinternal = FALSE
            """
        )["rows"]
    }

    assert primary_keys == EXPECTED_PRIMARY_KEYS
    assert unique_constraints == EXPECTED_UNIQUE_CONSTRAINTS
    assert check_constraints == EXPECTED_CHECK_CONSTRAINTS
    assert foreign_keys == EXPECTED_FOREIGN_KEYS
    assert not_null_columns == EXPECTED_NOT_NULL_COLUMNS
    assert triggers == EXPECTED_TRIGGERS


@pytest.mark.parametrize(
    "case",
    CONSTRAINT_CASES,
    ids=[case["case_id"] for case in CONSTRAINT_CASES],
)
def test_constraint_integrity_matrix_cases(
    real_query_env,
    case: dict[str, Any],
    constraint_matrix_recorder,
) -> None:
    suffix = uuid.uuid4().hex[:8]
    db = real_query_env["db"]
    execute = real_query_env["execute"]

    setup_sql = case.get("setup_sql")
    cleanup_sql = case.get("cleanup_sql")
    detail = ""
    outcome = "unexpected-success"

    try:
        if setup_sql:
            db.execute(_render(setup_sql, suffix))

        execute(_render(case["sql"], suffix))
    except HTTPException as exc:
        detail = str(exc.detail)
        assert exc.status_code == 400
        _assert_error_detail(case, detail)
        outcome = "matched"
    finally:
        if cleanup_sql:
            db.execute(_render(cleanup_sql, suffix))
        _record_case(
            constraint_matrix_recorder,
            case=case,
            outcome=outcome,
            detail=detail,
        )

    assert outcome == "matched", f"{case['case_id']} 应触发约束错误，但实际执行成功"
