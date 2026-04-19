<template>
  <aside ref="railRef" class="rail" :class="{ collapsed }">
    <div class="brand">
      <button class="sidebar-toggle" @click="toggleCollapsed" :title="collapsed ? '展开侧边栏' : '折叠侧边栏'">
        <span>{{ collapsed ? '▷' : '◁' }}</span>
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

      <router-link to="/test-cases" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="1"/><path d="M7 8h10"/><path d="M7 12h10"/><path d="M7 16h6"/></svg>
        <span class="nav-label">测试用例</span>
      </router-link>

      <router-link to="/milestones" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M5 7h14l-2 3 2 3H5z"/></svg>
        <span class="nav-label">里程碑</span>
      </router-link>

      <router-link to="/branches" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3v12"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><path d="M6 6a12 12 0 0 0 12 12"/></svg>
        <span class="nav-label">分支管理</span>
      </router-link>

      <router-link to="/comments" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        <span class="nav-label">评论管理</span>
      </router-link>

      <router-link to="/audit-logs" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6"/><path d="M12 3v4"/><rect x="4" y="7" width="16" height="14" rx="2"/><path d="M8 11h8"/><path d="M8 15h5"/></svg>
        <span class="nav-label">审计日志</span>
      </router-link>

      <router-link to="/complex-queries" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16"/><path d="M4 12h10"/><path d="M4 18h7"/><circle cx="18" cy="12" r="3"/><circle cx="14" cy="18" r="2"/></svg>
        <span class="nav-label">复杂查询</span>
      </router-link>

      <router-link to="/test-validation" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
        <span class="nav-label">测试验收</span>
      </router-link>

      <router-link to="/view-comparison" class="rail-link">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M4 17h16"/><path d="M7 4v16"/><path d="M17 4v16"/></svg>
        <span class="nav-label">视图对照</span>
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
            v-if="schema === 'public'"
            to="/performance-lab"
            class="submenu-item rail-link perf-entry"
          >
            <span class="submenu-dot perf-dot"></span>
            <span>性能验证</span>
          </router-link>
          <router-link
            v-if="schema === 'public'"
            to="/test-validation"
            class="submenu-item rail-link perf-entry"
          >
            <span class="submenu-dot perf-dot"></span>
            <span>测试验收台</span>
          </router-link>
          <router-link
            v-if="schema === 'public'"
            to="/view-comparison"
            class="submenu-item rail-link perf-entry"
          >
            <span class="submenu-dot perf-dot"></span>
            <span>视图对照台</span>
          </router-link>
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
      <div class="meta-block" v-if="!collapsed" style="padding: 16px;">
        <div class="type-sample-label" style="margin-bottom: 12px;">操作选项</div>
        <button class="btn-warm-sand" style="width: 100%;" @click="$emit('refresh')">↻ 刷新数据库字典</button>
      </div>
    </div>

    <div
      class="sidebar-resizer"
      :class="{ dragging: isDragging }"
      role="separator"
      aria-label="调整侧边栏宽度"
      aria-orientation="vertical"
      :aria-hidden="collapsed"
      tabindex="0"
      @pointerdown="onResizeStart"
      @keydown.left.prevent="nudgeWidth(-16)"
      @keydown.right.prevent="nudgeWidth(16)"
    ></div>
  </aside>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref, watch } from 'vue'

const props = defineProps({
  schemas: { type: Array, default: () => [] },
  tablesMap: { type: Object, default: () => ({}) },
  collapsed: { type: Boolean, default: false },
  width: { type: Number, default: 280 },
})
const emit = defineEmits(['refresh', 'update:collapsed', 'update:width'])

const expanded = reactive({})
const isDragging = ref(false)
const railRef = ref(null)
let activePointerId = null

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

function toggleCollapsed() {
  emit('update:collapsed', !props.collapsed)
}

function nudgeWidth(delta) {
  if (props.collapsed) {
    return
  }
  emit('update:width', props.width + delta)
}

function onResizeStart(event) {
  if (props.collapsed) {
    return
  }

  event.preventDefault()
  activePointerId = event.pointerId
  isDragging.value = true
  document.body.classList.add('sidebar-resizing')
  window.addEventListener('pointermove', onResizeMove)
  window.addEventListener('pointerup', onResizeEnd)
  window.addEventListener('pointercancel', onResizeEnd)
}

function onResizeMove(event) {
  if (!isDragging.value || event.pointerId !== activePointerId) {
    return
  }

  const layoutLeft = railRef.value?.closest('.app-layout')?.getBoundingClientRect().left ?? 0
  emit('update:width', event.clientX - layoutLeft)
}

function onResizeEnd(event) {
  if (activePointerId !== null && event.pointerId !== activePointerId) {
    return
  }

  activePointerId = null
  isDragging.value = false
  document.body.classList.remove('sidebar-resizing')
  window.removeEventListener('pointermove', onResizeMove)
  window.removeEventListener('pointerup', onResizeEnd)
  window.removeEventListener('pointercancel', onResizeEnd)
}

onBeforeUnmount(() => {
  document.body.classList.remove('sidebar-resizing')
  window.removeEventListener('pointermove', onResizeMove)
  window.removeEventListener('pointerup', onResizeEnd)
  window.removeEventListener('pointercancel', onResizeEnd)
})
</script>

<style scoped>
:global(body.sidebar-resizing) {
  cursor: col-resize;
  user-select: none;
}

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

.ref-app .perf-entry {
  margin-bottom: 6px;
  border-bottom: 1px dashed rgba(28, 40, 52, 0.08);
}

.ref-app .perf-dot {
  background: var(--color-terracotta);
  box-shadow: 0 0 0 2px rgba(201, 100, 66, 0.12);
}

.ref-app .sidebar-resizer {
  position: absolute;
  top: 0;
  right: 0;
  width: 12px;
  height: 100%;
  cursor: col-resize;
  touch-action: none;
  z-index: 30;
}

.ref-app .sidebar-resizer::after {
  content: "";
  position: absolute;
  top: 16px;
  bottom: 16px;
  right: 3px;
  width: 2px;
  background: transparent;
  transition: background 0.2s ease, box-shadow 0.2s ease;
}

.ref-app .sidebar-resizer:hover::after,
.ref-app .sidebar-resizer:focus-visible::after,
.ref-app .sidebar-resizer.dragging::after {
  background: rgba(201, 100, 66, 0.45);
  box-shadow: 0 0 0 1px rgba(201, 100, 66, 0.12);
}

.ref-app .rail.collapsed .sidebar-resizer {
  pointer-events: none;
  opacity: 0;
}
</style>
