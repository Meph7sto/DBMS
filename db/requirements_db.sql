-- ============================================================
-- 需求管理数据库 (Requirements Management Database)
-- 基于 Semantic-Atlas Beta Interface 管理模块设计
-- 课程: 2026 Spring Database Systems Lab
-- ============================================================

-- ============================================================
-- 一、产品层 (Product Layer)
-- ============================================================

-- 产品表
CREATE TABLE manage_products (
    product_id     TEXT PRIMARY KEY,
    name           TEXT NOT NULL UNIQUE,
    description    TEXT,
    status         TEXT NOT NULL DEFAULT 'active'
                   CHECK (status IN ('active', 'archived')),
    roadmap        TEXT,
    version        TEXT,
    tags           JSONB DEFAULT '[]',
    created_by     TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 产品成员表
CREATE TABLE manage_product_members (
    id         SERIAL PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES manage_products(product_id) ON DELETE CASCADE,
    user_id    TEXT NOT NULL,
    role       TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_product_member UNIQUE (product_id, user_id)
);

-- ============================================================
-- 二、项目层 (Project Layer)
-- ============================================================

-- 项目表
CREATE TABLE manage_projects (
    project_id          TEXT PRIMARY KEY,
    name               TEXT NOT NULL UNIQUE,
    description        TEXT,
    status             TEXT NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'archived')),
    product_id         TEXT REFERENCES manage_products(product_id) ON DELETE SET NULL,
    current_session_id TEXT,
    created_by         TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 三、需求层 (Requirements Layer)
-- ============================================================

-- 需求表（树形结构，自引用 parent_id）
CREATE TABLE manage_requirements (
    req_id           TEXT PRIMARY KEY,
    project_id       TEXT NOT NULL REFERENCES manage_projects(project_id) ON DELETE CASCADE,
    requirement_type TEXT NOT NULL CHECK (requirement_type IN ('top_level', 'low_level', 'task')),
    status           TEXT NOT NULL DEFAULT 'draft'
                     CHECK (status IN ('draft', 'under_review', 'confirmed', 'in_progress', 'completed', 'archived')),
    title            TEXT NOT NULL,
    description      TEXT,
    priority         TEXT CHECK (priority IN ('low', 'medium', 'high')),
    assignee         TEXT,
    tags             JSONB DEFAULT '[]',
    due_date         TEXT,
    parent_id        TEXT REFERENCES manage_requirements(req_id) ON DELETE SET NULL,
    order_index      INTEGER NOT NULL DEFAULT 0,
    source_req_id    TEXT,
    source_level     TEXT,
    custom_fields    JSONB DEFAULT '{}',
    is_planned       BOOLEAN NOT NULL DEFAULT FALSE,
    created_by       TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by       TEXT,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted          BOOLEAN NOT NULL DEFAULT FALSE
);

-- ============================================================
-- 四、测试与缺陷管理 (Test & Defect Management)
-- ============================================================

-- 测试用例表
CREATE TABLE manage_test_cases (
    test_case_id TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL REFERENCES manage_projects(project_id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    description  TEXT,
    status       TEXT NOT NULL DEFAULT 'draft'
                 CHECK (status IN ('draft', 'active', 'deprecated')),
    source       TEXT,
    created_by   TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 需求-测试用例关联表
CREATE TABLE manage_requirement_test_links (
    link_id        SERIAL PRIMARY KEY,
    requirement_id TEXT NOT NULL REFERENCES manage_requirements(req_id) ON DELETE CASCADE,
    test_case_id   TEXT NOT NULL REFERENCES manage_test_cases(test_case_id) ON DELETE CASCADE,
    link_type      TEXT NOT NULL DEFAULT 'verification',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_req_test_link UNIQUE (requirement_id, test_case_id)
);

-- 缺陷表
CREATE TABLE manage_defects (
    defect_id        TEXT PRIMARY KEY,
    project_id       TEXT NOT NULL REFERENCES manage_projects(project_id) ON DELETE CASCADE,
    requirement_id   TEXT NOT NULL REFERENCES manage_requirements(req_id) ON DELETE CASCADE,
    title            TEXT NOT NULL,
    reproduce_steps  TEXT NOT NULL DEFAULT '',
    severity         TEXT NOT NULL DEFAULT 'medium'
                     CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    priority         TEXT NOT NULL DEFAULT 'P2'
                     CHECK (priority IN ('P0', 'P1', 'P2', 'P3')),
    status           TEXT NOT NULL DEFAULT 'open'
                     CHECK (status IN ('open', 'in_progress', 'resolved', 'verified', 'closed', 'rejected')),
    reporter         TEXT,
    dev_assignee     TEXT,
    tester_assignee  TEXT,
    current_assignee TEXT,
    created_by       TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by       TEXT,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 五、里程碑管理 (Milestone Management)
-- ============================================================

-- 里程碑表
CREATE TABLE manage_milestones (
    milestone_id   TEXT PRIMARY KEY,
    project_id     TEXT NOT NULL REFERENCES manage_projects(project_id) ON DELETE CASCADE,
    name           TEXT NOT NULL,
    description    TEXT,
    message        TEXT,
    milestone_type TEXT NOT NULL DEFAULT 'regular'
                   CHECK (milestone_type IN ('regular', 'baseline', 'branch', 'merge')),
    is_baseline    BOOLEAN NOT NULL DEFAULT FALSE,
    sprint         TEXT,
    version        TEXT,
    tags           JSONB DEFAULT '[]',
    metadata       JSONB DEFAULT '{}',
    created_by     TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 里程碑节点表（需求快照）
CREATE TABLE manage_milestone_nodes (
    snapshot_id     TEXT PRIMARY KEY,
    milestone_id    TEXT NOT NULL REFERENCES manage_milestones(milestone_id) ON DELETE CASCADE,
    requirement_id  TEXT NOT NULL,
    requirement_type TEXT,
    status          TEXT,
    title           TEXT,
    description     TEXT,
    parent_id       TEXT,
    order_index     INTEGER DEFAULT 0,
    snapshot_data   JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 六、分支与变更管理 (Branch & Change Management)
-- ============================================================

-- 分支表
CREATE TABLE manage_branches (
    branch_id        TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES manage_projects(project_id) ON DELETE CASCADE,
    base_milestone_id TEXT NOT NULL REFERENCES manage_milestones(milestone_id) ON DELETE RESTRICT,
    name            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'under_review', 'merged', 'closed')),
    metadata        JSONB DEFAULT '{}',
    created_by      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_project_branch UNIQUE (project_id, name)
);

-- 变更集表
CREATE TABLE manage_change_sets (
    change_id      TEXT PRIMARY KEY,
    branch_id      TEXT NOT NULL REFERENCES manage_branches(branch_id) ON DELETE CASCADE,
    change_type    TEXT NOT NULL CHECK (change_type IN ('added', 'modified', 'deleted', 'moved')),
    requirement_id TEXT,
    before_data    JSONB,
    after_data     JSONB,
    created_by     TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 七、审计日志 (Audit Logs)
-- ============================================================

-- 审计日志表
CREATE TABLE manage_audit_logs (
    log_id      TEXT PRIMARY KEY,
    project_id  TEXT REFERENCES manage_projects(project_id) ON DELETE SET NULL,
    product_id  TEXT,
    actor       TEXT NOT NULL,
    action      TEXT NOT NULL,
    target_type TEXT,
    target_id   TEXT,
    detail      JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 八、索引设计 (Indexes)
-- ============================================================

-- 产品表索引
CREATE INDEX idx_products_status ON manage_products(status);
CREATE INDEX idx_products_created_at ON manage_products(created_at DESC);

-- 产品成员表索引
CREATE INDEX idx_product_members_product ON manage_product_members(product_id);
CREATE INDEX idx_product_members_user ON manage_product_members(user_id);

-- 项目表索引
CREATE INDEX idx_projects_product ON manage_projects(product_id) WHERE product_id IS NOT NULL;
CREATE INDEX idx_projects_status ON manage_projects(status);
CREATE INDEX idx_projects_created_at ON manage_projects(created_at DESC);

-- 需求表索引
CREATE INDEX idx_requirements_project ON manage_requirements(project_id);
CREATE INDEX idx_requirements_parent ON manage_requirements(parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX idx_requirements_status ON manage_requirements(status);
CREATE INDEX idx_requirements_type ON manage_requirements(requirement_type);
CREATE INDEX idx_requirements_assignee ON manage_requirements(assignee) WHERE assignee IS NOT NULL;
CREATE INDEX idx_requirements_deleted ON manage_requirements(deleted) WHERE deleted = FALSE;
CREATE INDEX idx_requirements_priority ON manage_requirements(priority) WHERE priority IS NOT NULL;
CREATE INDEX idx_requirements_due_date ON manage_requirements(due_date) WHERE due_date IS NOT NULL;

-- 测试用例表索引
CREATE INDEX idx_test_cases_project ON manage_test_cases(project_id);
CREATE INDEX idx_test_cases_status ON manage_test_cases(status);

-- 需求-测试关联表索引
CREATE INDEX idx_req_test_links_requirement ON manage_requirement_test_links(requirement_id);
CREATE INDEX idx_req_test_links_test_case ON manage_requirement_test_links(test_case_id);

-- 缺陷表索引
CREATE INDEX idx_defects_project ON manage_defects(project_id);
CREATE INDEX idx_defects_requirement ON manage_defects(requirement_id);
CREATE INDEX idx_defects_status ON manage_defects(status);
CREATE INDEX idx_defects_severity ON manage_defects(severity);
CREATE INDEX idx_defects_priority ON manage_defects(priority);
CREATE INDEX idx_defects_assignee ON manage_defects(current_assignee) WHERE current_assignee IS NOT NULL;

-- 里程碑表索引
CREATE INDEX idx_milestones_project ON manage_milestones(project_id);
CREATE INDEX idx_milestones_type ON manage_milestones(milestone_type);
CREATE INDEX idx_milestones_is_baseline ON manage_milestones(is_baseline) WHERE is_baseline = TRUE;

-- 里程碑节点表索引
CREATE INDEX idx_milestone_nodes_milestone ON manage_milestone_nodes(milestone_id);
CREATE INDEX idx_milestone_nodes_requirement ON manage_milestone_nodes(requirement_id);

-- 分支表索引
CREATE INDEX idx_branches_project ON manage_branches(project_id);
CREATE INDEX idx_branches_status ON manage_branches(status);
CREATE INDEX idx_branches_base_milestone ON manage_branches(base_milestone_id);

-- 变更集表索引
CREATE INDEX idx_change_sets_branch ON manage_change_sets(branch_id);
CREATE INDEX idx_change_sets_requirement ON manage_change_sets(requirement_id) WHERE requirement_id IS NOT NULL;
CREATE INDEX idx_change_sets_type ON manage_change_sets(change_type);

-- 审计日志表索引
CREATE INDEX idx_audit_logs_project ON manage_audit_logs(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_audit_logs_target ON manage_audit_logs(target_type, target_id);
CREATE INDEX idx_audit_logs_actor ON manage_audit_logs(actor);
CREATE INDEX idx_audit_logs_created_at ON manage_audit_logs(created_at DESC);

-- ============================================================
-- 九、视图设计 (Views)
-- ============================================================

-- 视图1: 需求完整视图（包含测试用例和缺陷数量）
CREATE OR REPLACE VIEW v_requirement_details AS
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
    r.project_id,
    r.title AS requirement_title,
    r.requirement_type,
    r.status AS requirement_status,
    r.priority,
    r.assignee,
    r.created_at AS requirement_created_at,
    p.name AS project_name,
    COALESCE(ts.test_case_count, 0) AS test_case_count,
    COALESCE(ds.defect_count, 0) AS defect_count,
    COALESCE(ds.open_defect_count, 0) AS open_defect_count,
    CASE WHEN COALESCE(ts.test_case_count, 0) > 0 THEN TRUE ELSE FALSE END AS has_test_coverage
FROM manage_requirements r
JOIN manage_projects p ON p.project_id = r.project_id
LEFT JOIN test_stats ts ON ts.requirement_id = r.req_id
LEFT JOIN defect_stats ds ON ds.requirement_id = r.req_id
WHERE r.deleted = FALSE;

-- 视图2: 项目统计视图
CREATE OR REPLACE VIEW v_project_statistics AS
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
    p.status AS project_status,
    COALESCE(r.total_requirements, 0) AS total_requirements,
    COALESCE(r.top_level_count, 0) AS top_level_count,
    COALESCE(r.low_level_count, 0) AS low_level_count,
    COALESCE(r.completed_count, 0) AS completed_count,
    COALESCE(r.in_progress_count, 0) AS in_progress_count,
    COALESCE(r.draft_count, 0) AS draft_count,
    COALESCE(d.total_defects, 0) AS total_defects,
    COALESCE(d.critical_defects, 0) AS critical_defects,
    COALESCE(d.open_defects, 0) AS open_defects,
    COALESCE(tc.total_test_cases, 0) AS total_test_cases,
    COALESCE(m.total_milestones, 0) AS total_milestones,
    COALESCE(m.baseline_count, 0) AS baseline_count,
    COALESCE(b.total_branches, 0) AS total_branches,
    CASE 
        WHEN COALESCE(r.total_requirements, 0) > 0 THEN 
            ROUND((COALESCE(r.completed_count, 0)::NUMERIC / r.total_requirements) * 100, 2)
        ELSE 0 
    END AS completion_rate_percent
FROM manage_projects p
LEFT JOIN req_stats r ON r.project_id = p.project_id
LEFT JOIN def_stats d ON d.project_id = p.project_id
LEFT JOIN tc_stats tc ON tc.project_id = p.project_id
LEFT JOIN ms_stats m ON m.project_id = p.project_id
LEFT JOIN br_stats b ON b.project_id = p.project_id;

-- ============================================================
-- 十、复杂查询 (Complex Queries)
-- ============================================================

-- 复杂查询1: 需求追溯查询（连接4张表：requirements, projects, requirement_test_links, test_cases, defects）
-- 查询某个项目下所有需求的完整信息，包括关联的测试用例和缺陷
CREATE OR REPLACE FUNCTION fn_requirement_trace(p_project_id TEXT)
RETURNS TABLE (
    req_id TEXT,
    requirement_title TEXT,
    requirement_type TEXT,
    status TEXT,
    priority TEXT,
    assignee TEXT,
    project_name TEXT,
    test_cases JSONB,
    defects JSONB,
    test_case_count BIGINT,
    total_defect_count BIGINT,
    open_defect_count BIGINT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH test_case_agg AS (
        SELECT
            rtl.requirement_id,
            JSON_AGG(
                DISTINCT JSONB_BUILD_OBJECT(
                    'test_case_id', tc.test_case_id,
                    'title', tc.title,
                    'status', tc.status,
                    'link_type', rtl.link_type
                )
            ) FILTER (WHERE tc.test_case_id IS NOT NULL) AS test_cases,
            COUNT(DISTINCT tc.test_case_id) AS test_case_count
        FROM manage_requirement_test_links rtl
        LEFT JOIN manage_test_cases tc ON tc.test_case_id = rtl.test_case_id
        GROUP BY rtl.requirement_id
    ),
    defect_agg AS (
        SELECT
            df.requirement_id,
            JSON_AGG(
                DISTINCT JSONB_BUILD_OBJECT(
                    'defect_id', df.defect_id,
                    'title', df.title,
                    'severity', df.severity,
                    'priority', df.priority,
                    'status', df.status,
                    'current_assignee', df.current_assignee
                )
            ) FILTER (WHERE df.defect_id IS NOT NULL) AS defects,
            COUNT(DISTINCT df.defect_id) AS total_defect_count,
            COUNT(DISTINCT CASE WHEN df.status IN ('open', 'in_progress') THEN df.defect_id END) AS open_defect_count
        FROM manage_defects df
        GROUP BY df.requirement_id
    )
    SELECT
        req.req_id,
        req.title AS requirement_title,
        req.requirement_type,
        req.status,
        req.priority,
        req.assignee,
        proj.name AS project_name,
        COALESCE(tca.test_cases, '[]'::JSONB) AS test_cases,
        COALESCE(da.defects, '[]'::JSONB) AS defects,
        COALESCE(tca.test_case_count, 0) AS test_case_count,
        COALESCE(da.total_defect_count, 0) AS total_defect_count,
        COALESCE(da.open_defect_count, 0) AS open_defect_count
    FROM manage_requirements req
    JOIN manage_projects proj ON proj.project_id = req.project_id
    LEFT JOIN test_case_agg tca ON tca.requirement_id = req.req_id
    LEFT JOIN defect_agg da ON da.requirement_id = req.req_id
    WHERE req.deleted = FALSE AND req.project_id = p_project_id
    ORDER BY req.created_at DESC;
END;
$$;

-- 复杂查询2: 项目进度统计（使用CTE进行多层嵌套聚合）
CREATE OR REPLACE FUNCTION fn_project_progress(p_project_id TEXT)
RETURNS TABLE (
    project_id TEXT,
    project_name TEXT,
    project_status TEXT,
    total_requirements BIGINT,
    completed_requirements BIGINT,
    in_progress_requirements BIGINT,
    draft_requirements BIGINT,
    completion_rate_percent NUMERIC,
    total_defects BIGINT,
    critical_defects BIGINT,
    open_defects BIGINT,
    total_requirements_for_coverage BIGINT,
    covered_requirements BIGINT,
    test_coverage_rate_percent NUMERIC,
    total_milestones BIGINT,
    baseline_count BIGINT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH requirement_stats AS (
        SELECT
            project_id,
            COUNT(*) AS total_reqs,
            COUNT(*) FILTER (WHERE status = 'completed') AS completed_reqs,
            COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress_reqs,
            COUNT(*) FILTER (WHERE status = 'draft') AS draft_reqs
        FROM manage_requirements
        WHERE deleted = FALSE
        GROUP BY project_id
    ),
    defect_stats AS (
        SELECT
            project_id,
            COUNT(*) AS total_defects,
            COUNT(*) FILTER (WHERE severity = 'critical') AS critical_defects,
            COUNT(*) FILTER (WHERE status IN ('open', 'in_progress')) AS open_defects
        FROM manage_defects
        GROUP BY project_id
    ),
    test_coverage_stats AS (
        SELECT
            r.project_id,
            COUNT(DISTINCT r.req_id) AS total_requirements,
            COUNT(DISTINCT r.req_id) FILTER (
                WHERE EXISTS (
                    SELECT 1 FROM manage_requirement_test_links rtl
                    WHERE rtl.requirement_id = r.req_id
                )
            ) AS covered_requirements
        FROM manage_requirements r
        WHERE r.deleted = FALSE
        GROUP BY r.project_id
    ),
    milestone_stats AS (
        SELECT
            project_id,
            COUNT(*) AS total_milestones,
            COUNT(*) FILTER (WHERE is_baseline = TRUE) AS baseline_count
        FROM manage_milestones
        GROUP BY project_id
    )
    SELECT
        p.project_id,
        p.name AS project_name,
        p.status AS project_status,
        COALESCE(rs.total_reqs, 0)::BIGINT AS total_requirements,
        COALESCE(rs.completed_reqs, 0)::BIGINT AS completed_requirements,
        COALESCE(rs.in_progress_reqs, 0)::BIGINT AS in_progress_requirements,
        COALESCE(rs.draft_reqs, 0)::BIGINT AS draft_requirements,
        CASE
            WHEN COALESCE(rs.total_reqs, 0) > 0
            THEN ROUND(COALESCE(rs.completed_reqs, 0)::NUMERIC / rs.total_reqs * 100, 2)
            ELSE 0
        END AS completion_rate_percent,
        COALESCE(ds.total_defects, 0)::BIGINT AS total_defects,
        COALESCE(ds.critical_defects, 0)::BIGINT AS critical_defects,
        COALESCE(ds.open_defects, 0)::BIGINT AS open_defects,
        COALESCE(tcs.total_requirements, 0)::BIGINT AS total_requirements_for_coverage,
        COALESCE(tcs.covered_requirements, 0)::BIGINT AS covered_requirements,
        CASE
            WHEN COALESCE(tcs.total_requirements, 0) > 0
            THEN ROUND(COALESCE(tcs.covered_requirements, 0)::NUMERIC / tcs.total_requirements * 100, 2)
            ELSE 0
        END AS test_coverage_rate_percent,
        COALESCE(ms.total_milestones, 0)::BIGINT AS total_milestones,
        COALESCE(ms.baseline_count, 0)::BIGINT AS baseline_count
    FROM manage_projects p
    LEFT JOIN requirement_stats rs ON rs.project_id = p.project_id
    LEFT JOIN defect_stats ds ON ds.project_id = p.project_id
    LEFT JOIN test_coverage_stats tcs ON tcs.project_id = p.project_id
    LEFT JOIN milestone_stats ms ON ms.project_id = p.project_id
    WHERE p.project_id = p_project_id
    ORDER BY p.created_at DESC;
END;
$$;

-- ============================================================
-- 十一、ER图关系描述 (ER Model Summary)
-- ============================================================
-- 实体关系:

-- manage_products (产品)
--   1:N manage_product_members (产品成员)
--   1:N manage_projects (项目)

-- manage_projects (项目)
--   1:N manage_requirements (需求树)
--   1:N manage_defects (缺陷)
--   1:N manage_test_cases (测试用例)
--   1:N manage_milestones (里程碑)
--   1:N manage_branches (分支)
--   1:N manage_audit_logs (审计日志)

-- manage_requirements (需求)
--   1:N manage_requirements (自引用，父需求)
--   1:N manage_defects (缺陷)
--   N:M manage_test_cases (通过 manage_requirement_test_links)

-- manage_milestones (里程碑)
--   1:N manage_milestone_nodes (里程碑节点)
--   1:N manage_branches (分支，以里程碑为基础)

-- manage_branches (分支)
--   1:N manage_change_sets (变更集)

-- 关系类型:
-- - 1:N 关系: products→projects, projects→requirements, etc.
-- - 自引用 1:N: requirements.parent_id → requirements.req_id
-- - M:N 关系: requirements ↔ test_cases (via requirement_test_links)
