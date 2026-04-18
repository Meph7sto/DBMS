from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL = ROOT / "db" / "requirements_db.sql"
PATCH_SQL = ROOT / "db" / "requirements_db_constraints_patch.sql"
BENCHMARK_SQL = ROOT / "db" / "generate_benchmark_data.sql"


EXPECTED_TABLES = {
    "manage_products",
    "manage_product_members",
    "manage_projects",
    "manage_project_members",
    "manage_requirements",
    "manage_requirement_links",
    "manage_test_cases",
    "manage_requirement_test_links",
    "manage_defects",
    "manage_milestones",
    "manage_milestone_nodes",
    "manage_branches",
    "manage_change_sets",
    "manage_comments",
    "manage_audit_logs",
}

EXPECTED_VIEWS = {
    "v_requirement_details",
    "v_project_statistics",
}

EXPECTED_COMPLEX_FUNCTIONS = {
    "fn_requirement_trace",
    "fn_project_progress",
    "fn_milestone_delivery_risk",
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

EXPECTED_INDEXES = {
    "idx_projects_product",
    "idx_requirements_project",
    "idx_requirements_parent",
    "idx_requirements_deleted",
    "idx_test_cases_project",
    "idx_req_test_links_requirement",
    "idx_defects_project",
    "idx_milestones_project",
    "idx_branches_base_milestone",
    "idx_comments_target",
    "idx_audit_logs_target",
}


def _extract_names(pattern: str, text: str) -> set[str]:
    return {match.group(1) for match in re.finditer(pattern, text, flags=re.IGNORECASE)}


def test_schema_sql_declares_required_tables_views_functions_and_triggers() -> None:
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    patch_text = PATCH_SQL.read_text(encoding="utf-8")

    tables = _extract_names(r"create table\s+([a-zA-Z0-9_]+)", schema_text)
    views = _extract_names(r"create or replace view\s+([a-zA-Z0-9_]+)", schema_text)
    functions = _extract_names(r"create or replace function\s+([a-zA-Z0-9_]+)", schema_text)
    triggers = _extract_names(r"create trigger\s+([a-zA-Z0-9_]+)", schema_text)
    patch_triggers = _extract_names(r"create trigger\s+([a-zA-Z0-9_]+)", patch_text)
    indexes = _extract_names(r"create index\s+([a-zA-Z0-9_]+)", schema_text)

    assert EXPECTED_TABLES.issubset(tables)
    assert EXPECTED_VIEWS == views
    assert EXPECTED_COMPLEX_FUNCTIONS.issubset(functions)
    assert EXPECTED_TRIGGERS == triggers
    assert EXPECTED_TRIGGERS == patch_triggers
    assert EXPECTED_INDEXES.issubset(indexes)
    assert len(indexes) >= 35


def test_complex_query_signatures_and_benchmark_script_exist() -> None:
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")

    assert "returns table (" in schema_text.lower()
    assert "test_case_count bigint" in schema_text.lower()
    assert "completion_rate_percent numeric" in schema_text.lower()
    assert "risk_level text" in schema_text.lower()
    assert BENCHMARK_SQL.exists()
