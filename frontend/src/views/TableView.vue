<template>
  <div class="table-page" style="display:flex;flex-direction:column;gap:20px;height:100%;overflow-y:auto;padding-right:8px;">
    <div class="page-header">
      <div>
        <div class="eyebrow" style="margin-bottom:6px">数据表查看器</div>
        <h1 style="margin:0"><span style="color:rgba(28,40,52,0.4)">{{ schema }}.</span>{{ name }}</h1>
      </div>
      <div class="page-actions" v-if="detail">
        <span class="chip chip-good">约 {{ detail.row_estimate }} 行</span>
      </div>
    </div>

    <div class="ribbon">
      <button v-for="t in tabs" :key="t.key" 
        class="ribbon-step" :class="{ active: activeTab === t.key }" 
        @click="activeTab = t.key">
        {{ t.label }}
      </button>
    </div>

    <!-- Structure Tab -->
    <div v-if="activeTab === 'structure'" class="anim-slide grid" style="margin-top:0">
      <div v-if="detail" class="card wide">
        <div class="card-header">
          <h4 class="card-kicker">字段定义</h4>
        </div>
        <div class="matrix">
          <div class="matrix-row head">
            <div>字段名</div><div>类型</div><div>允许空值</div><div>默认值</div><div>最大长度</div>
          </div>
          <div v-for="c in detail.columns" :key="c.column_name" class="matrix-row" style="padding: 10px 0; border-top: 1px solid rgba(28,40,52,0.06)">
            <div style="font-weight:600; color:var(--accent)">{{ c.column_name }}</div>
            <div>{{ c.data_type }}</div>
            <div>{{ c.is_nullable }}</div>
            <div style="font-family:monospace; color:rgba(28,40,52,0.6)">{{ c.column_default || '—' }}</div>
            <div>{{ c.character_maximum_length || '—' }}</div>
          </div>
        </div>
      </div>

      <div v-if="detail && detail.constraints.length" class="card">
        <div class="card-header"><h4 class="card-kicker">约束</h4></div>
        <div class="approval-list">
          <div v-for="c in detail.constraints" :key="c.constraint_name" class="approval-item">
            <div>
              <h3>{{ c.constraint_name }}</h3>
              <div class="form-hint" style="color:var(--ink-500)">{{ c.constraint_type }}</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="detail && detail.indexes.length" class="card">
        <div class="card-header"><h4 class="card-kicker">索引</h4></div>
        <div class="approval-list">
          <div v-for="idx in detail.indexes" :key="idx.indexname" class="approval-item" style="flex-direction:column; align-items:flex-start">
            <h3>{{ idx.indexname }}</h3>
            <div style="font-size:12px;color:rgba(28,40,52,0.6);font-family:monospace">{{ idx.indexdef }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Data Tab -->
    <div v-if="activeTab === 'data'" class="card wide anim-slide" style="flex:1;min-height:400px;overflow:hidden;display:flex;flex-direction:column;padding:0;background:rgba(255,255,255,0.95);">
      <ResultTable
        v-if="dataResult.columns.length"
        :columns="dataResult.columns"
        :rows="dataResult.rows"
        :row-count="dataResult.total"
        title="表数据"
      />
      <div v-if="dataResult.columns.length" style="padding:12px 20px; display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(28,40,52,0.1)">
         <button class="ghost" :disabled="dataResult.page <= 1" @click="loadData(dataResult.page - 1)">◂ 上一页</button>
         <span style="font-size:13px;color:rgba(28,40,52,0.6)">第 {{ dataResult.page }} 页，共 {{ totalPages }} 页</span>
         <button class="ghost" :disabled="dataResult.page >= totalPages" @click="loadData(dataResult.page + 1)">下一页 ▸</button>
      </div>
      <div v-else style="padding:40px; text-align:center; color:rgba(28,40,52,0.4)">暂无数据</div>
    </div>

    <div v-if="loadError" style="padding: 16px 20px; color: var(--signal)">{{ loadError }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { tableDetail, tableData } from '../api'
import ResultTable from '../components/ResultTable.vue'

const props = defineProps({
  schema: { type: String, required: true },
  name: { type: String, required: true },
})

const tabs = [
  { key: 'structure', label: '表结构' },
  { key: 'data', label: '数据预览' },
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
/* Inherited */
.table-page::-webkit-scrollbar { width: 6px; }
.table-page::-webkit-scrollbar-thumb { background: rgba(28,40,52,0.2); }
</style>
