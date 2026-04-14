<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <div>
          <h2>需求关联管理</h2>
          <div class="subhead">{{ requirement.title }}</div>
        </div>
        <button class="ghost" @click="$emit('close')">✕</button>
      </div>
      <div class="modal-body">
        <div v-if="error" class="error-banner">{{ error }}</div>

        <div class="ribbon">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['ribbon-step', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <div v-if="activeTab === 'links'" class="layout">
          <div class="card section">
            <div class="section-header">
              <h4 class="card-kicker">需求关联</h4>
              <span class="chip chip-neutral">{{ relatedLinks.length }} 条</span>
            </div>
            <div v-if="relatedLinks.length" style="overflow:auto;">
              <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead>
                  <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
                    <th class="th">源需求</th>
                    <th class="th">目标需求</th>
                    <th class="th">类型</th>
                    <th class="th">创建人</th>
                    <th class="th">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in relatedLinks" :key="item.link_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
                    <td class="td">{{ item.source_title }}</td>
                    <td class="td">{{ item.target_title }}</td>
                    <td class="td"><span class="chip chip-neutral">{{ item.link_type }}</span></td>
                    <td class="td">{{ item.created_by || '—' }}</td>
                    <td class="td">
                      <button class="ghost mini-btn" @click="editLink(item)">编辑</button>
                      <button class="ghost mini-btn danger" @click="handleDeleteLink(item.link_id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty">暂无关联需求</div>
          </div>

          <div class="card section">
            <div class="section-header">
              <h4 class="card-kicker">{{ editingLinkId ? '编辑关联' : '新增关联' }}</h4>
            </div>
            <div class="form-group">
              <label>源需求 *</label>
              <select v-model="linkForm.source_req_id">
                <option v-for="item in requirements" :key="item.req_id" :value="item.req_id">
                  {{ item.title }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>目标需求 *</label>
              <select v-model="linkForm.target_req_id">
                <option value="">选择目标需求...</option>
                <option v-for="item in targetRequirementOptions" :key="item.req_id" :value="item.req_id">
                  {{ item.title }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>关联类型</label>
              <select v-model="linkForm.link_type">
                <option value="blocks">blocks</option>
                <option value="depends_on">depends_on</option>
                <option value="relates_to">relates_to</option>
                <option value="duplicates">duplicates</option>
              </select>
            </div>
            <div class="form-group">
              <label>创建人</label>
              <input v-model="linkForm.created_by" type="text" placeholder="user_id" />
            </div>
            <div v-if="linkError" class="error-inline">{{ linkError }}</div>
            <div class="actions">
              <button class="ghost" @click="resetLinkForm">重置</button>
              <button class="primary" @click="submitLink">{{ editingLinkId ? '保存修改' : '添加关联' }}</button>
            </div>
          </div>
        </div>

        <div v-else class="layout">
          <div class="card section">
            <div class="section-header">
              <h4 class="card-kicker">关联测试用例</h4>
              <span class="chip chip-neutral">{{ relatedTestLinks.length }} 条</span>
            </div>
            <div v-if="relatedTestLinks.length" style="overflow:auto;">
              <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead>
                  <tr style="border-bottom:1px solid rgba(28,40,52,0.1);">
                    <th class="th">测试用例</th>
                    <th class="th">类型</th>
                    <th class="th">创建时间</th>
                    <th class="th">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in relatedTestLinks" :key="item.link_id" style="border-bottom:1px solid rgba(28,40,52,0.06);">
                    <td class="td strong">{{ item.test_case_title }}</td>
                    <td class="td"><span class="chip chip-neutral">{{ item.link_type }}</span></td>
                    <td class="td muted">{{ formatTime(item.created_at) }}</td>
                    <td class="td">
                      <button class="ghost mini-btn" @click="editTestLink(item)">编辑</button>
                      <button class="ghost mini-btn danger" @click="handleDeleteTestLink(item.link_id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty">暂无关联测试</div>
          </div>

          <div class="card section">
            <div class="section-header">
              <h4 class="card-kicker">{{ editingTestLinkId ? '编辑测试关联' : '新增测试关联' }}</h4>
            </div>
            <div class="form-group">
              <label>测试用例 *</label>
              <select v-model="testLinkForm.test_case_id">
                <option value="">选择测试用例...</option>
                <option v-for="item in testCases" :key="item.test_case_id" :value="item.test_case_id">
                  {{ item.title }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>关联类型</label>
              <input v-model="testLinkForm.link_type" type="text" placeholder="verification" />
            </div>
            <div v-if="testLinkError" class="error-inline">{{ testLinkError }}</div>
            <div class="actions">
              <button class="ghost" @click="resetTestLinkForm">重置</button>
              <button class="primary" @click="submitTestLink">{{ editingTestLinkId ? '保存修改' : '添加测试关联' }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import {
  listRequirementLinks,
  createRequirementLink,
  updateRequirementLink,
  deleteRequirementLink,
  listRequirementTestLinks,
  createRequirementTestLink,
  updateRequirementTestLink,
  deleteRequirementTestLink,
  listRequirements,
  listTestCases,
} from '../api'
import { formatTime } from '../utils/admin'

const props = defineProps({
  requirement: { type: Object, required: true },
})

defineEmits(['close'])

const tabs = [
  { key: 'links', label: '需求关联' },
  { key: 'tests', label: '测试关联' },
]

const activeTab = ref('links')
const requirements = ref([])
const testCases = ref([])
const links = ref([])
const testLinks = ref([])
const error = ref('')

const editingLinkId = ref(null)
const linkError = ref('')
const linkForm = reactive({
  source_req_id: '',
  target_req_id: '',
  link_type: 'relates_to',
  created_by: '',
})

const editingTestLinkId = ref(null)
const testLinkError = ref('')
const testLinkForm = reactive({
  test_case_id: '',
  link_type: 'verification',
})

watch(
  () => props.requirement.req_id,
  async () => {
    activeTab.value = 'links'
    resetLinkForm()
    resetTestLinkForm()
    await Promise.all([loadLookups(), loadItems()])
  },
  { immediate: true }
)

const relatedLinks = computed(() =>
  links.value.filter(
    (item) =>
      item.source_req_id === props.requirement.req_id ||
      item.target_req_id === props.requirement.req_id
  )
)

const relatedTestLinks = computed(() =>
  testLinks.value.filter((item) => item.requirement_id === props.requirement.req_id)
)

const targetRequirementOptions = computed(() =>
  requirements.value.filter((item) => item.req_id !== linkForm.source_req_id)
)

async function loadLookups() {
  try {
    const [{ data: reqData }, { data: tcData }] = await Promise.all([
      listRequirements(props.requirement.project_id),
      listTestCases(props.requirement.project_id),
    ])
    requirements.value = reqData.items || []
    testCases.value = tcData.items || []
    linkForm.source_req_id = props.requirement.req_id
  } catch {
    requirements.value = []
    testCases.value = []
  }
}

async function loadItems() {
  error.value = ''
  try {
    const [{ data: linkData }, { data: testData }] = await Promise.all([
      listRequirementLinks(props.requirement.project_id),
      listRequirementTestLinks(props.requirement.project_id),
    ])
    links.value = linkData.items || []
    testLinks.value = testData.items || []
  } catch (err) {
    error.value = err.response?.data?.detail || '加载关联数据失败'
  }
}

function resetLinkForm() {
  editingLinkId.value = null
  linkError.value = ''
  Object.assign(linkForm, {
    source_req_id: props.requirement.req_id,
    target_req_id: '',
    link_type: 'relates_to',
    created_by: '',
  })
}

function editLink(item) {
  editingLinkId.value = item.link_id
  Object.assign(linkForm, {
    source_req_id: item.source_req_id,
    target_req_id: item.target_req_id,
    link_type: item.link_type,
    created_by: item.created_by || '',
  })
}

async function submitLink() {
  linkError.value = ''
  try {
    if (editingLinkId.value) {
      await updateRequirementLink(editingLinkId.value, { ...linkForm })
    } else {
      await createRequirementLink({ ...linkForm })
    }
    resetLinkForm()
    await loadItems()
  } catch (err) {
    linkError.value = err.response?.data?.detail || '操作失败'
  }
}

async function handleDeleteLink(id) {
  if (!confirm('确认删除此需求关联？')) return
  try {
    await deleteRequirementLink(id)
    if (editingLinkId.value === id) resetLinkForm()
    await loadItems()
  } catch (err) {
    error.value = err.response?.data?.detail || '删除失败'
  }
}

function resetTestLinkForm() {
  editingTestLinkId.value = null
  testLinkError.value = ''
  Object.assign(testLinkForm, {
    test_case_id: '',
    link_type: 'verification',
  })
}

function editTestLink(item) {
  editingTestLinkId.value = item.link_id
  Object.assign(testLinkForm, {
    test_case_id: item.test_case_id,
    link_type: item.link_type,
  })
  activeTab.value = 'tests'
}

async function submitTestLink() {
  testLinkError.value = ''
  const payload = {
    requirement_id: props.requirement.req_id,
    test_case_id: testLinkForm.test_case_id,
    link_type: testLinkForm.link_type,
  }
  try {
    if (editingTestLinkId.value) {
      await updateRequirementTestLink(editingTestLinkId.value, payload)
    } else {
      await createRequirementTestLink(payload)
    }
    resetTestLinkForm()
    await loadItems()
  } catch (err) {
    testLinkError.value = err.response?.data?.detail || '操作失败'
  }
}

async function handleDeleteTestLink(id) {
  if (!confirm('确认删除此测试关联？')) return
  try {
    await deleteRequirementTestLink(id)
    if (editingTestLinkId.value === id) resetTestLinkForm()
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
.modal-body { padding:24px; display:flex; flex-direction:column; gap:20px; }
.layout { display:grid; grid-template-columns: minmax(0, 1.4fr) minmax(300px, 0.8fr); gap:20px; }
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
@media (max-width: 1000px) {
  .layout { grid-template-columns: 1fr; }
}
</style>
