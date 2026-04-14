export function formatTime(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function stringifyJson(value, fallback = '{}') {
  if (value === null || value === undefined || value === '') return fallback
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return fallback
  }
}

export function parseJsonInput(text, fallback = null) {
  const raw = typeof text === 'string' ? text.trim() : ''
  if (!raw) return fallback
  return JSON.parse(raw)
}

export function truncateText(value, max = 48) {
  if (!value) return '—'
  return value.length > max ? `${value.slice(0, max)}…` : value
}
