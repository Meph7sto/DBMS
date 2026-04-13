<template>
  <div style="position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(4px);" @click.self="$emit('close')">
    <div class="card card-whisper anim-slide" style="width: 440px; padding: 32px; background: var(--bg-card);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <h3 style="margin: 0; color: var(--text-primary); font-family: var(--font-serif); font-size: 25px; font-weight: 500;">连接数据库</h3>
        <button class="btn-white" style="padding: 4px 10px; font-size: 14px;" @click="$emit('close')">✕</button>
      </div>
      <div>
        <div style="margin-bottom: 16px;">
          <div class="type-sample-label" style="margin-bottom: 6px;">主机地址</div>
          <input v-model="form.host" placeholder="localhost" style="width: 100%; padding: 10px 12px; border: 1px solid var(--border-color); border-radius: 0; font-family: var(--font-sans); font-size: 15px; background: var(--color-white); color: var(--text-primary);" />
        </div>
        <div style="margin-bottom: 16px;">
          <div class="type-sample-label" style="margin-bottom: 6px;">端口</div>
          <input v-model.number="form.port" placeholder="5438" style="width: 100%; padding: 10px 12px; border: 1px solid var(--border-color); border-radius: 0; font-family: var(--font-sans); font-size: 15px; background: var(--color-white); color: var(--text-primary);" />
        </div>
        <div style="margin-bottom: 16px;">
          <div class="type-sample-label" style="margin-bottom: 6px;">用户名</div>
          <input v-model="form.user" placeholder="postgres" style="width: 100%; padding: 10px 12px; border: 1px solid var(--border-color); border-radius: 0; font-family: var(--font-sans); font-size: 15px; background: var(--color-white); color: var(--text-primary);" />
        </div>
        <div style="margin-bottom: 16px;">
          <div class="type-sample-label" style="margin-bottom: 6px;">密码</div>
          <input type="password" v-model="form.password" style="width: 100%; padding: 10px 12px; border: 1px solid var(--border-color); border-radius: 0; font-family: var(--font-sans); font-size: 15px; background: var(--color-white); color: var(--text-primary);" />
        </div>
        <div style="margin-bottom: 24px;">
          <div class="type-sample-label" style="margin-bottom: 6px;">数据库</div>
          <input v-model="form.database" placeholder="postgres" style="width: 100%; padding: 10px 12px; border: 1px solid var(--border-color); border-radius: 0; font-family: var(--font-sans); font-size: 15px; background: var(--color-white); color: var(--text-primary);" />
        </div>
        
        <div v-if="error" style="color: var(--color-error); font-size: 13px; margin: 8px 0 16px;">{{ error }}</div>
        
        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 16px;">
          <button class="btn-warm-sand" style="padding: 8px 16px;" @click="$emit('close')">取消</button>
          <button class="btn-brand" style="padding: 8px 16px;" :disabled="loading" @click="doConnect">
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
