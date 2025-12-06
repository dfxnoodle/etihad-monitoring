from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import psutil
import platform
import time
import asyncio
import json
import httpx
from datetime import datetime, timezone

from contextlib import asynccontextmanager
from database import init_db, get_db
from models import SystemInfo, MetricData, HistoricalData, OdooHealthStatus
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

def parse_utc_timestamp(ts):
    if isinstance(ts, str):
        try:
            # SQLite default format: "YYYY-MM-DD HH:MM:SS"
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                return datetime.now(timezone.utc)
        return dt.replace(tzinfo=timezone.utc)
    if isinstance(ts, datetime):
        return ts.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

@app.get("/api/metrics/latest", response_model=MetricData)
async def get_latest_metrics(db = Depends(get_db)):
    async with db.execute("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1") as cursor:
        row = await cursor.fetchone()
        if row:
            return MetricData(
                timestamp=parse_utc_timestamp(row['timestamp']),
                cpu_percent=row['cpu_percent'],
                memory_percent=row['memory_percent'],
                disk_percent=row['disk_percent'],
                disk_details=json.loads(row['disk_details']) if row['disk_details'] else [],
                net_sent=row['net_sent'],
                net_recv=row['net_recv']
            )
    # Fallback if no data yet
    return MetricData(
        timestamp=datetime.now(timezone.utc),
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
                timestamp=parse_utc_timestamp(row['timestamp']),
                cpu_percent=row['cpu_percent'],
                memory_percent=row['memory_percent'],
                disk_percent=row['disk_percent'],
                disk_details=json.loads(row['disk_details']) if row['disk_details'] else [],
                net_sent=row['net_sent'],
                net_recv=row['net_recv']
            ) for row in rows
        ]
        return HistoricalData(metrics=metrics)

@app.get("/api/odoo/health", response_model=OdooHealthStatus)
async def check_odoo_health(url: str):
    """Check if Odoo platform is working by verifying redirect to /web"""
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=10.0, verify=False) as client:
            response = await client.head(url)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Check if we get a redirect (301, 302, 303, 307, 308)
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location", "")
                
                # Check if redirect is to /web
                if "/web" in location:
                    return OdooHealthStatus(
                        url=url,
                        status="online",
                        redirect_location=location,
                        response_time_ms=round(response_time, 2),
                        checked_at=datetime.now(timezone.utc),
                        message="Odoo platform is working correctly"
                    )
                else:
                    return OdooHealthStatus(
                        url=url,
                        status="error",
                        redirect_location=location,
                        response_time_ms=round(response_time, 2),
                        checked_at=datetime.now(timezone.utc),
                        message=f"Unexpected redirect location: {location}"
                    )
            else:
                return OdooHealthStatus(
                    url=url,
                    status="error",
                    response_time_ms=round(response_time, 2),
                    checked_at=datetime.now(timezone.utc),
                    message=f"Unexpected status code: {response.status_code}"
                )
                
    except httpx.TimeoutException:
        return OdooHealthStatus(
            url=url,
            status="offline",
            checked_at=datetime.now(timezone.utc),
            message="Connection timeout"
        )
    except httpx.ConnectError as e:
        return OdooHealthStatus(
            url=url,
            status="offline",
            checked_at=datetime.now(timezone.utc),
            message=f"Connection failed: {str(e)}"
        )
    except Exception as e:
        return OdooHealthStatus(
            url=url,
            status="error",
            checked_at=datetime.now(timezone.utc),
            message=f"Error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
