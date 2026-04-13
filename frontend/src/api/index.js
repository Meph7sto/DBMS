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

/* ── CRUD: Test Cases ── */
export const listTestCases = (projectId) =>
  api.get('/crud/test-cases', { params: projectId ? { project_id: projectId } : {} })
export const createTestCase = (data) => api.post('/crud/test-cases', data)

/* ── CRUD: Milestones ── */
export const listMilestones = (projectId) =>
  api.get('/crud/milestones', { params: projectId ? { project_id: projectId } : {} })
export const createMilestone = (data) => api.post('/crud/milestones', data)

/* ── Statistics ── */
export const listProjectStats = () => api.get('/stats/projects')
export const getProjectStats = (id) => api.get(`/stats/project/${id}`)
export const getRequirementTrace = (projectId) => api.get(`/stats/project/${projectId}/trace`)
export const getProjectProgress = (projectId) => api.get(`/stats/project/${projectId}/progress`)
