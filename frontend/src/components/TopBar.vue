<template>
  <header class="topbar">
    <div class="topbar__left">
      <span class="topbar__logo">▦ DBMS</span>
      <span class="topbar__sep">│</span>
      <template v-if="connection">
        <span class="status-dot connected"></span>
        <span class="topbar__db">{{ connection.database }}</span>
        <span class="topbar__host">@ {{ connection.host }}:{{ connection.port }}</span>
      </template>
      <template v-else>
        <span class="status-dot"></span>
        <span class="topbar__host">未连接</span>
      </template>
    </div>
    <div class="topbar__right">
      <button v-if="connection" class="btn btn--sm" @click="$emit('disconnect')">
        断开
      </button>
      <button class="btn btn--sm btn--accent" @click="$emit('open-connect')">
        {{ connection ? '切换连接' : '连接数据库' }}
      </button>
    </div>
  </header>
</template>

<script setup>
defineProps({ connection: Object })
defineEmits(['open-connect', 'disconnect'])
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--topbar-height);
  padding: 0 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.topbar__left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.topbar__logo {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--accent);
}
.topbar__sep {
  color: var(--border);
}
.topbar__db {
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--text-primary);
}
.topbar__host {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--text-muted);
}
.topbar__right {
  display: flex;
  gap: 8px;
}
</style>
