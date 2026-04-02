<template>
  <aside class="sidebar">
    <div class="sidebar__actions">
      <router-link to="/query" class="btn btn--accent" style="width:100%;justify-content:center">
        ＋ 新建查询
      </router-link>
    </div>

    <div class="sidebar__tree">
      <div v-for="schema in schemas" :key="schema" class="schema-group">
        <div
          class="schema-header"
          @click="toggleSchema(schema)"
        >
          <span class="schema-icon">{{ expanded[schema] ? '▾' : '▸' }}</span>
          <span class="schema-name">{{ schema }}</span>
          <span class="schema-count">{{ (tablesMap[schema] || []).length }}</span>
        </div>

        <div v-if="expanded[schema]" class="schema-tables anim-slide">
          <router-link
            v-for="t in tablesMap[schema] || []"
            :key="t.name"
            :to="`/table/${schema}/${t.name}`"
            class="table-item"
            :class="{ 'table-item--view': t.type === 'VIEW' }"
          >
            <span class="table-icon">{{ t.type === 'VIEW' ? '◇' : '▤' }}</span>
            <span class="table-label">{{ t.name }}</span>
          </router-link>
        </div>
      </div>

      <div v-if="schemas.length === 0" class="sidebar__empty">
        暂无数据
      </div>
    </div>

    <div class="sidebar__footer">
      <button class="btn btn--sm" style="width:100%;justify-content:center" @click="$emit('refresh')">
        ↻ 刷新
      </button>
    </div>
  </aside>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  schemas: { type: Array, default: () => [] },
  tablesMap: { type: Object, default: () => ({}) },
})
defineEmits(['refresh'])

const expanded = reactive({})

watch(
  () => props.schemas,
  (list) => {
    list.forEach((s) => {
      if (!(s in expanded)) expanded[s] = true
    })
  },
  { immediate: true }
)

function toggleSchema(s) {
  expanded[s] = !expanded[s]
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  flex-shrink: 0;
  overflow: hidden;
}
.sidebar__actions {
  padding: 12px;
  border-bottom: 1px solid var(--border);
}
.sidebar__tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}
.sidebar__footer {
  padding: 10px 12px;
  border-top: 1px solid var(--border);
}
.sidebar__empty {
  padding: 24px 16px;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.82rem;
}

/* Schema Group */
.schema-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  cursor: pointer;
  user-select: none;
  transition: background var(--t-fast);
}
.schema-header:hover { background: var(--bg-hover); }
.schema-icon {
  font-size: 0.7rem;
  color: var(--text-muted);
  width: 12px;
}
.schema-name {
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-secondary);
}
.schema-count {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--text-muted);
}

/* Table Items */
.table-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px 5px 32px;
  text-decoration: none;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 0.8rem;
  transition: all var(--t-fast);
  border-left: 2px solid transparent;
}
.table-item:hover {
  background: var(--bg-hover);
  border-left-color: var(--border-hover);
}
.table-item.router-link-active {
  background: var(--accent-muted);
  border-left-color: var(--accent);
  color: var(--accent);
}
.table-icon {
  font-size: 0.72rem;
  color: var(--text-muted);
}
.table-item--view .table-icon { color: var(--warning); }
</style>
