# ER 图 — 需求管理数据库

> PlantUML 源文件：[`docs/er-diagram.uml`](./er-diagram.uml)
>
> 当前文档与 ER 图均以 `db/requirements_db.sql` 和 `db/requirements_db_constraints_patch.sql` 为准。

## 1. 概述

本数据库为**需求管理系统**的管理模块，支持产品-项目-需求三级管理、产品/项目成员管理、测试用例追踪、缺陷管理、里程碑管理、分支变更管理、协同评论及审计日志。

- **实体数量**：15 个
- **关系类型**：1:N（主）、M:N（通过关联表）、自引用 1:N、多态关联
- **DBMS**：PostgreSQL
- **图文件**：`docs/er-diagram.uml`
- **字段与关系来源**：`db/requirements_db.sql` + `db/requirements_db_constraints_patch.sql`

---

## 2. 实体关系图（文字版 IDEF1X）

```
┌─────────────────────┐       ┌──────────────────────────┐
│  manage_products     │       │  manage_product_members  │
│─────────────────────│       │──────────────────────────│
│ PK product_id        │───────│ PK id                    │
│    name              │  1:N  │ FK product_id            │
│    description       │       │    user_id               │
│    status            │       │    role                  │
│    roadmap           │       │    created_at            │
│    version           │       │    updated_at            │
│    tags (JSONB)      │       └──────────────────────────┘
│    created_by        │
│    created_at        │
│    updated_at        │
└─────────┬─────────────┘
          │ 1:N
          ▼
┌─────────────────────┐       ┌──────────────────────────┐
│  manage_projects     │       │  manage_project_members  │
│─────────────────────│       │──────────────────────────│
│ PK project_id        │───────│ PK id                    │
│    name              │  1:N  │ FK project_id            │
│    description       │       │    user_id               │
│    status            │       │    role                  │
│ FK product_id        │       │    created_at            │
│    current_session_id│       │    updated_at            │
│    created_by        │       └──────────────────────────┘
│    created_at        │
│    updated_at        │
└─────────┬─────────────┐
          │ 1:N         │ 1:N
          ▼             ▼
┌─────────────────────┐       ┌──────────────────────────┐
│ manage_requirements  │       │  manage_comments         │
│─────────────────────│       │──────────────────────────│
│ PK req_id            │       │ PK comment_id            │
│ FK project_id        │       │ FK project_id            │
│ FK parent_id (自引用)│       │    target_type           │
│    requirement_type  │       │    target_id             │
│    status            │       │    content               │
│    title             │       │ FK reply_to_id (自引用)  │
│    priority          │       │    created_by            │
│    assignee          │       │    created_at            │
│    order_index       │       │    updated_at            │
│    deleted           │       │    deleted               │
└──────┬───────────────┘       └──────────────────────────┘
       │ 1:N   ▲
       │       │ M:N（通过关联表）
       ▼       │
┌─────────────────────┐       ┌──────────────────────────┐
│ manage_defects       │       │ manage_requirement_links │
│─────────────────────│       │──────────────────────────│
│ PK defect_id         │       │ PK link_id               │
│ FK project_id        │       │ FK source_req_id         │
│ FK requirement_id    │       │ FK target_req_id         │
│    severity          │       │    link_type             │
│    priority          │       │    created_by            │
│    status            │       │    created_at            │
└─────────────────────┘       └──────────────────────────┘

┌─────────────────────┐       ┌──────────────────────────┐
│ manage_test_cases    │       │ manage_requirement_test_ │
│─────────────────────│       │ links                    │
│ PK test_case_id      │───────│──────────────────────────│
│ FK project_id        │  1:N  │ PK link_id               │
│    title             │       │ FK requirement_id        │
│    description       │       │ FK test_case_id          │
│    status            │       │    link_type             │
│    source            │       │    created_at            │
│    created_by        │       └──────────────────────────┘
│    created_at        │
└─────────────────────┘

┌─────────────────────┐       ┌──────────────────────────┐
│ manage_milestones    │       │ manage_milestone_nodes   │
│─────────────────────│       │──────────────────────────│
│ PK milestone_id      │───────│ PK snapshot_id           │
│ FK project_id        │  1:N  │ FK milestone_id          │
│    name              │       │ FK requirement_id        │
│    milestone_type    │       │    snapshot_data (JSONB) │
│    is_baseline       │       │    created_at            │
│    sprint            │       └──────────────────────────┘
│    version           │
│    metadata (JSONB)  │
└─────────┬────────────┘
          │ 1:N
          ▼
┌─────────────────────┐       ┌──────────────────────────┐
│ manage_branches      │       │ manage_change_sets       │
│─────────────────────│       │──────────────────────────│
│ PK branch_id         │───────│ PK change_id             │
│ FK project_id        │  1:N  │ FK branch_id             │
│ FK base_milestone_id │       │ FK requirement_id        │
│    name              │       │    change_type           │
│    status            │       │    before_data (JSONB)   │
│    metadata (JSONB)  │       │    after_data (JSONB)    │
│    created_at        │       │    created_at            │
│    updated_at        │       └──────────────────────────┘
└─────────────────────┘

┌─────────────────────┐
│ manage_audit_logs    │
│─────────────────────│
│ PK log_id            │
│ FK project_id        │
│ FK product_id        │
│    actor             │
│    action            │
│    target_type       │
│    target_id         │
│    detail (JSONB)    │
│    created_at        │
└─────────────────────┘
```

补充说明：

- `manage_project_members` 表示项目与用户之间的成员关系，是 `manage_projects` 的 1:N 子实体。
- `manage_requirement_links` 用于表达需求之间的平行依赖、阻塞、关联、重复等关系，是 `manage_requirements` 到自身的 M:N 联系展开表。
- `manage_comments` 是协同评论实体，通过 `project_id` 归属项目，通过 `reply_to_id` 支持评论树，并通过 `target_type + target_id` 多态挂接需求、缺陷、测试用例和里程碑。

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

**关系**：N:1 → manage_products；1:N → manage_project_members / manage_requirements / manage_defects / manage_test_cases / manage_milestones / manage_branches / manage_comments / manage_audit_logs

---

### 3.4 manage_project_members（项目成员）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| id | SERIAL | PK | 成员记录ID |
| project_id | TEXT | FK → projects, ON DELETE CASCADE | 所属项目 |
| user_id | TEXT | NOT NULL | 用户ID |
| role | TEXT | NOT NULL, CHECK(in/..) | 角色：owner/admin/member/viewer |
| created_at | TIMESTAMPTZ | NOT NULL | 加入时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |

**关系**：N:1 → manage_projects；UK(project_id, user_id)

---

### 3.5 manage_requirements（需求）

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

**关系**：N:1 → manage_projects；自引用 1:N（parent_id → req_id，同项目且禁止成环）；1:N → manage_defects；N:M → manage_requirements（通过 manage_requirement_links）；M:N → manage_test_cases（通过 manage_requirement_test_links，同项目约束）

---

### 3.6 manage_requirement_links（需求关联）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| link_id | SERIAL | PK | 关联记录ID |
| source_req_id | TEXT | FK → requirements, ON DELETE CASCADE | 源需求 |
| target_req_id | TEXT | FK → requirements, ON DELETE CASCADE | 目标需求 |
| link_type | TEXT | NOT NULL, CHECK(in/..) | 关联类型：blocks/depends_on/relates_to/duplicates |
| created_by | TEXT | — | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

**关系**：N:1 → manage_requirements（源需求）；N:1 → manage_requirements（目标需求）；UK(source_req_id, target_req_id, link_type)

---

### 3.7 manage_test_cases（测试用例）

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

### 3.8 manage_requirement_test_links（需求-测试用例关联）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| link_id | SERIAL | PK | 关联记录ID |
| requirement_id | TEXT | FK → requirements, ON DELETE CASCADE | 需求ID |
| test_case_id | TEXT | FK → test_cases, ON DELETE CASCADE | 测试用例ID |
| link_type | TEXT | NOT NULL, DEFAULT 'verification' | 关联类型 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

**关系**：N:1 → manage_requirements；N:1 → manage_test_cases；UK(requirement_id, test_case_id)

---

### 3.9 manage_defects（缺陷）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| defect_id | TEXT | PK | 缺陷唯一标识 |
| project_id | TEXT | FK → projects, ON DELETE CASCADE | 所属项目 |
| requirement_id | TEXT | 与 project_id 共同构成复合 FK → requirements(project_id, req_id), ON DELETE CASCADE | 关联需求，保证缺陷与需求属于同一项目 |
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

**关系**：N:1 → manage_projects；N:1 → manage_requirements（通过 `(project_id, requirement_id)` → `manage_requirements(project_id, req_id)` 的复合外键保证项目范围一致）

---

### 3.10 manage_milestones（里程碑）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| milestone_id | TEXT | PK | 里程碑唯一标识 |
| project_id | TEXT | FK → projects, ON DELETE CASCADE | 所属项目 |
| name | TEXT | NOT NULL | 里程碑名称 |
| description | TEXT | — | 描述 |
| message | TEXT | — | 里程碑消息 |
| milestone_type | TEXT | NOT NULL, CHECK(in/..) | 类型：regular/baseline/branch/merge |
| is_baseline | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否为基线 |
| sprint | TEXT | — | 所属 Sprint |
| version | TEXT | — | 版本号 |
| tags | JSONB | DEFAULT '[]' | 标签 |
| metadata | JSONB | DEFAULT '{}' | 元数据 |
| created_by | TEXT | — | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

**关系**：N:1 → manage_projects；1:N → manage_milestone_nodes；1:N → manage_branches；1:N（多态）→ manage_comments

---

### 3.11 manage_milestone_nodes（里程碑节点/需求快照）

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

**关系**：N:1 → manage_milestones；N:1 → manage_requirements

---

### 3.12 manage_branches（分支）

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

### 3.13 manage_change_sets（变更集）

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

**关系**：N:1 → manage_branches；N:1 → manage_requirements

---

### 3.14 manage_comments（评论）

| 属性 | 数据类型 | 约束 | 说明 |
|------|---------|------|------|
| comment_id | TEXT | PK | 评论唯一标识 |
| project_id | TEXT | FK → projects, ON DELETE CASCADE | 所属项目 |
| target_type | TEXT | NOT NULL, CHECK(in/..) | 目标类型：requirement/defect/test_case/milestone |
| target_id | TEXT | NOT NULL | 目标对象ID |
| content | TEXT | NOT NULL | 评论内容 |
| reply_to_id | TEXT | FK → comments, ON DELETE SET NULL | 回复的上级评论 |
| created_by | TEXT | NOT NULL | 创建人 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | 更新时间 |
| deleted | BOOLEAN | NOT NULL, DEFAULT FALSE | 软删除标记 |

**关系**：N:1 → manage_projects；自引用 1:N（reply_to_id → comment_id）；多态关联 → manage_requirements / manage_defects / manage_test_cases / manage_milestones

---

### 3.15 manage_audit_logs（审计日志）

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

**关系**：N:1 → manage_projects；N:1 → manage_products；多态关联 → 任意业务对象

---

## 4. 关系矩阵

| 源实体 | 目标实体 | 关系类型 | 描述 |
|--------|---------|---------|------|
| manage_products | manage_product_members | 1:N | 一个产品有多个成员 |
| manage_products | manage_projects | 1:N | 一个产品有多个项目 |
| manage_projects | manage_project_members | 1:N | 一个项目有多个成员 |
| manage_projects | manage_requirements | 1:N | 一个项目有多个需求 |
| manage_projects | manage_defects | 1:N | 一个项目有多个缺陷 |
| manage_projects | manage_test_cases | 1:N | 一个项目有多个测试用例 |
| manage_projects | manage_milestones | 1:N | 一个项目有多个里程碑 |
| manage_projects | manage_branches | 1:N | 一个项目有多个分支 |
| manage_projects | manage_comments | 1:N | 一个项目有多条评论 |
| manage_projects | manage_audit_logs | 1:N | 一个项目有多条审计日志 |
| manage_requirements | manage_requirements | 1:N（自引用） | 需求有父子层级关系 |
| manage_requirements | manage_requirements | M:N（通过 manage_requirement_links） | 需求之间存在阻塞、依赖、关联、重复等平行关系 |
| manage_requirements | manage_defects | 1:N | 一个需求有多个缺陷 |
| manage_requirements | manage_test_cases | M:N（通过 manage_requirement_test_links） | 需求与测试用例多对多 |
| manage_milestones | manage_milestone_nodes | 1:N | 一个里程碑有多个快照节点 |
| manage_milestones | manage_branches | 1:N | 一个里程碑可作为多个分支的基础 |
| manage_branches | manage_change_sets | 1:N | 一个分支有多个变更集 |
| manage_comments | manage_comments | 1:N（自引用） | 一条评论可以有多条回复 |
| manage_comments | manage_requirements / manage_defects / manage_test_cases / manage_milestones | 多态 N:1 | 评论可挂接到多种业务对象 |

---

## 5. 完整性约束总结

### 5.1 主键约束（PK）

所有 15 个实体均有主键：

- manage_products.product_id
- manage_product_members.id
- manage_projects.project_id
- manage_project_members.id
- manage_requirements.req_id
- manage_requirement_links.link_id
- manage_test_cases.test_case_id
- manage_requirement_test_links.link_id
- manage_defects.defect_id
- manage_milestones.milestone_id
- manage_milestone_nodes.snapshot_id
- manage_branches.branch_id
- manage_change_sets.change_id
- manage_comments.comment_id
- manage_audit_logs.log_id

### 5.2 外键约束（FK）

- manage_product_members.product_id → manage_products (CASCADE)
- manage_projects.product_id → manage_products (SET NULL)
- manage_project_members.project_id → manage_projects (CASCADE)
- manage_requirements.project_id → manage_projects (CASCADE)
- manage_requirements.parent_id → manage_requirements (SET NULL)
- manage_requirement_links.source_req_id → manage_requirements (CASCADE)
- manage_requirement_links.target_req_id → manage_requirements (CASCADE)
- manage_test_cases.project_id → manage_projects (CASCADE)
- manage_requirement_test_links.requirement_id → manage_requirements (CASCADE)
- manage_requirement_test_links.test_case_id → manage_test_cases (CASCADE)
- manage_defects.project_id / requirement_id → manage_projects / manage_requirements（跨项目一致性由复合外键保证）
- manage_milestones.project_id → manage_projects (CASCADE)
- manage_milestone_nodes.milestone_id → manage_milestones (CASCADE)
- manage_milestone_nodes.requirement_id → manage_requirements (CASCADE)
- manage_branches.project_id → manage_projects (CASCADE)
- manage_branches.base_milestone_id → manage_milestones (RESTRICT)
- manage_change_sets.branch_id → manage_branches (CASCADE)
- manage_change_sets.requirement_id → manage_requirements (SET NULL)
- manage_comments.project_id → manage_projects (CASCADE)
- manage_comments.reply_to_id → manage_comments (SET NULL)
- manage_audit_logs.product_id → manage_products (SET NULL)
- manage_audit_logs.project_id → manage_projects (SET NULL)

### 5.3 非空约束（NOT NULL）

- 产品：name, status, created_at, updated_at
- 产品成员：product_id, user_id, role, created_at, updated_at
- 项目：name, status, created_at, updated_at
- 项目成员：project_id, user_id, role, created_at, updated_at
- 需求：project_id, requirement_type, status, title, order_index, is_planned, created_at, updated_at, deleted
- 需求关联：source_req_id, target_req_id, link_type, created_at
- 测试用例：project_id, title, status, created_at
- 需求-测试关联：requirement_id, test_case_id, link_type, created_at
- 缺陷：project_id, requirement_id, title, reproduce_steps, severity, priority, status, created_at, updated_at
- 里程碑：project_id, name, milestone_type, created_at
- 里程碑节点：milestone_id, requirement_id, created_at
- 分支：project_id, base_milestone_id, name, status, created_at, updated_at
- 变更集：branch_id, change_type, created_at
- 评论：project_id, target_type, target_id, content, created_by, created_at, updated_at, deleted
- 审计日志：actor, action, created_at

### 5.4 唯一约束（UNIQUE）

- manage_products.name
- manage_projects.name
- manage_product_members(product_id, user_id)
- manage_project_members(project_id, user_id)
- manage_requirements(project_id, req_id)
- manage_requirement_links(source_req_id, target_req_id, link_type)
- manage_test_cases(project_id, test_case_id)
- manage_requirement_test_links(requirement_id, test_case_id)
- manage_milestones(project_id, milestone_id)
- manage_branches(project_id, name)

### 5.5 检查约束（CHECK）

- products.status IN ('active', 'archived')
- product_members.role IN ('owner', 'admin', 'member', 'viewer')
- projects.status IN ('active', 'archived')
- project_members.role IN ('owner', 'admin', 'member', 'viewer')
- requirements.requirement_type IN ('top_level', 'low_level', 'task')
- requirements.status IN ('draft', 'under_review', 'confirmed', 'in_progress', 'completed', 'archived')
- requirements.priority IN ('low', 'medium', 'high')
- requirement_links.link_type IN ('blocks', 'depends_on', 'relates_to', 'duplicates')
- requirement_links.source_req_id != target_req_id
- test_cases.status IN ('draft', 'active', 'deprecated')
- defects.severity IN ('critical', 'high', 'medium', 'low')
- defects.priority IN ('P0', 'P1', 'P2', 'P3')
- defects.status IN ('open', 'in_progress', 'resolved', 'verified', 'closed', 'rejected')
- milestones.milestone_type IN ('regular', 'baseline', 'branch', 'merge')
- branches.status IN ('active', 'under_review', 'merged', 'closed')
- change_sets.change_type IN ('added', 'modified', 'deleted', 'moved')
- comments.target_type IN ('requirement', 'defect', 'test_case', 'milestone')

### 5.6 触发器约束（业务完整性）

- 父需求、需求关联、需求-测试关联、分支-里程碑、里程碑快照、变更集、评论与审计日志均校验同项目范围
- 需求层级规则：top_level 无父需求；low_level 的父需求必须为 top_level；task 的父需求必须为 top_level 或 low_level
- 禁止需求父子循环引用
- 禁止评论跨项目回复
- 禁止审计日志中的产品与项目归属不一致

---

## 6. ER 到关系模型的转换

### 6.1 每个实体如何转换成关系表

本设计采用“**一个实体对应一张主关系表**”的基本策略：

| ER 实体 | 转换后的关系表 | 主键 | 说明 |
|--------|---------------|------|------|
| 产品 | manage_products | product_id | 直接映射为产品主表 |
| 产品成员 | manage_product_members | id | 依附产品的成员实体，保留 product_id 外键 |
| 项目 | manage_projects | project_id | 直接映射为项目主表 |
| 项目成员 | manage_project_members | id | 依附项目的成员实体，保留 project_id 外键 |
| 需求 | manage_requirements | req_id | 直接映射为需求主表，并通过 parent_id 表达树结构 |
| 需求关联 | manage_requirement_links | link_id | 将需求间平行依赖关系单独建模为关联实体 |
| 测试用例 | manage_test_cases | test_case_id | 直接映射为测试用例表 |
| 需求-测试关联 | manage_requirement_test_links | link_id | 将需求与测试用例的多对多关系展开为关联表 |
| 缺陷 | manage_defects | defect_id | 直接映射为缺陷表，并保留 requirement_id 外键 |
| 里程碑 | manage_milestones | milestone_id | 直接映射为里程碑表 |
| 里程碑节点 | manage_milestone_nodes | snapshot_id | 作为需求在特定里程碑时刻的快照实体 |
| 分支 | manage_branches | branch_id | 直接映射为分支表，并引用基线里程碑 |
| 变更集 | manage_change_sets | change_id | 作为分支的从属变更记录实体 |
| 评论 | manage_comments | comment_id | 协同评论实体，使用 reply_to_id 构建评论树 |
| 审计日志 | manage_audit_logs | log_id | 直接映射为审计日志表 |

整体上，强实体直接转换为主表，联系实体与业务从属记录也显式落地为独立关系表，便于约束、查询和扩展。

### 6.2 每个联系如何转换成外键或关联表

- **1:N 联系转换为外键**
  - 产品 → 项目：`manage_projects.product_id`
  - 项目 → 需求：`manage_requirements.project_id`
  - 项目 → 缺陷：`manage_defects.project_id`
  - 项目 → 测试用例：`manage_test_cases.project_id`
  - 项目 → 里程碑：`manage_milestones.project_id`
  - 项目 → 分支：`manage_branches.project_id`
  - 项目 → 评论：`manage_comments.project_id`
  - 项目 → 审计日志：`manage_audit_logs.project_id`

- **自引用 1:N 联系转换为同表外键**
  - 需求父子层级：`manage_requirements.parent_id → manage_requirements.req_id`
  - 评论回复关系：`manage_comments.reply_to_id → manage_comments.comment_id`

- **M:N 联系转换为关联表**
  - 需求 ↔ 测试用例：`manage_requirement_test_links(requirement_id, test_case_id, link_type, created_at)`
  - 需求 ↔ 需求：`manage_requirement_links(source_req_id, target_req_id, link_type, created_at)`

- **从属记录转换为独立关系表**
  - 里程碑 → 里程碑节点：`manage_milestone_nodes.milestone_id`
  - 分支 → 变更集：`manage_change_sets.branch_id`

- **多态联系转换为类型列 + 目标标识**
  - 评论：`target_type + target_id`
  - 审计日志：`target_type + target_id`

这种多态联系无法完全用标准外键直接表达，因此数据库通过 `CHECK`、触发器和应用层校验来保证目标对象类型和项目范围的一致性。

### 6.3 关系模式的完整性讨论

- **实体完整性**
  - 所有 15 张关系表均定义主键，确保元组可唯一识别。

- **参照完整性**
  - 主要业务对象之间通过外键维护层级与归属关系。
  - 删除语义采用了 `CASCADE`、`SET NULL` 和 `RESTRICT` 的混合策略，以符合业务需求。
  - `manage_defects` 通过 `(project_id, requirement_id)` 指向 `manage_requirements(project_id, req_id)`，进一步保证“缺陷与需求必须属于同一项目”。

- **用户定义完整性**
  - 状态、角色、优先级、严重程度、需求类型、变更类型等均通过 `CHECK` 约束限制取值范围。
  - 需求层级、跨项目范围、评论回复范围、审计日志项目-产品一致性等通过触发器实现。

- **应用层完整性补充**
  - 后端接口对空标题、非法状态、非法父需求、跨项目引用等进行了参数校验，并在交互层返回中文提示。

- **多态引用的局限**
  - `manage_comments.target_type + target_id` 与 `manage_audit_logs.target_type + target_id` 不是纯数据库级外键，因此它们的参照完整性相对弱于普通外键关系，需要触发器和应用层逻辑协同保证。

### 6.4 模式优劣分析

- **规范化程度**
  - 核心业务主表整体接近 **第三范式（3NF）**，实体职责划分较清晰。
  - 但考虑到快照、多态关联和 JSONB 扩展字段，整个模式更准确地说是“以 3NF 为主，并为扩展性做了适度反规范化”，不宜笼统表述为全面满足 BCNF。

- **优点**
  - 实体边界清晰，产品、项目、需求、缺陷、测试、里程碑、分支等主题分离明确。
  - 多对多关系采用关联表展开，结构规范，便于扩展与统计。
  - 通过触发器补足了跨项目一致性、层级规则、循环依赖检测等复杂业务约束。
  - JSONB 字段为标签、元数据、快照和审计详情提供了扩展能力。

- **不足与优化空间**
  - `due_date` 当前为 `TEXT`，若后续需要日期比较、范围查询或日期校验，更适合改为 `DATE` 或 `TIMESTAMPTZ`。
  - `tags`、`metadata`、`custom_fields`、`detail` 等 JSONB 字段增强了灵活性，但牺牲了部分严格规范化和静态约束能力；若查询频繁依赖其中字段，可考虑拆表或建立表达式索引。
  - `current_session_id`、`source_req_id`、`source_level` 等字段尚未形成强外键语义，后续若成为核心业务对象，可进一步实体化。
  - 评论和审计日志的多态目标引用不是纯关系模型中的理想形式；若未来需要更强的数据库级参照完整性，可考虑按目标对象拆分子表或引入统一对象主表。
  - `manage_projects.name` 当前为全局唯一。若业务允许不同产品下项目重名，则可改为 `(product_id, name)` 联合唯一，这会更贴近现实业务边界。

总体来看，当前模式在“规范化”“可实现性”“业务扩展性”之间做了较合理的折中，适合作为课程实验中的完整关系数据库模式。

---

## 7. 视图

### 7.1 v_requirement_details（需求完整视图）

连接 `manage_requirements`、`manage_projects`、`manage_requirement_test_links`、`manage_defects`，聚合测试用例数量、缺陷数量、开启缺陷数量、是否有测试覆盖。

### 7.2 v_project_statistics（项目统计视图）

连接 `manage_projects` 及各子表，聚合需求总数、各状态数量、缺陷数、测试用例数、里程碑数、分支数，计算完成率。

---

## 8. 复杂查询函数

### 8.1 fn_requirement_trace(project_id)

需求追溯查询，连接 4 表以上（`requirements`、`projects`、`requirement_test_links`、`test_cases`、`defects`），并对测试用例和缺陷信息做 JSON 聚合。

### 8.2 fn_project_progress(project_id)

项目进度 CTE 统计，使用 4 个 CTE（`requirement_stats`、`defect_stats`、`test_coverage_stats`、`milestone_stats`）进行多层嵌套聚合。
