<template>
  <div class="page" style="display:flex;flex-direction:column;gap:20px;height:100%;overflow-y:auto;padding-right:8px;">
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
      <h1 style="margin: 0; font-size: 20px; color: var(--near-black);">产品管理</h1>
      <button class="btn-brand" @click="showForm = true">+ 新建产品</button>
    </div>

    <!-- Error -->
    <div v-if="error" style="padding:12px 16px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius: 0;color:var(--signal);font-size:13px;">{{ error }}</div>

    <!-- Table -->
    <div v-if="items.length" class="card wide" style="overflow:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">产品名称</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">状态</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">版本</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">创建时间</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in items" :key="p.product_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
            <td style="padding:10px 12px;font-weight:600;color:var(--accent)">{{ p.name }}</td>
            <td style="padding:10px 12px;"><span :class="['chip', p.status === 'active' ? 'chip-good' : 'chip-neutral']">{{ p.status }}</span></td>
            <td style="padding:10px 12px;font-family:monospace;">{{ p.version || '—' }}</td>
            <td style="padding:10px 12px;color:rgba(28,40,52,0.6)">{{ formatTime(p.created_at) }}</td>
            <td style="padding:10px 12px;">
              <button class="ghost" style="font-size:12px;padding:4px 8px;" @click="editProduct(p)">编辑</button>
              <button class="ghost" style="font-size:12px;padding:4px 8px;color:var(--signal);" @click="handleDelete(p.product_id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="!loading" style="padding:40px;text-align:center;color:rgba(28,40,52,0.4)">暂无产品数据</div>

    <!-- Loading -->
    <div v-if="loading" style="padding:20px;text-align:center;color:rgba(28,40,52,0.4)">加载中...</div>

    <!-- Form Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingId ? '编辑产品' : '新建产品' }}</h2>
          <button class="ghost" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>产品名称 *</label>
            <input v-model="form.name" type="text" placeholder="如：智能车载系统 V3.0" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="form.description" rows="3" placeholder="产品功能描述..."></textarea>
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="form.status">
              <option value="active">active</option>
              <option value="archived">archived</option>
            </select>
          </div>
          <div class="form-group">
            <label>版本</label>
            <input v-model="form.version" type="text" placeholder="如：3.0.0" />
          </div>
          <div class="form-group">
            <label>路线图</label>
            <input v-model="form.roadmap" type="text" placeholder="如：2026年Q2发布" />
          </div>
          <div v-if="formError" style="padding:10px;color:var(--signal);font-size:13px;background:rgba(239,68,68,0.08);border-radius: 0;">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="ghost" @click="closeForm">取消</button>
          <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '创建产品' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { listProducts, createProduct, updateProduct, deleteProduct } from '../api'

const items = ref([])
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingId = ref(null)
const formError = ref('')
const form = reactive({ name: '', description: '', status: 'active', roadmap: '', version: '' })

onMounted(loadItems)

async function loadItems() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await listProducts()
    items.value = data.items || []
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

function editProduct(p) {
  editingId.value = p.product_id
  Object.assign(form, { name: p.name, description: p.description || '', status: p.status, roadmap: p.roadmap || '', version: p.version || '' })
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
  Object.assign(form, { name: '', description: '', status: 'active', roadmap: '', version: '' })
}

async function handleSubmit() {
  formError.value = ''
  try {
    if (editingId.value) {
      await updateProduct(editingId.value, form)
    } else {
      await createProduct(form)
    }
    closeForm()
    await loadItems()
  } catch (e) {
    formError.value = e.response?.data?.detail || '操作失败'
  }
}

async function handleDelete(id) {
  if (!confirm('确认删除此产品？')) return
  try {
    await deleteProduct(id)
    await loadItems()
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
