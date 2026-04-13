<template>
  <nav class="nav">
    <div class="nav-brand">
      <div class="logo-mark">DB</div>
      <span>{{ pageTitle }}</span>
    </div>
    <div class="nav-links">
      <button v-if="connection" class="btn-white" style="color: var(--color-error); border-color: var(--color-error);" @click="$emit('disconnect')">断开连接</button>
      <button class="btn-brand" @click="$emit('open-connect')">{{ connection ? '切换连接' : '连接数据库' }}</button>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

defineProps({ connection: Object })
defineEmits(['open-connect', 'disconnect'])

const route = useRoute()

const pageTitle = computed(() => {
  if (!route) return '未连接数据库'
  const nameMap = {
    'dashboard': '仪表盘',
    'query': 'SQL查询',
    'table': route.params.name ? `数据表: ${route.params.name}` : '表数据',
    'products': '产品管理',
    'projects': '项目管理',
    'requirements': '需求列表',
    'defects': '缺陷追踪',
  }
  return nameMap[route.name] || 'DB Admin'
})
</script>

<style scoped>
/* Styles inherited from global ref-styles.css */
</style>
