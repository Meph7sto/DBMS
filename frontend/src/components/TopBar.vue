<template>
  <header class="page-header" style="margin-bottom: 24px;">
    <div>
      <h1 v-if="connection">{{ connection.database }}</h1>
      <h1 v-else>未连接数据库</h1>
      <div class="eyebrow" style="margin-top: 6px;">
        <template v-if="connection">
          <span style="color:var(--teal)">●</span> 
          {{ connection.host }}:{{ connection.port }}
        </template>
        <template v-else>
          <span style="color:var(--signal)">●</span> 等待连接...
        </template>
      </div>
    </div>
    <div class="page-actions">
      <button v-if="connection" class="danger" @click="$emit('disconnect')">断开连接</button>
      <button class="primary" @click="$emit('open-connect')">{{ connection ? '切换连接' : '连接数据库' }}</button>
    </div>
  </header>
</template>

<script setup>
defineProps({ connection: Object })
defineEmits(['open-connect', 'disconnect'])
</script>

<style scoped>
/* Styles inherited from global ref-styles.css */
</style>
