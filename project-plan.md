# Etihad Rail – Ubuntu Monitoring Dashboard

A lightweight, Etihad-Rail–styled monitoring dashboard for a single Ubuntu machine.

- **Backend:** FastAPI + `psutil` + SQLite
- **Frontend:** Vue 3 + Vite + Chart.js (via `vue-chartjs`)
- **Data:** Live metrics + historical time series in SQLite  
- **Retention:** Automatically clears metrics older than **7 days**
- **Auth:** _None in dev_ (hooks left in place for future auth)
- **Alerts:** Data model & hooks ready; delivery to be added later

---

## 1. Objectives

1. Monitor an Ubuntu server with a web dashboard:
   - CPU usage (overall + per-core)
   - Memory usage
   - Disk usage (overall + per-partition)
   - Network activity (TX/RX counters; later: rates)
   - System info (hostname, uptime, kernel, etc.)
2. Store metrics as time series in **SQLite** for short historical view & alerting.
3. Use **Vue.js** + **Chart.js** dashboard with Etihad Rail–inspired styling:
   - Clean, white layout
   - Milano Red (`#C10505`) as primary accent
   - Silver (`#B9B9B9`) as neutral accent
4. Use **`uv`** instead of `pip` for Python dependency management.
5. No authentication for development, but structure ready for future auth.

---

## 2. High-Level Architecture

```text
+---------------------------+
| Ubuntu Host               |
|                           |
|  +---------------------+  |
|  | FastAPI Backend     |  |
|  |  - /api/metrics     |  |
|  |  - /api/history     |  |
|  |  - /api/system      |  |
|  |                     |  |
|  | psutil              |  |
|  | SQLite (time series)|  |
|  +---------------------+  |
|             ^             |
|             | HTTP (JSON) |
|             v             |
|  +---------------------+  |
|  | Vue 3 + Chart.js    |  |
|  | - Live metrics      |  |
|  | - Historical charts |  |
|  +---------------------+  |
+---------------------------+
