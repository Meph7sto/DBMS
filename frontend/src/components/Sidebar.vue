<template>
  <aside class="rail" :class="{ collapsed: isCollapsed }">
    <button class="sidebar-toggle" @click="isCollapsed = !isCollapsed">
      <span>◁</span>
    </button>

    <div class="brand">
      <div class="brand-mark">Db</div>
      <div class="brand-sub">数据系统</div>
    </div>

    <nav class="rail-nav">
      <router-link to="/" class="rail-link active">
        <span class="nav-icon">⌘</span>
        <span class="nav-label">仪表盘</span>
      </router-link>

      <router-link to="/products" class="rail-link">
        <span class="nav-icon">📐</span>
        <span class="nav-label">产品管理</span>
      </router-link>

      <router-link to="/projects" class="rail-link">
        <span class="nav-icon">📋</span>
        <span class="nav-label">项目管理</span>
      </router-link>

      <router-link to="/requirements" class="rail-link">
        <span class="nav-icon">🎯</span>
        <span class="nav-label">需求管理</span>
      </router-link>

      <router-link to="/defects" class="rail-link">
        <span class="nav-icon">🐛</span>
        <span class="nav-label">缺陷管理</span>
      </router-link>

      <router-link to="/query" class="rail-link">
        <span class="nav-icon">✨</span>
        <span class="nav-label">新建查询</span>
      </router-link>

      <div v-for="schema in schemas" :key="schema" class="nav-group">
        <button class="rail-link has-children" @click="toggleSchema(schema)">
          <span class="nav-icon">📦</span>
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
      <div class="meta-block" v-if="!isCollapsed">
        <div class="meta-title">操作选项</div>
        <button class="ghost" style="width: 100%; border: 1px solid rgba(28,40,52,0.2)" @click="$emit('refresh')">↻ 刷新数据库字典</button>
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
/* Styles inherited from global ref-styles.css */
</style>
