<template>
  <div class="query-page">
    <div class="query-toolbar">
      <span class="query-toolbar__title">SQL 查询</span>
      <div class="query-toolbar__right">
        <span class="query-hint">Ctrl + Enter 执行</span>
        <button class="btn btn--sm" @click="sqlText = ''">清空</button>
        <button class="btn btn--sm btn--accent" :disabled="running" @click="run">
          {{ running ? '执行中...' : '▶ 执行' }}
        </button>
      </div>
    </div>

    <div class="query-editor-area">
      <SqlEditor v-model="sqlText" @execute="run" />
    </div>

    <ResultTable
      :columns="result.columns"
      :rows="result.rows"
      :row-count="result.rowCount"
      :error="result.error"
      :message="result.message"
    />

    <div v-if="elapsed !== null" class="query-status">
      耗时 {{ elapsed }} ms
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
  height: 100%;
}
.query-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.query-toolbar__title {
  font-family: var(--font-display);
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-secondary);
}
.query-toolbar__right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.query-hint {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
}
.query-editor-area {
  flex: 1;
  display: flex;
  min-height: 120px;
  max-height: 50%;
}
.query-status {
  padding: 4px 14px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}
</style>
