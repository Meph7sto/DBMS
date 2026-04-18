<template>
  <div class="query-page">
    <div class="card" style="padding:20px;">
      <div class="card-header" style="margin-bottom:12px;">
        <h4 class="card-kicker" style="margin:0;">演示查询示例</h4>
        <span class="eyebrow" style="text-transform:none;">点击后自动填充到编辑器</span>
      </div>
      <div class="sample-grid">
        <button
          v-for="sample in querySamples"
          :key="sample.label"
          class="sample-btn"
          @click="applySample(sample.sql)"
        >
          <strong>{{ sample.label }}</strong>
          <span>{{ sample.description }}</span>
        </button>
      </div>
    </div>

    <div class="card" style="padding:20px;">
      <div class="card-header" style="margin-bottom:12px;">
        <h4 class="card-kicker" style="margin:0;">完整性约束演示</h4>
        <span class="eyebrow" style="text-transform:none;">点击后先填充 SQL，再手动执行查看中文错误提示</span>
      </div>
      <div class="constraint-copy">
        这六条 SQL 都会故意触发失败，用于课堂演示数据库完整性约束和触发器校验时系统返回的中文提示。
      </div>
      <div class="constraint-grid">
        <button
          v-for="sample in constraintSamples"
          :key="sample.label"
          class="sample-btn constraint-btn"
          @click="applyConstraintSample(sample.sql)"
        >
          <strong>{{ sample.label }}</strong>
          <span>{{ sample.description }}</span>
        </button>
      </div>
    </div>

    <div class="card" style="padding:0; overflow:hidden">
      <div class="card-header" style="padding: 16px 20px; margin-bottom: 0;">
         <h4 class="card-kicker" style="margin: 0;">SQL 编辑器</h4>
         <div class="hero-actions" style="margin: 0; display: flex; align-items: center;">
           <span class="eyebrow" style="margin-right:12px;text-transform:none">Ctrl + Enter 执行</span>
           <button class="ghost" @click="sqlText = ''">清空</button>
           <button class="primary" :disabled="running" @click="run">
             {{ running ? '执行中...' : '▶ 执行' }}
           </button>
         </div>
      </div>
      <div class="editor-panel">
        <SqlEditor v-model="sqlText" @execute="run" style="flex:1;" />
      </div>
      <div v-if="elapsed !== null" style="padding: 8px 20px; font-size: 11px; color: rgba(28,40,52,0.6);" class="eyebrow">
        耗时: {{ elapsed }} ms
      </div>
    </div>

    <div class="card wide result-card" style="flex:1;overflow:hidden;display:flex;flex-direction:column;padding:0;background:rgba(255,255,255,0.95);">
      <ResultTable
        :columns="result.columns"
        :rows="result.rows"
        :row-count="result.rowCount"
        :error="result.error"
        :message="result.message"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { executeQuery } from '../api'
import SqlEditor from '../components/SqlEditor.vue'
import ResultTable from '../components/ResultTable.vue'

const sqlText = ref('SELECT 1;')
const running = ref(false)
const elapsed = ref(null)
const result = reactive({
  columns: [],
  rows: [],
  rowCount: null,
  error: '',
  message: '',
})

const querySamples = [
  {
    label: '产品与项目总览',
    description: '查看两条演示产品线及其下属项目',
    sql: `SELECT
  p.product_id,
  p.name AS product_name,
  pr.project_id,
  pr.name AS project_name,
  pr.status,
  pr.created_at
FROM manage_products p
LEFT JOIN manage_projects pr ON pr.product_id = p.product_id
WHERE p.product_id LIKE 'demo_prod_%'
ORDER BY p.created_at, pr.created_at;`,
  },
  {
    label: '需求树明细',
    description: '查看会员结算改造项目的完整需求层级',
    sql: `SELECT
  req_id,
  parent_id,
  requirement_type,
  status,
  priority,
  assignee,
  order_index,
  title
FROM manage_requirements
WHERE project_id = 'demo_proj_checkout'
  AND deleted = FALSE
ORDER BY parent_id NULLS FIRST, order_index, created_at;`,
  },
  {
    label: '缺陷与负责人',
    description: '查看当前未关闭缺陷及其处理人',
    sql: `SELECT
  d.defect_id,
  d.title,
  d.severity,
  d.priority,
  d.status,
  d.current_assignee,
  r.title AS requirement_title,
  p.name AS project_name
FROM manage_defects d
JOIN manage_projects p ON p.project_id = d.project_id
LEFT JOIN manage_requirements r ON r.req_id = d.requirement_id
WHERE d.defect_id LIKE 'demo_def_%'
  AND d.status IN ('open', 'in_progress', 'resolved')
ORDER BY d.created_at DESC;`,
  },
  {
    label: '里程碑与分支',
    description: '查看基线里程碑和对应开发分支',
    sql: `SELECT
  m.project_id,
  m.name AS milestone_name,
  m.is_baseline,
  b.name AS branch_name,
  b.status AS branch_status,
  b.created_by
FROM manage_milestones m
LEFT JOIN manage_branches b ON b.base_milestone_id = m.milestone_id
WHERE m.milestone_id LIKE 'demo_ms_%'
ORDER BY m.created_at DESC, b.created_at DESC;`,
  },
  {
    label: '评论与审计日志',
    description: '查看演示数据里的协同评论和操作记录',
    sql: `SELECT
  'comment' AS record_type,
  c.project_id,
  c.target_type,
  c.target_id,
  c.created_by AS actor,
  c.content AS detail,
  c.created_at
FROM manage_comments c
WHERE c.comment_id LIKE 'demo_comment_%'
UNION ALL
SELECT
  'audit_log' AS record_type,
  a.project_id,
  a.target_type,
  a.target_id,
  a.actor,
  a.action AS detail,
  a.created_at
FROM manage_audit_logs a
WHERE a.log_id LIKE 'demo_log_%'
ORDER BY created_at DESC;`,
  },
  {
    label: '需求追踪视图',
    description: '直接查课程项目的测试覆盖和缺陷统计',
    sql: `SELECT
  req_id,
  requirement_title,
  project_name,
  test_case_count,
  defect_count,
  open_defect_count,
  has_test_coverage
FROM v_requirement_details
WHERE project_id = 'demo_proj_course'
ORDER BY requirement_created_at DESC;`,
  },
  {
    label: '里程碑交付风险',
    description: '按里程碑汇总需求、缺陷、依赖和分支活跃度',
    sql: `SELECT
  milestone_id,
  milestone_name,
  is_baseline,
  scoped_requirement_count,
  incomplete_requirement_count,
  uncovered_requirement_count,
  blocked_requirement_count,
  unresolved_defect_count,
  critical_defect_count,
  active_branch_count,
  pending_change_count,
  risk_score,
  risk_level
FROM fn_milestone_delivery_risk('demo_proj_checkout');`,
  },
]

const constraintSamples = [
  {
    label: '唯一约束',
    description: '单条语句中重复写入同一产品名称，展示“违反唯一约束”中文提示。',
    sql: `INSERT INTO manage_products (product_id, name, status)
VALUES
  ('demo_prod_unique_violation_a', '唯一约束演示产品', 'active'),
  ('demo_prod_unique_violation_b', '唯一约束演示产品', 'active');`,
  },
  {
    label: '外键无效',
    description: '项目引用不存在的产品 ID，展示“外键引用无效”中文提示。',
    sql: `INSERT INTO manage_projects (project_id, name, status, product_id)
VALUES ('demo_proj_fk_violation', '外键约束演示项目', 'active', 'prod_not_exists_demo');`,
  },
  {
    label: '非空为空',
    description: '给产品名写入 NULL，展示“字段不能为空”中文提示。',
    sql: `INSERT INTO manage_products (product_id, name, status)
VALUES ('demo_prod_not_null_violation', NULL, 'active');`,
  },
  {
    label: '检查约束',
    description: '写入非法状态值，展示“数据校验失败”中文提示。',
    sql: `INSERT INTO manage_products (product_id, name, status)
VALUES ('demo_prod_check_violation', '检查约束演示产品', 'disabled');`,
  },
  {
    label: '层级规则',
    description: '构造一个没有父需求的 low_level 需求，展示层级触发器中文提示。',
    sql: `WITH seed AS (
  SELECT substring(md5(clock_timestamp()::text) for 8) AS suffix
),
new_project AS (
  INSERT INTO manage_projects (project_id, name, status)
  SELECT
    'demo_proj_hierarchy_' || suffix,
    '层级规则演示项目-' || suffix,
    'active'
  FROM seed
  RETURNING project_id
)
INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
SELECT
  'demo_req_hierarchy_' || seed.suffix,
  new_project.project_id,
  'low_level',
  'draft',
  '层级规则演示需求-' || seed.suffix
FROM seed
JOIN new_project ON TRUE;`,
  },
  {
    label: '跨项目关联',
    description: '让需求和测试用例分属不同项目，展示跨项目触发器中文提示。',
    sql: `WITH seed AS (
  SELECT substring(md5(clock_timestamp()::text) for 8) AS suffix
),
project_a AS (
  INSERT INTO manage_projects (project_id, name, status)
  SELECT
    'demo_proj_scope_a_' || suffix,
    '跨项目约束项目A-' || suffix,
    'active'
  FROM seed
  RETURNING project_id
),
project_b AS (
  INSERT INTO manage_projects (project_id, name, status)
  SELECT
    'demo_proj_scope_b_' || suffix,
    '跨项目约束项目B-' || suffix,
    'active'
  FROM seed
  RETURNING project_id
),
req_a AS (
  INSERT INTO manage_requirements (req_id, project_id, requirement_type, status, title)
  SELECT
    'demo_req_scope_' || seed.suffix,
    project_a.project_id,
    'top_level',
    'draft',
    '跨项目需求-' || seed.suffix
  FROM seed
  JOIN project_a ON TRUE
  RETURNING req_id
),
tc_b AS (
  INSERT INTO manage_test_cases (test_case_id, project_id, title, status)
  SELECT
    'demo_tc_scope_' || seed.suffix,
    project_b.project_id,
    '跨项目测试用例-' || seed.suffix,
    'draft'
  FROM seed
  JOIN project_b ON TRUE
  RETURNING test_case_id
)
INSERT INTO manage_requirement_test_links (requirement_id, test_case_id, link_type)
SELECT req_a.req_id, tc_b.test_case_id, 'verification'
FROM req_a
JOIN tc_b ON TRUE;`,
  },
]

function applySample(sql) {
  sqlText.value = sql
}

function applyConstraintSample(sql) {
  sqlText.value = sql
}

async function run() {
  if (!sqlText.value.trim() || running.value) return
  running.value = true
  result.columns = []
  result.rows = []
  result.rowCount = null
  result.error = ''
  result.message = ''
  elapsed.value = null

  const t0 = performance.now()
  try {
    const { data } = await executeQuery(sqlText.value)
    elapsed.value = Math.round(performance.now() - t0)
    if (data.type === 'result') {
      result.columns = data.columns
      result.rows = data.rows
      result.rowCount = data.row_count
    } else {
      result.message = data.message
      result.rowCount = data.row_count
    }
  } catch (err) {
    elapsed.value = Math.round(performance.now() - t0)
    result.error = err.response?.data?.detail || err.message || '查询失败'
  } finally {
    running.value = false
  }
}
</script>
<style scoped>
.query-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
}

.result-card {
  min-height: 320px;
}

.editor-panel {
  display: flex;
  height: 320px;
  min-height: 240px;
  max-height: 52vh;
  border-bottom: 1px solid rgba(28,40,52,0.12);
}

.sample-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.constraint-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.constraint-copy {
  margin-bottom: 12px;
  font-size: 12px;
  color: rgba(28,40,52,0.64);
  line-height: 1.6;
}

.sample-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 14px 16px;
  border: 1px solid rgba(28,40,52,0.12);
  background: rgba(255,255,255,0.92);
  color: var(--near-black);
  text-align: left;
  transition: background-color 120ms ease, border-color 120ms ease, transform 120ms ease;
}

.sample-btn strong {
  font-size: 13px;
  color: var(--accent);
}

.sample-btn span {
  font-size: 12px;
  color: rgba(28,40,52,0.65);
  line-height: 1.5;
}

.sample-btn:hover {
  background: rgba(201, 100, 66, 0.06);
  border-color: rgba(201, 100, 66, 0.24);
  transform: translateY(-1px);
}

.constraint-btn {
  background: rgba(255, 248, 238, 0.96);
}

.constraint-btn:hover {
  background: rgba(201, 100, 66, 0.08);
}
</style>
