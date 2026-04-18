-- ============================================================
-- 需求管理数据库约束补丁
-- 用于给已初始化的数据库补齐跨项目一致性、层级规则与强外键约束
-- ============================================================

ALTER TABLE manage_requirements
    DROP CONSTRAINT IF EXISTS chk_requirement_parent_not_self;

ALTER TABLE manage_requirements
    ADD CONSTRAINT chk_requirement_parent_not_self
    CHECK (parent_id IS NULL OR parent_id <> req_id);

ALTER TABLE manage_requirements
    DROP CONSTRAINT IF EXISTS uk_requirement_project_req;

ALTER TABLE manage_requirements
    ADD CONSTRAINT uk_requirement_project_req UNIQUE (project_id, req_id);

ALTER TABLE manage_test_cases
    DROP CONSTRAINT IF EXISTS uk_test_case_project_case;

ALTER TABLE manage_test_cases
    ADD CONSTRAINT uk_test_case_project_case UNIQUE (project_id, test_case_id);

ALTER TABLE manage_milestones
    DROP CONSTRAINT IF EXISTS uk_milestone_project_milestone;

ALTER TABLE manage_milestones
    ADD CONSTRAINT uk_milestone_project_milestone UNIQUE (project_id, milestone_id);

ALTER TABLE manage_defects
    DROP CONSTRAINT IF EXISTS manage_defects_requirement_id_fkey;

ALTER TABLE manage_defects
    DROP CONSTRAINT IF EXISTS fk_defects_requirement_project;

ALTER TABLE manage_defects
    ADD CONSTRAINT fk_defects_requirement_project
    FOREIGN KEY (project_id, requirement_id)
    REFERENCES manage_requirements(project_id, req_id)
    ON DELETE CASCADE;

ALTER TABLE manage_milestone_nodes
    DROP CONSTRAINT IF EXISTS manage_milestone_nodes_requirement_id_fkey;

ALTER TABLE manage_milestone_nodes
    ADD CONSTRAINT manage_milestone_nodes_requirement_id_fkey
    FOREIGN KEY (requirement_id)
    REFERENCES manage_requirements(req_id)
    ON DELETE CASCADE;

ALTER TABLE manage_change_sets
    DROP CONSTRAINT IF EXISTS manage_change_sets_requirement_id_fkey;

ALTER TABLE manage_change_sets
    ADD CONSTRAINT manage_change_sets_requirement_id_fkey
    FOREIGN KEY (requirement_id)
    REFERENCES manage_requirements(req_id)
    ON DELETE SET NULL;

ALTER TABLE manage_audit_logs
    DROP CONSTRAINT IF EXISTS manage_audit_logs_product_id_fkey;

ALTER TABLE manage_audit_logs
    ADD CONSTRAINT manage_audit_logs_product_id_fkey
    FOREIGN KEY (product_id)
    REFERENCES manage_products(product_id)
    ON DELETE SET NULL;

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

DROP TRIGGER IF EXISTS trg_validate_requirement_hierarchy ON manage_requirements;
CREATE TRIGGER trg_validate_requirement_hierarchy
BEFORE INSERT OR UPDATE OF project_id, requirement_type, parent_id
ON manage_requirements
FOR EACH ROW
EXECUTE FUNCTION fn_validate_requirement_hierarchy();

DROP TRIGGER IF EXISTS trg_validate_requirement_link_scope ON manage_requirement_links;
CREATE TRIGGER trg_validate_requirement_link_scope
BEFORE INSERT OR UPDATE OF source_req_id, target_req_id
ON manage_requirement_links
FOR EACH ROW
EXECUTE FUNCTION fn_validate_requirement_link_scope();

DROP TRIGGER IF EXISTS trg_validate_requirement_test_link_scope ON manage_requirement_test_links;
CREATE TRIGGER trg_validate_requirement_test_link_scope
BEFORE INSERT OR UPDATE OF requirement_id, test_case_id
ON manage_requirement_test_links
FOR EACH ROW
EXECUTE FUNCTION fn_validate_requirement_test_link_scope();

DROP TRIGGER IF EXISTS trg_validate_branch_scope ON manage_branches;
CREATE TRIGGER trg_validate_branch_scope
BEFORE INSERT OR UPDATE OF project_id, base_milestone_id
ON manage_branches
FOR EACH ROW
EXECUTE FUNCTION fn_validate_branch_scope();

DROP TRIGGER IF EXISTS trg_validate_milestone_node_scope ON manage_milestone_nodes;
CREATE TRIGGER trg_validate_milestone_node_scope
BEFORE INSERT OR UPDATE OF milestone_id, requirement_id
ON manage_milestone_nodes
FOR EACH ROW
EXECUTE FUNCTION fn_validate_milestone_node_scope();

DROP TRIGGER IF EXISTS trg_validate_change_set_scope ON manage_change_sets;
CREATE TRIGGER trg_validate_change_set_scope
BEFORE INSERT OR UPDATE OF branch_id, requirement_id
ON manage_change_sets
FOR EACH ROW
EXECUTE FUNCTION fn_validate_change_set_scope();

DROP TRIGGER IF EXISTS trg_validate_comment_scope ON manage_comments;
CREATE TRIGGER trg_validate_comment_scope
BEFORE INSERT OR UPDATE OF project_id, target_type, target_id, reply_to_id
ON manage_comments
FOR EACH ROW
EXECUTE FUNCTION fn_validate_comment_scope();

DROP TRIGGER IF EXISTS trg_validate_audit_log_scope ON manage_audit_logs;
CREATE TRIGGER trg_validate_audit_log_scope
BEFORE INSERT OR UPDATE OF project_id, product_id
ON manage_audit_logs
FOR EACH ROW
EXECUTE FUNCTION fn_validate_audit_log_scope();

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
