<template>
  <div class="dashboard">
    <div class="dash-hero">
      <h1 class="dash-title">▦ DBMS</h1>
      <p class="dash-subtitle">可视化数据库管理系统</p>
    </div>

    <div v-if="connection" class="dash-grid anim-slide">
      <div class="dash-card">
        <div class="dash-card__label">数据库</div>
        <div class="dash-card__value">{{ connection.database }}</div>
      </div>
      <div class="dash-card">
        <div class="dash-card__label">服务器</div>
        <div class="dash-card__value font-mono" style="font-size:0.78rem">
          {{ connection.host }}:{{ connection.port }}
        </div>
      </div>
      <div class="dash-card">
        <div class="dash-card__label">Schema 数</div>
        <div class="dash-card__value">{{ schemas.length }}</div>
      </div>
      <div class="dash-card">
        <div class="dash-card__label">总表数</div>
        <div class="dash-card__value">{{ totalTables }}</div>
      </div>
    </div>

    <div v-if="connection" class="dash-actions anim-slide">
      <router-link to="/query" class="btn btn--accent">＋ 新建查询</router-link>
    </div>

    <div v-if="!connection" class="dash-empty">
      请先连接数据库
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
.dashboard {
  padding: 48px 40px;
  max-width: 800px;
}
.dash-hero {
  margin-bottom: 40px;
}
.dash-title {
  font-family: var(--font-display);
  font-size: 2.2rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--accent);
  line-height: 1;
}
.dash-subtitle {
  margin-top: 8px;
  font-size: 0.92rem;
  color: var(--text-secondary);
}
.dash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  margin-bottom: 32px;
}
.dash-card {
  padding: 18px 20px;
  background: var(--bg-secondary);
}
.dash-card__label {
  font-family: var(--font-display);
  font-size: 0.68rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.dash-card__value {
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-primary);
}
.dash-actions {
  display: flex;
  gap: 12px;
}
.dash-empty {
  padding: 48px;
  text-align: center;
  color: var(--text-muted);
  font-size: 1rem;
}
</style>
