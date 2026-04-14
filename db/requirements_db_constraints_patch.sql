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
