<template>
  <div class="view-lab-page">
    <section class="card wide view-lab-hero">
      <div class="hero-copy">
        <div class="eyebrow">public.view_comparison_lab</div>
        <h1>视图对照台</h1>
        <p>
          这个页面专门对比“直接读取视图”和“页面自己拼完整 SQL”两种做法。
          默认使用首页“引入演示数据”按钮导入的 `demo_*` 数据，让视图价值看得更直观。
        </p>

        <div class="hero-tags">
          <span class="hero-tag">首页演示数据</span>
          <span class="hero-tag">视图 vs 直接 SQL</span>
          <span class="hero-tag">结果一致性验证</span>
        </div>
      </div>

      <div class="hero-console">
        <div class="console-row">
          <span>当前数据库</span>
          <strong>{{ connection?.database || '未连接' }}</strong>
        </div>
        <div class="console-row">
          <span>演示项目</span>
          <strong>{{ selectedProjectLabel }}</strong>
        </div>
        <div class="console-row">
          <span>数据状态</span>
          <strong>{{ hasDemoProjects ? '已检测到 demo 数据' : '尚未检测到 demo 数据' }}</strong>
        </div>

        <div class="hero-actions">
          <button class="btn-warm-sand" :disabled="busy || !connection" @click="handleImportDemo">
            {{ importLoading ? '引入中...' : '引入首页测试数据' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="handleRefresh">
            {{ refreshLoading ? '刷新中...' : '刷新项目与结果' }}
          </button>
          <button class="ghost danger" :disabled="busy || !connection" @click="handleDeleteDemo">
            {{ deleteLoading ? '删除中...' : '删除首页测试数据' }}
          </button>
        </div>
      </div>
    </section>

    <div v-if="pageError" class="page-error">{{ pageError }}</div>
    <div v-if="pageMessage" class="page-message">{{ pageMessage }}</div>

    <section class="card wide control-card">
      <div class="card-header">
        <div>
          <h4 class="card-kicker">对照控制</h4>
          <div class="panel-subtitle">选一个首页演示项目，再切换你想说明的视图场景。</div>
        </div>
      </div>

      <div class="control-grid">
        <label class="control-block">
          <span>演示项目</span>
          <select v-model="selectedProjectId" class="hero-select" :disabled="busy || !connection">
            <option value="">请选择项目</option>
            <option v-for="project in demoProjects" :key="project.project_id" :value="project.project_id">
              {{ project.name }} · {{ project.project_id }}
            </option>
          </select>
        </label>

        <div class="control-block">
          <span>对照场景</span>
          <div class="scenario-tabs">
            <button
              v-for="scenario in scenarioList"
              :key="scenario.key"
              class="scenario-tab"
              :class="{ active: selectedScenarioKey === scenario.key }"
              :disabled="busy || !connection"
              @click="selectedScenarioKey = scenario.key"
            >
              {{ scenario.label }}
            </button>
          </div>
        </div>

        <div class="control-block action-block">
          <span>执行</span>
          <button class="primary" :disabled="!selectedProjectId || busy || !connection" @click="runComparison">
            {{ comparisonLoading ? '对照中...' : '运行视图对照' }}
          </button>
        </div>
      </div>

      <div class="scenario-notes">
        <article class="note-card">
          <div class="note-label">当前场景</div>
          <h3>{{ activeScenario.label }}</h3>
          <p>{{ activeScenario.description }}</p>
        </article>
        <article class="note-card accent">
          <div class="note-label">用视图</div>
          <p>{{ activeScenario.viewPitch }}</p>
        </article>
        <article class="note-card warm">
          <div class="note-label">不用视图</div>
          <p>{{ activeScenario.directPitch }}</p>
        </article>
      </div>
    </section>

    <section v-if="!hasDemoProjects" class="card wide empty-demo-card">
      <div class="empty-state">
        还没有检测到 `demo_proj_*` 项目。先在首页点“引入演示数据”，或者直接在本页点“引入首页测试数据”。
      </div>
    </section>

    <section class="comparison-ribbon">
      <article class="card ribbon-card">
        <div class="ribbon-label">视图 SQL</div>
        <strong>{{ viewSqlLineCount }} 行</strong>
        <p>页面直接查询数据库里已经定义好的视图对象。</p>
      </article>

      <article class="card ribbon-card accent">
        <div class="ribbon-label">直接 SQL</div>
        <strong>{{ directSqlLineCount }} 行</strong>
        <p>不使用视图时，页面自己拼接完整聚合逻辑。</p>
      </article>

      <article class="card ribbon-card warm">
        <div class="ribbon-label">对照结论</div>
        <strong>{{ comparisonBadge }}</strong>
        <p>{{ comparisonSummary }}</p>
      </article>
    </section>

    <section class="sql-contrast-grid">
      <article class="card sql-card">
        <div class="card-header">
          <div>
            <h4 class="card-kicker">使用视图</h4>
            <div class="panel-subtitle">页面只需要读取视图，SQL 更短，复用口径更稳定。</div>
          </div>
          <span class="eyebrow">{{ activeScenario.viewName }}</span>
        </div>
        <pre class="sql-block">{{ activeViewSql }}</pre>
      </article>

      <article class="card sql-card">
        <div class="card-header">
          <div>
            <h4 class="card-kicker">不使用视图</h4>
            <div class="panel-subtitle">页面需要自己写完整 CTE / JOIN / 聚合逻辑。</div>
          </div>
          <span class="eyebrow">Direct SQL</span>
        </div>
        <pre class="sql-block">{{ activeDirectSql }}</pre>
      </article>
    </section>

    <section class="result-compare-grid">
      <article class="card result-card">
        <div class="card-header">
          <div>
            <h4 class="card-kicker">视图结果</h4>
            <div class="panel-subtitle">{{ activeScenario.resultDescription }}</div>
          </div>
          <span class="eyebrow">{{ viewResult.rowCount ?? '—' }} 行</span>
        </div>
        <div class="result-shell">
          <ResultTable
            :title="`${activeScenario.label} · 视图结果`"
            :columns="viewResult.columns"
            :rows="viewResult.rows"
            :row-count="viewResult.rowCount"
            :error="viewResult.error"
            :message="viewResult.message"
          />
        </div>
      </article>

      <article class="card result-card">
        <div class="card-header">
          <div>
            <h4 class="card-kicker">直接 SQL 结果</h4>
            <div class="panel-subtitle">和左侧结果相同，但查询逻辑完全由页面承担。</div>
          </div>
          <span class="eyebrow">{{ directResult.rowCount ?? '—' }} 行</span>
        </div>
        <div class="result-shell">
          <ResultTable
            :title="`${activeScenario.label} · 直接 SQL 结果`"
            :columns="directResult.columns"
            :rows="directResult.rows"
            :row-count="directResult.rowCount"
            :error="directResult.error"
            :message="directResult.message"
          />
        </div>
      </article>
    </section>

    <section class="card wide takeaway-card">
      <div class="card-header">
        <div>
          <h4 class="card-kicker">页面层面的区别</h4>
          <div class="panel-subtitle">这块专门用来解释为什么“有视图”和“没视图”在系统设计上不一样。</div>
        </div>
      </div>

      <div class="takeaway-grid">
        <article class="takeaway-item">
          <span>有视图时</span>
          <strong>页面读的是统一数据口径</strong>
          <p>前端只关心“拿什么字段”，不用重复维护复杂聚合逻辑。后续统计规则变动时，只需要改视图定义。</p>
        </article>
        <article class="takeaway-item">
          <span>没视图时</span>
          <strong>页面自己承担 SQL 复杂度</strong>
          <p>每个页面都可能复制一份 CTE 与 JOIN，SQL 更长、更难复用，也更容易出现不同页面统计口径不一致。</p>
        </article>
        <article class="takeaway-item">
          <span>本页验证</span>
          <strong>{{ comparisonBadge }}</strong>
          <p>{{ comparisonSummary }}</p>
        </article>
      </div>

      <div class="shortcut-row">
        <router-link class="ghost shortcut-link" to="/query">去 SQL 编辑器复跑当前 SQL</router-link>
        <router-link class="ghost shortcut-link" to="/performance-lab">去性能验证页继续看视图与索引</router-link>
        <router-link class="ghost shortcut-link" to="/test-validation">回到测试验收台</router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import ResultTable from '../components/ResultTable.vue'
import {
  deleteVisibleDemoData,
  executeQuery,
  importVisibleDemoData,
  listProjects,
} from '../api'

const props = defineProps({
  connection: { type: Object, default: null },
})

const pageError = ref('')
const pageMessage = ref('')
const importLoading = ref(false)
const deleteLoading = ref(false)
const refreshLoading = ref(false)
const comparisonLoading = ref(false)

const projects = ref([])
const selectedProjectId = ref('')
const selectedScenarioKey = ref('projectStats')

const viewResult = reactive(makeResultState('选择项目并运行对照后，这里显示视图查询结果。'))
const directResult = reactive(makeResultState('选择项目并运行对照后，这里显示直接 SQL 查询结果。'))

const scenarios = {
  projectStats: {
    key: 'projectStats',
    label: '项目统计视图',
    viewName: 'v_project_statistics',
    description: '对比项目级统计数据：需求总数、缺陷总数、完成率。',
    viewPitch: '数据库已经把项目统计封装成视图，页面只需要按项目读取结果。',
    directPitch: '如果没有视图，页面就得自己写统计需求和缺陷的聚合 SQL。',
    resultDescription: '每个项目 1 行，适合概览卡片和项目列表。',
    buildViewSql(projectId) {
      return `SELECT
  project_id,
  project_name,
  total_requirements,
  total_defects,
  completion_rate_percent
FROM v_project_statistics
WHERE project_id = '${projectId}';`
    },
    buildDirectSql(projectId) {
      return `WITH req_stats AS (
  SELECT
    project_id,
    COUNT(*) FILTER (WHERE deleted = FALSE) AS total_requirements,
    COUNT(*) FILTER (WHERE status = 'completed' AND deleted = FALSE) AS completed_count
  FROM manage_requirements
  GROUP BY project_id
),
def_stats AS (
  SELECT
    project_id,
    COUNT(*) AS total_defects
  FROM manage_defects
  GROUP BY project_id
)
SELECT
  p.project_id,
  p.name AS project_name,
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
WHERE p.project_id = '${projectId}';`
    },
  },
  requirementDetails: {
    key: 'requirementDetails',
    label: '需求详情视图',
    viewName: 'v_requirement_details',
    description: '对比需求详情结果：需求名称、所属项目、关联测试和缺陷统计。',
    viewPitch: '数据库把需求、项目、测试和缺陷的明细聚合封装到了视图里。',
    directPitch: '如果不用视图，页面需要自己关联多张表并处理计数与排序。',
    resultDescription: '每条需求 1 行，适合需求详情看板和核对结果。',
    buildViewSql(projectId) {
      return `SELECT
  req_id,
  requirement_title,
  project_name,
  test_case_count,
  defect_count,
  open_defect_count
FROM v_requirement_details
WHERE project_id = '${projectId}'
ORDER BY requirement_created_at DESC
LIMIT 8;`
    },
    buildDirectSql(projectId) {
      return `WITH test_stats AS (
  SELECT
    requirement_id,
    COUNT(DISTINCT test_case_id) AS test_case_count
  FROM manage_requirement_test_links
  GROUP BY requirement_id
),
defect_stats AS (
  SELECT
    requirement_id,
    COUNT(DISTINCT defect_id) AS defect_count,
    COUNT(DISTINCT CASE WHEN status IN ('open', 'in_progress') THEN defect_id END) AS open_defect_count
  FROM manage_defects
  GROUP BY requirement_id
)
SELECT
  r.req_id,
  r.title AS requirement_title,
  p.name AS project_name,
  COALESCE(ts.test_case_count, 0) AS test_case_count,
  COALESCE(ds.defect_count, 0) AS defect_count,
  COALESCE(ds.open_defect_count, 0) AS open_defect_count
FROM manage_requirements r
JOIN manage_projects p ON p.project_id = r.project_id
LEFT JOIN test_stats ts ON ts.requirement_id = r.req_id
LEFT JOIN defect_stats ds ON ds.requirement_id = r.req_id
WHERE r.project_id = '${projectId}' AND r.deleted = FALSE
ORDER BY r.created_at DESC
LIMIT 8;`
    },
  },
}

const activeScenario = computed(() => scenarios[selectedScenarioKey.value] || scenarios.projectStats)

const scenarioList = computed(() => Object.values(scenarios))

const demoProjects = computed(() => (
  projects.value.filter((item) => item.project_id?.startsWith('demo_proj_'))
))

const hasDemoProjects = computed(() => demoProjects.value.length > 0)

const selectedProjectLabel = computed(() => {
  const project = demoProjects.value.find((item) => item.project_id === selectedProjectId.value)
  return project ? `${project.name} · ${project.project_id}` : '未选择项目'
})

const activeViewSql = computed(() => (
  selectedProjectId.value ? activeScenario.value.buildViewSql(selectedProjectId.value) : '-- 请选择演示项目'
))

const activeDirectSql = computed(() => (
  selectedProjectId.value ? activeScenario.value.buildDirectSql(selectedProjectId.value) : '-- 请选择演示项目'
))

const viewSqlLineCount = computed(() => countSqlLines(activeViewSql.value))
const directSqlLineCount = computed(() => countSqlLines(activeDirectSql.value))

const resultsMatch = computed(() => (
  JSON.stringify({
    columns: viewResult.columns,
    rows: viewResult.rows,
  }) === JSON.stringify({
    columns: directResult.columns,
    rows: directResult.rows,
  })
))

const comparisonBadge = computed(() => {
  if (comparisonLoading.value) return '对照中'
  if (viewResult.error || directResult.error) return '执行失败'
  if (!viewResult.columns.length && !directResult.columns.length) return '等待执行'
  return resultsMatch.value ? '结果一致' : '结果不同'
})

const comparisonSummary = computed(() => {
  if (comparisonLoading.value) {
    return '正在同时执行视图查询和直接 SQL 查询。'
  }
  if (viewResult.error || directResult.error) {
    return '至少有一侧查询执行失败，请先看结果区里的错误信息。'
  }
  if (!viewResult.columns.length && !directResult.columns.length) {
    return '选择项目后运行对照，这里会给出最终结论。'
  }
  if (resultsMatch.value) {
    return `两边结果一致，但视图版只用了 ${viewSqlLineCount.value} 行 SQL，直接 SQL 需要 ${directSqlLineCount.value} 行。`
  }
  return '两边结果没有完全对齐，说明当前 SQL 口径需要继续核对。'
})

const busy = computed(() => (
  importLoading.value
  || deleteLoading.value
  || refreshLoading.value
  || comparisonLoading.value
))

onMounted(async () => {
  await loadProjects()
  if (selectedProjectId.value) {
    await runComparison()
  }
})

watch(
  () => props.connection?.database,
  async (databaseName) => {
    if (!databaseName) {
      projects.value = []
      selectedProjectId.value = ''
      resetResults()
      return
    }
    await loadProjects()
    if (selectedProjectId.value) {
      await runComparison()
    }
  },
)

watch(selectedScenarioKey, async (scenarioKey, previousKey) => {
  if (!selectedProjectId.value || scenarioKey === previousKey) {
    return
  }
  await runComparison()
})

watch(selectedProjectId, async (projectId, previousId) => {
  if (!projectId || projectId === previousId) {
    return
  }
  await runComparison()
})

async function loadProjects() {
  pageError.value = ''
  try {
    const { data } = await listProjects()
    projects.value = data.items || []
    ensureProjectSelection()
  } catch (error) {
    pageError.value = error.response?.data?.detail || '演示项目加载失败'
  }
}

function ensureProjectSelection() {
  if (selectedProjectId.value && demoProjects.value.some((item) => item.project_id === selectedProjectId.value)) {
    return
  }
  const preferred = demoProjects.value.find((item) => item.project_id === 'demo_proj_checkout') || demoProjects.value[0]
  selectedProjectId.value = preferred?.project_id || ''
}

async function runComparison() {
  if (!selectedProjectId.value) {
    return
  }

  pageError.value = ''
  pageMessage.value = ''
  comparisonLoading.value = true
  resetResults()

  try {
    const [viewResponse, directResponse] = await Promise.all([
      executeQuery(activeViewSql.value),
      executeQuery(activeDirectSql.value),
    ])

    applyQueryData(viewResponse.data, viewResult, '视图查询没有返回结果。')
    applyQueryData(directResponse.data, directResult, '直接 SQL 查询没有返回结果。')
  } catch (error) {
    pageError.value = error.response?.data?.detail || error.message || '视图对照执行失败'
  } finally {
    comparisonLoading.value = false
  }
}

async function handleImportDemo() {
  pageError.value = ''
  pageMessage.value = ''
  importLoading.value = true
  try {
    await importVisibleDemoData()
    await loadProjects()
    pageMessage.value = '首页测试数据已引入，当前页面已刷新。'
    if (selectedProjectId.value) {
      await runComparison()
    }
  } catch (error) {
    pageError.value = error.response?.data?.detail || error.message || '首页测试数据引入失败'
  } finally {
    importLoading.value = false
  }
}

async function handleDeleteDemo() {
  pageError.value = ''
  pageMessage.value = ''
  deleteLoading.value = true
  try {
    await deleteVisibleDemoData()
    await loadProjects()
    resetResults()
    pageMessage.value = '首页测试数据已删除。'
  } catch (error) {
    pageError.value = error.response?.data?.detail || error.message || '首页测试数据删除失败'
  } finally {
    deleteLoading.value = false
  }
}

async function handleRefresh() {
  pageError.value = ''
  pageMessage.value = ''
  refreshLoading.value = true
  try {
    await loadProjects()
    if (selectedProjectId.value) {
      await runComparison()
    }
    pageMessage.value = '演示项目与对照结果已刷新。'
  } catch (error) {
    pageError.value = error.response?.data?.detail || error.message || '刷新失败'
  } finally {
    refreshLoading.value = false
  }
}

function resetResults() {
  Object.assign(viewResult, makeResultState('选择项目并运行对照后，这里显示视图查询结果。'))
  Object.assign(directResult, makeResultState('选择项目并运行对照后，这里显示直接 SQL 查询结果。'))
}

function applyQueryData(payload, target, emptyMessage) {
  if (payload.type === 'result') {
    target.columns = payload.columns || []
    target.rows = payload.rows || []
    target.rowCount = payload.row_count ?? (payload.rows?.length || 0)
    target.error = ''
    target.message = target.rows.length ? '' : emptyMessage
    return
  }

  target.columns = []
  target.rows = []
  target.rowCount = payload.row_count ?? 0
  target.error = ''
  target.message = payload.message || emptyMessage
}

function makeResultState(message) {
  return {
    columns: [],
    rows: [],
    rowCount: null,
    error: '',
    message,
  }
}

function countSqlLines(sql) {
  if (!sql || sql.startsWith('--')) {
    return 0
  }
  return sql.split('\n').length
}
</script>

<style scoped>
.view-lab-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
}

.view-lab-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.92fr);
  gap: 18px;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(201, 100, 66, 0.14), transparent 36%),
    linear-gradient(135deg, rgba(255, 249, 241, 0.98), rgba(244, 236, 222, 0.9));
}

.hero-copy h1 {
  margin: 6px 0 10px;
  font-size: clamp(28px, 3.6vw, 38px);
  line-height: 1.06;
  color: var(--near-black);
}

.hero-copy p {
  margin: 0;
  max-width: 720px;
  color: rgba(28, 40, 52, 0.72);
  line-height: 1.78;
  font-size: 14px;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}

.hero-tag {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border: 1px solid rgba(201, 100, 66, 0.18);
  background: rgba(255, 255, 255, 0.72);
  font-size: 11px;
  letter-spacing: 0.08em;
  color: rgba(28, 40, 52, 0.68);
  text-transform: uppercase;
}

.hero-console {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(249, 244, 235, 0.86));
}

.console-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: rgba(28, 40, 52, 0.58);
  font-size: 12px;
}

.console-row strong {
  color: var(--near-black);
  font-size: 12px;
  font-family: var(--font-mono);
  text-align: right;
}

.hero-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin-top: 8px;
}

.danger {
  color: var(--signal);
  border-color: rgba(239, 68, 68, 0.28);
}

.page-error,
.page-message {
  padding: 12px 16px;
  font-size: 13px;
  border: 1px solid;
}

.page-error {
  color: var(--signal);
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.24);
}

.page-message {
  color: rgba(28, 40, 52, 0.88);
  background: rgba(212, 178, 116, 0.14);
  border-color: rgba(212, 178, 116, 0.3);
}

.control-card,
.takeaway-card {
  padding: 20px;
}

.panel-subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(28, 40, 52, 0.54);
}

.control-grid {
  display: grid;
  grid-template-columns: minmax(220px, 0.9fr) minmax(0, 1.5fr) 220px;
  gap: 14px;
}

.control-block {
  display: grid;
  gap: 10px;
}

.control-block span {
  font-size: 12px;
  color: rgba(28, 40, 52, 0.56);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.hero-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(28, 40, 52, 0.16);
  background: rgba(255, 255, 255, 0.94);
  color: var(--near-black);
  font-size: 13px;
}

.action-block {
  align-content: end;
}

.scenario-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scenario-tab {
  border: 1px solid rgba(28, 40, 52, 0.12);
  background: rgba(255, 255, 255, 0.72);
  color: rgba(28, 40, 52, 0.68);
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
}

.scenario-tab.active {
  background: rgba(201, 100, 66, 0.12);
  color: var(--terracotta);
  border-color: rgba(201, 100, 66, 0.32);
  box-shadow: 0 0 0 1px rgba(201, 100, 66, 0.18);
}

.scenario-notes {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.note-card {
  padding: 16px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background: rgba(255, 255, 255, 0.76);
}

.note-card.accent {
  background: rgba(201, 100, 66, 0.08);
}

.note-card.warm {
  background: rgba(212, 178, 116, 0.14);
}

.note-label {
  font-size: 11px;
  color: rgba(28, 40, 52, 0.48);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.note-card h3 {
  margin: 10px 0 8px;
  font-size: 17px;
  color: var(--near-black);
}

.note-card p {
  margin: 0;
  color: rgba(28, 40, 52, 0.68);
  font-size: 13px;
  line-height: 1.72;
}

.empty-demo-card {
  padding: 20px;
}

.comparison-ribbon {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.ribbon-card {
  display: grid;
  gap: 10px;
  min-height: 146px;
}

.ribbon-card.accent {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 245, 238, 0.92));
}

.ribbon-card.warm {
  background: linear-gradient(180deg, rgba(248, 242, 231, 0.98), rgba(255, 255, 255, 0.94));
}

.ribbon-label {
  font-size: 11px;
  color: rgba(28, 40, 52, 0.5);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.ribbon-card strong {
  font-size: 30px;
  line-height: 1;
  color: var(--near-black);
}

.ribbon-card p {
  margin: 0;
  color: rgba(28, 40, 52, 0.68);
  line-height: 1.7;
  font-size: 13px;
}

.sql-contrast-grid,
.result-compare-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.sql-card,
.result-card {
  padding: 20px;
}

.sql-block {
  margin: 0;
  min-height: 320px;
  max-height: 520px;
  overflow: auto;
  padding: 16px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.76), rgba(246, 240, 229, 0.95));
  border: 1px solid rgba(28, 40, 52, 0.08);
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.66;
  white-space: pre-wrap;
  word-break: break-word;
}

.result-shell {
  min-height: 360px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background: rgba(255, 255, 255, 0.84);
  overflow: hidden;
}

.takeaway-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.takeaway-item {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-top: 2px solid rgba(201, 100, 66, 0.18);
  background: rgba(255, 248, 238, 0.78);
}

.takeaway-item span {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(28, 40, 52, 0.5);
}

.takeaway-item strong {
  font-size: 18px;
  color: var(--near-black);
}

.takeaway-item p {
  margin: 0;
  color: rgba(28, 40, 52, 0.68);
  font-size: 13px;
  line-height: 1.72;
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

@media (max-width: 1220px) {
  .view-lab-hero,
  .control-grid,
  .scenario-notes,
  .comparison-ribbon,
  .sql-contrast-grid,
  .result-compare-grid,
  .takeaway-grid {
    grid-template-columns: 1fr;
  }
}
</style>
