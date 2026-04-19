#!/usr/bin/env python3
"""Run repeatable PostgreSQL performance validation and emit a Markdown report."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PSQL_BIN = Path("/mnt/w/DB/PostgreSQL/bin/psql.exe")
BENCHMARK_SQL = ROOT / "db" / "generate_benchmark_data.sql"
BENCHMARK_CLEANUP_SQL = ROOT / "db" / "cleanup_benchmark_data.sql"
DEFAULT_REPORT = ROOT / "docs" / "performance_validation_report.md"
DEMO_TABLE = "manage_requirements_perf_demo"
DEMO_INDEX = "idx_req_perf_project_deleted_order"
DEMO_PROJECT_ID = "bproj_003"


PROJECT_STATS_DIRECT_SQL = f"""
WITH req_stats AS (
    SELECT project_id,
           COUNT(*) FILTER (WHERE deleted = FALSE) AS total_requirements,
           COUNT(*) FILTER (WHERE requirement_type = 'top_level' AND deleted = FALSE) AS top_level_count,
           COUNT(*) FILTER (WHERE requirement_type = 'low_level' AND deleted = FALSE) AS low_level_count,
           COUNT(*) FILTER (WHERE status = 'completed' AND deleted = FALSE) AS completed_count,
           COUNT(*) FILTER (WHERE status = 'in_progress' AND deleted = FALSE) AS in_progress_count,
           COUNT(*) FILTER (WHERE status = 'draft' AND deleted = FALSE) AS draft_count
    FROM manage_requirements
    GROUP BY project_id
),
def_stats AS (
    SELECT project_id,
           COUNT(*) AS total_defects,
           COUNT(*) FILTER (WHERE severity = 'critical') AS critical_defects,
           COUNT(*) FILTER (WHERE status IN ('open', 'in_progress')) AS open_defects
    FROM manage_defects
    GROUP BY project_id
),
tc_stats AS (
    SELECT project_id, COUNT(*) AS total_test_cases
    FROM manage_test_cases
    GROUP BY project_id
),
ms_stats AS (
    SELECT project_id,
           COUNT(*) AS total_milestones,
           COUNT(*) FILTER (WHERE is_baseline = TRUE) AS baseline_count
    FROM manage_milestones
    GROUP BY project_id
),
br_stats AS (
    SELECT project_id, COUNT(*) AS total_branches
    FROM manage_branches
    GROUP BY project_id
)
SELECT
    p.project_id,
    p.name AS project_name,
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
LEFT JOIN tc_stats tc ON tc.project_id = p.project_id
LEFT JOIN ms_stats m ON m.project_id = p.project_id
LEFT JOIN br_stats b ON b.project_id = p.project_id
WHERE p.project_id = '{DEMO_PROJECT_ID}';
""".strip()


REQUIREMENT_DETAILS_DIRECT_SQL = f"""
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
SELECT
    r.req_id,
    r.title AS requirement_title,
    p.name AS project_name,
    COALESCE(ts.test_case_count, 0) AS test_case_count,
    COALESCE(ds.defect_count, 0) AS defect_count,
    COALESCE(ds.open_defect_count, 0) AS open_defect_count
FROM manage_requirements r
JOIN manage_projects p ON p.project_id = r.project_id
LEFT JOIN test_stats ts ON ts.requirement_id = r.req_id
LEFT JOIN defect_stats ds ON ds.requirement_id = r.req_id
WHERE r.deleted = FALSE
  AND r.project_id = '{DEMO_PROJECT_ID}'
ORDER BY r.created_at DESC
LIMIT 8;
""".strip()


@dataclass
class ExplainSummary:
    label: str
    execution_time_ms: float | None
    planning_time_ms: float | None
    node_types: list[str]
    relation_names: list[str]
    index_names: list[str]
    raw_plan: Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.getenv("DB_HOST", "localhost"))
    parser.add_argument("--port", default=os.getenv("DB_PORT", "5438"))
    parser.add_argument("--database", default=os.getenv("DB_NAME", "postgres"))
    parser.add_argument("--user", default=os.getenv("DB_USER", "postgres"))
    parser.add_argument("--password", default=os.getenv("DB_PASSWORD", "postgres"))
    parser.add_argument("--psql-bin", default=os.getenv("PSQL_BIN", str(DEFAULT_PSQL_BIN)))
    parser.add_argument("--project-id", default=DEMO_PROJECT_ID)
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--skip-import", action="store_true")
    parser.add_argument("--skip-cleanup", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    psql_bin = Path(args.psql_bin)
    report_path = Path(args.report)
    project_id = args.project_id

    if not psql_bin.exists():
        raise SystemExit(f"psql binary not found: {psql_bin}")

    context = {
        "host": args.host,
        "port": str(args.port),
        "database": args.database,
        "user": args.user,
        "password": args.password,
        "psql_bin": psql_bin,
    }

    if not args.skip_cleanup:
        run_sql_file(context, BENCHMARK_CLEANUP_SQL)
    if not args.skip_import:
        run_sql_file(context, BENCHMARK_SQL)

    setup_demo_sql = f"""
    DROP INDEX IF EXISTS public.{DEMO_INDEX};
    DROP TABLE IF EXISTS public.{DEMO_TABLE};
    CREATE TABLE public.{DEMO_TABLE} AS
    SELECT *
    FROM public.manage_requirements
    WHERE req_id LIKE 'breq_%';
    ANALYZE public.{DEMO_TABLE};
    """
    run_sql(context, setup_demo_sql)

    before_summary = run_explain_json(
        context,
        "索引前需求列表查询",
        f"""
        SELECT req_id, title, status
        FROM public.{DEMO_TABLE}
        WHERE project_id = '{project_id}' AND deleted = FALSE
        ORDER BY order_index;
        """,
    )

    run_sql(
        context,
        f"""
        CREATE INDEX IF NOT EXISTS {DEMO_INDEX}
        ON public.{DEMO_TABLE}(project_id, deleted, order_index);
        ANALYZE public.{DEMO_TABLE};
        """,
    )
    after_summary = run_explain_json(
        context,
        "索引后需求列表查询",
        f"""
        SELECT req_id, title, status
        FROM public.{DEMO_TABLE}
        WHERE project_id = '{project_id}' AND deleted = FALSE
        ORDER BY order_index;
        """,
    )

    project_view_summary = run_explain_json(
        context,
        "项目统计视图",
        f"""
        SELECT project_id, project_name, total_requirements, total_defects, completion_rate_percent
        FROM v_project_statistics
        WHERE project_id = '{project_id}';
        """,
    )
    project_direct_summary = run_explain_json(
        context,
        "项目统计直接 SQL",
        PROJECT_STATS_DIRECT_SQL.replace(DEMO_PROJECT_ID, project_id),
    )

    requirement_view_summary = run_explain_json(
        context,
        "需求详情视图",
        f"""
        SELECT req_id, requirement_title, project_name, test_case_count, defect_count, open_defect_count
        FROM v_requirement_details
        WHERE project_id = '{project_id}'
        ORDER BY requirement_created_at DESC
        LIMIT 8;
        """,
    )
    requirement_direct_summary = run_explain_json(
        context,
        "需求详情直接 SQL",
        REQUIREMENT_DETAILS_DIRECT_SQL.replace(DEMO_PROJECT_ID, project_id),
    )

    function_summaries = [
        run_explain_json(context, "需求追溯函数", f"SELECT * FROM fn_requirement_trace('{project_id}');"),
        run_explain_json(context, "项目进度函数", f"SELECT * FROM fn_project_progress('{project_id}');"),
        run_explain_json(context, "里程碑风险函数", f"SELECT * FROM fn_milestone_delivery_risk('{project_id}');"),
    ]

    report = build_report(
        project_id=project_id,
        connection_context=context,
        before_summary=before_summary,
        after_summary=after_summary,
        project_view_summary=project_view_summary,
        project_direct_summary=project_direct_summary,
        requirement_view_summary=requirement_view_summary,
        requirement_direct_summary=requirement_direct_summary,
        function_summaries=function_summaries,
    )
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote report to {report_path}")
    return 0


def run_sql_file(context: dict[str, Any], path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    run_psql(context, extra_args=["-f", str(path)])


def run_sql(context: dict[str, Any], sql: str) -> str:
    return run_psql(context, extra_args=["-c", sql])


def run_explain_json(context: dict[str, Any], label: str, sql: str) -> ExplainSummary:
    explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql.strip().rstrip(';')};"
    raw = run_psql(context, extra_args=["-t", "-A", "-c", explain_sql]).strip()
    plan_json = json.loads(raw)
    payload = plan_json[0]
    root_plan = payload["Plan"]
    node_types: list[str] = []
    relation_names: list[str] = []
    index_names: list[str] = []
    walk_plan(root_plan, node_types, relation_names, index_names)
    return ExplainSummary(
        label=label,
        execution_time_ms=payload.get("Execution Time"),
        planning_time_ms=payload.get("Planning Time"),
        node_types=dedupe(node_types),
        relation_names=dedupe(relation_names),
        index_names=dedupe(index_names),
        raw_plan=payload,
    )


def walk_plan(plan: dict[str, Any], node_types: list[str], relation_names: list[str], index_names: list[str]) -> None:
    node_type = plan.get("Node Type")
    if node_type:
        node_types.append(str(node_type))
    relation_name = plan.get("Relation Name")
    if relation_name:
        relation_names.append(str(relation_name))
    index_name = plan.get("Index Name")
    if index_name:
        index_names.append(str(index_name))
    for child in plan.get("Plans", []):
        walk_plan(child, node_types, relation_names, index_names)


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def run_psql(context: dict[str, Any], *, extra_args: list[str]) -> str:
    env = os.environ.copy()
    env["PGPASSWORD"] = context["password"]
    command = [
        str(context["psql_bin"]),
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-P",
        "pager=off",
        "-h",
        str(context["host"]),
        "-p",
        str(context["port"]),
        "-U",
        str(context["user"]),
        "-d",
        str(context["database"]),
        *extra_args,
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        cmd_text = " ".join(shlex.quote(part) for part in command)
        raise RuntimeError(
            f"psql failed with exit code {result.returncode}\n"
            f"Command: {cmd_text}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    return result.stdout


def format_ms(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.3f}"


def compare_line(before: ExplainSummary, after: ExplainSummary) -> str:
    if before.execution_time_ms is None or after.execution_time_ms is None:
        return "无法计算倍数"
    if after.execution_time_ms == 0:
        return "后者接近 0 ms"
    ratio = before.execution_time_ms / after.execution_time_ms
    if ratio >= 1:
        return f"{ratio:.2f}x 更快"
    return f"{(1 / ratio):.2f}x 更慢"


def build_summary_table(rows: list[ExplainSummary]) -> str:
    lines = [
        "| 场景 | Execution Time (ms) | Planning Time (ms) | 关键节点 | 命中索引 |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.label,
                    format_ms(row.execution_time_ms),
                    format_ms(row.planning_time_ms),
                    ", ".join(row.node_types) or "N/A",
                    ", ".join(row.index_names) or "N/A",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def build_report(
    *,
    project_id: str,
    connection_context: dict[str, Any],
    before_summary: ExplainSummary,
    after_summary: ExplainSummary,
    project_view_summary: ExplainSummary,
    project_direct_summary: ExplainSummary,
    requirement_view_summary: ExplainSummary,
    requirement_direct_summary: ExplainSummary,
    function_summaries: list[ExplainSummary],
) -> str:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    return f"""# PostgreSQL 性能验证报告

生成时间：`{generated_at}`

## 1. 执行环境

- 目标数据库：`{connection_context['database']}`
- 主机端口：`{connection_context['host']}:{connection_context['port']}`
- 执行用户：`{connection_context['user']}`
- 演示项目：`{project_id}`
- 数据脚本：`db/generate_benchmark_data.sql`
- 清理脚本：`db/cleanup_benchmark_data.sql`

## 2. 索引前后对比

{build_summary_table([before_summary, after_summary])}

结论：索引前后需求列表查询对比为 **{compare_line(before_summary, after_summary)}**。

## 3. 视图 vs 直接 SQL

{build_summary_table([project_view_summary, project_direct_summary, requirement_view_summary, requirement_direct_summary])}

项目统计视图对比：**{compare_line(project_direct_summary, project_view_summary)}**。

需求详情视图对比：**{compare_line(requirement_direct_summary, requirement_view_summary)}**。

## 4. 各类功能查询效率

{build_summary_table(function_summaries)}

## 5. 结果解读建议

- 若索引后出现 `Index Scan`、`Bitmap Heap Scan` 或命中 `{DEMO_INDEX}`，可说明索引已经参与优化，而不是只比较页面耗时。
- 若视图与直接 SQL 耗时接近，可说明 PostgreSQL 会对普通视图进行查询展开，重点应转向“视图减少应用层重复 SQL、统一统计口径”的工程价值。
- 若 `fn_milestone_delivery_risk` 明显慢于其他函数，属于正常现象，因为它同时聚合里程碑快照、依赖、缺陷、分支和变更集。

## 6. 命令记录

```bash
python scripts/run_pg_perf_validation.py --report docs/performance_validation_report.md
```
"""


if __name__ == "__main__":
    raise SystemExit(main())
