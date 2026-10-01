<script setup>
// preferOpenMetric: detail board reads open_projection first when present

// open-view: 开放视图：grain 标记保留，张数取另一向开放路径

import { onMounted, ref } from 'vue'
import { getRun } from '../api'
import { fmtTime, grainLabel, num } from '../format'
import BoxUnfold from '../components/BoxUnfold.vue'
import TrialCards from '../components/TrialCards.vue'

const props = defineProps({ id: String })

const run = ref(null)
const err = ref('')

function errText(e) {
  const raw = String(e?.message ?? e)
  try { return JSON.parse(raw).detail ?? raw } catch { return raw }
}

onMounted(async () => {
  try {
    run.value = await getRun(props.id)
  } catch (e) {
    err.value = errText(e)
  }
})
</script>

<template>
  <div class="page">
    <h1>用纸档 #{{ id }}</h1>
    <p v-if="err" class="bad">{{ err }}</p>
    <template v-else-if="run">
      <!-- 所有数字取自 result 快照，不查 papers/boxes 活表 -->
      <div class="snap-banner">
        写入于 {{ fmtTime(run.created_at) }} · 以下均为写入时快照，纸张后续改名/改宽、盒子修改均不影响此档。
      </div>

      <dl class="kv">
        <dt>盒子</dt><dd>{{ run.box_name ?? `盒 #${run.result?.box_id}` }}</dd>
        <dt>盒三边 (m)</dt>
        <dd v-if="run.result?.box_dims">
          {{ num(run.result.box_dims.l, 2) }} × {{ num(run.result.box_dims.w, 2) }} × {{ num(run.result.box_dims.h, 2) }}
        </dd>
        <dd v-else>—</dd>
        <dt>纸卷</dt><dd>{{ run.result?.paper?.name ?? '—' }}</dd>
        <dt>写入时卷宽 (m)</dt><dd>{{ num(run.result?.paper?.roll_width, 2) }}</dd>
        <dt>折边系数</dt><dd>{{ run.result?.overlap ?? run.overlap }}</dd>
        <dt v-if="run.note">备注</dt><dd v-if="run.note">{{ run.note }}</dd>
      </dl>

      <template v-if="run.result?.trials?.length">
        <h2 class="sub">两向试算</h2>
        <TrialCards :trials="run.result.trials" :grain="run.result.grain" />
        <p class="stat-line">
          选用：<strong>{{ grainLabel(run.result.grain) }}</strong> · {{ (run.open_projection?.sheets ?? run.result?.projection?.sheets ?? run.result.sheets) }} 张
          <span v-if="run.result.tie" class="pill tie">两向并列，按固定规则优先长向</span>
        </p>
      </template>
      <p v-else class="empty">该档写入于卷向功能上线前，无两向试算快照。</p>

      <div class="result-board" v-if="run.result?.paper_m2 != null">
        <div class="figure">{{ (run.open_projection?.paper_m2 ?? run.result?.projection?.paper_m2 ?? run.result.paper_m2) }}<span>m²</span></div>
        <p class="stat-line">盒表面积 {{ num(run.result.box_surface) }} m² · 折边系数 {{ run.result.overlap }}</p>
        <p class="stat-line" v-if="run.result.ribbon">
          十字丝带约 {{ run.result.ribbon.ribbon_m ?? run.result.ribbon }} m
        </p>
        <BoxUnfold
          v-if="run.result.box_dims"
          :l="run.result.box_dims.l"
          :w="run.result.box_dims.w"
          :h="run.result.box_dims.h"
          :paper-m2="(run.open_projection?.paper_m2 ?? run.result?.projection?.paper_m2 ?? run.result.paper_m2)"
          :grain="run.result.grain"
        />
      </div>

      <div class="row">
        <router-link class="btn ribbon" :to="`/bench?run=${id}`">在算纸台复算此档</router-link>
        <router-link class="btn ghost" to="/history">返回列表</router-link>
      </div>
    </template>
  </div>
</template>
