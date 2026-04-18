<template>
  <div class="complex-page">
    <section class="card wide complex-hero">
      <div class="hero-copy">
        <div class="eyebrow">public.complex_queries</div>
        <h1>复杂查询控制台</h1>
        <p>
          把课程实验里的 3 个复杂查询统一接入到一个页面，面向项目经理和验收演示场景，
          直接查看需求关联、项目进度和里程碑交付风险。
        </p>
      </div>

      <div class="hero-side">
        <div class="hero-meta">
          <span>当前项目</span>
          <strong>{{ selectedProjectLabel }}</strong>
        </div>
        <div class="hero-meta">
          <span>当前数据库</span>
          <strong>{{ connection?.database || '未连接' }}</strong>
        </div>
        <div class="hero-actions">
          <select v-model="selectedProjectId" class="hero-select" :disabled="projectsLoading || busy">
            <option value="">请选择项目</option>
            <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
              {{ project.name }} · {{ project.project_id }}
            </option>
          </select>
          <button class="ghost" :disabled="projectsLoading || busy" @click="loadProjects">
            {{ projectsLoading ? '刷新中...' : '刷新项目列表' }}
          </button>
          <button class="primary" :disabled="!selectedProjectId || busy" @click="runAllQueries">
            {{ busy ? '执行中...' : '一键执行三项查询' }}
          </button>
        </div>
      </div>
    </section>

    <div v-if="pageError" class="page-error">{{ pageError }}</div>

    <section class="complex-ribbon">
      <article class="card ribbon-card">
        <div class="ribbon-head">
          <span class="ribbon-index">01</span>
          <h3>需求关联</h3>
        </div>
        <p>连接需求、项目、测试用例和缺陷，展示一条需求的完整验证与缺陷闭环。</p>
        <div class="query-chip-row">
          <span class="query-chip">5表关联</span>
          <span class="query-chip">分组聚合</span>
          <span class="query-chip">JSONB 聚合</span>
        </div>
        <button class="ghost" :disabled="!selectedProjectId || traceState.loading" @click="loadRequirementTrace">
          {{ traceState.loading ? '查询中...' : '执行需求关联查询' }}
        </button>
      </article>

      <article class="card ribbon-card">
        <div class="ribbon-head">
          <span class="ribbon-index">02</span>
          <h3>项目进度</h3>
        </div>
        <p>基于多层 CTE 聚合需求状态、缺陷、覆盖率和里程碑，输出项目整体进展。</p>
        <div class="query-chip-row">
          <span class="query-chip">多层 CTE</span>
          <span class="query-chip">条件聚合</span>
          <span class="query-chip">项目级汇总</span>
        </div>
        <button class="ghost" :disabled="!selectedProjectId || progressState.loading" @click="loadProjectProgress">
          {{ progressState.loading ? '查询中...' : '执行项目进度' }}
        </button>
      </article>

      <article class="card ribbon-card">
        <div class="ribbon-head">
          <span class="ribbon-index">03</span>
          <h3>里程碑风险</h3>
        </div>
        <p>联动里程碑、需求、测试、缺陷、分支与变更集，识别发布前最危险的交付点。</p>
        <div class="query-chip-row">
          <span class="query-chip">9表分析</span>
          <span class="query-chip">多层嵌套</span>
          <span class="query-chip">风险评分</span>
        </div>
        <button class="ghost" :disabled="!selectedProjectId || riskState.loading" @click="loadMilestoneRisk">
          {{ riskState.loading ? '查询中...' : '执行风险分析' }}
        </button>
      </article>
    </section>

    <section class="card wide progress-panel">
      <div class="card-header">
        <div>
          <h4 class="card-kicker">项目进度复杂查询</h4>
          <div class="panel-sql">`SELECT * FROM fn_project_progress(project_id)`</div>
        </div>
        <span class="eyebrow">{{ progressMetaText }}</span>
      </div>

      <div v-if="progressState.error" class="panel-error">{{ progressState.error }}</div>
      <div v-else-if="progressState.loading" class="panel-placeholder">正在计算项目进度...</div>
      <div v-else-if="progressState.data" class="progress-body">
        <div class="query-annotation">
          <div class="annotation-block">
            <span class="annotation-label">涉及表</span>
            <div class="annotation-value">{{ queryGlossary.progress.tables }}</div>
          </div>
          <div class="annotation-block">
            <span class="annotation-label">查询方式</span>
            <div class="annotation-value">{{ queryGlossary.progress.methods }}</div>
          </div>
        </div>
        <div class="summary-grid">
          <article class="summary-panel">
            <div class="summary-label">需求完成率</div>
            <div class="summary-value">{{ progressState.data.completion_rate_percent ?? 0 }}%</div>
            <div class="summary-copy">
              已完成 {{ progressState.data.completed_requirements || 0 }} / {{ progressState.data.total_requirements || 0 }}
            </div>
          </article>
          <article class="summary-panel accent">
            <div class="summary-label">测试覆盖率</div>
            <div class="summary-value">{{ progressState.data.test_coverage_rate_percent ?? 0 }}%</div>
            <div class="summary-copy">
              已覆盖 {{ progressState.data.covered_requirements || 0 }} / {{ progressState.data.total_requirements_for_coverage || 0 }}
            </div>
          </article>
          <article class="summary-panel warm">
            <div class="summary-label">风险缺陷</div>
            <div class="summary-value">{{ progressState.data.open_defects || 0 }}</div>
            <div class="summary-copy">
              其中严重缺陷 {{ progressState.data.critical_defects || 0 }} 个
            </div>
          </article>
        </div>

        <div class="metric-grid">
          <div class="metric-item">
            <span>项目状态</span>
            <strong>{{ progressState.data.project_status }}</strong>
          </div>
          <div class="metric-item">
            <span>进行中需求</span>
            <strong>{{ progressState.data.in_progress_requirements || 0 }}</strong>
          </div>
          <div class="metric-item">
            <span>草稿需求</span>
            <strong>{{ progressState.data.draft_requirements || 0 }}</strong>
          </div>
          <div class="metric-item">
            <span>里程碑数</span>
            <strong>{{ progressState.data.total_milestones || 0 }}</strong>
          </div>
          <div class="metric-item">
            <span>基线数</span>
            <strong>{{ progressState.data.baseline_count || 0 }}</strong>
          </div>
          <div class="metric-item">
            <span>缺陷总数</span>
            <strong>{{ progressState.data.total_defects || 0 }}</strong>
          </div>
        </div>
      </div>
      <div v-else class="panel-placeholder">选择项目后执行查询，查看聚合后的项目进度面板。</div>
    </section>

    <section class="card wide trace-panel">
      <div class="card-header">
        <div>
          <h4 class="card-kicker">需求关联复杂查询</h4>
          <div class="panel-sql">`SELECT * FROM fn_requirement_trace(project_id)`</div>
        </div>
        <span class="eyebrow">{{ traceMetaText }}</span>
      </div>

      <div class="trace-highlight-row">
        <article class="highlight-card">
          <span>需求条数</span>
          <strong>{{ traceState.rows.length }}</strong>
        </article>
        <article class="highlight-card">
          <span>关联测试用例</span>
          <strong>{{ totalTraceTestCases }}</strong>
        </article>
        <article class="highlight-card">
          <span>开放缺陷</span>
          <strong>{{ totalTraceOpenDefects }}</strong>
        </article>
      </div>

      <div class="query-annotation">
        <div class="annotation-block">
          <span class="annotation-label">涉及表</span>
          <div class="annotation-value">{{ queryGlossary.trace.tables }}</div>
        </div>
        <div class="annotation-block">
          <span class="annotation-label">查询方式</span>
          <div class="annotation-value">{{ queryGlossary.trace.methods }}</div>
        </div>
      </div>

      <div class="result-shell">
        <ResultTable
          title="需求关联结果"
          :columns="traceState.columns"
          :rows="traceState.rows"
          :row-count="traceState.rowCount"
          :error="traceState.error"
          :message="traceState.message"
        />
      </div>
    </section>

    <section class="card wide risk-panel">
      <div class="card-header">
        <div>
          <h4 class="card-kicker">里程碑交付风险复杂查询</h4>
          <div class="panel-sql">`SELECT * FROM fn_milestone_delivery_risk(project_id)`</div>
        </div>
        <span class="eyebrow">{{ riskMetaText }}</span>
      </div>

      <div class="risk-overview">
        <article class="risk-badge high">
          <span>高风险里程碑</span>
          <strong>{{ highRiskCount }}</strong>
        </article>
        <article class="risk-badge medium">
          <span>中风险里程碑</span>
          <strong>{{ mediumRiskCount }}</strong>
        </article>
        <article class="risk-badge low">
          <span>低风险里程碑</span>
          <strong>{{ lowRiskCount }}</strong>
        </article>
      </div>

      <div class="query-annotation">
        <div class="annotation-block">
          <span class="annotation-label">涉及表</span>
          <div class="annotation-value">{{ queryGlossary.risk.tables }}</div>
        </div>
        <div class="annotation-block">
          <span class="annotation-label">查询方式</span>
          <div class="annotation-value">{{ queryGlossary.risk.methods }}</div>
        </div>
      </div>

      <div class="result-shell">
        <ResultTable
          title="里程碑风险结果"
          :columns="riskState.columns"
          :rows="riskState.rows"
          :row-count="riskState.rowCount"
          :error="riskState.error"
          :message="riskState.message"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import ResultTable from '../components/ResultTable.vue'
import {
  getMilestoneRisk,
  getProjectProgress,
  getRequirementTrace,
  listProjects,
} from '../api'

const props = defineProps({
  connection: { type: Object, default: null },
})

const projects = ref([])
const projectsLoading = ref(false)
const selectedProjectId = ref('')
const pageError = ref('')

const traceState = ref(makeTableState('执行需求关联查询后，这里显示需求、测试与缺陷的关联结果。'))
const riskState = ref(makeTableState('执行风险分析后，这里显示里程碑级别的风险排序。'))
const progressState = ref({
  loading: false,
  error: '',
  data: null,
  updatedAt: '',
})

const queryGlossary = {
  trace: {
    tables: 'manage_requirements、manage_projects、manage_requirement_test_links、manage_test_cases、manage_defects',
    methods: '多表连接查询 + 按需求分组聚合 + JSONB 聚合。之所以属于复杂查询，是因为它同时连接了 5 张业务表，并在关联结果上做聚合统计与结构化汇总。',
  },
  progress: {
    tables: 'manage_projects、manage_requirements、manage_defects、manage_requirement_test_links、manage_milestones',
    methods: '多层 CTE 嵌套查询 + GROUP BY 分组统计 + 条件聚合。之所以属于复杂查询，是因为它不是单次查询，而是先分层统计需求、缺陷、覆盖率、里程碑，再汇总成项目级结果。',
  },
  risk: {
    tables: 'manage_milestones、manage_milestone_nodes、manage_requirements、manage_requirement_test_links、manage_test_cases、manage_requirement_links、manage_defects、manage_branches、manage_change_sets',
    methods: '多表关联查询 + 多层 CTE 嵌套分析 + 条件聚合与风险评分。之所以属于复杂查询，是因为它连接了 9 张表，并通过多层中间结果逐步计算需求、测试、缺陷和分支带来的交付风险。',
  },
}

const busy = computed(() => (
  projectsLoading.value || traceState.value.loading || progressState.value.loading || riskState.value.loading
))

const selectedProjectLabel = computed(() => {
  const project = projects.value.find((item) => item.project_id === selectedProjectId.value)
  return project ? `${project.name} · ${project.project_id}` : '未选择项目'
})

const totalTraceTestCases = computed(() => (
  traceState.value.rows.reduce((sum, row) => sum + Number(row.test_case_count || 0), 0)
))

const totalTraceOpenDefects = computed(() => (
  traceState.value.rows.reduce((sum, row) => sum + Number(row.open_defect_count || 0), 0)
))

const highRiskCount = computed(() => (
  riskState.value.rows.filter((row) => row.risk_level === 'high').length
))

const mediumRiskCount = computed(() => (
  riskState.value.rows.filter((row) => row.risk_level === 'medium').length
))

const lowRiskCount = computed(() => (
  riskState.value.rows.filter((row) => row.risk_level === 'low').length
))

const traceMetaText = computed(() => (
  traceState.value.updatedAt ? `最近更新 ${traceState.value.updatedAt}` : '按需求维度展开'
))

const riskMetaText = computed(() => (
  riskState.value.updatedAt ? `最近更新 ${riskState.value.updatedAt}` : '按里程碑风险排序'
))

const progressMetaText = computed(() => (
  progressState.value.updatedAt ? `最近更新 ${progressState.value.updatedAt}` : '多层 CTE 聚合结果'
))

onMounted(async () => {
  await loadProjects()
})

watch(selectedProjectId, async (projectId, previousId) => {
  if (!projectId || projectId === previousId) {
    return
  }
  await runAllQueries()
})

async function loadProjects() {
  projectsLoading.value = true
  pageError.value = ''
  try {
    const { data } = await listProjects()
    projects.value = data.items || []

    if (!selectedProjectId.value) {
      const preferred = projects.value.find((item) => item.project_id === 'demo_proj_checkout')
      selectedProjectId.value = preferred?.project_id || projects.value[0]?.project_id || ''
    }
  } catch (error) {
    pageError.value = error.response?.data?.detail || '项目列表加载失败'
  } finally {
    projectsLoading.value = false
  }
}

async function runAllQueries() {
  if (!selectedProjectId.value) {
    return
  }
  await Promise.all([
    loadRequirementTrace(),
    loadProjectProgress(),
    loadMilestoneRisk(),
  ])
}

async function loadRequirementTrace() {
  if (!selectedProjectId.value) {
    return
  }

  traceState.value.loading = true
  traceState.value.error = ''
  traceState.value.message = ''

  try {
    const { data } = await getRequirementTrace(selectedProjectId.value)
    traceState.value.columns = data.items?.length ? Object.keys(data.items[0]) : []
    traceState.value.rows = data.items || []
    traceState.value.rowCount = data.total ?? (data.items?.length || 0)
    traceState.value.message = data.items?.length ? '' : '该项目当前没有可展示的需求关联数据。'
    traceState.value.updatedAt = formatNow()
  } catch (error) {
    traceState.value.error = error.response?.data?.detail || '需求关联查询失败'
  } finally {
    traceState.value.loading = false
  }
}

async function loadProjectProgress() {
  if (!selectedProjectId.value) {
    return
  }

  progressState.value.loading = true
  progressState.value.error = ''

  try {
    const { data } = await getProjectProgress(selectedProjectId.value)
    progressState.value.data = data
    progressState.value.updatedAt = formatNow()
  } catch (error) {
    progressState.value.error = error.response?.data?.detail || '项目进度查询失败'
    progressState.value.data = null
  } finally {
    progressState.value.loading = false
  }
}

async function loadMilestoneRisk() {
  if (!selectedProjectId.value) {
    return
  }

  riskState.value.loading = true
  riskState.value.error = ''
  riskState.value.message = ''

  try {
    const { data } = await getMilestoneRisk(selectedProjectId.value)
    riskState.value.columns = data.items?.length ? Object.keys(data.items[0]) : []
    riskState.value.rows = data.items || []
    riskState.value.rowCount = data.total ?? (data.items?.length || 0)
    riskState.value.message = data.items?.length ? '' : '该项目当前没有里程碑风险数据。'
    riskState.value.updatedAt = formatNow()
  } catch (error) {
    riskState.value.error = error.response?.data?.detail || '里程碑风险查询失败'
  } finally {
    riskState.value.loading = false
  }
}

function makeTableState(message) {
  return {
    loading: false,
    columns: [],
    rows: [],
    rowCount: null,
    error: '',
    message,
    updatedAt: '',
  }
}

function formatNow() {
  return new Date().toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.complex-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
}

.complex-hero {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 18px;
  padding: 22px 24px;
  background:
    linear-gradient(135deg, rgba(255, 248, 238, 0.96), rgba(245, 237, 221, 0.88)),
    linear-gradient(90deg, rgba(201, 100, 66, 0.05), transparent);
}

.hero-copy h1 {
  margin: 6px 0 10px;
  font-family: "Noto Serif SC", Georgia, serif;
  font-size: 28px;
  font-weight: 600;
  color: var(--near-black);
}

.hero-copy p {
  margin: 0;
  max-width: 720px;
  color: rgba(28, 40, 52, 0.72);
  line-height: 1.75;
  font-size: 14px;
}

.hero-side {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background: rgba(255, 255, 255, 0.72);
}

.hero-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: rgba(28, 40, 52, 0.6);
}

.hero-meta strong {
  color: var(--near-black);
  font-family: var(--font-mono);
  font-size: 12px;
  text-align: right;
}

.hero-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 4px;
}

.hero-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(28, 40, 52, 0.16);
  background: rgba(255, 255, 255, 0.94);
  color: var(--near-black);
  font-size: 13px;
}

.page-error,
.panel-error {
  padding: 12px 16px;
  border: 1px solid rgba(239, 68, 68, 0.26);
  background: rgba(239, 68, 68, 0.08);
  color: var(--signal);
  font-size: 13px;
}

.complex-ribbon {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.ribbon-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 174px;
}

.ribbon-card p {
  margin: 0;
  color: rgba(28, 40, 52, 0.68);
  line-height: 1.65;
  font-size: 13px;
  flex: 1;
}

.query-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.query-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 9px;
  border: 1px solid rgba(201, 100, 66, 0.18);
  background: rgba(255, 248, 238, 0.84);
  color: rgba(28, 40, 52, 0.72);
  font-size: 11px;
  letter-spacing: 0.4px;
}

.ribbon-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ribbon-head h3 {
  margin: 0;
  font-size: 16px;
  color: var(--near-black);
}

.ribbon-index {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(201, 100, 66, 0.22);
  background: rgba(201, 100, 66, 0.09);
  color: var(--accent);
  font-family: var(--font-mono);
  font-size: 12px;
}

.panel-sql {
  margin-top: 6px;
  color: rgba(28, 40, 52, 0.58);
  font-size: 12px;
  font-family: var(--font-mono);
}

.panel-placeholder {
  padding: 32px 16px;
  text-align: center;
  color: rgba(28, 40, 52, 0.44);
  font-size: 14px;
}

.query-annotation {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.annotation-block {
  padding: 14px 16px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background: rgba(255, 255, 255, 0.72);
}

.annotation-label {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: rgba(28, 40, 52, 0.5);
}

.annotation-value {
  color: rgba(28, 40, 52, 0.72);
  font-size: 13px;
  line-height: 1.7;
}

.progress-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.summary-panel {
  padding: 18px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background: rgba(255, 255, 255, 0.72);
}

.summary-panel.accent {
  background: rgba(201, 100, 66, 0.08);
}

.summary-panel.warm {
  background: rgba(212, 178, 116, 0.14);
}

.summary-label {
  font-size: 11px;
  color: rgba(28, 40, 52, 0.52);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.summary-value {
  margin-top: 10px;
  font-size: 30px;
  line-height: 1;
  color: var(--near-black);
  font-family: "Noto Serif SC", Georgia, serif;
}

.summary-copy {
  margin-top: 10px;
  color: rgba(28, 40, 52, 0.66);
  font-size: 13px;
  line-height: 1.6;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 12px;
  border-top: 2px solid rgba(201, 100, 66, 0.16);
  background: rgba(255, 248, 238, 0.72);
}

.metric-item span {
  font-size: 11px;
  color: rgba(28, 40, 52, 0.54);
  text-transform: uppercase;
}

.metric-item strong {
  font-size: 20px;
  color: var(--near-black);
}

.trace-highlight-row,
.risk-overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.highlight-card,
.risk-badge {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  border-left: 3px solid rgba(201, 100, 66, 0.3);
  background: rgba(255, 250, 244, 0.78);
}

.highlight-card span,
.risk-badge span {
  font-size: 12px;
  color: rgba(28, 40, 52, 0.56);
}

.highlight-card strong,
.risk-badge strong {
  font-size: 24px;
  color: var(--near-black);
}

.risk-badge.high {
  background: rgba(239, 68, 68, 0.08);
  border-left-color: rgba(239, 68, 68, 0.38);
}

.risk-badge.medium {
  background: rgba(245, 158, 11, 0.12);
  border-left-color: rgba(245, 158, 11, 0.42);
}

.risk-badge.low {
  background: rgba(16, 185, 129, 0.08);
  border-left-color: rgba(16, 185, 129, 0.34);
}

.result-shell {
  min-height: 320px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background: rgba(255, 255, 255, 0.82);
}

@media (max-width: 1200px) {
  .complex-hero,
  .complex-ribbon,
  .summary-grid,
  .metric-grid,
  .query-annotation,
  .trace-highlight-row,
  .risk-overview {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 820px) {
  .complex-hero,
  .complex-ribbon,
  .summary-grid,
  .metric-grid,
  .query-annotation,
  .trace-highlight-row,
  .risk-overview {
    grid-template-columns: 1fr;
  }

  .hero-copy h1 {
    font-size: 24px;
  }
}
</style>
