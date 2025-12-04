<script setup>
defineProps({
  label: String,
  value: [Number, String],
  unit: String,
  accent: Boolean
})
</script>

<template>
  <div class="card" :class="{ accent: accent }">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value">
      {{ value }}<span v-if="unit" style="font-size: 1rem; color: #999;">{{ unit }}</span>
    </div>
  </div>
</template>
