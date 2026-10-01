<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getJSON, listBoxes, listPapers, getRun, dryEstimate, saveEstimate } from '../api'
import { grainLabel, num } from '../format'
import BoxUnfold from '../components/BoxUnfold.vue'
import TrialCards from '../components/TrialCards.vue'

const route = useRoute()
const router = useRouter()

const boxes = ref([])
const papers = ref([])
const bid = ref(null)
const pid = ref(null)
const overlapInput = ref('')
const out = ref(null)
const err = ref('')
const busy = ref(false)
const saving = ref(false)

const replayId = ref(null)
const replay = ref(null)      // 落库快照
const verify = ref(null)      // { ok, diffs }
const verifyErr = ref('')

const validPapers = computed(() => papers.value.filter((p) => Number(p.roll_width) > 0))
const readonlyParams = computed(() => replay.value !== null)
// 回放快照的中选试算：grain/张数/条料长同属择优卷向
const replayChosenTrial = computed(() =>
  replay.value?.trials?.find((t) => t.grain === replay.value?.grain) ?? null
)

// 复算模式下下拉展示写入时名字/卷宽（控件只读），避免活表改名/改宽造成口径错位
const paperOptions = computed(() => {
  if (!replay.value?.paper) return papers.value
  return papers.value.map((p) => (p.id === replay.value.paper.id
    ? { ...p, name: replay.value.paper.name, roll_width: replay.value.paper.roll_width, data_quality: 'snapshot' }
    : p))
})
const boxOptions = computed(() => {
  if (!replay.value?.box_dims) return boxes.value
  return boxes.value.map((b) => (b.id === replay.value.box_id
    ? { ...b, length: replay.value.box_dims.l, width: replay.value.box_dims.w, height: replay.value.box_dims.h }
    : b))
})

function errText(e) {
  const raw = String(e?.message ?? e)
  try { return JSON.parse(raw).detail ?? raw } catch { return raw }
}

function closeEq(a, b, tol = 1e-6) {
  return Math.abs(Number(a) - Number(b)) <= tol
}

// 复算干算 vs 落库快照：逐项互证。
// replay 取自详情接口的 result——中选卷向投影快照（grain/张数/条料长同属一向）；
// 不比顶层 strip_length（干算响应无此顶层键，条料长在各 trial 内），不比 .paper（干算响应为活纸行）。
function compare(fresh, snap) {
  const diffs = []
  for (const k of ['box_id', 'grain', 'sheets', 'tie', 'tiebreak', 'paper_m2']) {
    if (JSON.stringify(fresh[k]) !== JSON.stringify(snap[k])) diffs.push(k)
  }
  for (let i = 0; i < Math.max(fresh.trials?.length ?? 0, snap.trials?.length ?? 0); i++) {
    const ft = fresh.trials?.[i]
    const st = snap.trials?.[i]
    if (!ft || !st) { diffs.push(`trials[${i}]`); continue }
    if (ft.grain !== st.grain || ft.sheets !== st.sheets) diffs.push(`trials[${i}].grain/sheets`)
    for (const k of ['aligned_ruler', 'cross_ruler', 'roll_width', 'roll_length_used']) {
      if (!closeEq(ft[k], st[k])) diffs.push(`trials[${i}].${k}`)
    }
  }
  return diffs
}

async function go() {
  err.value = ''
  verify.value = null
  verifyErr.value = ''
  if (!readonlyParams.value) {
    if (!validPapers.value.some((p) => p.id === pid.value)) {
      err.value = '请选择卷宽为正的纸卷'
      return
    }
  }
  busy.value = true
  try {
    const params = readonlyParams.value
      ? { box_id: replay.value.box_id, paper_id: replay.value.paper.id,
          overlap: replay.value.overlap, wrap_style: replay.value.wrap_style ?? 'cross' }
      : { box_id: bid.value, paper_id: pid.value, overlap: overlapInput.value }
    out.value = await dryEstimate(params)
    if (readonlyParams.value) {
      const diffs = compare(out.value, replay.value)
      verify.value = { ok: diffs.length === 0, diffs }
    }
  } catch (e) {
    const msg = errText(e)
    if (readonlyParams.value) {
      // 纸/盒可能已被删除或置脏：快照照常展示，错误只落在复算区
      verifyErr.value = `复算失败：${msg}`
    } else {
      err.value = msg
    }
  } finally {
    busy.value = false
  }
}

async function save() {
  err.value = ''
  if (!validPapers.value.some((p) => p.id === pid.value)) {
    err.value = '请选择卷宽为正的纸卷'
    return
  }
  saving.value = true
  try {
    const r = await saveEstimate({
      box_id: bid.value,
      paper_id: pid.value,
      overlap: overlapInput.value === '' ? undefined : Number(overlapInput.value),
    })
    await router.push(`/history/${r.run_id}`)
  } catch (e) {
    err.value = errText(e)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const [bRes, pRes] = await Promise.all([listBoxes(), listPapers()])
    boxes.value = bRes.items.filter((b) => b.data_quality === 'clean')
    papers.value = pRes.items

    const runQ = route.query.run
    if (runQ) {
      replayId.value = Number(runQ)
      const r = await getRun(replayId.value)
      replay.value = r.result
      bid.value = replay.value.box_id
      pid.value = replay.value.paper?.id
      overlapInput.value = String(replay.value.overlap ?? '')
      // 快照中的盒/纸可能已不在活表（删除/置脏）：补合成项让只读下拉仍能显示写入时名字
      if (!boxes.value.some((b) => b.id === bid.value) && replay.value.box_dims) {
        boxes.value = [{
          id: bid.value,
          name: r.box_name ?? `盒 #${bid.value}（已不可用）`,
          length: replay.value.box_dims.l, width: replay.value.box_dims.w, height: replay.value.box_dims.h,
          data_quality: 'snapshot',
        }, ...boxes.value]
      }
      if (!papers.value.some((p) => p.id === pid.value) && replay.value.paper) {
        papers.value = [{ ...replay.value.paper, data_quality: 'snapshot' }, ...papers.value]
      }
      return
    }

    const boxQ = route.query.box
    const wanted = boxQ ? Number(boxQ) : null
    if (wanted && boxes.value.some((b) => b.id === wanted)) bid.value = wanted
    else bid.value = boxes.value[0]?.id ?? null
    pid.value = validPapers.value[0]?.id ?? null
  } catch (e) {
    err.value = errText(e)
  }
})
</script>

<template>
  <div class="page">
    <h1>算纸</h1>
    <p class="lede">绑定纸卷后按两种卷向分别试算：卷宽对齐长向/宽向展开主尺，取张数更少者；并列时固定优先长向。</p>

    <div v-if="replay" class="snap-banner">
      复算档 #{{ replayId }} ·
      写入用纸「{{ replay.paper?.name }}」卷宽 {{ num(replay.paper?.roll_width) }} m ·
      当时选用 <strong>{{ grainLabel(replay.grain) }}</strong> {{ replay.sheets }} 张 · 条料长 {{ num(replayChosenTrial?.strip_length ?? replay.strip_length) }} m ·
      参数只读，干算与落库快照互证。
      <router-link class="btn btn-sm ghost" to="/bench">退出复算</router-link>
    </div>

    <div class="row">
      <select v-model.number="bid" :disabled="readonlyParams">
        <option v-for="b in boxOptions" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <select v-model.number="pid" :disabled="readonlyParams">
        <option v-for="p in paperOptions" :key="p.id" :value="p.id" :disabled="Number(p.roll_width) <= 0">
          {{ p.name }} · 卷宽 {{ num(p.roll_width, 2) }} m{{ Number(p.roll_width) <= 0 ? '（不可用）' : '' }}
        </option>
      </select>
      <label class="field">折边系数
        <input v-model="overlapInput" type="number" step="0.01" min="1" placeholder="默认 1.15" :disabled="readonlyParams">
      </label>
      <button :disabled="busy" @click="go">干算</button>
      <button v-if="!readonlyParams" class="ribbon" :disabled="saving" @click="save">写入用纸档</button>
    </div>

    <p v-if="err" class="bad">{{ err }}</p>

    <div v-if="replay && verify" :class="['verify', verify.ok ? 'ok' : 'bad']">
      <template v-if="verify.ok">✓ 互证一致：两向试算、选用 {{ grainLabel(out.grain) }}/{{ out.sheets }} 张、paper_m2 均与落库快照相同。</template>
      <template v-else>✗ 互证不一致：{{ verify.diffs.join('、') }}</template>
    </div>
    <p v-if="verifyErr" class="bad">{{ verifyErr }}（落库快照仍可在用纸档详情查看）</p>

    <div v-if="out" class="result-board">
      <TrialCards :trials="out.trials" :grain="out.grain" />
      <p class="stat-line">
        选用：<strong>{{ grainLabel(out.grain) }}</strong> · {{ out.sheets }} 张
        <span v-if="out.tie" class="pill tie">两向并列，按固定规则优先长向</span>
      </p>
      <div class="figure">{{ out.paper_m2 }}<span>m²</span></div>
      <p class="stat-line" v-if="out.ribbon">
        十字丝带约 {{ out.ribbon.ribbon_m ?? out.ribbon }} m
      </p>
      <BoxUnfold
        :l="out.box?.length ?? out.box_dims?.l"
        :w="out.box?.width ?? out.box_dims?.w"
        :h="out.box?.height ?? out.box_dims?.h"
        :paper-m2="out.paper_m2"
        :grain="out.grain"
      />
    </div>
  </div>
</template>
