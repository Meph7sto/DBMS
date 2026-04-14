<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <div>
          <h2>{{ title }}</h2>
          <div class="subhead">{{ entityName }}</div>
        </div>
        <button class="ghost" @click="$emit('close')">✕</button>
      </div>
      <div class="modal-body">
        <div v-if="error" class="error-banner">{{ error }}</div>
        <div class="layout">
          <div class="card section">
            <div class="section-header">
              <h4 class="card-kicker">成员列表</h4>
              <span class="chip chip-neutral">{{ items.length }} 条</span>
            </div>
            <div v-if="items.length" style="overflow:auto;">
              <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead>
                  <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
                    <th class="th">用户</th>
                    <th class="th">角色</th>
                    <th class="th">更新时间</th>
                    <th class="th">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in items" :key="item.id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
                    <td class="td strong">{{ item.user_id }}</td>
                    <td class="td"><span class="chip chip-neutral">{{ item.role }}</span></td>
                    <td class="td muted">{{ formatTime(item.updated_at || item.created_at) }}</td>
                    <td class="td">
                      <button class="ghost mini-btn" @click="editItem(item)">编辑</button>
                      <button class="ghost mini-btn danger" @click="handleDelete(item.id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty">暂无成员</div>
          </div>

          <div class="card section">
            <div class="section-header">
              <h4 class="card-kicker">{{ editingId ? '编辑成员' : '新增成员' }}</h4>
            </div>
            <div class="form-group">
              <label>用户 ID *</label>
              <input v-model="form.user_id" type="text" placeholder="如：alice" />
            </div>
            <div class="form-group">
              <label>角色</label>
              <select v-model="form.role">
                <option value="owner">owner</option>
                <option value="admin">admin</option>
                <option value="member">member</option>
                <option value="viewer">viewer</option>
              </select>
            </div>
            <div v-if="formError" class="error-inline">{{ formError }}</div>
            <div class="actions">
              <button class="ghost" @click="resetForm">重置</button>
              <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '添加成员' }}</button>
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
  listProductMembers,
  createProductMember,
  updateProductMember,
  deleteProductMember,
  listProjectMembers,
  createProjectMember,
  updateProjectMember,
  deleteProjectMember,
} from '../api'
import { formatTime } from '../utils/admin'

const props = defineProps({
  mode: { type: String, required: true },
  entityId: { type: String, required: true },
  entityName: { type: String, default: '' },
})

defineEmits(['close'])

const items = ref([])
const error = ref('')
const formError = ref('')
const editingId = ref(null)
const form = reactive({
  user_id: '',
  role: 'member',
})

watch(
  () => [props.mode, props.entityId],
  async () => {
    resetForm()
    await loadItems()
  },
  { immediate: true }
)

const title = props.mode === 'product' ? '产品成员管理' : '项目成员管理'

function apiSet() {
  if (props.mode === 'product') {
    return {
      list: () => listProductMembers(props.entityId),
      create: (payload) => createProductMember({ product_id: props.entityId, ...payload }),
      update: (id, payload) => updateProductMember(id, payload),
      remove: (id) => deleteProductMember(id),
    }
  }
  return {
    list: () => listProjectMembers(props.entityId),
    create: (payload) => createProjectMember({ project_id: props.entityId, ...payload }),
    update: (id, payload) => updateProjectMember(id, payload),
    remove: (id) => deleteProjectMember(id),
  }
}

async function loadItems() {
  error.value = ''
  try {
    const { data } = await apiSet().list()
    items.value = data.items || []
  } catch (err) {
    error.value = err.response?.data?.detail || '加载成员失败'
  }
}

function editItem(item) {
  editingId.value = item.id
  form.user_id = item.user_id
  form.role = item.role
}

function resetForm() {
  editingId.value = null
  formError.value = ''
  form.user_id = ''
  form.role = 'member'
}

async function handleSubmit() {
  formError.value = ''
  try {
    if (editingId.value) {
      await apiSet().update(editingId.value, { user_id: form.user_id, role: form.role })
    } else {
      await apiSet().create({ user_id: form.user_id, role: form.role })
    }
    resetForm()
    await loadItems()
  } catch (err) {
    formError.value = err.response?.data?.detail || '操作失败'
  }
}

async function handleDelete(id) {
  if (!confirm('确认删除此成员？')) return
  try {
    await apiSet().remove(id)
    if (editingId.value === id) resetForm()
    await loadItems()
  } catch (err) {
    error.value = err.response?.data?.detail || '删除失败'
  }
}
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 110; }
.modal { background: var(--bg-card); width: 900px; max-width: 94vw; max-height: 90vh; overflow-y: auto; }
.modal-header { display:flex; justify-content:space-between; align-items:flex-start; padding:20px 24px; border-bottom:1px solid rgba(28,40,52,0.1); position:sticky; top:0; background:var(--bg-card); z-index:1; }
.modal-header h2 { margin:0; font-size:16px; }
.subhead { margin-top:6px; color:rgba(28,40,52,0.55); font-size:12px; }
.modal-body { padding:24px; }
.layout { display:grid; grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.8fr); gap:20px; }
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
.form-group input, .form-group select { padding:8px 12px; border:1px solid rgba(28,40,52,0.2); border-radius:0; font-size:13px; background:rgba(28,40,52,0.02); }
.actions { display:flex; gap:12px; justify-content:flex-end; margin-top:auto; }
.empty { padding:24px; text-align:center; color:rgba(28,40,52,0.4); }
.error-banner, .error-inline { padding:10px 12px; color:var(--signal); background:rgba(239,68,68,0.08); font-size:13px; }
@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
}
</style>
