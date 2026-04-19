<template>
  <div class="validation-page">
    <section class="card wide validation-hero">
      <div class="hero-copy">
        <div class="eyebrow">db_lab_requirements_2026_spring</div>
        <h1>测试与验收展示台</h1>
        <p>
          把课程文档里和测试相关的 4 类要求集中到一个页面：
          索引与视图效率验证、复杂查询验收、完整性约束中文提示，以及 benchmark 测试数据规模。
        </p>
      </div>

      <div class="hero-side">
        <div class="hero-meta">
          <span>当前数据库</span>
          <strong>{{ connection?.database || '未连接' }}</strong>
        </div>
        <div class="hero-meta">
          <span>演示项目</span>
          <strong>{{ selectedProjectLabel }}</strong>
        </div>
        <div class="hero-meta">
          <span>benchmark 状态</span>
          <strong>{{ benchmarkSummary.has_benchmark_data ? '已导入' : '未导入' }}</strong>
        </div>
        <div class="hero-actions">
          <button class="primary" :disabled="busy || !connection" @click="handleImportBenchmark">
            {{ importLoading ? '导入中...' : '导入 benchmark 数据' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="handleRefresh">
            {{ refreshLoading ? '刷新中...' : '刷新验收状态' }}
          </button>
          <button class="ghost" :disabled="busy || !connection" @click="handleDeleteBenchmark">
            {{ deleteLoading ? '删除中...' : '删除 benchmark 数据' }}
          </button>
        </div>
      </div>
    </section>

    <div v-if="pageMessage" class="page-message">{{ pageMessage }}</div>
    <div v-if="pageError" class="page-error">{{ pageError }}</div>

    <section class="validation-ribbon">
      <article class="card status-card">
        <div class="status-head">
          <span class="status-index">5.a</span>
          <div>
            <h3>索引与视图验证</h3>
            <p>验证索引对查询效率的提升，并展示视图与直接 SQL 的对照。</p>
          </div>
        </div>
        <div class="status-pill-row">
          <span class="status-pill" :class="performanceReady ? 'ok' : 'pending'">
            {{ performanceReady ? '可演示' : '待准备' }}
          </span>
          <span class="status-pill">{{ performanceGuide.demoProjectId || 'bproj_003' }}</span>
        </div>
        <div class="status-detail">
          <div class="detail-item">
            <span>演示表</span>
            <strong>{{ performanceGuide.demoTable || 'manage_requirements_perf_demo' }}</strong>
          </div>
          <div class="detail-item">
            <span>目标索引</span>
            <strong>{{ performanceGuide.demoIndex || 'idx_req_perf_project_deleted_order' }}</strong>
          </div>
        </div>
        <router-link to="/performance-lab" class="ghost action-link">打开性能验证页</router-link>
      </article>

      <article class="card status-card">
        <div class="status-head">
          <span class="status-index">5.b</span>
          <div>
            <h3>复杂查询验收</h3>
            <p>集中展示需求追溯、项目进度、里程碑风险三类复杂查询结果。</p>
          </div>
        </div>
        <div class="status-pill-row">
          <span class="status-pill" :class="complexQueryReady ? 'ok' : 'pending'">
            {{ complexQueryReady ? '已就绪' : '待加载' }}
          </span>
          <span class="status-pill">{{ selectedProjectId || '未选择项目' }}</span>
        </div>
        <div class="status-detail">
          <div class="detail-item">
            <span>需求追溯</span>
            <strong>{{ traceTotal }}</strong>
          </div>
          <div class="detail-item">
            <span>项目进度</span>
            <strong>{{ progressSummary }}</strong>
          </div>
          <div class="detail-item">
            <span>里程碑风险</span>
            <strong>{{ riskTotal }}</strong>
          </div>
        </div>
        <router-link to="/complex-queries" class="ghost action-link">打开复杂查询页</router-link>
      </article>

      <article class="card status-card">
        <div class="status-head">
          <span class="status-index">5.c</span>
          <div>
            <h3>中文错误提示</h3>
            <p>把唯一约束、外键、非空、检查约束和跨项目触发器错误统一演示。</p>
          </div>
        </div>
        <div class="status-pill-row">
          <span class="status-pill ok">已内置</span>
          <span class="status-pill">SQL 编辑器</span>
        </div>
        <div class="constraint-chip-row">
          <span v-for="item in constraintLabels" :key="item" class="constraint-chip">{{ item }}</span>
        </div>
        <router-link to="/query" class="ghost action-link">打开中文提示页</router-link>
      </article>

      <article class="card status-card">
        <div class="status-head">
          <span class="status-index">5.d</span>
          <div>
            <h3>测试数据规模</h3>
            <p>检查 benchmark 产品、项目、需求、测试用例、缺陷、快照与变更是否已形成完整规模。</p>
          </div>
        </div>
        <div class="status-pill-row">
          <span class="status-pill" :class="benchmarkReady ? 'ok' : 'pending'">
            {{ benchmarkReady ? '数据充分' : '数据缺失' }}
          </span>
          <span class="status-pill">{{ benchmarkSummary.total_records || 0 }} 条</span>
        </div>
        <div class="status-detail">
          <div class="detail-item">
            <span>需求</span>
            <strong>{{ benchmarkSummary.requirements || 0 }}</strong>
          </div>
          <div class="detail-item">
            <span>测试用例</span>
            <strong>{{ benchmarkSummary.test_cases || 0 }}</strong>
          </div>
          <div class="detail-item">
            <span>缺陷</span>
            <strong>{{ benchmarkSummary.defects || 0 }}</strong>
          </div>
        </div>
        <button class="ghost" :disabled="busy || !connection" @click="loadBenchmarkSummary">刷新数据摘要</button>
      </article>
    </section>

    <section class="card wide acceptance-panel">
      <div class="card-header">
        <div>
          <h4 class="card-kicker">课程要求对照</h4>
          <div class="panel-subtitle">把 `db_lab_requirements_2026_spring.md` 中针对测试的要求映射为可检查证据。</div>
        </div>
        <select v-model="selectedProjectId" class="hero-select compact" :disabled="busy || projectsLoading">
          <option value="">请选择项目</option>
          <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
            {{ project.name }} · {{ project.project_id }}
          </option>
        </select>
      </div>

      <div class="acceptance-grid">
        <article v-for="item in requirementCards" :key="item.code" class="acceptance-card">
          <div class="acceptance-top">
            <span class="acceptance-code">{{ item.code }}</span>
            <span class="acceptance-state" :class="item.stateClass">{{ item.stateLabel }}</span>
          </div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.requirement }}</p>
          <div class="evidence-label">当前证据</div>
          <div class="evidence-copy">{{ item.evidence }}</div>
          <div class="evidence-actions">
            <router-link v-for="link in item.links" :key="link.to" :to="link.to" class="ghost action-link small">
              {{ link.label }}
            </router-link>
          </div>
        </article>
      </div>
    </section>

    <section class="validation-grid">
      <article class="card data-card">
        <div class="card-header">
          <div>
            <h4 class="card-kicker">benchmark 数据摘要</h4>
            <div class="panel-subtitle">确认测试数据不是口头描述，而是已经进库。</div>
          </div>
          <span class="eyebrow">{{ benchmarkCaption }}</span>
        </div>
        <div class="metric-grid">
          <div v-for="item in benchmarkCards" :key="item.key" class="metric-item">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </article>

      <article class="card data-card">
        <div class="card-header">
          <div>
            <h4 class="card-kicker">复杂查询实时结果</h4>
            <div class="panel-subtitle">直接读取数据库函数，证明不是纯文档页。</div>
          </div>
          <span class="eyebrow">{{ selectedProjectId || '未选择项目' }}</span>
        </div>
        <div class="query-metric-grid">
          <div class="query-metric">
            <span>需求追溯条数</span>
            <strong>{{ traceTotal }}</strong>
            <small>{{ traceCoverageText }}</small>
          </div>
          <div class="query-metric">
            <span>项目完成率</span>
            <strong>{{ progressData?.completion_rate_percent ?? '—' }}<small v-if="progressData">%</small></strong>
            <small>{{ progressDefectText }}</small>
          </div>
          <div class="query-metric">
            <span>里程碑风险条数</span>
            <strong>{{ riskTotal }}</strong>
            <small>{{ riskLevelText }}</small>
          </div>
        </div>
        <div v-if="queryError" class="panel-error">{{ queryError }}</div>
      </article>
    </section>

    <section class="card wide script-panel">
      <div class="card-header">
        <div>
          <h4 class="card-kicker">课堂演示顺序</h4>
          <div class="panel-subtitle">把测试相关要求压缩成一条可直接走的演示链路。</div>
        </div>
      </div>
      <ol class="script-list">
        <li>先在本页确认 benchmark 数据已导入，证明“已生成足够测试数据”。</li>
        <li>点击“性能验证页”，展示索引前后执行计划与视图对照，完成 5.a。</li>
        <li>返回本页或进入“复杂查询页”，展示 3 类复杂查询结果，完成 5.b。</li>
        <li>打开“SQL 编辑器”，依次点唯一约束、外键、非空、检查约束、层级规则、跨项目关联，完成 5.c。</li>
        <li>最后回到本页，用课程要求对照卡说明 5.a~5.d 已有页面、SQL、数据和结果支撑。</li>
      </ol>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  deleteBenchmark,
  getBenchmarkSummary,
  getMilestoneRisk,
  getPerformanceGuide,
  getProjectProgress,
  getRequirementTrace,
  importBenchmark,
  listProjects,
} from '../api'

const props = defineProps({
  connection: { type: Object, default: null },
})

const projects = ref([])
const projectsLoading = ref(false)
const selectedProjectId = ref('')

const importLoading = ref(false)
const refreshLoading = ref(false)
const deleteLoading = ref(false)

const pageError = ref('')
const pageMessage = ref('')
const queryError = ref('')

const traceTotal = ref(0)
const riskTotal = ref(0)
const progressData = ref(null)

const performanceGuide = ref({
  demoProjectId: 'bproj_003',
  demoTable: 'manage_requirements_perf_demo',
  demoIndex: 'idx_req_perf_project_deleted_order',
})

const benchmarkSummary = ref({
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

const constraintLabels = [
  '唯一约束',
  '外键无效',
  '非空为空',
  '检查约束',
  '层级规则',
  '跨项目关联',
]

const busy = computed(() => (
  importLoading.value
  || refreshLoading.value
  || deleteLoading.value
  || projectsLoading.value
))

const benchmarkReady = computed(() => (
  benchmarkSummary.value.has_benchmark_data
  && benchmarkSummary.value.requirements >= 10000
  && benchmarkSummary.value.test_cases >= 500
  && benchmarkSummary.value.defects >= 500
))

const performanceReady = computed(() => (
  Boolean(performanceGuide.value.demoProjectId)
  && benchmarkReady.value
))

const complexQueryReady = computed(() => (
  traceTotal.value > 0
  && Boolean(progressData.value)
  && riskTotal.value > 0
))

const selectedProjectLabel = computed(() => {
  const project = projects.value.find((item) => item.project_id === selectedProjectId.value)
  return project ? `${project.name} · ${project.project_id}` : (performanceGuide.value.demoProjectId || '未选择项目')
})

const benchmarkCaption = computed(() => (
  benchmarkSummary.value.has_benchmark_data
    ? `当前已识别 ${benchmarkSummary.value.total_records} 条 benchmark 记录`
    : '当前未识别到 benchmark 数据'
))

const benchmarkCards = computed(() => ([
  { key: 'products', label: '产品', value: benchmarkSummary.value.products },
  { key: 'projects', label: '项目', value: benchmarkSummary.value.projects },
  { key: 'requirements', label: '需求', value: benchmarkSummary.value.requirements },
  { key: 'test_cases', label: '测试用例', value: benchmarkSummary.value.test_cases },
  { key: 'defects', label: '缺陷', value: benchmarkSummary.value.defects },
  { key: 'milestones', label: '里程碑', value: benchmarkSummary.value.milestones },
  { key: 'milestone_nodes', label: '快照节点', value: benchmarkSummary.value.milestone_nodes },
  { key: 'branches', label: '分支', value: benchmarkSummary.value.branches },
  { key: 'change_sets', label: '变更集', value: benchmarkSummary.value.change_sets },
  { key: 'audit_logs', label: '审计日志', value: benchmarkSummary.value.audit_logs },
]))

const traceCoverageText = computed(() => (
  traceTotal.value ? `已返回 ${traceTotal.value} 条需求追溯记录` : '等待加载需求追溯函数'
))

const progressSummary = computed(() => (
  progressData.value ? `${progressData.value.completion_rate_percent}%` : '待加载'
))

const progressDefectText = computed(() => (
  progressData.value
    ? `开放缺陷 ${progressData.value.open_defects || 0} 个`
    : '等待加载项目进度函数'
))

const riskLevelText = computed(() => (
  riskTotal.value ? `已返回 ${riskTotal.value} 条里程碑风险记录` : '等待加载风险函数'
))

const requirementCards = computed(() => ([
  {
    code: '5.a',
    title: '索引、视图与查询效率提升',
    requirement: '根据业务查询需求使用索引、设计视图，并基于实际场景验证索引对系统查询效率的提升作用。',
    evidence: performanceReady.value
      ? `性能页已绑定演示项目 ${performanceGuide.value.demoProjectId}，可直接展示演示表 ${performanceGuide.value.demoTable} 与索引 ${performanceGuide.value.demoIndex}。`
      : '性能页已接好，但 benchmark 数据尚未达到演示状态。',
    stateLabel: performanceReady.value ? '已满足' : '待准备',
    stateClass: performanceReady.value ? 'ok' : 'pending',
    links: [{ to: '/performance-lab', label: '性能验证页' }],
  },
  {
    code: '5.b',
    title: '至少 1 个复杂查询功能',
    requirement: '实现 3 张及以上表连接查询，或带分组、排序的多层嵌套查询，贴合实际业务需求。',
    evidence: complexQueryReady.value
      ? `当前项目 ${selectedProjectId.value} 已成功返回需求追溯 ${traceTotal.value} 条、项目进度 1 条、里程碑风险 ${riskTotal.value} 条。`
      : '复杂查询页和函数已存在，但当前页尚未加载出完整结果。',
    stateLabel: complexQueryReady.value ? '已满足' : '待加载',
    stateClass: complexQueryReady.value ? 'ok' : 'pending',
    links: [{ to: '/complex-queries', label: '复杂查询页' }],
  },
  {
    code: '5.c',
    title: '完整性约束与中文提示',
    requirement: '违规操作时，界面需给出明确、具体的中文警告和提示信息。',
    evidence: 'SQL 编辑器已内置唯一约束、外键、非空、检查约束、层级规则和跨项目关联 6 组失败 SQL，可直接课堂演示。',
    stateLabel: '已满足',
    stateClass: 'ok',
    links: [{ to: '/query', label: 'SQL 编辑器' }],
  },
  {
    code: '5.d',
    title: '足够数量测试数据验证查询效率',
    requirement: '生成足够数量的测试数据测试各种功能的查询效率，分析索引和视图的作用。',
    evidence: benchmarkReady.value
      ? `当前 benchmark 数据包含 ${benchmarkSummary.value.requirements} 条需求、${benchmarkSummary.value.test_cases} 条测试用例、${benchmarkSummary.value.defects} 条缺陷与 ${benchmarkSummary.value.total_records} 条总记录。`
      : 'benchmark 数据未导入或数量不足，不能直接支撑效率验收。',
    stateLabel: benchmarkReady.value ? '已满足' : '待准备',
    stateClass: benchmarkReady.value ? 'ok' : 'pending',
    links: [
      { to: '/performance-lab', label: '性能验证页' },
      { to: '/complex-queries', label: '复杂查询页' },
    ],
  },
]))

onMounted(async () => {
  await loadValidationState()
})

watch(
  () => props.connection?.database,
  async (databaseName) => {
    if (!databaseName) {
      return
    }
    await loadValidationState()
  },
)

watch(selectedProjectId, async (projectId, previousId) => {
  if (!projectId || projectId === previousId) {
    return
  }
  await loadQueryEvidence()
})

async function loadValidationState() {
  await Promise.all([
    loadProjects(),
    loadBenchmarkSummary(),
    loadPerformanceGuideData(),
  ])
  await ensureProjectSelection()
  await loadQueryEvidence()
}

async function ensureProjectSelection() {
  if (selectedProjectId.value) {
    return
  }
  const preferred = projects.value.find((item) => item.project_id === performanceGuide.value.demoProjectId)
    || projects.value.find((item) => item.project_id === 'bproj_003')
    || projects.value[0]
  selectedProjectId.value = preferred?.project_id || ''
}

async function loadProjects() {
  projectsLoading.value = true
  try {
    const { data } = await listProjects()
    projects.value = data.items || []
  } catch (error) {
    pageError.value = error.response?.data?.detail || '项目列表加载失败'
  } finally {
    projectsLoading.value = false
  }
}

async function loadBenchmarkSummary() {
  try {
    const { data } = await getBenchmarkSummary()
    benchmarkSummary.value = {
      ...benchmarkSummary.value,
      ...(data.summary || {}),
    }
  } catch (error) {
    pageError.value = error.response?.data?.detail || 'benchmark 数据摘要加载失败'
  }
}

async function loadPerformanceGuideData() {
  try {
    const { data } = await getPerformanceGuide()
    performanceGuide.value = {
      demoProjectId: data?.demo_project_id || 'bproj_003',
      demoTable: data?.index_demo?.demo_table || 'manage_requirements_perf_demo',
      demoIndex: data?.index_demo?.index_name || 'idx_req_perf_project_deleted_order',
    }
  } catch {
    performanceGuide.value = {
      demoProjectId: 'bproj_003',
      demoTable: 'manage_requirements_perf_demo',
      demoIndex: 'idx_req_perf_project_deleted_order',
    }
  }
}

async function loadQueryEvidence() {
  if (!selectedProjectId.value) {
    return
  }
  queryError.value = ''
  try {
    const [traceResp, progressResp, riskResp] = await Promise.all([
      getRequirementTrace(selectedProjectId.value),
      getProjectProgress(selectedProjectId.value),
      getMilestoneRisk(selectedProjectId.value),
    ])
    traceTotal.value = traceResp.data?.total || 0
    progressData.value = progressResp.data || null
    riskTotal.value = riskResp.data?.total || 0
  } catch (error) {
    queryError.value = error.response?.data?.detail || '复杂查询结果加载失败'
    traceTotal.value = 0
    progressData.value = null
    riskTotal.value = 0
  }
}

async function handleImportBenchmark() {
  pageError.value = ''
  pageMessage.value = ''
  importLoading.value = true
  try {
    await importBenchmark()
    pageMessage.value = 'benchmark 数据导入成功，当前页已刷新验收状态。'
    await loadValidationState()
  } catch (error) {
    pageError.value = error.response?.data?.detail || 'benchmark 数据导入失败'
  } finally {
    importLoading.value = false
  }
}

async function handleDeleteBenchmark() {
  pageError.value = ''
  pageMessage.value = ''
  deleteLoading.value = true
  try {
    await deleteBenchmark()
    pageMessage.value = 'benchmark 数据已删除，当前页已刷新验收状态。'
    await loadValidationState()
  } catch (error) {
    pageError.value = error.response?.data?.detail || 'benchmark 数据删除失败'
  } finally {
    deleteLoading.value = false
  }
}

async function handleRefresh() {
  pageError.value = ''
  pageMessage.value = ''
  refreshLoading.value = true
  try {
    await loadValidationState()
    pageMessage.value = '测试与验收状态已刷新。'
  } catch (error) {
    pageError.value = error.response?.data?.detail || '验收状态刷新失败'
  } finally {
    refreshLoading.value = false
  }
}
</script>

<style scoped>
.validation-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
}

.validation-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.95fr);
  gap: 18px;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(201, 100, 66, 0.14), transparent 42%),
    linear-gradient(135deg, rgba(255, 249, 242, 0.98), rgba(245, 237, 221, 0.88));
}

.hero-copy h1 {
  margin: 8px 0 10px;
  font-family: "Noto Serif SC", Georgia, serif;
  font-size: 30px;
  font-weight: 600;
  color: var(--near-black);
}

.hero-copy p {
  margin: 0;
  max-width: 720px;
  color: rgba(28, 40, 52, 0.72);
  line-height: 1.78;
  font-size: 14px;
}

.hero-side {
  display: grid;
  gap: 12px;
  padding: 18px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(250, 245, 236, 0.84));
}

.hero-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: rgba(28, 40, 52, 0.58);
}

.hero-meta strong {
  text-align: right;
  color: var(--near-black);
  font-family: var(--font-mono);
  font-size: 12px;
}

.hero-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin-top: 4px;
}

.page-message,
.page-error,
.panel-error {
  padding: 12px 16px;
  font-size: 13px;
  border: 1px solid;
}

.page-message {
  background: rgba(212, 178, 116, 0.14);
  border-color: rgba(212, 178, 116, 0.32);
  color: rgba(28, 40, 52, 0.86);
}

.page-error,
.panel-error {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.24);
  color: var(--signal);
}

.validation-ribbon {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.status-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 232px;
}

.status-head {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

.status-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid rgba(201, 100, 66, 0.22);
  background: rgba(201, 100, 66, 0.1);
  color: var(--accent);
  font-family: var(--font-mono);
  font-size: 12px;
}

.status-head h3 {
  margin: 0 0 6px;
  font-size: 16px;
  color: var(--near-black);
}

.status-head p {
  margin: 0;
  color: rgba(28, 40, 52, 0.66);
  line-height: 1.65;
  font-size: 13px;
}

.status-pill-row,
.constraint-chip-row,
.status-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-pill,
.constraint-chip {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border: 1px solid rgba(28, 40, 52, 0.12);
  background: rgba(255, 255, 255, 0.72);
  color: rgba(28, 40, 52, 0.72);
  font-size: 11px;
  letter-spacing: 0.04em;
}

.status-pill.ok {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.26);
  color: #0f766e;
}

.status-pill.pending {
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.26);
  color: #92400e;
}

.detail-item {
  flex: 1 1 92px;
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-top: 2px solid rgba(201, 100, 66, 0.16);
  background: rgba(255, 248, 238, 0.74);
}

.detail-item span {
  font-size: 11px;
  color: rgba(28, 40, 52, 0.52);
}

.detail-item strong {
  font-size: 14px;
  color: var(--near-black);
  word-break: break-word;
}

.action-link {
  text-decoration: none;
  width: fit-content;
}

.action-link.small {
  font-size: 12px;
  padding: 8px 10px;
}

.acceptance-panel,
.script-panel,
.data-card {
  padding: 20px;
}

.panel-subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(28, 40, 52, 0.54);
}

.acceptance-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.acceptance-card {
  padding: 18px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.84), rgba(248, 243, 235, 0.88));
}

.acceptance-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.acceptance-code {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--accent);
}

.acceptance-state {
  padding: 4px 9px;
  font-size: 11px;
  border: 1px solid rgba(28, 40, 52, 0.12);
}

.acceptance-state.ok {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.22);
  color: #0f766e;
}

.acceptance-state.pending {
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.22);
  color: #92400e;
}

.acceptance-card h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--near-black);
}

.acceptance-card p,
.evidence-copy {
  margin: 0;
  color: rgba(28, 40, 52, 0.68);
  line-height: 1.72;
  font-size: 13px;
}

.evidence-label {
  margin-top: 14px;
  margin-bottom: 8px;
  font-size: 11px;
  color: rgba(28, 40, 52, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.evidence-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.validation-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 14px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.metric-item,
.query-metric {
  display: grid;
  gap: 6px;
  padding: 14px 12px;
  border: 1px solid rgba(28, 40, 52, 0.08);
  background: rgba(255, 250, 244, 0.78);
}

.metric-item span,
.query-metric span {
  font-size: 11px;
  color: rgba(28, 40, 52, 0.54);
  text-transform: uppercase;
}

.metric-item strong,
.query-metric strong {
  font-size: 24px;
  line-height: 1;
  color: var(--near-black);
  font-family: "Noto Serif SC", Georgia, serif;
}

.query-metric strong small {
  font-size: 12px;
  margin-left: 2px;
}

.metric-item strong {
  font-family: var(--font-mono);
  font-size: 18px;
}

.query-metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.query-metric small {
  color: rgba(28, 40, 52, 0.62);
  font-size: 12px;
  line-height: 1.6;
}

.script-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 10px;
  color: rgba(28, 40, 52, 0.72);
  line-height: 1.74;
  font-size: 14px;
}

.hero-select.compact {
  width: 260px;
  padding: 10px 12px;
  border: 1px solid rgba(28, 40, 52, 0.16);
  background: rgba(255, 255, 255, 0.94);
  color: var(--near-black);
  font-size: 13px;
}

@media (max-width: 1280px) {
  .validation-ribbon,
  .acceptance-grid,
  .validation-grid,
  .metric-grid,
  .query-metric-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 860px) {
  .validation-hero,
  .validation-ribbon,
  .acceptance-grid,
  .validation-grid,
  .metric-grid,
  .query-metric-grid {
    grid-template-columns: 1fr;
  }

  .hero-select.compact {
    width: 100%;
    margin-top: 12px;
  }

  .hero-copy h1 {
    font-size: 24px;
  }
}
</style>
