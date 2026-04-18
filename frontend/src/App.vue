<template>
  <div class="ref-app">
    <div class="grain"></div>
    <div class="app-layout" :class="{ 'no-sidebar': !connection }" :style="connection ? sidebarLayoutStyle : undefined">
      <Sidebar
        v-if="connection"
        :schemas="schemas"
        :tables-map="tablesMap"
        :collapsed="isSidebarCollapsed"
        :width="sidebarWidth"
        @refresh="loadMeta"
        @update:collapsed="onSidebarCollapsedChange"
        @update:width="onSidebarWidthChange"
      />
      <main class="canvas">
        <ConnectionModal
          v-if="showConnect"
          @connected="onConnected"
          @close="showConnect = false"
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  connect,
  connectionDefaults,
  connectionStatus,
  disconnect,
  listSchemas,
  listTables,
} from './api'
import Sidebar from './components/Sidebar.vue'
import ConnectionModal from './components/ConnectionModal.vue'

const DEFAULT_SIDEBAR_WIDTH = 280
const SIDEBAR_COLLAPSED_WIDTH = 72
const SIDEBAR_MIN_WIDTH = 240
const SIDEBAR_MAX_WIDTH = 480
const SIDEBAR_STORAGE_KEY = 'ref-app-sidebar-width'

const connection = ref(null)
const showConnect = ref(false)
const schemas = ref([])
const tablesMap = ref({})
const sidebarWidth = ref(DEFAULT_SIDEBAR_WIDTH)
const isSidebarCollapsed = ref(false)

const sidebarLayoutStyle = computed(() => ({
  '--sidebar-width': `${isSidebarCollapsed.value ? SIDEBAR_COLLAPSED_WIDTH : sidebarWidth.value}px`,
}))

function clampSidebarWidth(width) {
  const viewportMax = typeof window === 'undefined'
    ? SIDEBAR_MAX_WIDTH
    : Math.min(SIDEBAR_MAX_WIDTH, Math.floor(window.innerWidth * 0.45))

  return Math.min(Math.max(width, SIDEBAR_MIN_WIDTH), Math.max(SIDEBAR_MIN_WIDTH, viewportMax))
}

function readSidebarWidth() {
  if (typeof window === 'undefined') {
    return DEFAULT_SIDEBAR_WIDTH
  }

  const raw = window.localStorage.getItem(SIDEBAR_STORAGE_KEY)
  const parsed = Number.parseInt(raw ?? '', 10)
  return Number.isFinite(parsed) ? clampSidebarWidth(parsed) : DEFAULT_SIDEBAR_WIDTH
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function tryAutoConnect() {
  const { data: status } = await connectionStatus()
  if (status.connected) {
    connection.value = status.connection
    await loadMeta()
    return true
  }

  const { data: defaults } = await connectionDefaults()
  const { data } = await connect(defaults)
  if (!data.ok) {
    return false
  }

  connection.value = data.connection
  await loadMeta()
  return true
}

async function checkConnection() {
  const maxAttempts = 10
  const retryDelayMs = 1000

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      const connected = await tryAutoConnect()
      if (connected) {
        showConnect.value = false
        return
      }
    } catch (err) {
      console.warn(`Auto-connect attempt ${attempt} failed`, err)
    }

    if (attempt < maxAttempts) {
      await sleep(retryDelayMs)
    }
  }

  showConnect.value = true
}

async function loadMeta() {
  try {
    const { data: schemaList } = await listSchemas()
    schemas.value = schemaList.map((s) => s.name)

    const entries = await Promise.all(
      schemas.value.map(async (schema) => {
        const { data: tableList } = await listTables(schema)
        return [schema, tableList]
      })
    )
    tablesMap.value = Object.fromEntries(entries)
  } catch (err) {
    console.error('Failed to load metadata', err)
  }
}

function onConnected(info) {
  connection.value = info
  showConnect.value = false
  loadMeta()
}

function onSidebarCollapsedChange(collapsed) {
  isSidebarCollapsed.value = collapsed
}

function onSidebarWidthChange(width) {
  sidebarWidth.value = clampSidebarWidth(width)
}

function handleWindowResize() {
  sidebarWidth.value = clampSidebarWidth(sidebarWidth.value)
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

watch(sidebarWidth, (width) => {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(width))
  }
})

onMounted(() => {
  sidebarWidth.value = readSidebarWidth()
  window.addEventListener('resize', handleWindowResize)
  checkConnection()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleWindowResize)
})
</script>

<style scoped>
/* Scoped styles removed because ref-styles.css handles global layouts */
.app-layout.no-sidebar {
  grid-template-columns: 1fr;
}
</style>
