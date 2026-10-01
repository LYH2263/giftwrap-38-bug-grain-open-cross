<script setup>
import { onMounted, ref } from 'vue'
import { listPapers, updatePaper } from '../api'
import { num } from '../format'

const items = ref([])
const err = ref('')
const editingId = ref(null)
const draft = ref('')
const saving = ref(false)
const formErr = ref('')

function errText(e) {
  const raw = String(e?.message ?? e)
  try { return JSON.parse(raw).detail ?? raw } catch { return raw }
}

async function load() {
  items.value = (await listPapers()).items
}

function startEdit(p) {
  editingId.value = p.id
  draft.value = String(p.roll_width)
  formErr.value = ''
}

async function saveWidth(id) {
  formErr.value = ''
  const v = Number(draft.value)
  if (!(v > 0) || !Number.isFinite(v)) {
    formErr.value = '卷宽须为正数'
    return
  }
  saving.value = true
  try {
    const updated = await updatePaper(id, v)
    items.value = items.value.map((p) => (p.id === id ? updated : p))
    editingId.value = null
  } catch (e) {
    formErr.value = errText(e)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    await load()
  } catch (e) {
    err.value = errText(e)
  }
})
</script>

<template>
  <div class="page">
    <h1>包装纸</h1>
    <p class="lede">卷宽用于卷向试算（卷宽对齐展开主尺，ceil 取张数）。修改卷宽只影响新测算，已写入用纸档保留写入时快照，不被重择。</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <div v-else class="paper-grid">
      <div v-for="p in items" :key="p.id" class="paper-tile">
        <template v-if="editingId === p.id">
          <strong>{{ p.name }}</strong>
          <label class="field">卷宽 (m)
            <input v-model="draft" type="number" step="0.01" min="0.01">
          </label>
          <p v-if="formErr" class="bad">{{ formErr }}</p>
          <div class="row">
            <button class="btn-sm" :disabled="saving" @click="saveWidth(p.id)">保存</button>
            <button class="btn-sm ghost" :disabled="saving" @click="editingId = null">取消</button>
          </div>
        </template>
        <template v-else>
          <strong>{{ p.name }}</strong>
          <span class="meta">卷宽 {{ num(p.roll_width, 2) }} m</span>
          <button class="btn-sm ghost" @click="startEdit(p)">修改卷宽</button>
        </template>
      </div>
    </div>
  </div>
</template>
