<template>
  <div class="ref-app">
    <div class="grain"></div>
    <div class="app-layout" :class="{ 'no-sidebar': !connection }">
      <Sidebar
        v-if="connection"
        :schemas="schemas"
        :tables-map="tablesMap"
        @refresh="loadMeta"
      />
      <main class="canvas">
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
    const { data: status } = await connectionStatus()
    if (status.connected) {
      connection.value = status.connection
      await loadMeta()
    } else {
      // Auto-connect with default credentials
      const { data: defaults } = await connectionDefaults()
      const { data } = await connect(defaults)
      if (data.ok) {
        connection.value = data.connection
        await loadMeta()
      } else {
        showConnect.value = true
      }
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
/* Scoped styles removed because ref-styles.css handles global layouts */
.app-layout.no-sidebar {
  grid-template-columns: 1fr;
}
</style>
