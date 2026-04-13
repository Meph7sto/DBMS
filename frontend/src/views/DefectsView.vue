<template>
  <div class="page" style="display:flex;flex-direction:column;gap:20px;height:100%;overflow-y:auto;padding-right:8px;">
    <div class="page-header" style="justify-content: flex-end;">
      <div style="display:flex;gap:10px;align-items:center;">
        <select v-model="filterProject" style="padding:6px 10px;border:1px solid rgba(28,40,52,0.2);border-radius: 0;font-size:12px;background:rgba(28,40,52,0.02);">
          <option value="">全部项目</option>
          <option v-for="p in projects" :key="p.project_id" :value="p.project_id">{{ p.name }}</option>
        </select>
        <button class="btn-brand" @click="showForm = true">+ 新建缺陷</button>
      </div>
    </div>

    <div v-if="error" style="padding:12px 16px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius: 0;color:var(--signal);font-size:13px;">{{ error }}</div>

    <div v-if="items.length" class="card wide anim-slide" style="overflow:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">缺陷标题</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">关联需求</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">严重程度</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">优先级</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">状态</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">负责人</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in items" :key="d.defect_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
            <td style="padding:10px 12px;font-weight:600;color:var(--accent)">{{ d.title }}</td>
            <td style="padding:10px 12px;color:rgba(28,40,52,0.6);font-size:12px;">{{ d.requirement_title || d.requirement_id }}</td>
            <td style="padding:10px 12px;"><span :class="['chip', severityColor(d.severity)]">{{ d.severity }}</span></td>
            <td style="padding:10px 12px;"><span class="chip chip-accent">{{ d.priority }}</span></td>
            <td style="padding:10px 12px;"><span :class="['chip', statusColor(d.status)]">{{ d.status }}</span></td>
            <td style="padding:10px 12px;">{{ d.current_assignee || '—' }}</td>
            <td style="padding:10px 12px;">
              <button class="ghost" style="font-size:12px;padding:4px 8px;" @click="editDefect(d)">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="!loading" style="padding:40px;text-align:center;color:rgba(28,40,52,0.4)">暂无缺陷数据</div>
    <div v-if="loading" style="padding:20px;text-align:center;color:rgba(28,40,52,0.4)">加载中...</div>

    <!-- Form Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingId ? '编辑缺陷' : '新建缺陷' }}</h2>
          <button class="ghost" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>所属项目 *</label>
            <select v-model="form.project_id" :disabled="!!editingId">
              <option value="">选择项目...</option>
              <option v-for="p in projects" :key="p.project_id" :value="p.project_id">{{ p.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>关联需求 *</label>
            <select v-model="form.requirement_id" :disabled="!!editingId">
              <option value="">选择需求...</option>
              <option v-for="r in requirements" :key="r.req_id" :value="r.req_id">{{ r.title }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>缺陷标题 *</label>
            <input v-model="form.title" type="text" placeholder="缺陷标题" />
          </div>
          <div class="form-group">
            <label>复现步骤</label>
            <textarea v-model="form.reproduce_steps" rows="4" placeholder="1. ...\n2. ..."></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>严重程度</label>
              <select v-model="form.severity">
                <option value="critical">critical</option>
                <option value="high">high</option>
                <option value="medium">medium</option>
                <option value="low">low</option>
              </select>
            </div>
            <div class="form-group">
              <label>优先级</label>
              <select v-model="form.priority">
                <option value="P0">P0</option>
                <option value="P1">P1</option>
                <option value="P2">P2</option>
                <option value="P3">P3</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>状态</label>
              <select v-model="form.status">
                <option value="open">open</option>
                <option value="in_progress">in_progress</option>
                <option value="resolved">resolved</option>
                <option value="verified">verified</option>
                <option value="closed">closed</option>
                <option value="rejected">rejected</option>
              </select>
            </div>
            <div class="form-group">
              <label>负责人</label>
              <input v-model="form.current_assignee" type="text" placeholder="user_id" />
            </div>
          </div>
          <div v-if="formError" style="padding:10px;color:var(--signal);font-size:13px;background:rgba(239,68,68,0.08);border-radius: 0;">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="ghost" @click="closeForm">取消</button>
          <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '创建缺陷' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { listDefects, createDefect, updateDefect, listProjects, listRequirements } from '../api'

const items = ref([])
const projects = ref([])
const requirements = ref([])
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingId = ref(null)
const formError = ref('')
const filterProject = ref('')
const form = reactive({ project_id: '', requirement_id: '', title: '', reproduce_steps: '', severity: 'medium', priority: 'P2', status: 'open', current_assignee: '' })

onMounted(async () => {
  await loadProjects()
  await loadItems()
})

watch(filterProject, async () => { await loadItems() })
watch(() => form.project_id, async (pid) => {
  if (pid) {
    try {
      const { data } = await listRequirements(pid)
      requirements.value = data.items || []
    } catch { requirements.value = [] }
  } else { requirements.value = [] }
})

async function loadProjects() {
  try {
    const { data } = await listProjects()
    projects.value = data.items || []
  } catch { projects.value = [] }
}

async function loadItems() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await listDefects(filterProject.value || null)
    items.value = data.items || []
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

function editDefect(d) {
  editingId.value = d.defect_id
  Object.assign(form, {
    project_id: d.project_id, requirement_id: d.requirement_id, title: d.title,
    reproduce_steps: d.reproduce_steps || '', severity: d.severity, priority: d.priority,
    status: d.status, current_assignee: d.current_assignee || '',
  })
  showForm.value = true
  // Load requirements for this project
  listRequirements(d.project_id).then(r => { requirements.value = r.data.items || [] }).catch(() => {})
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
  Object.assign(form, { project_id: '', requirement_id: '', title: '', reproduce_steps: '', severity: 'medium', priority: 'P2', status: 'open', current_assignee: '' })
}

async function handleSubmit() {
  formError.value = ''
  try {
    if (editingId.value) {
      await updateDefect(editingId.value, form)
    } else {
      await createDefect(form)
    }
    closeForm()
    await loadItems()
  } catch (e) {
    formError.value = e.response?.data?.detail || '操作失败'
  }
}

function severityColor(s) {
  const map = { critical: 'chip-good', high: 'chip-accent', medium: 'chip-neutral', low: 'chip-neutral' }
  return map[s] || 'chip-neutral'
}
function statusColor(s) {
  const map = { open: 'chip-good', in_progress: 'chip-accent', resolved: 'chip-neutral', verified: 'chip-good', closed: 'chip-neutral', rejected: 'chip-neutral' }
  return map[s] || 'chip-neutral'
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: var(--bg-card); border-radius: 0; width: 520px; max-width: 90vw; box-shadow: none; max-height: 90vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(28,40,52,0.1); position: sticky; top: 0; background: var(--bg-card); }
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
