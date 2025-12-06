<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import MetricCard from './components/MetricCard.vue'
import HistoryChart from './components/HistoryChart.vue'
import DiskMetrics from './components/DiskMetrics.vue'
import StatusCard from './components/StatusCard.vue'

const systemInfo = ref(null)
const metrics = ref(null)
const history = ref(null)
const odooHealth = ref(null)
const timeRange = ref(1) // Default 1 hour

const API_URL = '/monitoring/api'

// Configurable service URLs to monitor
const SERVICES = {
  odoo: 'https://al-tos.linus-services.com'
}

const cpuChartData = ref({
  labels: [],
  datasets: [
    {
      label: 'CPU Usage (%)',
      backgroundColor: '#C10505',
      borderColor: '#C10505',
      data: []
    }
  ]
})

const memChartData = ref({
  labels: [],
  datasets: [
    {
      label: 'Memory Usage (%)',
      backgroundColor: '#B9B9B9',
      borderColor: '#B9B9B9',
      data: []
    }
  ]
})

const diskChartData = ref({
  labels: [],
  datasets: []
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
      max: 100
    }
  }
}

const fetchSystemInfo = async () => {
  try {
    const response = await axios.get(`${API_URL}/system`)
    systemInfo.value = response.data
  } catch (error) {
    console.error('Error fetching system info:', error)
  }
}

const fetchMetrics = async () => {
  try {
    const response = await axios.get(`${API_URL}/metrics/latest`)
    metrics.value = response.data
  } catch (error) {
    console.error('Error fetching metrics:', error)
  }
}

const fetchHistory = async () => {
  try {
    const response = await axios.get(`${API_URL}/history?hours=${timeRange.value}`)
    const data = response.data.metrics
    
    // Format timestamp to UAE time (UTC+4)
    const formatTime = (isoString) => {
      return new Date(isoString).toLocaleTimeString('en-US', {
        timeZone: 'Asia/Dubai',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const labels = data.map(m => formatTime(m.timestamp))
    const cpuData = data.map(m => m.cpu_percent)
    const memData = data.map(m => m.memory_percent)

    cpuChartData.value = {
      labels,
      datasets: [{ ...cpuChartData.value.datasets[0], data: cpuData }]
    }
    
    memChartData.value = {
      labels,
      datasets: [{ ...memChartData.value.datasets[0], data: memData }]
    }

    // Process Disk Data
    // We need to group by mountpoint
    const diskDatasets = {}
    const colors = ['#C10505', '#B9B9B9', '#28a745', '#ffc107', '#17a2b8', '#6610f2']
    
    data.forEach(m => {
      if (m.disk_details) {
        m.disk_details.forEach(d => {
          // Skip /snap partitions
          if (d.mountpoint.startsWith('/snap')) return

          if (!diskDatasets[d.mountpoint]) {
            diskDatasets[d.mountpoint] = []
          }
          diskDatasets[d.mountpoint].push(d.percent)
        })
      }
    })

    const datasets = Object.keys(diskDatasets).map((mountpoint, index) => ({
      label: mountpoint,
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length],
      data: diskDatasets[mountpoint],
      tension: 0.4
    }))

    diskChartData.value = {
      labels,
      datasets
    }

  } catch (error) {
    console.error('Error fetching history:', error)
  }
}

const setTimeRange = (hours) => {
  timeRange.value = hours
  fetchHistory()
}

const fetchOdooHealth = async () => {
  try {
    const response = await axios.get(`${API_URL}/odoo/health`, {
      params: { url: SERVICES.odoo }
    })
    odooHealth.value = response.data
  } catch (error) {
    console.error('Error fetching Odoo health:', error)
    odooHealth.value = {
      status: 'error',
      message: 'Failed to check Odoo status'
    }
  }
}

let intervalId

onMounted(async () => {
  await fetchSystemInfo()
  await fetchMetrics()
  await fetchHistory()
  await fetchOdooHealth()
  
  intervalId = setInterval(async () => {
    await fetchMetrics()
    await fetchHistory()
    await fetchOdooHealth()
  }, 5000)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<template>
  <div class="dashboard-container">
    <header class="header">
      <div>
        <h1>Etihad Rail Monitoring</h1>
        <div v-if="systemInfo" style="color: #666; margin-top: 5px;">
          Host: {{ systemInfo.hostname }} | OS: {{ systemInfo.platform }} | Uptime: {{ (systemInfo.uptime_seconds / 3600).toFixed(1) }}h
        </div>
      </div>
      <div>
        <img src="https://api.etihadrail.ae/uploads/media/66fd6458cd1a28bc81efa67b_ER_PRIMARY_RGB68654571d127d.svg" alt="Etihad Rail" style="height: 60px;">
      </div>
    </header>

    <div class="metrics-grid" v-if="metrics">
      <MetricCard label="CPU Usage" :value="metrics.cpu_percent" unit="%" accent />
      <MetricCard label="Memory Usage" :value="metrics.memory_percent" unit="%" />
      <MetricCard label="Network Sent" :value="(metrics.net_sent / 1024 / 1024).toFixed(1)" unit="MB" />
      <MetricCard label="Network Recv" :value="(metrics.net_recv / 1024 / 1024).toFixed(1)" unit="MB" />
    </div>

    <div class="services-section">
      <h2 class="section-title">Service Health</h2>
      <div class="services-grid">
        <StatusCard 
          v-if="odooHealth"
          label="Odoo Platform (AL-TOS)"
          :status="odooHealth.status"
          :message="odooHealth.message"
          :responseTime="odooHealth.response_time_ms"
          :url="odooHealth.url"
        />
      </div>
    </div>

    <div class="controls">
      <button :class="{ active: timeRange === 1 }" @click="setTimeRange(1)">1h</button>
      <button :class="{ active: timeRange === 6 }" @click="setTimeRange(6)">6h</button>
      <button :class="{ active: timeRange === 12 }" @click="setTimeRange(12)">12h</button>
      <button :class="{ active: timeRange === 24 }" @click="setTimeRange(24)">24h</button>
      <button :class="{ active: timeRange === 72 }" @click="setTimeRange(72)">3d</button>
      <button :class="{ active: timeRange === 168 }" @click="setTimeRange(168)">7d</button>
    </div>

    <div class="charts-container">
      <HistoryChart :chartData="cpuChartData" :options="chartOptions" />
      <HistoryChart :chartData="memChartData" :options="chartOptions" />
      <HistoryChart :chartData="diskChartData" :options="chartOptions" />
      <DiskMetrics v-if="metrics && metrics.disk_details" :partitions="metrics.disk_details" />
    </div>
  </div>
</template>
