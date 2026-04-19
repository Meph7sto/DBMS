<template>
  <div class="perf-page">
    <div class="perf-hero card wide">
      <div>
        <div class="eyebrow">public.performance_lab</div>
        <h1>索引与视图验证台</h1>
        <p class="perf-copy">
          这个页面用于完成实验要求 a：导入基准数据、构造演示表、对比索引前后执行计划，并给出“视图 SQL / 展开后的直接 SQL / 页面操作步骤”的对照材料。
        </p>
      </div>
      <div class="perf-meta">
        <div class="meta-item">
          <span>当前数据库</span>
          <strong>{{ connection?.database || '未连接' }}</strong>
        </div>
        <div class="meta-item">
          <span>演示项目</span>
          <strong>{{ performanceGuide.demoProjectId }}</strong>
        </div>
        <div class="meta-item">
          <span>演示表</span>
          <strong>{{ performanceGuide.demoTable }}</strong>
        </div>
      </div>
    </div>

    <div v-if="globalError" class="perf-error">{{ globalError }}</div>
    <div v-if="globalMessage" class="perf-message">{{ globalMessage }}</div>

    <div class="perf-grid">
      <section class="card perf-card">
        <div class="card-header">
          <h4 class="card-kicker">步骤控制</h4>
        </div>
        <div class="perf-steps">
          <button class="primary" :disabled="busy || !connection" @click="handleImportBenchmark">
            {{ importState.loading ? '导入中...' : '1. 导入测试数据' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="handleDeleteBenchmark">
            {{ deleteState.loading ? '删除中...' : '2. 删除测试数据' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="loadBenchmarkSummary">
            {{ benchmarkState.loading ? '读取中...' : '3. 刷新数据摘要' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="handleSetupDemoTable">
            {{ setupState.loading ? '初始化中...' : '4. 初始化演示表' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="runBeforePlan">
            {{ beforeState.loading ? '分析中...' : '5. 运行未建索引查询' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="runAfterPlan">
            {{ afterState.loading ? '建索引中...' : '6. 创建索引并重跑' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="loadActiveView">
            {{ viewsState.loading ? '加载中...' : '7. 载入视图结果' }}
          </button>
          <button class="btn-warm-sand" :disabled="busy || !connection" @click="runFullDemo">
            {{ fullDemoLoading ? '执行中...' : '一键完整演示' }}
          </button>
        </div>

        <div class="perf-notes">
          <div class="note-item">
            <span class="note-index">A</span>
            <div>
              <strong>真实查询场景</strong>
              <p>模拟需求列表页：按项目筛选、只看未删除需求、按顺序展示。</p>
            </div>
          </div>
          <div class="note-item">
            <span class="note-index">B</span>
            <div>
              <strong>推荐讲法</strong>
              <p>先看执行计划中的 Seq Scan / Sort，再看建索引后的 Index Scan。</p>
            </div>
          </div>
          <div class="note-item">
            <span class="note-index">C</span>
            <div>
              <strong>视图对照</strong>
              <p>先查看视图 SQL，再查看展开后的直接 SQL，说明视图的价值是复用统计口径，而不只是停留在页面结果层面。</p>
            </div>
          </div>
          <div class="note-item">
            <span class="note-index">D</span>
            <div>
              <strong>中文提示演示</strong>
              <p>性能页负责索引与视图；中文错误提示请切到 SQL 编辑器页面，按预置失败 SQL 逐条查看。</p>
            </div>
          </div>
        </div>

        <div class="benchmark-status">
          <div class="benchmark-header">
            <strong>benchmark 数据摘要</strong>
            <span>{{ benchmarkCaption }}</span>
          </div>
          <div class="benchmark-grid">
            <div v-for="item in benchmarkCards" :key="item.key" class="benchmark-item">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="card perf-card">
        <div class="card-header">
          <h4 class="card-kicker">结果摘要</h4>
        </div>
        <div class="summary-grid">
          <article class="summary-panel">
            <div class="summary-label">建索引前</div>
            <div class="summary-value">
              {{ beforeState.summary.executionTime ?? '—' }}
              <small v-if="beforeState.summary.executionTime !== null">ms</small>
            </div>
            <div class="summary-copy">{{ beforeState.summary.scanType || '尚未执行' }}</div>
            <div class="summary-copy">{{ beforeState.summary.sortMode || '—' }}</div>
          </article>
          <article class="summary-panel accent">
            <div class="summary-label">建索引后</div>
            <div class="summary-value">
              {{ afterState.summary.executionTime ?? '—' }}
              <small v-if="afterState.summary.executionTime !== null">ms</small>
            </div>
            <div class="summary-copy">{{ afterState.summary.scanType || '尚未执行' }}</div>
            <div class="summary-copy">{{ afterState.summary.sortMode || '—' }}</div>
          </article>
          <article class="summary-panel warm">
            <div class="summary-label">对比结论</div>
            <div class="summary-value">
              {{ speedupText }}
            </div>
            <div class="summary-copy">{{ comparisonText }}</div>
            <div class="summary-copy">目标索引：`(project_id, deleted, order_index)`</div>
          </article>
        </div>

        <div class="shortcut-row">
          <router-link class="ghost shortcut-link" to="/table/public/manage_requirements">查看原始表索引</router-link>
          <router-link class="ghost shortcut-link" :to="`/table/public/${performanceGuide.demoTable}`">查看演示副本表</router-link>
          <router-link class="ghost shortcut-link" to="/complex-queries">切换到复杂查询控制台</router-link>
          <router-link class="ghost shortcut-link" to="/query">打开 SQL 编辑器</router-link>
        </div>
      </section>
    </div>

    <div class="perf-grid plans">
      <section class="card perf-card">
        <div class="card-header">
          <h4 class="card-kicker">索引前执行计划</h4>
          <span class="eyebrow">{{ beforeState.elapsedLabel }}</span>
        </div>
        <pre class="plan-output">{{ beforePlanText }}</pre>
      </section>

      <section class="card perf-card">
        <div class="card-header">
          <h4 class="card-kicker">索引后执行计划</h4>
          <span class="eyebrow">{{ afterState.elapsedLabel }}</span>
        </div>
        <pre class="plan-output">{{ afterPlanText }}</pre>
      </section>
    </div>

    <section class="card wide perf-card">
      <div class="card-header">
        <h4 class="card-kicker">视图验证</h4>
        <div class="perf-tabs">
          <button
            class="ribbon-step"
            :class="{ active: activeView === 'projectStats' }"
            :disabled="viewsState.loading || !connection"
            @click="activeView = 'projectStats'; loadActiveView()"
          >
            项目统计视图
          </button>
          <button
            class="ribbon-step"
            :class="{ active: activeView === 'requirementDetails' }"
            :disabled="viewsState.loading || !connection"
            @click="activeView = 'requirementDetails'; loadActiveView()"
          >
            需求详情视图
          </button>
        </div>
      </div>

      <div class="view-copy">
        <span>{{ activeViewLabel }}</span>
        <code>{{ activeViewSql }}</code>
      </div>

      <div class="sql-compare-grid">
        <div class="sql-compare-panel">
          <div class="sql-compare-title">视图 SQL</div>
          <code>{{ activeViewSql }}</code>
        </div>
        <div class="sql-compare-panel">
          <div class="sql-compare-title">直接 SQL</div>
          <code>{{ activeViewDirectSql }}</code>
        </div>
      </div>

      <div class="demo-script">
        <div class="demo-script-title">页面操作步骤</div>
        <p>{{ activeViewPitch }}</p>
        <div class="shortcut-row">
          <router-link class="ghost shortcut-link" to="/query">把对照 SQL 粘贴到 SQL 编辑器</router-link>
          <router-link class="ghost shortcut-link" to="/query">切换到中文错误提示演示</router-link>
        </div>
      </div>

      <div class="view-result">
        <ResultTable
          :title="activeViewLabel"
          :columns="viewResult.columns"
          :rows="viewResult.rows"
          :row-count="viewResult.rowCount"
          :error="viewResult.error"
          :message="viewResult.message"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  deleteBenchmark,
  executeQuery,
  getBenchmarkSummary,
  getPerformanceGuide,
  getPerformancePreview,
  importBenchmark,
} from '../api'
import ResultTable from '../components/ResultTable.vue'

const props = defineProps({
  connection: { type: Object, default: null },
})

const demoProjectId = 'bproj_003'
const demoTable = 'manage_requirements_perf_demo'
const demoIndex = 'idx_req_perf_project_deleted_order'

const globalError = ref('')
const globalMessage = ref('')
const activeView = ref('projectStats')
const fullDemoLoading = ref(false)

const importState = reactive({ loading: false })
const deleteState = reactive({ loading: false })
const benchmarkState = reactive({ loading: false })
const setupState = reactive({ loading: false, elapsedLabel: '尚未执行' })
const beforeState = reactive({
  loading: false,
  elapsedLabel: '尚未执行',
  summary: makeEmptySummary(),
})
const afterState = reactive({
  loading: false,
  elapsedLabel: '尚未执行',
  summary: makeEmptySummary(),
})
const viewsState = reactive({ loading: false })

const beforePlanText = ref('点击“运行未建索引查询”后，这里会显示 EXPLAIN ANALYZE 输出。')
const afterPlanText = ref('点击“创建索引并重跑”后，这里会显示 EXPLAIN ANALYZE 输出。')

const viewResult = reactive({
  columns: [],
  rows: [],
  rowCount: null,
  error: '',
  message: '点击上方按钮加载视图数据。',
})

const benchmarkSummary = reactive({
  products: 0,
  product_members: 0,
  projects: 0,
  project_members: 0,
  requirements: 0,
  requirement_links: 0,
  test_cases: 0,
  requirement_test_links: 0,
  defects: 0,
  milestones: 0,
  milestone_nodes: 0,
  branches: 0,
  change_sets: 0,
  audit_logs: 0,
  total_records: 0,
  has_benchmark_data: false,
})

const performanceGuide = reactive({
  demoProjectId,
  demoTable,
  demoIndex,
  viewScenarios: {
    projectStats: {
      label: 'v_project_statistics 视图结果',
      viewSql: "SELECT project_id, project_name, total_requirements, total_defects, completion_rate_percent FROM v_project_statistics ORDER BY completion_rate_percent DESC LIMIT 8;",
      directSql: `WITH req_stats AS (
  SELECT project_id,
         COUNT(*) FILTER (WHERE deleted = FALSE) AS total_requirements,
         COUNT(*) FILTER (WHERE status = 'completed' AND deleted = FALSE) AS completed_count
  FROM manage_requirements
  GROUP BY project_id
),
def_stats AS (
  SELECT project_id, COUNT(*) AS total_defects
  FROM manage_defects
  GROUP BY project_id
)
SELECT p.project_id, p.name AS project_name,
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
ORDER BY completion_rate_percent DESC
LIMIT 8;`,
      pitch: '可先点“项目统计视图”，说明页面直接读 v_project_statistics；再把右侧直接 SQL 贴到 SQL 编辑器，解释视图把项目级统计口径固化成了统一对象。',
    },
    requirementDetails: {
      label: 'v_requirement_details 视图结果',
      viewSql: `SELECT req_id, requirement_title, project_name, test_case_count, defect_count, open_defect_count FROM v_requirement_details WHERE project_id = '${demoProjectId}' ORDER BY requirement_created_at DESC LIMIT 8;`,
      directSql: `WITH test_stats AS (
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
SELECT r.req_id,
       r.title AS requirement_title,
       p.name AS project_name,
       COALESCE(ts.test_case_count, 0) AS test_case_count,
       COALESCE(ds.defect_count, 0) AS defect_count,
       COALESCE(ds.open_defect_count, 0) AS open_defect_count
FROM manage_requirements r
JOIN manage_projects p ON p.project_id = r.project_id
LEFT JOIN test_stats ts ON ts.requirement_id = r.req_id
LEFT JOIN defect_stats ds ON ds.requirement_id = r.req_id
WHERE r.project_id = '${demoProjectId}' AND r.deleted = FALSE
ORDER BY r.created_at DESC
LIMIT 8;`,
      pitch: '可先点“需求详情视图”，查看需求、测试用例和缺陷的聚合结果；再说明右侧直接 SQL 是视图展开后的等价查询，视图减少了页面重复拼接多表 SQL 的负担。',
    },
  },
})

const activeViewSql = computed(() => (
  performanceGuide.viewScenarios[activeView.value]?.viewSql || ''
))

const activeViewLabel = computed(() => (
  performanceGuide.viewScenarios[activeView.value]?.label || '视图结果'
))

const activeViewDirectSql = computed(() => (
  performanceGuide.viewScenarios[activeView.value]?.directSql || ''
))

const activeViewPitch = computed(() => (
  performanceGuide.viewScenarios[activeView.value]?.pitch || '可在 SQL 编辑器中查看视图与直接 SQL 的对照。'
))

const busy = computed(() => (
  importState.loading
  || deleteState.loading
  || benchmarkState.loading
  || setupState.loading
  || beforeState.loading
  || afterState.loading
  || viewsState.loading
  || fullDemoLoading.value
))

const benchmarkCaption = computed(() => (
  benchmarkSummary.has_benchmark_data
    ? `当前已识别 ${benchmarkSummary.total_records} 条 benchmark 记录`
    : '当前未识别到 benchmark 数据'
))

const benchmarkCards = computed(() => ([
  { key: 'products', label: '产品', value: benchmarkSummary.products },
  { key: 'product_members', label: '产品成员', value: benchmarkSummary.product_members },
  { key: 'projects', label: '项目', value: benchmarkSummary.projects },
  { key: 'project_members', label: '项目成员', value: benchmarkSummary.project_members },
  { key: 'requirements', label: '需求', value: benchmarkSummary.requirements },
  { key: 'requirement_links', label: '需求关联', value: benchmarkSummary.requirement_links },
  { key: 'test_cases', label: '测试用例', value: benchmarkSummary.test_cases },
  { key: 'requirement_test_links', label: '需求-测试关联', value: benchmarkSummary.requirement_test_links },
  { key: 'defects', label: '缺陷', value: benchmarkSummary.defects },
  { key: 'milestones', label: '里程碑', value: benchmarkSummary.milestones },
  { key: 'milestone_nodes', label: '快照节点', value: benchmarkSummary.milestone_nodes },
  { key: 'branches', label: '分支', value: benchmarkSummary.branches },
  { key: 'change_sets', label: '变更集', value: benchmarkSummary.change_sets },
  { key: 'audit_logs', label: '审计日志', value: benchmarkSummary.audit_logs },
  { key: 'total_records', label: '总记录数', value: benchmarkSummary.total_records },
]))

const speedupText = computed(() => {
  const beforeTime = beforeState.summary.executionTime
  const afterTime = afterState.summary.executionTime
  if (beforeTime === null || afterTime === null) return '待比较'
  if (beforeTime === 0) return '已完成'
  return `${(beforeTime / afterTime).toFixed(2)}x`
})

const comparisonText = computed(() => {
  const beforeTime = beforeState.summary.executionTime
  const afterTime = afterState.summary.executionTime
  if (beforeTime === null || afterTime === null) {
    return '完成前后两次执行后，这里会生成结论。'
  }
  if (afterTime < beforeTime) {
    return '建索引后执行时间下降，说明索引命中了该查询路径。'
  }
  if (afterTime === beforeTime) {
    return '两次耗时接近，数据量可能偏小，但执行计划仍可用于说明命中方式。'
  }
  return '建索引后未明显变快，建议重点讲执行计划变化而不是只讲耗时。'
  })

function makeEmptySummary() {
  return {
    executionTime: null,
    planningTime: null,
    scanType: '',
    sortMode: '',
    indexName: '',
  }
}

function resetFeedback() {
  globalError.value = ''
  globalMessage.value = ''
}

async function runSql(sql) {
  const { data } = await executeQuery(sql)
  return data
}

function planLinesToText(lines) {
  return lines.length ? lines.join('\n') : '没有返回执行计划。'
}

function parsePlanSummary(lines) {
  const joined = lines.join('\n')
  const executionMatch = joined.match(/Execution Time: ([\d.]+) ms/i)
  const planningMatch = joined.match(/Planning Time: ([\d.]+) ms/i)
  const scanLine = lines.find((line) => /Index Scan|Seq Scan|Bitmap Heap Scan|Bitmap Index Scan/i.test(line)) || ''
  const sortLine = lines.find((line) => /\bSort\b/i.test(line)) || ''
  const indexLine = lines.find((line) => /Index Cond|using idx_/i.test(line)) || ''

  return {
    executionTime: executionMatch ? Number(executionMatch[1]) : null,
    planningTime: planningMatch ? Number(planningMatch[1]) : null,
    scanType: scanLine ? scanLine.trim() : '未识别到 Scan 节点',
    sortMode: sortLine ? sortLine.trim() : '未出现显式 Sort 节点',
    indexName: indexLine ? indexLine.trim() : '',
  }
}

async function handleImportBenchmark() {
  resetFeedback()
  importState.loading = true
  try {
    await importBenchmark()
    await loadBenchmarkSummary({ silent: true })
    globalMessage.value = '基准测试数据已导入，可以继续初始化演示表。'
  } catch (err) {
    globalError.value = err.response?.data?.detail || err.message || '导入测试数据失败'
  } finally {
    importState.loading = false
  }
}

async function handleDeleteBenchmark() {
  resetFeedback()
  deleteState.loading = true
  try {
    await deleteBenchmark()
    resetBenchmarkState()
    globalMessage.value = 'benchmark 测试数据已删除，可重新导入演示。'
  } catch (err) {
    globalError.value = err.response?.data?.detail || err.message || '删除测试数据失败'
  } finally {
    deleteState.loading = false
  }
}

function resetBenchmarkState() {
  Object.assign(benchmarkSummary, {
    products: 0,
    product_members: 0,
    projects: 0,
    project_members: 0,
    requirements: 0,
    requirement_links: 0,
    test_cases: 0,
    requirement_test_links: 0,
    defects: 0,
    milestones: 0,
    milestone_nodes: 0,
    branches: 0,
    change_sets: 0,
    audit_logs: 0,
    total_records: 0,
    has_benchmark_data: false,
  })
}

async function loadBenchmarkSummary(options = {}) {
  const { silent = false } = options
  if (!silent) {
    resetFeedback()
  }
  benchmarkState.loading = true
  try {
    const { data } = await getBenchmarkSummary()
    Object.assign(benchmarkSummary, data.summary || {})
    if (!silent) {
      globalMessage.value = benchmarkSummary.has_benchmark_data
        ? 'benchmark 数据摘要已刷新。'
        : '当前尚未识别到 benchmark 数据。'
    }
  } catch (err) {
    if (!silent) {
      globalError.value = err.response?.data?.detail || err.message || '读取 benchmark 数据摘要失败'
    }
  } finally {
    benchmarkState.loading = false
  }
}

async function handleSetupDemoTable() {
  resetFeedback()
  setupState.loading = true
  const t0 = performance.now()
  try {
    await runSql(`DROP TABLE IF EXISTS public.${performanceGuide.demoTable};`)
    await runSql(`
      CREATE TABLE public.${performanceGuide.demoTable} AS
      SELECT *
      FROM public.manage_requirements
      WHERE req_id LIKE 'breq_%';
    `)
    await runSql(`ANALYZE public.${performanceGuide.demoTable};`)
    beforeState.summary = makeEmptySummary()
    afterState.summary = makeEmptySummary()
    beforePlanText.value = '演示表已重建。请运行“未建索引查询”生成第一份执行计划。'
    afterPlanText.value = '演示表已重建。创建索引后，这里会显示第二份执行计划。'
    setupState.elapsedLabel = `${Math.round(performance.now() - t0)} ms`
    globalMessage.value = `演示表 public.${performanceGuide.demoTable} 已重建，当前不含自定义索引。`
  } catch (err) {
    globalError.value = err.response?.data?.detail || err.message || '初始化演示表失败'
  } finally {
    setupState.loading = false
  }
}

async function runExplainInto(targetState, targetText) {
  const t0 = performance.now()
  const data = await runSql(`
    EXPLAIN (ANALYZE, BUFFERS)
    SELECT req_id, title, status
    FROM public.${performanceGuide.demoTable}
    WHERE project_id = '${performanceGuide.demoProjectId}' AND deleted = FALSE
    ORDER BY order_index;
  `)
  const lines = (data.rows || []).map((row) => row['QUERY PLAN']).filter(Boolean)
  targetState.summary = parsePlanSummary(lines)
  targetState.elapsedLabel = `${Math.round(performance.now() - t0)} ms`
  targetText.value = planLinesToText(lines)
}

async function runBeforePlan() {
  resetFeedback()
  beforeState.loading = true
  try {
    await runExplainInto(beforeState, beforePlanText)
    globalMessage.value = '索引前执行计划已生成。下一步可以创建索引并重跑。'
  } catch (err) {
    globalError.value = err.response?.data?.detail || err.message || '运行索引前执行计划失败'
  } finally {
    beforeState.loading = false
  }
}

async function runAfterPlan() {
  resetFeedback()
  afterState.loading = true
  try {
    await runSql(`
      CREATE INDEX IF NOT EXISTS ${performanceGuide.demoIndex}
      ON public.${performanceGuide.demoTable}(project_id, deleted, order_index);
    `)
    await runSql(`ANALYZE public.${performanceGuide.demoTable};`)
    await runExplainInto(afterState, afterPlanText)
    globalMessage.value = '组合索引已创建，索引后执行计划已刷新。'
  } catch (err) {
    globalError.value = err.response?.data?.detail || err.message || '运行索引后执行计划失败'
  } finally {
    afterState.loading = false
  }
}

async function loadActiveView() {
  resetFeedback()
  viewsState.loading = true
  viewResult.columns = []
  viewResult.rows = []
  viewResult.rowCount = null
  viewResult.error = ''
  viewResult.message = ''
  try {
    const { data } = await getPerformancePreview(activeView.value)
    viewResult.columns = data.columns || []
    viewResult.rows = data.rows || []
    viewResult.rowCount = data.row_count ?? 0
    viewResult.message = `已通过统计接口载入 ${data.label}。`
  } catch (err) {
    try {
      const data = await runSql(activeViewSql.value)
      if (data.type === 'result') {
        viewResult.columns = data.columns
        viewResult.rows = data.rows
        viewResult.rowCount = data.row_count
        viewResult.message = '已通过 SQL 查询回退载入视图结果。'
      } else {
        viewResult.message = data.message
        viewResult.rowCount = data.row_count
      }
    } catch (fallbackErr) {
      viewResult.error = fallbackErr.response?.data?.detail || err.response?.data?.detail || fallbackErr.message || err.message || '加载视图数据失败'
    }
  } finally {
    viewsState.loading = false
  }
}

async function runFullDemo() {
  resetFeedback()
  fullDemoLoading.value = true
  try {
    await handleImportBenchmark()
    if (globalError.value) return
    await loadBenchmarkSummary({ silent: true })
    if (globalError.value) return
    await handleSetupDemoTable()
    if (globalError.value) return
    await runBeforePlan()
    if (globalError.value) return
    await runAfterPlan()
    if (globalError.value) return
    await loadActiveView()
    if (!globalError.value) {
      globalMessage.value = '完整流程已执行完成，可以直接继续查看结果。'
    }
  } finally {
    fullDemoLoading.value = false
  }
}

async function loadPerformanceGuide() {
  try {
    const { data } = await getPerformanceGuide()
    if (data?.demo_project_id) {
      performanceGuide.demoProjectId = data.demo_project_id
    }
    if (data?.index_demo?.demo_table) {
      performanceGuide.demoTable = data.index_demo.demo_table
    }
    if (data?.index_demo?.index_name) {
      performanceGuide.demoIndex = data.index_demo.index_name
    }
    if (data?.view_scenarios?.projectStats) {
      performanceGuide.viewScenarios.projectStats = {
        label: data.view_scenarios.projectStats.label,
        viewSql: data.view_scenarios.projectStats.view_sql,
        directSql: data.view_scenarios.projectStats.direct_sql,
        pitch: data.view_scenarios.projectStats.pitch,
      }
    }
    if (data?.view_scenarios?.requirementDetails) {
      performanceGuide.viewScenarios.requirementDetails = {
        label: data.view_scenarios.requirementDetails.label,
        viewSql: data.view_scenarios.requirementDetails.view_sql,
        directSql: data.view_scenarios.requirementDetails.direct_sql,
        pitch: data.view_scenarios.requirementDetails.pitch,
      }
    }
  } catch {
    // Keep local fallback content so the page still shows the teaching script.
  }
}

onMounted(() => {
  loadPerformanceGuide()
})

watch(
  () => props.connection?.database,
  (databaseName) => {
    if (databaseName) {
      loadBenchmarkSummary({ silent: true })
      return
    }
    resetBenchmarkState()
  },
  { immediate: true },
)
</script>

<style scoped>
.perf-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  overflow-y: auto;
  padding-right: 8px;
}

.perf-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.9fr);
  gap: 18px;
  align-items: stretch;
}

.perf-hero h1 {
  margin: 8px 0 10px;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.05;
}

.perf-copy {
  margin: 0;
  max-width: 680px;
  color: rgba(28, 40, 52, 0.7);
  line-height: 1.7;
}

.perf-meta {
  display: grid;
  gap: 12px;
}

.meta-item {
  border: 1px solid rgba(28, 40, 52, 0.12);
  background:
    linear-gradient(135deg, rgba(213, 183, 131, 0.2), rgba(255, 255, 255, 0.92)),
    repeating-linear-gradient(90deg, rgba(28, 40, 52, 0.02) 0 1px, transparent 1px 18px);
  padding: 14px 16px;
}

.meta-item span {
  display: block;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(28, 40, 52, 0.45);
  margin-bottom: 8px;
}

.meta-item strong {
  font-size: 15px;
  color: var(--ink-900);
  word-break: break-all;
}

.perf-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.perf-grid.plans {
  align-items: stretch;
}

.perf-card {
  padding: 20px;
}

.perf-steps {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.perf-steps button {
  min-height: 44px;
}

.perf-notes {
  display: grid;
  gap: 12px;
}

.benchmark-status {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid rgba(28, 40, 52, 0.08);
}

.benchmark-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  margin-bottom: 12px;
  color: rgba(28, 40, 52, 0.68);
  font-size: 13px;
}

.benchmark-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.benchmark-item {
  display: grid;
  gap: 4px;
  padding: 12px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background: rgba(255, 248, 238, 0.78);
}

.benchmark-item span {
  font-size: 12px;
  color: rgba(28, 40, 52, 0.5);
}

.benchmark-item strong {
  font-size: 18px;
  color: var(--ink-900);
}

.note-item {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 12px 0;
  border-top: 1px solid rgba(28, 40, 52, 0.08);
}

.note-item:first-child {
  border-top: none;
}

.note-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid rgba(28, 40, 52, 0.18);
  background: rgba(214, 188, 149, 0.25);
  color: var(--ink-900);
  font-family: var(--font-mono);
  font-size: 12px;
}

.note-item strong {
  display: block;
  margin-bottom: 4px;
  font-size: 13px;
}

.note-item p {
  margin: 0;
  color: rgba(28, 40, 52, 0.62);
  line-height: 1.6;
  font-size: 13px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.summary-panel {
  border: 1px solid rgba(28, 40, 52, 0.1);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(245, 239, 230, 0.85));
  padding: 16px;
  min-height: 150px;
}

.summary-panel.accent {
  background:
    linear-gradient(180deg, rgba(255, 248, 238, 0.96), rgba(243, 226, 199, 0.86));
}

.summary-panel.warm {
  background:
    linear-gradient(180deg, rgba(248, 242, 231, 0.98), rgba(231, 214, 183, 0.82));
}

.summary-label {
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(28, 40, 52, 0.46);
}

.summary-value {
  margin: 14px 0 10px;
  font-size: 30px;
  line-height: 1;
  color: var(--ink-900);
}

.summary-value small {
  font-size: 13px;
}

.summary-copy {
  color: rgba(28, 40, 52, 0.66);
  font-size: 13px;
  line-height: 1.5;
  word-break: break-word;
}

.shortcut-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.shortcut-link {
  text-decoration: none;
}

.plan-output {
  margin: 0;
  min-height: 320px;
  max-height: 440px;
  overflow: auto;
  padding: 16px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(246, 240, 230, 0.95));
  border: 1px solid rgba(28, 40, 52, 0.08);
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.perf-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.view-copy {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
  color: rgba(28, 40, 52, 0.68);
  font-size: 13px;
}

.view-copy code {
  display: block;
  padding: 10px 12px;
  background: rgba(255, 248, 238, 0.9);
  border: 1px solid rgba(28, 40, 52, 0.08);
  font-family: var(--font-mono);
  white-space: pre-wrap;
}

.view-result {
  min-height: 340px;
  overflow: hidden;
  border: 1px solid rgba(28, 40, 52, 0.08);
}

.sql-compare-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.sql-compare-panel {
  display: grid;
  gap: 8px;
}

.sql-compare-title,
.demo-script-title {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(28, 40, 52, 0.5);
}

.sql-compare-panel code {
  display: block;
  min-height: 176px;
  padding: 12px;
  background: rgba(255, 248, 238, 0.9);
  border: 1px solid rgba(28, 40, 52, 0.08);
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.demo-script {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
  padding: 14px 16px;
  background: linear-gradient(180deg, rgba(248, 242, 231, 0.96), rgba(255, 255, 255, 0.92));
  border: 1px solid rgba(28, 40, 52, 0.08);
}

.demo-script p {
  margin: 0;
  color: rgba(28, 40, 52, 0.7);
  line-height: 1.6;
  font-size: 13px;
}

.perf-error,
.perf-message {
  padding: 12px 16px;
  font-size: 13px;
  border: 1px solid;
}

.perf-error {
  color: var(--signal);
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.22);
}

.perf-message {
  color: var(--ink-900);
  background: rgba(213, 183, 131, 0.18);
  border-color: rgba(213, 183, 131, 0.34);
}

@media (max-width: 1180px) {
  .perf-hero,
  .perf-grid,
  .summary-grid,
  .sql-compare-grid,
  .benchmark-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .perf-steps {
    grid-template-columns: 1fr;
  }

  .perf-card {
    padding: 16px;
  }

  .plan-output {
    min-height: 240px;
  }
}
</style>
