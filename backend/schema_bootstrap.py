"""Schema bootstrap helpers for the requirement management database."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = PROJECT_ROOT / "db"
SCHEMA_SQL_FILE = DB_DIR / "requirements_db.sql"
SCHEMA_PATCH_FILE = DB_DIR / "requirements_db_constraints_patch.sql"
REQUIRED_TABLES = (
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
)
REQUIRED_RUNTIME_FUNCTIONS = {
    "fn_milestone_delivery_risk": "public.fn_milestone_delivery_risk(text)",
}
PARTIAL_SCHEMA_REPAIR_SQL = dedent(
    """
    CREATE TABLE IF NOT EXISTS manage_project_members (
        id         SERIAL PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES manage_projects(project_id) ON DELETE CASCADE,
        user_id    TEXT NOT NULL,
        role       TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uk_project_member UNIQUE (project_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS manage_requirement_links (
        link_id        SERIAL PRIMARY KEY,
        source_req_id  TEXT NOT NULL REFERENCES manage_requirements(req_id) ON DELETE CASCADE,
        target_req_id  TEXT NOT NULL REFERENCES manage_requirements(req_id) ON DELETE CASCADE,
        link_type      TEXT NOT NULL CHECK (link_type IN ('blocks', 'depends_on', 'relates_to', 'duplicates')),
        created_by     TEXT,
        created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uk_req_link UNIQUE (source_req_id, target_req_id, link_type),
        CONSTRAINT chk_no_self_link CHECK (source_req_id != target_req_id)
    );

    CREATE INDEX IF NOT EXISTS idx_project_members_project ON manage_project_members(project_id);
    CREATE INDEX IF NOT EXISTS idx_project_members_user ON manage_project_members(user_id);
    CREATE INDEX IF NOT EXISTS idx_req_links_source ON manage_requirement_links(source_req_id);
    CREATE INDEX IF NOT EXISTS idx_req_links_target ON manage_requirement_links(target_req_id);
    """
).strip()
COMMENTS_REPAIR_SQL = dedent(
    """
    CREATE TABLE IF NOT EXISTS manage_comments (
        comment_id  TEXT PRIMARY KEY,
        project_id  TEXT NOT NULL REFERENCES manage_projects(project_id) ON DELETE CASCADE,
        target_type TEXT NOT NULL CHECK (target_type IN ('requirement', 'defect', 'test_case', 'milestone')),
        target_id   TEXT NOT NULL,
        content     TEXT NOT NULL,
        reply_to_id TEXT REFERENCES manage_comments(comment_id) ON DELETE SET NULL,
        created_by  TEXT NOT NULL,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted     BOOLEAN NOT NULL DEFAULT FALSE
    );

    CREATE INDEX IF NOT EXISTS idx_comments_project ON manage_comments(project_id);
    CREATE INDEX IF NOT EXISTS idx_comments_target ON manage_comments(target_type, target_id);
    CREATE INDEX IF NOT EXISTS idx_comments_created_at ON manage_comments(created_at);
    """
).strip()
COMMENTS_TRIGGER_PATCH_SQL = dedent(
    """
    CREATE OR REPLACE FUNCTION fn_validate_comment_scope()
    RETURNS TRIGGER
    LANGUAGE plpgsql
    AS $$
    DECLARE
        v_target_project_id TEXT;
        v_reply_project_id  TEXT;
    BEGIN
        CASE NEW.target_type
            WHEN 'requirement' THEN
                SELECT project_id INTO v_target_project_id
                  FROM manage_requirements
                 WHERE req_id = NEW.target_id
                   AND deleted = FALSE;
            WHEN 'defect' THEN
                SELECT project_id INTO v_target_project_id
                  FROM manage_defects
                 WHERE defect_id = NEW.target_id;
            WHEN 'test_case' THEN
                SELECT project_id INTO v_target_project_id
                  FROM manage_test_cases
                 WHERE test_case_id = NEW.target_id;
            WHEN 'milestone' THEN
                SELECT project_id INTO v_target_project_id
                  FROM manage_milestones
                 WHERE milestone_id = NEW.target_id;
            ELSE
                RAISE EXCEPTION '不支持的评论目标类型 %', NEW.target_type;
        END CASE;

        IF v_target_project_id IS NULL THEN
            RAISE EXCEPTION '评论目标 % 不存在或已删除', NEW.target_id;
        END IF;

        IF v_target_project_id <> NEW.project_id THEN
            RAISE EXCEPTION '评论所属项目与目标对象不一致';
        END IF;

        IF NEW.reply_to_id IS NOT NULL THEN
            SELECT project_id
              INTO v_reply_project_id
              FROM manage_comments
             WHERE comment_id = NEW.reply_to_id
               AND deleted = FALSE;

            IF v_reply_project_id IS NULL THEN
                RAISE EXCEPTION '被回复的评论 % 不存在或已删除', NEW.reply_to_id;
            END IF;

            IF v_reply_project_id <> NEW.project_id THEN
                RAISE EXCEPTION '评论回复必须发生在同一项目内';
            END IF;
        END IF;

        RETURN NEW;
    END;
    $$;

    DROP TRIGGER IF EXISTS trg_validate_comment_scope ON manage_comments;
    CREATE TRIGGER trg_validate_comment_scope
    BEFORE INSERT OR UPDATE OF project_id, target_type, target_id, reply_to_id
    ON manage_comments
    FOR EACH ROW
    EXECUTE FUNCTION fn_validate_comment_scope();
    """
).strip()


def ensure_requirements_schema(conn) -> dict[str, Any]:
    """Initialize the app schema for an empty database and verify required tables."""
    table_state = _required_table_state(conn)
    schema_applied = False
    patch_applied = False

    if not table_state["manage_products"]:
        _execute_sql_file(conn, SCHEMA_SQL_FILE, "核心 schema")
        schema_applied = True
        table_state = _required_table_state(conn)
        if all(table_state.values()) and SCHEMA_PATCH_FILE.exists():
            _execute_sql_file(conn, SCHEMA_PATCH_FILE, "schema 约束补丁")
            patch_applied = True
            table_state = _required_table_state(conn)
    else:
        repaired = False
        if _can_repair_comments_table(table_state):
            _execute_sql_text(conn, COMMENTS_REPAIR_SQL)
            _execute_sql_text(conn, COMMENTS_TRIGGER_PATCH_SQL)
            repaired = True
            table_state = _required_table_state(conn)
        if _can_repair_partial_schema(table_state):
            _execute_sql_text(conn, PARTIAL_SCHEMA_REPAIR_SQL)
            repaired = True
            table_state = _required_table_state(conn)
        if repaired:
            schema_applied = True
            if SCHEMA_PATCH_FILE.exists():
                _execute_sql_file(conn, SCHEMA_PATCH_FILE, "schema 约束补丁")
                patch_applied = True
                table_state = _required_table_state(conn)

    if not all(table_state.values()):
        missing = ", ".join(name for name, exists in table_state.items() if not exists)
        raise RuntimeError(
            "当前数据库缺少需求管理核心表："
            f"{missing}。请执行 db/requirements_db.sql 初始化，"
            "或通过 start.ps1 启动完整环境。"
        )

    function_state = _required_function_state(conn)
    missing_functions = [
        name for name, exists in function_state.items() if not exists
    ]
    if missing_functions and SCHEMA_PATCH_FILE.exists():
        _execute_sql_file(conn, SCHEMA_PATCH_FILE, "schema 约束补丁")
        patch_applied = True
        function_state = _required_function_state(conn)
        missing_functions = [
            name for name, exists in function_state.items() if not exists
        ]

    if missing_functions:
        missing = ", ".join(missing_functions)
        raise RuntimeError(
            "当前数据库缺少运行时必需函数："
            f"{missing}。请执行 db/requirements_db.sql 或 db/requirements_db_constraints_patch.sql 更新。"
        )

    return {
        "schema_applied": schema_applied,
        "patch_applied": patch_applied,
        "required_tables": list(REQUIRED_TABLES),
        "required_functions": list(REQUIRED_RUNTIME_FUNCTIONS),
    }


def _required_table_state(conn) -> dict[str, bool]:
    state: dict[str, bool] = {}
    with conn.cursor() as cur:
        for table_name in REQUIRED_TABLES:
            cur.execute("SELECT to_regclass(%s) IS NOT NULL AS exists", (f"public.{table_name}",))
            row = cur.fetchone()
            state[table_name] = bool(row[0]) if row else False
    return state


def _required_function_state(conn) -> dict[str, bool]:
    state: dict[str, bool] = {}
    with conn.cursor() as cur:
        for function_name, signature in REQUIRED_RUNTIME_FUNCTIONS.items():
            cur.execute(
                "SELECT to_regprocedure(%s) IS NOT NULL AS exists",
                (signature,),
            )
            row = cur.fetchone()
            state[function_name] = bool(row[0]) if row else False
    return state


def _execute_sql_file(conn, path: Path, label: str) -> None:
    if not path.exists():
        raise RuntimeError(f"{label} 文件不存在：{path}")

    sql_text = path.read_text(encoding="utf-8")
    _execute_sql_text(conn, sql_text)


def _execute_sql_text(conn, sql_text: str) -> None:
    with conn.cursor() as cur:
        cur.execute(sql_text)


def _can_repair_comments_table(table_state: dict[str, bool]) -> bool:
    return (
        table_state["manage_products"]
        and table_state["manage_projects"]
        and not table_state["manage_comments"]
    )


def _can_repair_partial_schema(table_state: dict[str, bool]) -> bool:
    return (
        table_state["manage_projects"]
        and table_state["manage_requirements"]
        and (
            not table_state["manage_project_members"]
            or not table_state["manage_requirement_links"]
        )
    )
