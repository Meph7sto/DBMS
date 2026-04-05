<template>
  <div class="dashboard">
    <div class="hero head-hero">
      <div class="hero-panel">
        <div class="eyebrow">终端面板</div>
        <h1>DBMS 数据库管理系统</h1>
        <p class="lead">使用现代数据终端轻松地可视化、管理和查询您的数据库。</p>
        <div class="hero-actions" v-if="connection">
          <router-link to="/query" class="primary">✦ 新建查询</router-link>
        </div>
      </div>
      <div class="hero-panel">
        <div v-if="!connection" class="panel-card">
           <div class="panel-title">系统状态</div>
           <div class="panel-value" style="color:var(--signal)">未连接</div>
           <div class="panel-caption">请通过右上角连接数据库</div>
        </div>
        <div v-else class="panel-card" style="background: rgba(47, 143, 137, 0.1); border-color: rgba(47, 143, 137, 0.4)">
           <div class="panel-title">当前活动库</div>
           <div class="panel-value">{{ connection.database }}</div>
           <div class="panel-caption">{{ connection.host }}:{{ connection.port }}</div>
           <div class="signal-grid" style="margin-top:20px;">
             <div class="signal good"></div><div class="signal good"></div><div class="signal good"></div>
           </div>
        </div>
      </div>
    </div>

    <div v-if="connection" class="grid anim-slide" style="margin-top: 24px;">
      <div class="card">
        <div class="card-header">
          <h4 class="card-kicker">数据库模式</h4>
          <span class="chip chip-accent">总计: {{ schemas.length }}</span>
        </div>
        <h2>模式列表</h2>
        <div class="chip-row">
          <span v-for="s in schemas.slice(0, 8)" :key="s" class="chip chip-neutral">{{ s }}</span>
          <span v-if="schemas.length > 8" class="chip chip-neutral">...</span>
        </div>
      </div>
      <div class="card">
        <div class="card-header">
          <h4 class="card-kicker">数据表</h4>
          <span class="chip chip-good">总计: {{ totalTables }}</span>
        </div>
        <h2>全部数据表</h2>
        <div class="chip-row">
           <span class="chip chip-good">数据已就绪</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  connection: Object,
  schemas: { type: Array, default: () => [] },
  tablesMap: { type: Object, default: () => ({}) },
})

const totalTables = computed(() =>
  Object.values(props.tablesMap).reduce((sum, list) => sum + list.length, 0)
)
</script>

<style scoped>
/* Inherit from ref-styles.css */
</style>
