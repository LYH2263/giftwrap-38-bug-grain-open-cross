<script setup>
import { grainLabel, num } from '../format'

defineProps({
  trials: { type: Array, default: () => [] },
  grain: { type: String, default: '' },
})
</script>

<template>
  <div class="trial-grid">
    <div
      v-for="t in trials"
      :key="t.grain"
      class="trial-card"
      :class="{ chosen: t.grain === grain }"
    >
      <div class="trial-head">
        <strong>{{ grainLabel(t.grain) }}卷向</strong>
        <span v-if="t.grain === grain" class="pill">选用</span>
      </div>
      <div class="sheets">{{ t.sheets }}<span>张</span></div>
      <p class="stat-line">主尺 {{ num(t.aligned_ruler) }} m · 对齐卷宽 {{ num(t.roll_width) }} m</p>
      <p class="stat-line">副尺 {{ num(t.cross_ruler) }} m · 每条料长 {{ num(t.strip_length) }} m</p>
      <p class="stat-line">共耗卷长约 {{ num(t.roll_length_used) }} m</p>
    </div>
  </div>
</template>
