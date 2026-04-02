<template>
  <div class="table-page">
    <div class="table-header">
      <h2 class="table-title">
        <span class="table-schema">{{ schema }}.</span>{{ name }}
      </h2>
      <span v-if="detail" class="table-row-est">
        ≈ {{ detail.row_estimate }} 行
      </span>
    </div>

    <div class="tab-bar">
      <button
        v-for="t in tabs"
        :key="t.key"
        class="tab-item"
        :class="{ active: activeTab === t.key }"
        @click="activeTab = t.key"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- Structure Tab -->
    <div v-if="activeTab === 'structure'" class="tab-content overflow-auto anim-slide">
      <div v-if="detail" class="section">
        <div class="section-label">列定义</div>
        <table class="data-table">
          <thead>
            <tr>
              <th>列名</th>
              <th>类型</th>
              <th>可空</th>
              <th>默认值</th>
              <th>最大长度</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in detail.columns" :key="c.column_name">
              <td style="color:var(--accent)">{{ c.column_name }}</td>
              <td>{{ c.data_type }}</td>
              <td>{{ c.is_nullable }}</td>
              <td>{{ c.column_default || '—' }}</td>
              <td>{{ c.character_maximum_length || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="detail && detail.constraints.length" class="section">
        <div class="section-label">约束</div>
        <table class="data-table">
          <thead><tr><th>约束名</th><th>类型</th></tr></thead>
          <tbody>
            <tr v-for="c in detail.constraints" :key="c.constraint_name">
              <td>{{ c.constraint_name }}</td>
              <td>{{ c.constraint_type }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="detail && detail.indexes.length" class="section">
        <div class="section-label">索引</div>
        <table class="data-table">
          <thead><tr><th>索引名</th><th>定义</th></tr></thead>
          <tbody>
            <tr v-for="idx in detail.indexes" :key="idx.indexname">
              <td>{{ idx.indexname }}</td>
              <td style="white-space:pre-wrap;max-width:500px">{{ idx.indexdef }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Data Tab -->
    <div v-if="activeTab === 'data'" class="tab-content overflow-auto anim-slide">
      <div v-if="dataResult.columns.length" class="data-area">
        <table class="data-table">
          <thead>
            <tr>
              <th class="row-num">#</th>
              <th v-for="col in dataResult.columns" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in dataResult.rows" :key="i">
              <td class="row-num">{{ (dataResult.page - 1) * dataResult.size + i + 1 }}</td>
              <td v-for="col in dataResult.columns" :key="col">
                <span v-if="row[col] === null" class="null-val">NULL</span>
                <span v-else>{{ row[col] }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pager">
        <button class="btn btn--sm" :disabled="dataResult.page <= 1" @click="loadData(dataResult.page - 1)">
          ◂ 上一页
        </button>
        <span class="pager-info">
          第 {{ dataResult.page }} 页 · 共 {{ totalPages }} 页 · {{ dataResult.total }} 条
        </span>
        <button class="btn btn--sm" :disabled="dataResult.page >= totalPages" @click="loadData(dataResult.page + 1)">
          下一页 ▸
        </button>
      </div>
    </div>

    <div v-if="loadError" class="load-error">{{ loadError }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { tableDetail, tableData } from '../api'

const props = defineProps({
  schema: { type: String, required: true },
  name: { type: String, required: true },
})

const tabs = [
  { key: 'structure', label: '结构' },
  { key: 'data', label: '数据' },
]
const activeTab = ref('structure')
const detail = ref(null)
const loadError = ref('')

const dataResult = reactive({
  columns: [],
  rows: [],
  page: 1,
  size: 50,
  total: 0,
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(dataResult.total / dataResult.size))
)

async function loadDetail() {
  loadError.value = ''
  try {
    const { data } = await tableDetail(props.schema, props.name)
    detail.value = data
  } catch (err) {
    loadError.value = err.response?.data?.detail || '加载失败'
  }
}

async function loadData(page = 1) {
  loadError.value = ''
  try {
    const { data } = await tableData(props.schema, props.name, page)
    dataResult.columns = data.columns
    dataResult.rows = data.rows
    dataResult.page = data.page
    dataResult.size = data.size
    dataResult.total = data.total
  } catch (err) {
    loadError.value = err.response?.data?.detail || '加载数据失败'
  }
}

watch(
  () => `${props.schema}.${props.name}`,
  () => {
    activeTab.value = 'structure'
    detail.value = null
    dataResult.columns = []
    dataResult.rows = []
    dataResult.page = 1
    dataResult.total = 0
    loadDetail()
    loadData()
  },
  { immediate: true }
)
</script>

<style scoped>
.table-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.table-header {
  display: flex;
  align-items: baseline;
  gap: 14px;
  padding: 16px 20px 10px;
  flex-shrink: 0;
}
.table-title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
}
.table-schema {
  color: var(--text-muted);
}
.table-row-est {
  font-family: var(--font-mono);
  font-size: 0.76rem;
  color: var(--text-muted);
}
.tab-content {
  flex: 1;
  min-height: 0;
}
.section {
  margin: 16px 0;
  padding: 0 20px;
}
.section-label {
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
  padding-left: 2px;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 10px 20px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}
.pager-info {
  font-family: var(--font-mono);
  font-size: 0.74rem;
  color: var(--text-secondary);
}
.load-error {
  padding: 10px 20px;
  font-size: 0.82rem;
  color: var(--danger);
}
.row-num {
  color: var(--text-muted);
  text-align: right;
  width: 40px;
  min-width: 40px;
}
</style>
