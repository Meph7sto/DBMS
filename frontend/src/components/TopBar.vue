<template>
  <nav class="nav">
    <div class="nav-brand">
      <span>{{ pageTitle }}</span>
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
    'test-cases': '测试用例',
    'milestones': '里程碑',
    'branches': '分支管理',
    'comments': '评论管理',
    'audit-logs': '审计日志',
    'complex-queries': '复杂查询',
  }
  return nameMap[route.name] || 'DB Admin'
})
</script>

<style scoped>
/* Styles inherited from global ref-styles.css */
</style>
