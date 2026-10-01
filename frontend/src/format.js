export const GRAIN_LABEL = { length: '长向', width: '宽向' }

export const grainLabel = (g) => GRAIN_LABEL[g] ?? '—'

export const fmtTime = (s) => (s ? String(s).replace('T', ' ').slice(0, 16) : '—')

export const num = (v, d = 3) => (v == null || Number.isNaN(Number(v)) ? '—' : Number(v).toFixed(d))
