<template>
  <div class="result-panel">
    <div class="result-header">
      <span class="result-title">{{ title }}</span>
      <span v-if="rowCount !== null" class="result-count">
        {{ rowCount }} 行
      </span>
    </div>

    <div v-if="error" class="result-error">{{ error }}</div>

    <div v-else-if="message" class="result-message">{{ message }}</div>

    <div v-else-if="columns.length" class="result-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th class="row-num">#</th>
            <th v-for="col in columns" :key="col">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in rows" :key="i">
            <td class="row-num">{{ i + 1 }}</td>
            <td v-for="col in columns" :key="col">
              <span v-if="row[col] === null" class="null-val">NULL</span>
              <span v-else>{{ row[col] }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="result-empty">执行查询以查看结果</div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '查询结果' },
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowCount: { type: Number, default: null },
  error: { type: String, default: '' },
  message: { type: String, default: '' },
})
</script>

<style scoped>
.result-panel {
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--border);
  background: var(--bg-primary);
  min-height: 0;
  flex: 1;
}
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.result-title {
  font-family: var(--font-display);
  font-size: 0.74rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-secondary);
}
.result-count {
  font-family: var(--font-mono);
  font-size: 0.74rem;
  color: var(--accent);
}
.result-scroll {
  flex: 1;
  overflow: auto;
}
.result-error {
  padding: 12px 14px;
  font-family: var(--font-mono);
  font-size: 0.82rem;
  color: var(--danger);
  background: rgba(255, 71, 87, 0.06);
  border-bottom: 1px solid var(--danger);
}
.result-message {
  padding: 12px 14px;
  font-family: var(--font-mono);
  font-size: 0.82rem;
  color: var(--success);
}
.result-empty {
  padding: 32px;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.85rem;
}
.row-num {
  color: var(--text-muted);
  text-align: right;
  width: 40px;
  min-width: 40px;
}
</style>
