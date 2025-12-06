<script setup>
defineProps({
  label: String,
  status: String,
  message: String,
  responseTime: [Number, String],
  url: String
})

const statusColor = (status) => {
  switch (status) {
    case 'online': return '#28a745'
    case 'offline': return '#dc3545'
    case 'error': return '#ffc107'
    default: return '#6c757d'
  }
}

const statusIcon = (status) => {
  switch (status) {
    case 'online': return '✓'
    case 'offline': return '✗'
    case 'error': return '!'
    default: return '?'
  }
}
</script>

<template>
  <div class="card status-card">
    <div class="metric-label">{{ label }}</div>
    <div class="status-indicator" :style="{ backgroundColor: statusColor(status) }">
      <span class="status-icon">{{ statusIcon(status) }}</span>
      <span class="status-text">{{ status?.toUpperCase() || 'CHECKING...' }}</span>
    </div>
    <div v-if="responseTime" class="response-time">{{ responseTime }}ms</div>
    <div v-if="message" class="status-message">{{ message }}</div>
    <a v-if="url" :href="url" target="_blank" class="status-url">{{ url }}</a>
  </div>
</template>

<style scoped>
.status-card {
  border-top: 4px solid #17a2b8 !important;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  color: white;
  font-weight: 600;
  margin-top: 10px;
}

.status-icon {
  font-size: 1.2rem;
  font-weight: bold;
}

.status-text {
  font-size: 0.9rem;
  letter-spacing: 1px;
}

.response-time {
  margin-top: 8px;
  font-size: 0.85rem;
  color: #666;
}

.status-message {
  margin-top: 5px;
  font-size: 0.8rem;
  color: #888;
}

.status-url {
  display: block;
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--etihad-red);
  text-decoration: none;
  word-break: break-all;
}

.status-url:hover {
  text-decoration: underline;
}
</style>
