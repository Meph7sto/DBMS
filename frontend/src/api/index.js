import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

/* ── Connection ── */
export const connect = (params) => api.post('/connect', params)
export const disconnect = () => api.delete('/connect')
export const connectionStatus = () => api.get('/connect')
export const connectionDefaults = () => api.get('/connect/defaults')


/* ── Explore ── */
export const listDatabases = () => api.get('/databases')
export const listSchemas = () => api.get('/schemas')
export const listTables = (schema = 'public') =>
  api.get('/tables', { params: { schema } })
export const tableDetail = (schema, name) =>
  api.get(`/tables/${schema}/${name}`)
export const tableData = (schema, name, page = 1, size = 50) =>
  api.get(`/tables/${schema}/${name}/data`, { params: { page, size } })

/* ── Query ── */
export const executeQuery = (sql) => api.post('/query', { sql })

/* ── Benchmark ── */
export const importBenchmark = () => api.post('/benchmark/import')
export const deleteBenchmark = () => api.post('/benchmark/delete')

/* ── Visible Demo Data ── */
export const importVisibleDemoData = () => api.post('/demo/import')
export const deleteVisibleDemoData = () => api.post('/demo/delete')


/* ── CRUD: Products ── */
export const listProducts = () => api.get('/crud/products')
export const createProduct = (data) => api.post('/crud/products', data)
export const updateProduct = (id, data) => api.put(`/crud/products/${id}`, data)
export const deleteProduct = (id) => api.delete(`/crud/products/${id}`)

/* ── CRUD: Projects ── */
export const listProjects = () => api.get('/crud/projects')
export const createProject = (data) => api.post('/crud/projects', data)
export const updateProject = (id, data) => api.put(`/crud/projects/${id}`, data)
export const deleteProject = (id) => api.delete(`/crud/projects/${id}`)

/* ── CRUD: Requirements ── */
export const listRequirements = (projectId) =>
  api.get('/crud/requirements', { params: projectId ? { project_id: projectId } : {} })
export const createRequirement = (data) => api.post('/crud/requirements', data)
export const updateRequirement = (id, data) => api.put(`/crud/requirements/${id}`, data)
export const deleteRequirement = (id) => api.delete(`/crud/requirements/${id}`)

/* ── CRUD: Defects ── */
export const listDefects = (projectId) =>
  api.get('/crud/defects', { params: projectId ? { project_id: projectId } : {} })
export const createDefect = (data) => api.post('/crud/defects', data)
export const updateDefect = (id, data) => api.put(`/crud/defects/${id}`, data)
export const deleteDefect = (id) => api.delete(`/crud/defects/${id}`)

/* ── CRUD: Test Cases ── */
export const listTestCases = (projectId) =>
  api.get('/crud/test-cases', { params: projectId ? { project_id: projectId } : {} })
export const createTestCase = (data) => api.post('/crud/test-cases', data)
export const updateTestCase = (id, data) => api.put(`/crud/test-cases/${id}`, data)
export const deleteTestCase = (id) => api.delete(`/crud/test-cases/${id}`)

/* ── CRUD: Milestones ── */
export const listMilestones = (projectId) =>
  api.get('/crud/milestones', { params: projectId ? { project_id: projectId } : {} })
export const createMilestone = (data) => api.post('/crud/milestones', data)
export const updateMilestone = (id, data) => api.put(`/crud/milestones/${id}`, data)
export const deleteMilestone = (id) => api.delete(`/crud/milestones/${id}`)

/* ── CRUD: Product Members ── */
export const listProductMembers = (productId) =>
  api.get('/crud/product-members', { params: productId ? { product_id: productId } : {} })
export const createProductMember = (data) => api.post('/crud/product-members', data)
export const updateProductMember = (id, data) => api.put(`/crud/product-members/${id}`, data)
export const deleteProductMember = (id) => api.delete(`/crud/product-members/${id}`)

/* ── CRUD: Project Members ── */
export const listProjectMembers = (projectId) =>
  api.get('/crud/project-members', { params: projectId ? { project_id: projectId } : {} })
export const createProjectMember = (data) => api.post('/crud/project-members', data)
export const updateProjectMember = (id, data) => api.put(`/crud/project-members/${id}`, data)
export const deleteProjectMember = (id) => api.delete(`/crud/project-members/${id}`)

/* ── CRUD: Requirement Links ── */
export const listRequirementLinks = (projectId) =>
  api.get('/crud/requirement-links', { params: projectId ? { project_id: projectId } : {} })
export const createRequirementLink = (data) => api.post('/crud/requirement-links', data)
export const updateRequirementLink = (id, data) => api.put(`/crud/requirement-links/${id}`, data)
export const deleteRequirementLink = (id) => api.delete(`/crud/requirement-links/${id}`)

/* ── CRUD: Requirement Test Links ── */
export const listRequirementTestLinks = (projectId) =>
  api.get('/crud/requirement-test-links', { params: projectId ? { project_id: projectId } : {} })
export const createRequirementTestLink = (data) => api.post('/crud/requirement-test-links', data)
export const updateRequirementTestLink = (id, data) => api.put(`/crud/requirement-test-links/${id}`, data)
export const deleteRequirementTestLink = (id) => api.delete(`/crud/requirement-test-links/${id}`)

/* ── CRUD: Milestone Nodes ── */
export const listMilestoneNodes = (params = {}) =>
  api.get('/crud/milestone-nodes', { params })
export const createMilestoneNode = (data) => api.post('/crud/milestone-nodes', data)
export const updateMilestoneNode = (id, data) => api.put(`/crud/milestone-nodes/${id}`, data)
export const deleteMilestoneNode = (id) => api.delete(`/crud/milestone-nodes/${id}`)

/* ── CRUD: Branches ── */
export const listBranches = (projectId) =>
  api.get('/crud/branches', { params: projectId ? { project_id: projectId } : {} })
export const createBranch = (data) => api.post('/crud/branches', data)
export const updateBranch = (id, data) => api.put(`/crud/branches/${id}`, data)
export const deleteBranch = (id) => api.delete(`/crud/branches/${id}`)

/* ── CRUD: Change Sets ── */
export const listChangeSets = (params = {}) =>
  api.get('/crud/change-sets', { params })
export const createChangeSet = (data) => api.post('/crud/change-sets', data)
export const updateChangeSet = (id, data) => api.put(`/crud/change-sets/${id}`, data)
export const deleteChangeSet = (id) => api.delete(`/crud/change-sets/${id}`)

/* ── CRUD: Comments ── */
export const listComments = (projectId) =>
  api.get('/crud/comments', { params: projectId ? { project_id: projectId } : {} })
export const createComment = (data) => api.post('/crud/comments', data)
export const updateComment = (id, data) => api.put(`/crud/comments/${id}`, data)
export const deleteComment = (id) => api.delete(`/crud/comments/${id}`)

/* ── CRUD: Audit Logs ── */
export const listAuditLogs = (params = {}) =>
  api.get('/crud/audit-logs', { params })
export const createAuditLog = (data) => api.post('/crud/audit-logs', data)
export const updateAuditLog = (id, data) => api.put(`/crud/audit-logs/${id}`, data)
export const deleteAuditLog = (id) => api.delete(`/crud/audit-logs/${id}`)

/* ── Statistics ── */
export const listProjectStats = () => api.get('/stats/projects')
export const getProjectStats = (id) => api.get(`/stats/project/${id}`)
export const getRequirementTrace = (projectId) => api.get(`/stats/project/${projectId}/trace`)
export const getProjectProgress = (projectId) => api.get(`/stats/project/${projectId}/progress`)
export const getMilestoneRisk = (projectId) => api.get(`/stats/project/${projectId}/milestone-risk`)
