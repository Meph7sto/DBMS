<template>
  <div class="app-shell">
    <ConnectionModal
      v-if="showConnect"
      @connected="onConnected"
      @close="showConnect = false"
    />
    <TopBar
      :connection="connection"
      @open-connect="showConnect = true"
      @disconnect="onDisconnect"
    />
    <div class="app-body">
      <Sidebar
        v-if="connection"
        :schemas="schemas"
        :tables-map="tablesMap"
        @refresh="loadMeta"
      />
      <main class="app-main">
        <router-view
          :connection="connection"
          :schemas="schemas"
          :tables-map="tablesMap"
        />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { connectionStatus, disconnect, listSchemas, listTables } from './api'
import TopBar from './components/TopBar.vue'
import Sidebar from './components/Sidebar.vue'
import ConnectionModal from './components/ConnectionModal.vue'

const connection = ref(null)
const showConnect = ref(false)
const schemas = ref([])
const tablesMap = ref({})

async function checkConnection() {
  try {
    const { data } = await connectionStatus()
    if (data.connected) {
      connection.value = data.connection
      await loadMeta()
    } else {
      showConnect.value = true
    }
  } catch {
    showConnect.value = true
  }
}

async function loadMeta() {
  try {
    const { data: schemaList } = await listSchemas()
    schemas.value = schemaList.map((s) => s.name)

    const map = {}
    for (const s of schemas.value) {
      const { data: tableList } = await listTables(s)
      map[s] = tableList
    }
    tablesMap.value = map
  } catch (err) {
    console.error('Failed to load metadata', err)
  }
}

function onConnected(info) {
  connection.value = info
  showConnect.value = false
  loadMeta()
}

async function onDisconnect() {
  try {
    await disconnect()
  } catch { /* ignore */ }
  connection.value = null
  schemas.value = []
  tablesMap.value = {}
  showConnect.value = true
}

onMounted(checkConnection)
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-root);
}
.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.app-main {
  flex: 1;
  overflow: auto;
  background: var(--bg-primary);
}
</style>
