export async function getJSON(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
export async function postJSON(path, body) {
  const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
export async function putJSON(path, body) {
  const r = await fetch(path, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export const listBoxes = () => getJSON('/api/boxes')
export const listPapers = () => getJSON('/api/papers')
export const updatePaper = (id, roll_width) => putJSON(`/api/papers/${id}`, { roll_width })
export const listRuns = (limit = 50) => getJSON(`/api/runs?limit=${limit}`)
export const getRun = (id) => getJSON(`/api/runs/${id}`)

export function dryEstimate({ box_id, paper_id, overlap, wrap_style = 'cross' }) {
  const q = new URLSearchParams({ box_id, paper_id, wrap_style })
  if (overlap !== '' && overlap != null) q.set('overlap', overlap)
  return getJSON(`/api/estimate?${q}`)
}
// 复算互证：按写入同参（快照盒三边/卷宽/折边）干算，不读活表、不落库
export const dryEstimateParams = (payload) => postJSON('/api/estimate/dry', payload)
export const saveEstimate = (payload) => postJSON('/api/estimate', { ...payload, save: true })
