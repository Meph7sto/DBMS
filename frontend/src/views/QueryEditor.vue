<template>
  <div class="query-page" style="display:flex;flex-direction:column;gap:16px;height:100%;">
    <div class="card" style="padding:0; overflow:hidden">
      <div class="card-header" style="padding: 16px 20px 0 20px;">
         <h4 class="card-kicker">SQL 编辑器</h4>
         <div class="hero-actions" style="margin:0">
           <span class="eyebrow" style="margin-right:12px;text-transform:none">Ctrl + Enter 执行</span>
           <button class="ghost" @click="sqlText = ''">清空</button>
           <button class="primary" :disabled="running" @click="run">
             {{ running ? '执行中...' : '▶ 执行' }}
           </button>
         </div>
      </div>
      <div style="border-top: 1px solid rgba(28,40,52,0.12); border-bottom: 1px solid rgba(28,40,52,0.12); margin-top: 10px; min-height: 200px; display:flex;">
        <SqlEditor v-model="sqlText" @execute="run" style="flex:1;" />
      </div>
      <div v-if="elapsed !== null" style="padding: 8px 20px; font-size: 11px; color: rgba(28,40,52,0.6);" class="eyebrow">
        耗时: {{ elapsed }} ms
      </div>
    </div>

    <div class="card wide" style="flex:1;overflow:hidden;display:flex;flex-direction:column;padding:0;background:rgba(255,255,255,0.95);">
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
/* Inherited */
</style>
