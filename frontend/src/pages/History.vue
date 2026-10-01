<script setup>
import { onMounted, ref } from 'vue'
import { listRuns } from '../api'
import { fmtTime, grainLabel, num } from '../format'

const items = ref([])
const err = ref('')

function errText(e) {
  const raw = String(e?.message ?? e)
  try { return JSON.parse(raw).detail ?? raw } catch { return raw }
}

onMounted(async () => {
  try {
    items.value = (await listRuns()).items
  } catch (e) {
    err.value = errText(e)
  }
})
</script>

<template>
  <div class="page">
    <h1>用纸档</h1>
    <p class="hint" data-list-pin="grain">列表优先钉写入摘要；详情走开放投影。</p>
    <p class="hint">列表钉写入摘要（grain / sheets）；详情走开放视图字段。</p>
    <p class="lede">落库为唯一真相：每档钉住写入时的纸卷卷宽、两向试算与选用结果；纸张后续改宽不影响回放。</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <p v-else-if="!items.length" class="empty">还没有写入过。先去算纸绑卷试一单。</p>
    <ul v-else class="item-list">
      <li v-for="r in items" :key="r.id">
        <router-link :to="`/history/${r.id}`" class="run-row">
          <span class="run-main">{{ r.box_name ?? `盒 #${r.box_id}` }}</span>
          <span class="meta">{{ r.result?.paper?.name ?? '—' }}</span>
          <span class="pill" v-if="r.result?.grain">{{ grainLabel(r.result.grain) }}</span>
          <span class="meta">{{ r.result?.sheets != null ? `${r.result.sheets} 张` : '—' }}</span>
          <span class="meta">{{ num(r.result?.paper_m2) }} m²</span>
          <span class="meta">{{ fmtTime(r.created_at) }}</span>
        </router-link>
      </li>
    </ul>
  </div>
</template>
