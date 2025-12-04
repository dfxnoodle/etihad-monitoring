from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import psutil
import platform
import time
import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager
from database import init_db, get_db
from models import SystemInfo, MetricData, HistoricalData
from collector import collect_metrics

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(collect_metrics())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan, root_path="/monitoring")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/system", response_model=SystemInfo)
async def get_system_info():
    return SystemInfo(
        hostname=platform.node(),
        platform=platform.system(),
        uptime_seconds=time.time() - psutil.boot_time(),
        cpu_count=psutil.cpu_count(),
        memory_total=psutil.virtual_memory().total
    )

@app.get("/api/metrics/latest", response_model=MetricData)
async def get_latest_metrics(db = Depends(get_db)):
    async with db.execute("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1") as cursor:
        row = await cursor.fetchone()
        if row:
            return MetricData(
                timestamp=row['timestamp'],
                cpu_percent=row['cpu_percent'],
                memory_percent=row['memory_percent'],
                disk_percent=row['disk_percent'],
                disk_details=json.loads(row['disk_details']) if row['disk_details'] else [],
                net_sent=row['net_sent'],
                net_recv=row['net_recv']
            )
    # Fallback if no data yet
    return MetricData(
        timestamp=datetime.now(),
        cpu_percent=0,
        memory_percent=0,
        disk_percent=0,
        disk_details=[],
        net_sent=0,
        net_recv=0
    )

@app.get("/api/history", response_model=HistoricalData)
async def get_history(hours: int = 1, db = Depends(get_db)):
    async with db.execute(
        "SELECT * FROM metrics WHERE timestamp > datetime('now', ? || ' hours') ORDER BY timestamp ASC",
        (f"-{hours}",)
    ) as cursor:
        rows = await cursor.fetchall()
        metrics = [
            MetricData(
                timestamp=row['timestamp'],
                cpu_percent=row['cpu_percent'],
                memory_percent=row['memory_percent'],
                disk_percent=row['disk_percent'],
                disk_details=json.loads(row['disk_details']) if row['disk_details'] else [],
                net_sent=row['net_sent'],
                net_recv=row['net_recv']
            ) for row in rows
        ]
        return HistoricalData(metrics=metrics)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
