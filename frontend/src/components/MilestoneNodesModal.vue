<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <div>
          <h2>里程碑节点管理</h2>
          <div class="subhead">{{ milestone.name }}</div>
        </div>
        <button class="ghost" @click="$emit('close')">✕</button>
      </div>
      <div class="modal-body">
        <div v-if="error" class="error-banner">{{ error }}</div>
        <div class="layout">
          <div class="card section">
            <div class="section-header">
              <h4 class="card-kicker">节点列表</h4>
              <span class="chip chip-neutral">{{ items.length }} 条</span>
            </div>
            <div v-if="items.length" style="overflow:auto;">
              <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead>
                  <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
                    <th class="th">需求</th>
                    <th class="th">类型</th>
                    <th class="th">状态</th>
                    <th class="th">排序</th>
                    <th class="th">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in items" :key="item.snapshot_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
                    <td class="td strong">{{ item.title || item.requirement_title || item.requirement_id }}</td>
                    <td class="td">{{ item.requirement_type || '—' }}</td>
                    <td class="td">{{ item.status || '—' }}</td>
                    <td class="td">{{ item.order_index ?? 0 }}</td>
                    <td class="td">
                      <button class="ghost mini-btn" @click="editItem(item)">编辑</button>
                      <button class="ghost mini-btn danger" @click="handleDelete(item.snapshot_id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty">暂无快照节点</div>
          </div>

          <div class="card section">
            <div class="section-header">
              <h4 class="card-kicker">{{ editingId ? '编辑节点' : '新增节点' }}</h4>
            </div>
            <div class="form-group">
              <label>需求 *</label>
              <select v-model="form.requirement_id">
                <option value="">选择需求...</option>
                <option v-for="item in requirements" :key="item.req_id" :value="item.req_id">
                  {{ item.title }}
                </option>
              </select>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>需求类型</label>
                <input v-model="form.requirement_type" type="text" placeholder="top_level / low_level / task" />
              </div>
              <div class="form-group">
                <label>状态</label>
                <input v-model="form.status" type="text" placeholder="draft / confirmed / completed" />
              </div>
            </div>
            <div class="form-group">
              <label>快照标题</label>
              <input v-model="form.title" type="text" placeholder="默认沿用需求标题" />
            </div>
            <div class="form-group">
              <label>快照描述</label>
              <textarea v-model="form.description" rows="3" placeholder="可覆盖需求描述"></textarea>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>父需求 ID</label>
                <input v-model="form.parent_id" type="text" placeholder="可留空" />
              </div>
              <div class="form-group">
                <label>排序</label>
                <input v-model.number="form.order_index" type="number" min="0" />
              </div>
            </div>
            <div class="form-group">
              <label>快照 JSON</label>
              <textarea v-model="form.snapshot_json" rows="7" placeholder='{"note":"baseline snapshot"}'></textarea>
            </div>
            <div v-if="formError" class="error-inline">{{ formError }}</div>
            <div class="actions">
              <button class="ghost" @click="resetForm">重置</button>
              <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '添加节点' }}</button>
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
  listMilestoneNodes,
  createMilestoneNode,
  updateMilestoneNode,
  deleteMilestoneNode,
  listRequirements,
} from '../api'
import { parseJsonInput, stringifyJson } from '../utils/admin'

const props = defineProps({
  milestone: { type: Object, required: true },
})

defineEmits(['close'])

const items = ref([])
const requirements = ref([])
const error = ref('')
const editingId = ref(null)
const formError = ref('')
const form = reactive({
  requirement_id: '',
  requirement_type: '',
  status: '',
  title: '',
  description: '',
  parent_id: '',
  order_index: 0,
  snapshot_json: '{}',
})

watch(
  () => props.milestone.milestone_id,
  async () => {
    resetForm()
    await Promise.all([loadItems(), loadRequirements()])
  },
  { immediate: true }
)

async function loadItems() {
  error.value = ''
  try {
    const { data } = await listMilestoneNodes({ milestone_id: props.milestone.milestone_id })
    items.value = data.items || []
  } catch (err) {
    error.value = err.response?.data?.detail || '加载节点失败'
  }
}

async function loadRequirements() {
  try {
    const { data } = await listRequirements(props.milestone.project_id)
    requirements.value = data.items || []
  } catch {
    requirements.value = []
  }
}

function resetForm() {
  editingId.value = null
  formError.value = ''
  Object.assign(form, {
    requirement_id: '',
    requirement_type: '',
    status: '',
    title: '',
    description: '',
    parent_id: '',
    order_index: 0,
    snapshot_json: '{}',
  })
}

function editItem(item) {
  editingId.value = item.snapshot_id
  Object.assign(form, {
    requirement_id: item.requirement_id,
    requirement_type: item.requirement_type || '',
    status: item.status || '',
    title: item.title || '',
    description: item.description || '',
    parent_id: item.parent_id || '',
    order_index: item.order_index ?? 0,
    snapshot_json: stringifyJson(item.snapshot_data, '{}'),
  })
}

async function handleSubmit() {
  formError.value = ''
  let snapshotData = null
  try {
    snapshotData = parseJsonInput(form.snapshot_json, {})
  } catch {
    formError.value = '快照 JSON 格式无效'
    return
  }

  const payload = {
    milestone_id: props.milestone.milestone_id,
    requirement_id: form.requirement_id,
    requirement_type: form.requirement_type || null,
    status: form.status || null,
    title: form.title || null,
    description: form.description || null,
    parent_id: form.parent_id || null,
    order_index: Number(form.order_index || 0),
    snapshot_data: snapshotData,
  }

  try {
    if (editingId.value) {
      await updateMilestoneNode(editingId.value, payload)
    } else {
      await createMilestoneNode(payload)
    }
    resetForm()
    await loadItems()
  } catch (err) {
    formError.value = err.response?.data?.detail || '操作失败'
  }
}

async function handleDelete(id) {
  if (!confirm('确认删除此里程碑节点？')) return
  try {
    await deleteMilestoneNode(id)
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
.mini-btn { font-size:12px; padding:4px 8px; }
.danger { color:var(--signal); }
.form-group { display:flex; flex-direction:column; gap:6px; }
.form-group label { font-size:12px; color:rgba(28,40,52,0.6); font-weight:500; }
.form-group input, .form-group textarea, .form-group select { padding:8px 12px; border:1px solid rgba(28,40,52,0.2); border-radius:0; font-size:13px; background:rgba(28,40,52,0.02); }
.form-group textarea { resize:vertical; }
.form-row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.actions { display:flex; gap:12px; justify-content:flex-end; margin-top:auto; }
.empty { padding:24px; text-align:center; color:rgba(28,40,52,0.4); }
.error-banner, .error-inline { padding:10px 12px; color:var(--signal); background:rgba(239,68,68,0.08); font-size:13px; }
@media (max-width: 1000px) {
  .layout { grid-template-columns: 1fr; }
}
</style>
