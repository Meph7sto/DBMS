import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

/* ── Connection ── */
export const connect = (params) => api.post('/connect', params)
export const disconnect = () => api.delete('/connect')
export const connectionStatus = () => api.get('/connect')

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
