# 数据库表结构文档

## 一、产品层 (Product Layer)

### manage_products - 产品表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| product_id | TEXT | PK | 产品ID |
| name | TEXT | NOT NULL, UNIQUE | 产品名称 |
| description | TEXT | | 产品描述 |
| status | TEXT | NOT NULL, DEFAULT 'active' | 状态: active, archived |
| roadmap | TEXT | | 路线图 |
| version | TEXT | | 版本 |
| tags | JSONB | DEFAULT '[]' | 标签数组 |
| created_by | TEXT | | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

### manage_product_members - 产品成员表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PK | 主键 |
| product_id | TEXT | FK → manage_products, ON DELETE CASCADE | 产品ID |
| user_id | TEXT | NOT NULL | 用户ID |
| role | TEXT | NOT NULL | 角色: owner, admin, member, viewer |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

**唯一约束**: (product_id, user_id)

---

## 二、项目层 (Project Layer)

### manage_projects - 项目表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| project_id | TEXT | PK | 项目ID |
| name | TEXT | NOT NULL, UNIQUE | 项目名称 |
| description | TEXT | | 项目描述 |
| status | TEXT | NOT NULL, DEFAULT 'active' | 状态: active, archived |
| product_id | TEXT | FK → manage_products, ON DELETE SET NULL | 所属产品ID |
| current_session_id | TEXT | | 当前里程碑ID |
| created_by | TEXT | | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

### manage_project_members - 项目成员表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PK | 主键 |
| project_id | TEXT | FK → manage_projects, ON DELETE CASCADE | 项目ID |
| user_id | TEXT | NOT NULL | 用户ID |
| role | TEXT | NOT NULL | 角色: owner, admin, member, viewer |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

**唯一约束**: (project_id, user_id)

---

## 三、需求层 (Requirements Layer)

### manage_requirements - 需求表（树形结构）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| req_id | TEXT | PK | 需求ID |
| project_id | TEXT | FK → manage_projects, ON DELETE CASCADE | 项目ID |
| requirement_type | TEXT | NOT NULL | 类型: top_level, low_level, task |
| status | TEXT | NOT NULL, DEFAULT 'draft' | 状态: draft, under_review, confirmed, in_progress, completed, archived |
| title | TEXT | NOT NULL | 需求标题 |
| description | TEXT | | 需求描述 |
| priority | TEXT | | 优先级: low, medium, high |
| assignee | TEXT | | 负责人 |
| tags | JSONB | DEFAULT '[]' | 标签数组 |
| due_date | TEXT | | 截止日期 |
| parent_id | TEXT | FK → manage_requirements, ON DELETE SET NULL | 父需求ID（自引用） |
| order_index | INTEGER | NOT NULL, DEFAULT 0 | 排序索引 |
| source_req_id | TEXT | | 来源需求ID |
| source_level | TEXT | | 来源层级 |
| custom_fields | JSONB | DEFAULT '{}' | 自定义字段 |
| is_planned | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否已计划 |
| created_by | TEXT | | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_by | TEXT | | 更新人 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |
| deleted | BOOLEAN | NOT NULL, DEFAULT FALSE | 软删除标记 |

**约束**:
- 父需求不能是自己
- 唯一约束: (project_id, req_id)

### manage_requirement_links - 需求关联表（平行依赖）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| link_id | SERIAL | PK | 关联ID |
| source_req_id | TEXT | FK → manage_requirements, ON DELETE CASCADE | 源需求ID |
| target_req_id | TEXT | FK → manage_requirements, ON DELETE CASCADE | 目标需求ID |
| link_type | TEXT | NOT NULL | 关联类型: blocks, depends_on, relates_to, duplicates |
| created_by | TEXT | | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

**约束**:
- 不能自引用 (source_req_id != target_req_id)
- 唯一约束: (source_req_id, target_req_id, link_type)

---

## 四、测试与缺陷管理 (Test & Defect Management)

### manage_test_cases - 测试用例表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| test_case_id | TEXT | PK | 测试用例ID |
| project_id | TEXT | FK → manage_projects, ON DELETE CASCADE | 项目ID |
| title | TEXT | NOT NULL | 用例标题 |
| description | TEXT | | 用例描述 |
| status | TEXT | NOT NULL, DEFAULT 'draft' | 状态: draft, active, deprecated |
| source | TEXT | | 来源 |
| created_by | TEXT | | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

**唯一约束**: (project_id, test_case_id)

### manage_requirement_test_links - 需求-测试用例关联表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| link_id | SERIAL | PK | 关联ID |
| requirement_id | TEXT | FK → manage_requirements, ON DELETE CASCADE | 需求ID |
| test_case_id | TEXT | FK → manage_test_cases, ON DELETE CASCADE | 测试用例ID |
| link_type | TEXT | NOT NULL, DEFAULT 'verification' | 关联类型 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

**唯一约束**: (requirement_id, test_case_id)

### manage_defects - 缺陷表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| defect_id | TEXT | PK | 缺陷ID |
| project_id | TEXT | FK → manage_projects, ON DELETE CASCADE | 项目ID |
| requirement_id | TEXT | NOT NULL | 需求ID（复合外键） |
| title | TEXT | NOT NULL | 缺陷标题 |
| reproduce_steps | TEXT | NOT NULL, DEFAULT '' | 复现步骤 |
| severity | TEXT | NOT NULL, DEFAULT 'medium' | 严重程度: critical, high, medium, low |
| priority | TEXT | NOT NULL, DEFAULT 'P2' | 优先级: P0, P1, P2, P3 |
| status | TEXT | NOT NULL, DEFAULT 'open' | 状态: open, in_progress, resolved, verified, closed, rejected |
| reporter | TEXT | | 报告人 |
| dev_assignee | TEXT | | 开发负责人 |
| tester_assignee | TEXT | | 测试负责人 |
| current_assignee | TEXT | | 当前负责人 |
| created_by | TEXT | | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_by | TEXT | | 更新人 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

**复合外键**: (project_id, requirement_id) → manage_requirements

---

## 五、里程碑管理 (Milestone Management)

### manage_milestones - 里程碑表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| milestone_id | TEXT | PK | 里程碑ID |
| project_id | TEXT | FK → manage_projects, ON DELETE CASCADE | 项目ID |
| name | TEXT | NOT NULL | 里程碑名称 |
| description | TEXT | | 里程碑描述 |
| message | TEXT | | 消息 |
| milestone_type | TEXT | NOT NULL, DEFAULT 'regular' | 类型: regular, baseline, branch, merge |
| is_baseline | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否为基线 |
| sprint | TEXT | | 冲刺/迭代 |
| version | TEXT | | 版本号 |
| tags | JSONB | DEFAULT '[]' | 标签数组 |
| metadata | JSONB | DEFAULT '{}' | 元数据 |
| created_by | TEXT | | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

**唯一约束**: (project_id, milestone_id)

### manage_milestone_nodes - 里程碑节点表（需求快照）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| snapshot_id | TEXT | PK | 快照ID |
| milestone_id | TEXT | FK → manage_milestones, ON DELETE CASCADE | 里程碑ID |
| requirement_id | TEXT | FK → manage_requirements, ON DELETE CASCADE | 需求ID |
| requirement_type | TEXT | | 需求类型（快照） |
| status | TEXT | | 状态（快照） |
| title | TEXT | | 标题（快照） |
| description | TEXT | | 描述（快照） |
| parent_id | TEXT | | 父需求ID（快照） |
| order_index | INTEGER | DEFAULT 0 | 排序索引（快照） |
| snapshot_data | JSONB | | 完整快照数据 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

---

## 六、分支与变更管理 (Branch & Change Management)

### manage_branches - 分支表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| branch_id | TEXT | PK | 分支ID |
| project_id | TEXT | FK → manage_projects, ON DELETE CASCADE | 项目ID |
| base_milestone_id | TEXT | FK → manage_milestones, ON DELETE RESTRICT | 基线里程碑ID |
| name | TEXT | NOT NULL | 分支名称 |
| status | TEXT | NOT NULL, DEFAULT 'active' | 状态: active, under_review, merged, closed |
| metadata | JSONB | DEFAULT '{}' | 元数据 |
| created_by | TEXT | | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |

**唯一约束**: (project_id, name)

### manage_change_sets - 变更集表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| change_id | TEXT | PK | 变更ID |
| branch_id | TEXT | FK → manage_branches, ON DELETE CASCADE | 分支ID |
| change_type | TEXT | NOT NULL | 变更类型: added, modified, deleted, moved |
| requirement_id | TEXT | FK → manage_requirements, ON DELETE SET NULL | 关联需求ID |
| before_data | JSONB | | 变更前数据 |
| after_data | JSONB | | 变更后数据 |
| created_by | TEXT | | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

---

## 七、协同与审计日志 (Collaboration & Audit Logs)

### manage_comments - 评论表（多态）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| comment_id | TEXT | PK | 评论ID |
| project_id | TEXT | FK → manage_projects, ON DELETE CASCADE | 项目ID |
| target_type | TEXT | NOT NULL | 目标类型: requirement, defect, test_case, milestone |
| target_id | TEXT | NOT NULL | 目标ID（多态） |
| content | TEXT | NOT NULL | 评论内容 |
| reply_to_id | TEXT | FK → manage_comments, ON DELETE SET NULL | 回复的评论ID |
| created_by | TEXT | NOT NULL | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 更新时间 |
| deleted | BOOLEAN | NOT NULL, DEFAULT FALSE | 软删除标记 |

### manage_audit_logs - 审计日志表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| log_id | TEXT | PK | 日志ID |
| project_id | TEXT | FK → manage_projects, ON DELETE SET NULL | 项目ID |
| product_id | TEXT | FK → manage_products, ON DELETE SET NULL | 产品ID |
| actor | TEXT | NOT NULL | 操作人 |
| action | TEXT | NOT NULL | 操作类型 |
| target_type | TEXT | | 目标类型 |
| target_id | TEXT | | 目标ID |
| detail | JSONB | DEFAULT '{}' | 详情 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

---

## 表关系总览

```
manage_products (产品)
├── 1:N manage_product_members (产品成员)
└── 1:N manage_projects (项目)
    ├── 1:N manage_project_members (项目成员)
    ├── 1:N manage_requirements (需求树)
    │   ├── 1:N manage_requirements (自引用父需求)
    │   ├── N:M manage_requirements (通过 manage_requirement_links)
    │   ├── 1:N manage_defects (缺陷)
    │   └── N:M manage_test_cases (通过 manage_requirement_test_links)
    ├── 1:N manage_test_cases (测试用例)
    ├── 1:N manage_milestones (里程碑)
    │   ├── 1:N manage_milestone_nodes (里程碑节点)
    │   └── 1:N manage_branches (分支)
    │       └── 1:N manage_change_sets (变更集)
    ├── 1:N manage_branches (分支)
    ├── 1:N manage_comments (协同评论 - 多态)
    └── 1:N manage_audit_logs (审计日志)

manage_comments (多态关联)
└── target_id → requirements / defects / test_cases / milestones

manage_audit_logs (多态关联)
└── target_id → 任意对象实体
```

---

## 实体说明

### 关系类型

| 关系类型 | 说明 |
|----------|------|
| 1:N | 一对多关系，如 products → projects |
| 自引用 1:N | 需求树形结构，requirements.parent_id → requirements.req_id |
| N:M (自关联) | 需求间平行依赖，通过 manage_requirement_links |
| N:M | 需求 ↔ 测试用例，通过 manage_requirement_test_links |
| 多态 | manage_comments.target_id 关联多种实体 |

### 层级结构

1. **产品层 (Product Layer)**: manage_products, manage_product_members
2. **项目层 (Project Layer)**: manage_projects, manage_project_members
3. **需求层 (Requirements Layer)**: manage_requirements, manage_requirement_links
4. **测试与缺陷层**: manage_test_cases, manage_requirement_test_links, manage_defects
5. **里程碑层**: manage_milestones, manage_milestone_nodes
6. **分支与变更层**: manage_branches, manage_change_sets
7. **协同与审计层**: manage_comments, manage_audit_logs
