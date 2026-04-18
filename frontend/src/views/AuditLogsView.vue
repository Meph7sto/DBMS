<template>
  <div class="page" style="display:flex;flex-direction:column;gap:20px;height:100%;overflow-y:auto;padding-right:8px;">
    <div class="page-header">
      <h1 style="margin:0;font-size:20px;color:var(--near-black);">审计日志</h1>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <select v-model="filterProject" class="filter-select">
          <option value="">全部项目</option>
          <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
            {{ project.name }}
          </option>
        </select>
        <select v-model="filterProduct" class="filter-select">
          <option value="">全部产品</option>
          <option v-for="product in products" :key="product.product_id" :value="product.product_id">
            {{ product.name }}
          </option>
        </select>
        <button class="btn-brand" @click="showForm = true">+ 新建日志</button>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="items.length" class="card wide anim-slide" style="overflow:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
            <th class="th">日志信息</th>
            <th class="th">项目</th>
            <th class="th">产品</th>
            <th class="th">目标</th>
            <th class="th">详情</th>
            <th class="th">时间</th>
            <th class="th">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.log_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
            <td class="td" style="min-width:320px;">
              <div style="display:flex;flex-direction:column;gap:6px;">
                <div class="td strong" style="padding:0;">{{ item.actor }}</div>
                <div><span class="chip chip-neutral">{{ item.action }}</span></div>
                <div style="font-family:monospace;font-size:12px;color:rgba(28,40,52,0.55)">{{ item.log_id }}</div>
                <details style="margin-top:2px;">
                  <summary style="cursor:pointer;font-size:12px;color:rgba(28,40,52,0.55);">完整字段</summary>
                  <pre style="margin:8px 0 0;white-space:pre-wrap;word-break:break-all;font-size:11px;line-height:1.45;color:rgba(28,40,52,0.72);">{{ stringifyRecord(item) }}</pre>
                </details>
              </div>
            </td>
            <td class="td">{{ item.project_name || item.project_id || '—' }}</td>
            <td class="td">{{ item.product_name || item.product_id || '—' }}</td>
            <td class="td">{{ item.target_type ? `${item.target_type}:${item.target_id || '—'}` : '—' }}</td>
            <td class="td" style="white-space:pre-wrap;word-break:break-all;">{{ stringifyJson(item.detail, '{}') }}</td>
            <td class="td muted">{{ formatTime(item.created_at) }}</td>
            <td class="td">
              <button class="ghost mini-btn" @click="editItem(item)">编辑</button>
              <button class="ghost mini-btn danger" @click="handleDelete(item.log_id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="!loading" class="empty">暂无审计日志</div>
    <div v-if="loading" class="loading">加载中...</div>

    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingId ? '编辑审计日志' : '新建审计日志' }}</h2>
          <button class="ghost" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="editingId" class="form-group">
            <label>日志 ID</label>
            <input :value="editingId" type="text" readonly />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>项目</label>
              <select v-model="form.project_id">
                <option value="">— 无 —</option>
                <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
                  {{ project.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>产品</label>
              <select v-model="form.product_id">
                <option value="">— 无 —</option>
                <option v-for="product in products" :key="product.product_id" :value="product.product_id">
                  {{ product.name }}
                </option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>操作者 *</label>
              <input v-model="form.actor" type="text" placeholder="user_id" />
            </div>
            <div class="form-group">
              <label>动作 *</label>
              <input v-model="form.action" type="text" placeholder="如：create_requirement" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>目标类型</label>
              <input v-model="form.target_type" type="text" placeholder="requirement / branch" />
            </div>
            <div class="form-group">
              <label>目标 ID</label>
              <input v-model="form.target_id" type="text" placeholder="req_xxx / branch_xxx" />
            </div>
          </div>
          <div class="form-group">
            <label>详情 JSON</label>
            <textarea v-model="form.detail_json" rows="8" placeholder='{"field":"status","before":"draft","after":"confirmed"}'></textarea>
          </div>
          <div v-if="formError" class="error-inline">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="ghost" @click="closeForm">取消</button>
          <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '创建日志' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import {
  listAuditLogs,
  createAuditLog,
  updateAuditLog,
  deleteAuditLog,
  listProjects,
  listProducts,
} from '../api'
import { formatTime, parseJsonInput, stringifyJson } from '../utils/admin'

const items = ref([])
const projects = ref([])
const products = ref([])
const loading = ref(false)
const error = ref('')
const filterProject = ref('')
const filterProduct = ref('')
const showForm = ref(false)
const editingId = ref(null)
const formError = ref('')
const form = reactive({
  project_id: '',
  product_id: '',
  actor: '',
  action: '',
  target_type: '',
  target_id: '',
  detail_json: '{}',
})

onMounted(async () => {
  await Promise.all([loadItems(), loadProjects(), loadProducts()])
})

watch([filterProject, filterProduct], async () => {
  await loadItems()
})

async function loadProjects() {
  try {
    const { data } = await listProjects()
    projects.value = data.items || []
  } catch {
    projects.value = []
  }
}

async function loadProducts() {
  try {
    const { data } = await listProducts()
    products.value = data.items || []
  } catch {
    products.value = []
  }
}

async function loadItems() {
  loading.value = true
  error.value = ''
  try {
    const params = {}
    if (filterProject.value) params.project_id = filterProject.value
    if (filterProduct.value) params.product_id = filterProduct.value
    const { data } = await listAuditLogs(params)
    items.value = data.items || []
  } catch (err) {
    error.value = err.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

function editItem(item) {
  editingId.value = item.log_id
  Object.assign(form, {
    project_id: item.project_id || '',
    product_id: item.product_id || '',
    actor: item.actor,
    action: item.action,
    target_type: item.target_type || '',
    target_id: item.target_id || '',
    detail_json: stringifyJson(item.detail, '{}'),
  })
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
  Object.assign(form, {
    project_id: '',
    product_id: '',
    actor: '',
    action: '',
    target_type: '',
    target_id: '',
    detail_json: '{}',
  })
}

async function handleSubmit() {
  formError.value = ''
  let detail = null
  try {
    detail = parseJsonInput(form.detail_json, {})
  } catch {
    formError.value = '详情 JSON 格式无效'
    return
  }
  const payload = {
    project_id: form.project_id || null,
    product_id: form.product_id || null,
    actor: form.actor,
    action: form.action,
    target_type: form.target_type || null,
    target_id: form.target_id || null,
    detail,
  }
  try {
    if (editingId.value) {
      await updateAuditLog(editingId.value, payload)
    } else {
      await createAuditLog(payload)
    }
    closeForm()
    await loadItems()
  } catch (err) {
    formError.value = err.response?.data?.detail || '操作失败'
  }
}

async function handleDelete(id) {
  if (!confirm('确认删除此审计日志？')) return
  try {
    await deleteAuditLog(id)
    await loadItems()
  } catch (err) {
    error.value = err.response?.data?.detail || '删除失败'
  }
}

function stringifyRecord(record) {
  try {
    return JSON.stringify(record, null, 2)
  } catch {
    return '{}'
  }
}
</script>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap; }
.filter-select { padding: 0 12px; border: 1px solid rgba(28,40,52,0.2); border-radius: 0; font-size: 14px; background: rgba(28,40,52,0.02); height: 36px; outline: none; }
.th { padding:10px 12px; text-align:left; color:rgba(28,40,52,0.5); font-weight:500; }
.td { padding:10px 12px; }
.td.strong { font-weight:600; color:var(--accent); }
.td.muted { color:rgba(28,40,52,0.6); }
.mini-btn { font-size:12px; padding:4px 8px; }
.danger { color:var(--signal); }
.empty, .loading { padding:40px; text-align:center; color:rgba(28,40,52,0.4); }
.error-banner { padding:12px 16px; background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:var(--signal); font-size:13px; }
.error-inline { padding:10px; color:var(--signal); font-size:13px; background:rgba(239,68,68,0.08); }
.form-row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: var(--bg-card); border-radius: 0; width: 720px; max-width: 94vw; max-height: 90vh; overflow-y: auto; }
.modal-header { display:flex; justify-content:space-between; align-items:center; padding:20px 24px; border-bottom:1px solid rgba(28,40,52,0.1); position:sticky; top:0; background:var(--bg-card); }
.modal-header h2 { margin:0; font-size:16px; }
.modal-body { padding:24px; display:flex; flex-direction:column; gap:16px; }
.modal-footer { padding:16px 24px; border-top:1px solid rgba(28,40,52,0.1); display:flex; gap:12px; justify-content:flex-end; }
.form-group { display:flex; flex-direction:column; gap:6px; }
.form-group label { font-size:12px; color:rgba(28,40,52,0.6); font-weight:500; }
.form-group input, .form-group textarea, .form-group select { padding:8px 12px; border:1px solid rgba(28,40,52,0.2); border-radius:0; font-size:13px; background:rgba(28,40,52,0.02); }
.form-group textarea { resize:vertical; }
.page::-webkit-scrollbar { width: 6px; }
.page::-webkit-scrollbar-thumb { background: rgba(28,40,52,0.2); }
</style>
