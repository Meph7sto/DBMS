<template>
  <div style="position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(4px);" @click.self="$emit('close')">
    <div class="card anim-slide" style="width: 440px; padding: 32px; box-shadow: 0 10px 40px rgba(0,0,0,0.1)">
      <div class="card-header" style="margin-bottom: 24px;">
        <h2 style="font-size: 26px;">连接数据库</h2>
        <button class="ghost" style="padding: 4px 10px; border:none" @click="$emit('close')">✕</button>
      </div>
      <div class="form">
        <label class="form-group">
          <span>主机地址</span>
          <input v-model="form.host" placeholder="localhost" />
        </label>
        <label class="form-group">
          <span>端口</span>
          <input v-model.number="form.port" placeholder="5438" />
        </label>
        <label class="form-group">
          <span>用户名</span>
          <input v-model="form.user" placeholder="postgres" />
        </label>
        <label class="form-group">
          <span>密码</span>
          <input type="password" v-model="form.password" />
        </label>
        <label class="form-group">
          <span>数据库</span>
          <input v-model="form.database" placeholder="postgres" />
        </label>
        
        <div v-if="error" style="color: var(--signal); font-size: 13px; margin: 8px 0;">{{ error }}</div>
        
        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 16px;">
          <button class="ghost" @click="$emit('close')">取消</button>
          <button class="primary" :disabled="loading" @click="doConnect">
            {{ loading ? '连接中...' : '连接' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { connect, connectionDefaults } from '../api'

const emit = defineEmits(['connected', 'close'])

const form = reactive({
  host: '',
  port: '',
  user: '',
  password: '',
  database: '',
})
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    const { data } = await connectionDefaults()
    Object.assign(form, data)
  } catch (err) {
    console.error("Failed to load connection defaults:", err)
  }
})

async function doConnect() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await connect({ ...form })
    if (data.ok) {
      emit('connected', data.connection)
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || '连接失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Inherited */
</style>
