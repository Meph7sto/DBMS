# ER 图 — 需求管理数据库（Semantic-Atlas 管理模块）

## 1. 概述

本数据库为 **Semantic-Atlas 需求管理系统**的管理模块，支持产品-项目-需求三级管理、测试用例追踪、缺陷管理、里程碑管理、分支变更管理及审计日志。

- **实体数量**：12 个
- **关系类型**：1:N（主）、M:N（通过关联表）、自引用 1:N
- **DBMS**：PostgreSQL

---

## 2. 实体关系图（文字版 IDEF1X）

```
┌─────────────────────┐       ┌──────────────────────────┐
│  manage_products     │       │  manage_product_members  │
│─────────────────────│       │──────────────────────────│
│ PK product_id        │───────│ FK product_id            │
│    name               │  1:N  │    user_id               │
│    description        │       │    role                  │
│    status             │       │    created_at            │
│    roadmap            │       │    updated_at            │
│    version            │       └──────────────────────────┘
│    tags (JSONB)       │
│    created_by         │
│    created_at         │
│    updated_at         │
└─────────┬─────────────┘
          │ 1:N
          ▼
┌─────────────────────┐       ┌──────────────────────────┐
│  manage_projects     │       │  manage_requirements     │
│─────────────────────│       │──────────────────────────│
│ PK project_id        │───────│ FK project_id            │───┐
│    name               │  1:N  │ PK req_id                │   │
│    description        │       │ FK parent_id (自引用)     │   │
│    status             │       │    requirement_type       │   │
│ FK product_id         │       │    status                │   │
│    current_session_id │       │    title                 │   │
│    created_by         │       │    description           │   │
│    created_at         │       │    priority             │   │
│    updated_at         │       │    assignee             │   │
└─────────┬─────────────┘       │    tags (JSONB)         │   │
          │                      │    due_date             │   │
          │ 1:N                  │    order_index          │   │
          │                      │    source_req_id        │   │
          ▼                      │    is_planned           │   │
┌─────────────────────┐       │    deleted               │   │
│  manage_defects     │       │    created_by           │   │
│─────────────────────│       │    created_at           │   │
│ PK defect_id        │       │    updated_by           │   │
│ FK project_id       │       │    updated_at           │   │
│ FK requirement_id   │───────│                         │   │
│    title            │       └──────────────────────────┘   │
│    reproduce_steps  │                 ▲                   │
│    severity          │                 │ 1:N (自引用)      │
│    priority          │                 │                  │
│    status            │       ┌─────────┴──────────────────┐
│    reporter          │       │  (parent_id → req_id)     │
│    current_assignee  │       └───────────────────────────┘
│    created_at        │
│    updated_at        │
└─────────────────────┘

┌─────────────────────┐       ┌──────────────────────────┐
│  manage_test_cases   │       │ manage_requirement_test_  │
│─────────────────────│       │ links                     │
│ PK test_case_id     │───────│──────────────────────────│
│ FK project_id       │  1:N  │ PK link_id               │
│    title            │       │ FK requirement_id         │──┘
│    description      │       │ FK test_case_id           │
│    status            │       │    link_type              │
│    source           │       │    created_at             │
│    created_by        │       └──────────────────────────┘
│    created_at        │
└─────────────────────┘

┌─────────────────────┐       ┌──────────────────────────┐
│  manage_milestones   │       │  manage_milestone_nodes   │
│─────────────────────│       │──────────────────────────│
│ PK milestone_id     │───────│ FK milestone_id          │───┐
│ FK project_id       │  1:N  │ PK snapshot_id           │   │
│    name             │       │ FK requirement_id         │   │
│    description      │       │    requirement_type       │   │
│    message          │       │    status                 │   │
│    milestone_type   │       │    title                 │   │
│    is_baseline      │       │    description           │   │
│    sprint           │       │    parent_id              │   │
│    version          │       │    order_index           │   │
│    tags (JSONB)     │       │    snapshot_data (JSONB) │   │
│    metadata (JSONB) │       │    created_at            │   │
│    created_by        │       └──────────────────────────┘
│    created_at        │
└─────────┬───────────┘
          │ 1:N
          ▼
┌─────────────────────┐       ┌──────────────────────────┐
│  manage_branches     │       │  manage_change_sets       │
│─────────────────────│       │──────────────────────────│
│ PK branch_id        │───────│ FK branch_id             │───┐
│ FK project_id       │  1:N  │ PK change_id            │   │
│ FK base_milestone_id│       │    change_type           │   │
│    name             │       │ FK requirement_id         │   │
│    status           │       │    before_data (JSONB)   │   │
│    metadata (JSONB) │       │    after_data (JSONB)    │   │
│    created_by       │       │    created_by            │   │
│    created_at       │       │    created_at            │   │
│    updated_at       │       └──────────────────────────┘
└─────────────────────┘

┌─────────────────────┐
│  manage_audit_logs  │
│─────────────────────│
│ PK log_id           │
│ FK project_id       │
│    product_id       │
│    actor            │
│    action           │
│    target_type       │
│    target_id         │
│    detail (JSONB)    │
│    created_at        │
└─────────────────────┘
```

---

## 3. 实体详细说明

### 3.1 manage_products（产品）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| product_id | TEXT | PK | 产品唯一标识 |
| name | TEXT | NOT NULL, UNIQUE | 产品名称 |
| description | TEXT | — | 产品描述 |
| status | TEXT | NOT NULL, CHECK(in/..) | 状态：active/archived |
| roadmap | TEXT | — | 产品路线图 |
| version | TEXT | — | 当前版本 |
| tags | JSONB | DEFAULT '[]' | 标签数组 |
| created_by | TEXT | — | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

**关系**：1:N → manage_product_members（产品成员），1:N → manage_projects（项目）

---

### 3.2 manage_product_members（产品成员）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| id | SERIAL | PK | 成员记录ID |
| product_id | TEXT | FK → products, ON DELETE CASCADE | 所属产品 |
| user_id | TEXT | NOT NULL | 用户ID |
| role | TEXT | NOT NULL, CHECK(in/..) | 角色：owner/admin/member/viewer |
| created_at | TIMESTAMPTZ | NOT NULL | 加入时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

**关系**：N:1 → manage_products；UK(product_id, user_id)

---

### 3.3 manage_projects（项目）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| project_id | TEXT | PK | 项目唯一标识 |
| name | TEXT | NOT NULL, UNIQUE | 项目名称 |
| description | TEXT | — | 项目描述 |
| status | TEXT | NOT NULL, CHECK(in/..) | 状态：active/archived |
| product_id | TEXT | FK → products, ON DELETE SET NULL | 所属产品 |
| current_session_id | TEXT | — | 当前会话ID |
| created_by | TEXT | — | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

**关系**：N:1 → manage_products；1:N → manage_requirements/defects/test_cases/milestones/branches/audit_logs

---

### 3.4 manage_requirements（需求）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| req_id | TEXT | PK | 需求唯一标识 |
| project_id | TEXT | FK → projects, ON DELETE CASCADE | 所属项目 |
| parent_id | TEXT | FK → requirements, ON DELETE SET NULL | 父需求ID（自引用，同项目约束由触发器保证） |
| requirement_type | TEXT | NOT NULL, CHECK(in/..) | 类型：top_level/low_level/task |
| status | TEXT | NOT NULL, CHECK(in/..) | 状态：draft/under_review/confirmed/in_progress/completed/archived |
| title | TEXT | NOT NULL | 需求标题 |
| description | TEXT | — | 需求描述 |
| priority | TEXT | CHECK(in/..) | 优先级：low/medium/high |
| assignee | TEXT | — | 负责人 |
| tags | JSONB | DEFAULT '[]' | 标签 |
| due_date | TEXT | — | 截止日期 |
| order_index | INTEGER | NOT NULL, DEFAULT 0 | 排序索引 |
| source_req_id | TEXT | — | 源需求ID |
| source_level | TEXT | — | 源层级 |
| custom_fields | JSONB | DEFAULT '{}' | 自定义字段 |
| is_planned | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否已计划 |
| created_by | TEXT | — | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_by | TEXT | — | 更新人 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |
| deleted | BOOLEAN | NOT NULL, DEFAULT FALSE | 软删除标记 |

**关系**：N:1 → manage_projects；自引用 1:N（parent_id → req_id，同项目且禁止成环）；1:N → manage_defects；M:N → manage_test_cases（通过 manage_requirement_test_links，同项目约束）

---

### 3.5 manage_test_cases（测试用例）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| test_case_id | TEXT | PK | 测试用例唯一标识 |
| project_id | TEXT | FK → projects, ON DELETE CASCADE | 所属项目 |
| title | TEXT | NOT NULL | 用例标题 |
| description | TEXT | — | 用例描述 |
| status | TEXT | NOT NULL, CHECK(in/..) | 状态：draft/active/deprecated |
| source | TEXT | — | 来源需求 |
| created_by | TEXT | — | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

**关系**：N:1 → manage_projects；M:N → manage_requirements（通过 manage_requirement_test_links）

---

### 3.6 manage_requirement_test_links（需求-测试用例关联）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| link_id | SERIAL | PK | 关联记录ID |
| requirement_id | TEXT | FK → requirements, ON DELETE CASCADE | 需求ID |
| test_case_id | TEXT | FK → test_cases, ON DELETE CASCADE | 测试用例ID |
| link_type | TEXT | NOT NULL, DEFAULT 'verification' | 关联类型 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

**关系**：N:1 → manage_requirements；N:1 → manage_test_cases；UK(requirement_id, test_case_id)

---

### 3.7 manage_defects（缺陷）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| defect_id | TEXT | PK | 缺陷唯一标识 |
| project_id | TEXT | FK → projects, ON DELETE CASCADE | 所属项目 |
| requirement_id | TEXT | FK → requirements, ON DELETE CASCADE | 关联需求 |
| title | TEXT | NOT NULL | 缺陷标题 |
| reproduce_steps | TEXT | NOT NULL, DEFAULT '' | 复现步骤 |
| severity | TEXT | NOT NULL, CHECK(in/..) | 严重程度：critical/high/medium/low |
| priority | TEXT | NOT NULL, CHECK(in/..) | 优先级：P0/P1/P2/P3 |
| status | TEXT | NOT NULL, CHECK(in/..) | 状态：open/in_progress/resolved/verified/closed/rejected |
| reporter | TEXT | — | 报告人 |
| dev_assignee | TEXT | — | 开发负责人 |
| tester_assignee | TEXT | — | 测试负责人 |
| current_assignee | TEXT | — | 当前负责人 |
| created_by | TEXT | — | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_by | TEXT | — | 更新人 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

**关系**：N:1 → manage_projects；N:1 → manage_requirements

---

### 3.8 manage_milestones（里程碑）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| milestone_id | TEXT | PK | 里程碑唯一标识 |
| project_id | TEXT | FK → projects, ON DELETE CASCADE | 所属项目 |
| name | TEXT | NOT NULL | 里程碑名称 |
| description | TEXT | — | 描述 |
| message | TEXT | — | 里程碑消息 |
| milestone_type | TEXT | NOT NULL, CHECK(in/..) | 类型：regular/baseline/branch/merge |
| is_baseline | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否为基线 |
| sprint | TEXT | — | 所属Sprint |
| version | TEXT | — | 版本号 |
| tags | JSONB | DEFAULT '[]' | 标签 |
| metadata | JSONB | DEFAULT '{}' | 元数据 |
| created_by | TEXT | — | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

**关系**：N:1 → manage_projects；1:N → manage_milestone_nodes；1:N → manage_branches

---

### 3.9 manage_milestone_nodes（里程碑节点/需求快照）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| snapshot_id | TEXT | PK | 快照ID |
| milestone_id | TEXT | FK → milestones, ON DELETE CASCADE | 所属里程碑 |
| requirement_id | TEXT | FK → requirements, ON DELETE CASCADE | 需求ID |
| requirement_type | TEXT | — | 需求类型快照 |
| status | TEXT | — | 状态快照 |
| title | TEXT | — | 标题快照 |
| description | TEXT | — | 描述快照 |
| parent_id | TEXT | — | 父需求ID快照 |
| order_index | INTEGER | DEFAULT 0 | 排序索引快照 |
| snapshot_data | JSONB | — | 完整快照数据 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

**关系**：N:1 → manage_milestones

---

### 3.10 manage_branches（分支）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| branch_id | TEXT | PK | 分支唯一标识 |
| project_id | TEXT | FK → projects, ON DELETE CASCADE | 所属项目 |
| base_milestone_id | TEXT | FK → milestones, ON DELETE RESTRICT | 基础里程碑 |
| name | TEXT | NOT NULL | 分支名称 |
| status | TEXT | NOT NULL, CHECK(in/..) | 状态：active/under_review/merged/closed |
| metadata | JSONB | DEFAULT '{}' | 元数据 |
| created_by | TEXT | — | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

**关系**：N:1 → manage_projects；N:1 → manage_milestones；1:N → manage_change_sets；UK(project_id, name)

---

### 3.11 manage_change_sets（变更集）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| change_id | TEXT | PK | 变更唯一标识 |
| branch_id | TEXT | FK → branches, ON DELETE CASCADE | 所属分支 |
| change_type | TEXT | NOT NULL, CHECK(in/..) | 变更类型：added/modified/deleted/moved |
| requirement_id | TEXT | FK → requirements, ON DELETE SET NULL | 关联需求ID |
| before_data | JSONB | — | 变更前数据 |
| after_data | JSONB | — | 变更后数据 |
| created_by | TEXT | — | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

**关系**：N:1 → manage_branches

---

### 3.12 manage_audit_logs（审计日志）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| log_id | TEXT | PK | 日志唯一标识 |
| project_id | TEXT | FK → projects, ON DELETE SET NULL | 关联项目 |
| product_id | TEXT | FK → products, ON DELETE SET NULL | 关联产品 |
| actor | TEXT | NOT NULL | 操作用户 |
| action | TEXT | NOT NULL | 操作类型 |
| target_type | TEXT | — | 目标类型 |
| target_id | TEXT | — | 目标ID |
| detail | JSONB | DEFAULT '{}' | 详细数据 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

**关系**：N:1 → manage_projects

---

## 4. 关系矩阵

| 源实体 | 目标实体 | 关系类型 | 描述 |
|--------|---------|---------|------|
| manage_products | manage_product_members | 1:N | 一个产品有多个成员 |
| manage_products | manage_projects | 1:N | 一个产品有多个项目 |
| manage_projects | manage_requirements | 1:N | 一个项目有多个需求 |
| manage_projects | manage_defects | 1:N | 一个项目有多个缺陷 |
| manage_projects | manage_test_cases | 1:N | 一个项目有多个测试用例 |
| manage_projects | manage_milestones | 1:N | 一个项目有多个里程碑 |
| manage_projects | manage_branches | 1:N | 一个项目有多个分支 |
| manage_projects | manage_audit_logs | 1:N | 一个项目有多条审计日志 |
| manage_requirements | manage_requirements | 1:N（自引用） | 需求有父子层级关系 |
| manage_requirements | manage_defects | 1:N | 一个需求有多个缺陷 |
| manage_requirements | manage_test_cases | M:N（通过关联表） | 需求与测试用例多对多 |
| manage_milestones | manage_milestone_nodes | 1:N | 一个里程碑有多个快照节点 |
| manage_milestones | manage_branches | 1:N | 一个里程碑可作为多个分支的基础 |
| manage_branches | manage_change_sets | 1:N | 一个分支有多个变更集 |

---

## 5. 完整性约束总结

### 5.1 主键约束（PK）
所有 12 个实体均有主键：product_id, id, project_id, req_id, test_case_id, link_id, defect_id, milestone_id, snapshot_id, branch_id, change_id, log_id

### 5.2 外键约束（FK）
- manage_product_members.product_id → manage_products
- manage_projects.product_id → manage_products (SET NULL)
- manage_requirements.project_id → manage_projects (CASCADE)
- manage_requirements.parent_id → manage_requirements (SET NULL)
- manage_test_cases.project_id → manage_projects (CASCADE)
- manage_requirement_test_links.requirement_id → manage_requirements (CASCADE)
- manage_requirement_test_links.test_case_id → manage_test_cases (CASCADE)
- manage_defects.project_id → manage_projects (CASCADE)
- manage_defects.requirement_id → manage_requirements (CASCADE)
- manage_milestones.project_id → manage_projects (CASCADE)
- manage_milestone_nodes.milestone_id → manage_milestones (CASCADE)
- manage_branches.project_id → manage_projects (CASCADE)
- manage_branches.base_milestone_id → manage_milestones (RESTRICT)
- manage_change_sets.branch_id → manage_branches (CASCADE)
- manage_milestone_nodes.requirement_id → manage_requirements (CASCADE)
- manage_change_sets.requirement_id → manage_requirements (SET NULL)
- manage_audit_logs.product_id → manage_products (SET NULL)
- manage_audit_logs.project_id → manage_projects (SET NULL)

### 5.3 非空约束（NOT NULL）
- 产品：name, status, created_at, updated_at
- 项目：name, status, created_at, updated_at
- 需求：project_id, requirement_type, status, title, order_index, created_at, deleted
- 缺陷：project_id, requirement_id, title, reproduce_steps, severity, priority, status, created_at
- 测试用例：project_id, title, status, created_at
- 关联表：requirement_id, test_case_id, link_type, created_at
- 里程碑：project_id, name, milestone_type, created_at
- 分支：project_id, base_milestone_id, name, status, created_at, updated_at
- 变更集：branch_id, change_type, created_at
- 审计日志：actor, action, created_at

### 5.4 唯一约束（UNIQUE）
- manage_products.name
- manage_projects.name
- manage_product_members(product_id, user_id)
- manage_requirement_test_links(requirement_id, test_case_id)
- manage_branches(project_id, name)

### 5.5 检查约束（CHECK）
- products.status IN ('active', 'archived')
- product_members.role IN ('owner', 'admin', 'member', 'viewer')
- projects.status IN ('active', 'archived')
- requirements.requirement_type IN ('top_level', 'low_level', 'task')
- requirements.status IN ('draft', 'under_review', 'confirmed', 'in_progress', 'completed', 'archived')
- requirements.priority IN ('low', 'medium', 'high')
- test_cases.status IN ('draft', 'active', 'deprecated')
- defects.severity IN ('critical', 'high', 'medium', 'low')
- defects.priority IN ('P0', 'P1', 'P2', 'P3')
- defects.status IN ('open', 'in_progress', 'resolved', 'verified', 'closed', 'rejected')
- milestones.milestone_type IN ('regular', 'baseline', 'branch', 'merge')
- branches.status IN ('active', 'under_review', 'merged', 'closed')
- change_sets.change_type IN ('added', 'modified', 'deleted', 'moved')

### 5.6 触发器约束（业务完整性）
- 父需求、需求关联、需求-测试关联、分支-里程碑、里程碑快照、变更集、评论与审计日志均校验同项目范围
- 需求层级规则：top_level 无父需求；low_level 的父需求必须为 top_level；task 的父需求必须为 top_level 或 low_level
- 禁止需求父子循环引用，禁止评论跨项目回复，禁止审计日志中的项目和产品归属不一致

---

## 6. 视图

### 6.1 v_requirement_details（需求完整视图）
连接 manage_requirements、manage_projects、manage_requirement_test_links、manage_defects，聚合测试用例数量、缺陷数量、开启缺陷数量、是否有测试覆盖。

### 6.2 v_project_statistics（项目统计视图）
连接 manage_projects 及各子表，聚合需求总数、各状态数量、缺陷数、测试用例数、里程碑数、分支数，计算完成率。

---

## 7. 复杂查询函数

### 7.1 fn_requirement_trace(project_id)
需求追溯查询，连接 4 表（requirements, projects, requirement_test_links, test_cases, defects），JSON 聚合测试用例和缺陷信息。

### 7.2 fn_project_progress(project_id)
项目进度 CTE 统计，使用 4 个 CTE（requirement_stats, defect_stats, test_coverage_stats, milestone_stats）进行多层嵌套聚合。
