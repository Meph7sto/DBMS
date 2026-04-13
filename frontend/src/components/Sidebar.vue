<template>
  <aside class="rail" :class="{ collapsed: isCollapsed }">
    <div class="brand">
      <button class="sidebar-toggle" @click="isCollapsed = !isCollapsed" :title="isCollapsed ? '展开侧边栏' : '折叠侧边栏'">
        <span>{{ isCollapsed ? '▷' : '◁' }}</span>
      </button>
      <div class="brand-content">
        <div class="brand-mark">DB</div>
        <div class="brand-sub">数据系统</div>
      </div>
    </div>

    <nav class="rail-nav">
      <router-link to="/" class="rail-link" active-class="" exact-active-class="router-link-active">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>
        <span class="nav-label">仪表盘</span>
      </router-link>

      <router-link to="/products" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
        <span class="nav-label">产品管理</span>
      </router-link>

      <router-link to="/projects" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        <span class="nav-label">项目管理</span>
      </router-link>

      <router-link to="/requirements" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
        <span class="nav-label">需求管理</span>
      </router-link>

      <router-link to="/defects" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v4"/><path d="M16 2v4"/><path d="M11.76 15.6a4 4 0 0 0 4.14-2l.9-1.5a4 4 0 0 0-1.85-5.61A4.01 4.01 0 0 0 9.2 8.1l.9 1.5a4 4 0 0 0 1.66 4"/><path d="M22 10.5l-4 1.5"/><path d="M2 10.5l4 1.5"/><path d="M12 22v-4"/><path d="M20 16l-3.5-1.5"/><path d="M4 16l3.5-1.5"/></svg>
        <span class="nav-label">缺陷管理</span>
      </router-link>

      <router-link to="/query" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
        <span class="nav-label">新建查询</span>
      </router-link>

      <div v-for="schema in schemas" :key="schema" class="nav-group">
        <button class="rail-link has-children" @click="toggleSchema(schema)">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
          <span class="nav-label">{{ schema }} ({{ (tablesMap[schema] || []).length }})</span>
          <svg class="nav-chevron" :class="{ rotated: expanded[schema] }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>

        <div v-if="expanded[schema]" class="nav-submenu">
          <router-link
            v-for="t in tablesMap[schema] || []"
            :key="t.name"
            :to="`/table/${schema}/${t.name}`"
            class="submenu-item rail-link"
          >
            <span class="submenu-dot"></span>
            <span>{{ t.name }}</span>
          </router-link>
        </div>
      </div>
    </nav>

    <div class="rail-meta">
      <div class="meta-block" v-if="!isCollapsed" style="padding: 16px;">
        <div class="type-sample-label" style="margin-bottom: 12px;">操作选项</div>
        <button class="btn-warm-sand" style="width: 100%;" @click="$emit('refresh')">↻ 刷新数据库字典</button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  schemas: { type: Array, default: () => [] },
  tablesMap: { type: Object, default: () => ({}) },
})
defineEmits(['refresh'])

const expanded = reactive({})
const isCollapsed = ref(false)

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
.ref-app .brand {
  position: relative;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-cream);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-direction: row-reverse;
}

.ref-app .brand-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: opacity 0.2s ease, max-width 0.2s ease;
  max-width: 200px;
}

.ref-app .brand-mark {
  font-family: "Noto Serif SC", Georgia, serif;
  font-size: 28px;
  font-weight: 500;
  letter-spacing: 2px;
  color: var(--near-black);
  transition: opacity 0.2s ease;
  white-space: nowrap;
}

.ref-app .brand-sub {
  color: var(--olive-gray);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-top: 6px;
  font-weight: 500;
  transition: opacity 0.2s ease;
  white-space: nowrap;
}

/* 鼠标靠近按钮时隐藏品牌内容 */
.ref-app .sidebar-toggle:hover ~ .brand-content {
  opacity: 0;
  max-width: 0;
}

/* 折叠状态：品牌内容隐藏 */
.ref-app .rail.collapsed .brand-content {
  display: none;
}

.ref-app .rail.collapsed .brand {
  justify-content: center;
  padding-right: 0;
}

/* 折叠状态下显示展开按钮图标 */
.ref-app .rail.collapsed .sidebar-toggle {
  position: static;
  transform: none;
}

.ref-app .sidebar-toggle {
  position: relative;
  top: auto;
  right: auto;
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1px solid var(--border-warm);
  border-radius: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  color: var(--olive-gray);
  transition: all 0.2s ease;
  box-shadow: 0px 0px 0px 1px var(--ring-warm);
  flex-shrink: 0;
}

.ref-app .sidebar-toggle:hover {
  background: var(--warm-sand);
  color: var(--near-black);
  box-shadow: 0px 0px 0px 1px var(--ring-deep);
}
</style>
