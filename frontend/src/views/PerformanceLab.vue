<template>
  <div class="perf-page">
    <div class="perf-hero card wide">
      <div>
        <div class="eyebrow">public.performance_lab</div>
        <h1>索引与视图验证台</h1>
        <p class="perf-copy">
          这个页面用于演示实验要求 a：导入基准数据、构造演示表、对比索引前后执行计划，并直接查看视图查询结果。
        </p>
      </div>
      <div class="perf-meta">
        <div class="meta-item">
          <span>当前数据库</span>
          <strong>{{ connection?.database || '未连接' }}</strong>
        </div>
        <div class="meta-item">
          <span>演示项目</span>
          <strong>{{ demoProjectId }}</strong>
        </div>
        <div class="meta-item">
          <span>演示表</span>
          <strong>{{ demoTable }}</strong>
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
          <button class="ghost" :disabled="busy || !connection" @click="handleSetupDemoTable">
            {{ setupState.loading ? '初始化中...' : '2. 初始化演示表' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="runBeforePlan">
            {{ beforeState.loading ? '分析中...' : '3. 运行未建索引查询' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="runAfterPlan">
            {{ afterState.loading ? '建索引中...' : '4. 创建索引并重跑' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="loadActiveView">
            {{ viewsState.loading ? '加载中...' : '5. 载入视图结果' }}
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
              <strong>视图用途</strong>
              <p>复杂统计逻辑提前封装，前端和后端只需要直接查询视图。</p>
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
          <router-link class="ghost shortcut-link" :to="`/table/public/${demoTable}`">查看演示副本表</router-link>
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
import { computed, reactive, ref } from 'vue'
import { executeQuery, importBenchmark } from '../api'
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

const activeViewSql = computed(() => (
  activeView.value === 'projectStats'
    ? "SELECT project_id, project_name, total_requirements, total_defects, completion_rate_percent FROM v_project_statistics ORDER BY completion_rate_percent DESC LIMIT 8;"
    : `SELECT req_id, requirement_title, project_name, test_case_count, defect_count, open_defect_count FROM v_requirement_details WHERE project_id = '${demoProjectId}' ORDER BY requirement_created_at DESC LIMIT 8;`
))

const activeViewLabel = computed(() => (
  activeView.value === 'projectStats' ? 'v_project_statistics 视图结果' : 'v_requirement_details 视图结果'
))

const busy = computed(() => (
  importState.loading || setupState.loading || beforeState.loading || afterState.loading || viewsState.loading || fullDemoLoading.value
))

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
    globalMessage.value = '基准测试数据已导入，可以继续初始化演示表。'
  } catch (err) {
    globalError.value = err.response?.data?.detail || err.message || '导入测试数据失败'
  } finally {
    importState.loading = false
  }
}

async function handleSetupDemoTable() {
  resetFeedback()
  setupState.loading = true
  const t0 = performance.now()
  try {
    await runSql(`DROP TABLE IF EXISTS public.${demoTable};`)
    await runSql(`
      CREATE TABLE public.${demoTable} AS
      SELECT *
      FROM public.manage_requirements
      WHERE req_id LIKE 'breq_%';
    `)
    await runSql(`ANALYZE public.${demoTable};`)
    beforeState.summary = makeEmptySummary()
    afterState.summary = makeEmptySummary()
    beforePlanText.value = '演示表已重建。请运行“未建索引查询”生成第一份执行计划。'
    afterPlanText.value = '演示表已重建。创建索引后，这里会显示第二份执行计划。'
    setupState.elapsedLabel = `${Math.round(performance.now() - t0)} ms`
    globalMessage.value = `演示表 public.${demoTable} 已重建，当前不含自定义索引。`
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
    FROM public.${demoTable}
    WHERE project_id = '${demoProjectId}' AND deleted = FALSE
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
      CREATE INDEX IF NOT EXISTS ${demoIndex}
      ON public.${demoTable}(project_id, deleted, order_index);
    `)
    await runSql(`ANALYZE public.${demoTable};`)
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
    const data = await runSql(activeViewSql.value)
    if (data.type === 'result') {
      viewResult.columns = data.columns
      viewResult.rows = data.rows
      viewResult.rowCount = data.row_count
    } else {
      viewResult.message = data.message
      viewResult.rowCount = data.row_count
    }
  } catch (err) {
    viewResult.error = err.response?.data?.detail || err.message || '加载视图数据失败'
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
    await handleSetupDemoTable()
    if (globalError.value) return
    await runBeforePlan()
    if (globalError.value) return
    await runAfterPlan()
    if (globalError.value) return
    await loadActiveView()
    if (!globalError.value) {
      globalMessage.value = '完整演示流程已执行完成，可以直接用于课堂展示。'
    }
  } finally {
    fullDemoLoading.value = false
  }
}
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
  .summary-grid {
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
