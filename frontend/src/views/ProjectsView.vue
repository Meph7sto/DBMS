<template>
  <div class="page" style="display:flex;flex-direction:column;gap:20px;height:100%;overflow-y:auto;padding-right:8px;">
    <div class="page-header" style="justify-content: flex-end;">
      <button class="btn-brand" @click="showForm = true">+ 新建项目</button>
    </div>

    <div v-if="error" style="padding:12px 16px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius: 0;color:var(--signal);font-size:13px;">{{ error }}</div>

    <div v-if="items.length" class="card wide" style="overflow:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">项目名称</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">所属产品</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">状态</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">创建时间</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in items" :key="p.project_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
            <td style="padding:10px 12px;font-weight:600;color:var(--accent)">{{ p.name }}</td>
            <td style="padding:10px 12px;">{{ p.product_name || '—' }}</td>
            <td style="padding:10px 12px;"><span :class="['chip', p.status === 'active' ? 'chip-good' : 'chip-neutral']">{{ p.status }}</span></td>
            <td style="padding:10px 12px;color:rgba(28,40,52,0.6)">{{ formatTime(p.created_at) }}</td>
            <td style="padding:10px 12px;">
              <button class="ghost" style="font-size:12px;padding:4px 8px;" @click="editProject(p)">编辑</button>
              <button class="ghost" style="font-size:12px;padding:4px 8px;color:var(--signal);" @click="handleDelete(p.project_id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="!loading" style="padding:40px;text-align:center;color:rgba(28,40,52,0.4)">暂无项目数据</div>
    <div v-if="loading" style="padding:20px;text-align:center;color:rgba(28,40,52,0.4)">加载中...</div>

    <!-- Stats Cards -->
    <div v-if="stats.length" class="grid" style="margin-top:0">
      <div v-for="s in stats" :key="s.project_id" class="card">
        <div class="card-header">
          <h4 class="card-kicker">{{ s.project_name }}</h4>
          <span :class="['chip', s.project_status === 'active' ? 'chip-good' : 'chip-neutral']">{{ s.project_status }}</span>
        </div>
        <div class="stat-grid">
          <div class="stat-item"><span class="stat-value">{{ s.total_requirements || 0 }}</span><span class="stat-label">需求总数</span></div>
          <div class="stat-item"><span class="stat-value" style="color:var(--accent)">{{ s.completion_rate_percent || 0 }}%</span><span class="stat-label">完成率</span></div>
          <div class="stat-item"><span class="stat-value" style="color:var(--signal)">{{ s.open_defects || 0 }}</span><span class="stat-label">开启缺陷</span></div>
          <div class="stat-item"><span class="stat-value">{{ s.total_test_cases || 0 }}</span><span class="stat-label">测试用例</span></div>
        </div>
      </div>
    </div>

    <!-- Form Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingId ? '编辑项目' : '新建项目' }}</h2>
          <button class="ghost" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>项目名称 *</label>
            <input v-model="form.name" type="text" placeholder="如：车载语音助手重构" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="form.description" rows="3" placeholder="项目功能描述..."></textarea>
          </div>
          <div class="form-group">
            <label>所属产品</label>
            <select v-model="form.product_id">
              <option value="">— 无 —</option>
              <option v-for="prod in products" :key="prod.product_id" :value="prod.product_id">{{ prod.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="form.status">
              <option value="active">active</option>
              <option value="archived">archived</option>
            </select>
          </div>
          <div v-if="formError" style="padding:10px;color:var(--signal);font-size:13px;background:rgba(239,68,68,0.08);border-radius: 0;">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="ghost" @click="closeForm">取消</button>
          <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '创建项目' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { listProjects, createProject, updateProject, deleteProject, listProducts, listProjectStats } from '../api'

const items = ref([])
const stats = ref([])
const products = ref([])
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingId = ref(null)
const formError = ref('')
const form = reactive({ name: '', description: '', status: 'active', product_id: '' })

onMounted(async () => {
  await loadItems()
  loadProducts()
  loadStats()
})

async function loadItems() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await listProjects()
    items.value = data.items || []
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadProducts() {
  try {
    const { data } = await listProducts()
    products.value = data.items || []
  } catch { products.value = [] }
}

async function loadStats() {
  try {
    const { data } = await listProjectStats()
    stats.value = data.items || []
  } catch { stats.value = [] }
}

function editProject(p) {
  editingId.value = p.project_id
  Object.assign(form, { name: p.name, description: p.description || '', status: p.status, product_id: p.product_id || '' })
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
  Object.assign(form, { name: '', description: '', status: 'active', product_id: '' })
}

async function handleSubmit() {
  formError.value = ''
  try {
    if (editingId.value) {
      await updateProject(editingId.value, form)
    } else {
      await createProject(form)
    }
    closeForm()
    await Promise.all([loadItems(), loadStats()])
  } catch (e) {
    formError.value = e.response?.data?.detail || '操作失败'
  }
}

async function handleDelete(id) {
  if (!confirm('确认删除此项目？')) return
  try {
    await deleteProject(id)
    await Promise.all([loadItems(), loadStats()])
  } catch (e) {
    error.value = e.response?.data?.detail || '删除失败'
  }
}

function formatTime(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
.stat-item { display: flex; flex-direction: column; gap: 2px; }
.stat-value { font-size: 20px; font-weight: 700; color: var(--ink-700); }
.stat-label { font-size: 11px; color: rgba(28,40,52,0.5); text-transform: uppercase; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: var(--bg-card); border-radius: 0; width: 480px; max-width: 90vw; box-shadow: none; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(28,40,52,0.1); }
.modal-header h2 { margin: 0; font-size: 16px; }
.modal-body { padding: 24px; display: flex; flex-direction: column; gap: 16px; }
.modal-footer { padding: 16px 24px; border-top: 1px solid rgba(28,40,52,0.1); display: flex; gap: 12px; justify-content: flex-end; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 12px; color: rgba(28,40,52,0.6); font-weight: 500; }
.form-group input, .form-group textarea, .form-group select { padding: 8px 12px; border: 1px solid rgba(28,40,52,0.2); border-radius: 0; font-size: 13px; background: rgba(28,40,52,0.02); }
.form-group textarea { resize: vertical; }
.page::-webkit-scrollbar { width: 6px; }
.page::-webkit-scrollbar-thumb { background: rgba(28,40,52,0.2); }
</style>
