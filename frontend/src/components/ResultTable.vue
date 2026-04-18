<template>
  <div style="display:flex;flex-direction:column;height:100%;min-height:0;">
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; border-bottom: 1px solid var(--border-color); background: var(--bg-card)">
      <span class="type-sample-label" style="font-size: 13px;">{{ title }}</span>
      <span v-if="rowCount !== null" class="type-sample-label" style="color:var(--color-terracotta); font-size: 13px;">
        共 {{ rowCount }} 行
      </span>
    </div>

    <div
      v-if="error"
      style="flex:1;overflow:auto;padding:16px 20px;color:var(--color-error);font-family:var(--font-mono);font-size:13px;white-space:pre-wrap;line-height:1.6;"
    >{{ error }}</div>

    <div
      v-else-if="message"
      style="flex:1;overflow:auto;padding:16px 20px;color:var(--text-secondary);font-family:var(--font-mono);font-size:13px;white-space:pre-wrap;line-height:1.6;"
    >{{ message }}</div>

    <div v-else-if="columns.length" style="flex:1; overflow:auto;">
      <table style="width:100%; border-collapse:collapse; font-family: var(--font-mono); font-size:13px; text-align:left;">
        <thead style="position:sticky; top:0; background:var(--bg-card); z-index:1;">
          <tr>
            <th style="padding: 12px 16px; color:var(--text-tertiary); width:40px; font-weight: normal; border-bottom: 1px solid var(--border-color);">#</th>
            <th v-for="col in columns" :key="col" style="padding: 12px 16px; color:var(--text-secondary); white-space:nowrap; font-weight: normal; border-bottom: 1px solid var(--border-color);">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in rows" :key="i" style="border-bottom: 1px solid var(--border-subtle);">
            <td style="padding: 8px 16px; color:var(--text-tertiary);">{{ i + 1 }}</td>
            <td v-for="col in columns" :key="col" style="padding: 8px 16px; white-space:nowrap; color: var(--text-primary);">
              <span v-if="row[col] === null" style="color:var(--text-tertiary); font-style:italic">NULL</span>
              <span v-else>{{ row[col] }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else style="padding: 40px; text-align:center; color:var(--text-tertiary); font-size:14px;">执行查询以查看结果</div>
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
/* Inherited */
tbody tr:hover {
  background: rgba(201, 100, 66, 0.05);
}
</style>
