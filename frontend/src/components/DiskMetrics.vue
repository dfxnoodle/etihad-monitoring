<script setup>
defineProps({
  partitions: Array
})
</script>

<template>
  <div class="card">
    <div class="metric-label">Disk Details</div>
    <div class="partitions-list">
      <div v-for="part in partitions" :key="part.mountpoint" class="partition-item">
        <div class="partition-header">
          <span class="mountpoint">{{ part.mountpoint }}</span>
          <span class="device">{{ part.device }}</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" :class="getUsageClass(part.percent)" :style="{ width: part.percent + '%' }"></div>
        </div>
        <div class="partition-stats">
          <span>{{ part.percent }}% used</span>
          <span>{{ (part.free / 1024 / 1024 / 1024).toFixed(1) }} GB free</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    getUsageClass(percent) {
      if (percent < 70) return 'usage-normal'
      if (percent < 90) return 'usage-warning'
      return 'usage-critical'
    }
  }
}
</script>

<style scoped>
.partitions-list {
  margin-top: 15px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.partition-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 0.9rem;
}

.mountpoint {
  font-weight: bold;
}

.device {
  color: #999;
  font-size: 0.8rem;
}

.progress-bar-bg {
  background-color: #eee;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease, background-color 0.3s ease;
}

.usage-normal {
  background-color: #28a745; /* Green */
}

.usage-warning {
  background-color: #ffc107; /* Orange */
}

.usage-critical {
  background-color: var(--etihad-red); /* Red */
}

.partition-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 3px;
  font-size: 0.8rem;
  color: #666;
}
</style>
