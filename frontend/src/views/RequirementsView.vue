<template>
  <div class="page" style="display:flex;flex-direction:column;gap:20px;height:100%;overflow-y:auto;padding-right:8px;">
    <div class="page-header" style="justify-content: space-between; align-items: center;">
      <h1 style="margin: 0; font-size: 20px; color: var(--near-black);">需求列表</h1>
      <div style="display:flex;gap:10px;align-items:center;">
        <select v-model="filterProject" style="padding: 0 12px; border: 1px solid rgba(28,40,52,0.2); border-radius: 0; font-size: 14px; background: rgba(28,40,52,0.02); height: 36px; outline: none; box-sizing: border-box;">
          <option value="">全部项目</option>
          <option v-for="p in projects" :key="p.project_id" :value="p.project_id">{{ p.name }}</option>
        </select>
        <button class="btn-brand" @click="showForm = true">+ 新建需求</button>
      </div>
    </div>

    <div v-if="error" style="padding:12px 16px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius: 0;color:var(--signal);font-size:13px;">{{ error }}</div>

    <!-- Ribbon -->
    <div class="ribbon">
      <button v-for="v in ['table', 'tree']" :key="v" :class="['ribbon-step', { active: view === v }]" @click="view = v">{{ v === 'table' ? '表格视图' : '树形视图' }}</button>
    </div>

    <!-- Table View -->
    <div v-if="view === 'table' && items.length" class="card wide anim-slide" style="overflow:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">需求信息</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">类型</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">状态</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">优先级</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">负责人</th>
            <th style="padding:10px 12px;text-align:left;color:rgba(28,40,52,0.5);font-weight:500;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in items" :key="r.req_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
            <td style="padding:10px 12px;min-width:300px;">
              <div style="display:flex;flex-direction:column;gap:6px;">
                <div style="font-weight:600;color:var(--accent)">{{ r.title }}</div>
                <div style="font-family:monospace;font-size:12px;color:rgba(28,40,52,0.55)">{{ r.req_id }}</div>
                <div style="color:rgba(28,40,52,0.68);line-height:1.45;">{{ r.description || '—' }}</div>
                <details style="margin-top:2px;">
                  <summary style="cursor:pointer;font-size:12px;color:rgba(28,40,52,0.55);">完整字段</summary>
                  <pre style="margin:8px 0 0;white-space:pre-wrap;word-break:break-all;font-size:11px;line-height:1.45;color:rgba(28,40,52,0.72);">{{ stringifyRecord(r) }}</pre>
                </details>
              </div>
            </td>
            <td style="padding:10px 12px;"><span class="chip chip-neutral">{{ r.requirement_type }}</span></td>
            <td style="padding:10px 12px;"><span :class="['chip', statusColor(r.status)]">{{ r.status }}</span></td>
            <td style="padding:10px 12px;"><span :class="['chip', priorityColor(r.priority)]">{{ r.priority || '—' }}</span></td>
            <td style="padding:10px 12px;">{{ r.assignee || '—' }}</td>
            <td style="padding:10px 12px;">
              <button class="ghost" style="font-size:12px;padding:4px 8px;" @click="editReq(r)">编辑</button>
              <button class="ghost" style="font-size:12px;padding:4px 8px;" @click="openRelations(r)">关联</button>
              <button class="ghost" style="font-size:12px;padding:4px 8px;color:var(--signal);" @click="handleDelete(r.req_id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Tree View -->
    <div v-else-if="view === 'tree'" class="anim-slide" style="display:flex;flex-direction:column;gap:8px;">
      <div v-for="r in treeItems" :key="r.req_id" class="tree-node card" :style="{ marginLeft: (r.depth * 24) + 'px' }">
        <div style="display:flex;align-items:center;gap:10px;padding:10px 14px;">
          <span v-if="r.children && r.children.length" @click="toggleNode(r.req_id)" style="cursor:pointer;color:rgba(28,40,52,0.4);font-size:10px;">{{ expanded[r.req_id] ? '▼' : '▶' }}</span>
          <span v-else style="width:10px;"></span>
          <span style="display:flex;flex-direction:column;gap:2px;flex:1;">
            <span style="font-weight:600;color:var(--accent);">{{ r.title }}</span>
            <span style="font-family:monospace;font-size:11px;color:rgba(28,40,52,0.52);">{{ r.req_id }}</span>
          </span>
          <span class="chip chip-neutral" style="font-size:11px;">{{ r.requirement_type }}</span>
          <span :class="['chip', statusColor(r.status)]" style="font-size:11px;">{{ r.status }}</span>
          <button class="ghost" style="font-size:11px;padding:2px 6px;" @click="editReq(r)">编辑</button>
          <button class="ghost" style="font-size:11px;padding:2px 6px;" @click="openRelations(r)">关联</button>
          <button class="ghost" style="font-size:11px;padding:2px 6px;color:var(--signal);" @click="handleDelete(r.req_id)">✕</button>
        </div>
        <div v-if="expanded[r.req_id] && r.children">
          <div v-for="child in r.children" :key="child.req_id" class="tree-node" :style="{ marginLeft: ((child.depth || r.depth + 1) * 24) + 'px' }">
            <div style="display:flex;align-items:center;gap:10px;padding:8px 14px;border-top:1px solid rgba(28,40,52,0.06);">
              <span style="width:10px;"></span>
              <span style="display:flex;flex-direction:column;gap:2px;flex:1;">
                <span style="font-weight:500;color:var(--accent);">{{ child.title }}</span>
                <span style="font-family:monospace;font-size:11px;color:rgba(28,40,52,0.52);">{{ child.req_id }}</span>
              </span>
              <span class="chip chip-neutral" style="font-size:11px;">{{ child.requirement_type }}</span>
              <span :class="['chip', statusColor(child.status)]" style="font-size:11px;">{{ child.status }}</span>
              <button class="ghost" style="font-size:11px;padding:2px 6px;" @click="editReq(child)">编辑</button>
              <button class="ghost" style="font-size:11px;padding:2px 6px;" @click="openRelations(child)">关联</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!loading && items.length === 0" style="padding:40px;text-align:center;color:rgba(28,40,52,0.4)">暂无需求数据</div>
    <div v-if="loading" style="padding:20px;text-align:center;color:rgba(28,40,52,0.4)">加载中...</div>

    <!-- Form Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingId ? '编辑需求' : '新建需求' }}</h2>
          <button class="ghost" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="editingId" class="form-group">
            <label>需求 ID</label>
            <input :value="editingId" type="text" readonly />
          </div>
          <div class="form-group">
            <label>所属项目 *</label>
            <select v-model="form.project_id" :disabled="!!editingId">
              <option value="">选择项目...</option>
              <option v-for="p in projects" :key="p.project_id" :value="p.project_id">{{ p.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>需求标题 *</label>
            <input v-model="form.title" type="text" placeholder="需求标题" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>需求类型</label>
              <select v-model="form.requirement_type">
                <option value="top_level">top_level</option>
                <option value="low_level">low_level</option>
                <option value="task">task</option>
              </select>
            </div>
            <div class="form-group">
              <label>优先级</label>
              <select v-model="form.priority">
                <option value="">—</option>
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>状态</label>
              <select v-model="form.status">
                <option value="draft">draft</option>
                <option value="under_review">under_review</option>
                <option value="confirmed">confirmed</option>
                <option value="in_progress">in_progress</option>
                <option value="completed">completed</option>
                <option value="archived">archived</option>
              </select>
            </div>
            <div class="form-group">
              <label>负责人</label>
              <input v-model="form.assignee" type="text" placeholder="user_id" />
            </div>
          </div>
          <div class="form-group">
            <label>父需求</label>
            <select v-model="form.parent_id">
              <option value="">— 无父需求 —</option>
              <option v-for="r in allRequirements" :key="r.req_id" :value="r.req_id">{{ r.title }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="form.description" rows="3" placeholder="需求详细描述..."></textarea>
          </div>
          <div v-if="formError" style="padding:10px;color:var(--signal);font-size:13px;background:rgba(239,68,68,0.08);border-radius: 0;">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="ghost" @click="closeForm">取消</button>
          <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '创建需求' }}</button>
        </div>
      </div>
    </div>

    <RequirementRelationsModal
      v-if="activeRequirement"
      :requirement="activeRequirement"
      @close="activeRequirement = null"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { listRequirements, createRequirement, updateRequirement, deleteRequirement, listProjects } from '../api'
import RequirementRelationsModal from '../components/RequirementRelationsModal.vue'

const items = ref([])
const projects = ref([])
const allRequirements = ref([])
const loading = ref(false)
const error = ref('')
const view = ref('table')
const expanded = reactive({})
const showForm = ref(false)
const editingId = ref(null)
const formError = ref('')
const filterProject = ref('')
const activeRequirement = ref(null)
const form = reactive({ project_id: '', title: '', requirement_type: 'top_level', status: 'draft', priority: '', assignee: '', parent_id: '', description: '' })

onMounted(async () => {
  await loadItems()
  loadProjects()
})

watch(filterProject, async () => { await loadItems() })

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
    const { data } = await listRequirements(filterProject.value || null)
    items.value = data.items || []
    allRequirements.value = items.value
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

function buildTree(flat, parentId = null, depth = 0) {
  return flat
    .filter(r => r.parent_id === parentId)
    .map(r => ({
      ...r,
      depth,
      children: buildTree(flat, r.req_id, depth + 1),
    }))
}

const treeItems = computed(() => buildTree(items.value))

function toggleNode(id) {
  expanded[id] = !expanded[id]
}

function editReq(r) {
  editingId.value = r.req_id
  Object.assign(form, {
    project_id: r.project_id, title: r.title, requirement_type: r.requirement_type,
    status: r.status, priority: r.priority || '', assignee: r.assignee || '',
    parent_id: r.parent_id || '', description: r.description || '',
  })
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
  Object.assign(form, { project_id: '', title: '', requirement_type: 'top_level', status: 'draft', priority: '', assignee: '', parent_id: '', description: '' })
}

async function handleSubmit() {
  formError.value = ''
  try {
    if (editingId.value) {
      await updateRequirement(editingId.value, form)
    } else {
      await createRequirement(form)
    }
    closeForm()
    await loadItems()
  } catch (e) {
    formError.value = e.response?.data?.detail || '操作失败'
  }
}

async function handleDelete(id) {
  if (!confirm('确认删除此需求（软删除）？')) return
  try {
    await deleteRequirement(id)
    await loadItems()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除失败'
  }
}

function statusColor(s) {
  const map = { draft: 'chip-neutral', under_review: 'chip-accent', confirmed: 'chip-good', in_progress: 'chip-accent', completed: 'chip-good', archived: 'chip-neutral' }
  return map[s] || 'chip-neutral'
}
function priorityColor(p) {
  const map = { low: 'chip-neutral', medium: 'chip-accent', high: 'chip-good' }
  return map[p] || 'chip-neutral'
}

function stringifyRecord(record) {
  try {
    return JSON.stringify(record, null, 2)
  } catch {
    return '{}'
  }
}

function openRelations(requirement) {
  activeRequirement.value = requirement
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; }
.tree-node { border-radius: 0; overflow: hidden; }
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
