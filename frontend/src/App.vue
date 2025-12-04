<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import MetricCard from './components/MetricCard.vue'
import HistoryChart from './components/HistoryChart.vue'
import DiskMetrics from './components/DiskMetrics.vue'

const systemInfo = ref(null)
const metrics = ref(null)
const history = ref(null)

const API_URL = 'http://localhost:8004/api'

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
    const response = await axios.get(`${API_URL}/history?hours=1`)
    const data = response.data.metrics
    
    const labels = data.map(m => new Date(m.timestamp).toLocaleTimeString())
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
  } catch (error) {
    console.error('Error fetching history:', error)
  }
}

let intervalId

onMounted(async () => {
  await fetchSystemInfo()
  await fetchMetrics()
  await fetchHistory()
  
  intervalId = setInterval(async () => {
    await fetchMetrics()
    await fetchHistory()
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

    <div class="charts-container">
      <HistoryChart :chartData="cpuChartData" :options="chartOptions" />
      <HistoryChart :chartData="memChartData" :options="chartOptions" />
      <DiskMetrics v-if="metrics && metrics.disk_details" :partitions="metrics.disk_details" />
    </div>
  </div>
</template>
