<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <div>
          <h2>变更集管理</h2>
          <div class="subhead">{{ branch.name }}</div>
        </div>
        <button class="ghost" @click="$emit('close')">✕</button>
      </div>
      <div class="modal-body">
        <div v-if="error" class="error-banner">{{ error }}</div>
        <div class="layout">
          <div class="card section">
            <div class="section-header">
              <h4 class="card-kicker">变更列表</h4>
              <span class="chip chip-neutral">{{ items.length }} 条</span>
            </div>
            <div v-if="items.length" style="overflow:auto;">
              <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead>
                  <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
                    <th class="th">类型</th>
                    <th class="th">需求</th>
                    <th class="th">创建人</th>
                    <th class="th">创建时间</th>
                    <th class="th">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in items" :key="item.change_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
                    <td class="td"><span class="chip chip-neutral">{{ item.change_type }}</span></td>
                    <td class="td strong">{{ item.requirement_title || item.requirement_id || '—' }}</td>
                    <td class="td">{{ item.created_by || '—' }}</td>
                    <td class="td muted">{{ formatTime(item.created_at) }}</td>
                    <td class="td">
                      <button class="ghost mini-btn" @click="editItem(item)">编辑</button>
                      <button class="ghost mini-btn danger" @click="handleDelete(item.change_id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty">暂无变更集</div>
          </div>

          <div class="card section">
            <div class="section-header">
              <h4 class="card-kicker">{{ editingId ? '编辑变更集' : '新增变更集' }}</h4>
            </div>
            <div class="form-group">
              <label>变更类型</label>
              <select v-model="form.change_type">
                <option value="added">added</option>
                <option value="modified">modified</option>
                <option value="deleted">deleted</option>
                <option value="moved">moved</option>
              </select>
            </div>
            <div class="form-group">
              <label>关联需求</label>
              <select v-model="form.requirement_id">
                <option value="">— 无 —</option>
                <option v-for="item in requirements" :key="item.req_id" :value="item.req_id">
                  {{ item.title }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>变更前 JSON</label>
              <textarea v-model="form.before_json" rows="6" placeholder='{"title":"旧标题"}'></textarea>
            </div>
            <div class="form-group">
              <label>变更后 JSON</label>
              <textarea v-model="form.after_json" rows="6" placeholder='{"title":"新标题"}'></textarea>
            </div>
            <div class="form-group">
              <label>创建人</label>
              <input v-model="form.created_by" type="text" placeholder="user_id" />
            </div>
            <div v-if="formError" class="error-inline">{{ formError }}</div>
            <div class="actions">
              <button class="ghost" @click="resetForm">重置</button>
              <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '添加变更集' }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import {
  listChangeSets,
  createChangeSet,
  updateChangeSet,
  deleteChangeSet,
  listRequirements,
} from '../api'
import { formatTime, parseJsonInput, stringifyJson } from '../utils/admin'

const props = defineProps({
  branch: { type: Object, required: true },
})

defineEmits(['close'])

const items = ref([])
const requirements = ref([])
const error = ref('')
const editingId = ref(null)
const formError = ref('')
const form = reactive({
  change_type: 'modified',
  requirement_id: '',
  before_json: '{}',
  after_json: '{}',
  created_by: '',
})

watch(
  () => props.branch.branch_id,
  async () => {
    resetForm()
    await Promise.all([loadItems(), loadRequirements()])
  },
  { immediate: true }
)

async function loadItems() {
  error.value = ''
  try {
    const { data } = await listChangeSets({ branch_id: props.branch.branch_id })
    items.value = data.items || []
  } catch (err) {
    error.value = err.response?.data?.detail || '加载变更集失败'
  }
}

async function loadRequirements() {
  try {
    const { data } = await listRequirements(props.branch.project_id)
    requirements.value = data.items || []
  } catch {
    requirements.value = []
  }
}

function resetForm() {
  editingId.value = null
  formError.value = ''
  Object.assign(form, {
    change_type: 'modified',
    requirement_id: '',
    before_json: '{}',
    after_json: '{}',
    created_by: '',
  })
}

function editItem(item) {
  editingId.value = item.change_id
  Object.assign(form, {
    change_type: item.change_type,
    requirement_id: item.requirement_id || '',
    before_json: stringifyJson(item.before_data, '{}'),
    after_json: stringifyJson(item.after_data, '{}'),
    created_by: item.created_by || '',
  })
}

async function handleSubmit() {
  formError.value = ''
  let beforeData = null
  let afterData = null
  try {
    beforeData = parseJsonInput(form.before_json, {})
    afterData = parseJsonInput(form.after_json, {})
  } catch {
    formError.value = 'JSON 格式无效'
    return
  }

  const payload = {
    branch_id: props.branch.branch_id,
    change_type: form.change_type,
    requirement_id: form.requirement_id || null,
    before_data: beforeData,
    after_data: afterData,
    created_by: form.created_by || null,
  }
  try {
    if (editingId.value) {
      await updateChangeSet(editingId.value, payload)
    } else {
      await createChangeSet(payload)
    }
    resetForm()
    await loadItems()
  } catch (err) {
    formError.value = err.response?.data?.detail || '操作失败'
  }
}

async function handleDelete(id) {
  if (!confirm('确认删除此变更集？')) return
  try {
    await deleteChangeSet(id)
    if (editingId.value === id) resetForm()
    await loadItems()
  } catch (err) {
    error.value = err.response?.data?.detail || '删除失败'
  }
}
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 110; }
.modal { background: var(--bg-card); width: 1080px; max-width: 96vw; max-height: 90vh; overflow-y: auto; }
.modal-header { display:flex; justify-content:space-between; align-items:flex-start; padding:20px 24px; border-bottom:1px solid rgba(28,40,52,0.1); position:sticky; top:0; background:var(--bg-card); z-index:2; }
.modal-header h2 { margin:0; font-size:16px; }
.subhead { margin-top:6px; color:rgba(28,40,52,0.55); font-size:12px; }
.modal-body { padding:24px; }
.layout { display:grid; grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.8fr); gap:20px; }
.section { padding:20px; display:flex; flex-direction:column; gap:16px; }
.section-header { display:flex; justify-content:space-between; align-items:center; }
.th { padding:10px 12px; text-align:left; color:rgba(28,40,52,0.5); font-weight:500; }
.td { padding:10px 12px; }
.td.strong { font-weight:600; color:var(--accent); }
.td.muted { color:rgba(28,40,52,0.6); }
.mini-btn { font-size:12px; padding:4px 8px; }
.danger { color:var(--signal); }
.form-group { display:flex; flex-direction:column; gap:6px; }
.form-group label { font-size:12px; color:rgba(28,40,52,0.6); font-weight:500; }
.form-group input, .form-group textarea, .form-group select { padding:8px 12px; border:1px solid rgba(28,40,52,0.2); border-radius:0; font-size:13px; background:rgba(28,40,52,0.02); }
.form-group textarea { resize:vertical; }
.actions { display:flex; gap:12px; justify-content:flex-end; margin-top:auto; }
.empty { padding:24px; text-align:center; color:rgba(28,40,52,0.4); }
.error-banner, .error-inline { padding:10px 12px; color:var(--signal); background:rgba(239,68,68,0.08); font-size:13px; }
@media (max-width: 1000px) {
  .layout { grid-template-columns: 1fr; }
}
</style>
