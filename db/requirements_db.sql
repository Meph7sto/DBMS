-- ============================================================
-- 需求管理数据库 (Requirements Management Database)
-- 基于管理模块设计
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

-- 项目成员表
CREATE TABLE manage_project_members (
    id         SERIAL PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES manage_projects(project_id) ON DELETE CASCADE,
    user_id    TEXT NOT NULL,
    role       TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_project_member UNIQUE (project_id, user_id)
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
    deleted          BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT chk_requirement_parent_not_self CHECK (parent_id IS NULL OR parent_id <> req_id),
    CONSTRAINT uk_requirement_project_req UNIQUE (project_id, req_id)
);

-- 需求关联表（用于平行依赖：如 blocks, depends_on, relates_to, duplicates）
CREATE TABLE manage_requirement_links (
    link_id        SERIAL PRIMARY KEY,
    source_req_id  TEXT NOT NULL REFERENCES manage_requirements(req_id) ON DELETE CASCADE,
    target_req_id  TEXT NOT NULL REFERENCES manage_requirements(req_id) ON DELETE CASCADE,
    link_type      TEXT NOT NULL CHECK (link_type IN ('blocks', 'depends_on', 'relates_to', 'duplicates')),
    created_by     TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_req_link UNIQUE (source_req_id, target_req_id, link_type),
    CONSTRAINT chk_no_self_link CHECK (source_req_id != target_req_id)
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
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_test_case_project_case UNIQUE (project_id, test_case_id)
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
    requirement_id   TEXT NOT NULL,
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
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_defects_requirement_project
        FOREIGN KEY (project_id, requirement_id)
        REFERENCES manage_requirements(project_id, req_id)
        ON DELETE CASCADE
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
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_milestone_project_milestone UNIQUE (project_id, milestone_id)
);

-- 里程碑节点表（需求快照）
CREATE TABLE manage_milestone_nodes (
    snapshot_id     TEXT PRIMARY KEY,
    milestone_id    TEXT NOT NULL REFERENCES manage_milestones(milestone_id) ON DELETE CASCADE,
    requirement_id  TEXT NOT NULL REFERENCES manage_requirements(req_id) ON DELETE CASCADE,
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
    requirement_id TEXT REFERENCES manage_requirements(req_id) ON DELETE SET NULL,
    before_data    JSONB,
    after_data     JSONB,
    created_by     TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 七、协同与审计日志 (Collaboration & Audit Logs)
-- ============================================================

-- 评论表（支持多态，可关联需求、缺陷、用例等）
CREATE TABLE manage_comments (
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

-- 审计日志表
CREATE TABLE manage_audit_logs (
    log_id      TEXT PRIMARY KEY,
    project_id  TEXT REFERENCES manage_projects(project_id) ON DELETE SET NULL,
    product_id  TEXT REFERENCES manage_products(product_id) ON DELETE SET NULL,
    actor       TEXT NOT NULL,
    action      TEXT NOT NULL,
    target_type TEXT,
    target_id   TEXT,
    detail      JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 八、业务约束触发器 (Business Integrity Triggers)
-- ============================================================

CREATE OR REPLACE FUNCTION fn_validate_requirement_hierarchy()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_parent_project_id TEXT;
    v_parent_type TEXT;
BEGIN
    IF NEW.parent_id IS NULL THEN
        IF NEW.requirement_type <> 'top_level' THEN
            RAISE EXCEPTION '非顶层需求必须指定父需求';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.parent_id = NEW.req_id THEN
        RAISE EXCEPTION '需求不能将自己设置为父需求';
    END IF;

    SELECT project_id, requirement_type
      INTO v_parent_project_id, v_parent_type
      FROM manage_requirements
     WHERE req_id = NEW.parent_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION '父需求 % 不存在', NEW.parent_id;
    END IF;

    IF v_parent_project_id <> NEW.project_id THEN
        RAISE EXCEPTION '父需求 % 与当前需求不属于同一项目', NEW.parent_id;
    END IF;

    IF NEW.requirement_type = 'top_level' THEN
        RAISE EXCEPTION '顶层需求不能设置父需求';
    ELSIF NEW.requirement_type = 'low_level' AND v_parent_type <> 'top_level' THEN
        RAISE EXCEPTION 'low_level 的父需求必须是 top_level';
    ELSIF NEW.requirement_type = 'task' AND v_parent_type NOT IN ('top_level', 'low_level') THEN
        RAISE EXCEPTION 'task 的父需求必须是 top_level 或 low_level';
    END IF;

    IF TG_OP = 'UPDATE' AND EXISTS (
        WITH RECURSIVE ancestors AS (
            SELECT req_id, parent_id
              FROM manage_requirements
             WHERE req_id = NEW.parent_id
            UNION ALL
            SELECT r.req_id, r.parent_id
              FROM manage_requirements r
              JOIN ancestors a ON r.req_id = a.parent_id
             WHERE a.parent_id IS NOT NULL
        )
        SELECT 1
          FROM ancestors
         WHERE req_id = NEW.req_id
         LIMIT 1
    ) THEN
        RAISE EXCEPTION '检测到循环父子关系';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validate_requirement_link_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_source_project_id TEXT;
    v_target_project_id TEXT;
BEGIN
    SELECT project_id
      INTO v_source_project_id
      FROM manage_requirements
     WHERE req_id = NEW.source_req_id
       AND deleted = FALSE;

    IF NOT FOUND THEN
        RAISE EXCEPTION '源需求 % 不存在或已删除', NEW.source_req_id;
    END IF;

    SELECT project_id
      INTO v_target_project_id
      FROM manage_requirements
     WHERE req_id = NEW.target_req_id
       AND deleted = FALSE;

    IF NOT FOUND THEN
        RAISE EXCEPTION '目标需求 % 不存在或已删除', NEW.target_req_id;
    END IF;

    IF v_source_project_id <> v_target_project_id THEN
        RAISE EXCEPTION '需求关联两端必须属于同一项目';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validate_requirement_test_link_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_requirement_project_id TEXT;
    v_test_case_project_id TEXT;
BEGIN
    SELECT project_id
      INTO v_requirement_project_id
      FROM manage_requirements
     WHERE req_id = NEW.requirement_id
       AND deleted = FALSE;

    IF NOT FOUND THEN
        RAISE EXCEPTION '需求 % 不存在或已删除', NEW.requirement_id;
    END IF;

    SELECT project_id
      INTO v_test_case_project_id
      FROM manage_test_cases
     WHERE test_case_id = NEW.test_case_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION '测试用例 % 不存在', NEW.test_case_id;
    END IF;

    IF v_requirement_project_id <> v_test_case_project_id THEN
        RAISE EXCEPTION '需求与测试用例必须属于同一项目';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validate_branch_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_milestone_project_id TEXT;
BEGIN
    SELECT project_id
      INTO v_milestone_project_id
      FROM manage_milestones
     WHERE milestone_id = NEW.base_milestone_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION '基线里程碑 % 不存在', NEW.base_milestone_id;
    END IF;

    IF v_milestone_project_id <> NEW.project_id THEN
        RAISE EXCEPTION '分支与基线里程碑必须属于同一项目';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validate_milestone_node_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_milestone_project_id TEXT;
    v_requirement_project_id TEXT;
BEGIN
    SELECT project_id
      INTO v_milestone_project_id
      FROM manage_milestones
     WHERE milestone_id = NEW.milestone_id;

    IF v_milestone_project_id IS NULL THEN
        RAISE EXCEPTION '里程碑 % 不存在', NEW.milestone_id;
    END IF;

    SELECT project_id
      INTO v_requirement_project_id
      FROM manage_requirements
     WHERE req_id = NEW.requirement_id
       AND deleted = FALSE;

    IF v_requirement_project_id IS NULL THEN
        RAISE EXCEPTION '里程碑节点关联的需求 % 不存在或已删除', NEW.requirement_id;
    END IF;

    IF v_milestone_project_id <> v_requirement_project_id THEN
        RAISE EXCEPTION '里程碑节点与需求必须属于同一项目';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validate_change_set_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_branch_project_id TEXT;
    v_requirement_project_id TEXT;
BEGIN
    IF NEW.requirement_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT project_id
      INTO v_branch_project_id
      FROM manage_branches
     WHERE branch_id = NEW.branch_id;

    IF v_branch_project_id IS NULL THEN
        RAISE EXCEPTION '分支 % 不存在', NEW.branch_id;
    END IF;

    SELECT project_id
      INTO v_requirement_project_id
      FROM manage_requirements
     WHERE req_id = NEW.requirement_id
       AND deleted = FALSE;

    IF v_requirement_project_id IS NULL THEN
        RAISE EXCEPTION '变更集关联的需求 % 不存在或已删除', NEW.requirement_id;
    END IF;

    IF v_branch_project_id <> v_requirement_project_id THEN
        RAISE EXCEPTION '变更集与需求必须属于同一项目';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION fn_validate_comment_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_target_project_id TEXT;
    v_reply_project_id TEXT;
BEGIN
    CASE NEW.target_type
        WHEN 'requirement' THEN
            SELECT project_id
              INTO v_target_project_id
              FROM manage_requirements
             WHERE req_id = NEW.target_id
               AND deleted = FALSE;
        WHEN 'defect' THEN
            SELECT project_id
              INTO v_target_project_id
              FROM manage_defects
             WHERE defect_id = NEW.target_id;
        WHEN 'test_case' THEN
            SELECT project_id
              INTO v_target_project_id
              FROM manage_test_cases
             WHERE test_case_id = NEW.target_id;
        WHEN 'milestone' THEN
            SELECT project_id
              INTO v_target_project_id
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

CREATE OR REPLACE FUNCTION fn_validate_audit_log_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_project_product_id TEXT;
BEGIN
    IF NEW.project_id IS NULL OR NEW.product_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT product_id
      INTO v_project_product_id
      FROM manage_projects
     WHERE project_id = NEW.project_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION '审计日志关联的项目 % 不存在', NEW.project_id;
    END IF;

    IF v_project_product_id IS DISTINCT FROM NEW.product_id THEN
        RAISE EXCEPTION '审计日志中的产品与项目归属不一致';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_requirement_hierarchy
BEFORE INSERT OR UPDATE OF project_id, requirement_type, parent_id
ON manage_requirements
FOR EACH ROW
EXECUTE FUNCTION fn_validate_requirement_hierarchy();

CREATE TRIGGER trg_validate_requirement_link_scope
BEFORE INSERT OR UPDATE OF source_req_id, target_req_id
ON manage_requirement_links
FOR EACH ROW
EXECUTE FUNCTION fn_validate_requirement_link_scope();

CREATE TRIGGER trg_validate_requirement_test_link_scope
BEFORE INSERT OR UPDATE OF requirement_id, test_case_id
ON manage_requirement_test_links
FOR EACH ROW
EXECUTE FUNCTION fn_validate_requirement_test_link_scope();

CREATE TRIGGER trg_validate_branch_scope
BEFORE INSERT OR UPDATE OF project_id, base_milestone_id
ON manage_branches
FOR EACH ROW
EXECUTE FUNCTION fn_validate_branch_scope();

CREATE TRIGGER trg_validate_milestone_node_scope
BEFORE INSERT OR UPDATE OF milestone_id, requirement_id
ON manage_milestone_nodes
FOR EACH ROW
EXECUTE FUNCTION fn_validate_milestone_node_scope();

CREATE TRIGGER trg_validate_change_set_scope
BEFORE INSERT OR UPDATE OF branch_id, requirement_id
ON manage_change_sets
FOR EACH ROW
EXECUTE FUNCTION fn_validate_change_set_scope();

CREATE TRIGGER trg_validate_comment_scope
BEFORE INSERT OR UPDATE OF project_id, target_type, target_id, reply_to_id
ON manage_comments
FOR EACH ROW
EXECUTE FUNCTION fn_validate_comment_scope();

CREATE TRIGGER trg_validate_audit_log_scope
BEFORE INSERT OR UPDATE OF project_id, product_id
ON manage_audit_logs
FOR EACH ROW
EXECUTE FUNCTION fn_validate_audit_log_scope();

-- ============================================================
-- 九、索引设计 (Indexes)
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

-- 项目成员表索引
CREATE INDEX idx_project_members_project ON manage_project_members(project_id);
CREATE INDEX idx_project_members_user ON manage_project_members(user_id);

-- 需求关联表索引
CREATE INDEX idx_req_links_source ON manage_requirement_links(source_req_id);
CREATE INDEX idx_req_links_target ON manage_requirement_links(target_req_id);

-- 评论表索引
CREATE INDEX idx_comments_project ON manage_comments(project_id);
CREATE INDEX idx_comments_target ON manage_comments(target_type, target_id);
CREATE INDEX idx_comments_created_at ON manage_comments(created_at);

-- 审计日志表索引
CREATE INDEX idx_audit_logs_project ON manage_audit_logs(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_audit_logs_target ON manage_audit_logs(target_type, target_id);
CREATE INDEX idx_audit_logs_actor ON manage_audit_logs(actor);
CREATE INDEX idx_audit_logs_created_at ON manage_audit_logs(created_at DESC);

-- ============================================================
-- 十、视图设计 (Views)
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
-- 十一、复杂查询 (Complex Queries)
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
            JSONB_AGG(
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
            JSONB_AGG(
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
            mr.project_id,
            COUNT(*) AS total_reqs,
            COUNT(*) FILTER (WHERE mr.status = 'completed') AS completed_reqs,
            COUNT(*) FILTER (WHERE mr.status = 'in_progress') AS in_progress_reqs,
            COUNT(*) FILTER (WHERE mr.status = 'draft') AS draft_reqs
        FROM manage_requirements mr
        WHERE mr.deleted = FALSE
        GROUP BY mr.project_id
    ),
    defect_stats AS (
        SELECT
            md.project_id,
            COUNT(*) AS total_defects,
            COUNT(*) FILTER (WHERE md.severity = 'critical') AS critical_defects,
            COUNT(*) FILTER (WHERE md.status IN ('open', 'in_progress')) AS open_defects
        FROM manage_defects md
        GROUP BY md.project_id
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
            mm.project_id,
            COUNT(*) AS total_milestones,
            COUNT(*) FILTER (WHERE mm.is_baseline = TRUE) AS baseline_count
        FROM manage_milestones mm
        GROUP BY mm.project_id
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

-- 复杂查询3: 里程碑交付风险分析（连接 milestones, milestone_nodes, requirements,
-- requirement_test_links, test_cases, requirement_links, defects, branches, change_sets）
-- 查询某个项目下各里程碑当前的交付风险，综合评估范围需求、测试覆盖、缺陷、依赖和分支变更活跃度
CREATE OR REPLACE FUNCTION fn_milestone_delivery_risk(p_project_id TEXT)
RETURNS TABLE (
    milestone_id TEXT,
    milestone_name TEXT,
    milestone_type TEXT,
    is_baseline BOOLEAN,
    sprint TEXT,
    version TEXT,
    project_name TEXT,
    scoped_requirement_count BIGINT,
    incomplete_requirement_count BIGINT,
    uncovered_requirement_count BIGINT,
    blocked_requirement_count BIGINT,
    unresolved_defect_count BIGINT,
    critical_defect_count BIGINT,
    active_branch_count BIGINT,
    pending_change_count BIGINT,
    latest_branch_activity TIMESTAMPTZ,
    risk_score NUMERIC,
    risk_level TEXT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH milestone_requirement_stats AS (
        SELECT
            m.milestone_id,
            COUNT(DISTINCT mn.requirement_id) AS scoped_requirement_count,
            COUNT(DISTINCT mn.requirement_id) FILTER (
                WHERE r.req_id IS NOT NULL
                  AND r.deleted = FALSE
                  AND r.status <> 'completed'
            ) AS incomplete_requirement_count,
            COUNT(DISTINCT mn.requirement_id) FILTER (
                WHERE r.req_id IS NOT NULL
                  AND r.deleted = FALSE
                  AND NOT EXISTS (
                      SELECT 1
                        FROM manage_requirement_test_links rtl
                        JOIN manage_test_cases tc
                          ON tc.test_case_id = rtl.test_case_id
                         AND tc.status = 'active'
                       WHERE rtl.requirement_id = mn.requirement_id
                  )
            ) AS uncovered_requirement_count,
            COUNT(DISTINCT mn.requirement_id) FILTER (
                WHERE r.req_id IS NOT NULL
                  AND r.deleted = FALSE
                  AND EXISTS (
                      SELECT 1
                        FROM manage_requirement_links rl
                        JOIN manage_requirements dep
                          ON dep.req_id = rl.target_req_id
                       WHERE rl.source_req_id = mn.requirement_id
                         AND rl.link_type = 'depends_on'
                         AND dep.deleted = FALSE
                         AND dep.status <> 'completed'
                  )
            ) AS blocked_requirement_count
        FROM manage_milestones m
        LEFT JOIN manage_milestone_nodes mn ON mn.milestone_id = m.milestone_id
        LEFT JOIN manage_requirements r ON r.req_id = mn.requirement_id
        WHERE m.project_id = p_project_id
        GROUP BY m.milestone_id
    ),
    milestone_defect_stats AS (
        SELECT
            m.milestone_id,
            COUNT(DISTINCT d.defect_id) FILTER (
                WHERE d.status NOT IN ('closed', 'rejected')
            ) AS unresolved_defect_count,
            COUNT(DISTINCT d.defect_id) FILTER (
                WHERE d.severity = 'critical'
                  AND d.status NOT IN ('closed', 'rejected')
            ) AS critical_defect_count
        FROM manage_milestones m
        LEFT JOIN manage_milestone_nodes mn ON mn.milestone_id = m.milestone_id
        LEFT JOIN manage_defects d
               ON d.project_id = m.project_id
              AND d.requirement_id = mn.requirement_id
        WHERE m.project_id = p_project_id
        GROUP BY m.milestone_id
    ),
    milestone_branch_stats AS (
        SELECT
            m.milestone_id,
            COUNT(DISTINCT b.branch_id) FILTER (
                WHERE b.status IN ('active', 'under_review')
            ) AS active_branch_count,
            COUNT(DISTINCT cs.change_id) FILTER (
                WHERE b.status IN ('active', 'under_review')
            ) AS pending_change_count,
            MAX(COALESCE(cs.created_at, b.updated_at, b.created_at)) AS latest_branch_activity
        FROM manage_milestones m
        LEFT JOIN manage_branches b ON b.base_milestone_id = m.milestone_id
        LEFT JOIN manage_change_sets cs ON cs.branch_id = b.branch_id
        WHERE m.project_id = p_project_id
        GROUP BY m.milestone_id
    ),
    risk_metrics AS (
        SELECT
            m.milestone_id,
            COALESCE(mrs.scoped_requirement_count, 0)::BIGINT AS scoped_requirement_count,
            COALESCE(mrs.incomplete_requirement_count, 0)::BIGINT AS incomplete_requirement_count,
            COALESCE(mrs.uncovered_requirement_count, 0)::BIGINT AS uncovered_requirement_count,
            COALESCE(mrs.blocked_requirement_count, 0)::BIGINT AS blocked_requirement_count,
            COALESCE(mds.unresolved_defect_count, 0)::BIGINT AS unresolved_defect_count,
            COALESCE(mds.critical_defect_count, 0)::BIGINT AS critical_defect_count,
            COALESCE(mbs.active_branch_count, 0)::BIGINT AS active_branch_count,
            COALESCE(mbs.pending_change_count, 0)::BIGINT AS pending_change_count,
            mbs.latest_branch_activity,
            ROUND(
                (
                    COALESCE(mrs.incomplete_requirement_count, 0) * 2.0 +
                    COALESCE(mrs.uncovered_requirement_count, 0) * 1.5 +
                    COALESCE(mrs.blocked_requirement_count, 0) * 2.5 +
                    COALESCE(mds.unresolved_defect_count, 0) * 2.0 +
                    COALESCE(mds.critical_defect_count, 0) * 3.0 +
                    COALESCE(mbs.pending_change_count, 0) * 0.5
                )::NUMERIC,
                2
            ) AS risk_score
        FROM manage_milestones m
        LEFT JOIN milestone_requirement_stats mrs ON mrs.milestone_id = m.milestone_id
        LEFT JOIN milestone_defect_stats mds ON mds.milestone_id = m.milestone_id
        LEFT JOIN milestone_branch_stats mbs ON mbs.milestone_id = m.milestone_id
        WHERE m.project_id = p_project_id
    )
    SELECT
        m.milestone_id,
        m.name AS milestone_name,
        m.milestone_type,
        m.is_baseline,
        m.sprint,
        m.version,
        p.name AS project_name,
        rm.scoped_requirement_count,
        rm.incomplete_requirement_count,
        rm.uncovered_requirement_count,
        rm.blocked_requirement_count,
        rm.unresolved_defect_count,
        rm.critical_defect_count,
        rm.active_branch_count,
        rm.pending_change_count,
        rm.latest_branch_activity,
        rm.risk_score,
        CASE
            WHEN rm.risk_score >= 12 THEN 'high'
            WHEN rm.risk_score >= 6 THEN 'medium'
            ELSE 'low'
        END AS risk_level
    FROM manage_milestones m
    JOIN manage_projects p ON p.project_id = m.project_id
    JOIN risk_metrics rm ON rm.milestone_id = m.milestone_id
    WHERE m.project_id = p_project_id
    ORDER BY
        CASE WHEN m.is_baseline THEN 0 ELSE 1 END,
        rm.risk_score DESC,
        m.created_at DESC;
END;
$$;

-- ============================================================
-- 十二、ER图关系描述 (ER Model Summary)
-- ============================================================
-- 实体关系:

-- manage_products (产品)
--   1:N manage_product_members (产品成员)
--   1:N manage_projects (项目)

-- manage_projects (项目)
--   1:N manage_project_members (项目成员)
--   1:N manage_requirements (需求树)
--   1:N manage_defects (缺陷)
--   1:N manage_test_cases (测试用例)
--   1:N manage_milestones (里程碑)
--   1:N manage_branches (分支)
--   1:N manage_comments (协同评论)
--   1:N manage_audit_logs (审计日志)

-- manage_requirements (需求)
--   1:N manage_requirements (自引用，父需求)
--   N:M manage_requirements (平行依赖，通过 manage_requirement_links)
--   1:N manage_defects (缺陷)
--   N:M manage_test_cases (通过 manage_requirement_test_links)

-- manage_milestones (里程碑)
--   1:N manage_milestone_nodes (里程碑节点)
--   1:N manage_branches (分支，以里程碑为基础)

-- manage_branches (分支)
--   1:N manage_change_sets (变更集)

-- 跨表多态关系 (Polymorphic):
-- - manage_comments.target_id → requirements / defects / test_cases / milestones
-- - manage_audit_logs.target_id → 任意对象实体

-- 关系类型:
-- - 1:N 关系: products→projects, projects→requirements, etc.
-- - 自引用 1:N: requirements.parent_id → requirements.req_id
-- - M:N 关系: requirements ↔ test_cases (via requirement_test_links)
-- - M:N 关系: requirements ↔ requirements (via requirement_links)
