-- ============================================================
-- Benchmark Data Generator
-- 基于 requirements_db.sql 的现有表结构批量生成万级测试数据
-- 仅生成数据，不修改建表结构
-- 可重复执行：会先清理此前生成的 b* / blog_* 基准数据
-- ============================================================
--
-- 数据规模：
--   Products: 10
--   Product Members: 60 (10×6)
--   Projects: 20 (2 per product)
--   Requirements: 10,000 (500 per project)
--   Test Cases: 500 (25 per project)
--   Defects: 500 (25 per project)
--   Milestones: 100 (5 per project)
--   Branches: 200 (10 per project)
--   Change Sets: 1000 (5 per branch)
--   Audit Logs: 2000 (100 per project)
--   Requirement-Test Links: ~500
--   Requirement Links: ~1000
--   Project Members: ~120
-- ============================================================

BEGIN;

-- ============================================================
-- 0. Cleanup
-- ============================================================

DELETE FROM manage_audit_logs
WHERE log_id LIKE 'blog_%';

DELETE FROM manage_change_sets
WHERE change_id LIKE 'bcs_%';

DELETE FROM manage_branches
WHERE branch_id LIKE 'bbranch_%';

DELETE FROM manage_milestone_nodes
WHERE snapshot_id LIKE 'bsnap_%';

DELETE FROM manage_milestones
WHERE milestone_id LIKE 'bms_%';

DELETE FROM manage_defects
WHERE defect_id LIKE 'bdef_%';

DELETE FROM manage_requirement_links
WHERE source_req_id LIKE 'breq_%'
   OR target_req_id LIKE 'breq_%';

DELETE FROM manage_requirement_test_links
WHERE requirement_id LIKE 'breq_%'
   OR test_case_id LIKE 'btc_%';

DELETE FROM manage_test_cases
WHERE test_case_id LIKE 'btc_%';

DELETE FROM manage_requirements
WHERE req_id LIKE 'breq_%';

DELETE FROM manage_projects
WHERE project_id LIKE 'bproj_%';

DELETE FROM manage_product_members
WHERE product_id LIKE 'bprod_%'
   OR user_id LIKE 'bench_user_%';

DELETE FROM manage_products
WHERE product_id LIKE 'bprod_%';

DELETE FROM manage_project_members
WHERE project_id LIKE 'bproj_%';

-- ============================================================
-- 1. Products: 10
-- ============================================================

INSERT INTO manage_products (
    product_id,
    name,
    description,
    status,
    roadmap,
    version,
    tags,
    created_by,
    created_at,
    updated_at
)
SELECT
    'bprod_' || lpad(gs::text, 3, '0') AS product_id,
    'Benchmark Product ' || gs AS name,
    '用于索引、聚合、关联查询压测的基准产品 ' || gs AS description,
    CASE
        WHEN gs = 5 THEN 'archived'
        ELSE 'active'
    END AS status,
    '2026-Q' || ((gs - 1) % 4 + 1) || ' benchmark roadmap' AS roadmap,
    '10.' || gs || '.0' AS version,
    jsonb_build_array(
        'benchmark',
        'product-' || gs,
        CASE WHEN gs % 2 = 0 THEN 'platform' ELSE 'embedded' END
    ) AS tags,
    'bench_seed' AS created_by,
    NOW() - make_interval(days => 240 - gs * 12) AS created_at,
    NOW() - make_interval(days => 80 - gs * 4) AS updated_at
FROM generate_series(1, 10) AS gs;

-- ============================================================
-- 1b. Project Members for Products: 60 (10 products × 6 members)
-- ============================================================

INSERT INTO manage_product_members (
    product_id,
    user_id,
    role,
    created_at,
    updated_at
)
SELECT
    'bprod_' || lpad(p.gs::text, 3, '0') AS product_id,
    'bench_user_' || lpad((((p.gs - 1) * 6) + m.gs)::text, 3, '0') AS user_id,
    CASE m.gs
        WHEN 1 THEN 'owner'
        WHEN 2 THEN 'admin'
        WHEN 3 THEN 'member'
        WHEN 4 THEN 'member'
        WHEN 5 THEN 'viewer'
        ELSE 'viewer'
    END AS role,
    NOW() - make_interval(days => 150 - p.gs * 5 - m.gs) AS created_at,
    NOW() - make_interval(days => 60 - p.gs * 2 - m.gs) AS updated_at
FROM generate_series(1, 10) AS p(gs)
CROSS JOIN generate_series(1, 6) AS m(gs);

-- ============================================================
-- 2. Projects: 20 (2 per product)
-- ============================================================

INSERT INTO manage_projects (
    project_id,
    name,
    description,
    status,
    product_id,
    current_session_id,
    created_by,
    created_at,
    updated_at
)
SELECT
    'bproj_' || lpad(gs::text, 3, '0') AS project_id,
    'Benchmark Project ' || gs AS name,
    '基准项目 ' || gs || '，用于验证需求树、测试追溯、缺陷聚合与审计日志查询性能。' AS description,
    CASE
        WHEN gs IN (9, 18) THEN 'archived'
        ELSE 'active'
    END AS status,
    'bprod_' || lpad(gs::text, 3, '0') AS product_id,
    'bench-session-' || lpad(gs::text, 3, '0') AS current_session_id,
    'bench_user_' || lpad((((gs - 1) % 60) + 1)::text, 3, '0') AS created_by,
    NOW() - make_interval(days => 210 - gs * 3) AS created_at,
    NOW() - make_interval(days => 45 - (gs % 15)) AS updated_at
FROM generate_series(1, 20) AS gs;

-- ============================================================
-- 2b. Project Members for Projects: ~120
-- ============================================================

INSERT INTO manage_project_members (
    project_id,
    user_id,
    role,
    created_at
)
SELECT
    'bproj_' || lpad(p.gs::text, 3, '0') AS project_id,
    'bench_user_' || lpad((((p.gs - 1) * 6 + m.gs) % 60 + 1)::text, 3, '0') AS user_id,
    CASE m.gs
        WHEN 1 THEN 'owner'
        WHEN 2 THEN 'admin'
        WHEN 3 THEN 'member'
        WHEN 4 THEN 'member'
        WHEN 5 THEN 'viewer'
        ELSE 'viewer'
    END AS role,
    NOW() - make_interval(days => 180 - p.gs * 2 - m.gs * 3) AS created_at
FROM generate_series(1, 20) AS p(gs)
CROSS JOIN generate_series(1, 6) AS m(gs);

-- ============================================================
-- 3. Requirements: 10,000
-- 每项目 500 条:
--   top_level = 50
--   low_level = 150
--   task = 300
-- 比例约 1 : 3 : 6
-- ============================================================

WITH req_seed AS (
    SELECT
        gs AS req_num,
        ((gs - 1) / 500) + 1 AS project_num,
        ((gs - 1) % 500) + 1 AS local_num
    FROM generate_series(1, 10000) AS gs
)
INSERT INTO manage_requirements (
    req_id,
    project_id,
    requirement_type,
    status,
    title,
    description,
    priority,
    assignee,
    tags,
    due_date,
    parent_id,
    order_index,
    source_req_id,
    source_level,
    custom_fields,
    is_planned,
    created_by,
    created_at,
    updated_by,
    updated_at,
    deleted
)
SELECT
    'breq_' || lpad(req_num::text, 5, '0') AS req_id,
    'bproj_' || lpad(project_num::text, 3, '0') AS project_id,
    CASE
        WHEN local_num <= 50 THEN 'top_level'
        WHEN local_num <= 200 THEN 'low_level'
        ELSE 'task'
    END AS requirement_type,
    CASE
        WHEN req_num % 41 = 0 THEN 'archived'
        WHEN req_num % 13 = 0 THEN 'completed'
        WHEN req_num % 7 IN (0, 1) THEN 'in_progress'
        WHEN req_num % 5 = 0 THEN 'under_review'
        WHEN req_num % 3 = 0 THEN 'confirmed'
        ELSE 'draft'
    END AS status,
    CASE
        WHEN local_num <= 50 THEN 'Top Requirement P' || project_num || '-' || lpad(local_num::text, 4, '0')
        WHEN local_num <= 200 THEN 'Low Requirement P' || project_num || '-' || lpad((local_num - 50)::text, 4, '0')
        ELSE 'Task P' || project_num || '-' || lpad((local_num - 200)::text, 4, '0')
    END AS title,
    CASE
        WHEN local_num <= 50 THEN '项目 ' || project_num || ' 的顶层业务目标需求。'
        WHEN local_num <= 200 THEN '项目 ' || project_num || ' 的细化功能需求，挂载在对应顶层需求下。'
        ELSE '项目 ' || project_num || ' 的执行任务，挂载在对应层级需求下。'
    END AS description,
    CASE
        WHEN req_num % 10 IN (0, 1) THEN 'high'
        WHEN req_num % 10 IN (2, 3, 4, 5) THEN 'medium'
        ELSE 'low'
    END AS priority,
    CASE
        WHEN req_num % 8 = 0 THEN NULL
        ELSE 'bench_user_' || lpad((((project_num - 1) * 7 + req_num) % 60 + 1)::text, 3, '0')
    END AS assignee,
    jsonb_build_array(
        'benchmark',
        'product-' || ((project_num - 1) / 2 + 1),
        'project-' || project_num,
        CASE
            WHEN local_num <= 50 THEN 'top_level'
            WHEN local_num <= 200 THEN 'low_level'
            ELSE 'task'
        END
    ) AS tags,
    CASE
        WHEN req_num % 9 = 0 THEN NULL
        ELSE to_char(CURRENT_DATE + ((req_num % 120) - 30), 'YYYY-MM-DD')
    END AS due_date,
    CASE
        WHEN local_num <= 50 THEN NULL
        WHEN local_num <= 200 THEN
            'breq_' || lpad((((project_num - 1) * 500) + (1 + ((local_num - 51) / 3)))::text, 5, '0')
        ELSE
            'breq_' || lpad((((project_num - 1) * 500) + (51 + ((local_num - 201) % 150 / 5))::text, 5, '0')
    END AS parent_id,
    CASE
        WHEN local_num <= 50 THEN local_num - 1
        WHEN local_num <= 200 THEN (local_num - 51) % 3
        ELSE (local_num - 201) / 5
    END AS order_index,
    NULL AS source_req_id,
    NULL AS source_level,
    jsonb_build_object(
        'seed', req_num,
        'project_num', project_num,
        'local_num', local_num,
        'layer',
        CASE
            WHEN local_num <= 50 THEN 'top_level'
            WHEN local_num <= 200 THEN 'low_level'
            ELSE 'task'
        END
    ) AS custom_fields,
    CASE WHEN req_num % 5 <> 0 THEN TRUE ELSE FALSE END AS is_planned,
    'bench_user_' || lpad(((req_num + 11) % 60 + 1)::text, 3, '0') AS created_by,
    NOW() - make_interval(days => 180 - (req_num % 150)) AS created_at,
    'bench_user_' || lpad(((req_num + 23) % 60 + 1)::text, 3, '0') AS updated_by,
    NOW() - make_interval(days => 20 - (req_num % 18)) AS updated_at,
    CASE
        WHEN req_num % 53 = 0 THEN TRUE
        ELSE FALSE
    END AS deleted
FROM req_seed;

-- ============================================================
-- 4. Test Cases: 500 (25 per project)
-- ============================================================

WITH tc_seed AS (
    SELECT
        gs AS tc_num,
        ((gs - 1) / 25) + 1 AS project_num,
        ((gs - 1) % 25) + 1 AS local_num
    FROM generate_series(1, 500) AS gs
)
INSERT INTO manage_test_cases (
    test_case_id,
    project_id,
    title,
    description,
    status,
    source,
    created_by,
    created_at
)
SELECT
    'btc_' || lpad(tc_num::text, 5, '0') AS test_case_id,
    'bproj_' || lpad(project_num::text, 3, '0') AS project_id,
    'Benchmark Test Case P' || project_num || '-' || lpad(local_num::text, 3, '0') AS title,
    '项目 ' || project_num || ' 的功能/回归测试用例 ' || local_num || '。' AS description,
    CASE
        WHEN tc_num % 11 = 0 THEN 'deprecated'
        WHEN tc_num % 4 = 0 THEN 'draft'
        ELSE 'active'
    END AS status,
    'breq_' || lpad((((project_num - 1) * 500) + ((local_num * 7 - 1) % 500) + 1)::text, 5, '0') AS source,
    'bench_user_' || lpad(((tc_num + 5) % 60 + 1)::text, 3, '0') AS created_by,
    NOW() - make_interval(days => 120 - (tc_num % 90)) AS created_at
FROM tc_seed;

INSERT INTO manage_requirement_test_links (
    requirement_id,
    test_case_id,
    link_type,
    created_at
)
SELECT
    'breq_' || lpad((((project_num - 1) * 500) + ((local_num * 7 - 1) % 500) + 1)::text, 5, '0') AS requirement_id,
    'btc_' || lpad(tc_num::text, 5, '0') AS test_case_id,
    CASE
        WHEN tc_num % 6 = 0 THEN 'regression'
        WHEN tc_num % 4 = 0 THEN 'coverage'
        ELSE 'verification'
    END AS link_type,
    NOW() - make_interval(days => 90 - (tc_num % 60)) AS created_at
FROM (
    SELECT
        gs AS tc_num,
        ((gs - 1) / 25) + 1 AS project_num,
        ((gs - 1) % 25) + 1 AS local_num
    FROM generate_series(1, 500) AS gs
) AS link_seed;

-- ============================================================
-- 5. Defects: 500 (25 per project)
-- ============================================================

WITH def_seed AS (
    SELECT
        gs AS defect_num,
        ((gs - 1) / 25) + 1 AS project_num,
        ((gs - 1) % 25) + 1 AS local_num
    FROM generate_series(1, 500) AS gs
)
INSERT INTO manage_defects (
    defect_id,
    project_id,
    requirement_id,
    title,
    reproduce_steps,
    severity,
    priority,
    status,
    reporter,
    dev_assignee,
    tester_assignee,
    current_assignee,
    created_by,
    created_at,
    updated_by,
    updated_at
)
SELECT
    'bdef_' || lpad(defect_num::text, 5, '0') AS defect_id,
    'bproj_' || lpad(project_num::text, 3, '0') AS project_id,
    'breq_' || lpad((((project_num - 1) * 500) + ((local_num * 9 - 1) % 500) + 1)::text, 5, '0') AS requirement_id,
    'Benchmark Defect P' || project_num || '-' || lpad(local_num::text, 3, '0') AS title,
    '1. 打开项目 ' || project_num || E'\n'
    || '2. 执行场景 ' || local_num || E'\n'
    || '3. 观察功能偏差与日志输出' AS reproduce_steps,
    CASE
        WHEN defect_num % 20 = 0 THEN 'critical'
        WHEN defect_num % 6 = 0 THEN 'high'
        WHEN defect_num % 2 = 0 THEN 'medium'
        ELSE 'low'
    END AS severity,
    CASE
        WHEN defect_num % 20 = 0 THEN 'P0'
        WHEN defect_num % 6 = 0 THEN 'P1'
        WHEN defect_num % 2 = 0 THEN 'P2'
        ELSE 'P3'
    END AS priority,
    CASE
        WHEN defect_num % 17 = 0 THEN 'rejected'
        WHEN defect_num % 13 = 0 THEN 'closed'
        WHEN defect_num % 11 = 0 THEN 'verified'
        WHEN defect_num % 7 = 0 THEN 'resolved'
        WHEN defect_num % 3 = 0 THEN 'in_progress'
        ELSE 'open'
    END AS status,
    'bench_user_' || lpad(((defect_num + 1) % 60 + 1)::text, 3, '0') AS reporter,
    'bench_user_' || lpad(((defect_num + 7) % 60 + 1)::text, 3, '0') AS dev_assignee,
    'bench_user_' || lpad(((defect_num + 13) % 60 + 1)::text, 3, '0') AS tester_assignee,
    CASE
        WHEN defect_num % 17 = 0 OR defect_num % 13 = 0 THEN NULL
        ELSE 'bench_user_' || lpad(((defect_num + 19) % 60 + 1)::text, 3, '0')
    END AS current_assignee,
    'bench_user_' || lpad(((defect_num + 3) % 60 + 1)::text, 3, '0') AS created_by,
    NOW() - make_interval(days => 110 - (defect_num % 85)) AS created_at,
    'bench_user_' || lpad(((defect_num + 9) % 60 + 1)::text, 3, '0') AS updated_by,
    NOW() - make_interval(days => 18 - (defect_num % 14)) AS updated_at
FROM def_seed;

-- ============================================================
-- 6. Milestones: 100 (5 per project)
-- ============================================================

WITH ms_seed AS (
    SELECT
        gs AS milestone_num,
        ((gs - 1) / 5) + 1 AS project_num,
        ((gs - 1) % 5) + 1 AS local_num
    FROM generate_series(1, 100) AS gs
)
INSERT INTO manage_milestones (
    milestone_id,
    project_id,
    name,
    description,
    message,
    milestone_type,
    is_baseline,
    sprint,
    version,
    tags,
    metadata,
    created_by,
    created_at
)
SELECT
    'bms_' || lpad(milestone_num::text, 4, '0') AS milestone_id,
    'bproj_' || lpad(project_num::text, 3, '0') AS project_id,
    'Benchmark Milestone P' || project_num || '-' || local_num AS name,
    '项目 ' || project_num || ' 的阶段里程碑 ' || local_num || '。' AS description,
    CASE local_num
        WHEN 1 THEN '初始化基线'
        WHEN 2 THEN '需求收敛'
        WHEN 3 THEN '开发分支冻结'
        WHEN 4 THEN '集成验证'
        ELSE '回归收尾'
    END AS message,
    CASE local_num
        WHEN 1 THEN 'baseline'
        WHEN 3 THEN 'branch'
        WHEN 5 THEN 'merge'
        ELSE 'regular'
    END AS milestone_type,
    CASE
        WHEN local_num = 1 THEN TRUE
        ELSE FALSE
    END AS is_baseline,
    'Sprint-2026-' || lpad((project_num + local_num + 8)::text, 2, '0') AS sprint,
    '10.' || project_num || '.' || local_num AS version,
    jsonb_build_array('benchmark', 'project-' || project_num, 'milestone-' || local_num) AS tags,
    jsonb_build_object(
        'seed', milestone_num,
        'project_num', project_num,
        'local_num', local_num
    ) AS metadata,
    'bench_user_' || lpad(((milestone_num + 2) % 60 + 1)::text, 3, '0') AS created_by,
    NOW() - make_interval(days => 140 - (milestone_num % 100)) AS created_at
FROM ms_seed;

-- ============================================================
-- 7. Branches: 200 (10 per project)
-- ============================================================

WITH branch_seed AS (
    SELECT
        gs AS branch_num,
        ((gs - 1) / 10) + 1 AS project_num,
        ((gs - 1) % 10) + 1 AS local_num
    FROM generate_series(1, 200) AS gs
)
INSERT INTO manage_branches (
    branch_id,
    project_id,
    base_milestone_id,
    name,
    status,
    metadata,
    created_by,
    created_at,
    updated_at
)
SELECT
    'bbranch_' || lpad(branch_num::text, 4, '0') AS branch_id,
    'bproj_' || lpad(project_num::text, 3, '0') AS project_id,
    'bms_' || lpad((((project_num - 1) * 5) + ((local_num - 1) % 5 + 1))::text, 4, '0') AS base_milestone_id,
    CASE local_num
        WHEN 1 THEN 'feature/benchmark-core-' || project_num
        WHEN 2 THEN 'feature/benchmark-ui-' || project_num
        WHEN 3 THEN 'fix/benchmark-hotfix-' || project_num
        ELSE 'refactor/benchmark-sync-' || project_num
    END AS name,
    CASE
        WHEN branch_num % 13 = 0 THEN 'closed'
        WHEN branch_num % 9 = 0 THEN 'merged'
        WHEN branch_num % 5 = 0 THEN 'under_review'
        ELSE 'active'
    END AS status,
    jsonb_build_object(
        'project_num', project_num,
        'local_num', local_num,
        'source', 'benchmark'
    ) AS metadata,
    'bench_user_' || lpad(((branch_num + 4) % 60 + 1)::text, 3, '0') AS created_by,
    NOW() - make_interval(days => 95 - (branch_num % 70)) AS created_at,
    NOW() - make_interval(days => 12 - (branch_num % 10)) AS updated_at
FROM branch_seed;

-- ============================================================
-- 8. Change Sets: 1000 (5 per branch, 200 branches)
-- ============================================================

WITH cs_seed AS (
    SELECT
        gs AS change_num,
        ((gs - 1) / 5) + 1 AS branch_num,
        (((((gs - 1) / 5) - 1) / 10) + 1) AS project_num
    FROM generate_series(1, 1000) AS gs
)
INSERT INTO manage_change_sets (
    change_id,
    branch_id,
    change_type,
    requirement_id,
    before_data,
    after_data,
    created_by,
    created_at
)
SELECT
    'bcs_' || lpad(change_num::text, 5, '0') AS change_id,
    'bbranch_' || lpad(branch_num::text, 4, '0') AS branch_id,
    CASE
        WHEN change_num % 10 = 0 THEN 'deleted'
        WHEN change_num % 6 = 0 THEN 'moved'
        WHEN change_num % 2 = 0 THEN 'modified'
        ELSE 'added'
    END AS change_type,
    'breq_' || lpad((((project_num - 1) * 500) + ((change_num * 17 - 1) % 500) + 1)::text, 5, '0') AS requirement_id,
    CASE
        WHEN change_num % 10 = 0 THEN
            jsonb_build_object('status', 'confirmed', 'order_index', change_num % 8)
        WHEN change_num % 2 = 0 THEN
            jsonb_build_object('status', 'draft', 'order_index', change_num % 8)
        ELSE NULL
    END AS before_data,
    CASE
        WHEN change_num % 10 = 0 THEN NULL
        ELSE jsonb_build_object(
            'status',
            CASE
                WHEN change_num % 9 = 0 THEN 'completed'
                WHEN change_num % 4 = 0 THEN 'in_progress'
                ELSE 'confirmed'
            END,
            'order_index', (change_num + 2) % 8,
            'changed_by', 'bench_user_' || lpad(((change_num + 15) % 48 + 1)::text, 3, '0')
        )
    END AS after_data,
    'bench_user_' || lpad(((change_num + 15) % 60 + 1)::text, 3, '0') AS created_by,
    NOW() - make_interval(days => 70 - (change_num % 50)) AS created_at
FROM cs_seed;

-- ============================================================
-- 9. Audit Logs: 2000 (100 per project)
-- ============================================================

WITH log_seed AS (
    SELECT
        gs AS log_num,
        ((gs - 1) / 100) + 1 AS project_num,
        ((gs - 1) / 100) + 1 AS product_num
    FROM generate_series(1, 2000) AS gs
)
INSERT INTO manage_audit_logs (
    log_id,
    project_id,
    product_id,
    actor,
    action,
    target_type,
    target_id,
    detail,
    created_at
)
SELECT
    'blog_' || lpad(log_num::text, 5, '0') AS log_id,
    'bproj_' || lpad(project_num::text, 3, '0') AS project_id,
    'bprod_' || lpad(product_num::text, 3, '0') AS product_id,
    'bench_user_' || lpad(((log_num + 21) % 60 + 1)::text, 3, '0') AS actor,
    CASE (log_num % 7)
        WHEN 0 THEN '创建项目'
        WHEN 1 THEN '更新需求'
        WHEN 2 THEN '创建测试用例'
        WHEN 3 THEN '创建缺陷'
        WHEN 4 THEN '创建里程碑'
        WHEN 5 THEN '提交变更集'
        ELSE '更新分支状态'
    END AS action,
    CASE (log_num % 7)
        WHEN 0 THEN 'project'
        WHEN 1 THEN 'requirement'
        WHEN 2 THEN 'test_case'
        WHEN 3 THEN 'defect'
        WHEN 4 THEN 'milestone'
        WHEN 5 THEN 'change_set'
        ELSE 'branch'
    END AS target_type,
    CASE (log_num % 7)
        WHEN 0 THEN
            'bproj_' || lpad(project_num::text, 3, '0')
        WHEN 1 THEN
            'breq_' || lpad((((project_num - 1) * 500) + ((log_num * 7 - 1) % 500) + 1)::text, 5, '0')
        WHEN 2 THEN
            'btc_' || lpad((((project_num - 1) * 25) + ((log_num * 3 - 1) % 25) + 1)::text, 5, '0')
        WHEN 3 THEN
            'bdef_' || lpad((((project_num - 1) * 25) + ((log_num * 5 - 1) % 25) + 1)::text, 5, '0')
        WHEN 4 THEN
            'bms_' || lpad((((project_num - 1) * 5) + ((log_num % 5) + 1))::text, 4, '0')
        WHEN 5 THEN
            'bcs_' || lpad(((log_num - 1) % 1000 + 1)::text, 5, '0')
        ELSE
            'bbranch_' || lpad((((project_num - 1) * 10) + ((log_num % 10) + 1))::text, 4, '0')
    END AS target_id,
    jsonb_build_object(
        'source', 'benchmark',
        'project_num', project_num,
        'product_num', product_num,
        'seed', log_num
    ) AS detail,
    NOW() - make_interval(days => 130 - (log_num % 100)) AS created_at
FROM log_seed;

-- ============================================================
-- 10. Requirement Links: ~1000
-- Random links between requirements for tree structure testing
-- ============================================================

INSERT INTO manage_requirement_links (source_req_id, target_req_id, link_type, created_at)
SELECT
    'breq_' || lpad(((gs * 13 - 1) % 10000 + 1)::text, 5, '0') AS source_req_id,
    'breq_' || lpad(((gs * 17 + 5) % 10000 + 1)::text, 5, '0') AS target_req_id,
    CASE gs % 3
        WHEN 0 THEN 'parent'
        WHEN 1 THEN 'relates'
        ELSE 'blocks'
    END AS link_type,
    NOW() - make_interval(days => 100 - (gs % 80)) AS created_at
FROM generate_series(1, 1000) AS gs;

COMMIT;

-- ============================================================
-- 10. Refresh statistics
-- ============================================================

ANALYZE manage_products;
ANALYZE manage_product_members;
ANALYZE manage_projects;
ANALYZE manage_requirements;
ANALYZE manage_test_cases;
ANALYZE manage_requirement_test_links;
ANALYZE manage_defects;
ANALYZE manage_milestones;
ANALYZE manage_branches;
ANALYZE manage_change_sets;
ANALYZE manage_audit_logs;
ANALYZE manage_requirement_links;
