<template>
  <div class="dashboard">
    <div class="hero head-hero">
      <div class="hero-panel">
        <div class="eyebrow">终端面板</div>
        <h1>DBMS 数据库管理系统</h1>

        <div class="hero-actions" v-if="connection">
          <router-link to="/query" class="btn-brand">✦ 新建查询</router-link>
          <button @click="handleImportVisibleDemoData" class="btn-white" :disabled="isLoading">引入演示数据</button>
          <button @click="handleDeleteVisibleDemoData" class="btn-white" :disabled="isLoading" style="color: var(--error); border-color: var(--error);">删除演示数据</button>
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


  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { importVisibleDemoData, deleteVisibleDemoData } from '../api'

const props = defineProps({
  connection: Object,
  schemas: { type: Array, default: () => [] },
  tablesMap: { type: Object, default: () => ({}) },
})

const totalTables = computed(() =>
  Object.values(props.tablesMap).reduce((sum, list) => sum + list.length, 0)
)

const isLoading = ref(false)

const handleImportVisibleDemoData = async () => {
  if (!confirm("确定要引入首页演示数据吗？这会清空并重建当前这套演示业务数据。")) return;
  try {
    isLoading.value = true;
    await importVisibleDemoData();
    alert('演示数据引入成功！现在可以进入各业务页面查看完整数据。');
  } catch (e) {
    alert('演示数据引入失败: ' + (e.response?.data?.detail || e.message));
  } finally {
    isLoading.value = false;
  }
}

const handleDeleteVisibleDemoData = async () => {
  if (!confirm("确定要删除首页演示数据吗？")) return;
  try {
    isLoading.value = true;
    await deleteVisibleDemoData();
    alert('演示数据删除成功！');
  } catch (e) {
    alert('演示数据删除失败: ' + (e.response?.data?.detail || e.message));
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
/* Inherit from ref-styles.css */
</style>
