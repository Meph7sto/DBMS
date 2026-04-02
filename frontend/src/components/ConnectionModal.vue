<template>
  <div class="overlay anim-fade" @click.self="$emit('close')">
    <div class="modal anim-slide">
      <div class="modal-header">
        <span>连接数据库</span>
        <button class="btn btn--sm" @click="$emit('close')">✕</button>
      </div>
      <div class="modal-body">
        <div class="mb-3">
          <label class="label">主机地址</label>
          <input class="input" v-model="form.host" placeholder="localhost" />
        </div>
        <div class="mb-3">
          <label class="label">端口</label>
          <input class="input" v-model.number="form.port" placeholder="5438" />
        </div>
        <div class="mb-3">
          <label class="label">用户名</label>
          <input class="input" v-model="form.user" placeholder="postgres" />
        </div>
        <div class="mb-3">
          <label class="label">密码</label>
          <input class="input" type="password" v-model="form.password" />
        </div>
        <div class="mb-3">
          <label class="label">数据库</label>
          <input class="input" v-model="form.database" placeholder="postgres" />
        </div>
        <div v-if="error" class="conn-error">{{ error }}</div>
      </div>
      <div class="modal-footer">
        <button class="btn" @click="$emit('close')">取消</button>
        <button class="btn btn--accent" :disabled="loading" @click="doConnect">
          {{ loading ? '连接中...' : '连接' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { connect } from '../api'

const emit = defineEmits(['connected', 'close'])

const form = reactive({
  host: 'localhost',
  port: 5438,
  user: 'postgres',
  password: 'postgres',
  database: 'postgres',
})
const loading = ref(false)
const error = ref('')

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
.conn-error {
  padding: 8px 12px;
  font-size: 0.82rem;
  color: var(--danger);
  background: rgba(255, 71, 87, 0.08);
  border: 1px solid var(--danger);
}
</style>
