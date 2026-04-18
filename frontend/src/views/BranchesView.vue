<template>
  <div class="page" style="display:flex;flex-direction:column;gap:20px;height:100%;overflow-y:auto;padding-right:8px;">
    <div class="page-header">
      <h1 style="margin:0;font-size:20px;color:var(--near-black);">分支管理</h1>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <select v-model="filterProject" class="filter-select">
          <option value="">全部项目</option>
          <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
            {{ project.name }}
          </option>
        </select>
        <button class="btn-brand" @click="showForm = true">+ 新建分支</button>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="items.length" class="card wide anim-slide" style="overflow:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
            <th class="th">分支信息</th>
            <th class="th">项目</th>
            <th class="th">基线里程碑</th>
            <th class="th">状态</th>
            <th class="th">创建人</th>
            <th class="th">创建时间</th>
            <th class="th">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.branch_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
            <td class="td" style="min-width:300px;">
              <div style="display:flex;flex-direction:column;gap:6px;">
                <div class="td strong" style="padding:0;">{{ item.name }}</div>
                <div style="font-family:monospace;font-size:12px;color:rgba(28,40,52,0.55)">{{ item.branch_id }}</div>
                <details style="margin-top:2px;">
                  <summary style="cursor:pointer;font-size:12px;color:rgba(28,40,52,0.55);">完整字段</summary>
                  <pre style="margin:8px 0 0;white-space:pre-wrap;word-break:break-all;font-size:11px;line-height:1.45;color:rgba(28,40,52,0.72);">{{ stringifyRecord(item) }}</pre>
                </details>
              </div>
            </td>
            <td class="td">{{ item.project_name || item.project_id }}</td>
            <td class="td">{{ item.base_milestone_name || item.base_milestone_id }}</td>
            <td class="td"><span :class="['chip', statusColor(item.status)]">{{ item.status }}</span></td>
            <td class="td">{{ item.created_by || '—' }}</td>
            <td class="td muted">{{ formatTime(item.created_at) }}</td>
            <td class="td">
              <button class="ghost mini-btn" @click="editItem(item)">编辑</button>
              <button class="ghost mini-btn" @click="openChangeSets(item)">变更集</button>
              <button class="ghost mini-btn danger" @click="handleDelete(item.branch_id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="!loading" class="empty">暂无分支数据</div>
    <div v-if="loading" class="loading">加载中...</div>

    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingId ? '编辑分支' : '新建分支' }}</h2>
          <button class="ghost" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="editingId" class="form-group">
            <label>分支 ID</label>
            <input :value="editingId" type="text" readonly />
          </div>
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
            <label>基线里程碑 *</label>
            <select v-model="form.base_milestone_id">
              <option value="">选择里程碑...</option>
              <option v-for="item in projectMilestones" :key="item.milestone_id" :value="item.milestone_id">
                {{ item.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>分支名称 *</label>
            <input v-model="form.name" type="text" placeholder="如：feature/payment-redesign" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>状态</label>
              <select v-model="form.status">
                <option value="active">active</option>
                <option value="under_review">under_review</option>
                <option value="merged">merged</option>
                <option value="closed">closed</option>
              </select>
            </div>
            <div class="form-group">
              <label>创建人</label>
              <input v-model="form.created_by" type="text" placeholder="user_id" />
            </div>
          </div>
          <div class="form-group">
            <label>元数据 JSON</label>
            <textarea v-model="form.metadata_json" rows="7" placeholder='{"owner":"team-a"}'></textarea>
          </div>
          <div v-if="formError" class="error-inline">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="ghost" @click="closeForm">取消</button>
          <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '创建分支' }}</button>
        </div>
      </div>
    </div>

    <ChangeSetsModal
      v-if="activeBranch"
      :branch="activeBranch"
      @close="activeBranch = null"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  listProjects,
  listMilestones,
  listBranches,
  createBranch,
  updateBranch,
  deleteBranch,
} from '../api'
import ChangeSetsModal from '../components/ChangeSetsModal.vue'
import { formatTime, parseJsonInput, stringifyJson } from '../utils/admin'

const items = ref([])
const projects = ref([])
const milestones = ref([])
const loading = ref(false)
const error = ref('')
const filterProject = ref('')
const showForm = ref(false)
const editingId = ref(null)
const formError = ref('')
const activeBranch = ref(null)
const form = reactive({
  project_id: '',
  base_milestone_id: '',
  name: '',
  status: 'active',
  created_by: '',
  metadata_json: '{}',
})

onMounted(async () => {
  await Promise.all([loadItems(), loadProjects(), loadMilestones()])
})

watch(filterProject, async () => {
  await loadItems()
})

watch(
  () => form.project_id,
  async (projectId) => {
    if (!projectId) return
    await loadMilestones(projectId)
  }
)

const projectMilestones = computed(() =>
  milestones.value.filter((item) => item.project_id === form.project_id)
)

async function loadProjects() {
  try {
    const { data } = await listProjects()
    projects.value = data.items || []
  } catch {
    projects.value = []
  }
}

async function loadMilestones(projectId = null) {
  try {
    const { data } = await listMilestones(projectId)
    if (projectId) {
      const map = new Map(milestones.value.map((item) => [item.milestone_id, item]))
      ;(data.items || []).forEach((item) => map.set(item.milestone_id, item))
      milestones.value = Array.from(map.values())
    } else {
      milestones.value = data.items || []
    }
  } catch {
    if (!projectId) milestones.value = []
  }
}

async function loadItems() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await listBranches(filterProject.value || null)
    items.value = data.items || []
  } catch (err) {
    error.value = err.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

async function editItem(item) {
  editingId.value = item.branch_id
  Object.assign(form, {
    project_id: item.project_id,
    base_milestone_id: item.base_milestone_id,
    name: item.name,
    status: item.status,
    created_by: item.created_by || '',
    metadata_json: stringifyJson(item.metadata, '{}'),
  })
  await loadMilestones(item.project_id)
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
  Object.assign(form, {
    project_id: '',
    base_milestone_id: '',
    name: '',
    status: 'active',
    created_by: '',
    metadata_json: '{}',
  })
}

async function handleSubmit() {
  formError.value = ''
  let metadata = null
  try {
    metadata = parseJsonInput(form.metadata_json, {})
  } catch {
    formError.value = '元数据 JSON 格式无效'
    return
  }
  const payload = {
    project_id: form.project_id,
    base_milestone_id: form.base_milestone_id,
    name: form.name,
    status: form.status,
    metadata,
    created_by: form.created_by || null,
  }
  try {
    if (editingId.value) {
      await updateBranch(editingId.value, payload)
    } else {
      await createBranch(payload)
    }
    closeForm()
    await loadItems()
  } catch (err) {
    formError.value = err.response?.data?.detail || '操作失败'
  }
}

function openChangeSets(item) {
  activeBranch.value = item
}

async function handleDelete(id) {
  if (!confirm('确认删除此分支？')) return
  try {
    await deleteBranch(id)
    if (activeBranch.value?.branch_id === id) activeBranch.value = null
    await loadItems()
  } catch (err) {
    error.value = err.response?.data?.detail || '删除失败'
  }
}

function statusColor(status) {
  const map = {
    active: 'chip-good',
    under_review: 'chip-accent',
    merged: 'chip-neutral',
    closed: 'chip-neutral',
  }
  return map[status] || 'chip-neutral'
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
.modal { background: var(--bg-card); border-radius: 0; width: 620px; max-width: 92vw; max-height: 90vh; overflow-y: auto; }
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
