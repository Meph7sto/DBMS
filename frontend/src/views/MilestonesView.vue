<template>
  <div class="page" style="display:flex;flex-direction:column;gap:20px;height:100%;overflow-y:auto;padding-right:8px;">
    <div class="page-header">
      <h1 style="margin:0;font-size:20px;color:var(--near-black);">里程碑管理</h1>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <select v-model="filterProject" class="filter-select">
          <option value="">全部项目</option>
          <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
            {{ project.name }}
          </option>
        </select>
        <button class="btn-brand" @click="showForm = true">+ 新建里程碑</button>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="items.length" class="card wide anim-slide" style="overflow:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
            <th class="th">名称</th>
            <th class="th">项目</th>
            <th class="th">类型</th>
            <th class="th">基线</th>
            <th class="th">版本</th>
            <th class="th">创建时间</th>
            <th class="th">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.milestone_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
            <td class="td strong">{{ item.name }}</td>
            <td class="td">{{ item.project_name || item.project_id }}</td>
            <td class="td"><span class="chip chip-neutral">{{ item.milestone_type }}</span></td>
            <td class="td">
              <span :class="['chip', item.is_baseline ? 'chip-good' : 'chip-neutral']">
                {{ item.is_baseline ? 'baseline' : 'normal' }}
              </span>
            </td>
            <td class="td">{{ item.version || '—' }}</td>
            <td class="td muted">{{ formatTime(item.created_at) }}</td>
            <td class="td">
              <button class="ghost mini-btn" @click="editItem(item)">编辑</button>
              <button class="ghost mini-btn" @click="openNodes(item)">节点</button>
              <button class="ghost mini-btn danger" @click="handleDelete(item.milestone_id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="!loading" class="empty">暂无里程碑数据</div>
    <div v-if="loading" class="loading">加载中...</div>

    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingId ? '编辑里程碑' : '新建里程碑' }}</h2>
          <button class="ghost" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>所属项目 *</label>
            <select v-model="form.project_id" :disabled="!!editingId">
              <option value="">选择项目...</option>
              <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
                {{ project.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>里程碑名称 *</label>
            <input v-model="form.name" type="text" placeholder="如：R1 冻结基线" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="form.description" rows="3" placeholder="描述里程碑目标、范围和说明"></textarea>
          </div>
          <div class="form-group">
            <label>消息</label>
            <input v-model="form.message" type="text" placeholder="如：完成核心需求冻结" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>类型</label>
              <select v-model="form.milestone_type">
                <option value="regular">regular</option>
                <option value="baseline">baseline</option>
                <option value="branch">branch</option>
                <option value="merge">merge</option>
              </select>
            </div>
            <div class="form-group">
              <label>版本</label>
              <input v-model="form.version" type="text" placeholder="如：v1.0" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>迭代</label>
              <input v-model="form.sprint" type="text" placeholder="如：Sprint 4" />
            </div>
            <label class="check-row">
              <input v-model="form.is_baseline" type="checkbox" />
              <span>标记为基线</span>
            </label>
          </div>
          <div class="form-group">
            <label>创建人</label>
            <input v-model="form.created_by" type="text" placeholder="user_id" />
          </div>
          <div v-if="formError" class="error-inline">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="ghost" @click="closeForm">取消</button>
          <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '创建里程碑' }}</button>
        </div>
      </div>
    </div>

    <MilestoneNodesModal
      v-if="activeMilestone"
      :milestone="activeMilestone"
      @close="activeMilestone = null"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import {
  listProjects,
  listMilestones,
  createMilestone,
  updateMilestone,
  deleteMilestone,
} from '../api'
import MilestoneNodesModal from '../components/MilestoneNodesModal.vue'
import { formatTime } from '../utils/admin'

const items = ref([])
const projects = ref([])
const loading = ref(false)
const error = ref('')
const filterProject = ref('')
const showForm = ref(false)
const editingId = ref(null)
const formError = ref('')
const activeMilestone = ref(null)
const form = reactive({
  project_id: '',
  name: '',
  description: '',
  message: '',
  milestone_type: 'regular',
  is_baseline: false,
  sprint: '',
  version: '',
  created_by: '',
})

onMounted(async () => {
  await Promise.all([loadItems(), loadProjects()])
})

watch(filterProject, async () => {
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

async function loadItems() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await listMilestones(filterProject.value || null)
    items.value = data.items || []
  } catch (err) {
    error.value = err.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

function editItem(item) {
  editingId.value = item.milestone_id
  Object.assign(form, {
    project_id: item.project_id,
    name: item.name,
    description: item.description || '',
    message: item.message || '',
    milestone_type: item.milestone_type,
    is_baseline: !!item.is_baseline,
    sprint: item.sprint || '',
    version: item.version || '',
    created_by: item.created_by || '',
  })
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
  Object.assign(form, {
    project_id: '',
    name: '',
    description: '',
    message: '',
    milestone_type: 'regular',
    is_baseline: false,
    sprint: '',
    version: '',
    created_by: '',
  })
}

async function handleSubmit() {
  formError.value = ''
  const payload = { ...form }
  try {
    if (editingId.value) {
      await updateMilestone(editingId.value, {
        name: payload.name,
        description: payload.description,
        message: payload.message,
        milestone_type: payload.milestone_type,
        is_baseline: payload.is_baseline,
        sprint: payload.sprint,
        version: payload.version,
      })
    } else {
      await createMilestone(payload)
    }
    closeForm()
    await loadItems()
  } catch (err) {
    formError.value = err.response?.data?.detail || '操作失败'
  }
}

function openNodes(item) {
  activeMilestone.value = item
}

async function handleDelete(id) {
  if (!confirm('确认删除此里程碑？')) return
  try {
    await deleteMilestone(id)
    if (activeMilestone.value?.milestone_id === id) activeMilestone.value = null
    await loadItems()
  } catch (err) {
    error.value = err.response?.data?.detail || '删除失败'
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
.check-row { display:flex; align-items:center; gap:10px; font-size:13px; color:rgba(28,40,52,0.75); }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: var(--bg-card); border-radius: 0; width: 580px; max-width: 92vw; max-height: 90vh; overflow-y: auto; }
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
