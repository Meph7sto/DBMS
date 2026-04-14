<template>
  <div class="page" style="display:flex;flex-direction:column;gap:20px;height:100%;overflow-y:auto;padding-right:8px;">
    <div class="page-header">
      <h1 style="margin:0;font-size:20px;color:var(--near-black);">评论管理</h1>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <select v-model="filterProject" class="filter-select">
          <option value="">全部项目</option>
          <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
            {{ project.name }}
          </option>
        </select>
        <button class="btn-brand" @click="showForm = true">+ 新建评论</button>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="items.length" class="card wide anim-slide" style="overflow:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead>
          <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
            <th class="th">项目</th>
            <th class="th">目标</th>
            <th class="th">作者</th>
            <th class="th">内容</th>
            <th class="th">状态</th>
            <th class="th">创建时间</th>
            <th class="th">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.comment_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
            <td class="td">{{ item.project_name || item.project_id }}</td>
            <td class="td">
              <span class="chip chip-neutral">{{ item.target_type }}</span>
              <span style="margin-left:6px;color:rgba(28,40,52,0.65)">{{ item.target_id }}</span>
            </td>
            <td class="td strong">{{ item.created_by }}</td>
            <td class="td">{{ truncateText(item.content, 48) }}</td>
            <td class="td">
              <span :class="['chip', item.deleted ? 'chip-accent' : 'chip-good']">
                {{ item.deleted ? 'deleted' : 'active' }}
              </span>
            </td>
            <td class="td muted">{{ formatTime(item.created_at) }}</td>
            <td class="td">
              <button class="ghost mini-btn" @click="editItem(item)">编辑</button>
              <button class="ghost mini-btn danger" @click="handleDelete(item.comment_id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="!loading" class="empty">暂无评论数据</div>
    <div v-if="loading" class="loading">加载中...</div>

    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingId ? '编辑评论' : '新建评论' }}</h2>
          <button class="ghost" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>所属项目 *</label>
            <select v-model="form.project_id">
              <option value="">选择项目...</option>
              <option v-for="project in projects" :key="project.project_id" :value="project.project_id">
                {{ project.name }}
              </option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>目标类型 *</label>
              <select v-model="form.target_type">
                <option value="requirement">requirement</option>
                <option value="defect">defect</option>
                <option value="test_case">test_case</option>
                <option value="milestone">milestone</option>
              </select>
            </div>
            <div class="form-group">
              <label>目标对象 *</label>
              <select v-model="form.target_id">
                <option value="">选择目标...</option>
                <option v-for="item in targetOptions" :key="item.id" :value="item.id">
                  {{ item.label }}
                </option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>评论内容 *</label>
            <textarea v-model="form.content" rows="5" placeholder="输入评论内容"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>回复评论</label>
              <select v-model="form.reply_to_id">
                <option value="">— 无 —</option>
                <option v-for="item in replyOptions" :key="item.comment_id" :value="item.comment_id">
                  {{ item.created_by }}: {{ truncateText(item.content, 24) }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>创建人 *</label>
              <input v-model="form.created_by" type="text" placeholder="user_id" />
            </div>
          </div>
          <label class="check-row">
            <input v-model="form.deleted" type="checkbox" />
            <span>标记为已删除</span>
          </label>
          <div v-if="formError" class="error-inline">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="ghost" @click="closeForm">取消</button>
          <button class="primary" @click="handleSubmit">{{ editingId ? '保存修改' : '创建评论' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  listComments,
  createComment,
  updateComment,
  deleteComment,
  listProjects,
  listRequirements,
  listDefects,
  listTestCases,
  listMilestones,
} from '../api'
import { formatTime, truncateText } from '../utils/admin'

const items = ref([])
const projects = ref([])
const requirements = ref([])
const defects = ref([])
const testCases = ref([])
const milestones = ref([])
const loading = ref(false)
const error = ref('')
const filterProject = ref('')
const showForm = ref(false)
const editingId = ref(null)
const formError = ref('')
const form = reactive({
  project_id: '',
  target_type: 'requirement',
  target_id: '',
  content: '',
  reply_to_id: '',
  created_by: '',
  deleted: false,
})

onMounted(async () => {
  await Promise.all([loadItems(), loadProjects()])
})

watch(filterProject, async () => {
  await loadItems()
})

watch(
  () => form.project_id,
  async (projectId) => {
    if (!projectId) {
      requirements.value = []
      defects.value = []
      testCases.value = []
      milestones.value = []
      return
    }
    await loadTargetData(projectId)
  }
)

watch(
  () => form.target_type,
  () => {
    form.target_id = ''
  }
)

const targetOptions = computed(() => {
  const map = {
    requirement: requirements.value.map((item) => ({ id: item.req_id, label: item.title })),
    defect: defects.value.map((item) => ({ id: item.defect_id, label: item.title })),
    test_case: testCases.value.map((item) => ({ id: item.test_case_id, label: item.title })),
    milestone: milestones.value.map((item) => ({ id: item.milestone_id, label: item.name })),
  }
  return map[form.target_type] || []
})

const replyOptions = computed(() =>
  items.value.filter(
    (item) =>
      item.project_id === form.project_id &&
      item.comment_id !== editingId.value
  )
)

async function loadProjects() {
  try {
    const { data } = await listProjects()
    projects.value = data.items || []
  } catch {
    projects.value = []
  }
}

async function loadTargetData(projectId) {
  try {
    const [reqData, defectData, testData, milestoneData] = await Promise.all([
      listRequirements(projectId),
      listDefects(projectId),
      listTestCases(projectId),
      listMilestones(projectId),
    ])
    requirements.value = reqData.data.items || []
    defects.value = defectData.data.items || []
    testCases.value = testData.data.items || []
    milestones.value = milestoneData.data.items || []
  } catch {
    requirements.value = []
    defects.value = []
    testCases.value = []
    milestones.value = []
  }
}

async function loadItems() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await listComments(filterProject.value || null)
    items.value = data.items || []
  } catch (err) {
    error.value = err.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

async function editItem(item) {
  editingId.value = item.comment_id
  Object.assign(form, {
    project_id: item.project_id,
    target_type: item.target_type,
    target_id: item.target_id,
    content: item.content,
    reply_to_id: item.reply_to_id || '',
    created_by: item.created_by,
    deleted: !!item.deleted,
  })
  await loadTargetData(item.project_id)
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formError.value = ''
  Object.assign(form, {
    project_id: '',
    target_type: 'requirement',
    target_id: '',
    content: '',
    reply_to_id: '',
    created_by: '',
    deleted: false,
  })
}

async function handleSubmit() {
  formError.value = ''
  const payload = {
    project_id: form.project_id,
    target_type: form.target_type,
    target_id: form.target_id,
    content: form.content,
    reply_to_id: form.reply_to_id || null,
    created_by: form.created_by,
    deleted: form.deleted,
  }
  try {
    if (editingId.value) {
      await updateComment(editingId.value, payload)
    } else {
      await createComment(payload)
    }
    closeForm()
    await loadItems()
  } catch (err) {
    formError.value = err.response?.data?.detail || '操作失败'
  }
}

async function handleDelete(id) {
  if (!confirm('确认删除此评论？')) return
  try {
    await deleteComment(id)
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
.modal { background: var(--bg-card); border-radius: 0; width: 680px; max-width: 94vw; max-height: 90vh; overflow-y: auto; }
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
