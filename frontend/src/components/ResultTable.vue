<template>
  <div style="display:flex;flex-direction:column;height:100%;">
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; border-bottom: 1px solid rgba(28,40,52,0.1); background: rgba(28,40,52,0.02)">
      <span class="eyebrow">{{ title }}</span>
      <span v-if="rowCount !== null" class="eyebrow" style="color:var(--accent)">
        共 {{ rowCount }} 行
      </span>
    </div>

    <div v-if="error" style="padding: 16px 20px; color: var(--signal); font-family: monospace; font-size: 13px;">{{ error }}</div>

    <div v-else-if="message" style="padding: 16px 20px; color: var(--teal); font-family: monospace; font-size: 13px;">{{ message }}</div>

    <div v-else-if="columns.length" style="flex:1; overflow:auto;">
      <table style="width:100%; border-collapse:collapse; font-family: monospace; font-size:12px; text-align:left;">
        <thead style="position:sticky; top:0; background:var(--paper); z-index:1; border-bottom: 1px solid rgba(28,40,52,0.2);">
          <tr>
            <th style="padding: 8px 12px; color:rgba(28,40,52,0.5); width:40px">#</th>
            <th v-for="col in columns" :key="col" style="padding: 8px 12px; color:rgba(28,40,52,0.8); white-space:nowrap;">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in rows" :key="i" style="border-bottom: 1px solid rgba(28,40,52,0.06);">
            <td style="padding: 6px 12px; color:rgba(28,40,52,0.4);">{{ i + 1 }}</td>
            <td v-for="col in columns" :key="col" style="padding: 6px 12px; white-space:nowrap;">
              <span v-if="row[col] === null" style="color:rgba(28,40,52,0.3); font-style:italic">NULL</span>
              <span v-else>{{ row[col] }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else style="padding: 40px; text-align:center; color:rgba(28,40,52,0.4); font-size:13px;">执行查询以查看结果</div>
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
  background: rgba(47, 143, 137, 0.05);
}
</style>
